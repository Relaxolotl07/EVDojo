from fastapi import APIRouter, HTTPException
from typing import List

from ..schemas import CreateVariantsRequest, VariantOut
from ..storage import db
from ..variants import generate_text_variants


router = APIRouter(prefix="/variants", tags=["variants"])


@router.post("")
def create_variants(req: CreateVariantsRequest) -> List[VariantOut]:
    item = db.items.get(req.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    payload = {
        "modality": item["modality"],
        "content_refs": item["content_refs"],
        "compact_features": item["features_json"],
        "context": item["context_json"],
    }
    vs = generate_text_variants(payload)
    out = []
    for v in vs:
        vid = db.create_variant(req.item_id, v["content_ref"], v["features"], v["diff_type"])
        out.append(
            VariantOut(
                variant_id=vid,
                parent_item_id=req.item_id,
                diff_type=v["diff_type"],
                content=v["content_ref"],
            )
        )
    return out


@router.post("/apply_suggestion")
def apply_suggestion(item_id: str, diff_type: str, content_text: str) -> VariantOut:
    item = db.items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    features = {"length": len(content_text), "words": len(content_text.split())}
    vid = db.create_variant(item_id, {"text": content_text}, features, diff_type)
    return VariantOut(variant_id=vid, parent_item_id=item_id, diff_type=diff_type, content={"text": content_text})
