#!/usr/bin/env python3
"""test_run_store_concurrency.py — سکانسِ run_store زیرِ نوشتنِ هم‌زمان.

چرا این فایل هست (2026-08-23، TDR-DBOS-RUNSTORE §3):
    `run_store.append_event` یک read-modify-write ِ بی‌قفل بود:
        events = _read_jsonl(...)      # بخوان
        seq = max(...) + 1             # حساب کن
        _append_jsonl(..., rec)        # بنویس
    دو نویسندهٔ هم‌زمان روی یک run_id همان max_seq را می‌دیدند و **هر دو** با
    یک sequence می‌نوشتند. خودِ ماژول هم صادق بود:
        DURABILITY = "PROCESS_DURABLE"  # no cross-process guarantee

    سوییتِ موجود (`test_cognitive_events.py::t_sequence_monotonic` و
    `t_duplicate_run_id_idempotent`) سکانس را فقط **تک‌نخی** می‌سنجید — یعنی
    مسیرِ خراب اصلاً دیده نمی‌شد (درسِ suite-can-pin-the-very-bug).

قرارداد این تست (آستانهٔ خودِ TDR): **اول باید روی کدِ قدیم قرمز شود.**
    اگر سبز باشد یعنی یا race را بازتولید نمی‌کند یا باگ را pin می‌کند —
    در هر دو حالت بی‌ارزش است (درسِ green-mutation-means-unwatched).

ناوردی‌ای که سنجیده می‌شود: **sequence هرگز تکراری نیست.**
    شکاف (gap) عمداً مجاز است — مصرف‌کننده‌ها با `>` مقایسه می‌کنند
    (`run_store.list_events`) و SSE از `id:` استفاده می‌کند؛ پس جهشِ شماره بی‌ضرر
    است ولی تکرار، رویدادِ مالک را می‌بلعد.
"""
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("run-store-concurrency")
_OPS = harness.SELF_OPS

sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "cognitive"))

import run_store as rs  # noqa: E402

N_THREADS = 8
APPENDS_EACH = 12


def _fresh_store():
    """state ِ ایزوله — هرگز درختِ زنده (live_state_guard هم پشتِ سر مسلح است)."""
    rs.STATE_DIR = Path(ENV["ops"]) / "state"
    rs.RUNS_DIR = rs.STATE_DIR / "cognitive" / "runs"


def _hammer(run_id: str, barrier: threading.Barrier, errors: list) -> None:
    """همهٔ نخ‌ها دقیقاً با هم شروع می‌کنند تا پنجرهٔ race باز شود."""
    try:
        barrier.wait(timeout=30)
        for i in range(APPENDS_EACH):
            rs.append_event(run_id, "INTENT_DETECTED", producer=f"t{i}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{type(exc).__name__}: {exc}")


def _run_concurrent(run_id: str) -> list[dict]:
    barrier = threading.Barrier(N_THREADS)
    errors: list = []
    threads = [threading.Thread(target=_hammer, args=(run_id, barrier, errors))
               for _ in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert not errors, f"نخ‌ها استثنا دادند: {errors[:3]}"
    return rs.list_events(run_id)


def t_concurrent_appends_no_duplicate_sequence():
    """ناوردیِ اصلی: هیچ دو رویدادی یک sequence ندارند."""
    _fresh_store()
    rs.create_run("run_conc_dup")
    events = _run_concurrent("run_conc_dup")

    seqs = [e["sequence"] for e in events]
    dupes = {s for s in seqs if seqs.count(s) > 1}
    assert not dupes, (
        f"sequence تکراری: {sorted(dupes)[:10]} — "
        f"{len(seqs)} رویداد ولی فقط {len(set(seqs))} شمارهٔ یکتا "
        f"(race در append_event)")


def t_no_event_lost():
    """هر append باید دقیقاً یک رویداد بگذارد — نه کمتر (نوشتنِ روی‌هم‌افتاده)."""
    _fresh_store()
    rs.create_run("run_conc_count")
    events = _run_concurrent("run_conc_count")

    # create_run خودش یک RUN_CREATED با seq=0 می‌گذارد
    expected = N_THREADS * APPENDS_EACH + 1
    assert len(events) == expected, (
        f"انتظار {expected} رویداد، {len(events)} یافت شد — رویداد گم شده است")


def t_returned_sequences_are_unique():
    """مقدارِ برگشتیِ append_event هم باید یکتا باشد — مصرف‌کننده (SSE `id:`)
    مستقیماً روی همین عدد حساب می‌کند، نه روی محتویاتِ فایل."""
    _fresh_store()
    rs.create_run("run_conc_ret")
    returned: list = []
    lock = threading.Lock()
    barrier = threading.Barrier(N_THREADS)

    def _collect():
        barrier.wait(timeout=30)
        for _ in range(APPENDS_EACH):
            seq = rs.append_event("run_conc_ret", "MODEL_FINISHED")
            with lock:
                returned.append(seq)

    threads = [threading.Thread(target=_collect) for _ in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    dupes = {s for s in returned if returned.count(s) > 1}
    assert not dupes, (
        f"append_event دو بار همان sequence را برگرداند: {sorted(dupes)[:10]}")


def t_sequence_still_monotonic_single_thread():
    """گاردِ رگرسیون: رفتارِ تک‌نخی که سوییتِ قدیم تضمین می‌کرد نباید بشکند."""
    _fresh_store()
    rs.create_run("run_conc_seq")
    seqs = [rs.append_event("run_conc_seq", "INTENT_DETECTED") for _ in range(5)]
    assert seqs == sorted(seqs), f"سکانس صعودی نیست: {seqs}"
    assert len(seqs) == len(set(seqs)), f"تکرار در تک‌نخی: {seqs}"
    assert seqs[0] == 1, f"باید از ۱ ادامه دهد (۰ مالِ RUN_CREATED است): {seqs[0]}"


if __name__ == "__main__":
    failed = harness.run([
        ("concurrent appends -> no duplicate sequence", t_concurrent_appends_no_duplicate_sequence),
        ("concurrent appends -> no event lost", t_no_event_lost),
        ("returned sequences unique", t_returned_sequences_are_unique),
        ("single-thread monotonic (regression guard)", t_sequence_still_monotonic_single_thread),
    ])
    sys.exit(1 if failed else 0)
