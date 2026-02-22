from fastapi import APIRouter, Depends

from backend.core.config import config
from backend.core.container import get_assistant_service
from backend.core.security import AuthUser, require_roles
from backend.schemas.analysis import OrganizationProfile
from backend.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from backend.services.assistant_service import AssistantService


router = APIRouter()


@router.post("")
async def assistant_safe_endpoint(
    query: dict,
    service: AssistantService = Depends(get_assistant_service),
) -> dict:
    try:
        message = str(query.get("message", "")).strip()
        if not message:
            return {"error": "Assistant failed safely", "details": "message is required"}

        profile = OrganizationProfile(
            organization_name="Default Organization",
            industry="General",
            business_model="General",
            sub_sector="General",
        )
        response = await service.chat(message, profile)
        return {"response": response.reply, "confidence": response.confidence, "context_used": response.context_used}
    except Exception:
        return {"error": "Assistant failed safely"}


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
)
async def chat_with_assistant(
    request: AssistantChatRequest,
    service: AssistantService = Depends(get_assistant_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user"))
    if config.environment != "dev"
    else Depends(
        lambda: AuthUser.model_validate(
            {
                "sub": "dev",
                "role": "admin",
                "iss": config.jwt_issuer,
                "aud": config.jwt_audience,
                "exp": 9999999999,
            }
        )
    ),
) -> AssistantChatResponse:
    _ = user
    return await service.chat(request.message, request.organizationProfile)
