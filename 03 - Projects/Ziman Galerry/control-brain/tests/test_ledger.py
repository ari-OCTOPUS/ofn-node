"""تست‌های evt.v1 دفترِ رویداد — زنجیرهٔ هش، تشخیصِ دستکاری، ULID، شناسهٔ تصمیم."""
import sqlite3

from core.store import Store, new_ulid, format_decision_id


def test_append_and_verify_chain(tmp_path):
    s = Store(tmp_path / "led.db")
    a = s.append_event("propose", "ziman", "draft dm batch", actor="agent")
    b = s.append_event("propose", "ziman", "draft post batch", actor="agent")
    assert a["seq"] == 1 and b["seq"] == 2
    # زنجیره: prev_hash رکوردِ دوم = self_hash رکوردِ اول
    assert b["prev_hash"] == a["self_hash"]
    assert s.verify_ledger() == {"ok": True, "count": 2, "broken_at": None}


def test_legacy_events_untouched(tmp_path):
    s = Store(tmp_path / "led.db")
    s.log("start", "demo", "legacy path", actor="admin")   # مسیرِ قدیمی
    s.append_event("propose", "demo", "new path", actor="agent")
    assert len(s.recent_events()) == 1          # events فقط رکوردِ log()
    assert len(s.ledger_tail()) == 1            # ledger فقط رکوردِ append_event()


def test_tamper_is_detected(tmp_path):
    s = Store(tmp_path / "led.db")
    s.append_event("propose", "ziman", "original detail", actor="agent")
    s.append_event("propose", "ziman", "second", actor="agent")
    # دستکاریِ مستقیمِ محتوا در پایگاه‌داده (شبیه‌سازیِ حمله)
    con = sqlite3.connect(str(tmp_path / "led.db"))
    con.execute("UPDATE ledger SET detail = ? WHERE seq = 1", ("TAMPERED",))
    con.commit(); con.close()
    result = s.verify_ledger()
    assert result["ok"] is False
    assert result["broken_at"] == 1


def test_deletion_breaks_chain(tmp_path):
    s = Store(tmp_path / "led.db")
    s.append_event("a", "p", "1")
    s.append_event("b", "p", "2")
    s.append_event("c", "p", "3")
    con = sqlite3.connect(str(tmp_path / "led.db"))
    con.execute("DELETE FROM ledger WHERE seq = 2")   # حذفِ میانی
    con.commit(); con.close()
    # رکوردِ ۳ prev_hashِ رکوردِ حذف‌شده را انتظار دارد → شکست
    assert s.verify_ledger()["ok"] is False


def test_ulid_is_sortable_and_26_chars():
    early = new_ulid(1_000_000_000_000)
    late = new_ulid(2_000_000_000_000)
    assert len(early) == 26 and len(late) == 26
    assert early < late          # پیشوندِ زمانی → مرتب‌شونده


def test_decision_id_sequence(tmp_path):
    s = Store(tmp_path / "led.db")
    d1 = s.next_decision_id(day="20260712")
    assert d1 == "ZIM-DEC-20260712-0001"
    s.append_event("decide", "ziman", "approved X", actor="SahebZiman",
                   decision_id=d1)
    d2 = s.next_decision_id(day="20260712")
    assert d2 == "ZIM-DEC-20260712-0002"     # پس از ثبتِ اولی، شمارنده جلو می‌رود
    # روزِ دیگر → از ۰۰۰۱ شروع
    assert s.next_decision_id(day="20260713") == "ZIM-DEC-20260713-0001"


def test_format_decision_id_pure():
    assert format_decision_id("20260712", 7) == "ZIM-DEC-20260712-0007"
