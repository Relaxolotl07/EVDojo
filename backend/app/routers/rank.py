from fastapi import APIRouter, HTTPException
from typing import List, Dict

from ..schemas import RankResponse, RankResponseEntry
from ..storage import db


router = APIRouter(prefix="/rank", tags=["rank"])


@router.get("")
def get_rank(item_id: str) -> RankResponse:
    vids = [v_id for v_id, v in db.variants.items() if v["item_id"] == item_id]
    if not vids:
        raise HTTPException(status_code=404, detail="No variants for item")
    scores = {v: (db.scores.get(v, {}).get("s", 0.0), db.scores.get(v, {}).get("stderr", 1.0)) for v in vids}
    ranked = sorted(vids, key=lambda x: scores[x][0], reverse=True)

    entries: List[RankResponseEntry] = []
    for v in ranked:
        entries.append(
            RankResponseEntry(
                variant_id=v, score=scores[v][0], stderr=scores[v][1], win_prob_row=None
            )
        )
    return RankResponse(item_id=item_id, ranking=entries)

