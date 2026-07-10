#!/usr/bin/env python3
"""تست S (S-fix-3) — protective-override واقعاً enforce می‌شود، نه فقط alert/flag. $0 آفلاین.

درسِ ۳ دورِ قبل: تستِ ساختاریِ «flag set شد» کافی نیست — گپ این بود که flag **مصرف** نمی‌شد و
تصمیم **بعد از** epoch/fitness گرفته می‌شد. این تست دقیقاً همان دو نقص را می‌گیرد:
  (۱) رفتاری: protective_override برای pain>0.7 → override غیرقابل‌سرکوب + protective_halt.
  (۲) ساختاری-هدف‌مند: در organism، epoch و fitness روی `not _protective_skip` گِیت‌اند (flag مصرف می‌شود)
      و تصمیمِ neural **پیش از** epoch است؛ بدونِ continue (busy-loop ban)؛ sleep همیشه.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("organism-protective")
sys.path.insert(0, str((harness.REAL_VAULT / r"_ops")))
sys.path.insert(0, str((harness.REAL_VAULT / r"_ops\budget")))
import wiring  # noqa: E402

ORG = (harness.REAL_VAULT / r"_ops\organism.py").read_text("utf-8")
_BODY = ORG[ORG.index("while True:"):]


def t_protective_halt_decision():
    r = wiring.protective_override({"pain": {"level": 0.85}, "reflexes": []})
    assert r["override"] and r["suppressible"] is False and r["action"] == "protective_halt", r


def t_low_pain_no_override():
    r = wiring.protective_override({"pain": {"level": 0.1}, "reflexes": []})
    assert r["override"] is False, r


def t_critical_reflex_non_suppressible():
    r = wiring.protective_override({"pain": {"level": 0.0},
                                   "reflexes": [{"triggered": True, "severity": "critical", "name": "budget"}]})
    assert r["override"] and r["suppressible"] is False, r


def t_epoch_gated_on_protective_skip():
    # گپِ اصلی: flag باید مصرف شود — epoch داخلِ گاردِ `not _protective_skip`
    assert re.search(r"if not _protective_skip[^\n]*:\s*\n\s+rec = governor_epoch\.run_epoch\(\)", _BODY), \
        "epoch باید روی `not _protective_skip` گیت باشد (flag واقعاً مصرف شود)"


def t_fitness_gated_on_protective_skip():
    assert re.search(r"if not _protective_skip[^\n]*:\s*\n\s+fit = fitness\.compute\(\)", _BODY), \
        "fitness/daily باید روی `not _protective_skip` گیت باشد"


def t_decision_before_work():
    # تصمیمِ protective باید پیش از epoch باشد (وگرنه نمی‌تواند جلوش را بگیرد)
    i_prot = _BODY.find("_protective_skip = True")
    i_epoch = _BODY.find("rec = governor_epoch.run_epoch()")
    assert 0 < i_prot < i_epoch, ("تصمیمِ protective باید پیش از اجرای epoch باشد", i_prot, i_epoch)


def t_no_busyloop_continue():
    # هیچ continue در بدنهٔ while (از sleep می‌پرد → busy-loop)
    assert not re.search(r"\n\s+continue\b", _BODY), "continue در tick ممنوع (busy-loop)"


def t_sleep_always_reached():
    # time.sleep در سطحِ بدنهٔ while (نه داخلِ گاردِ protective) → همیشه اجرا.
    # CARDIAC-ALLOMETRY: sleep ممکن است داینامیک باشد (OCTOPUS_WIRE_BIO) ولی باید همیشه
    # در انتها اجرا شود. پذیرفتن هر دو: static (TICK_SECONDS) یا dynamic (متغیر).
    assert re.search(r"\n        time\.sleep\(", ORG), \
        "time.sleep باید همیشه انتهای while اجرا شود (busy-loop ban)"


if __name__ == "__main__":
    failed = harness.run([
        ("pain>0.7 → protective_halt غیرقابل‌سرکوب", t_protective_halt_decision),
        ("pain پایین → بدونِ override", t_low_pain_no_override),
        ("reflex بحرانی → غیرقابل‌سرکوب", t_critical_reflex_non_suppressible),
        ("epoch روی not _protective_skip گیت (flag مصرف)", t_epoch_gated_on_protective_skip),
        ("fitness روی not _protective_skip گیت", t_fitness_gated_on_protective_skip),
        ("تصمیمِ protective پیش از epoch", t_decision_before_work),
        ("بدونِ continue (busy-loop ban)", t_no_busyloop_continue),
        ("time.sleep همیشه اجرا می‌شود", t_sleep_always_reached),
    ])
    sys.exit(1 if failed else 0)
