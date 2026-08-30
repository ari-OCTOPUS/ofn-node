# -*- coding: utf-8 -*-
"""T27 extra: no money path, no scheduler, credits_to_aud not called."""
from pathlib import Path
import ast

_OPS = Path(__file__).resolve().parents[1]
PKG = _OPS / "shadow_homeostasis"


def test_no_money_or_scheduler_strings_as_imports():
    text = "\n".join(p.read_text("utf-8") for p in PKG.glob("*.py"))
    assert "credits_to_aud" not in text
    assert "model_router" not in text
    assert "schtasks" not in text
    assert "crontab" not in text
    assert "import organism" not in text
    assert "from organism" not in text
