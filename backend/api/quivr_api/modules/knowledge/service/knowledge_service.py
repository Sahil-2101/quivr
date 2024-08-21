from typing import List
from uuid import UUID

from quivr_core.models import KnowledgeStatus
from quivr_core.models import QuivrKnowledge as Knowledge
from sqlalchemy.exc import IntegrityError

from quivr_api.logger import get_logger
from quivr_api.modules.dependencies import BaseService
from quivr_api.modules.knowledge.dto.inputs import CreateKnowledgeProperties
from quivr_api.modules.knowledge.dto.outputs import DeleteKnowledgeResponse
from quivr_api.modules.knowledge.entity.knowledge import KnowledgeDB
from quivr_api.modules.knowledge.repository.knowledges import KnowledgeRepository
from quivr_api.modules.knowledge.repository.storage import Storage

logger = get_logger(__name__)


class KnowledgeService(BaseService[KnowledgeRepository]):
    repository_cls = KnowledgeRepository

    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository
        self.storage = Storage()

    async def add_knowledge(
        self, knowledge_to_add: CreateKnowledgeProperties
    ) -> Knowledge:
        knowledge_data = knowledge_to_add.dict()
        knowledge = KnowledgeDB(**knowledge_data)

        inserted_knowledge_db_instance = await self.repository.insert_knowledge(
            knowledge
        )

        assert inserted_knowledge_db_instance.id, "Knowledge ID not generated"
        if inserted_knowledge_db_instance.source == "local":
            source_link = f"s3://quivr/{inserted_knowledge_db_instance.brain_id}/{inserted_knowledge_db_instance.id}"
            inserted_knowledge_db_instance.source_link = source_link

        inserted_knowledge = await self.repository.insert_knowledge(
            inserted_knowledge_db_instance
        )

        inserted_knowledge = Knowledge(
            id=inserted_knowledge_db_instance.id,
            brain_id=inserted_knowledge_db_instance.brain_id,
            file_name=inserted_knowledge_db_instance.file_name,
            url=inserted_knowledge_db_instance.url,
            mime_type=inserted_knowledge_db_instance.mime_type,
            status=KnowledgeStatus(inserted_knowledge_db_instance.status),
            source=inserted_knowledge_db_instance.source,
            source_link=inserted_knowledge_db_instance.source_link,
            file_size=inserted_knowledge_db_instance.file_size,
            file_sha1=inserted_knowledge_db_instance.file_sha1,
            updated_at=inserted_knowledge_db_instance.updated_at,
            created_at=inserted_knowledge_db_instance.created_at,
            metadata=inserted_knowledge_db_instance.metadata_,  # type: ignore
        )
        return inserted_knowledge

    async def get_all_knowledge(
        self, brain_id: UUID
    ) -> List[Knowledge]:  # FIXME : @chloe use mapping
        knowledges_models = await self.repository.get_all_knowledge_in_brain(brain_id)

        knowledges = [
            Knowledge(
                id=knowledge.id,  # type: ignore
                brain_id=knowledge.brain_id,
                file_name=knowledge.file_name,
                url=knowledge.url,
                mime_type=knowledge.mime_type,
                status=KnowledgeStatus(knowledge.status),
                source=knowledge.source,
                source_link=knowledge.source_link,
                file_size=knowledge.file_size
                if knowledge.file_size
                else 0,  # FIXME: Should not be optional @chloedia
                file_sha1=knowledge.file_sha1
                if knowledge.file_sha1
                else "",  # FIXME: Should not be optional @chloedia
                updated_at=knowledge.updated_at,
                created_at=knowledge.created_at,
                metadata=knowledge.metadata_,  # type: ignore
            )
            for knowledge in knowledges_models
        ]

        return knowledges

    async def update_status_knowledge(
        self,
        knowledge_id: UUID,
        status: KnowledgeStatus,
        brain_id: UUID | None = None,
    ):
        knowledge = await self.repository.update_status_knowledge(knowledge_id, status)
        assert knowledge, "Knowledge not found"
        if status == KnowledgeStatus.ERROR and brain_id:
            assert isinstance(knowledge.file_name, str), "file_name should be a string"
            file_name_with_brain_id = f"{brain_id}/{knowledge.file_name}"
            try:
                self.storage.remove_file(file_name_with_brain_id)
            except Exception as e:
                logger.error(
                    f"Error while removing file {file_name_with_brain_id}: {e}"
                )

        return knowledge

    async def update_file_sha1_knowledge(self, knowledge_id: UUID, file_sha1: str):
        try:
            knowledge = await self.repository.update_file_sha1_knowledge(
                knowledge_id, file_sha1
            )

            return knowledge
        except IntegrityError as e:
            logger.error(f"IntegrityError: {e}")
            raise FileExistsError(
                f"File {knowledge_id} already exists maybe under another file_name"
            )

    async def get_knowledge(self, knowledge_id: UUID) -> Knowledge:
        inserted_knowledge_db_instance = await self.repository.get_knowledge_by_id(
            knowledge_id
        )

        assert inserted_knowledge_db_instance.id, "Knowledge ID not generated"

        inserted_knowledge = Knowledge(
            id=inserted_knowledge_db_instance.id,
            brain_id=inserted_knowledge_db_instance.brain_id,
            file_name=inserted_knowledge_db_instance.file_name,
            url=inserted_knowledge_db_instance.url,
            mime_type=inserted_knowledge_db_instance.mime_type,
            status=KnowledgeStatus(inserted_knowledge_db_instance.status),
            source=inserted_knowledge_db_instance.source,
            source_link=inserted_knowledge_db_instance.source_link,
            file_size=inserted_knowledge_db_instance.file_size,
            file_sha1=inserted_knowledge_db_instance.file_sha1
            if inserted_knowledge_db_instance.file_sha1
            else "",  # FIXME: Should not be optional @chloedia
            updated_at=inserted_knowledge_db_instance.updated_at,
            created_at=inserted_knowledge_db_instance.created_at,
            metadata=inserted_knowledge_db_instance.metadata_,  # type: ignore
        )
        return inserted_knowledge

    async def remove_brain_all_knowledge(self, brain_id: UUID) -> None:
        await self.repository.remove_brain_all_knowledge(brain_id)

        logger.info(
            f"All knowledge in brain {brain_id} removed successfully from table"
        )

    async def remove_knowledge(
        self,
        brain_id: UUID,
        knowledge_id: UUID,  # FIXME: @amine when name in storage change no need for brain id
    ) -> DeleteKnowledgeResponse:
        message = await self.repository.remove_knowledge_by_id(knowledge_id)
        file_name_with_brain_id = f"{brain_id}/{message.file_name}"
        try:
            self.storage.remove_file(file_name_with_brain_id)
        except Exception as e:
            logger.error(f"Error while removing file {file_name_with_brain_id}: {e}")

        return message
