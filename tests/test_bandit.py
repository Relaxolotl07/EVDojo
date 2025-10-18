from backend.app.bandit import pick_next_duel


def test_pick_next_duel_differs():
    vids = ["v1", "v2", "v3"]
    scores = {"v1": (0.2, 0.5), "v2": (0.1, 0.9), "v3": (-0.1, 0.6)}
    a, b = pick_next_duel(vids, scores)
    assert a != b

