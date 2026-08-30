"""test_hebbian_cockpit_tab.py — ۲۰۲۶-۰۸-۰۵: تبِ «brain/hebbian» با هر تپ کرش می‌کرد.

`read_hebbian()` فایلِ خامِ hebbian.json را می‌خواند که یک **لیست** است
(`[{signals,strength,co_occurrences,last_seen}, ...]`)، نه دیکشنری. کدِ قبلی
`h.get('pairs', h)` می‌زد که روی لیست `AttributeError` می‌داد — سنجیده مستقیم روی
پایگاهِ زنده، نه از رویِ کد. `_dispatch_card` این را fail-soft می‌کرد به «❌ خطای
رندرِ کارت»، پس هیچ‌وقت به‌عنوانِ کرش دیده نمی‌شد؛ فقط کارتی که همیشه خطا می‌داد.
"""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("hebbian_cockpit_tab")

from approval_channel import TelegramApprovalChannel  # noqa: E402


def _chan(ops_dir):
    # `_rm()` خودش ops_dir را از parentِ state_dir مشتق می‌کند (C8) — پس
    # همان ریشه را برای state_dir می‌دهیم تا neural/hebbian.json زیرِ
    # همین ops_dir قرار بگیرد.
    return TelegramApprovalChannel(state_dir=str(Path(ops_dir) / "state"))


def _write_hebbian(ops_dir, rows):
    p = Path(ops_dir) / "neural"
    p.mkdir(parents=True, exist_ok=True)
    (p / "hebbian.json").write_text(json.dumps(rows), encoding="utf-8")


def t_a_no_file_shows_empty_not_a_crash():
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        out = ch._render_card("brain", "hebbian")
        assert "خطای رندر" not in out, out
        assert "بی‌فایل" in out, out


def t_b_real_rows_show_signal_names_and_strength():
    """قرارداد: پیش از رفع، همین ورودی AttributeError می‌داد."""
    with tempfile.TemporaryDirectory() as td:
        _write_hebbian(td, [
            {"signals": ["errors_high", "rhythm_amber"], "strength": 0.786,
             "co_occurrences": 20, "last_seen": 1785904233.0},
            {"signals": ["alpha", "beta"], "strength": 0.036,
             "co_occurrences": 2, "last_seen": 1785850801.0},
        ])
        ch = _chan(td)
        out = ch._render_card("brain", "hebbian")
        assert "خطای رندر" not in out, out
        assert "errors_high" in out and "rhythm_amber" in out, out
        assert "0.79" in out or "0.78" in out, out          # گردشده به دو رقم
        assert "20" in out, out                              # هم‌رخداد


def t_c_strongest_pair_sorts_first():
    with tempfile.TemporaryDirectory() as td:
        _write_hebbian(td, [
            {"signals": ["weak_a", "weak_b"], "strength": 0.05, "co_occurrences": 1},
            {"signals": ["strong_a", "strong_b"], "strength": 0.9, "co_occurrences": 50},
        ])
        ch = _chan(td)
        out = ch._render_card("brain", "hebbian")
        assert out.index("strong_a") < out.index("weak_a"), out


def t_d_malformed_rows_are_skipped_not_fatal():
    """رکوردِ ناقص/بدشکل نباید کلِ کارت را بترکاند — فقط رد شود."""
    with tempfile.TemporaryDirectory() as td:
        _write_hebbian(td, [
            {"signals": ["only_one"], "strength": 0.5},   # signals با طولِ ۱ — بدشکل
            "not-a-dict-at-all",
            {"signals": ["ok_a", "ok_b"], "strength": 0.4, "co_occurrences": 3},
        ])
        ch = _chan(td)
        out = ch._render_card("brain", "hebbian")
        assert "خطای رندر" not in out, out
        assert "ok_a" in out, out
        assert "1 جفت" in out, out          # فقط ردیفِ سالم شمرده شود


if __name__ == "__main__":
    for f in (t_a_no_file_shows_empty_not_a_crash, t_b_real_rows_show_signal_names_and_strength,
              t_c_strongest_pair_sorts_first, t_d_malformed_rows_are_skipped_not_fatal):
        f()
        print("ok", f.__name__)
    print("PASS test_hebbian_cockpit_tab")
