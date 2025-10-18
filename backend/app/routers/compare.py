from fastapi import APIRouter, HTTPException
from typing import Dict

from ..schemas import CompareRequest, CompareResponse
from ..storage import db
from ..bt import BradleyTerry
from ..config import config


router = APIRouter(prefix="/compare", tags=["compare"])
bt = BradleyTerry()


@router.post("")
def compare(req: CompareRequest) -> CompareResponse:
    if req.a_id not in db.variants or req.b_id not in db.variants:
        raise HTTPException(status_code=404, detail="Variant not found")
    # init rater skill if needed
    alpha = config.crowd_alpha
    if req.judge_type == "expert":
        alpha = config.expert_alpha
    elif req.judge_type == "llm":
        alpha = config.llm_alpha
    rater_id = req.rater_id or f"{req.judge_type}_default"
    bt.set_alpha(rater_id, alpha)

    winner = req.winner_id if not req.abstain else None
    bt.update(req.a_id, req.b_id, winner, rater_id)

    # persist scores
    for vid, (s, se) in bt.get_scores([req.a_id, req.b_id]).items():
        db.scores[vid] = {"s": s, "stderr": se}

    cid = db.create_comparison(
        item_id=req.item_id,
        a_id=req.a_id,
        b_id=req.b_id,
        winner_id=winner,
        judge_type=req.judge_type,
        rater_id=req.rater_id,
        tags=req.tags,
        abstain=req.abstain,
        confidence=req.confidence or 0.5,
    )
    return CompareResponse(
        comparison_id=cid,
        updated_scores={vid: db.scores[vid]["s"] for vid in [req.a_id, req.b_id]},
    )

