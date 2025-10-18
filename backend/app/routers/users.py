from fastapi import APIRouter, Header
from typing import Optional

from ..storage import db
from ..config import config


router = APIRouter(prefix="/users", tags=["users"])


def _uid(x_user_id: Optional[str]) -> str:
    return x_user_id or "u_demo"


@router.get("/me")
def me(x_user_id: Optional[str] = Header(None)):
    uid = _uid(x_user_id)
    rec = db.users.get(uid) or {"preferred_topic": None}
    return {"user_id": uid, "preferred_topic": rec.get("preferred_topic")}


@router.post("/me/topic")
def set_topic(payload: dict, x_user_id: Optional[str] = Header(None)):
    uid = _uid(x_user_id)
    topic = payload.get("topic")
    if topic not in config.topics:
        return {"ok": False, "error": "unknown topic"}
    db.users[uid] = {"preferred_topic": topic}
    return {"ok": True, "user_id": uid, "preferred_topic": topic}

