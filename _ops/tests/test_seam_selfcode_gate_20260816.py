"""test_seam_selfcode_gate_20260816.py — SEAM-LOOP C5 / C-026 (تست منفی، طبق مگاپرامپت 0.5).

درز (C-026): approve()/reject() در 4d_system/brain/self_code.py گیتِ enabled()
را چک نمی‌کنند — پیشنهادِ ساخته‌شده حین ON، بعد از OFF شدن فلگ هم
approve/apply-پذیر می‌ماند (پایین‌دست TCB/stale/suite هنوز محافظ‌اند؛ گپ =
گیت ورودی).

طبق مأموریت: رفتار تولید عوض نمی‌شود مگر رأی مالک بیاید — این تست شکست را
«قفل» می‌کند: دو xfail سخت‌گیر (strict) که با پیام C-026 در هر اجرا دیده
می‌شوند؛ لحظه‌ای کسی گیت را اضافه کند، XPASS-strict تست را قرمز می‌کند تا
نشانگر به positive منتقل شود (گap ناپدیدشدنی).
"""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "4d_system" / "brain" / "self_code.py"


def _fn_calls_enabled(fn_name: str) -> bool:
    tree = ast.parse(SRC.read_text("utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                       and n.func.id == "enabled" for n in ast.walk(node))
    return False


@pytest.mark.xfail(strict=True, reason="C-026: گیت enabled() در approve نیست — رأی مالک در انتظار")
def test_approve_gated_by_enabled():
    assert _fn_calls_enabled("approve"), "approve باید enabled() را در ورودی چک کند"


@pytest.mark.xfail(strict=True, reason="C-026: گیت enabled() در reject نیست — رأی مالک در انتظار")
def test_reject_gated_by_enabled():
    assert _fn_calls_enabled("reject"), "reject باید enabled() را در ورودی چک کند"


def test_enabled_guard_exists_and_reads_flag():
    """قفل مثبت: نگهبانِ اصلی تعریف است و فلگ SELF_CODE_ENABLED می‌خواند."""
    src = SRC.read_text("utf-8")
    assert "def enabled(" in src
    assert "SELF_CODE_ENABLED" in src
