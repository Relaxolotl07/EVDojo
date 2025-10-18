from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..schemas import CreateItemRequest, CreateItemResponse
from ..adapters.text_adapter import normalize_text_payload
from ..storage import db
from ..moderation import is_goal_allowed


router = APIRouter(prefix="/items", tags=["items"])


def normalize_payload(req: CreateItemRequest) -> Dict[str, Any]:
    if req.modality != "text":
        # For MVP, only text supported; others as stubs
        raise HTTPException(status_code=400, detail="Only text modality supported in MVP")
    goal = req.context.get("goal", "")
    allowed, reason = is_goal_allowed(goal)
    if not allowed:
        raise HTTPException(status_code=400, detail=f"Unsafe goal: {reason}")
    return normalize_text_payload(req.content.get("text", ""), req.context)


@router.post("")
def create_item(req: CreateItemRequest) -> CreateItemResponse:
    payload = normalize_payload(req)
    item_id = db.create_item(
        user_id=req.user_id,
        modality=req.modality,
        context=payload["context"],
        content_refs=payload["content_refs"],
        features=payload["compact_features"],
    )
    return CreateItemResponse(item_id=item_id, payload=payload)

