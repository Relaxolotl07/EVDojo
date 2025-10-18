from backend.app.streaming import streaming_score, find_spans


def test_streaming_score_basic():
    text = "hey maybe we could meet"
    p, conf, tags = streaming_score(text, {"goal": "ask clearly"}, "v1")
    assert 0.0 <= p <= 1.0
    assert 0.0 <= conf <= 1.0


def test_find_spans_hedges():
    text = "I think we could maybe meet"
    spans = find_spans(text)
    assert any(s["tag"] == "hedge" for s in spans)

