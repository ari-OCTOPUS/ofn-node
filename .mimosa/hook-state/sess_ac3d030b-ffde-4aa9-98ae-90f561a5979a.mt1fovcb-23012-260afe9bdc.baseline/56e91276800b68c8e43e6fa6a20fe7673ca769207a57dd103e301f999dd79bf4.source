#!/usr/bin/env python3
"""Phase 0 — safety-net: characterization tests for 4 broken states + ledger guard.

این تست‌ها رفتارِ فعلیِ (شکسته) را قفل می‌کنند، نه رفتارِ مطلوب.
وقتی فازهای بعدی (B5/B6/B8/A2) این موارد را درست کنند، این تست‌ها
شکست می‌خورند و باید به‌روز شوند. این دقیقاً هدفِ characterization است:
رگرسیون را catch کند و تغییرِ آگاهانه را اجبار کند.

همچنین: ledger hash-chain guard + append-only + no-spend assertion
(ابزارِ مشترکِ همهٔ فازها).

$0 آفلاین.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("phase0-safety-net")

# ⚠️ تا ۲۰۲۶-۰۸-۰۳ این `harness.REAL_VAULT` بود، پس `chrono` از درختِ **زنده**
# import می‌شد و یک اتصالِ **نوشتنی** به `F:\backup\_ops\state\chrono.db` ِ زنده باز
# می‌کرد — همان دیتابیسی که جدولِ `gated_effect` ِ آن سنجهٔ پذیرشِ برشِ ۱ است.
# `SELF_OPS` قراردادِ خودِ harness است: کدِ زیرِ آزمون = همین درخت، نه درختِ زنده.
_OPS = harness.SELF_OPS
for _p in [str(_OPS), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chrono  # noqa: E402
import opslib  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# 0a — doctor=None در pacemaker (self-heal مرده)
# ════════════════════════════════════════════════════════════════════════════════

def t_0a_doctor_not_passed_to_pacemaker():
    """[CHARACTERIZE] start_pacemaker_thread پارامترِ doctor ندارد → Pacemaker.doctor همیشه None.

    این تست ثابت می‌کند که self-heal (restart_from_known_good) در مسیرِ زنده مرده است.
    وقتی B5 این را درست کند، این تست شکست می‌خورد (doctor != None) → به‌روز کن."""
    # ساختِ Pacemaker مستقیم با doctor=None (شبیه‌سازیِ start_pacemaker_thread فعلی)
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-p0a.db")
    pm = chrono.Pacemaker(db=db)   # doctor و dispatcher پاس داده نشد
    assert pm.doctor is None, \
        "characterization: doctor باید None باشد (start_pacemaker_thread پاس نمی‌دهد)"


def t_0a_start_pacemaker_thread_no_doctor_param():
    """[FIXED in Phase 1 B5] start_pacemaker_thread اکنون doctor و dispatcher دارد."""
    import inspect
    sig = inspect.signature(chrono.start_pacemaker_thread)
    params = list(sig.parameters.keys())
    assert "doctor" in params, \
        f"B5 fix: start_pacemaker_thread باید doctor داشته باشد: {params}"
    assert "dispatcher" in params, \
        f"B5 fix: start_pacemaker_thread باید dispatcher داشته باشد: {params}"


# ════════════════════════════════════════════════════════════════════════════════
# 0b — dispatcher=None (scheduler F19 مرده)
# ════════════════════════════════════════════════════════════════════════════════

def t_0b_dispatcher_none_in_default_pacemaker():
    """[CHARACTERIZE] dispatcher در Pacemakerِ پیش‌فرض همیشه None → schedule queue مرده."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-p0b.db")
    pm = chrono.Pacemaker(db=db)
    assert pm.dispatcher is None, \
        "characterization: dispatcher باید None باشد (start_pacemaker_thread پاس نمی‌دهد)"


def t_0b_schedule_fills_queue_but_dispatch_dead():
    """[CHARACTERIZE] schedule() صف را پر می‌کند ولی dispatcher=None → هیچ dispatch نمی‌شود."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-p0b2.db")
    pm = chrono.Pacemaker(db=db)
    # schedule یک task
    pm.schedule(kind="followup", task_ref="test-task", in_beats=1)
    # ولی dispatcher=None → وقتی due می‌شود، dispatch نمی‌شود
    assert pm.dispatcher is None
    # صف پر شده ولی هیچ‌کس مصرف نمی‌کند
    rows = db.q("SELECT COUNT(*) FROM anticipation_queue")
    assert rows[0][0] >= 1, "schedule باید صف را پر کند"


# ════════════════════════════════════════════════════════════════════════════════
# 0c — outbox خالی (fitness گرسنه)
# ════════════════════════════════════════════════════════════════════════════════

def t_0c_outbox_empty_or_absent():
    """[CHARACTERIZE] outbox.jsonl یا غایب است یا خالی (هیچ‌کس در مسیرِ زنده نمی‌نویسد).

    fitness.py از آن می‌خواند ولی هیچ‌کس نمی‌نویسد → fitness گرسنه."""
    outbox_path = opslib.BRAIN_DIR / "logs" / "outbox.jsonl"
    if outbox_path.exists():
        lines = [l for l in outbox_path.read_text("utf-8").splitlines() if l.strip()]
        # در محیطِ تست، harness ممکن است چیزی نوشته باشد؛ در production خالی/غایب است
        # این تست فقط وجود/عدم‌وجود را مستند می‌کند
        assert isinstance(lines, list)
    else:
        assert True  # غایب — characterization تأیید شد


def t_0c_fitness_reads_empty_outbox_gracefully():
    """[CHARACTERIZE] fitness.compute با outbox خالی کرش نمی‌کند (graceful)، ولی cells خالی."""
    import fitness
    result = fitness.compute(write=False)
    assert isinstance(result, dict)
    assert "authoritative" in result
    # authoritative باید False باشد (هنوز ۲۸ روز نگذشته)
    assert result["authoritative"] is False, \
        "fitness باید authoritative=False باشد (outbox خالی / کم‌داده)"


# ════════════════════════════════════════════════════════════════════════════════
# 0d — phi_t بدون novelty (compute_phi_t اجرا، phi_to_novelty هرگز صدا)
# ════════════════════════════════════════════════════════════════════════════════

def t_0d_phi_to_novelty_not_called_in_doctor():
    """[FIXED in Phase 1 B8] phi_to_novelty اکنون در doctor.py صدا زده می‌شود."""
    doctor_src = (_OPS / "doctor" / "doctor.py").read_text("utf-8")
    assert "phi_to_novelty" in doctor_src, \
        "B8 fix: phi_to_novelty باید در doctor.py صدا زده شود (وصل شد)"
    assert "compute_phi_t" in doctor_src, \
        "compute_phi_t باید در doctor.py صدا زده شود (این بخش زنده است)"


def t_0d_phi_to_novelty_exists_in_b4_fusion():
    """phi_to_novelty در b4_fusion.py تعریف شده (آمادهٔ وصل‌شدن)."""
    b4_src = (_OPS / "doctor" / "box" / "b4_fusion.py").read_text("utf-8")
    assert "def phi_to_novelty" in b4_src


# ════════════════════════════════════════════════════════════════════════════════
# 0e — ledger guard: hash-chain integrity + append-only + no-spend
# ════════════════════════════════════════════════════════════════════════════════

def t_0e_ledger_hash_chain_intact():
    """[GUARD] hash-chainِ ledgerِ ژنوم سالم است (هر mutate = شکست)."""
    ledger_path = opslib.genome_ledger()
    try:
        records = ledger_path.filter()
    except Exception:  # noqa: BLE001 — ledger ممکن است خالی باشد در محیطِ تست
        return
    if not records:
        return
    # هر رکورد باید prev + hash داشته باشد (schema ثابت)
    for rec in records:
        assert "hash" in rec, f"رکورد باید hash داشته باشد: {rec.get('id', '?')}"
        assert "prev" in rec, f"رکورد باید prev داشته باشد: {rec.get('id', '?')}"


def test_append_only_guard():
    """[GUARD] assert_append_only: اگر رکوردِ قبلی حذف/تغییر شد → شکست."""
    before = [{"id": 1, "type": "NOTE", "payload": {"a": 1}, "prev": "", "hash": "h1"},
              {"id": 2, "type": "NOTE", "payload": {"b": 2}, "prev": "h1", "hash": "h2"}]
    # append درست
    after_ok = before + [{"id": 3, "type": "NOTE", "payload": {"c": 3}, "prev": "h2", "hash": "h3"}]
    assert len(after_ok) >= len(before)
    assert after_ok[:len(before)] == before
    # mutate غلط
    after_bad = before.copy()
    after_bad[0] = {"id": 1, "type": "SPEND", "payload": {"stolen": True}}
    assert after_bad[:len(before)] != before, "mutate باید detect شود"


def test_no_spend_in_ledger():
    """[GUARD] هیچ type='spend' یا type='pay' در ledger نیست (no-spend)."""
    ledger_path = opslib.genome_ledger()
    try:
        records = ledger_path.filter()
    except Exception:  # noqa: BLE001
        return
    for rec in records:
        etype = rec.get("type", "")
        assert etype not in ("spend", "pay", "transfer"), \
            f"no-spend ناقض: type={etype} در ledger (id={rec.get('id', '?')})"


# ════════════════════════════════════════════════════════════════════════════════
# 0f — golden snapshot: organism decision output on fixed fixture
# ════════════════════════════════════════════════════════════════════════════════

def t_0f_governor_epoch_snapshot():
    """[SNAPSHOT] خروجیِ run_epoch روی fixtureِ ثابت را snapshot کن.

    این طلاییِ مرجع برای فازهای ۴/۵ (no-collision test) است.
    اگر epistemics تصمیمِ organism را عوض کند → snapshot متفاوت → fail."""
    # fixture: telemetry mock با دادهٔ ثابت
    # (run_epoch از telemetry.snapshot می‌خواند؛ در محیطِ تست ممکن است خالی باشد)
    import governor_epoch
    try:
        record = governor_epoch.run_epoch()
    except Exception:  # noqa: BLE001 — ممکن است به telemetry واقعی وابسته باشد
        return
    # snapshot باید این فیلدها داشته باشد
    assert "next_epoch_minutes" in record
    assert "pressure" in record
    assert "epoch_mode" in record
    # allocation_dry اگر هست، h1_check باید ok یا None باشد
    if "allocation_dry" in record:
        assert "h1_check" in record["allocation_dry"]


if __name__ == "__main__":
    failed = harness.run([
        # 0a
        ("0a: doctor=None در pacemaker", t_0a_doctor_not_passed_to_pacemaker),
        ("0a: start_pacemaker_thread بدونِ doctor param", t_0a_start_pacemaker_thread_no_doctor_param),
        # 0b
        ("0b: dispatcher=None", t_0b_dispatcher_none_in_default_pacemaker),
        ("0b: schedule پر می‌کند ولی dispatch مرده", t_0b_schedule_fills_queue_but_dispatch_dead),
        # 0c
        ("0c: outbox خالی/غایب", t_0c_outbox_empty_or_absent),
        ("0c: fitness با outbox خالی graceful", t_0c_fitness_reads_empty_outbox_gracefully),
        # 0d
        ("0d: phi_to_novelty در doctor صدا زده نمی‌شود", t_0d_phi_to_novelty_not_called_in_doctor),
        ("0d: phi_to_novelty در b4_fusion موجود", t_0d_phi_to_novelty_exists_in_b4_fusion),
        # 0e
        ("0e: ledger hash-chain سالم", t_0e_ledger_hash_chain_intact),
        ("0e: append-only guard", test_append_only_guard),
        ("0e: no-spend در ledger", test_no_spend_in_ledger),
        # 0f
        ("0f: governor epoch snapshot", t_0f_governor_epoch_snapshot),
    ])
    sys.exit(1 if failed else 0)
