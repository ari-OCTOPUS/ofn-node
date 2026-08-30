#!/usr/bin/env python3
"""test_ps_writeback_verdict.py — گیتِ fail-closed per-item مالک پیش از PocketSmith writeback.

مأموریت (Wave-D / D1، safe-default owner-preapproved): حتی با هر سه فلگِ مسلح
(OCTOPUS_WIRE_PS_WRITEBACK + ACCT_BEAT_SYNC + OCTOPUS_WIRE_POCKETSMITH)، هیچ آیتمی به
PocketSmith **PUT** نمی‌شود مگر یک رکوردِ رأیِ پایدارِ مالک (approve) دقیقاً همان آیتم را
(بر پایهٔ tid + field=labels + هشِ محتوایِ برچسب‌های oct) مجاز کند. این گیت اثرِ بیرونی را
*کم* می‌کند (byte-parity لازم نیست — رفتار فقط سخت‌گیرانه‌تر می‌شود).

اثبات‌ها (صفر شبکهٔ واقعی، صفر کلیدِ واقعی — seamِ _transport و choke-pointِ _request جاسوسی می‌شوند):
  ۱) هر سه فلگ مسلح + بدونِ رأی → صفر PUT (تابعِ PUT هرگز صدا نمی‌خورد)؛ نوتِ صادقِ «منتظرِ رأی».
  ۲) هر سه فلگ مسلح + رأیِ معتبر → جریان تا مرزِ PUT می‌رسد (PUT با fake بلاک/جعل، نه HTTP واقعی).
  ۳) رأیِ آیتمِ A، آیتمِ B را مجاز نمی‌کند (بایندِ per-item بر پایهٔ tid).
  ۴) HALT فعال → صفر PUT، صرف‌نظر از وجودِ رأی‌ها.
  ۵) خاموش‌بودنِ هر کدام از سه فلگ → صفر PUT (بدونِ تغییر): فلگِ PS_WRITEBACK مستقیم؛
     دو فلگِ دیگر ساختاراً در caller (wiring.acct_beat) پیش از sync_network گیت می‌شوند.
  ۶) ساختاری: مسیرِ نوشتن هیچ settle/effector/approval_channel/tg_api را import نمی‌کند؛
     هیچ urllib/http/socketِ واقعی در تست‌ها لمس نمی‌شود (فقط seamِ fake).

اجرا: REAL_VAULT=worktree ORG_ROOT=worktree python -X utf8 _ops/tests/test_ps_writeback_verdict.py
"""
from __future__ import annotations

import ast
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness  # noqa: E402
ENV = harness.setup("ps_writeback_verdict")

import ps_writeback as pw   # noqa: E402

FAKE_KEY = "TEST-WBV-KEY-DO-NOT-USE"   # جعلی — هرگز شبکه، هرگز واقعی
_THREE_FLAGS = ("OCTOPUS_WIRE_PS_WRITEBACK", "ACCT_BEAT_SYNC", "OCTOPUS_WIRE_POCKETSMITH")
_TMP = Path(tempfile.mkdtemp(prefix="pswbv-test-"))
_checks = 0


def check(name: str, cond: bool) -> None:
    global _checks
    _checks += 1
    if not cond:
        print(f"✗ {name}")
        sys.exit(1)
    print(f"✓ {name}")


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
    """صفِ پاسخ‌ها + ضبطِ درخواست‌ها. اگر خالی شود IndexError می‌دهد (نه شبکهٔ واقعی)."""

    def __init__(self, actions):
        self.actions = list(actions)
        self.calls: list[dict] = []

    def __call__(self, req, timeout):
        self.calls.append({"method": req.get_method(), "url": req.full_url,
                           "body": (json.loads(req.data.decode("utf-8")) if req.data else None)})
        a = self.actions.pop(0)
        if isinstance(a, Exception):
            raise a
        return a

    def puts(self):
        return [c for c in self.calls if c["method"] == "PUT"]

    def gets(self):
        return [c for c in self.calls if c["method"] == "GET"]


def _arm_all() -> None:
    for f in _THREE_FLAGS:
        os.environ[f] = "1"


def _disarm_all() -> None:
    for f in _THREE_FLAGS:
        os.environ.pop(f, None)


def _p(tag: str) -> tuple[Path, Path]:
    return _TMP / f"q-{tag}.jsonl", _TMP / f"a-{tag}.jsonl"


# ── choke-pointِ PUT را جاسوسی کن: مستقیماً ثابت کنیم تابعِ PUT اصلاً صدا نمی‌خورد ──
_orig_request = pw._request
_put_attempts: list[dict] = []


def _spy_request(method, path, body=None, **kw):
    if method == "PUT":
        _put_attempts.append({"path": path, "body": body})
    return _orig_request(method, path, body, **kw)


_orig_transport = pw._transport
_orig_halted = pw._halted
try:
    pw._request = _spy_request
    pw._halted = lambda: None            # هرمتیک: پیش‌فرض not-halted (تستِ HALT جدا set می‌کند)

    # ─── ۱) هر سه فلگ مسلح + بدونِ رأی → صفر PUT، نوتِ صادق، آیتم در صف می‌ماند ───
    _arm_all()
    _put_attempts.clear()
    q, a = _p("noverdict")
    pw.enqueue("500001", "armin", "expense", queue_path=q)
    ft = FakeTransport([FakeResp({"id": 500001, "labels": ["فروشگاه"]})])   # فقط GET؛ هیچ PUT
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("بدونِ رأی: تابعِ PUT اصلاً صدا نخورد (choke-point)", _put_attempts == [])
    check("بدونِ رأی: هیچ درخواستِ PUT به شبکه (fake)", ft.puts() == [])
    check("بدونِ رأی: written=0 و awaiting_verdict=1", r["written"] == 0 and r.get("awaiting_verdict") == 1)
    check("بدونِ رأی: آیتم در صف می‌ماند (kept)، ok صادق",
          r["ok"] and r["kept"] == 1 and len(pw._read_queue(q)) == 1)
    check("بدونِ رأی: نوتِ صادقِ «منتظرِ رأی»", "منتظرِ رأی" in r["note"])
    check("بدونِ رأی: لاگِ ممیزی «no-owner-verdict-skipped» دارد",
          "no-owner-verdict-skipped" in a.read_text("utf-8"))

    # ─── ۲) هر سه فلگ مسلح + رأیِ معتبر → جریان تا مرزِ PUT می‌رسد (PUT با fake) ───
    _put_attempts.clear()
    q, a = _p("valid")
    pw.enqueue("500002", "armin", "expense", queue_path=q)
    vr = pw.record_owner_verdict("500002", "armin", "expense", queue_path=q)   # کنشِ صریحِ مالک
    check("ثبتِ رأیِ مالک موفق + هشِ ۶۴-hex", vr["recorded"] and len(vr["content_sha256"]) == 64)
    ft = FakeTransport([FakeResp({"id": 500002, "labels": ["فروشگاه"]}),          # GET
                        FakeResp({"id": 500002, "labels": ["فروشگاه", "oct-مالک-آرمین"]})])  # PUT(fake)
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("رأیِ معتبر: گارد رد شد و جریان به مرزِ PUT رسید (تابعِ PUT صدا خورد)",
          len(_put_attempts) == 1 and _put_attempts[0]["path"] == "/transactions/500002")
    check("رأیِ معتبر: PUT به مرزِ شبکه (fake) رسید — نه HTTP واقعی",
          len(ft.puts()) == 1 and ft.puts()[0]["url"].endswith("/transactions/500002"))
    check("رأیِ معتبر: written=1، awaiting=0، صف خالی",
          r["written"] == 1 and r.get("awaiting_verdict") == 0 and not pw._read_queue(q))
    check("رأیِ معتبر: بدنهٔ PUT برچسب‌های merge‌شده (برچسبِ مالک محفوظ)",
          ft.puts()[0]["body"] == {"labels": "فروشگاه,oct-مالک-آرمین,oct-نوع-خرج"})

    # ─── ۳) بایندِ per-item: رأیِ A آیتمِ B را مجاز نمی‌کند (کلید = tid) ──────────
    _put_attempts.clear()
    q, a = _p("bind")
    pw.enqueue("700001", "armin", "expense", queue_path=q)   # A
    pw.enqueue("700002", "armin", "expense", queue_path=q)   # B (همان owner/ptype، tidِ متفاوت)
    pw.record_owner_verdict("700001", "armin", "expense", queue_path=q)   # فقط A تأیید شد
    ft = FakeTransport([FakeResp({"labels": []}),                   # GET A
                        FakeResp({"labels": ["oct-مالک-آرمین"]}),   # PUT A (fake)
                        FakeResp({"labels": []})])                  # GET B (بعد گیت بلاک)
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    put_paths = [p["path"] for p in _put_attempts]
    check("بایند: فقط A پوت شد، B هرگز (رأیِ A مجوزِ B نیست)",
          put_paths == ["/transactions/700001"])
    check("بایند: written=1 (A) و awaiting_verdict=1 (B)",
          r["written"] == 1 and r.get("awaiting_verdict") == 1)
    left = [it["tid"] for it in pw._read_queue(q)]
    check("بایند: B در صف می‌ماند، A حذف شد", left == ["700002"])

    # هشِ محتوا واقعاً per-tid فرق می‌کند (اثباتِ سطحِ پایین)
    ha = pw._verdict_content_hash("700001", "labels", ["oct-مالک-آرمین", "oct-نوع-خرج"])
    hb = pw._verdict_content_hash("700002", "labels", ["oct-مالک-آرمین", "oct-نوع-خرج"])
    check("هشِ محتوا per-tid یکتا است (A≠B با همان برچسب‌ها)",
          bool(ha) and bool(hb) and ha != hb and len(ha) == 64)

    # ─── ۴) HALT فعال + رأی موجود → صفر PUT ────────────────────────────────────
    _put_attempts.clear()
    q, a = _p("halt")
    pw.enqueue("500009", "armin", "expense", queue_path=q)
    pw.record_owner_verdict("500009", "armin", "expense", queue_path=q)   # رأی هست، ولی HALT مقدم
    ft = FakeTransport([])
    pw._transport = ft
    pw._halted = lambda: "TEST-HALT"
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    pw._halted = lambda: None
    check("HALT: صفر PUT با وجودِ رأی، صفر شبکه، صف دست‌نخورده",
          _put_attempts == [] and not ft.calls and r["written"] == 0
          and "HALT" in r["note"] and len(pw._read_queue(q)) == 1)

    # ─── ۵) خاموش‌بودنِ فلگ → صفر PUT (بدونِ تغییر) ─────────────────────────────
    _put_attempts.clear()
    q, a = _p("flagoff")
    # اول با فلگ روشن enqueue + رأی بساز، بعد فلگِ PS_WRITEBACK را خاموش کن
    _arm_all()
    pw.enqueue("500010", "armin", "expense", queue_path=q)
    pw.record_owner_verdict("500010", "armin", "expense", queue_path=q)
    os.environ.pop("OCTOPUS_WIRE_PS_WRITEBACK", None)   # یکی از سه فلگ خاموش
    ft = FakeTransport([])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("فلگِ PS_WRITEBACK خاموش: wired=False، صفر PUT، صفر شبکه (حتی با رأی)",
          r["wired"] is False and _put_attempts == [] and not ft.calls and r["written"] == 0)
    _arm_all()

    # caller-gate: دو فلگِ دیگر ساختاراً در wiring.acct_beat پیش از sync_network گیت می‌شوند
    _wiring_src = (_HERE.parent / "wiring.py").read_text("utf-8")
    check("caller-gate: ACCT_BEAT_SYNC + OCTOPUS_WIRE_POCKETSMITH پیش از sync_network گیت می‌شوند",
          'os.environ.get("ACCT_BEAT_SYNC") == "1" and _ps_flag_on()' in _wiring_src
          and "accountant.sync_network()" in _wiring_src)

    # ─── ۶) ساختاری: مسیرِ نوشتن هیچ settle/effector/approval_channel/tg_api import نمی‌کند ─
    _forbidden = {"settle", "effector", "approval_channel", "tg_api"}
    _src = Path(pw.__file__).read_text("utf-8")
    _tree = ast.parse(_src)
    _imports: set[str] = set()
    for node in ast.walk(_tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                _imports.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _imports.add(node.module.split(".")[0])
    check("ساختاری: ps_writeback هیچ‌کدام از settle/effector/approval_channel/tg_api را import نمی‌کند",
          _imports.isdisjoint(_forbidden))
    check("ساختاری: هیچ‌کدام از آن ماژول‌ها با importِ ps_writeback واردِ sys.modules نشدند",
          not any(m in sys.modules for m in _forbidden))
    # مسیرِ writeback فقط از mission_contract برای هشِ محتوا بازاستفاده می‌کند (reuse، نه اختراع)
    check("ساختاری: هشِ per-item از mission_contract.content_sha256 بازاستفاده می‌شود",
          "mission_contract" in _imports or "mission_contract" in _src)
    # هیچ urllib/http/socketِ واقعی: تنها seamِ شبکه _transport است و در همهٔ تست‌ها fake بود
    check("ساختاری: تنها seamِ شبکه (_transport) در سراسرِ تست fake بود (صفر urlopen واقعی)",
          pw._transport is not _orig_transport)

    # ─── ۷) D1-hardening: رأیِ منقضی (کهنه‌تر از VERDICT_TTL_SEC) → صفر PUT ────────
    _put_attempts.clear()
    q, a = _p("expired")
    pw.enqueue("500020", "armin", "expense", queue_path=q)
    pw.record_owner_verdict("500020", "armin", "expense", queue_path=q)
    _vp = pw._verdict_path(queue_path=q)
    _recs = pw._read_verdicts(_vp)
    for _rc in _recs:                          # ts_epoch را به گذشتهٔ دور ببر → منقضی
        _rc["ts_epoch"] = time.time() - pw.VERDICT_TTL_SEC - 1000
    _vp.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in _recs) + "\n", "utf-8")
    ft = FakeTransport([FakeResp({"id": 500020, "labels": ["فروشگاه"]})])   # فقط GET
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("منقضی: رأیِ کهنه صفر PUT (choke-point) + awaiting=1 + صفر شبکه",
          _put_attempts == [] and ft.puts() == [] and r["written"] == 0
          and r.get("awaiting_verdict") == 1)

    # ─── ۸) D1-hardening single-use: پس از PUTِ اول، replayِ همان محتوا → صفر PUT ─
    _put_attempts.clear()
    q, a = _p("singleuse")
    pw.enqueue("500021", "armin", "expense", queue_path=q)
    pw.record_owner_verdict("500021", "armin", "expense", queue_path=q)
    ft = FakeTransport([FakeResp({"id": 500021, "labels": ["فروشگاه"]}),                     # GET1
                        FakeResp({"id": 500021, "labels": ["فروشگاه", "oct-مالک-آرمین"]})])  # PUT1(fake)
    pw._transport = ft
    r1 = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("single-use: PUTِ اول انجام شد (written=1، یک PUT)",
          len(_put_attempts) == 1 and r1["written"] == 1)
    _put_attempts.clear()
    pw.enqueue("500021", "armin", "expense", queue_path=q)   # replayِ همان tid/محتوا
    ft2 = FakeTransport([FakeResp({"id": 500021, "labels": ["فروشگاه"]})])   # GET؛ oct نیست → changed=True
    pw._transport = ft2
    r2 = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("single-use: replayِ همان محتوا صفر PUT (رأی مصرف شده = consumed) + awaiting=1",
          _put_attempts == [] and ft2.puts() == [] and r2["written"] == 0
          and r2.get("awaiting_verdict") == 1)

    # ─── ۹) رأیِ با هشِ نامتطبق (non-owner/forged/wrong-scope) → صفر PUT ──────────
    _put_attempts.clear()
    q, a = _p("wronghash")
    pw.enqueue("500022", "armin", "expense", queue_path=q)
    _vp = pw._verdict_path(queue_path=q)
    _vp.parent.mkdir(parents=True, exist_ok=True)
    _bad = {"ts": "x", "ts_epoch": time.time(), "tid": "500022", "field": "labels",
            "owner": "armin", "ptype": "expense", "content_sha256": "0" * 64, "verdict": "approve"}
    _vp.write_text(json.dumps(_bad, ensure_ascii=False) + "\n", "utf-8")
    ft = FakeTransport([FakeResp({"id": 500022, "labels": ["فروشگاه"]})])
    pw._transport = ft
    r = pw.flush(queue_path=q, audit_path=a, key=FAKE_KEY)
    check("هشِ نامتطبق: رأیِ approve با content_sha256 غلط صفر PUT (فقط بایندِ دقیقِ per-item مجاز)",
          _put_attempts == [] and ft.puts() == [] and r["written"] == 0
          and r.get("awaiting_verdict") == 1)

finally:
    pw._request = _orig_request
    pw._transport = _orig_transport
    pw._halted = _orig_halted
    _disarm_all()

print(f"\nهمه سبز — {_checks} چک ✅")
