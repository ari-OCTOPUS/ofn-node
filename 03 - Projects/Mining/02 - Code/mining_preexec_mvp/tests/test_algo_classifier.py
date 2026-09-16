from mining_preexec_mvp.algo_classifier import classify_algorithm


def test_yespower_is_arm_viable():
    a = classify_algorithm("yespower")
    assert a.arm_viable
    assert a.category == "cpu_arm_preferred"


def test_kheavyhash_is_not_arm_cpu_target():
    a = classify_algorithm("kHeavyHash")
    assert not a.arm_viable
    assert a.risk.value == "red"


def test_unknown_requires_review():
    a = classify_algorithm("NewMysteryAlgo")
    assert not a.arm_viable
    assert a.risk.value == "orange"
