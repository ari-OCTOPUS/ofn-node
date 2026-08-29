from octopus_cognition.metacontrol.skill import DomainSkillTracker


def test_insufficient_samples_before_world_model_outcomes():
    tracker = DomainSkillTracker(minimum=50)
    report = tracker.report()
    assert report.eligible is False
    assert report.reason == "insufficient_samples"
    assert report.score is None


def test_zero_losses_are_no_advantage():
    tracker = DomainSkillTracker(minimum=50)
    for _ in range(50):
        tracker.record(0.0, 0.0)
    report = tracker.report()
    assert report.score == 0.0
    assert report.eligible is False
    tracker = DomainSkillTracker(minimum=50)
    for _ in range(50):
        tracker.record(0.001, 0.001)
    report = tracker.report()
    assert report.samples == 50
    assert report.score is not None
    assert report.score == 0.0
    assert report.eligible is False
    assert report.reason == "not_better_than_baseline"


def test_positive_skill_lower_bound():
    tracker = DomainSkillTracker(minimum=50)
    for _ in range(50):
        tracker.record(0.001, 0.010)
    report = tracker.report()
    assert report.eligible is True
    assert report.lower_bound is not None and report.lower_bound > 0
    assert report.reason == "skill_confirmed"


def test_shuffled_worse_than_baseline_denies():
    tracker = DomainSkillTracker(minimum=50)
    for _ in range(50):
        tracker.record(0.050, 0.001)
    report = tracker.report()
    assert report.eligible is False
    assert report.score is not None and report.score < 0
