from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Item(BaseModel):
    id: str
    user_id: str
    modality: str
    context_json: Dict[str, Any]
    content_refs: Dict[str, Any]
    features_json: Dict[str, Any]
    created_at: float


class Variant(BaseModel):
    id: str
    item_id: str
    content_ref: Dict[str, Any]
    features_json: Dict[str, Any]
    diff_type: str
    created_at: float


class Comparison(BaseModel):
    id: str
    item_id: str
    a_id: str
    b_id: str
    winner_id: Optional[str]
    judge_type: str
    rater_id: Optional[str]
    tags: List[str] = []
    abstain: bool = False
    confidence: Optional[float]
    created_at: float


class Score(BaseModel):
    variant_id: str
    s: float
    stderr: float
    updated_at: Optional[float]


class Rater(BaseModel):
    id: str
    type: str
    domain: str
    alpha: float
    trust: float
    created_at: float

