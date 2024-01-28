from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
<<<<<<< Updated upstream
||||||| Stash base
from logger import get_logger
=======
from langchain.embeddings.ollama import OllamaEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from logger import get_logger
>>>>>>> Stashed changes
from middlewares.auth import AuthBearer, get_current_user
<<<<<<< Updated upstream
from models.databases.entity import LLMModels
||||||| Stash base
=======
from models.settings import BrainSettings, get_supabase_client
>>>>>>> Stashed changes
from models.user_usage import UserUsage
from modules.brain.service.brain_service import BrainService
from modules.chat.controller.chat.brainful_chat import BrainfulChat
from modules.chat.controller.chat.factory import get_chat_strategy
from modules.chat.controller.chat.utils import NullableUUID, check_user_requests_limit
from modules.chat.dto.chats import ChatItem, ChatQuestion
from modules.chat.dto.inputs import (
    ChatUpdatableProperties,
    CreateChatProperties,
    QuestionAndAnswer,
)
from modules.chat.entity.chat import Chat
from modules.chat.service.chat_service import ChatService
from modules.notification.service.notification_service import NotificationService
from modules.user.entity.user_identity import UserIdentity
from vectorstore.supabase import CustomSupabaseVectorStore

from logger import get_logger

logger = get_logger(__name__)

chat_router = APIRouter()

notification_service = NotificationService()
brain_service = BrainService()
chat_service = ChatService()


<<<<<<< Updated upstream
||||||| Stash base
def get_answer_generator(
    chat_id: UUID,
    chat_question: ChatQuestion,
    brain_id: UUID,
    current_user: UserIdentity,
):
    chat_instance = BrainfulChat()
    chat_instance.validate_authorization(user_id=current_user.id, brain_id=brain_id)

    user_usage = UserUsage(
        id=current_user.id,
        email=current_user.email,
    )

    # Get History
    history = chat_service.get_chat_history(chat_id)

    # Get user settings
    user_settings = user_usage.get_user_settings()

    # Get Model settings for the user
    models_settings = user_usage.get_model_settings()

    # Generic
    brain, metadata_brain = brain_service.find_brain_from_question(
        brain_id, chat_question.question, current_user, chat_id, history
    )

    model_to_use, metadata = find_model_and_generate_metadata(
        chat_id,
        brain,
        user_settings,
        models_settings,
        metadata_brain,
    )

    # Raises an error if the user has consumed all of of his credits
    check_user_requests_limit(
        usage=user_usage,
        user_settings=user_settings,
        models_settings=models_settings,
        model_name=model_to_use.name,
    )
    gpt_answer_generator = chat_instance.get_answer_generator(
        chat_id=str(chat_id),
        model=model_to_use.name,
        max_tokens=model_to_use.max_output,
        max_input=model_to_use.max_input,
        temperature=0.1,
        streaming=True,
        prompt_id=chat_question.prompt_id,
        user_id=current_user.id,
        metadata=metadata,
        brain=brain,
    )

    return gpt_answer_generator


=======
def init_vector_store(user_id: UUID) -> CustomSupabaseVectorStore:
    """
    Initialize the vector store
    """
    brain_settings = BrainSettings()
    supabase_client = get_supabase_client()
    embeddings = None
    if brain_settings.ollama_api_base_url:
        embeddings = OllamaEmbeddings(
            base_url=brain_settings.ollama_api_base_url
        )  # pyright: ignore reportPrivateUsage=none
    else:
        embeddings = OpenAIEmbeddings()
    vector_store = CustomSupabaseVectorStore(
        supabase_client, embeddings, table_name="vectors", user_id=user_id
    )

    return vector_store


def get_answer_generator(
    chat_id: UUID,
    chat_question: ChatQuestion,
    brain_id: UUID,
    current_user: UserIdentity,
):
    chat_instance = BrainfulChat()
    chat_instance.validate_authorization(user_id=current_user.id, brain_id=brain_id)

    user_usage = UserUsage(
        id=current_user.id,
        email=current_user.email,
    )

    vector_store = init_vector_store(user_id=current_user.id)

    # Get History
    history = chat_service.get_chat_history(chat_id)

    # Get user settings
    user_settings = user_usage.get_user_settings()

    # Get Model settings for the user
    models_settings = user_usage.get_model_settings()

    # Generic
    brain, metadata_brain = brain_service.find_brain_from_question(
        brain_id, chat_question.question, current_user, chat_id, history, vector_store
    )

    model_to_use, metadata = find_model_and_generate_metadata(
        chat_id,
        brain,
        user_settings,
        models_settings,
        metadata_brain,
    )

    # Raises an error if the user has consumed all of of his credits
    check_user_requests_limit(
        usage=user_usage,
        user_settings=user_settings,
        models_settings=models_settings,
        model_name=model_to_use.name,
    )

    gpt_answer_generator = chat_instance.get_answer_generator(
        chat_id=str(chat_id),
        model=model_to_use.name,
        max_tokens=model_to_use.max_output,
        max_input=model_to_use.max_input,
        temperature=0.1,
        streaming=True,
        prompt_id=chat_question.prompt_id,
        user_id=current_user.id,
        metadata=metadata,
        brain=brain,
    )

    return gpt_answer_generator


>>>>>>> Stashed changes
@chat_router.get("/chat/healthz", tags=["Health"])
async def healthz():
    return {"status": "ok"}


# get all chats
@chat_router.get("/chat", dependencies=[Depends(AuthBearer())], tags=["Chat"])
async def get_chats(current_user: UserIdentity = Depends(get_current_user)):
    """
    Retrieve all chats for the current user.

    - `current_user`: The current authenticated user.
    - Returns a list of all chats for the user.

    This endpoint retrieves all the chats associated with the current authenticated user. It returns a list of chat objects
    containing the chat ID and chat name for each chat.
    """
    chats = chat_service.get_user_chats(str(current_user.id))
    return {"chats": chats}


# delete one chat
@chat_router.delete(
    "/chat/{chat_id}", dependencies=[Depends(AuthBearer())], tags=["Chat"]
)
async def delete_chat(chat_id: UUID):
    """
    Delete a specific chat by chat ID.
    """
    notification_service.remove_chat_notifications(chat_id)

    chat_service.delete_chat_from_db(chat_id)
    return {"message": f"{chat_id}  has been deleted."}


# update existing chat metadata
@chat_router.put(
    "/chat/{chat_id}/metadata", dependencies=[Depends(AuthBearer())], tags=["Chat"]
)
async def update_chat_metadata_handler(
    chat_data: ChatUpdatableProperties,
    chat_id: UUID,
    current_user: UserIdentity = Depends(get_current_user),
):
    """
    Update chat attributes
    """

    chat = chat_service.get_chat_by_id(
        chat_id  # pyright: ignore reportPrivateUsage=none
    )
    if str(current_user.id) != chat.user_id:
        raise HTTPException(
            status_code=403,  # pyright: ignore reportPrivateUsage=none
            detail="You should be the owner of the chat to update it.",  # pyright: ignore reportPrivateUsage=none
        )
    return chat_service.update_chat(chat_id=chat_id, chat_data=chat_data)


# create new chat
@chat_router.post("/chat", dependencies=[Depends(AuthBearer())], tags=["Chat"])
async def create_chat_handler(
    chat_data: CreateChatProperties,
    current_user: UserIdentity = Depends(get_current_user),
):
    """
    Create a new chat with initial chat messages.
    """

    return chat_service.create_chat(user_id=current_user.id, chat_data=chat_data)


# add new question to chat
@chat_router.post(
    "/chat/{chat_id}/question",
    dependencies=[
        Depends(
            AuthBearer(),
        ),
    ],
    tags=["Chat"],
)
async def create_question_handler(
    request: Request,
    chat_question: ChatQuestion,
    chat_id: UUID,
    brain_id: NullableUUID
    | UUID
    | None = Query(..., description="The ID of the brain"),
    current_user: UserIdentity = Depends(get_current_user),
):
    """
    Add a new question to the chat.
    """

    chat_instance = get_chat_strategy(brain_id)

    chat_instance.validate_authorization(user_id=current_user.id, brain_id=brain_id)

    fallback_model = "gpt-3.5-turbo-1106"
    fallback_temperature = 0.1
    fallback_max_tokens = 512

    user_daily_usage = UserUsage(
        id=current_user.id,
        email=current_user.email,
    )
    user_settings = user_daily_usage.get_user_settings()
    is_model_ok = (chat_question).model in user_settings.get("models", ["gpt-3.5-turbo-1106"])  # type: ignore

    # Retrieve chat model (temperature, max_tokens, model)
    if (
        not chat_question.model
        or not chat_question.temperature
        or not chat_question.max_tokens
    ):
        if brain_id:
            brain = brain_service.get_brain_by_id(brain_id)
            if brain:
                fallback_model = brain.model or fallback_model
                fallback_temperature = brain.temperature or fallback_temperature
                fallback_max_tokens = brain.max_tokens or fallback_max_tokens

        chat_question.model = chat_question.model or fallback_model
        chat_question.temperature = chat_question.temperature or fallback_temperature
        chat_question.max_tokens = chat_question.max_tokens or fallback_max_tokens

    try:
        check_user_requests_limit(current_user, chat_question.model)
        is_model_ok = (chat_question).model in user_settings.get("models", ["gpt-3.5-turbo-1106"])  # type: ignore
        gpt_answer_generator = chat_instance.get_answer_generator(
            chat_id=str(chat_id),
            model=chat_question.model if is_model_ok else "gpt-3.5-turbo-1106",  # type: ignore
            max_tokens=chat_question.max_tokens,
            temperature=chat_question.temperature,
            streaming=False,
            prompt_id=chat_question.prompt_id,
            user_id=current_user.id,
            max_input=2000,
            brain=brain_service.get_brain_by_id(brain_id),
            metadata={},
        )

        chat_answer = gpt_answer_generator.generate_answer(
            chat_id, chat_question, save_answer=True
        )

        return chat_answer
    except HTTPException as e:
        raise e


# stream new question response from chat
@chat_router.post(
    "/chat/{chat_id}/question/stream",
    dependencies=[
        Depends(
            AuthBearer(),
        ),
    ],
    tags=["Chat"],
)
async def create_stream_question_handler(
    request: Request,
    chat_question: ChatQuestion,
    chat_id: UUID,
    brain_id: NullableUUID
    | UUID
    | None = Query(..., description="The ID of the brain"),
    current_user: UserIdentity = Depends(get_current_user),
) -> StreamingResponse:
<<<<<<< Updated upstream
    chat_instance = BrainfulChat()
    chat_instance.validate_authorization(user_id=current_user.id, brain_id=brain_id)

    user_usage = UserUsage(
        id=current_user.id,
        email=current_user.email,
||||||| Stash base
    gpt_answer_generator = get_answer_generator(
        chat_id, chat_question, brain_id, current_user
=======
    logger.info(f"Brain ID: {brain_id}")
    gpt_answer_generator = get_answer_generator(
        chat_id, chat_question, brain_id, current_user
>>>>>>> Stashed changes
    )

    # Get History
    history = chat_service.get_chat_history(chat_id)

    # Get user settings
    user_settings = user_usage.get_user_settings()

    # Get Model settings for the user
    models_settings = user_usage.get_model_settings()

    # Generic
    brain_id_to_use, metadata_brain = brain_service.find_brain_from_question(
        brain_id, chat_question.question, current_user, chat_id, history
    )

    # Add metadata_brain to metadata
    metadata = {}
    metadata = {**metadata, **metadata_brain}
    follow_up_questions = chat_service.get_follow_up_question(chat_id)
    metadata["follow_up_questions"] = follow_up_questions

    # Get the Brain settings
    brain = brain_service.get_brain_by_id(brain_id_to_use)

    logger.info(f"Brain model: {brain.model}")
    logger.info(f"Brain is : {str(brain)}")
    try:
        # Default model is gpt-3.5-turbo-1106
        model_to_use = LLMModels(
            name="gpt-3.5-turbo-1106", price=1, max_input=512, max_output=512
        )

        is_brain_model_available = any(
            brain.model == model_dict.get("name") for model_dict in models_settings
        )

        is_user_allowed_model = brain.model in user_settings.get(
            "models", ["gpt-3.5-turbo-1106"]
        )  # Checks if the model is available in the list of models

        logger.info(f"Brain model: {brain.model}")
        logger.info(f"User models: {user_settings.get('models', [])}")
        logger.info(f"Model available: {is_brain_model_available}")
        logger.info(f"User allowed model: {is_user_allowed_model}")

        if is_brain_model_available and is_user_allowed_model:
            # Use the model from the brain
            model_to_use.name = brain.model
            for model_dict in models_settings:
                if model_dict.get("name") == model_to_use.name:
                    logger.info(f"Using model {model_to_use.name}")
                    model_to_use.max_input = model_dict.get("max_input")
                    model_to_use.max_output = model_dict.get("max_output")
                    break

        metadata["model"] = model_to_use.name
        metadata["max_tokens"] = model_to_use.max_output
        metadata["max_input"] = model_to_use.max_input

        check_user_requests_limit(current_user, model_to_use.name)
        gpt_answer_generator = chat_instance.get_answer_generator(
            chat_id=str(chat_id),
            model=model_to_use.name,
            max_tokens=model_to_use.max_output,
            max_input=model_to_use.max_input,
            temperature=0.1,
            streaming=True,
            prompt_id=chat_question.prompt_id,
            user_id=current_user.id,
            metadata=metadata,
            brain=brain,
        )

        return StreamingResponse(
            gpt_answer_generator.generate_stream(
                chat_id, chat_question, save_answer=True
            ),
            media_type="text/event-stream",
        )

    except HTTPException as e:
        raise e


# get chat history
@chat_router.get(
    "/chat/{chat_id}/history", dependencies=[Depends(AuthBearer())], tags=["Chat"]
)
async def get_chat_history_handler(
    chat_id: UUID,
) -> List[ChatItem]:
    # TODO: RBAC with current_user
    return chat_service.get_chat_history_with_notifications(chat_id)


@chat_router.post(
    "/chat/{chat_id}/question/answer",
    dependencies=[Depends(AuthBearer())],
    tags=["Chat"],
)
async def add_question_and_answer_handler(
    chat_id: UUID,
    question_and_answer: QuestionAndAnswer,
) -> Optional[Chat]:
    """
    Add a new question and anwser to the chat.
    """
    return chat_service.add_question_and_answer(chat_id, question_and_answer)
