"""test_organ_create.py — Wave 2 (2026-07-15): ساختِ اندامِ نو (data-driven، دو-مرحله‌ای).
اثباتِ کلیدی: هیچ کدِ تولید نوشته نمی‌شود — فقط یک ورودی در state/organ-registry.json."""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("organ_create")

from approval_channel import TelegramApprovalChannel  # noqa: E402


def _chan(sd):
    return TelegramApprovalChannel(state_dir=str(sd))


def t_a_propose_then_approve_writes_registry_only():
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        r1 = ch.handle_command("/neworgan Woo Shop")
        assert isinstance(r1, str) and "woo-shop" in r1 and "/organ-approve" in r1
        assert (Path(td) / "organ-proposals" / "woo-shop.json").exists()
        assert not (Path(td) / "organ-registry.json").exists()   # هنوز رجیستری نه
        r2 = ch.handle_command("/organ-approve woo-shop")
        assert "ساخته شد" in r2
        reg = json.loads((Path(td) / "organ-registry.json").read_text("utf-8"))
        assert "woo-shop" in [o["key"] for o in reg["organs"]]
        assert reg["organs"][0]["live"] is False              # اسکلت
        assert not (Path(td) / "organ-proposals" / "woo-shop.json").exists()  # مصرف‌شده


def t_b_organs_tab_lists_custom():
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        ch.handle_command("/neworgan Test Organ X")
        ch.handle_command("/organ-approve test-organ-x")
        out = ch.handle_command("/organs")
        assert "Test Organ X" in out["text"] and "owner-ساخت: 1" in out["text"]


def t_c_approve_without_proposal_refused():
    with tempfile.TemporaryDirectory() as td:
        assert "نیست" in _chan(td).handle_command("/organ-approve ghost")


def t_d_duplicate_refused():
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        ch.handle_command("/neworgan Dup")
        ch.handle_command("/organ-approve dup")
        assert "از قبل" in ch.handle_command("/neworgan Dup")


def t_e_short_name_refused():
    with tempfile.TemporaryDirectory() as td:
        assert "کوتاه" in _chan(td).handle_command("/neworgan x")


def t_f_no_production_code_written():
    """قویترین گارد: ساختِ اندام هیچ .py نمی‌نویسد — فقط دادهٔ state."""
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        ch.handle_command("/neworgan Safe Check")
        ch.handle_command("/organ-approve safe-check")
        assert list(Path(td).rglob("*.py")) == []


if __name__ == "__main__":
    for f in (t_a_propose_then_approve_writes_registry_only, t_b_organs_tab_lists_custom,
              t_c_approve_without_proposal_refused, t_d_duplicate_refused,
              t_e_short_name_refused, t_f_no_production_code_written):
        f()
        print("ok", f.__name__)
    print("PASS test_organ_create")
