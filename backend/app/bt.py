from __future__ import annotations

import math
from typing import Dict, Tuple, List


class BradleyTerry:
    def __init__(self):
        # variant_id -> (score, stderr)
        self.scores: Dict[str, Tuple[float, float]] = {}
        # rater_id -> alpha (temperature)
        self.rater_alpha: Dict[str, float] = {}

    def ensure(self, vid: str):
        if vid not in self.scores:
            self.scores[vid] = (0.0, 1.0)

    def set_alpha(self, rater_id: str, alpha: float):
        self.rater_alpha[rater_id] = alpha

    def prob_win(self, sa: float, sb: float, alpha: float = 1.0) -> float:
        # temperature via alpha: larger alpha -> flatter distribution
        return 1.0 / (1.0 + math.exp(-(sa - sb) / max(alpha, 1e-6)))

    def update(self, a: str, b: str, winner: str | None, rater_id: str | None, lr: float = 0.1):
        self.ensure(a)
        self.ensure(b)
        sa, ea = self.scores[a]
        sb, eb = self.scores[b]
        alpha = 1.0
        if rater_id and (rater_id in self.rater_alpha):
            alpha = self.rater_alpha[rater_id]

        # handle abstain: nudge towards tie (no update)
        if winner is None:
            return

        p = self.prob_win(sa, sb, alpha)
        ya = 1.0 if winner == a else 0.0
        yb = 1.0 - ya
        # gradient for sa: (ya - p); for sb: (yb - (1-p)) = (yb - 1 + p) = (p - ya)
        g = (ya - p)
        sa_new = sa + lr * g
        sb_new = sb - lr * g

        # simple stderr shrinkage with more comparisons
        ea_new = max(0.05, ea * 0.99)
        eb_new = max(0.05, eb * 0.99)
        self.scores[a] = (sa_new, ea_new)
        self.scores[b] = (sb_new, eb_new)

    def get_scores(self, vids: List[str]) -> Dict[str, Tuple[float, float]]:
        out = {}
        for v in vids:
            self.ensure(v)
            out[v] = self.scores[v]
        return out

