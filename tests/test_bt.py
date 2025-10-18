from backend.app.bt import BradleyTerry


def test_bt_update_pushes_scores():
    bt = BradleyTerry()
    a, b = "va", "vb"
    for _ in range(20):
        bt.update(a, b, a, rater_id=None, lr=0.2)
    sa, _ = bt.scores[a]
    sb, _ = bt.scores[b]
    assert sa > sb

