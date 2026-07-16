#!/usr/bin/env python3
"""test_ps_writeback.py — write-backِ گاردشدهٔ برچسب‌ها به PocketSmith (2026-07-16).

اثبات‌ها (صفر شبکهٔ واقعی، صفر کلیدِ واقعی — seamِ _transport جایگزین می‌شود):
  * فلگِ خاموش → enqueue/flush هر دو no-opِ کامل (صفر فایل، صفر شبکه).
  * choke-point: PUT با فیلدِ خارج از whitelist (مثلاً amount) یا مسیرِ غیرِ
    /transactions/{id} یا متدِ غیرمجاز → blocked، transport اصلاً صدا نمی‌خورد.
  * happy path: GET (idempotency) → PUTِ برچسبِ merge‌شده؛ برچسب‌های خودِ مالک می‌مانند،
    فقط دو namespaceِ oct- جایگزین می‌شود؛ صف خالی و لاگِ ممیزی نوشته می‌شود.
  * از-قبل-درست → skip (هیچ PUT)؛ 404 → drop؛ 403 → توقفِ صادق + صف دست‌نخورده.
  * سقفِ نوشتن در هر flush؛ dedupِ صف (آخرین جوابِ مالک می‌بَرد)؛
    enqueueِ همزمانِ حینِ flush گم نمی‌شود (raceِ صف).
  * مقدارِ کلیدِ جعلی هرگز در هیچ خروجی/note/فایل ظاهر نمی‌شود.

اجرا: REAL_VAULT=worktree PYTHONIOENCODING=utf-8 python -X utf8 test_ps_writeback.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.error
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness  # noqa: E402
ENV = harness.setup("ps_writeback")

import ps_writeback as pw   # noqa: E402

FAKE_KEY = "TEST-WB-KEY-DO-NOT-USE"   # جعلی — هرگز شبکه، هرگز واقعی
_TMP = Path(tempfile.mkdtemp(prefix="pswb-test-"))
_checks = 0


def check(name: str, cond: bool) -> None:
    global _checks
    _checks += 1
    if not cond:
        print(f"✗ {name}")
        sys.exit(1)
    print(f"✓ {name}")


def _paths(tag: str) -> tuple[Path, Path]:
    return _TMP / f"q-{tag}.jsonl", _TMP / f"a-{tag}.jsonl"


def _load_q(p: Path) -> list[dict]:
    """صف را با همان پارسرِ خودِ ماژول بخوان (منبعِ واحدِ حقیقت)."""
    return pw._read_queue(p)


class FakeResp:
    def __init__(self, obj, status=200):
        self._body = json.dumps(obj).encode("utf-8")
        self.headers = {}
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeTransport:
    """صفِ پاسخ‌ها + ضبطِ درخواست‌ها؛ پاسخ = FakeResp یا Exception یا callable(req)."""

    def __init__(self, actions):
        self.actions = list(actions)
        self.calls: list[dict] = []

    def __call__(self, req, timeout):
        self.calls.append({"method": req.get_method(), "url": req.full_url,
                           "body": (json.loads(req.data.decode("utf-8")) if req.data else None)})
        a = self.actions.pop(0)
        if callable(a) and not isinstance(a, FakeResp):
            a = a(req)
        if isinstance(a, Exception):
            raise a
        return a


def _http_err(url, code):
    return urllib.error.HTTPError(url, code, "err", {}, None)


def _flag(on: bool) -> None:
    if on:
        os.environ[pw.FLAG] = "1"
    else:
        os.environ.pop(pw.FLAG, None)


_orig_transport = pw._transport
try:
    # ─── ۱) فلگ خاموش: no-opِ کامل ────────────────────────────────────────────
    _flag(False)
    q, a = _paths("off")
    r = pw.enqueue("111", "armin", "expense", queue_path=q)
    check("فلگ خاموش: enqueue صف نمی‌کند", r["queued"] is False and not q.exists())
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("فلگ خاموش: flush no-op (wired=False)", r["wired"] is False and r["written"] == 0)

    # ─── ۲) choke-point: whitelist/مسیر/متد — transport هرگز صدا نمی‌خورد ─────
    _flag(True)
    ft = FakeTransport([])
    pw._transport = ft
    r = pw._request("PUT", "/transactions/5", {"amount": -1200}, key=FAKE_KEY)
    check("PUT با amount → blocked (وایت‌لیست)", r.get("blocked") is True and not ft.calls)
    r = pw._request("PUT", "/transactions/5", {"labels": "x", "date": "2026-01-01"}, key=FAKE_KEY)
    check("PUT با فیلدِ اضافه کنارِ labels → blocked", r.get("blocked") is True and not ft.calls)
    r = pw._request("PUT", "/users/9/transactions", {"labels": "x"}, key=FAKE_KEY)
    check("PUT به مسیرِ غیرِ /transactions/{id} → blocked", r.get("blocked") is True and not ft.calls)
    r = pw._request("DELETE", "/transactions/5", key=FAKE_KEY)
    check("متدِ DELETE → blocked", r.get("blocked") is True and not ft.calls)
    r = pw._request("PUT", "/transactions/5", {}, key=FAKE_KEY)
    check("PUTِ بدنه‌خالی → blocked", r.get("blocked") is True and not ft.calls)

    # ─── ۳) enqueue + happy-path flush ────────────────────────────────────────
    q, a = _paths("happy")
    r = pw.enqueue("222", "armin", "expense", queue_path=q)
    check("enqueue صف می‌کند (۱ خط)", r["queued"] is True and len(q.read_text("utf-8").splitlines()) == 1)
    r = pw.enqueue("222", "unknown", "unknown", queue_path=q)
    check("owner/ptype ناشناخته → صف نمی‌شود", r["queued"] is False)
    ft = FakeTransport([
        FakeResp({"id": 222, "labels": ["فروشگاه"]}),                       # GET
        FakeResp({"id": 222, "labels": ["فروشگاه", "oct-مالک-آرمین"]}),     # PUT
    ])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    put = ft.calls[1]
    check("flush: یک GET بعد یک PUT به /transactions/222",
          len(ft.calls) == 2 and ft.calls[0]["method"] == "GET"
          and put["method"] == "PUT" and put["url"].endswith("/transactions/222"))
    check("برچسبِ مالک می‌ماند + دو برچسبِ oct اضافه می‌شود",
          put["body"] == {"labels": "فروشگاه,oct-مالک-آرمین,oct-نوع-خرج"})
    check("flush ok و صف خالی شد", r["ok"] and r["written"] == 1 and not _load_q(q))
    check("لاگِ ممیزی «written» دارد", "written" in a.read_text("utf-8"))

    # ─── ۴) idempotent: از قبل درست → صفر PUT ────────────────────────────────
    q, a = _paths("idem")
    pw.enqueue("333", "abbas", "income", queue_path=q)
    ft = FakeTransport([FakeResp({"id": 333, "labels": ["oct-مالک-عباس", "oct-نوع-درآمد"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("از-قبل-درست: skip، هیچ PUT، صف خالی",
          r["skipped"] == 1 and r["written"] == 0 and len(ft.calls) == 1 and not _load_q(q))

    # ─── ۵) جایگزینیِ namespaceِ کهنه (جوابِ عوض‌شدهٔ مالک) ───────────────────
    merged, changed = pw._merge_labels(["oct-مالک-عباس", "قسط"], ["oct-مالک-آرمین", "oct-نوع-خرج"])
    check("namespaceِ کهنه جایگزین، برچسبِ مالک محفوظ",
          changed and merged == ["قسط", "oct-مالک-آرمین", "oct-نوع-خرج"])

    # ─── ۶) 403 → توقفِ صادق + صف دست‌نخورده ─────────────────────────────────
    q, a = _paths("403")
    pw.enqueue("444", "armin", "wage", queue_path=q)
    ft = FakeTransport([FakeResp({"id": 444, "labels": []}),
                        _http_err(pw._ps.BASE + "/transactions/444", 403)])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("403: ok=False + صف دست‌نخورده + پیامِ کلیدِ full-access",
          not r["ok"] and r["kept"] == 1 and "full-access" in r["note"] and len(_load_q(q)) == 1)

    # ─── ۷) 404 → drop ────────────────────────────────────────────────────────
    q, a = _paths("404")
    pw.enqueue("555", "business", "expense", queue_path=q)
    ft = FakeTransport([_http_err(pw._ps.BASE + "/transactions/555", 404)])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("404: drop و صف خالی", r["ok"] and r["dropped"] == 1 and not _load_q(q))

    # ─── ۸) سقفِ نوشتن ────────────────────────────────────────────────────────
    q, a = _paths("cap")
    pw.enqueue("661", "armin", "expense", queue_path=q)
    pw.enqueue("662", "armin", "expense", queue_path=q)
    ft = FakeTransport([FakeResp({"labels": []}), FakeResp({"labels": ["oct-مالک-آرمین"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY, max_writes=1)
    check("سقف=۱: یک نوشتن، بقیه در صف می‌مانند",
          r["written"] == 1 and r["kept"] == 1 and len(_load_q(q)) == 1)

    # ─── ۹) dedup: آخرین جوابِ مالک می‌بَرد ──────────────────────────────────
    q, a = _paths("dedup")
    pw.enqueue("777", "armin", "expense", queue_path=q)
    pw.enqueue("777", "armin", "income", queue_path=q)
    ft = FakeTransport([FakeResp({"labels": []}), FakeResp({"labels": ["x"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("dedup: یک PUT با آخرین جواب (درآمد)",
          r["written"] == 1 and len(ft.calls) == 2
          and ft.calls[1]["body"]["labels"].endswith("oct-نوع-درآمد"))

    # ─── ۱۰) raceِ صف: enqueueِ حینِ flush گم نمی‌شود ────────────────────────
    q, a = _paths("race")
    pw.enqueue("881", "armin", "expense", queue_path=q)

    def _get_with_side_effect(req):
        pw.enqueue("882", "abbas", "income", queue_path=q)   # همزمان صف می‌شود
        return FakeResp({"labels": []})

    ft = FakeTransport([_get_with_side_effect, FakeResp({"labels": ["ok"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    left = _load_q(q)
    check("raceِ صف: آیتمِ همزمان می‌ماند، آیتمِ پردازش‌شده حذف",
          r["written"] == 1 and len(left) == 1 and left[0]["tid"] == "882")

    # ─── ۱۰ب) idِ غیرعددی (ردیفِ xlsx/CSV با idِ hash) → اصلاً صف نمی‌شود ────
    q, a = _paths("nonps")
    r = pw.enqueue("sha1-abc123", "armin", "expense", queue_path=q)
    check("idِ غیرِ PocketSmith صف نمی‌شود", r["queued"] is False and not q.exists())
    r = pw.enqueue("۱۲۳۴", "armin", "expense", queue_path=q)
    check("رقمِ یونیکد (isdigit-پاس) هم صف نمی‌شود", r["queued"] is False and not q.exists())
    r = pw.enqueue("123456", "armin", "expense", source="xlsx-export", queue_path=q)
    check("منشأِ غیرِ PocketSmith (گاردِ provenance) صف نمی‌شود", r["queued"] is False)
    r = pw.enqueue("123456", "armin", "expense", source=pw._ps.SOURCE, queue_path=q)
    check("منشأِ PocketSmith صف می‌شود", r["queued"] is True)

    # ─── ۱۰د) HALT سراسری → flush no-op و صف دست‌نخورده ──────────────────────
    _orig_halted = pw._halted
    pw._halted = lambda: "TEST-HALT"
    ft = FakeTransport([])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    pw._halted = _orig_halted
    check("HALT: صفر شبکه، صف دست‌نخورده، نوتِ صادق",
          not r["ok"] and "HALT" in r["note"] and not ft.calls and len(_load_q(q)) == 1)

    # ─── ۱۰ه) قفلِ flusherِ همزمان ────────────────────────────────────────────
    lockf = q.with_name(q.name + ".lock")
    lockf.write_text("999999", "ascii")
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    lockf.unlink()
    check("قفلِ تازه: flushِ دوم رد می‌شود، صف دست‌نخورده",
          not r["ok"] and "در جریان" in r["note"] and len(_load_q(q)) == 1)

    # ─── ۱۰و) برچسبِ کامادارِ خودِ مالک → skip (دادهٔ مالک دست‌نخورده) ───────
    ft = FakeTransport([FakeResp({"labels": ["نان,پنیر"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("برچسبِ کامادار: skip، هیچ PUT، صف خالی",
          r["skipped"] == 1 and r["written"] == 0 and len(ft.calls) == 1 and not _load_q(q))

    # ─── ۱۰ز) tidِ سمی داخلِ صف (دست‌کاریِ فایل) → drop، نه wedge ────────────
    q, a = _paths("poison")
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text(json.dumps({"tid": "5?x=1", "owner": "armin", "ptype": "expense"},
                            ensure_ascii=False) + "\n", "utf-8")
    ft = FakeTransport([])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("tidِ سمی: drop بدونِ هیچ درخواست، صف خالی",
          r["ok"] and r["dropped"] == 1 and not ft.calls and not _load_q(q))

    # ─── ۱۰ح) auto-backfillِ یک‌باره در اولین flushِ سیمی ────────────────────
    bfdir = _TMP / "bf"
    bfdir.mkdir()
    q2, a2 = bfdir / "q.jsonl", bfdir / "a.jsonl"
    store = bfdir / "store.json"
    store.write_text(json.dumps({"txns": [
        {"id": "888001", "source": pw._ps.SOURCE, "review": "confirmed",
         "owner": "armin", "ptype": "expense"},
        {"id": "aabbcc", "source": "xlsx-export", "review": "confirmed",
         "owner": "armin", "ptype": "expense"},
    ]}, ensure_ascii=False), "utf-8")
    ft = FakeTransport([FakeResp({"labels": []}), FakeResp({"labels": ["ok"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q2, audit_path=a2, store_path=store, key=FAKE_KEY)
    check("auto-backfill: تأییدِ قدیمیِ PS نوشته شد، ردیفِ فایل نه، مارکر ساخته شد",
          r["written"] == 1 and (bfdir / pw.MARK_NAME).exists()
          and ft.calls[1]["url"].endswith("/transactions/888001"))
    ft = FakeTransport([])
    pw._transport = ft
    r = pw.flush(queue_path=q2, audit_path=a2, store_path=store, key=FAKE_KEY)
    check("backfill فقط یک‌بار (مارکر)", r["written"] == 0 and not ft.calls)

    # ─── ۱۰ج) خطِ خرابِ وسطِ صف: شمارشِ race خراب نمی‌شود ────────────────────
    q, a = _paths("malformed")
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text("GARBAGE-NOT-JSON\n", "utf-8")
    pw.enqueue("991", "armin", "expense", queue_path=q)
    ft = FakeTransport([FakeResp({"labels": []}), FakeResp({"labels": ["ok"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("خطِ خراب: پردازش‌شده حذف، بدونِ تکثیرِ خطوط",
          r["written"] == 1 and not _load_q(q))

    # ─── ۱۱) صفر نشتِ کلید ────────────────────────────────────────────────────
    blob = json.dumps([r, pw.flush(queue_path=_paths("leak")[0], key=FAKE_KEY)],
                      ensure_ascii=False)
    for p in _TMP.glob("*.jsonl"):
        blob += p.read_text("utf-8")
    check("مقدارِ کلید هرگز در خروجی/صف/لاگ نیست", FAKE_KEY not in blob)

finally:
    pw._transport = _orig_transport
    _flag(False)

print(f"\nهمه سبز — {_checks} چک ✅")
