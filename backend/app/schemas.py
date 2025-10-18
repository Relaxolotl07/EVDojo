from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CreateItemRequest(BaseModel):
    user_id: str
    modality: str
    content: Dict[str, Any]
    context: Dict[str, Any] = {}


class CreateItemResponse(BaseModel):
    item_id: str
    payload: Dict[str, Any]


class CreateVariantsRequest(BaseModel):
    item_id: str


class VariantOut(BaseModel):
    variant_id: str
    parent_item_id: str
    diff_type: str
    content: Dict[str, Any]


class RankResponseEntry(BaseModel):
    variant_id: str
    score: float
    stderr: float
    win_prob_row: Optional[Dict[str, float]] = None


class RankResponse(BaseModel):
    item_id: str
    ranking: List[RankResponseEntry]


class CompareRequest(BaseModel):
    item_id: str
    a_id: str
    b_id: str
    winner_id: Optional[str]
    judge_type: str
    rater_id: Optional[str] = None
    tags: List[str] = []
    abstain: bool = False
    confidence: Optional[float] = None


class CompareResponse(BaseModel):
    comparison_id: str
    updated_scores: Dict[str, float]


class NextDuelResponse(BaseModel):
    item_id: str
    a_variant_id: str
    b_variant_id: str


class RMScoreRequest(BaseModel):
    a_text: str
    b_text: str
    context: Dict[str, Any] = {}
    rater_trust: float = 1.0


class RMScoreResponse(BaseModel):
    winner: Optional[str]
    score_a: float
    score_b: float
    confidence: float
    top_reason_tags: List[str] = []


class JudgeRequest(BaseModel):
    a: Dict[str, Any]
    b: Dict[str, Any]
    context: Dict[str, Any] = {}


class JudgeResponse(BaseModel):
    winner: Optional[str]
    tags: List[str]
    judge_type: str
    confidence: float


# Streaming scorer
class CursorInfo(BaseModel):
    pos: int


class StreamScoreRequest(BaseModel):
    modality: str = "text"
    context: Dict[str, Any] = {}
    snippet: str
    features: Dict[str, Any] = {}
    cursor: Optional[CursorInfo] = None
    rm_version: str = "v1"
    user_id: Optional[str] = None
    item_id: Optional[str] = None
    mode: Optional[str] = "standard"  # off|light|standard|intense


class SpanTag(BaseModel):
    start: int
    end: int
    tag: str


class PatchOp(BaseModel):
    type: str
    range: List[int]
    text: str


class Suggestion(BaseModel):
    label: str
    patch: PatchOp


class StreamScoreResponse(BaseModel):
    p_win: float
    confidence: float
    state: str  # positive|negative|neutral
    tags: List[str] = []
    spans: List[SpanTag] = []
    suggestion: Optional[Suggestion] = None
    rm_version: str
    explanations: Dict[str, Any] = {}


class CalibrationMeta(BaseModel):
    rm_version: str
    method: str
    params: Dict[str, Any]


class MetricsStreamResponse(BaseModel):
    latency_p95_ms: float
    alerts_per_min: float
    suppress_rate: float
    ece: Optional[float] = None
    agreement_rate: Optional[float] = None


class ExpertQueueResponse(BaseModel):
    queue: List[Dict[str, Any]]


class ExpertLabelRequest(BaseModel):
    comparison_id: str
    winner_id: Optional[str]
    tags: List[str] = []
    abstain: bool = False


class ModerateCheckRequest(BaseModel):
    goal: str


class ModerateCheckResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None


class AbuseReportRequest(BaseModel):
    item_id: str
    reporter_id: str
    reason: str


class AbuseReportResponse(BaseModel):
    report_id: str
