from typing import Sequence
from uuid import UUID

from asyncpg.exceptions import UniqueViolationError
from fastapi import HTTPException
from quivr_core.models import KnowledgeStatus
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from quivr_api.logger import get_logger
from quivr_api.modules.brain.entity.brain_entity import Brain
from quivr_api.modules.dependencies import BaseRepository, get_supabase_client
from quivr_api.modules.knowledge.dto.outputs import DeleteKnowledgeResponse
from quivr_api.modules.knowledge.entity.knowledge import KnowledgeDB

logger = get_logger(__name__)


class KnowledgeRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        supabase_client = get_supabase_client()
        self.db = supabase_client

    async def insert_knowledge(
        self, knowledge: KnowledgeDB, brain_id: UUID
    ) -> KnowledgeDB:
        logger.debug(f"Inserting knowledge {knowledge}")
        query = select(Brain).where(Brain.brain_id == brain_id)
        result = await self.session.exec(query)
        brain = result.first()
        if not brain:
            raise HTTPException(404, "Brain not found")
        try:
            knowledge.brains.append(brain)
            self.session.add(knowledge)
            await self.session.commit()
            await self.session.refresh(knowledge)
        except IntegrityError:
            await self.session.rollback()
            raise Exception("Integrity error while creating knowledge.")
        except Exception as e:
            await self.session.rollback()
            raise e
        return knowledge

    async def link_to_brain(
        self, knowledge_id: UUID, brain_id: UUID
    ) -> (
        KnowledgeDB
    ):  # FIXME : @amine @chloe Unused but to use later for fixing sha1 issues
        knowledge = await self.get_knowledge_by_id(knowledge_id)
        brain = await self.get_brain_by_id(brain_id)
        knowledge.brains.append(brain)
        self.session.add(knowledge)
        await self.session.commit()
        await self.session.refresh(knowledge)
        return knowledge

    async def remove_knowledge_by_id(
        self, knowledge_id: UUID
    ) -> DeleteKnowledgeResponse:
        query = select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
        result = await self.session.exec(query)
        knowledge = result.first()

        if not knowledge:
            raise HTTPException(404, "Knowledge not found")

        await self.session.delete(knowledge)
        await self.session.commit()
        assert isinstance(knowledge.file_name, str), "file_name should be a string"
        return DeleteKnowledgeResponse(
            file_name=knowledge.file_name,
            status="deleted",
            knowledge_id=knowledge_id,
        )

    async def get_knowledge_by_id(self, knowledge_id: UUID) -> KnowledgeDB:
        query = select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
        result = await self.session.exec(query)
        knowledge = result.first()

        if not knowledge:
            raise HTTPException(404, "Knowledge not found")

        return knowledge

    async def get_brain_by_id(self, brain_id: UUID) -> Brain:
        # Get all knowledge_id in a brain
        query = select(Brain).where(Brain.brain_id == brain_id)
        result = await self.session.exec(query)
        brain = result.first()
        if not brain:
            raise HTTPException(404, "Knowledge not found")
        return brain

    async def remove_brain_all_knowledge(self, brain_id) -> int:
        """
        Remove all knowledge in a brain
        Args:
            brain_id (UUID): The id of the brain
        """
        brain = await self.get_brain_by_id(brain_id)
        all_knowledge = await brain.awaitable_attrs.knowledges
        knowledge_to_delete_list = [
            knowledge.knowledge.source_link
            for knowledge in all_knowledge
            if knowledge.source == "local"
        ]

        if knowledge_to_delete_list:
            # FIXME: Can we bypass db ? @Amine
            self.db.storage.from_("quivr").remove(knowledge_to_delete_list)

        for item in all_knowledge:
            await self.session.delete(item)
        await self.session.commit()
        return len(knowledge_to_delete_list)

    async def update_status_knowledge(
        self, knowledge_id: UUID, status: KnowledgeStatus
    ) -> KnowledgeDB | None:
        query = select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
        result = await self.session.exec(query)
        knowledge = result.first()

        if not knowledge:
            return None

        knowledge.status = status
        self.session.add(knowledge)
        await self.session.commit()
        await self.session.refresh(knowledge)

        return knowledge

    async def update_source_link_knowledge(
        self, knowledge_id: UUID, source_link: str
    ) -> KnowledgeDB:
        query = select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
        result = await self.session.exec(query)
        knowledge = result.first()

        if not knowledge:
            raise HTTPException(404, "Knowledge not found")

        knowledge.source_link = source_link
        self.session.add(knowledge)
        await self.session.commit()
        await self.session.refresh(knowledge)

        return knowledge

    async def update_file_sha1_knowledge(
        self, knowledge_id: UUID, file_sha1: str
    ) -> KnowledgeDB | None:
        query = select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
        result = await self.session.exec(query)
        knowledge = result.first()

        if not knowledge:
            return None

        try:
            knowledge.file_sha1 = file_sha1
            self.session.add(knowledge)
            await self.session.commit()
            await self.session.refresh(knowledge)
            return knowledge
        except (UniqueViolationError, IntegrityError, Exception):
            await self.session.rollback()
            raise FileExistsError(
                f"File {knowledge_id} already exists maybe under another file_name"
            )

    async def get_all_knowledge(self) -> Sequence[KnowledgeDB]:
        query = select(KnowledgeDB)
        result = await self.session.exec(query)
        return result.all()
