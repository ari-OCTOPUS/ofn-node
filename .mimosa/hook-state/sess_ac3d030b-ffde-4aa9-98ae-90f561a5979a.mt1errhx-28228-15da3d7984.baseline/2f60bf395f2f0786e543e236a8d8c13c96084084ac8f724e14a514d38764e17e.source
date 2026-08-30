#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_spine_sanitize.py — بهداشتِ ساختاریِ payload داخلِ event_spine.dual_write (D4، ITEM 2).

defense-in-depth: قبلاً بهداشت فقط در spine_adapters.sanitize_payload بود؛ حالا خودِ dual_write
هم صافی می‌زند تا callerِ مستقیم (غیرآداپتور: verdict_recorder / wiring) نتواند متنِ خام/PII
(body/text/prompt/email/…) را persist کند.

قیود:
- callerِ مستقیمِ dual_write با payloadِ حاویِ متنِ خام → رویدادِ ذخیره‌شده هیچ متنِ خام ندارد.
- فیلدهای ID/اسکالرِ مشروع (int/float/bool/strِ کوتاهِ snake_case) حفظ می‌شوند.
- double-sanitize (آداپتور سپس dual_write) idempotent است.
- هویت/کلیدِ idempotency تغییر نمی‌کند (از corr/type/domain/subject/mission ساخته می‌شود، نه payload).
- صفر شبکه/effector (ast). $0 آفلاین، spine روی temp.
"""
import ast
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "spine"),
           str(_HERE.parent / "outcomes"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("spine-sanitize")

import event_spine as es          # noqa: E402
import spine_adapters as esx      # noqa: E402


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


def _spine(td):
    return es.EventSpine(path=Path(td) / "spine.db")


def _on():
    class _C:
        def __enter__(self):
            self.p = os.environ.get(es.FLAG)
            os.environ[es.FLAG] = "1"
            return self

        def __exit__(self, *a):
            if self.p is None:
                os.environ.pop(es.FLAG, None)
            else:
                os.environ[es.FLAG] = self.p
    return _C()


_RAW_MARKERS = ["SECRETBODY_MARKER", "leak@example.com", "PROMPTLEAK_MARKER",
                "DESCLEAK_MARKER", "0400-000-000-MARKER", "John Applicant MARKER"]


def _raw_payload():
    return {
        # کلیدهای متن‌خام (block-list) — باید ساختاراً حذف شوند
        "body": "SECRETBODY_MARKER long raw text of the lead message that must never persist",
        "email": "leak@example.com",
        "prompt": "PROMPTLEAK_MARKER",
        "description": "DESCLEAK_MARKER",
        "phone": "0400-000-000-MARKER",
        "applicant_name": "John Applicant MARKER",
        # مقادیرِ ساختاراً نامعتبر — حذف
        "nested": {"a": 1},
        "items": [1, 2, 3],
        "toolong": "x" * 200,
        "multiline": "line1\nline2",
        # فیلدهای مشروعِ ID/اسکالر — باید حفظ شوند
        "score": 80,
        "ratio": 0.5,
        "ok": True,
        "leg_id": "leg-lead-01",
        "receipt_id": "dr_0123456789abcdef",
        "verdict": "ok",
    }


# ── (a) callerِ مستقیم با متنِ خام → صفر متنِ خام در رویداد ────────────────────────
def t_direct_dual_write_strips_raw_text():
    with _on(), _tmp() as td:
        sp = _spine(td)
        try:
            ev = {"event_type": "delivered", "domain": "lead", "correlation_id": "corr-raw",
                  "mission_id": "mis-raw", "subject": "lead:LD1", "trust": "GRADED",
                  "producer": "direct.caller", "payload": _raw_payload()}
            out = es.dual_write(sp, ev)
            assert out["published"] is True, out
            rows = sp.events(correlation_id="corr-raw")
            assert len(rows) == 1, rows
            pj = rows[0]["payload_json"]
            for marker in _RAW_MARKERS:
                assert marker not in pj, f"متنِ خام نشت کرد: {marker!r} در {pj}"
            for blocked in ("body", "email", "prompt", "description", "phone",
                            "applicant_name", "nested", "items", "toolong", "multiline"):
                assert f'"{blocked}"' not in pj, f"کلیدِ ممنوع باقی ماند: {blocked}"
        finally:
            sp.close()


# ── (b) فیلدهای ID/اسکالرِ مشروع حفظ می‌شوند ──────────────────────────────────────
def t_id_and_scalar_fields_preserved():
    import json
    with _on(), _tmp() as td:
        sp = _spine(td)
        try:
            ev = {"event_type": "delivered", "domain": "lead", "correlation_id": "corr-keep",
                  "subject": "lead:LD2", "trust": "GRADED", "producer": "direct.caller",
                  "payload": _raw_payload()}
            out = es.dual_write(sp, ev)
            assert out["published"] is True, out
            pj = json.loads(sp.events(correlation_id="corr-keep")[0]["payload_json"])
            assert pj.get("score") == 80 and pj.get("ratio") == 0.5 and pj.get("ok") is True, pj
            assert pj.get("leg_id") == "leg-lead-01", pj
            assert pj.get("receipt_id") == "dr_0123456789abcdef", pj
            assert pj.get("verdict") == "ok", pj
        finally:
            sp.close()


# ── (c) double-sanitize idempotent (آداپتور سپس dual_write = همان نتیجه) ──────────
def t_double_sanitize_idempotent():
    p = _raw_payload()
    once = es._sanitize_payload(p)
    twice = es._sanitize_payload(once)
    assert once == twice, (once, twice)
    # آینه با آداپتور: قواعدِ یکسان → همان خروجی
    assert es._sanitize_payload(p) == esx.sanitize_payload(p), "باید آینهٔ spine_adapters باشد"
    # پایداری از مسیرِ persist: payloadِ pre-sanitizedِ آداپتور، دوباره در dual_write → همان
    with _on(), _tmp() as td:
        sp = _spine(td)
        try:
            base = {"event_type": "delivered", "domain": "lead", "trust": "GRADED",
                    "producer": "x"}
            r1 = es.dual_write(sp, {**base, "correlation_id": "c-raw", "subject": "s1",
                                    "payload": p})
            r2 = es.dual_write(sp, {**base, "correlation_id": "c-pre", "subject": "s2",
                                    "payload": esx.sanitize_payload(p)})
            pj1 = sp.events(correlation_id="c-raw")[0]["payload_json"]
            pj2 = sp.events(correlation_id="c-pre")[0]["payload_json"]
            assert pj1 == pj2, (pj1, pj2)
        finally:
            sp.close()


# ── (d) هویت/کلیدِ idempotency از payload مستقل است (sanitize آن را عوض نمی‌کند) ──
def t_identity_and_idempotency_unchanged():
    with _on(), _tmp() as td:
        sp = _spine(td)
        try:
            ident = {"event_type": "delivered", "domain": "lead", "correlation_id": "corr-id",
                     "mission_id": "mis-id", "subject": "lead:LD3", "trust": "GRADED",
                     "producer": "p"}
            eid1 = sp.publish({**ident, "payload": es._sanitize_payload(_raw_payload())})
            assert eid1, "درجِ اول باید موفق شود"
            # همان هویت، payloadِ خامِ کاملاً متفاوت → باید duplicate باشد (identity از payload نیست)
            out2 = es.dual_write(sp, {**ident, "payload": _raw_payload()})
            assert out2["published"] is False and out2["reason"] == "duplicate", out2
            row = sp.events(correlation_id="corr-id")[0]
            # کلیدِ idempotency = _sha روی هویت (نه payload)
            expected = es._sha({"c": "corr-id", "t": "delivered", "d": "lead",
                                "s": "lead:LD3", "m": "mis-id"})
            assert row["idempotency_key"] == expected, (row["idempotency_key"], expected)
            assert row["event_id"] == eid1
        finally:
            sp.close()


# ── (e) flag-off dual_write هنوز no-op (parity — sanitize چیزی را زودتر اجرا نمی‌کند) ──
def t_flag_off_still_noop():
    with _tmp() as td:                 # فلگ خاموش
        sp = _spine(td)
        try:
            out = es.dual_write(sp, {"event_type": "delivered", "domain": "lead",
                                     "correlation_id": "c-off", "payload": _raw_payload()})
            assert out == {"published": False, "reason": "flag-off"}, out
            assert sp.events(correlation_id="c-off") == [], "flag خاموش نباید بنویسد"
        finally:
            sp.close()


# ── (f) ساختاری: صفر شبکه/effector در event_spine ────────────────────────────────
def t_structural_zero_network():
    src = (_HERE.parent / "spine" / "event_spine.py").read_text("utf-8")
    tree = ast.parse(src)
    banned_mods = {"socket", "urllib", "requests", "http", "smtplib", "ftplib", "telnetlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in banned_mods, f"importِ شبکه: {a.name}"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_mods, node.module


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} spine_sanitize: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
