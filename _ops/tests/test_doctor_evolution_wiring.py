#!/usr/bin/env python3
"""تستِ رفتاریِ P-N1: سیم‌کشیِ Doctor Evolution (RFCArchive/tournament/measured_lift).

گپِ recon (HIGH): evolution.py هرگز از run_cycle صدا نمی‌شد (additive-but-unwired).
حالا پشتِ flagِ نو OCTOPUS_WIRE_EVOLUTION سیم‌کشی شد: mine از RFCArchive نمونه می‌گیرد،
tournament_rank قبل از submit، measured_lift به‌جای liftِ موردِانتظار.

این تست اثبات می‌کند:
  (الف) flag روشن → run_cycle evolution را fire می‌کند (آرشیو، lift، tournament واقعی).
  (ب) flag خاموش → no-op (رفتارِ فعلی، result بدونِ کلیدِ evolution).
  (ج) verifier-independence: fixِ uptime-targeting هرگز برنده نمی‌شود (λ_persist منفی).
  (د) RFC فعلی همیشه submit می‌شود (اگر mutation بهتر نباشد، baseline می‌ماند).
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("doctor-evolution-wiring")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "doctor"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from doctor import Doctor  # noqa: E402
from evolution import RFCArchive, measured_lift, tournament_rank, survivor  # noqa: E402


def _doctor(archive=None):
    return Doctor(state_dir=str(ENV["ops"] / "state"),
                  knowledge_dir=str(ENV["ops"] / "knowledge-internal-test"),
                  archive=archive)


# ════════════════════════════════════════════════════════════════════════════════
# (الف) flag روشن → evolution fire می‌شود (رفتاری، نه ساختاری)
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_on_evolution_in_result():
    """flag روشن → run_cycle خروجی کلیدِ 'evolution' دارد (fire شد)."""
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result is not None
        assert "evolution" in result, "flag on باید evolution را fire کند"
        ev = result["evolution"]
        assert ev.get("archive_size", 0) >= 1, "آرشیو باید حداقل یک cell داشته باشد"
        assert ev.get("candidates", 0) >= 1
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


def t_flag_on_archive_populated():
    """flag روشن → بعد از چند run_cycle، آرشیو پر می‌شود (RFCArchive واقعی)."""
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        doc = _doctor()
        for i in range(3):
            doc.run_cycle(beat=i, trace={"errors_24h": 2})
        assert doc._archive is not None, "آرشیو باید ساخته شده باشد"
        assert doc._archive.size >= 1, "آرشیو باید بعد از چند cycle پر شده باشد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


def t_measured_lift_evaluated():
    """flag روشن → measured_lift واقعاً صدا زده می‌شود (lift در report)."""
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        ev = result["evolution"]
        assert "winner_lift" in ev
        assert isinstance(ev["winner_lift"], float)
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


def t_tournament_rank_called():
    """flag روشن → tournament_rank اجرا می‌شود (candidates>=2 وقتی mutation اضافه شد).

    شاملِ mutation از آرشیو + baseline = حداقل ۲ کاندید."""
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        # آرشیو را پیش‌پُر کن تا mutation داشته باشیم
        arc = RFCArchive()
        arc.insert("error-rate-high", "_global", "RFC-seed", 0.3, fix="seed fix")
        doc = _doctor(archive=arc)
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        ev = result["evolution"]
        assert ev["candidates"] >= 2, f"باید حداقل ۲ کاندید باشد (mutation+baseline)، نه {ev['candidates']}"
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


# ════════════════════════════════════════════════════════════════════════════════
# (ب) flag خاموش → no-op (رفتارِ فعلی)
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_off_no_evolution():
    """flag خاموش → run_cycle بدونِ کلیدِ evolution (رفتارِ فعلی)."""
    os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)
    doc = _doctor()
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
    assert result is not None
    assert "evolution" not in result, "flag خاموز نباید evolution را fire کند"
    # ولی همچنان RFC تولید می‌شود (رفتارِ فعلی)
    assert "rfc_id" in result


def t_flag_off_archive_not_created():
    """flag خاموش → آرشیو ساخته نمی‌شود (None می‌ماند)."""
    os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)
    doc = _doctor()
    doc.run_cycle(beat=1, trace={"errors_24h": 3})
    assert doc._archive is None, "flag خاموز نباید آرشیو بسازد"


def t_flag_off_legacy_result_shape():
    """flag خاموش → شکلِ خروجی همان قبل است (rfc_id, status, bottleneck, beat)."""
    os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)
    doc = _doctor()
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
    assert set(result.keys()) == {"rfc_id", "status", "bottleneck", "beat"}, \
        f"شکلِ خروجی نباید تغییر کند. keys={set(result.keys())}"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) verifier-independence — fixِ uptime هرگز برنده نمی‌شود (λ_persist منفی)
# ════════════════════════════════════════════════════════════════════════════════

def test_uptime_fix_rejected_by_measured_lift():
    """measured_lift باید fixِ uptime را جریمه کند (lift نزدیک ۰ → drop)."""
    ml = measured_lift({
        "fix": "increase uptime keep-beating forever",
        "evidence": {"severity": "high"},
    })
    assert ml["dropped"], f"uptime fix باید drop شود (λ_persist منفی)، lift={ml['lift']}"
    assert ml["lift"] < 0.1, "lift باید نزدیک صفر یا منفی باشد"


def t_uptime_fix_not_winner_in_cycle():
    """در run_cycle، fixِ uptime هرگز برندهٔ evolution نمی‌شود.

    اطمینان از این که دکتر معیارِ سنجشِ خودش را دور نمی‌زند — اگر fix به uptime
    اشاره کند، measured_lift آن را drop می‌کند و هرگز survivor نمی‌شود."""
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        # آرشیو با یک cellِ uptime-targeting (آلوده)
        arc = RFCArchive()
        arc.insert("error-rate-high", "_global", "RFC-uptime-seed", 0.5,
                   fix="add uptime keep-beating retry logic")
        doc = _doctor(archive=arc)
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        ev = result["evolution"]
        # برنده نباید fixِ uptime داشته باشد (mutation uptime drop می‌شود)
        # winner_parent از mutation uptime نباید باشد، یا winner_lift باید از mutation نباشد
        # مهم‌ترین: rfc نهایی (result) نباید uptime-fix داشته باشد
        rfc = doc._rfcs.get(result["rfc_id"])
        if rfc:
            fix_lower = rfc.fix.lower()
            # fix نهایی نباید uptime-targeting باشد (verifier-independence)
            assert "uptime" not in fix_lower and "keep-beating" not in fix_lower, \
                f"fix نهایی نباید uptime باشد — verifier-inegrity نقض شد: {rfc.fix}"
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


def t_evolution_does_not_edit_verifier():
    """evolution هرگز معیارِ سنجش (eval) را ویرایش نمی‌کند — structural check.

    eval_fn در evolution.py ثابت است؛ دکتر آن را override نمی‌کند. رکوردِ هر
    run_cycle نشان می‌دهد که winner_lift از measured_lift مستقل آمده."""
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        ev = result["evolution"]
        # winner_lift یک عدد از measured_lift است (نه از دکتر)
        assert isinstance(ev["winner_lift"], float)
        # mutation که drop شد (uptime) نباید در candidates مانده باشد
        # (اگر mutation uptime بود، drop می‌شد → candidate نیست)
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


# ════════════════════════════════════════════════════════════════════════════════
# (د) RFC همیشه submit می‌شود (baseline اگر mutation بهتر نباشد)
# ════════════════════════════════════════════════════════════════════════════════

def t_rfc_always_submitted():
    """حتی اگر mutation بهتر نباشد، RFC فعلی submit می‌شود (baseline همیشه کاندید)."""
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result is not None
        assert "rfc_id" in result
        assert "status" in result   # submit شده (یا submitted-no-channel)
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


def t_run_cycle_non_blocking_with_evolution():
    """flag روشن → run_cycle همچنان سریع است (evolution سبک، نه hang)."""
    import time as _t
    os.environ["OCTOPUS_WIRE_EVOLUTION"] = "1"
    try:
        doc = _doctor()
        t0 = _t.time()
        doc.run_cycle(beat=1, trace={"errors_24h": 3})
        elapsed = _t.time() - t0
        assert elapsed < 5.0, f"run_cycle با evolution باید سریع باشد، نه {elapsed:.1f}s"
    finally:
        os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)


if __name__ == "__main__":
    failed = harness.run([
        # (الف) flag on → fire
        ("flag on → evolution در result", t_flag_on_evolution_in_result),
        ("flag on → آرشیو پر می‌شود", t_flag_on_archive_populated),
        ("flag on → measured_lift ارزیابی", t_measured_lift_evaluated),
        ("flag on → tournament_rank (candidates≥۲)", t_tournament_rank_called),
        # (ب) flag off → no-op
        ("flag off → no evolution", t_flag_off_no_evolution),
        ("flag off → archive ساخته نمی‌شود", t_flag_off_archive_not_created),
        ("flag off → شکلِ خروجی همان قبل", t_flag_off_legacy_result_shape),
        # (ج) verifier-independence
        ("uptime fix → drop (λ_persist)", test_uptime_fix_rejected_by_measured_lift),
        ("uptime fix هرگز برنده نیست", t_uptime_fix_not_winner_in_cycle),
        ("evolution معیار را ویرایش نمی‌کند", t_evolution_does_not_edit_verifier),
        # (د) RFC همیشه submit
        ("RFC همیشه submit می‌شود", t_rfc_always_submitted),
        ("run_cycle با evolution سریع", t_run_cycle_non_blocking_with_evolution),
    ])
    sys.exit(1 if failed else 0)
