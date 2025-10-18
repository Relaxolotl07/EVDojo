from fastapi import APIRouter

from ..schemas import ModerateCheckRequest, ModerateCheckResponse
from ..moderation import is_goal_allowed


router = APIRouter(prefix="/moderate", tags=["moderation"])


@router.post("/check")
def moderate(req: ModerateCheckRequest) -> ModerateCheckResponse:
    ok, reason = is_goal_allowed(req.goal)
    return ModerateCheckResponse(allowed=ok, reason=reason)

