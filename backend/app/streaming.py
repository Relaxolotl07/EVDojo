from __future__ import annotations

import math
import time
import re
from typing import Dict, Any, List, Tuple

from .rm import get_rm
from .config import config
from .adapters.text_adapter import text_features
from .variants import remove_hedges, add_concrete_ask


class PlattCalibrator:
    def __init__(self, a: float = 1.0, b: float = 0.0):
        self.a = a
        self.b = b

    def calibrate(self, z: float) -> float:
        return 1.0 / (1.0 + math.exp(-(self.a * z + self.b)))


# In-memory artifacts and state
calibration_store: Dict[str, Dict[str, Any]] = {
    config.rm_version: {"method": "platt", "params": {"a": 1.0, "b": 0.0}, "obj": PlattCalibrator(1.0, 0.0)}
}


def get_calibrator(rm_version: str) -> PlattCalibrator:
    art = calibration_store.get(rm_version)
    if art and art.get("obj"):
        return art["obj"]
    # default
    cal = PlattCalibrator(1.0, 0.0)
    calibration_store[rm_version] = {"method": "platt", "params": {"a": 1.0, "b": 0.0}, "obj": cal}
    return cal


# Hysteresis/cooldown state per session (user_id:item_id)
class StreamState:
    def __init__(self):
        self.last_state: Dict[str, str] = {}
        self.last_ts: Dict[str, float] = {}
        self.good_run: Dict[str, int] = {}
        self.bad_run: Dict[str, int] = {}

    def key(self, user_id: str | None, item_id: str | None) -> str:
        return f"{user_id or 'anon'}:{item_id or 'none'}"

    def update(self, user_id: str | None, item_id: str | None, state: str, mode: str) -> Tuple[bool, str]:
        k = self.key(user_id, item_id)
        now = time.time() * 1000
        cooldowns = config.streaming["cooldown_ms"]  # type: ignore
        cooldown_ms = cooldowns.get(mode, cooldowns.get("standard", 8000))  # type: ignore
        min_persistence = int(config.streaming["min_persistence"])  # type: ignore

        # cooldown
        last = self.last_ts.get(k, 0)
        if (now - last) < cooldown_ms:
            return False, self.last_state.get(k, "neutral")

        # persistence counters
        if state == "positive":
            self.good_run[k] = self.good_run.get(k, 0) + 1
            self.bad_run[k] = 0
            if self.good_run[k] >= min_persistence:
                self.last_ts[k] = now
                self.last_state[k] = state
                self.good_run[k] = 0
                return True, state
            return False, self.last_state.get(k, "neutral")
        elif state == "negative":
            self.bad_run[k] = self.bad_run.get(k, 0) + 1
            self.good_run[k] = 0
            if self.bad_run[k] >= min_persistence:
                self.last_ts[k] = now
                self.last_state[k] = state
                self.bad_run[k] = 0
                return True, state
            return False, self.last_state.get(k, "neutral")
        else:
            # neutral resets slowly
            self.good_run[k] = max(0, self.good_run.get(k, 0) - 1)
            self.bad_run[k] = max(0, self.bad_run.get(k, 0) - 1)
            return False, self.last_state.get(k, "neutral")


stream_state = StreamState()


# Metrics (simple rolling counters)
class StreamMetrics:
    def __init__(self):
        self.latencies: List[float] = []
        self.alerts: int = 0
        self.suppressed: int = 0
        self.calls: int = 0

    def add_latency(self, ms: float):
        self.latencies.append(ms)
        self.latencies = self.latencies[-500:]

    def p95(self) -> float:
        if not self.latencies:
            return 0.0
        arr = sorted(self.latencies)
        idx = int(0.95 * (len(arr) - 1))
        return arr[idx]

    def suppress_rate(self) -> float:
        if self.calls == 0:
            return 0.0
        return float(self.suppressed) / float(self.calls)


stream_metrics = StreamMetrics()


HEDGE_PATTERNS = [
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bI think\b",
    r"\bjust\b",
]


def find_spans(text: str) -> List[Dict[str, Any]]:
    spans: List[Dict[str, Any]] = []
    for pat in HEDGE_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            spans.append({"start": m.start(), "end": m.end(), "tag": "hedge"})
    return spans


def derive_stream_features(text: str) -> Dict[str, Any]:
    feats = text_features(text)
    # Extra streaming markers
    feats["has_concrete_time"] = 1.0 if re.search(r"\b(at\s*\d|\d\s*(am|pm)|monday|tuesday|wednesday|thursday|friday)\b", text, re.I) else 0.0
    feats["has_place"] = 1.0 if re.search(r"\b(cafe|office|zoom|room|building|coffee)\b", text, re.I) else 0.0
    return feats


def streaming_score(text: str, context: Dict[str, Any], rm_version: str) -> Tuple[float, float, List[str]]:
    rm = get_rm([])
    feats = rm.features(derive_stream_features(text))
    # raw score as linear score mapped to probability via sigmoid
    z = sum(rm.w.get(k, 0.0) * v for k, v in feats.items())
    cal = get_calibrator(rm_version)
    p_win = cal.calibrate(z)
    conf = abs(p_win - 0.5) * 2.0
    tags = rm.explain(feats)
    return p_win, conf, tags


def suggestion_for(text: str, tags: List[str]) -> Tuple[str, str]:
    if "fewer_hedges" in tags or re.search("|".join(HEDGE_PATTERNS), text, re.I):
        return "Remove hedges", remove_hedges(text)
    else:
        return "Add a concrete time/place", add_concrete_ask(text)

