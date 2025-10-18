from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List, Dict, Any

from ..storage import db
from ..config import config
from .compare import bt as bt_instance


router = APIRouter(prefix="/expert", tags=["expert"])


@router.get("/queue")
def expert_queue(topic: Optional[str] = None, limit: int = 50):
    topic = topic or (config.topics[0] if config.topics else "internal-request")
    pairs = [p for p in db.pairs.values() if p["topic"] == topic and not p.get("labeled")]
    out: List[Dict[str, Any]] = []
    for p in pairs[:limit]:
        a = db.variants.get(p["a_id"]) or {}
        b = db.variants.get(p["b_id"]) or {}
        item = db.items.get(p["item_id"], {})
        out.append(
            {
                "pair_id": p["id"],
                "item_id": p["item_id"],
                "a": {"variant_id": p["a_id"], "subject": (a.get("content_ref", {}) or {}).get("subject", ""), "body": (a.get("content_ref", {}) or {}).get("body", "")},
                "b": {"variant_id": p["b_id"], "subject": (b.get("content_ref", {}) or {}).get("subject", ""), "body": (b.get("content_ref", {}) or {}).get("body", "")},
                "context": item.get("context_json", {}),
            }
        )
    return out


@router.post("/label")
def expert_label(payload: Dict[str, Any], idempotency_key: Optional[str] = Header(None)):
    pair_id = payload.get("pair_id")
    winner = payload.get("winner")
    tags = payload.get("tags", [])
    rater_id = payload.get("rater_id")
    confidence = float(payload.get("confidence", 0.5))

    if idempotency_key:
        if idempotency_key in db.idempotency:
            return db.idempotency[idempotency_key]

    p = db.pairs.get(pair_id)
    if not p:
        raise HTTPException(status_code=404, detail="pair not found")
    a_id, b_id, item_id = p["a_id"], p["b_id"], p["item_id"]

    # Update BT if not abstain
    if winner in ("A", "B"):
        win_vid = a_id if winner == "A" else b_id
        lose_vid = b_id if winner == "A" else a_id
        # set alpha for rater type expert
        from ..config import config as _cfg
        bt_instance.set_alpha(rater_id or "expert_default", _cfg.expert_alpha)
        bt_instance.update(a_id, b_id, win_vid, rater_id or "expert_default")
        # persist scores
        for vid, (s, se) in bt_instance.get_scores([a_id, b_id]).items():
            db.scores[vid] = {"s": s, "stderr": se}
        p["labeled"] = True
        p["abstain"] = False
    else:
        p["labeled"] = True
        p["abstain"] = True

    # Log comparison row
    db.create_comparison(
        item_id=item_id,
        a_id=a_id,
        b_id=b_id,
        winner_id=(a_id if winner == "A" else (b_id if winner == "B" else None)),
        judge_type="expert",
        rater_id=rater_id,
        tags=tags,
        abstain=(winner == "ABSTAIN"),
        confidence=confidence,
    )

    resp = {"ok": True}
    if idempotency_key:
        db.idempotency[idempotency_key] = resp
    return resp

