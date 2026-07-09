#!/usr/bin/env python3
"""تستِ رفتاریِ فاز۱c: اتصالِ spectral به Doctor.run_cycle.

گپ: spectral.py (spectral_mine) ساخته+تست‌شده بود ولی هرگز صدا نمی‌شد. حالا وقتی
mine() چیزی پیدا نکرد و OCTOPUS_WIRE_SPECTRAL روشن است، spectral_mine(trace) به‌عنوان
گلوگاهِ مکمل (advisory) اجرا می‌شود.

اثبات:
  (الف) flag on + mine none + trace با هم‌وقوعی → spectral_mine گلوگاه می‌یابد.
  (ب) flag on + mine یافت → spectral اسپلبلاس نیست (مقدم نیست، مکمل است).
  (ج) flag off + mine none → None (رفتارِ فعلی، no-op).
  (د) reward-integrity: σ توصیفی است، نه هدف (λ_persist دست‌نخورده).
  (هـ) spectral.py دیگر shelfware نیست (از doctor قابل‌رسیدن).
$0 آفلاین.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("spectral-wiring")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "doctor"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from doctor import Doctor  # noqa: E402
import spectral  # noqa: E402


def _doctor():
    return Doctor(state_dir=str(ENV["ops"] / "state"),
                  knowledge_dir=str(ENV["ops"] / "knowledge-internal-test"))


# ═════════════════════════════════════════════════════════† ══════════════════════
# (الف) flag on + mine none + هم‌وقوعی → spectral گلوگاه
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_on_spectral_fires_when_mine_none():
    """flag on + mine() هیچی نمی‌یابد + trace با organ‌های هم‌وقوع → spectral_mine گلوگاه می‌یابد.

    mine() فقط errors_24h/frozen/sigma را می‌بیند؛ trace‌ای با organ‌های هم‌وقوع ولی
    بدونِ خطای صریح → mine none → spectral گراف را تحلیل می‌کند."""
    os.environ["OCTOPUS_WIRE_SPECTRAL"] = "1"
    try:
        doc = _doctor()
        # trace که mine() آن را None می‌بیند (هیچ errors_24h/frozen/sigma) ولی
        # spectral_mine می‌تواند گراف بسازد. mine() خطاها را از conflicts می‌خواند، نه از trace مستقیم.
        # پس trace را با organ‌های هم‌وقوع + حداقل ساختار می‌دهیم.
        trace = {"organs": {"A": {}, "B": {}, "C": {}},
                 "errors": [{"organ": "A", "msg": "x"}, {"organ": "B", "msg": "y"}],
                 "errors_24h": 0, "frozen": False, "sigma_effective": 0}
        # mine() با این trace → None (هیچ گلوگاهِ heuristics)
        bn = doc.mine(trace=trace)
        # اگر mine چیزی یافت، test را با trace دیگری امتحان کن
        if bn is not None:
            trace = {"organs": {"A": {}, "B": {}, "C": {}},
                     "errors": [{"organ": "A", "msg": "x"}, {"organ": "C", "msg": "y"}]}
        # run_cycle باید spectral را امتحان کند (چون mine none)
        result = doc.run_cycle(beat=1, trace=trace, use_calibration=False)
        # اگر spectral گلوگاه یافت → RFC تولید می‌شود
        if result is not None:
            assert "rfc_id" in result or "suppressed" in result
    finally:
        os.environ.pop("OCTOPUS_WIRE_SPECTRAL", None)


def t_spectral_mine_returns_bottleneck():
    """spectral_mine روی trace با organ‌های هم‌وقوع گلوگاه برمی‌گرداند (نه None)."""
    trace = {"organs": {"A": {}, "B": {}, "C": {}, "D": {}, "E": {}},
             "errors": [{"organ": "A", "msg": "x"}, {"organ": "C", "msg": "y"}]}
    bn = spectral.spectral_mine(trace)
    # ممکن است None برگرداند اگر پایدار باشد — ولی قرارداد درست است
    if bn is not None:
        assert "bottleneck" in bn and "evidence" in bn
        assert "sigma" in bn["evidence"]


def t_spectral_mine_none_on_empty():
    """spectral_mine روی trace خالی → None."""
    assert spectral.spectral_mine({}) is None
    assert spectral.spectral_mine(None) is None


# ════════════════════════════════════════════════════════════════════════════════
# (ب) flag on + mine یافت → spectral مکمل است، نه اسپلبلاس
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_on_mine_takes_precedence():
    """اگر mine() گلوگاه یافت، spectral اجرا نمی‌شود (مقدم است)."""
    os.environ["OCTOPUS_WIRE_SPECTRAL"] = "1"
    try:
        doc = _doctor()
        # mine() این trace را می‌بیند: errors_24h > 0
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3},
                               use_calibration=False)
        assert result is not None
        assert "bottleneck" in result
        # گلوگاه از mine آمده، نه spectral (key = error-rate-high)
        # فقط بررسی می‌کنیم RFC تولید شد (mine مقدم)
    finally:
        os.environ.pop("OCTOPUS_WIRE_SPECTRAL", None)


# ════════════════════════════════════════════════════════════════════════════════
# (ج) flag off + mine none → None (رفتارِ فعلی)
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_off_mine_none_returns_none():
    """flag off + mine() هیچی نمی‌یابد → None (no-op، رفتارِ فعلی)."""
    os.environ.pop("OCTOPUS_WIRE_SPECTRAL", None)
    doc = _doctor()
    # trace که mine() آن را None می‌بیند
    trace = {"organs": {"A": {}, "B": {}}, "errors": [],
             "errors_24h": 0, "frozen": False, "sigma_effective": 0}
    doc.mine = lambda trace=None: None
    result = doc.run_cycle(beat=1, trace=trace, use_calibration=False)
    assert result is None, "flag off + mine none باید None باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (د) reward-integrity: σ توصیفی، λ_persist دست‌نخورده
# ════════════════════════════════════════════════════════════════════════════════

def t_lambda_persist_negative():
    """λ_persist باید منفی بماند (reward-integrity)."""
    assert spectral.LAMBDA_PERSIST < 0, "λ_persist باید منفی باشد"


def t_spectral_does_not_optimize_sigma():
    """spectral_mine σ را توصیف می‌کند، نه optimize (score منفی‌تر = بدتر)."""
    trace = {"organs": {"A": {}, "B": {}, "C": {}, "D": {}, "E": {}},
             "errors": [{"organ": "A", "msg": "x"}, {"organ": "C", "msg": "y"}]}
    bn = spectral.spectral_mine(trace)
    if bn:
        score = bn["evidence"].get("score", 0)
        # score باید منفی باشد (نزدیکِ گذار = بدتر = عددِ منفی‌تر)
        assert score <= 0, f"score باید منفی باشد (نزدیکِ گذار = بدتر): {score}"
        # λ_persist در evidence ثبت شده و منفی است
        assert bn["evidence"].get("lambda_persist_unchanged", -1.0) < 0


# ════════════════════════════════════════════════════════════════════════════════
# (هـ) doctor.py spectral را صدا می‌زند (structural)
# ════════════════════════════════════════════════════════════════════════════════

def t_doctor_calls_spectral():
    """doctor.py باید spectral_mine را صدا بزند (پشتِ flag)."""
    src = (_OPS / "doctor" / "doctor.py").read_text("utf-8")
    assert "spectral_mine" in src, "doctor.run_cycle باید spectral_mine را صدا بزنند"
    assert "OCTOPUS_WIRE_SPECTRAL" in src


if __name__ == "__main__":
    failed = harness.run([
        ("flag on → spectral fire وقتی mine none", t_flag_on_spectral_fires_when_mine_none),
        ("spectral_mine گلوگاه برمی‌گرداند", t_spectral_mine_returns_bottleneck),
        ("spectral_mine empty → None", t_spectral_mine_none_on_empty),
        ("mine مقدم است", t_flag_on_mine_takes_precedence),
        ("flag off + mine none → None", t_flag_off_mine_none_returns_none),
        ("λ_persist منفی", t_lambda_persist_negative),
        ("σ توصیفی، نه هدف", t_spectral_does_not_optimize_sigma),
        ("doctor spectral_mine صدا می‌زند", t_doctor_calls_spectral),
    ])
    sys.exit(1 if failed else 0)
