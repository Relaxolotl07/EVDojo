from __future__ import annotations

from typing import Dict, Any, List, Tuple
from .config import config
from .rm import get_rm


def judge_pair(a: Dict[str, Any], b: Dict[str, Any], context: Dict[str, Any]) -> Tuple[str | None, List[str], str, float]:
    # RM first
    rm = get_rm(config.allowed_reason_tags)
    fa = rm.features(a.get("features", a.get("compact_features", {})))
    fb = rm.features(b.get("features", b.get("compact_features", {})))
    p = rm.pairwise_prob(fa, fb)
    margin = abs(p - 0.5) * 2  # 0..1
    if margin >= config.rm_accept_margin:
        winner = "A" if p > 0.5 else "B"
        feats = fa if winner == "A" else fb
        tags = rm.explain(feats, top_k=3)
        return winner, tags, "rm", margin

    # Fallback to LLM (stub): return abstain with low confidence
    return None, [], "llm_stub", 0.3

