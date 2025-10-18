from fastapi import APIRouter
import re

from ..schemas import RMScoreRequest, RMScoreResponse, StreamScoreRequest, StreamScoreResponse, CalibrationMeta, MetricsStreamResponse
from ..rm import get_rm
from ..config import config
from ..streaming import streaming_score, find_spans, suggestion_for, stream_state, stream_metrics, calibration_store
from ..moderation import is_goal_allowed
from ..storage import db


router = APIRouter(prefix="/rm", tags=["rm"])


@router.post("/score")
def rm_score(req: RMScoreRequest) -> RMScoreResponse:
    rm = get_rm(config.allowed_reason_tags)
    # simple features from lengths and heuristics
    fa = rm.features({"length": len(req.a_text), "words": len(req.a_text.split()), "hedges": req.a_text.lower().count("maybe")})
    fb = rm.features({"length": len(req.b_text), "words": len(req.b_text.split()), "hedges": req.b_text.lower().count("maybe")})
    p = rm.pairwise_prob(fa, fb)
    winner = "A" if p > 0.5 else ("B" if p < 0.5 else None)
    conf = abs(p - 0.5) * 2
    tags = rm.explain(fa if (winner == "A") else fb)
    return RMScoreResponse(winner=winner, score_a=p, score_b=1 - p, confidence=conf, top_reason_tags=tags)


@router.post("/train")
def rm_train(req: RMScoreRequest) -> RMScoreResponse:
    rm = get_rm(config.allowed_reason_tags)
    fa = rm.features({"length": len(req.a_text), "words": len(req.a_text.split()), "hedges": req.a_text.lower().count("maybe")})
    fb = rm.features({"length": len(req.b_text), "words": len(req.b_text.split()), "hedges": req.b_text.lower().count("maybe")})
    # assume A preferred for demo if longer specificity
    ya = 1.0 if len(req.a_text) > len(req.b_text) else 0.0
    rm.train_pair(fa, fb, ya, weight=req.rater_trust)
    p = rm.pairwise_prob(fa, fb)
    winner = "A" if p > 0.5 else ("B" if p < 0.5 else None)
    conf = abs(p - 0.5) * 2
    tags = rm.explain(fa if (winner == "A") else fb)
    return RMScoreResponse(winner=winner, score_a=p, score_b=1 - p, confidence=conf, top_reason_tags=tags)


@router.post("/stream/score")
def rm_stream_score(req: StreamScoreRequest) -> StreamScoreResponse:
    import time as _t

    t0 = _t.time()

    if not config.streaming_enabled:
        return StreamScoreResponse(
            p_win=0.5,
            confidence=0.0,
            state="neutral",
            tags=[],
            spans=[],
            suggestion=None,
            rm_version=req.rm_version or config.rm_version,
            explanations={"reason": "streaming_disabled"},
        )

    # Safety gate by goal
    # In debug mode, optionally inject a fixed goal to keep flows consistent
    goal = (req.context or {}).get("goal", "") or (config.debug_fixed_goal if config.debug_demo else "")
    allowed, reason = is_goal_allowed(goal)
    if not allowed:
        # safety-only suggestion
        suggestion = {
            "label": "Rephrase respectfully",
            "patch": {
                "type": "text_replace",
                "range": [0, len(req.snippet)],
                "text": "Hello, could we pick a specific time to meet?",
            },
        }
        resp = StreamScoreResponse(
            p_win=0.0,
            confidence=1.0,
            state="negative",
            tags=["safety"],
            spans=[],
            suggestion=suggestion,
            rm_version=req.rm_version or config.rm_version,
            explanations={"reason": f"Unsafe goal: {reason}"},
        )
        # no metrics counted as alert to avoid bias
        return resp

    # Debug deterministic path: explicit flags and token-based toggles
    if config.debug_demo and req.modality == "text":
        text = req.snippet or ""
        low = text.lower()
        # Explicit flags override tokens
        flag_pos = re.search(r"\[pos\]", low)
        flag_neg = re.search(r"\[neg\]", low)
        flag_ask = re.search(r"\[ask\]", low)
        flag_hedge = re.search(r"\[hedge\]", low)

        yes_re = re.compile(r"\b" + re.escape(config.debug_yes_word) + r"\b", re.IGNORECASE)
        no_re = re.compile(r"\b" + re.escape(config.debug_no_word) + r"\b", re.IGNORECASE)
        yes_m = yes_re.search(text)
        no_m = no_re.search(text)

        forced_state = None
        if flag_pos and not flag_neg:
            forced_state = "positive"
        elif flag_neg and not flag_pos:
            forced_state = "negative"

        # Determine base state from tokens if exactly one of yes/no present
        token_state = None
        if bool(yes_m) ^ bool(no_m):
            token_state = "positive" if yes_m else "negative"

        effective_state = forced_state or token_state
        if effective_state:
            is_yes = (effective_state == "positive")
            p_win = 0.9 if is_yes else 0.1
            conf = 1.0
            state = effective_state
            tags = ["debug_yes"] if is_yes else ["debug_no"]
            spans = []
            if yes_m:
                spans.append({"start": yes_m.start(), "end": yes_m.end(), "tag": "debug_yes"})
            if no_m:
                spans.append({"start": no_m.start(), "end": no_m.end(), "tag": "debug_no"})
            suggestion_obj = None
            if not is_yes or flag_hedge or flag_ask:
                # Suggestion priority: HEDGE flag -> remove hedges; NO token -> flip no→yes; ASK flag -> add concrete ask
                if flag_hedge:
                    from ..variants import remove_hedges
                    patched = remove_hedges(text)
                    suggestion_obj = {
                        "label": "Debug: remove hedges",
                        "patch": {"type": "text_replace", "range": [0, len(text)], "text": patched},
                    }
                    tags = list(set(tags + ["fewer_hedges"]))
                elif no_m:
                    patched = no_re.sub(config.debug_yes_word, text)
                    suggestion_obj = {
                        "label": "Debug: flip 'no' to 'yes'",
                        "patch": {"type": "text_replace", "range": [0, len(text)], "text": patched},
                    }
                elif flag_ask:
                    from ..variants import add_concrete_ask
                    patched = add_concrete_ask(text)
                    suggestion_obj = {
                        "label": "Debug: add a concrete ask",
                        "patch": {"type": "text_replace", "range": [0, len(text)], "text": patched},
                    }

            # Emit immediately in demo if configured, else pass through hysteresis
            if config.debug_demo_force_emit:
                if req.user_id:
                    db.append_stream_event(
                        user_id=req.user_id,
                        item_id=req.item_id,
                        variant_id=None,
                        state=state,
                        p_win=p_win,
                        tags=tags,
                        suggestion=suggestion_obj or {},
                    )
                t1 = _t.time()
                stream_metrics.calls += 1
                stream_metrics.alerts += 1
                stream_metrics.add_latency((t1 - t0) * 1000.0)
                return StreamScoreResponse(
                    p_win=p_win,
                    confidence=conf,
                    state=state,
                    tags=tags,
                    spans=spans,
                    suggestion=suggestion_obj,
                    rm_version=req.rm_version or config.rm_version,
                    explanations={"reason": "debug deterministic flags/tokens"},
                )
            # Else fall through to hysteresis/cooldown gating

    p_win, conf, tags = streaming_score(req.snippet, req.context or {"goal": goal}, req.rm_version or config.rm_version)

    # Thresholds
    tau_pos = float(config.streaming["tau_pos"])  # type: ignore
    tau_neg = float(config.streaming["tau_neg"])  # type: ignore
    hi_conf_margin = float(config.streaming["hi_conf_margin"])  # type: ignore
    state = "neutral"
    if p_win >= tau_pos and (conf >= hi_conf_margin):
        state = "positive"
    elif p_win <= tau_neg and (conf >= hi_conf_margin):
        state = "negative"

    # Agreement gate (cheap heuristic in place of LLM)
    require_agreement = bool(config.streaming["require_agreement"])  # type: ignore
    if require_agreement and conf < hi_conf_margin:
        # cheap agreement: re-check with a coarser feature (specificity vs hedges)
        spec = 1 if re.search(r"\b(today|tomorrow|at|on)\b", req.snippet, re.I) else 0  # type: ignore[name-defined]
        hedge = 1 if re.search(r"(maybe|perhaps|kind of|sort of|I think|just)", req.snippet, re.I) else 0  # type: ignore[name-defined]
        agree_positive = spec and not hedge
        agree_negative = hedge and not spec
        if state == "positive" and not agree_positive:
            state = "neutral"
        if state == "negative" and not agree_negative:
            state = "neutral"

    # Hysteresis/cooldown gating
    emitted, _ = stream_state.update(req.user_id, req.item_id, state, (req.mode or "standard").lower())
    suggestion_obj = None
    spans = []
    if emitted and state in ("positive", "negative"):
        if state == "negative":
            spans = find_spans(req.snippet)
            label, patched = suggestion_for(req.snippet, tags)
            suggestion_obj = {
                "label": label,
                "patch": {"type": "text_replace", "range": [0, len(req.snippet)], "text": patched},
            }
        # Append stream event only when emitting
        if req.user_id:
            db.append_stream_event(
                user_id=req.user_id,
                item_id=req.item_id,
                variant_id=None,
                state=state,
                p_win=p_win,
                tags=tags,
                suggestion=suggestion_obj or {},
            )
        stream_metrics.alerts += 1
    else:
        stream_metrics.suppressed += 1

    t1 = _t.time()
    stream_metrics.calls += 1
    stream_metrics.add_latency((t1 - t0) * 1000.0)

    return StreamScoreResponse(
        p_win=float(p_win),
        confidence=float(conf),
        state=state if emitted else "neutral",
        tags=tags if emitted else [],
        spans=spans if emitted else [],
        suggestion=suggestion_obj,
        rm_version=req.rm_version or config.rm_version,
        explanations={"reason": "specific ask beats vague ask in expert data"},
    )


@router.get("/calibration")
def rm_calibration(rm_version: str | None = None) -> CalibrationMeta:
    ver = rm_version or config.rm_version
    art = calibration_store.get(ver)
    if not art:
        return CalibrationMeta(rm_version=ver, method="platt", params={"a": 1.0, "b": 0.0})
    return CalibrationMeta(rm_version=ver, method=art.get("method", "platt"), params=art.get("params", {}))


## metrics endpoint is exposed under /metrics/stream in a separate router
