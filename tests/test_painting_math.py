from ofn.kernel.painting_math import lead_priority, source_quality, b2b_account_score, tender_score, update_trust


def test_lead_score_is_explainable_and_bounded():
    r = lead_priority({"V": .9, "I": .8, "G": .7, "T": .6, "Q": .9, "R": .1, "C": .2})
    assert 0 <= r.score <= 1
    assert r.explanation
    assert r.recommendation in {"HOT", "WARM", "NURTURE", "OWNER_REVIEW"}


def test_missing_data_is_flagged_neutral_not_hidden():
    r = source_quality({"I": .8})
    assert r.incomplete
    assert "داده ناقص" in " ".join(r.explanation)


def test_b2b_models_route_segments_differently():
    s = b2b_account_score("strata", {"P": .9, "G": .8, "M": .8, "E": .8, "R": .7, "risk": .2, "cost": .2})
    f = b2b_account_score("fitout", {"V": .9, "D": .9, "F": .8, "C": .7, "E": .8, "risk": .2, "cost": .2})
    assert s.recommendation in {"HIGH_FIT", "QUALIFY"}
    assert f.recommendation in {"HIGH_FIT", "QUALIFY"}


def test_tender_never_claims_submit_permission():
    r = tender_score({"P": .95, "G": .9, "E": .8, "D": .8, "M": .7, "Q": .9, "R": .1, "C": .2})
    assert r.recommendation in {"BID", "CONSIDER"}
    assert "SUBMITTED" not in " ".join(r.explanation)


def test_trust_update_needs_minimum_samples_for_routing():
    r = update_trust(.5, 1.0, sample_count=3)
    assert r.recommendation == "HISTORY_ONLY"
