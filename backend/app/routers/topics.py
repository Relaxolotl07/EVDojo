from fastapi import APIRouter

from ..config import config


router = APIRouter(prefix="", tags=["topics"])


@router.get("/topics")
def get_topics():
    return {"topics": config.topics}


@router.post("/experts/topics/init")
def init_topic(payload: dict):
    topic = payload.get("topic")
    description = payload.get("description", "")
    tags = payload.get("tags", [])
    # Stub: accept only predefined topics, return current rm_version
    if topic not in config.topics:
        return {"topic": topic, "rm_version": config.rm_version, "note": "non-predefined topic; ok for dev"}
    return {"topic": topic, "rm_version": config.rm_version}

