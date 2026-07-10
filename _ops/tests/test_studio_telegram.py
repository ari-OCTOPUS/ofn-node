#!/usr/bin/env python3
"""تست studio_telegram — سطحِ تلگرامِ صبا (Project-F). $0 آفلاین، بدونِ شبکه/توکن.
walls: no-op بی‌token/chat_id · فقط chat_idِ صبا · صفر رسانه/PII در پیام · دوکلیده (submit→pending) ·
self-cert اجباری · halt مقدم · secret-guard (token masked) · ناشناخته→quarantine · isolation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("studio-telegram")
_STUDIO = (harness.REAL_VAULT / r"03 - Projects\اونلی فنز\studio")
if str(_STUDIO) not in sys.path:
    sys.path.insert(0, str(_STUDIO))
from studio_telegram import StudioTelegram  # noqa: E402
from content_studio import ContentStudio, COMPLIANCE_CHECKS  # noqa: E402


class _Rec:
    def __init__(self):
        self.sent = []

    def post(self, url, body, timeout_s=10.0):
        self.sent.append(body)
        return {"ok": True, "result": {}}

    def getter(self, updates):
        calls = {"n": 0}

        def _get(url, timeout_s):
            calls["n"] += 1
            return {"ok": True, "result": updates if calls["n"] == 1 else []}
        return _get


def _bot(rec, updates=None, token="T:secret", saba=555):
    return StudioTelegram(studio=ContentStudio(), token=token, saba_chat_id=saba,
                          http_get=rec.getter(updates or []), http_post=rec.post,
                          longpoll_timeout=0)


def _msg(chat_id, text):
    return {"update_id": 1, "message": {"chat": {"id": chat_id}, "text": text}}


def _cb(chat_id, data):
    return {"update_id": 2, "callback_query": {"data": data, "message": {"chat": {"id": chat_id}}}}


def t_noop_without_token():
    b = StudioTelegram(token="", saba_chat_id=555)
    assert b.wired is False and b.poll_once() == 0 and b.send("x") is False


def t_noop_without_saba():
    assert StudioTelegram(token="T:x", saba_chat_id=None).wired is False


def t_only_saba_processed():
    rec = _Rec(); b = _bot(rec, [_msg(999, "/start")])   # chat_idِ غیرِ صبا
    b.poll_once()
    assert rec.sent == [], rec.sent                        # هیچ پاسخی به غیرمجاز


def t_start_renders_menu():
    rec = _Rec(); b = _bot(rec, [_msg(555, "/start")]); b.poll_once()
    assert rec.sent and "استودیو" in rec.sent[0]["text"]
    assert "inline_keyboard" in json.dumps(rec.sent[0], ensure_ascii=False)


def t_submit_two_key_pending():
    rec = _Rec()
    b = _bot(rec, [_msg(555, "/submit عنوان | faceless,feet_only,no_explicit,over_18")])
    b.poll_once()
    assert rec.sent and "در انتظارِ تأییدِ آری" in rec.sent[0]["text"]   # دوکلیده، نه انتشار


def t_submit_incomplete_cert_fails():
    rec = _Rec(); b = _bot(rec, [_msg(555, "/submit t | faceless")]); b.poll_once()
    assert rec.sent and "ثبت نشد" in rec.sent[0]["text"]                 # self-cert اجباری


def t_analytics_zero_pii_media():
    rec = _Rec(); b = _bot(rec, [_cb(555, "studio:analytics")]); b.poll_once()
    assert rec.sent and "تجمیعی" in rec.sent[0]["text"]
    body = json.dumps(rec.sent[0], ensure_ascii=False)
    for forbidden in ("photo", "video", "\"media\"", "document", "@", "http"):
        assert forbidden not in body, forbidden                          # صفر رسانه/PII


def t_halt_supreme():
    rec = _Rec(); b = _bot(rec, [_msg(555, "/halt")]); b.poll_once()
    assert b._studio.is_halted
    assert b._studio.submit_draft("x", {c: True for c in COMPLIANCE_CHECKS})["ok"] is False


def t_token_masked_no_leak():
    b = StudioTelegram(token="1234567:SECRETSECRET", saba_chat_id=1)
    assert "SECRET" not in repr(b) and "1234" in repr(b)


def t_unknown_input_quarantined():
    rec = _Rec(); b = _bot(rec, [_msg(555, "سلام یک عکس بفرست")]); n = b.poll_once()
    assert n == 1 and rec.sent == [] and len(b._quarantine) == 1         # DATA، بی‌اجرا


def t_isolation_no_production_import():
    # فقط خطوطِ importِ واقعی را بسنج (نه اشارهٔ داخلِ docstring/کامنت)
    src = (_STUDIO / "studio_telegram.py").read_text("utf-8")
    imports = " ".join(ln.strip() for ln in src.splitlines()
                       if ln.strip().startswith(("import ", "from ")))
    for forbidden in ("organ_gate", "money_gate", "budget_gate", "chrono",
                      "opslib", "unified_bus", "_ops", "money"):
        assert forbidden not in imports, (forbidden, imports)


if __name__ == "__main__":
    failed = harness.run([
        ("no-op بدونِ token", t_noop_without_token),
        ("no-op بدونِ chat_idِ صبا", t_noop_without_saba),
        ("فقط chat_idِ صبا پردازش می‌شود", t_only_saba_processed),
        ("/start منوی استودیو + کیبورد", t_start_renders_menu),
        ("submit → دوکلیده (در انتظارِ آری)", t_submit_two_key_pending),
        ("self-cert ناقص → رد", t_submit_incomplete_cert_fails),
        ("آنالیز = صفر رسانه/PII", t_analytics_zero_pii_media),
        ("/halt مقدم → submit مسدود", t_halt_supreme),
        ("token در repr masked", t_token_masked_no_leak),
        ("ورودیِ ناشناخته → quarantine", t_unknown_input_quarantined),
        ("isolation: بدونِ import production", t_isolation_no_production_import),
    ])
    sys.exit(1 if failed else 0)
