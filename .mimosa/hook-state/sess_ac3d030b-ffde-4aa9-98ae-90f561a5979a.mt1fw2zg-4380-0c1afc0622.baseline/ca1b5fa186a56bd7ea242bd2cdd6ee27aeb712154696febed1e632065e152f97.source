#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_notif_inbox — صندوقِ اعلانِ مینی‌اپ (کاهشِ فشارِ تلگرام، ۲۰۲۶-۰۸-۰۷).

ادعاهای باربر:
  ۱) فلگ خاموش = route() دقیقاً send_fn() (صفر نوشتن به صندوق).
  ۲) فلگ روشن = push به صندوق، send_fn هرگز صدا زده نمی‌شود.
  ۳) prune فقط آیتمِ *خوانده‌شده* را حذف می‌کند، هرگز خوانده‌نشده را.
  ۴) maybe_ping فقط برای آیتمِ *نو از آخرین پینگ* پینگ می‌زند — نه صرفاً خوانده‌نشده
     (سنجهٔ باربر: آیتمِ کهنه‌ی هنوز-خوانده‌نشده نباید هر cooldown دوباره پینگ بزند).

mutation-gate: اگر ادعای ۴ به `unread_count() > 0` ساده‌سازی شود، تستِ
`t_maybe_ping_does_not_refire_for_stale_unread` قرمز می‌شود.
"""
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("notif-inbox")

_TG_CENTER = Path(__file__).resolve().parent.parent / "telegram_center"
if str(_TG_CENTER) not in sys.path:
    sys.path.insert(0, str(_TG_CENTER))

import notif_inbox as ni  # noqa: E402


class _Flag:
    """ctx manager: ست/پاک‌کردنِ یک env-flag با restore."""
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


def _reset_store():
    """صندوق را برای هر تست خالی کن (isolated tmp path از harness، ولی بینِ
    تست‌ها هم باید پاک شود)."""
    try:
        ni._STORE_PATH.unlink()
    except OSError:
        pass
    lock = ni._STORE_PATH.with_suffix(".json.lock")
    try:
        lock.unlink()
    except OSError:
        pass


# ════════════════════════════════════════════════════════════════════════════
# (۱)+(۲) فلگ خاموش/روشن — route()
# ════════════════════════════════════════════════════════════════════════════
def t_flag_off_route_calls_send_fn_untouched():
    _reset_store()
    calls = {"n": 0}

    def sf():
        calls["n"] += 1
        return "sent-directly"

    with _Flag(ni.FLAG, None):
        out = ni.route("needs", "t", "b", send_fn=sf)
    assert out == "sent-directly", out
    assert calls["n"] == 1, calls
    assert ni.unread_count() == 0, "فلگ خاموش نباید چیزی به صندوق بنویسد"


def t_flag_on_route_pushes_and_never_calls_send_fn():
    _reset_store()
    calls = {"n": 0}

    def sf():
        calls["n"] += 1
        return "sent-directly"

    with _Flag(ni.FLAG, "1"):
        out = ni.route("needs", "عنوان", "بدنه", send_fn=sf)
    assert out and isinstance(out, str), out
    assert calls["n"] == 0, f"send_fn نباید صدا زده شود: {calls}"
    assert ni.unread_count() == 1, ni.unread_count()
    items = ni.list_items()
    assert items[0]["category"] == "needs", items[0]
    assert items[0]["title"] == "عنوان", items[0]
    assert items[0]["body"] == "بدنه", items[0]


# ════════════════════════════════════════════════════════════════════════════
# push/list/unread/mark_read
# ════════════════════════════════════════════════════════════════════════════
def t_push_returns_none_not_empty_string_on_save_failure():
    """رگرسیون: center.py's health-digest caller نتیجه را با `is not None` می‌سنجد
    (نه صرفاً truthy) — رشتهٔ خالی از این چک رد می‌شد و دایجستِ نرسیده را
    «رسیده» علامت می‌زد. push() باید دقیقاً None بدهد، نه ""."""
    _reset_store()
    old_save = ni._save
    ni._save = lambda state: False
    try:
        out = ni.push("needs", "x")
        assert out is None, f"شکستِ ذخیره باید None بدهد نه {out!r}"
    finally:
        ni._save = old_save


def t_push_uses_default_title_when_empty():
    _reset_store()
    nid = ni.push("rfc_card")
    assert nid, "push باید id غیرخالی بدهد"
    items = ni.list_items()
    assert items[0]["title"] == ni._TITLES["rfc_card"], items[0]


def t_list_items_newest_first():
    _reset_store()
    id1 = ni.push("needs", "اول")
    id2 = ni.push("needs", "دوم")
    items = ni.list_items()
    assert [it["id"] for it in items] == [id2, id1], items


def t_mark_read_specific_ids_only():
    _reset_store()
    id1 = ni.push("needs", "اول")
    id2 = ni.push("needs", "دوم")
    changed = ni.mark_read(ids=[id1])
    assert changed == 1, changed
    by_id = {it["id"]: it for it in ni.list_items()}
    assert by_id[id1]["read"] is True, by_id[id1]
    assert by_id[id2]["read"] is False, by_id[id2]
    assert ni.unread_count() == 1, ni.unread_count()


def t_mark_read_all_when_ids_none():
    _reset_store()
    ni.push("needs", "اول")
    ni.push("needs", "دوم")
    changed = ni.mark_read()
    assert changed == 2, changed
    assert ni.unread_count() == 0, ni.unread_count()
    # idempotent: دوباره صدا زدن چیزی را تغییر نمی‌دهد
    assert ni.mark_read() == 0


# ════════════════════════════════════════════════════════════════════════════
# (۳) prune — فقط خوانده‌شده حذف می‌شود
# ════════════════════════════════════════════════════════════════════════════
def t_prune_never_drops_unread():
    _reset_store()
    old_max = ni._MAX_ITEMS
    ni._MAX_ITEMS = 5
    try:
        # ۳ تای اول را می‌سازیم و می‌خوانیم (کاندیدِ prune)
        read_ids = [ni.push("needs", f"r{i}") for i in range(3)]
        ni.mark_read(ids=read_ids)
        # ۴ تای دیگر می‌سازیم بدونِ خواندن — جمعاً ۷ > سقفِ ۵
        unread_ids = [ni.push("needs", f"u{i}") for i in range(4)]
        items = ni.list_items(limit=100)
        assert len(items) == ni._MAX_ITEMS, \
            f"باید دقیقاً به سقف برسد: {len(items)} != {ni._MAX_ITEMS}"
        surviving_ids = {it["id"] for it in items}
        for uid in unread_ids:
            assert uid in surviving_ids, f"آیتمِ خوانده‌نشده هرگز نباید prune شود: {uid}"
        # فقط قدیمی‌ترین‌های خوانده‌شده باید حذف شده باشند (۲ تای اول از ۳)
        assert read_ids[0] not in surviving_ids
        assert read_ids[1] not in surviving_ids
    finally:
        ni._MAX_ITEMS = old_max


# ════════════════════════════════════════════════════════════════════════════
# (۴) maybe_ping — فقط برای «نو از آخرین پینگ»، نه صرفاً خوانده‌نشده
# ════════════════════════════════════════════════════════════════════════════
def t_maybe_ping_flag_off_is_noop():
    _reset_store()
    with _Flag(ni.FLAG, None):
        calls = {"n": 0}
        res = ni.maybe_ping(lambda text: calls.__setitem__("n", calls["n"] + 1) or True)
        assert res == {"pinged": False, "unread": 0, "reason": "flag-off"}, res
        assert calls["n"] == 0


def t_maybe_ping_no_items_no_ping():
    _reset_store()
    with _Flag(ni.FLAG, "1"):
        res = ni.maybe_ping(lambda text: True)
        assert res["pinged"] is False, res
        assert res["reason"] == "no-fresh-items", res


def t_maybe_ping_does_not_refire_for_stale_unread():
    """سنجهٔ باربرِ اصلی: یک آیتمِ هنوز-خوانده‌نشده که قبلاً پینگ شده، دوباره
    پینگ نمی‌زند — حتی وقتی cooldown صفر است. اگر پیاده‌سازی به سادگیِ
    ``unread_count() > 0`` برگردد، این تست قرمز می‌شود."""
    _reset_store()
    with _Flag(ni.FLAG, "1"), _Flag("OCTOPUS_NOTIF_PING_COOLDOWN_S", "0"):
        ni.push("needs", "اول")
        pings = {"n": 0}

        def pf(text):
            pings["n"] += 1
            return True

        r1 = ni.maybe_ping(pf)
        assert r1["pinged"] is True, r1
        assert pings["n"] == 1, pings

        # هیچ آیتمِ نویی نیامده — آیتمِ قبلی همچنان unread است ولی نباید دوباره پینگ بزند
        r2 = ni.maybe_ping(pf)
        assert r2["pinged"] is False, r2
        assert r2["reason"] == "no-fresh-items", r2
        assert pings["n"] == 1, f"نباید دوباره پینگ بزند: {pings}"

        # یک آیتمِ *نوی* واقعی می‌آید → این بار باید پینگ بزند
        ni.push("needs", "دوم")
        r3 = ni.maybe_ping(pf)
        assert r3["pinged"] is True, r3
        assert pings["n"] == 2, pings


def t_maybe_ping_respects_cooldown():
    _reset_store()
    with _Flag(ni.FLAG, "1"), _Flag("OCTOPUS_NOTIF_PING_COOLDOWN_S", "3600"):
        ni.push("needs", "اول")
        pings = {"n": 0}

        def pf(text):
            pings["n"] += 1
            return True

        r1 = ni.maybe_ping(pf)
        assert r1["pinged"] is True, r1
        ni.push("needs", "دوم")   # آیتمِ نو، ولی داخلِ cooldown
        r2 = ni.maybe_ping(pf)
        assert r2["pinged"] is False, r2
        assert r2["reason"] == "cooldown", r2
        assert pings["n"] == 1, pings


def t_maybe_ping_send_failure_leaves_marker_untouched():
    _reset_store()
    with _Flag(ni.FLAG, "1"), _Flag("OCTOPUS_NOTIF_PING_COOLDOWN_S", "0"):
        ni.push("needs", "اول")
        r1 = ni.maybe_ping(lambda text: False)   # ارسال شکست می‌خورد
        assert r1["pinged"] is False, r1
        assert r1["reason"] == "send-failed", r1
        # چون marker پیش نرفت، آیتم هنوز «تازه» است — تلاشِ بعدی باید دوباره امتحان کند
        r2 = ni.maybe_ping(lambda text: True)
        assert r2["pinged"] is True, r2


def t_maybe_ping_send_fn_exception_is_fail_soft():
    _reset_store()
    with _Flag(ni.FLAG, "1"), _Flag("OCTOPUS_NOTIF_PING_COOLDOWN_S", "0"):
        ni.push("needs", "اول")

        def boom(text):
            raise RuntimeError("simulated transport failure")

        res = ni.maybe_ping(boom)   # نباید exception پرت کند
        assert res["pinged"] is False, res
        assert res["reason"] == "send-failed", res


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_notif_inbox: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
