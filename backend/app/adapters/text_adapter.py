import re
from typing import Dict, Any


HEDGES = [
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bI think\b",
    r"\bjust\b",
]


def redact_pii(s: str) -> str:
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", s)
    s = re.sub(r"@([A-Za-z0-9_]+)", "[@handle]", s)
    s = re.sub(r"\b\+?\d[\d\s\-]{6,}\b", "[phone]", s)
    return s


def count_hedges(s: str) -> int:
    lower = s.lower()
    return sum(len(re.findall(pat, lower)) for pat in HEDGES)


def text_features(s: str) -> Dict[str, Any]:
    return {
        "length": len(s),
        "words": len(s.split()),
        "hedges": count_hedges(s),
        "question_marks": s.count("?"),
        "exclamations": s.count("!"),
        "specificity_markers": sum(1 for t in ["today", "tomorrow", "at ", "on "] if t in s.lower()),
    }


def normalize_text_payload(text: str, context: Dict[str, Any]) -> Dict[str, Any]:
    redacted = redact_pii(text)
    feats = text_features(redacted)
    return {
        "modality": "text",
        "content_refs": {"text": redacted},
        "compact_features": feats,
        "context": context or {},
    }

