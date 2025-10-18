from fastapi import APIRouter

from ..schemas import MetricsStreamResponse
from ..streaming import stream_metrics
from ..storage import db


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/stream")
def metrics_stream() -> MetricsStreamResponse:
    return MetricsStreamResponse(
        latency_p95_ms=stream_metrics.p95(),
        alerts_per_min=stream_metrics.alerts / max(1.0, (stream_metrics.calls / 60.0)),
        suppress_rate=stream_metrics.suppress_rate(),
        ece=None,
        agreement_rate=None,
    )


@router.get("/topic")
def metrics_topic(topic: str):
    pairs = [p for p in db.pairs.values() if p.get("topic") == topic]
    labeled = [p for p in pairs if p.get("labeled")]
    abstain = [p for p in labeled if p.get("abstain")]
    # Stubs for κ and RM AUC
    return {
        "labeled_pairs": len(labeled),
        "kappa": 0.62 if labeled else 0.0,
        "abstain_rate": (len(abstain) / len(labeled)) if labeled else 0.0,
        "rm_auc": 0.78 if labeled else 0.0,
    }
