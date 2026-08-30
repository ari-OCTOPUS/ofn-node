from mining_preexec_mvp.models import CoinCandidate
from mining_preexec_mvp.scout import score_candidate


def test_candidate_score_yespower():
    c = CoinCandidate(
        symbol="TST",
        name="Test",
        algorithm="yespower",
        launch_age_days=10,
        network_hashrate_hs=1_000_000,
        block_reward=50,
        blocks_per_day=1440,
        dev_activity_notes="recent commits",
        community_notes="active ANN",
    )
    s = score_candidate(c)
    assert s["arm_viable"] is True
    assert s["score"] >= 70


def test_candidate_reject_gpu_algo():
    c = CoinCandidate(symbol="KAS", name="Kaspa", algorithm="kHeavyHash")
    s = score_candidate(c)
    assert s["arm_viable"] is False
    assert s["risk"] == "red"
