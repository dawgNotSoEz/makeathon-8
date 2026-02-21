from fastapi import APIRouter, Depends

from backend.core.container import get_assistant_service
from backend.core.security import AuthUser, require_roles
from backend.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from backend.services.assistant_service import AssistantService


router = APIRouter()


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
)
async def chat_with_assistant(
    request: AssistantChatRequest,
    service: AssistantService = Depends(get_assistant_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")),
) -> AssistantChatResponse:
    _ = user
    return await service.chat(request.message, request.organizationProfile)
