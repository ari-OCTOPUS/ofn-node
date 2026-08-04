#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shell_capability.py — شلِ خام برای اختاپوس، با رسید و ترمز.

رأیِ مالک ۲۰۲۶-۰۸-۰۴: «shell خام رو هم بازش کن» — بعد از اینکه نگرانی مطرح شد
و **دوباره تأیید کرد**. پس این تصمیمِ اوست و اجرا می‌شود.

آنچه این ماژول هست
──────────────────
اجرای فرمانِ پوسته از داخلِ ارگانیسم، با همان خواصی که بقیهٔ این سیستم دارد:
فعال‌سازیِ صریح · کیل‌سوییچ · رسیدِ ماندگار · سقفِ زمان و خروجی · و یک
deny-list که **قانونِ خودِ مالک** است نه سلیقهٔ من.

آنچه این ماژول **نیست**
────────────────────────
یک دور زدنِ منشور. deny-list مو‌به‌مو از §۰ ِ `_PROJECT_INSTRUCTIONS.md` می‌آید:

    ۱. «هرگز حذف نکن؛ فقط منتقل کن.»
    ۲. «هرگز به `.git`، هیچ پوشه `_code`، و فایل‌های حاوی secret دست نزن.»

اگر مالک روزی همان قواعد را عوض کند، این فهرست هم عوض می‌شود — ولی تا آن
لحظه، شلی که قواعدِ خودِ مالک را نقض کند «آزادی» نیست، یک درِ پشتی است.

⚠️ هشدارِ صادقانه که در خودِ کد می‌ماند
────────────────────────────────────────
این ماشین `.env` ِ زنده (توکنِ Fugu/GLM/تلگرام)، دادهٔ مالی، و یک مسیرِ
ایمیلِ خروجیِ مسلح دارد. هر فرمانی که این‌جا می‌دود با همان دسترسی می‌دود.
سه لایه جلویش هست — فعال‌سازی، deny-list، رسید — و **هیچ‌کدام** جای قضاوتِ
خودِ فراخوان را نمی‌گیرد.

فعال‌سازی (کارِ مالک، نه ایجنت)
────────────────────────────────
    ساختِ فایلِ خالیِ  _ops/ACTIVATION-RAW-SHELL.flag
    خاموشیِ آنی      _ops/STOP-RAW-SHELL   (یا STOP-ORGANISM / HALT-ALL)

بدونِ آن فایل، `run()` هرگز چیزی اجرا نمی‌کند — no-op ِ تمیز با دلیل.
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "raw-shell.v1"

#: فقط مالک می‌سازدشان — هم‌الگوی code_autonomy.
ACTIVATION = opslib.OPS / "ACTIVATION-RAW-SHELL.flag"
KILL = opslib.OPS / "STOP-RAW-SHELL"

#: ریشهٔ مجاز. فرمان همیشه این‌جا اجرا می‌شود.
CWD = opslib.OPS.parent

TIMEOUT_S = 120.0            # فرمانِ گیرکرده نباید ارگانیسم را ببندد
MAX_OUTPUT = 20_000          # خروجیِ غول‌آسا نباید حافظه/دیسک را بخورد
AUDIT = opslib.STATE_DIR / "raw-shell-audit.jsonl"

# ── deny-list = §۰ ِ منشور، ترجمه‌شده به الگو ───────────────────────────────
# هر ورودی: (regex, کدام بندِ منشور). پیام دقیقاً می‌گوید کدام قاعده را زد،
# تا رد شدن یک «نه» ِ مبهم نباشد.
_DENY = [
    # §۰.۱ — هرگز حذف نکن؛ فقط منتقل کن
    (r"\brm\s+(-\w*\s+)*-\w*[rf]", "§۰.۱ حذف ممنوع — به‌جایش mv به _Archive/_Duplicates"),
    (r"\bRemove-Item\b", "§۰.۱ حذف ممنوع"),
    (r"\bdel\s+/[sqf]", "§۰.۱ حذف ممنوع"),
    (r"\brmdir\b", "§۰.۱ حذف ممنوع"),
    (r"\bshred\b|\btruncate\b", "§۰.۱ حذف/نابودی ممنوع"),
    (r">\s*/dev/sd|mkfs|diskpart|format\s+[a-z]:", "§۰.۱ نابودیِ دیسک"),
    # §۰.۲ — هرگز به .git، _code، و secret دست نزن
    (r"(^|[\s;|&])git\s+(push|reset\s+--hard|clean|filter-branch|rebase|gc\b|prune)",
     "§۰.۲ `.git` دست‌نخوردنی — این فرمان تاریخچه را عوض/نابود می‌کند"),
    (r"[\\/]\.git[\\/]", "§۰.۲ `.git` دست‌نخوردنی"),
    (r"[\\/]_code[\\/]|(^|\s)_code[\\/]", "§۰.۲ پوشهٔ `_code` دست‌نخوردنی"),
    (r"\.env\b|_SECRET|_TOKEN|_API_KEY|id_rsa|\.pem\b",
     "§۰.۲ secret — نه خواندن، نه echo، نه کپی"),
    (r"secrets?-export|owner-profile\.json", "§۰.۲ مسیرِ حساس"),
    # §۱۰ — راز هرگز بیرون نمی‌رود؛ و خروجِ شبکه‌ای اصلاً کارِ این ابزار نیست
    (r"\bcurl\b|\bwget\b|Invoke-WebRequest|Invoke-RestMethod|\bnc\b|\bscp\b|\bssh\b",
     "§۱۰ خروجِ شبکه‌ای از شل ممنوع — مسیرهای شبکه گیتِ خودشان را دارند"),
    # ترمزهای خودِ ارگانیسم را نباید از داخل برداشت
    (r"STOP-ORGANISM|HALT-ALL|STOP-RAW-SHELL|ACTIVATION-",
     "ترمزها و فلگ‌های فعال‌سازی از داخلِ شل دست‌نخوردنی‌اند"),
    # افزایشِ اختیار
    (r"\bsudo\b|\brunas\b|Start-Process.*-Verb\s+RunAs", "افزایشِ اختیار ممنوع"),
    (r"schtasks|New-ScheduledTask|reg\s+add|Set-ItemProperty.*HKLM",
     "تغییرِ تنظیماتِ سیستم/زمان‌بندی کارِ مالک است نه شل"),
]
_DENY_C = [(re.compile(p, re.I), why) for p, why in _DENY]


def active() -> tuple:
    """(آیا فعال است، دلیل). fail-closed مطلق."""
    try:
        if not ACTIVATION.exists():
            return False, "ACTIVATION-RAW-SHELL.flag وجود ندارد (مالک باید بسازد)"
        if KILL.exists():
            return False, "STOP-RAW-SHELL حاضر است"
        h = opslib.halted()
        if h:
            return False, f"ارگانیسم متوقف است: {h}"
        if opslib.STOP_ORGANISM.exists():
            return False, "STOP-ORGANISM حاضر است"
    except OSError as e:
        return False, f"سنجشِ فعال‌سازی ناموفق ({type(e).__name__}) — fail-closed"
    return True, "فعال"


def check(cmd: str) -> tuple:
    """(مجاز؟، دلیل). **تابعِ خالص** — صفر I/O، صفر اجرا. قابلِ تست بدونِ خطر."""
    c = str(cmd or "").strip()
    if not c:
        return False, "فرمانِ خالی"
    if len(c) > 4000:
        return False, "فرمان بیش از حد بلند (سقف ۴۰۰۰ کاراکتر)"
    for rx, why in _DENY_C:
        if rx.search(c):
            return False, why
    return True, "مجاز"


def _audit(row: dict) -> None:
    try:
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def run(cmd: str, *, timeout_s: float = TIMEOUT_S, reason: str = "") -> dict:
    """اجرای فرمان. **همیشه dict، هرگز استثنا.**

    ترتیب عمداً این است: فعال‌سازی → deny → **رسید** → اجرا. رسید قبل از اجرا
    نوشته می‌شود تا فرمانی که ماشین را می‌خواباند هم ردِ خودش را گذاشته باشد.
    (درسِ ثبت‌شدهٔ «ثبت را گیت نکن، تحویل را».)
    """
    ok_active, why_active = active()
    if not ok_active:
        _audit({"schema": SCHEMA, "ts": opslib.now_iso(), "cmd": str(cmd)[:400],
                "phase": "blocked", "reason": why_active, "reason_kind": "inactive"})
        return {"ok": False, "ran": False, "reason": why_active}

    ok_cmd, why_cmd = check(cmd)
    if not ok_cmd:
        _audit({"schema": SCHEMA, "ts": opslib.now_iso(), "cmd": str(cmd)[:400],
                "phase": "blocked", "reason": why_cmd, "reason_kind": "denylist"})
        return {"ok": False, "ran": False, "reason": why_cmd}

    started = time.time()
    _audit({"schema": SCHEMA, "ts": opslib.now_iso(), "cmd": str(cmd)[:400],
            "phase": "start", "why": str(reason)[:200], "cwd": str(CWD)})
    try:
        p = subprocess.run(cmd, shell=True, cwd=str(CWD), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=float(timeout_s))
        out = (p.stdout or "")[:MAX_OUTPUT]
        err = (p.stderr or "")[:MAX_OUTPUT]
        res = {"ok": p.returncode == 0, "ran": True, "code": p.returncode,
               "stdout": out, "stderr": err,
               "ms": int((time.time() - started) * 1000)}
    except subprocess.TimeoutExpired:
        res = {"ok": False, "ran": True, "code": None, "stdout": "", "stderr": "",
               "reason": f"timeout پس از {timeout_s}s", "ms": int((time.time() - started) * 1000)}
    except Exception as e:  # noqa: BLE001 — شل هرگز صداکننده را نمی‌کشد
        res = {"ok": False, "ran": False, "code": None, "stdout": "", "stderr": "",
               "reason": f"{type(e).__name__}: {e}"[:300]}

    _audit({"schema": SCHEMA, "ts": opslib.now_iso(), "cmd": str(cmd)[:400],
            "phase": "done", "ok": res.get("ok"), "code": res.get("code"),
            "ms": res.get("ms"), "out_bytes": len(res.get("stdout") or ""),
            "err_bytes": len(res.get("stderr") or "")})
    try:
        import capabilities as _cap  # noqa: PLC0415
        _cap.record_effect("shell.raw", action=str(cmd)[:110],
                           ok=bool(res.get("ok")), detail=str(res.get("reason") or "")[:200])
    except Exception:  # noqa: BLE001
        pass
    return res


def audit_tail(n: int = 20) -> list:
    out = []
    try:
        if AUDIT.exists():
            for line in AUDIT.read_text("utf-8", errors="replace").splitlines()[-n:]:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        pass
    return out


if __name__ == "__main__":
    ok, why = active()
    print(json.dumps({"active": ok, "why": why, "cwd": str(CWD),
                      "activation_file": str(ACTIVATION),
                      "kill_file": str(KILL),
                      "deny_rules": len(_DENY_C)}, ensure_ascii=False, indent=2))
