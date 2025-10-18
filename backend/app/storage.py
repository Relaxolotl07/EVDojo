from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional, Tuple, Any


class InMemoryDB:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seq: Dict[str, int] = {}
        self.items: Dict[str, Dict[str, Any]] = {}
        self.variants: Dict[str, Dict[str, Any]] = {}
        self.comparisons: Dict[str, Dict[str, Any]] = {}
        self.scores: Dict[str, Dict[str, float]] = {}
        self.raters: Dict[str, Dict[str, Any]] = {}
        self.gold_pairs: Dict[str, Dict[str, Any]] = {}
        self.abuse_reports: Dict[str, Dict[str, Any]] = {}
        self.stream_events: Dict[str, Dict[str, Any]] = {}
        self.rm_calibration: Dict[str, Dict[str, Any]] = {}
        self.pairs: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
        self.idempotency: Dict[str, Any] = {}

    def _next_id(self, table: str) -> str:
        with self._lock:
            n = self._seq.get(table, 0) + 1
            self._seq[table] = n
        return f"{table}_{n}"

    def now(self) -> float:
        return time.time()

    # Items
    def create_item(self, user_id: str, modality: str, context: dict, content_refs: dict, features: dict) -> str:
        item_id = self._next_id("items")
        self.items[item_id] = {
            "id": item_id,
            "user_id": user_id,
            "modality": modality,
            "context_json": context,
            "content_refs": content_refs,
            "features_json": features,
            "created_at": self.now(),
        }
        return item_id

    # Variants
    def create_variant(self, item_id: str, content_ref: dict, features: dict, diff_type: str) -> str:
        v_id = self._next_id("variants")
        self.variants[v_id] = {
            "id": v_id,
            "item_id": item_id,
            "content_ref": content_ref,
            "features_json": features,
            "diff_type": diff_type,
            "created_at": self.now(),
        }
        # init score record if absent
        self.scores.setdefault(v_id, {"s": 0.0, "stderr": 1.0})
        return v_id

    # Comparisons
    def create_comparison(
        self,
        item_id: str,
        a_id: str,
        b_id: str,
        winner_id: Optional[str],
        judge_type: str,
        rater_id: Optional[str],
        tags: List[str],
        abstain: bool,
        confidence: Optional[float] = None,
    ) -> str:
        c_id = self._next_id("comparisons")
        self.comparisons[c_id] = {
            "id": c_id,
            "item_id": item_id,
            "a_id": a_id,
            "b_id": b_id,
            "winner_id": winner_id,
            "judge_type": judge_type,
            "rater_id": rater_id,
            "tags": tags,
            "abstain": abstain,
            "confidence": confidence,
            "created_at": self.now(),
        }
        return c_id

    # Raters
    def upsert_rater(self, r_id: str, r_type: str, domain: str, alpha: float, trust: float):
        self.raters[r_id] = {
            "id": r_id,
            "type": r_type,
            "domain": domain,
            "alpha": alpha,
            "trust": trust,
            "created_at": self.now(),
        }

    # Stream events
    def append_stream_event(self, user_id: str, item_id: str | None, variant_id: str | None, state: str, p_win: float, tags: list, suggestion: dict) -> str:
        e_id = self._next_id("stream_event")
        self.stream_events[e_id] = {
            "id": e_id,
            "user_id": user_id,
            "item_id": item_id,
            "variant_id": variant_id,
            "state": state,
            "p_win": p_win,
            "tags": tags,
            "suggestion": suggestion,
            "created_at": self.now(),
        }
        return e_id

    # Pairs
    def create_pair(self, item_id: str, a_id: str, b_id: str, topic: str) -> str:
        p_id = self._next_id("pair")
        self.pairs[p_id] = {
            "id": p_id,
            "item_id": item_id,
            "a_id": a_id,
            "b_id": b_id,
            "topic": topic,
            "created_at": self.now(),
            "labeled": False,
            "abstain": False,
        }
        return p_id


db = InMemoryDB()
