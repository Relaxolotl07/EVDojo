from fastapi import APIRouter

from ..config import config


router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/status")
def debug_status():
    return {
        "debug": bool(config.debug_demo),
        "force_emit": bool(config.debug_demo_force_emit),
        "yes_word": config.debug_yes_word,
        "no_word": config.debug_no_word,
        "fixed_goal": config.debug_fixed_goal,
        "streaming_enabled": bool(config.streaming_enabled),
    }

