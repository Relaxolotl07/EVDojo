from fastapi import APIRouter
from typing import List, Dict, Any

from ..schemas import ExpertQueueResponse, ExpertLabelRequest
from ..storage import db


router = APIRouter(prefix="/expert", tags=["expert"])


@router.get("/queue")
def expert_queue() -> ExpertQueueResponse:
    # simple queue: latest comparisons without winner
    pending = [c for c in db.comparisons.values() if c["winner_id"] is None]
    # limit size for demo
    queue: List[Dict[str, Any]] = []
    for c in pending[:20]:
        a = db.variants.get(c["a_id"]) or {}
        b = db.variants.get(c["b_id"]) or {}
        queue.append(
            {
                "comparison_id": c["id"],
                "item_id": c["item_id"],
                "A": a.get("content_ref"),
                "B": b.get("content_ref"),
                "context": db.items.get(c["item_id"], {}).get("context_json", {}),
            }
        )
    return ExpertQueueResponse(queue=queue)


@router.post("/label")
def expert_label(req: ExpertLabelRequest):
    c = db.comparisons.get(req.comparison_id)
    if not c:
        return {"ok": False}
    c["winner_id"] = req.winner_id
    c["tags"] = req.tags
    c["abstain"] = req.abstain
    return {"ok": True}

