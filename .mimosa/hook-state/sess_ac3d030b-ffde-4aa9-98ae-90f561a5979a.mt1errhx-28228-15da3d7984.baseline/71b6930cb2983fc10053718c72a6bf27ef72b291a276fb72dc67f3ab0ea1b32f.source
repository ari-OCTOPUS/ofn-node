#!/usr/bin/env python3
"""test_pocketsmith_api.py — کلاینتِ فقط‌خواندنیِ PocketSmith API v2 (2026-07-16).

اثبات‌ها (صفر شبکهٔ واقعی، صفر کلیدِ واقعی — urllib.request.urlopen mock می‌شود):
  * فلگِ خاموش → me/fetch/sync همه no-op (wired=False، صفر شبکه).
  * کلیدِ نبود (فلگ روشن) → خروجیِ خالیِ صادق، هرگز crash.
  * پاسخِ mockِ تراکنش‌ها → to_store_txns سنتِ درست می‌سازد و category/labelsِ خودِ مالک
    را عیناً حمل می‌کند (دقتِ کل سیستم).
  * pagination: هدرِ Link rel="next" دنبال می‌شود (۲ صفحه → همهٔ ردیف‌ها).
  * rate-limit 429 → backoff (Retry-After) و retry (با _sleep تزریقی، بدونِ خواب).
  * sync: fetch+map+merge روی انبار؛ dedup by id ⇒ syncِ دوباره idempotent.
  * صفر نشتِ کلید: مقدارِ کلیدِ جعلی هرگز در هیچ خروجی/note ظاهر نمی‌شود.

اجرا: REAL_VAULT=worktree PYTHONIOENCODING=utf-8 python -X utf8 test_pocketsmith_api.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness  # noqa: E402
ENV = harness.setup("pocketsmith_api")

import pocketsmith_api as ps   # noqa: E402

FAKE_KEY = "TEST-DEV-KEY-DO-NOT-USE"   # جعلی — فقط برای مسیرِ کد؛ هرگز شبکه، هرگز واقعی
FLAG = ps.FLAG
BASE_ME = ps.BASE + "/me"


# ─── mockِ urllib.request.urlopen (صفر شبکه) ─────────────────────────────────
class FakeResp:
    """پاسخِ جعلیِ context-manager (مثلِ HTTPResponse): read()/headers/status."""

    def __init__(self, obj, link=None, status=200):
        self._body = json.dumps(obj).encode("utf-8")
        self.headers = {"Link": link} if link else {}
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeUrlopen:
    """صفِ actionها را pop می‌کند؛ هر action یا FakeResp است یا Exception (raise).
    هر فراخوان (url, headers) را capture می‌کند تا pagination/هدرِ کلید assert شود."""

    def __init__(self, actions):
        self.actions = list(actions)
        self.calls = []

    def __call__(self, req, timeout=None):
        self.calls.append((req.full_url, dict(req.headers)))
        if not self.actions:
            raise AssertionError("urlopen بیش از انتظار صدا زده شد")
        act = self.actions.pop(0)
        if isinstance(act, Exception):
            raise act
        return act


def _patch(actions):
    """urllib.request.urlopen را با FakeUrlopen جایگزین کن؛ callerِ restore را برمی‌گرداند."""
    fake = FakeUrlopen(actions)
    orig = urllib.request.urlopen
    urllib.request.urlopen = fake

    def restore():
        urllib.request.urlopen = orig
    return fake, restore


def _flag_on():
    os.environ[FLAG] = "1"


def _flag_off():
    os.environ.pop(FLAG, None)


def _set_key():
    os.environ[ps.KEY_ENV] = FAKE_KEY   # env_loader idempotent است → overwrite نمی‌کند


def _clear_key():
    os.environ.pop(ps.KEY_ENV, None)


# نمونهٔ تراکنشِ خامِ PocketSmith (شکلِ واقعیِ v2) — دو ردیف: یک بدهکار، یک بستانکار
def _raw_txns():
    return [
        {"id": 1001, "date": "2026-03-15", "amount": -50.25, "payee": "Woolworths",
         "labels": ["groceries", "essential"],
         "category": {"id": 7, "title": "Groceries"},
         "transaction_account": {"id": 3, "title": "Everyday", "name": "acc-ever",
                                 "type": "bank", "currency_code": "aud",
                                 "current_balance": 987654.21}},   # balance نباید leak شود
        {"id": 1002, "date": "2026-03-16", "amount": 12.00, "payee": "Refund Co",
         "labels": [], "category": {"id": 9, "title": "Income"},
         "transaction_account": {"id": 3, "title": "Everyday"}},
    ]


# ─── تست‌ها ──────────────────────────────────────────────────────────────────
def test_flag_off_is_noop():
    """فلگِ خاموش → me/fetch/sync هیچ شبکه‌ای نمی‌زنند و wired=False می‌دهند."""
    _flag_off()
    _set_key()
    fake, restore = _patch([FakeResp({"id": 1})])   # نباید اصلاً مصرف شود
    try:
        assert ps.me()["wired"] is False
        assert ps.fetch_transactions("2026-01-01", "2026-12-31")["wired"] is False
        s = ps.sync("2026-01-01", "2026-12-31")
        assert s["wired"] is False and s["fetched"] == 0
        assert fake.calls == [], "فلگ خاموش نباید urlopen صدا بزند"
    finally:
        restore()


def test_missing_key_honest_empty():
    """فلگ روشن ولی بی‌کلید → خروجیِ خالیِ صادق، صفر crash، صفر شبکه."""
    _flag_on()
    _clear_key()
    orig_api_key = ps._api_key
    ps._api_key = lambda: None   # قطعی: هیچ کلیدی در دسترس نیست (مستقل از .env محیط)
    fake, restore = _patch([FakeResp({"id": 1})])
    try:
        m = ps.me()
        assert m["ok"] is False and m["user_id"] is None
        f = ps.fetch_transactions("2026-01-01", "2026-12-31")
        assert f["ok"] is False and f["transactions"] == []
        assert ps.KEY_ENV in f["note"]           # note نامِ متغیر را می‌گوید (نه مقدار)
        assert fake.calls == [], "بی‌کلید نباید urlopen صدا بزند"
    finally:
        ps._api_key = orig_api_key
        restore()


def test_to_store_txns_cents_and_category_labels():
    """نگاشت: سنتِ درستِ علامت‌دار + حملِ category/labelsِ خودِ مالک؛ صفر leakِ balance."""
    rows = ps.to_store_txns(_raw_txns())
    assert len(rows) == 2
    a, b = rows[0], rows[1]
    # سنت‌ها: -50.25 → -5025 (بدهکار/خروج) ، +12.00 → 1200 (بستانکار/ورود)
    assert a["amount_cents"] == -5025, a["amount_cents"]
    assert b["amount_cents"] == 1200, b["amount_cents"]
    # دسته‌بندیِ خودِ مالک عیناً حمل شد
    assert a["category"] == "Groceries" and b["category"] == "Income"
    assert a["labels"] == ["groceries", "essential"] and b["labels"] == []
    # schema/منبع/عنوانِ حساب
    assert a["id"] == "1001" and a["date"] == "2026-03-15"
    assert a["source"] == ps.SOURCE and a["account"] == "Everyday"
    assert a["desc"] == "Woolworths"
    assert a["owner"] == "unknown" and a["ptype"] == "unknown" and a["review"] == "pending"
    # balance/PII هرگز در ردیفِ نگاشته نیست
    dump = json.dumps(rows, ensure_ascii=False)
    assert "987654.21" not in dump and "current_balance" not in dump


def test_pagination_follows_next_link():
    """fetch_transactions هدرِ Link rel="next" را دنبال می‌کند → هر دو صفحه جمع می‌شوند."""
    _flag_on()
    _set_key()
    next_url = "https://api.pocketsmith.com/v2/users/42/transactions?page=2&per_page=100"
    actions = [
        FakeResp({"id": 42}),                                    # me()
        FakeResp([_raw_txns()[0]], link=f'<{next_url}>; rel="next"'),  # صفحهٔ ۱
        FakeResp([_raw_txns()[1]], link=None),                   # صفحهٔ ۲ (بدونِ next)
    ]
    fake, restore = _patch(actions)
    try:
        r = ps.fetch_transactions("2026-03-01", "2026-03-31")
        assert r["ok"] is True and r["pages"] == 2
        assert len(r["transactions"]) == 2
        # صفحهٔ دومِ درخواست‌شده باید عیناً همان URLِ Link باشد
        assert fake.calls[2][0] == next_url, fake.calls[2][0]
        # هدرِ احرازِ کلید در همهٔ فراخوان‌ها هست (بدونِ echoِ مقدار)
        for _url, hdrs in fake.calls:
            assert any(k.lower() == "x-developer-key" for k in hdrs), hdrs
    finally:
        restore()


def test_rate_limit_backoff_then_success():
    """429 با Retry-After → backoff (بدونِ خوابِ واقعی) و retry تا موفقیت."""
    _flag_on()
    _set_key()
    err = urllib.error.HTTPError(BASE_ME, 429, "Too Many Requests",
                                 {"Retry-After": "0"}, None)
    fake, restore = _patch([err, FakeResp({"id": 7})])   # اول 429 بعد موفق
    orig_sleep = ps._sleep
    ps._sleep = lambda s: None                            # backoff بدونِ خواب
    try:
        m = ps.me()
        assert m["ok"] is True and m["user_id"] == 7
        assert len(fake.calls) == 2, "باید یک‌بار retry شده باشد"
    finally:
        ps._sleep = orig_sleep
        restore()


def test_sync_merges_and_is_idempotent():
    """sync: fetch+map+merge روی انبار؛ tie-out سبز؛ syncِ دوباره → new_added=0 (dedup by id)."""
    _flag_on()
    _set_key()
    store = Path(ENV["root"]) / "ps-store.json"
    # هر sync دو urlopen می‌زند: me() + یک صفحهٔ تراکنش
    actions = [FakeResp({"id": 42}), FakeResp(_raw_txns(), link=None),
               FakeResp({"id": 42}), FakeResp(_raw_txns(), link=None)]
    fake, restore = _patch(actions)
    try:
        s1 = ps.sync("2026-03-01", "2026-03-31", persist=True, store_path=store)
        assert s1["ok"] and s1["fetched"] == 2 and s1["mapped"] == 2
        assert s1["new_added"] == 2 and s1["total_after_merge"] == 2
        assert s1["reconcile"]["tie_out_ok"] is True
        assert store.exists(), "انبار نوشته نشد"
        doc = json.loads(store.read_text("utf-8"))
        # category/labelsِ خودِ مالک در انبارِ ذخیره‌شده حاضرند
        cats = {t["category"] for t in doc["txns"]}
        assert {"Groceries", "Income"} <= cats, cats
        assert any(t["labels"] == ["groceries", "essential"] for t in doc["txns"])
        # syncِ دوباره روی همان انبار → idempotent (dedup by id)
        s2 = ps.sync("2026-03-01", "2026-03-31", persist=True, store_path=store)
        assert s2["new_added"] == 0 and s2["total_after_merge"] == 2, s2
    finally:
        restore()


def test_key_value_never_leaks():
    """مقدارِ کلیدِ جعلی هرگز در خروجی/note ظاهر نمی‌شود (فقط در هدرِ داخلی)."""
    _flag_on()
    _set_key()
    fake, restore = _patch([FakeResp({"id": 5}),
                            FakeResp([_raw_txns()[0]], link=None)])
    try:
        m = ps.me()
        f = ps.fetch_transactions("2026-03-01", "2026-03-31", user_id=5)
        blob = json.dumps([m, f], ensure_ascii=False)
        assert FAKE_KEY not in blob, "مقدارِ کلید leak شد!"
    finally:
        restore()


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items())
              if k.startswith("test_") and callable(v)]
    _fail = 0
    for _t in _tests:
        try:
            _t()
            print(f"  ✓ {_t.__name__}")
        except AssertionError as e:
            _fail += 1
            print(f"  ✗ {_t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            _fail += 1
            print(f"  💥 {_t.__name__}: {type(e).__name__}: {e}")
    if _fail:
        print(f"❌ test_pocketsmith_api: {_fail}/{len(_tests)} شکست")
        sys.exit(1)
    print(f"✅ test_pocketsmith_api: {len(_tests)}/{len(_tests)} سبز")
# BASE_ME بالای فایل تعریف شده (نزدیکِ ثابت‌ها).
