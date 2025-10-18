from typing import Dict, Any, List
import re

from .adapters.text_adapter import text_features
from .config import config


def remove_hedges(text: str) -> str:
    patterns = [
        r"\bmaybe\b",
        r"\bperhaps\b",
        r"\bkind of\b",
        r"\bsort of\b",
        r"\bI think\b",
        r"\bjust\b",
    ]
    s = text
    for p in patterns:
        s = re.sub(p, "", s, flags=re.IGNORECASE)
    # tidy spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tighten_length(text: str, ratio: float = 0.8) -> str:
    words = text.split()
    if len(words) <= 4:
        return text
    target = max(4, int(len(words) * ratio))
    return " ".join(words[:target])


def add_concrete_ask(text: str) -> str:
    if re.search(r"\b(today|tomorrow|at \d|on \w+)\b", text, flags=re.IGNORECASE):
        return text
    suffix = " Can we meet tomorrow at 10am to decide next steps?"
    if text.endswith(('.', '!', '?')):
        return text + suffix
    return text + "." + suffix


def generate_text_variants(item_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    base = item_payload["content_refs"]["text"]
    out: List[Dict[str, Any]] = []
    candidates = [
        ("remove_hedges", remove_hedges(base)),
        ("tighten_length", tighten_length(base)),
        ("add_concrete_ask", add_concrete_ask(base)),
    ]
    for diff_type, content in candidates[: config.max_variants]:
        out.append(
            {
                "diff_type": diff_type,
                "content_ref": {"text": content},
                "features": text_features(content),
            }
        )
    return out

