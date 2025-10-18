from __future__ import annotations

import math
from typing import Dict, Any, List, Tuple


class SimpleTextRM:
    def __init__(self, tags: List[str]):
        # linear weights for features
        self.w: Dict[str, float] = {
            "bias": 0.0,
            "length": -0.0005,
            "words": -0.01,
            "hedges": -0.3,
            "question_marks": 0.05,
            "exclamations": -0.02,
            "specificity_markers": 0.4,
        }
        # tag-head weights (simple linear + sigmoid)
        self.tag_w: Dict[str, Dict[str, float]] = {
            tag: {"bias": 0.0, "hedges": -0.8, "specificity_markers": 0.8, "words": -0.02}
            for tag in tags
        }

    def features(self, x: Dict[str, Any]) -> Dict[str, float]:
        feats = {
            "bias": 1.0,
            "length": float(x.get("length", 0)),
            "words": float(x.get("words", 0)),
            "hedges": float(x.get("hedges", 0)),
            "question_marks": float(x.get("question_marks", 0)),
            "exclamations": float(x.get("exclamations", 0)),
            "specificity_markers": float(x.get("specificity_markers", 0)),
        }
        return feats

    def score_feats(self, feats: Dict[str, float]) -> float:
        return sum(self.w.get(k, 0.0) * v for k, v in feats.items())

    def tag_scores(self, feats: Dict[str, float]) -> Dict[str, float]:
        out = {}
        for tag, tw in self.tag_w.items():
            z = sum(tw.get(k, 0.0) * feats.get(k, 0.0) for k in feats) + tw.get("bias", 0.0)
            out[tag] = 1.0 / (1.0 + math.exp(-z))
        return out

    def pairwise_prob(self, fa: Dict[str, float], fb: Dict[str, float]) -> float:
        za = self.score_feats(fa)
        zb = self.score_feats(fb)
        return 1.0 / (1.0 + math.exp(-(za - zb)))

    def train_pair(self, fa: Dict[str, float], fb: Dict[str, float], ya: float, lr: float = 0.01, weight: float = 1.0):
        p = self.pairwise_prob(fa, fb)
        g = (ya - p) * weight
        # update linear weights
        for k in self.w.keys():
            self.w[k] = self.w[k] + lr * g * (fa.get(k, 0.0) - fb.get(k, 0.0))

    def explain(self, feats: Dict[str, float], top_k: int = 3) -> List[str]:
        ts = self.tag_scores(feats)
        return [k for k, _ in sorted(ts.items(), key=lambda x: x[1], reverse=True)[:top_k]]


rm_global: SimpleTextRM | None = None


def get_rm(tags: List[str]) -> SimpleTextRM:
    global rm_global
    if rm_global is None:
        rm_global = SimpleTextRM(tags)
    return rm_global

