#!/usr/bin/env python3
"""test_orchestrator_standalone.py — orchestrator must boot without _ops/neural.

ARCH-SCAN-01 §8.1 / Forced Completion Sprint 2026-07-20: the only hard coupling
between Project-F and the vault-level Octopus core was orchestrator's import-time
dependency on 6 _ops/neural modules. After the fix, those imports are lazy with
stdlib no-op fallbacks: if the vault is not mounted, the orchestrator still boots,
stays advisory-only, and reports NEURAL_AVAILABLE = False.

Technique: mask the six neural modules in sys.modules (None ⇒ ImportError),
reload orchestrator, exercise it, then restore the real modules.

No PII, no network, stdlib-only. Run from the project root:
    python -m pytest tests/test_orchestrator_standalone.py -q
"""
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
for _p in [str(_PROJ), str(_PROJ / "brain")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

_NEURAL_MODULES = ["neural_driver", "hebbian", "consolidation",
                   "sprint", "hooks", "circadian"]


def _reload_with_neural_masked():
    saved = {}
    for m in _NEURAL_MODULES:
        saved[m] = sys.modules.pop(m, None)
        sys.modules[m] = None  # import <m> ⇒ ImportError
    import orchestrator
    importlib.reload(orchestrator)
    return orchestrator, saved


def _restore(saved):
    for m, mod in saved.items():
        if mod is None:
            sys.modules.pop(m, None)
        else:
            sys.modules[m] = mod
    import orchestrator
    importlib.reload(orchestrator)


def test_orchestrator_boots_and_ticks_without_neural(tmp_path, monkeypatch):
    monkeypatch.setenv("PF_STUDIO_DIR", str(tmp_path))
    orch_mod, saved = _reload_with_neural_masked()
    try:
        assert orch_mod.NEURAL_AVAILABLE is False
        monkeypatch.setattr(orch_mod, "_BRAIN_STATE", tmp_path)
        orch = orch_mod.PFOrchestrator(
            studio=SimpleNamespace(draft_count=0),
            acquisition=SimpleNamespace(
                memory=SimpleNamespace(learning_confidence=lambda: 0.0,
                                       tag_performance=lambda: {})),
            data_dir=tmp_path)
        result = orch.tick()
        # tick سالم برمی‌گردد؛ advisory-only می‌ماند؛ mode یکی از حالت‌های شناخته است
        assert result.advisory_only is True
        assert result.mode in ("normal", "throttled", "protective",
                               "blocked_compliance")
        st = orch.status()
        assert st["neural_available"] is False
        assert "compliance_ok" in st
    finally:
        _restore(saved)


def test_neural_restored_after_mask():
    """Sanity: after restore, orchestrator sees the real vault modules again
    (in this worktree _ops/neural exists, so NEURAL_AVAILABLE must be True)."""
    import orchestrator
    assert orchestrator.NEURAL_AVAILABLE is True
