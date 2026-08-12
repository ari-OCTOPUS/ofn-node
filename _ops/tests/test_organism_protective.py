#!/usr/bin/env python3
"""تست S — ADR-034/035 dual-mode protective skip.

(۱) APPLY=0: pain>0.7 → protective_proposal, override=False, executable=False.
(۲) ساختاری: organism/brain_worker فقط با executable gate skip می‌گذارند.
(۳) epoch/fitness هنوز روی not _protective_skip گیت‌اند.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("organism-protective")
sys.path.insert(0, str((harness.SELF_OPS)))
sys.path.insert(0, str((harness.SELF_OPS / "budget")))
os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
import wiring  # noqa: E402

ORG = (harness.SELF_OPS / "organism.py").read_text("utf-8")
BW = (harness.SELF_OPS / "brain_worker.py").read_text("utf-8")
_BODY = ORG[ORG.index("while True:"):]


def t_protective_proposal_not_halt():
    r = wiring.protective_override({"pain": {"level": 0.85}, "reflexes": []})
    assert r["override"] is False and r["executable"] is False, r
    assert r["action"] == "protective_proposal", r
    assert r.get("shadow_alert") is True, r


def t_low_pain_no_override():
    r = wiring.protective_override({"pain": {"level": 0.1}, "reflexes": []})
    assert r["override"] is False and r["action"] == "none", r


def t_critical_reflex_proposal_only():
    r = wiring.protective_override({"pain": {"level": 0.0},
                                   "reflexes": [{"triggered": True, "severity": "critical", "name": "budget"}]})
    assert r["override"] is False and r["executable"] is False, r
    assert r["action"] == "throttle_proposal", r


def t_epoch_gated_on_protective_skip():
    assert re.search(r"if not _protective_skip[^\n]*:\s*\n\s+rec = governor_epoch\.run_epoch\(\)", _BODY), \
        "epoch باید روی `not _protective_skip` گیت باشد (flag واقعاً مصرف شود)"


def t_fitness_gated_on_protective_skip():
    assert re.search(r"if not _protective_skip[^\n]*:\s*\n\s+fit = fitness\.compute\(\)", _BODY), \
        "fitness/daily باید روی `not _protective_skip` گیت باشد"


def t_neural_skip_requires_executable_gate():
    assert 'get("executable")' in ORG and 'get("executable")' in BW
    assert '_protective_skip = True' in ORG
    assert 'self.protective_skip = True' in BW
    assert ORG.index('get("executable")') < ORG.index('_protective_skip = True')


def t_neural_emits_shadow_alert_only():
    assert "SHADOW_ALERT neural" in ORG and "SHADOW_ALERT neural" in BW
    assert "pain_assessment" in ORG and "pain_assessment" in BW
    assert "NEURAL OVERRIDE" in ORG and "NEURAL OVERRIDE" in BW


def t_no_busyloop_continue():
    assert not re.search(r"\n\s+continue\b", _BODY), "continue در tick ممنوع (busy-loop)"


def t_sleep_always_reached():
    assert re.search(r"\n        time\.sleep\(", ORG), \
        "time.sleep باید همیشه انتهای while اجرا شود (busy-loop ban)"


if __name__ == "__main__":
    failed = harness.run([
        ("pain>0.7 → protective_proposal (نه halt)", t_protective_proposal_not_halt),
        ("pain پایین → بدونِ override", t_low_pain_no_override),
        ("reflex بحرانی → throttle_proposal", t_critical_reflex_proposal_only),
        ("epoch روی not _protective_skip گیت (flag مصرف)", t_epoch_gated_on_protective_skip),
        ("fitness روی not _protective_skip گیت", t_fitness_gated_on_protective_skip),
        ("neural skip فقط با executable", t_neural_skip_requires_executable_gate),
        ("neural SHADOW + OVERRIDE paths", t_neural_emits_shadow_alert_only),
        ("بدونِ continue (busy-loop ban)", t_no_busyloop_continue),
        ("time.sleep همیشه اجرا می‌شود", t_sleep_always_reached),
    ])
    sys.exit(1 if failed else 0)
