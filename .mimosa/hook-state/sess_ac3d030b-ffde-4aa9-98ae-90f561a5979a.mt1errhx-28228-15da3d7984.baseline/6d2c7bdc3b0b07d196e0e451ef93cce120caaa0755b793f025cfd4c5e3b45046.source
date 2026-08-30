#!/usr/bin/env python3
"""test_agi2027_control_url_redaction.py — VQ-CAPABILITY-URL-LEAK-001 (برشِ ۳، آیتمِ ۳).

`agi2027_control.integration.format_control_result` قبلاً `web_app_url` را
مستقیماً در متنِ Telegram می‌گذاشت — یک URL ِ حاملِ اعتبار (تونلِ خصوصیِ
mini-app)، همان کلاسِ secret که §۱۰ ِ منشور هرگز در چت نمی‌خواهدش، حتی وقتی
گیرنده خودِ مالک است.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("agi2027-control-url-redaction")
_OPS = harness.SELF_OPS
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from agi2027_control.integration import format_control_result  # noqa: E402

_SECRET_URL = "https://sneaky-subdomain-abc123.trycloudflare.com/miniapp"


def t_web_app_url_never_appears_in_the_formatted_text():
    text = format_control_result({"ok": True, "status": "READY",
                                  "web_app_url": _SECRET_URL})
    assert _SECRET_URL not in text, text
    assert "trycloudflare" not in text, text
    assert "MiniApp" in text, "باید هنوز بگوید MiniApp آماده شد، فقط بدونِ URL"


def t_no_web_app_url_key_means_no_miniapp_line():
    text = format_control_result({"ok": True, "status": "READY"})
    assert "MiniApp" not in text, text


def t_other_fields_are_unaffected():
    text = format_control_result({"ok": True, "status": "READY",
                                  "web_app_url": _SECRET_URL,
                                  "reason": "all good"})
    assert "all good" in text, text


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'PASS' if not failed else 'FAIL'} test_agi2027_control_url_redaction: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
