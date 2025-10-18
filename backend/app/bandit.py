from __future__ import annotations

import random
import math
from typing import Dict, Tuple, List


def thompson_sample(scores: Dict[str, Tuple[float, float]]) -> List[Tuple[str, float]]:
    # sample once from Normal(s, stderr)
    sampled = []
    for vid, (s, se) in scores.items():
        stdev = max(se, 0.05)
        # Box-Muller for normal sample
        u1, u2 = random.random(), random.random()
        z = math.sqrt(-2.0 * math.log(max(u1, 1e-12))) * math.cos(2 * math.pi * u2)
        draw = s + stdev * z
        sampled.append((vid, draw))
    sampled.sort(key=lambda x: x[1], reverse=True)
    return sampled


def pick_next_duel(vids: List[str], scores: Dict[str, Tuple[float, float]]) -> Tuple[str, str]:
    if len(vids) < 2:
        raise ValueError("Need at least two variants for a duel")
    sampled = thompson_sample({v: scores[v] for v in vids})
    a = sampled[0][0]
    # challenger: pick one with high stderr
    challengers = sorted(
        [v for v in vids if v != a], key=lambda v: scores[v][1], reverse=True
    )
    b = challengers[0]
    if a == b and len(sampled) > 1:
        b = sampled[1][0]
    return a, b

