from fastapi import APIRouter, HTTPException

from ..schemas import NextDuelResponse
from ..storage import db
from ..bandit import pick_next_duel


router = APIRouter(prefix="/next_duel", tags=["bandit"])


@router.get("")
def next_duel(item_id: str) -> NextDuelResponse:
    vids = [v_id for v_id, v in db.variants.items() if v["item_id"] == item_id]
    if len(vids) < 2:
        raise HTTPException(status_code=400, detail="Need at least two variants")
    scores = {v: (db.scores.get(v, {}).get("s", 0.0), db.scores.get(v, {}).get("stderr", 1.0)) for v in vids}
    a, b = pick_next_duel(vids, scores)
    return NextDuelResponse(item_id=item_id, a_variant_id=a, b_variant_id=b)

