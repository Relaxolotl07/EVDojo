from backend.app.rm import SimpleTextRM


def test_rm_pairwise_loss_direction():
    rm = SimpleTextRM(tags=["clearer_ask", "fewer_hedges"])
    a = rm.features({"words": 10, "hedges": 0, "specificity_markers": 1})
    b = rm.features({"words": 20, "hedges": 3, "specificity_markers": 0})
    p0 = rm.pairwise_prob(a, b)
    for _ in range(100):
        rm.train_pair(a, b, ya=1.0, lr=0.05)
    p1 = rm.pairwise_prob(a, b)
    assert p1 > p0

