"""test_seam_ledger_sampling_20260816.py — SEAM-LOOP فاز ۱-۴ (مصوب مالک).

نمونه‌گیریِ قطعیِ actorهای پرصدا در لجر ژنوم (scheduler = ۸۱٪ رویدادهای هفته).
سه قفل:
  A) پیش‌فرض (بدون set) = هر append می‌نویسد — بایت‌به‌بایتِ رفتارِ امروز
  B) rate=0.1 → فقط هر ۱۰اُمین رویدادِ همان actor می‌ماند؛ actorهای دیگر دست‌نخورده
  C) نرخ نامعتبر → ValueError؛ sampled-out یک dict نشانه برمی‌گرداند نه استثنا
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "07 - Knowledge" / "genome-system" / "ledger"))
import ledger as L  # noqa: E402


def _fresh(tmp_path):
    return L.Ledger(str(tmp_path / "l.jsonl"))


def test_default_is_write_all(tmp_path):
    lg = _fresh(tmp_path)
    for i in range(7):
        lg.append("NOTE", {"i": i}, actor="scheduler")
    assert len(list(lg.iter_events())) == 7


def test_sampling_keeps_every_kth_only_for_actor(tmp_path):
    lg = _fresh(tmp_path)
    L.set_actor_sampling("scheduler", 0.1)          # k=10
    try:
        kept, skipped = 0, 0
        for i in range(20):
            r = lg.append("NOTE", {"i": i}, actor="scheduler")
            if isinstance(r, dict) and r.get("sampled_out"):
                skipped += 1
            else:
                kept += 1
        for i in range(5):                            # actor دیگر بی‌نقص می‌ماند
            lg.append("NOTE", {"j": i}, actor="governor")
        rows = list(lg.iter_events())
        sched = [r for r in rows if r.get("actor") == "scheduler"]
        gov = [r for r in rows if r.get("actor") == "governor"]
        assert kept == 2 and skipped == 18, f"kept={kept} skipped={skipped}"
        assert len(sched) == 2 and len(gov) == 5
        assert [r["payload"]["i"] for r in sched] == [0, 10]   # هر ۱۰اُمین
    finally:
        L.set_actor_sampling("scheduler", 1.0)       # بازگشت به پیش‌فرض


def test_invalid_rate_and_marker_shape(tmp_path):
    lg = _fresh(tmp_path)
    try:
        L.set_actor_sampling("scheduler", 0.0)
        raise AssertionError("0.0 باید ValueError بدهد")
    except ValueError:
        pass
    L.set_actor_sampling("scheduler", 1.0)           # نمونه‌گیری خاموش
    r = lg.append("NOTE", {"x": 1}, actor="scheduler")
    assert not (isinstance(r, dict) and r.get("sampled_out"))
