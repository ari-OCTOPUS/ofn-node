#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""acceptance_journey — سفرِ پذیرشِ بدونِ ناظر: سیستم **خودش را با پیام‌دادن به مالک** می‌سنجد.

    خواستِ مالک (۲۰۲۶-۰۷-۳۱، از تلگرام، دور از لپ‌تاپ):
    «۶ ساعت خودت را از صفر تا صد امتحان کن و آخرش گزارش بده.»

قرارداد (سخت):
  · هر فاز یک **تعاملِ واقعی** است: یک تیک پیام می‌فرستد، تیکِ بعدی از
    **آرتیفکت** می‌سنجد که واقعاً کار کرد یا نه. هرگز از خودمان نمی‌پرسیم.
  · **هرگز poll نمی‌کند.** pollerِ زندهٔ مرکز صاحبِ توکن است؛ یک poller دوم
    یعنی 409 و دزدیدنِ پیامِ مالک. تنها فعلِ ما `send` است.
  · **صداقتِ سخت:** شاهدِ غایب هرگز PASS نمی‌شود. هیچ‌وقت ادعا نمی‌کنیم مالک
    کاری کرده؛ فقط می‌گوییم چه آرتیفکتی دیدیم.
  · **اثباتِ قابلیت (درون‌فرایندی):** مالک ممکن است اصلاً پای تلگرام نباشد؛
    گزارشی پر از «مالک کاری نکرد» صادق ولی بی‌فایده است. پس هر فازِ وابسته
    به مالک، علاوه بر شاهدِ مالک، **خودِ قابلیت** را هم در همین پروسه روی
    ماژولِ **تولیدیِ واقعی** می‌سنجد (هرگز پیاده‌سازیِ دوباره) با صفر آلودگی:
    هر نوشتنی داخلِ tempfile.mkdtemp است و env ِ مسیرها در finally برمی‌گردد.
    نتیجه سه حالت می‌شود و در کارنامه سه گروهِ جدا:
      PASS            = قابلیت سالم **و** تپِ مالک دیده شد
      CAPABILITY-OK   = قابلیت در-پروسه اثبات شد، ولی تپِ مالک نیامد
      BROKEN          = خودِ قابلیت خراب است (بلندترین خبر — همین را می‌خواهد)
    TIMEOUT فقط برای فازی می‌ماند که اثباتِ درون‌فرایندی برایش ممکن نیست.
    خطوطِ شاهد برچسب‌دارند: «مشاهدهٔ مالک: …» در برابر «قابلیت (درون‌فرایندی): …».
  · idempotent: دو تیک در یک پنجره = یک ارسال. هر نوشتن اتمیک (tmp+os.replace).
  · هر فاز داخل try/except خودش است — یک استثنا کلِ تیک را نمی‌کشد.
  · هر شکستِ ارسال = PENDING؛ **مکان‌نما هرگز جلو نمی‌رود**.
  · هرگز `center` را import نمی‌کند (singleton/پورت)، هرگز `poll_updates`.

اجرا: `python -X utf8 acceptance_journey.py --tick` هر ~۱۵ دقیقه (Scheduled Task).
`--status` فقط چاپ می‌کند (صفر ارسال، صفر نوشتن).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/telegram_center
_OPS = _HERE.parent                              # _ops
for _p in (str(_OPS), str(_OPS / "budget"), str(_HERE), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import tg_api          # noqa: E402
import tg_send_log     # noqa: E402 — فقط digest() ِ خالص (نویسنده و خواننده با هم)

# ─── ثابت‌ها ────────────────────────────────────────────────────────────────
JOURNEY_VERSION = "1"
MAX_ATTEMPTS = 3                       # شاهدِ غایب بعد از ۳ تلاش ⇒ TIMEOUT
MAX_STEPS_PER_TICK = 4                 # چند گذارِ فاز در یک تیک (سقفِ ضدِ حلقه)
MAX_SENDS_PER_TICK = 1                 # هرگز بیش از یک پیامِ درخواست در یک تیک
DEFAULT_WINDOW_S = 20 * 60             # پنجرهٔ استانداردِ هر فاز
LEAD_WINDOW_S = 45 * 60                # ضربانِ لوله ~۳۰-۴۰ دقیقه ⇒ پنجرهٔ بلندتر
DEFAULT_DEADLINE_S = 6 * 3600          # سقفِ کلِ سفر — بعدش مستقیم گزارشِ نهایی
STREAM = "journey"                     # برچسبِ رسیدِ خودمان در tg-send-log
TASK_NAME_ENV = "OCTOPUS_JOURNEY_TASK"
# ⚠️ ممیزیِ ۰۷-۳۱ (EVIDENCE-AUDIT §5b): نامِ پیش‌فرضِ قبلی
# «OctopusAcceptanceJourney» با تسکِ زندهٔ واقعی نمی‌خواند — سفر «خودم را
# متوقف کردم» می‌گفت و تسک هر ۱۵ دقیقه بیدار می‌ماند. نامِ واقعی (سنجیده با
# `schtasks /Query`): OCTOPUS-Journey-Tick. env همچنان برنده است.
DEFAULT_TASK_NAME = "OCTOPUS-Journey-Tick"
RAW_SUBDIR = ("10 - Telegram processing", "Raw")

# استریم‌های خودمختارِ سطحِ گروه (ممیزی ۰۷-۳۱، فازِ P6): digestِ دوره‌ای با
# stream=center می‌آید، کارتِ پا با leg-card-*، لوله با lead — هیچ‌کدام «پاسخ
# به فرمانِ مالک» نیستند. پاسخِ فرمانِ گروه هم امروز stream=center دارد
# (center.py:2135 استریم نمی‌دهد) پس از digest جداشدنی نیست؛ تا وقتی مرکز
# استریمِ متمایز (مثلاً cmd-reply) نزند، PASS ِ مالک برای P6 صادقانه ناممکن
# است و حکم از اثباتِ درون‌فرایندی می‌آید — نه از یک ردیفِ نسبت‌ندادنی.
_AUTONOMOUS_GROUP_STREAMS = frozenset({
    "center", "edit", "lead", "center-digest", "center-decision", STREAM})
_AUTONOMOUS_GROUP_PREFIXES = ("leg-card-",)

# نشانه‌های متنِ خودآزمون در store ِ یادآوری — RM-1 ِ زندهٔ ۰۷-۳۱ («خودآزمونِ
# زنجیرهٔ یادآوری (سیستم خودش ساخت)») را یک جلسهٔ ایجنت ساخته بود و ۶۰ ثانیه
# با PASS ِ کاذبِ P4A فاصله داشت. store فیلدِ origin ندارد (reminders.add
# provenance ثبت نمی‌کند) پس این denylist ِ متنی تنها فیلترِ در دسترس است.
_SELF_TEST_MARKERS = ("خودآزمون", "سفرِ پذیرش", "سفر پذیرش", "اثباتِ قابلیت",
                      "acceptance", "journey", "probe", "self-test")

# نامِ نوتِ capture ِ ماشینی: `YYYY-MM-DD HHmm <slug>.md` (قانونِ اساسی §۵؛
# capture.py:277). مهرِ داخلِ نام = زمانِ **ساخت** — برخلافِ mtime که با هر
# لمس (فرمت‌کن، sync، جلسهٔ ایجنت) تازه می‌شود و نوتِ دیروز را «نو» جا می‌زند.
_NOTE_STAMP = re.compile(r"^(\d{4})-(\d{2})-(\d{2}) (\d{2})(\d{2}) ")
# نشانِ رسانهٔ خودِ producer (capture._note_text:258): «منبع: تلگرام · … · [photo]»
# — substring ِ خام روی کلِ بدنه یک لاگِ paste‌شده را هم رسانه می‌شمرد.
_MEDIA_SRC_LINE = re.compile(r"منبع: تلگرام.*\[(photo|voice)\]")

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_LRI, _PDI = "⁦", "⁩"        # ایزولهٔ bidi برای تکه‌های LTR (منشور UX-9)

VERDICT_PASS = "PASS"
VERDICT_PENDING = "PENDING"
VERDICT_PARTIAL = "PARTIAL"   # شاهدِ نیم‌بند — نه سبز، نه هیچ
VERDICT_TIMEOUT = "TIMEOUT"
# قابلیت در همین پروسه روی ماژولِ تولیدی اثبات شد، ولی تپِ مالک دیده نشد.
VERDICT_CAPABILITY_OK = "CAPABILITY-OK"
# خودِ قابلیت خراب است — نقصِ واقعی، بلندترین خطِ کارنامه.
VERDICT_BROKEN = "BROKEN"
VERDICT_WAIT = "WAIT"                  # هنوز موعدش نرسیده — تلاش شمرده نمی‌شود
VERDICT_NOT_DUE = "SCHEDULED-NOT-DUE"
VERDICT_BLOCKED = "BLOCKED"            # پیش‌نیازِ ساختاری غایب (فلگ/پیکربندی)
VERDICT_DEGRADED = "DEGRADED"          # سنجیده شد ولی محیط کامل نبود (P0)
VERDICT_NOT_RUN = "NOT-RUN"

# PARTIAL هم پایانی است: «رسید ولی جواب نگرفت» یک واقعیتِ سنجیده است، نه
# انتظار — تکرارش سبزش نمی‌کند و در کارنامه باید همان‌طور دیده شود.
_TERMINAL = (VERDICT_PASS, VERDICT_PARTIAL, VERDICT_TIMEOUT, VERDICT_NOT_DUE,
             VERDICT_BLOCKED,
             VERDICT_DEGRADED, VERDICT_CAPABILITY_OK, VERDICT_BROKEN)

# برچسبِ خطوطِ شاهد — گروه‌بندیِ کارنامه و چشمِ مالک به همین دو تکیه می‌کند.
OWNER_PREFIX = "مشاهدهٔ مالک: "
CAP_PREFIX = "قابلیت (درون‌فرایندی): "

# سرگروه‌های کارنامهٔ نهایی (تست به همین ثابت‌ها تکیه می‌کند، نه به رشتهٔ inline).
GROUP_SEEN = "✅ کار کرد و دیدی"
GROUP_CAPABLE = "🟢 قابلیت سالم، تپِ تو نیامد"
GROUP_BROKEN = "🔴 خراب"
GROUP_UNKNOWN = "⌛️ نه دیده شد، نه اثباتِ درون‌فرایندی داشت"
REPORT_TITLE = "🧪 <b>کارنامهٔ سفرِ پذیرش</b>"
REPORT_CHUNK = 3800                    # یک پیام؛ فقط بالاتر از این تکه می‌شود

_PHASES = (
    {"key": "P0",  "title": "راه‌اندازی و نقشهٔ سفر",      "window_s": 0,
     "sends": True,  "immediate": True},
    {"key": "P1",  "title": "چتِ آزاد",                    "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P2",  "title": "ثبتِ متنی (capture)",         "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P3",  "title": "ثبتِ رسانه (عکس/ویس)",        "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P4A", "title": "ساختِ یادآوری",                "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P4B", "title": "شلیکِ همان یادآوری",           "window_s": DEFAULT_WINDOW_S,
     "sends": False, "immediate": False},
    {"key": "P5",  "title": "سؤال از والت",                "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P6",  "title": "فرمانِ طبیعیِ گروه (🎨)",      "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P7",  "title": "رفعِ مانعِ لیدِ گیرکرده",       "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P8",  "title": "کارتِ لید + رأیِ مالک",        "window_s": LEAD_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P9",  "title": "مینی‌اپ (داشبورد)",            "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P10", "title": "بودجهٔ سؤالِ اختاپوس",         "window_s": DEFAULT_WINDOW_S,
     "sends": True,  "immediate": False},
    {"key": "P11", "title": "جمع‌بندیِ شب",                 "window_s": DEFAULT_WINDOW_S,
     "sends": False, "immediate": False},
    {"key": "P12", "title": "گزارشِ نهایی",                 "window_s": 0,
     "sends": True,  "immediate": True},
)
_FINAL_KEY = "P12"
_FINAL_IDX = len(_PHASES) - 1

# فلگ‌هایی که باید مسلح باشند / نباشند (P0) — منبع: منشورِ TG-UI ۲۰۲۶-۰۷-۳۱.
_ARMED_FLAGS = ("OCTOPUS_TG_CAPTURE", "OCTOPUS_TG_REMINDERS", "OCTOPUS_TG_BRIEF",
                "OCTOPUS_TG_ASK_VAULT", "OCTOPUS_TG_CHAT_LOCAL", "OCTOPUS_TG_MINIAPP",
                "OCTOPUS_TG_WEEKLY_REVIEW", "OCTOPUS_TG_QBUDGET",
                "OCTOPUS_WIRE_LEAD_PIPELINE", "OCTOPUS_TG_SEND_LOG")
_DISARMED_FLAGS = ("OCTOPUS_WIRE_LEAD_OUTBOUND", "OCTOPUS_TG_CAPTURE_LLM")


# ─── کمکی‌های کوچک (همه fail-soft) ──────────────────────────────────────────
def _fa(v) -> str:
    return str(v).translate(_FA_DIGITS)


def _esc(s) -> str:
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _ltr(s) -> str:
    """تکهٔ LTR (مسیر/شناسه/URL) داخلِ متنِ فارسی — ایزولهٔ bidi (منشور UX-9)."""
    return _LRI + str(s if s is not None else "") + _PDI


def _read_json(path, default=None):
    """خواندنِ JSON ِ fail-soft. **BOM را می‌بلعد**: `miniapp-url.json` ِ زنده را
    PowerShell با BOM نوشته و `read_text("utf-8")` آن را نگه می‌دارد ⇒
    json.loads می‌ترکد و پروب بی‌صدا می‌گوید «تونل غایب». (سنجیده روی
    درختِ زنده، ۲۰۲۶-۰۷-۳۱.)"""
    try:
        return json.loads(Path(path).read_text("utf-8-sig"))
    except (OSError, ValueError, TypeError, LookupError):
        return default


def _read_jsonl(path) -> list:
    try:
        raw = Path(path).read_text("utf-8-sig", errors="replace")
    except (OSError, TypeError, LookupError):
        return []
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _atomic_write(path: Path, text: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, "utf-8")
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def _iso_to_ts(s):
    try:
        t = str(s or "").strip()
        if not t:
            return None
        if t.endswith("Z"):
            t = t[:-1] + "+00:00"
        return datetime.fromisoformat(t).timestamp()
    except (ValueError, TypeError, OSError):
        return None


def _cap_html(text: str, cap: int) -> str:
    """برشِ امنِ HTML: فقط روی مرزِ خطِ کامل می‌بُرد (هر تگِ ما داخلِ یک خط
    باز و بسته می‌شود) — وگرنه یک تگِ نیمه‌بریده = ۴۰۰ Bad Request و پیامِ
    گم‌شده. سقفِ تلگرام ۴۰۹۶ است؛ ما محافظه‌کارتر می‌مانیم."""
    t = str(text or "")
    if len(t) <= int(cap):
        return t
    cut = t.rfind("\n", 0, int(cap))
    if cut <= 0:
        cut = int(cap)
    return t[:cut] + "\n… (بریده شد)"


def split_report(text: str, cap: int = REPORT_CHUNK) -> list:
    """کارنامه = **یک** پیام؛ فقط اگر از cap گذشت تکه می‌شود (روی مرزِ خطِ کامل،
    چون هر تگِ ما داخلِ یک خط باز و بسته می‌شود — تگِ نیم‌بریده = ۴۰۰)."""
    t = str(text or "")
    cap = max(200, int(cap))
    if len(t) <= cap:
        return [t]
    parts, cur, size = [], [], 0
    for line in t.split("\n"):
        ln = line if len(line) < cap else line[:cap - 1]
        need = len(ln) + 1
        if cur and size + need > cap:
            parts.append("\n".join(cur))
            cur, size = [], 0
        cur.append(ln)
        size += need
    if cur:
        parts.append("\n".join(cur))
    n = len(parts)
    return [p if i == 0 else f"(ادامهٔ کارنامه {_fa(i + 1)}/{_fa(n)})\n{p}"
            for i, p in enumerate(parts)]


def _age_str(age_s) -> str:
    if age_s is None:
        return "؟"
    a = int(max(0, age_s))
    if a < 90:
        return f"{_fa(a)} ثانیه"
    if a < 5400:
        return f"{_fa(a // 60)} دقیقه"
    return f"{_fa(round(a / 3600, 1))} ساعت"


def _git_short_head(root) -> str:
    """HEADِ کوتاه بدونِ subprocess (خالص و ارزان). هر ابهام → '?'."""
    try:
        g = Path(root) / ".git"
        if g.is_file():
            txt = g.read_text("utf-8").strip()
            if txt.startswith("gitdir:"):
                g = Path(txt.split(":", 1)[1].strip())
        common = g
        cd = g / "commondir"
        if cd.exists():
            common = (g / cd.read_text("utf-8").strip()).resolve()
        head = (g / "HEAD").read_text("utf-8").strip()
        if not head.startswith("ref:"):
            return head[:7]
        ref = head.split(" ", 1)[1].strip()
        for base in (g, common):
            p = base / ref
            if p.exists():
                return p.read_text("utf-8").strip()[:7]
            packed = base / "packed-refs"
            if packed.exists():
                for line in packed.read_text("utf-8").splitlines():
                    if line.endswith(" " + ref):
                        return line.split(" ", 1)[0][:7]
        return "?"
    except (OSError, ValueError, IndexError):
        return "?"


class _TmpState:
    """مسیرهای state را موقتاً به یک پوشهٔ موقت می‌برد و در finally **دقیقاً**
    برمی‌گرداند — قلبِ «صفر آلودگی» ِ اثباتِ قابلیت.

    سه شیر را با هم می‌بندد چون ماژول‌ها سه‌جور مسیر می‌سازند:
      · `OCTOPUS_STATE_DIR` (reminders)
      · `opslib.STATE_DIR` (question_budget — env نمی‌خوانَد، ثابتِ ماژول است)
      · `OCTOPUS_LEG_TASKS_DIR` (leg_tasks)
    خودِ Journey مسیرهایش را در `__init__` حساب کرده، پس این جابه‌جاییِ
    کوتاه هیچ مسیرِ زنده‌ای را نه می‌خواند نه می‌نویسد."""

    def __init__(self, root, *, leg_tasks: bool = False):
        self.root = Path(root)
        self._leg_tasks = bool(leg_tasks)
        self._env_before = {}
        self._opslib_before = None

    def _set_env(self, key, value):
        self._env_before[key] = os.environ.get(key)
        os.environ[key] = str(value)

    def __enter__(self):
        self._set_env("OCTOPUS_STATE_DIR", self.root)
        if self._leg_tasks:
            self._set_env("OCTOPUS_LEG_TASKS_DIR", self.root / "telegram" / "legs")
        self._opslib_before = opslib.STATE_DIR
        opslib.STATE_DIR = self.root
        return self

    def __exit__(self, *_exc):
        opslib.STATE_DIR = self._opslib_before
        for k, v in self._env_before.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def _http_get(url: str, timeout: float = 12.0) -> dict:
    """GET ِ ساده روی تونلِ **خودمان** (نه تلگرام) — کدِ وضعیت مهم است نه بدنه.

    `urllib` برای 4xx/5xx استثنا می‌دهد؛ کدِ همان استثنا خودش جواب است."""
    req = urllib.request.Request(str(url), method="GET",
                                 headers={"User-Agent": "octopus-journey/1"})
    try:
        with urllib.request.urlopen(req, timeout=float(timeout)) as r:
            return {"status": int(r.status), "error": None}
    except urllib.error.HTTPError as e:
        return {"status": int(getattr(e, "code", 0) or 0), "error": None}
    except Exception as e:  # noqa: BLE001 — تونلِ خاموش/تایم‌اوت = دادهٔ صادق
        return {"status": None, "error": f"{type(e).__name__}: {e}"[:120]}


def _state_root() -> Path:
    """ریشهٔ state — دقیقاً همان فرمولی که reminders/leg_tasks/outcome_store
    استفاده می‌کنند (env اول، بعد opslib) تا هرگز به دو درختِ متفاوت نخوریم."""
    env = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(env) if env else Path(opslib.STATE_DIR)


# ─── هستهٔ سفر ───────────────────────────────────────────────────────────────
class Journey:
    """ماشینِ حالتِ سفر. client/clock تزریق‌پذیرند (تست بدونِ شبکه/ساعتِ واقعی)."""

    def __init__(self, *, client=None, clock=None, state_path=None,
                 deadline_s: float = DEFAULT_DEADLINE_S, task_name=None,
                 org_root=None, http_fn=None):
        self._client = client
        self._clock = clock or time.time
        self._http_fn = http_fn or _http_get
        self._deadline_s = float(deadline_s)
        self._task_name = str(task_name or os.environ.get(TASK_NAME_ENV)
                              or DEFAULT_TASK_NAME)
        self.org_root = Path(org_root or opslib.ORG_ROOT)
        root = _state_root()
        self.state_path = Path(state_path) if state_path else (
            root / "telegram" / "acceptance-journey.json")
        self.send_log_path = root / "tg-send-log.jsonl"
        self.center_config_path = root / "telegram" / "center-config.json"
        self.reminders_path = root / "reminders" / "reminders.json"
        self.reminders_cfg_path = root / "reminders" / "config.json"
        self.lead_tasks_path = Path(
            os.environ.get("OCTOPUS_LEG_TASKS_DIR", "").strip()
            or (root / "telegram" / "legs")) / "lead-tasks.json"
        self.qbudget_path = root / "telegram" / "question-budget.json"
        self.ask_brain_path = root / "telegram" / "ask-brain.jsonl"
        self.miniapp_hits_path = root / "telegram" / "miniapp-hits.jsonl"
        self.miniapp_url_path = root / "telegram" / "miniapp-url.json"
        self.outcomes_db_path = root / "outcomes" / "outcomes.db"
        self.organism_state_path = root / "ORGANISM-STATE.json"
        self.flags_path = root / "flags-loaded-center.json"
        self.raw_dir = self.org_root.joinpath(*RAW_SUBDIR)

    # ── ساعت/کلاینت ────────────────────────────────────────────────────────
    def now(self) -> float:
        try:
            return float(self._clock())
        except Exception:  # noqa: BLE001 — ساعتِ خراب هرگز تیک را نمی‌کشد
            return time.time()

    def client(self):
        if self._client is None:
            self._client = tg_api.TgClient()
        return self._client

    # ── state ──────────────────────────────────────────────────────────────
    def _blank_phase(self) -> dict:
        return {"prompt_sent_ts": None, "verdict": VERDICT_NOT_RUN,
                "evidence": [], "attempts": 0, "errors": [], "meta": {}}

    def _blank_state(self) -> dict:
        return {"schema": "acceptance-journey.v1", "version": JOURNEY_VERSION,
                "started_at": None, "phase_idx": 0, "phases": {},
                "our_sends": [], "consumed": {}, "ticks": 0,
                "last_tick_ts": None, "done": False}

    def load_state(self) -> dict:
        """خواندنِ fail-soft — فایلِ خراب/غایب ⇒ حالتِ نو (سفر متوقف نمی‌شود)."""
        d = _read_json(self.state_path)
        if not isinstance(d, dict):
            return self._blank_state()
        base = self._blank_state()
        for k, v in d.items():
            base[k] = v
        if not isinstance(base.get("phases"), dict):
            base["phases"] = {}
        if not isinstance(base.get("our_sends"), list):
            base["our_sends"] = []
        if not isinstance(base.get("consumed"), dict):
            base["consumed"] = {}
        try:
            base["phase_idx"] = max(0, min(int(base.get("phase_idx") or 0),
                                           len(_PHASES)))
        except (TypeError, ValueError):
            base["phase_idx"] = 0
        return base

    def save_state(self, st: dict) -> bool:
        try:
            st["our_sends"] = list(st.get("our_sends") or [])[-200:]
            c = st.get("consumed")
            if isinstance(c, dict):             # سقف مثل our_sends (ممیزی §۴)
                for k, v in c.items():
                    if isinstance(v, list):
                        c[k] = v[-50:]
                    elif isinstance(v, dict):
                        for b, lv in v.items():
                            if isinstance(lv, list):
                                v[b] = lv[-50:]
        except Exception:  # noqa: BLE001
            pass
        return _atomic_write(self.state_path,
                             json.dumps(st, ensure_ascii=False, indent=1))

    def _rec(self, st: dict, key: str) -> dict:
        rec = st["phases"].get(key)
        if not isinstance(rec, dict):
            rec = self._blank_phase()
            st["phases"][key] = rec
        for k, v in self._blank_phase().items():
            rec.setdefault(k, v)
        return rec

    # ── پیکربندیِ مقصدها ────────────────────────────────────────────────────
    def _center_cfg(self) -> dict:
        d = _read_json(self.center_config_path, {})
        return d if isinstance(d, dict) else {}

    def _group_target(self, leg: str = "lead"):
        """(chat_id, topic_id) ِ تاپیکِ یک پا از center-config. نبود ⇒ (None, None)."""
        cfg = self._center_cfg()
        chat = cfg.get("chat_id")
        topic = (cfg.get("topics") or {}).get(leg)
        try:
            return (int(chat), int(topic))
        except (TypeError, ValueError):
            return (None, None)

    # ── ارسال (تنها فعلِ شبکه‌ایِ این ماژول) ────────────────────────────────
    def _send(self, st: dict, text: str, *, chat_id=None, topic_id=None,
              label: str = "") -> "int | None":
        """ارسال + ثبتِ ردِ خودمان. هر شکست ⇒ None (صداکننده PENDING می‌دهد)."""
        cl = self.client()
        target = chat_id
        if target is None:
            target = getattr(cl, "owner_chat_id", None)
        if target is None:
            return None
        try:
            mid = cl.send(text, chat_id=target, topic_id=topic_id, stream=STREAM)
        except Exception:  # noqa: BLE001 — شکستِ ارسال هرگز تیک را نمی‌کشد
            return None
        if mid is None:
            return None
        st.setdefault("our_sends", []).append(
            {"ts": self.now(), "chat": target, "topic": topic_id,
             "label": str(label or ""), "message_id": mid, "chars": len(text or "")})
        return mid

    # ── خواندنِ رسیدهای ارسال ───────────────────────────────────────────────
    def _send_rows(self, since: float, until=None) -> list:
        rows = []
        for r in _read_jsonl(self.send_log_path):
            try:
                ts = float(r.get("ts") or 0)
            except (TypeError, ValueError):
                continue
            if ts < float(since):
                continue
            if until is not None and ts > float(until):
                continue
            rows.append(r)
        return rows

    def _is_ours(self, st: dict, row: dict) -> bool:
        """ردیفی که خودمان ساختیم — برچسبِ stream (اصلی) + مجاورتِ زمانی (کمربند)."""
        if str(row.get("stream") or "") == STREAM:
            return True
        try:
            ts = float(row.get("ts") or 0)
        except (TypeError, ValueError):
            return False
        for s in st.get("our_sends") or []:
            try:
                if abs(ts - float(s.get("ts") or 0)) <= 3.0 and \
                        str(s.get("chat")) == str(row.get("chat")):
                    return True
            except (TypeError, ValueError):
                continue
        return False

    def _consumed(self, st: dict, bucket: str) -> list:
        """همهٔ claimهای یک bucket، از همهٔ فازها (+ شکلِ تختِ قدیمی).

        ممیزی ۰۷-۳۱ (§۴): claim باید per-phase باشد تا با پس‌گرفتنِ حکم
        آزاد شود؛ شکلِ تختِ قدیمی ({bucket: [کلید]}) فقط خوانده می‌شود
        (فایلِ زندهٔ در جریان نباید بشکند) و هرگز نوشتهٔ نو نمی‌گیرد."""
        out = []
        c = st.setdefault("consumed", {})
        v = c.get(bucket)
        if isinstance(v, list):                      # شکلِ تختِ قدیمی
            out.extend(str(x) for x in v)
        for k, sub in c.items():
            if isinstance(sub, dict):
                lv = sub.get(bucket)
                if isinstance(lv, list):
                    out.extend(str(x) for x in lv)
        return out

    def _claim(self, st: dict, phase: str, bucket: str, key: str) -> None:
        """ثبتِ claim زیرِ نامِ همان فاز — قابلِ آزادسازی، قابلِ حسابرسی."""
        sub = st.setdefault("consumed", {}).setdefault(str(phase), {})
        if not isinstance(sub, dict):
            sub = {}
            st["consumed"][str(phase)] = sub
        sub.setdefault(bucket, []).append(str(key))

    def _release_stale_claims(self, st: dict) -> None:
        """claim ِ فازی که دیگر PASS نیست آزاد می‌شود (ممیزی §۴: «پس‌گرفتنِ
        حکم، claim را پس نمی‌گرفت» — ردیفِ سبزِ کاذبِ P1 برای همیشه از
        P5/P4B پنهان مانده بود). claim فقط همراهِ PASS ساخته می‌شود، پس
        حکمِ غیرِ PASS + claim = بقایای یک حکمِ برگشته."""
        c = st.get("consumed")
        if not isinstance(c, dict):
            return
        for k in [k for k, v in c.items() if isinstance(v, dict)]:
            rec = (st.get("phases") or {}).get(k) or {}
            if rec.get("verdict") != VERDICT_PASS:
                c.pop(k, None)

    def _outer_offset(self):
        """cursor ِ pollerِ باتِ outer (center-config.last_offset) — عددی یا None.
        این تنها شاهدِ در دسترس است که «آپدیتی مصرف شد»؛ خودِ متنِ ورودی را
        هرگز نمی‌بینیم (یک poller بیشتر مجاز نیست)."""
        try:
            v = (self._center_cfg() or {}).get("last_offset")
            return int(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    def _foreign_dm_rows(self, st: dict, since: float) -> list:
        """ردیفِ DM ِ «نه-از-ما» در پنجره — یعنی خودِ مرکز جواب داده.

        صادقانه: این شاهد **نمی‌گوید مالک چه نوشت** (ما ورودی نمی‌بینیم)؛
        فقط می‌گوید مرکز در این پنجره یک پاسخِ DM تولید کرد که ما نفرستادیم."""
        used = self._consumed(st, "dm_rows")
        out = []
        for r in self._send_rows(since):
            if str(r.get("surface") or "") != "dm":
                continue
            if str(r.get("state") or "sent") != "sent" or not r.get("ok"):
                continue
            if str(r.get("stream") or "") == "edit":
                continue
            if self._is_ours(st, r):
                continue
            key = f"{r.get('ts')}|{r.get('sha')}"
            if key in used:
                continue
            out.append(r)
        return out

    def _claim_dm_row(self, st: dict, phase: str, row: dict) -> None:
        self._claim(st, phase, "dm_rows", f"{row.get('ts')}|{row.get('sha')}")

    # ── نوت‌های خامِ capture ────────────────────────────────────────────────
    @staticmethod
    def _note_stamp_ts(name: str):
        """زمانِ **ساخت** از مهرِ نامِ فایل (capture §۵) — نه mtime.

        ممیزی ۰۷-۳۱ (P2 FALSE-PASS): هر پروسه‌ای که نوتِ دیروز را بازنویسی
        کند (فرمت‌کن، sync ِ ابسیدین، _set_note_status_idea، جلسهٔ ایجنت)
        mtime را نو می‌کند و نوتِ کهنه «شاهدِ تازه» می‌شد. مهرِ نام جعل‌ناپذیرِ
        عملی است: producer آن را از ساعتِ ساخت می‌نویسد و بازنویسی نامش را
        عوض نمی‌کند. نامِ بی‌مهر = capture ِ ماشینی نیست ⇒ None."""
        m = _NOTE_STAMP.match(str(name or ""))
        if not m:
            return None
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                            int(m.group(4)), int(m.group(5))).timestamp()
        except ValueError:
            return None

    @staticmethod
    def _note_media_kind(fm: dict, txt: str):
        """photo|voice|None — از فرانت‌متر (file_id/duration) یا **خطِ منبعِ خودِ
        producer**، نه substring ِ خام روی کلِ بدنه (ممیزی P3: متنی که فقط
        «[photo]» را paste کرده بود رسانه شمرده می‌شد)."""
        if fm.get("file_id") or fm.get("duration") not in (None, ""):
            return "voice"
        m = _MEDIA_SRC_LINE.search(str(txt or ""))
        return m.group(1) if m else None

    def _prompt_anchor(self, st: dict, label: str):
        """(کوچک‌ترین message_id، chat) ِ درخواستِ خودمان با این برچسب.

        message_id ِ تلگرام در هر chat یکنواخت صعودی است؛ پس نوتی که
        message_id اش از درخواستِ ما کوچک‌تر است، پیامی است که **قبل از**
        درخواست فرستاده شده — هرچه باشد، جوابِ این فاز نیست."""
        mids, chat = [], None
        for s in st.get("our_sends") or []:
            if str(s.get("label") or "") != str(label):
                continue
            try:
                mids.append(int(s.get("message_id")))
                chat = s.get("chat")
            except (TypeError, ValueError):
                continue
        return (min(mids) if mids else None, chat)

    def _note_owner_caused(self, st: dict, label: str, fm: dict) -> bool:
        """آیا فرانت‌مترِ نوت به پیامی **بعد از درخواستِ همین فاز** در همان
        chat اشاره می‌کند؟ لنگرِ نبود ⇒ نسبت‌دادنی نیست ⇒ False (صداقت)."""
        anchor_mid, anchor_chat = self._prompt_anchor(st, label)
        if anchor_mid is None:
            return False
        try:
            note_mid = int(str(fm.get("message_id") or "").strip())
        except (TypeError, ValueError):
            return False
        if note_mid <= anchor_mid:
            return False
        if anchor_chat is not None and \
                str(fm.get("chat_id") or "").strip() != str(anchor_chat):
            return False
        return True

    def _raw_notes_since(self, st: dict, since: float) -> list:
        """(path, frontmatter, body) ِ نوت‌های Raw ِ **ساخته‌شده بعد از since**
        (مهرِ نام، با ۹۰ ثانیه رواداریِ دقیقه‌ای) — مصرف‌شده‌ها کنار."""
        used = set(self._consumed(st, "raw_notes"))
        out = []
        try:
            names = sorted(self.raw_dir.glob("*.md"))
        except OSError:
            return out
        for p in names:
            stamp = self._note_stamp_ts(p.name)
            if stamp is None or stamp < float(since) - 90.0:
                continue
            if p.name in used:
                continue
            try:
                txt = p.read_text("utf-8", errors="replace")
            except OSError:
                continue
            fm = {}
            if txt.startswith("---"):
                head = txt.split("---", 2)
                if len(head) >= 3:
                    for line in head[1].splitlines():
                        if ":" in line:
                            k, _, v = line.partition(":")
                            fm[k.strip()] = v.strip()
            out.append((p, fm, txt))
        return out

    def _askbrain_msg_rows(self, since: float) -> list:
        """ردیف‌های ask-brain.jsonl که فقط مسیرِ **پیامِ ورودی** می‌سازد.

        topic=="" یعنی DM/General (center._topic_key) — تنها صداکنندهٔ آن
        مسیرِ `_handle_ask` ِ پیامِ مالک است؛ موتورِ پاها با topic=نامِ پا
        صدا می‌زند (center.py:1530) و از این فیلتر رد نمی‌شود."""
        out = []
        for r in _read_jsonl(self.ask_brain_path):
            if str(r.get("topic") or "") != "":
                continue
            ts = _iso_to_ts(r.get("ts"))
            if ts is None or ts < float(since):
                continue
            out.append(r)
        return out

    # ─── فازها: ساختِ پیام ─────────────────────────────────────────────────
    def _prompt(self, key: str, st: dict, rec: dict) -> bool:
        fn = getattr(self, f"_prompt_{key.lower()}", None)
        if fn is None:
            return True
        return bool(fn(st, rec))

    def _prompt_p0(self, st: dict, rec: dict) -> bool:
        env = self._probe_env()
        rec["meta"]["env"] = env
        lines = [
            "🧪 <b>سفرِ آزمونِ خودکار شروع شد</b>",
            "",
            "از حالا تا ~۶ ساعتِ آینده خودم را قدم‌به‌قدم امتحان می‌کنم و هر بار",
            "یک کارِ کوچک ازت می‌خوام. طبیعی جواب بده — دستور لازم نیست.",
            "آخرِ سفر یک کارنامهٔ کامل می‌فرستم (و همان را در والت هم می‌نویسم).",
            "",
            "<b>چه چیزهایی سنجیده می‌شود</b>",
            "۱ چتِ آزاد · ۲ ثبتِ متن · ۳ ثبتِ عکس/ویس · ۴ یادآوری",
            "۵ سؤال از والت · ۶ فرمانِ گروه · ۷ رفعِ مانعِ لید",
            "۸ کارتِ لید و رأی · ۹ مینی‌اپ · ۱۰ سؤالِ اختاپوس · ۱۱ جمع‌بندیِ شب",
            "",
            "<b>وضعیتِ الان</b>",
        ]
        lines += ["▸ " + ln for ln in env.get("lines", [])]
        lines += [
            "",
            "اگر وسطش سرت شلوغ شد اشکالی ندارد: هر مرحله چند بار صبر می‌کند و",
            "بعد صادقانه «انجام‌نشده» ثبت می‌شود — هیچ‌وقت الکی سبز نمی‌کنم.",
        ]
        return self._send(st, "\n".join(lines), label="P0") is not None

    def _prompt_p1(self, st: dict, rec: dict) -> bool:
        txt = ("۱/۱۲ — <b>چتِ آزاد</b>\n"
               "یک جملهٔ ساده برام بنویس (هرچی؛ نه دستور، نه «ثبت:»).\n"
               "می‌خوام ببینم گفتگوی معمولی جواب می‌دهد یا نه.")
        sent = self._send(st, txt, label="P1") is not None
        if sent:
            # لنگرِ شاهد: cursor ِ pollerِ outer در لحظهٔ پرسیدن. اگر بعداً جلو
            # رفته باشد یعنی واقعاً یک آپدیت مصرف شده (پیامِ مالک رسیده).
            rec = st["phases"].setdefault("P1", {})
            rec.setdefault("meta", {})["offset_at_prompt"] = self._outer_offset()
        return sent

    def _prompt_p2(self, st: dict, rec: dict) -> bool:
        txt = ("۲/۱۲ — <b>ثبتِ متنی</b>\n"
               "این را بفرست (یا هر چیزی که با «ثبت:» شروع شود):\n"
               "<code>ثبت: خرید رنگ ۵۰ دلار</code>")
        return self._send(st, txt, label="P2") is not None

    def _prompt_p3(self, st: dict, rec: dict) -> bool:
        txt = ("۳/۱۲ — <b>ثبتِ رسانه</b>\n"
               "یک عکس یا یک ویسِ کوتاه بفرست (هر چیزی، حتی عکسِ دیوار).\n"
               "می‌خوام ببینم رسانه هم درست بایگانی می‌شود.")
        return self._send(st, txt, label="P3") is not None

    def _prompt_p4a(self, st: dict, rec: dict) -> bool:
        txt = ("۴/۱۲ — <b>یادآوری با زبانِ خودت</b>\n"
               "بنویس:\n<code>۱۵ دقیقه دیگه یادم بنداز آب بخورم</code>\n"
               "(هر متنی بعد از «یادم بنداز» قبول است.)")
        return self._send(st, txt, label="P4A") is not None

    def _prompt_p5(self, st: dict, rec: dict) -> bool:
        txt = ("۵/۱۲ — <b>سؤال از والت</b>\n"
               "بنویس:\n<code>از والت بپرس امروز چه چیزی ساخته شد؟</code>")
        sent = self._send(st, txt, label="P5") is not None
        if sent:
            # لنگرِ cursor (ممیزی P5): «از والت بپرس …» یک **پیام** است؛ اگر
            # هیچ آپدیتی مصرف نشده باشد، هر ردیفِ DM ای کارتِ خودجوش است.
            rec.setdefault("meta", {})["offset_at_prompt"] = self._outer_offset()
        return sent

    def _prompt_p6(self, st: dict, rec: dict) -> bool:
        chat, topic = self._group_target("lead")
        if chat is None or topic is None:
            rec["errors"].append("center-config: chat_id/topics.lead غایب")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        rec["meta"]["chat"] = chat
        rec["meta"]["topic"] = topic
        txt = ("۶/۱۲ — <b>فرمانِ طبیعیِ گروه</b>\n"
               "همین‌جا در این تاپیک بنویس: <code>وضعیت</code>\n"
               "(دستورِ اسلش لازم نیست — همین کلمه کافی است.)")
        return self._send(st, txt, chat_id=chat, topic_id=topic,
                          label="P6") is not None

    def _prompt_p7(self, st: dict, rec: dict) -> bool:
        chat, topic = self._group_target("lead")
        if chat is None or topic is None:
            rec["errors"].append("center-config: chat_id/topics.lead غایب")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        snap = self._lead_task_snapshot()
        rec["meta"]["blocked_before"] = snap
        if not snap.get("blocked_ids"):
            # درخواستِ P7 به «کارتِ 🚧 ِ بالاتر» اشاره می‌کند؛ وقتی چنین کارتی
            # نیست، فرستادنش دروغ به مالک است و نمره‌دادنش نمره روی هیچ
            # (ممیزی P7). تیک‌های بعد دوباره می‌کوشند؛ نبودِ پایدار ⇒ BLOCKED.
            rec["errors"].append("هیچ کارِ BLOCKED ای در lead-tasks نیست")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        txt = ("۷/۱۲ — <b>رفعِ مانع</b>\n"
               "بالاتر یک کارتِ 🚧 هست که آدرس/محلهٔ پروژه را می‌پرسد.\n"
               "به همان کارت <b>ریپلای</b> کن و فقط یک محله بنویس — مثلاً "
               "<code>Parramatta</code>.")
        return self._send(st, txt, chat_id=chat, topic_id=topic,
                          label="P7") is not None

    def _prompt_p8(self, st: dict, rec: dict) -> bool:
        chat, topic = self._group_target("lead")
        if chat is None or topic is None:
            rec["errors"].append("center-config: chat_id/topics.lead غایب")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        sub = self._submit_synthetic_lead()
        rec["meta"]["candidate"] = sub
        if not sub.get("ok"):
            rec["errors"].append(f"submit_candidate: {sub.get('status')}"
                                 f"/{sub.get('reason')}")
        txt = ("۸/۱۲ — <b>ماشینِ لید</b>\n"
               "یک لیدِ <b>آزمایشی</b> به لوله دادم. تا ~۴۰ دقیقهٔ دیگر کارتِ\n"
               "«لیدِ آماده» در همین تاپیک ظاهر می‌شود — روی آن ✅ یا ❌ بزن.\n"
               "▸ ارسالِ بیرونی خاموش است: هیچ پیامی به هیچ مشتری نمی‌رود.")
        return self._send(st, txt, chat_id=chat, topic_id=topic,
                          label="P8") is not None

    def _prompt_p9(self, st: dict, rec: dict) -> bool:
        url = ""
        d = _read_json(self.miniapp_url_path, {})
        if isinstance(d, dict):
            url = str(d.get("url") or "").strip()
        rec["meta"]["url_present"] = bool(url)
        if not url.startswith("https://"):
            rec["errors"].append("miniapp-url.json: URL ِ https غایب")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        txt = ("۹/۱۲ — <b>داشبوردِ مینی‌اپ</b>\n"
               "این لینک را باز کن (از هر جایی، حتی بیرونِ خانه):\n"
               f"{_ltr(_esc(url))}/miniapp\n"
               "▸ دکمهٔ web_app هم روی کارتِ «خانه» هست؛ هر کدام را راحت‌تری.")
        return self._send(st, txt, label="P9") is not None

    def _prompt_p10(self, st: dict, rec: dict) -> bool:
        try:
            import question_budget as qb   # noqa: WPS433 — lazy
        except Exception as e:  # noqa: BLE001
            rec["errors"].append(f"question_budget import: {type(e).__name__}")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        if not qb.enabled():
            rec["errors"].append("OCTOPUS_TG_QBUDGET خاموش است")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        q = ("از بینِ بیزنس‌هایت، کدام‌یک باید سهمِ بعدیِ اتوماسیونِ من را "
             "بگیرد — نقاشی، زیمان، یا حسابداری؟ و چرا همان؟")
        r = None
        try:
            r = qb.submit(q, context="سفرِ پذیرشِ ۲۰۲۶-۰۷-۳۱",
                          goal="اولویتِ ساختِ خودکارِ هفتهٔ بعد", now=self.now())
        except Exception as e:  # noqa: BLE001
            rec["errors"].append(f"qb.submit: {type(e).__name__}")
        if not r or not r.get("item"):
            rec["errors"].append("qb.submit چیزی برنگرداند")
            rec.setdefault("meta", {})["prompt_blocked"] = True
            return False
        item = r["item"]
        rec["meta"]["qid"] = item.get("id")
        rec["meta"]["qstatus"] = r.get("status")
        # قراردادِ ۰۷-۳۱ (ممیزی، P10): `submit` **دیگر** asked=True نمی‌کند
        # (question_budget.py:97-101 — بودجه هنگامِ تحویل مصرف می‌شود). اگر
        # بعد از ارسالِ خودمان mark_asked نزنیم، ضربانِ مرکز همان سؤال را
        # pending می‌بیند و **دوباره** می‌فرستد + بودجه می‌سوزاند. متن عیناً
        # `question_text` است تا مسیرِ ریپلای→`record_answer` ِ مرکز
        # (مارکرِ «سؤالِ اختاپوس» + Q-n) بخورد.
        txt = qb.question_text(item) + "\n\n(۱۰/۱۲ سفرِ آزمون)"
        if self._send(st, txt, label="P10") is None:
            return False
        try:
            a = qb.mark_asked(item.get("id"), now=self.now())
            rec["meta"]["marked_asked"] = bool(a and a.get("asked"))
        except Exception as e:  # noqa: BLE001
            rec["meta"]["marked_asked"] = False
            rec["errors"].append(f"mark_asked: {type(e).__name__}")
        if not rec["meta"]["marked_asked"]:
            rec["errors"].append(
                "mark_asked نخورد — مرکز ممکن است همین سؤال را دوباره بفرستد")
        return True

    def _prompt_p12(self, st: dict, rec: dict) -> bool:
        report = self.compose_report(st)
        parts = split_report(report)
        rec["meta"]["report_chars"] = len(report)
        rec["meta"]["report_parts"] = len(parts)
        if self._send(st, parts[0], label="P12") is None:
            rec["errors"].append("ارسالِ گزارشِ نهایی ناموفق — تیکِ بعد دوباره")
            return False           # نه نوت، نه حذفِ تسک: هنوز تمام نشده
        # تکهٔ اول رفت ⇒ سفر تمام است. شکستِ تکه‌های بعدی صادقانه ثبت می‌شود
        # ولی دوباره فرستادنِ کلِ کارنامه یعنی پیامِ تکراری — نمی‌کنیم.
        for i, chunk in enumerate(parts[1:], start=2):
            if self._send(st, chunk, label=f"P12-{i}") is None:
                rec["errors"].append(f"تکهٔ {i} از {len(parts)} نرفت")
        self._persist_finale(st, rec, report)
        return True

    def _persist_finale(self, st: dict, rec: dict, report: str) -> None:
        """نوتِ والت + خودکشیِ زمان‌بندی — دقیقاً یک‌بار (idempotent)."""
        if not rec["meta"].get("note"):
            note = self._write_report_note(report)
            rec["meta"]["note"] = str(note or "")
            if note:
                rec["evidence"].append("نوتِ والت: " + _ltr(note))
            else:
                rec["errors"].append("نوشتنِ نوتِ والت ناموفق")
        if not rec["meta"].get("schtask"):
            r = self._delete_scheduled_task()
            rec["meta"]["schtask"] = r
            # صداقتِ توقفِ خود (ممیزی §5b): ادعای «متوقف شدم» فقط با rc=0.
            if r.get("ok"):
                rec["evidence"].append(
                    "زمان‌بندیِ " + _ltr(self._task_name) + " حذف شد — تیکِ بعدی نمی‌آید")
            else:
                rec["evidence"].append(
                    "⚠️ حذفِ زمان‌بندیِ " + _ltr(self._task_name)
                    + f" نشد ({_esc(str(r.get('msg'))[:100])}) — "
                    "سفر خودش را متوقف‌شده اعلام نمی‌کند")

    def _finish_without_delivery(self, st: dict, rec: dict) -> None:
        """گزارش نرفت (تلگرام در دسترس نبود) — ولی سکوت هم جواب نیست:
        همان محتوا در والت می‌نشیند و تسک حذف می‌شود تا تیکِ بی‌پایان نماند."""
        rec["evidence"].append("⚠️ گزارش به تلگرام نرفت — نسخهٔ والت تنها رسید است")
        self._persist_finale(st, rec, self.compose_report(st))

    # ─── فازها: سنجشِ شاهد ─────────────────────────────────────────────────
    def _verify(self, key: str, st: dict, rec: dict) -> tuple:
        fn = getattr(self, f"_verify_{key.lower()}", None)
        if fn is None:
            return VERDICT_PASS, []
        return fn(st, rec)

    def _verify_p0(self, st: dict, rec: dict) -> tuple:
        """P0 تعاملِ مالک نیست — خودآزمایی است، پس **همیشه پایانی** است.

        اگر PENDING می‌شد، یک محیطِ ناقص کلِ سفر را همان اولِ کار قفل می‌کرد.
        محیطِ ناقص ⇒ DEGRADED با فهرستِ دقیقِ آنچه غایب بود (نه PASS، نه گیر)."""
        env = rec.get("meta", {}).get("env") or self._probe_env()
        ev = list(env.get("lines", []))
        return (VERDICT_PASS if env.get("ok") else VERDICT_DEGRADED), ev

    def _verify_p1(self, st: dict, rec: dict) -> tuple:
        """دو شاهدِ مستقل — وگرنه کارتِ خودجوشِ ارگانیسم «گفتگو» خوانده می‌شود.

        ⚠️ ۰۷-۳۱ ۱۸:۰۰:۵۷ این دقیقاً اتفاق افتاد: ردیفِ DM ِ ۴۲۱ کاراکتری با
        bot_role=inner در حالی که offset ِ pollerِ inner از ۱۶:۱۶ تکان نخورده
        بود — هیچ‌کس چیزی نفرستاده بود و P1 سبزِ کاذب گرفت."""
        since = float(rec.get("prompt_sent_ts") or 0)
        before = (rec.get("meta") or {}).get("offset_at_prompt")
        now_off = self._outer_offset()
        advanced = (isinstance(before, int) and isinstance(now_off, int)
                    and now_off > before)
        rows = [r for r in self._foreign_dm_rows(st, since)
                if str(r.get("bot_role") or "") == "outer"]
        # لنگرِ سوم (ممیزی ۰۷-۳۱، P1 WEAK): cursor روی **هر** آپدیتی جلو
        # می‌رود — از جمله callback ِ یک دکمهٔ کهنه و service-messageهای گروه
        # (`poll_updates` ِ tg_api با allowed_updates=message+callback_query). پس
        # «cursor جلو رفت + کارتِ دوره‌ای رسید» هنوز جعلِ گفتگوست. تنها
        # آرتیفکتی که فقط مسیرِ *پیامِ متنی* می‌سازد، ردیفِ ask-brain با
        # topic="" است (center._handle_ask). جمله‌ای که به intent ِ ثابت
        # نگاشت شود این رد را ندارد — آن حالت صادقانه PARTIAL می‌ماند.
        anchors = self._askbrain_msg_rows(since)
        if rows and advanced and anchors:
            r = rows[0]
            self._claim_dm_row(st, "P1", r)
            return VERDICT_PASS, [
                OWNER_PREFIX + "cursor ِ outer از "
                f"{_ltr(before)} به {_ltr(now_off)} رفت، ردِ پیامِ متنی در "
                "ask-brain هست، و باتِ outer پاسخِ DM داد — "
                f"ts={_ltr(round(float(r.get('ts') or 0), 1))} "
                f"sha={_ltr(r.get('sha'))}"]
        if rows and advanced:
            return VERDICT_PARTIAL, [
                f"cursor جلو رفت ({_ltr(before)}→{_ltr(now_off)}) و یک ردیفِ "
                "DM ِ outer هست، ولی هیچ ردِ پیامِ متنی (ask-brain) نیست — "
                "از یک تپِ دکمه + کارتِ دوره‌ای جداشدنی نیست؛ PASS ادعا نمی‌شود"]
        if advanced:
            return VERDICT_PARTIAL, [
                f"آپدیتی مصرف شد (cursor {_ltr(before)}→{_ltr(now_off)}) ولی "
                "باتِ outer در این پنجره پاسخِ DM نداد — یا مسیرِ جواب کند بود "
                "یا پیام به مسیرِ دیگری (capture/console) رفت"]
        if rows:
            return VERDICT_PENDING, [
                "ردیفِ DM هست ولی cursor تکان نخورده — احتمالاً کارتِ خودجوشِ "
                "سیستم، نه جوابِ پیام (شاهدِ دوم نداریم)"]
        return VERDICT_PENDING, ["نه cursor جلو رفته، نه پاسخِ DM ِ outer هست"]

    def _verify_p2(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        cap = self._proof(rec, self._prove_capture_text)
        for p, fm, txt in self._raw_notes_since(st, since):
            if not (fm.get("message_id") and fm.get("chat_id")):
                continue
            # نوتِ رسانه‌ای مالِ P3 است — وگرنه یک عکسِ زودرس، P2 را «متن»
            # سبز می‌کرد و P3 را گرسنه می‌گذاشت (ممیزی: دزدیِ شاهدِ خواهر).
            if self._note_media_kind(fm, txt):
                continue
            # نسبت‌دادنی به همین درخواست: message_id ِ نوت باید از message_id ِ
            # درخواستِ خودمان (در همان chat، شمارندهٔ یکنواخت) بزرگ‌تر باشد.
            if not self._note_owner_caused(st, "P2", fm):
                continue
            self._claim(st, "P2", "raw_notes", p.name)
            rec["meta"]["note"] = p.name
            return VERDICT_PASS, [
                OWNER_PREFIX + "نوتِ خام ساخته شد — " + _ltr(p.name)
                + f" · message_id={_ltr(fm.get('message_id'))}"
                f" · chat_id={_ltr(fm.get('chat_id'))}"
                " (مهرِ نامِ نوت بعد از درخواست و message_id بعد از پیامِ ما)",
                self._cap_line(cap)]
        return VERDICT_PENDING, [
            OWNER_PREFIX + "هیچ نوتِ متنیِ تازه‌ای (مهرِ نام بعد از درخواست + "
            "message_id بعد از پیامِ ما) در " + _ltr("/".join(RAW_SUBDIR)) + " نیست",
            self._cap_line(cap)]

    def _verify_p3(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        cap = self._proof(rec, self._prove_capture_media)
        for p, fm, txt in self._raw_notes_since(st, since):
            media = self._note_media_kind(fm, txt)
            if not media:
                continue
            if not self._note_owner_caused(st, "P3", fm):
                continue
            self._claim(st, "P3", "raw_notes", p.name)
            rec["meta"]["note"] = p.name
            ev = [OWNER_PREFIX + "نوتِ رسانه — " + _ltr(p.name)
                  + f" · نوع={media}"]
            if fm.get("file_id"):
                ev.append("file_id در فرانت‌متر حاضر است (ویس)")
            ev.append(self._cap_line(cap))
            return VERDICT_PASS, ev
        return VERDICT_PENDING, [
            OWNER_PREFIX + "نوتِ رسانهٔ تازه‌ای (فرانت‌مترِ file_id/duration یا "
            "خطِ منبعِ [photo]/[voice]) با مهر و message_id ِ بعد از درخواست نیست",
            self._cap_line(cap)]

    def _verify_p4a(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        cap = self._proof(rec, self._prove_reminders)
        d = _read_json(self.reminders_path, {}) or {}
        for it in reversed(d.get("items") or []):
            try:
                created = float(it.get("created") or 0)
                due = float(it.get("due") or 0)
            except (TypeError, ValueError):
                continue
            if created < since:
                continue
            # پنجرهٔ موعد ۲–۹۰ دقیقه (ممیزی: «نیم ساعت دیگه» ی واقعی نباید
            # بیرون بیفتد؛ ۳۰۰ ثانیهٔ قبلی RM-1 ِ ایجنت را هم فقط شانسی رد کرد).
            if not (created + 120 <= due <= created + 5400):
                continue
            body = str(it.get("text") or "").strip()
            if not body:
                continue
            if str(it.get("scope") or "dm") != "dm":
                continue                    # درخواستِ ما DM بود؛ leg مالِ ما نیست
            low = body.lower()
            if any(m in low or m in body for m in _SELF_TEST_MARKERS):
                # store فیلدِ منشأ ندارد؛ ولی متنِ خودآزمونی (مثل RM-1 ِ زندهٔ
                # ۰۷-۳۱ که یک ایجنت ساخته بود) هرگز «تپِ مالک» شمرده نمی‌شود.
                continue
            rec["meta"]["reminder_id"] = it.get("id")
            rec["meta"]["reminder_due"] = due
            return VERDICT_PASS, [
                OWNER_PREFIX + "یادآوری ساخته شد — "
                f"{_ltr(it.get('id'))} · موعد "
                f"{_ltr(datetime.fromtimestamp(due).strftime('%H:%M'))}"
                f" · متن «{_esc(body[:40])}»"
                " (صداقت: store فیلدِ منشأ ندارد — «بعد از درخواست + dm + "
                "متنِ غیرِ خودآزمون» تنها سندِ در دسترس است)",
                self._cap_line(cap)]
        return VERDICT_PENDING, [
            OWNER_PREFIX + "در " + _ltr("reminders/reminders.json")
            + " هیچ آیتمِ تازهٔ dm ای با موعدِ ۲–۹۰ دقیقهٔ آینده نیست",
            self._cap_line(cap)]

    def _verify_p4b(self, st: dict, rec: dict) -> tuple:
        cap = self._proof(rec, self._prove_reminders)
        rid = (st["phases"].get("P4A") or {}).get("meta", {}).get("reminder_id")
        if not rid:
            # مالک یادآوری نساخت ⇒ صبرِ بیشتر بی‌معناست. ولی «شلیک» را همین
            # حالا در-پروسه اثبات کرده‌ایم؛ پس حکم را همان‌جا از اثبات بگیر.
            return self._timeout_verdict(rec), [
                OWNER_PREFIX + "P4A یادآوری‌ای نساخت — شاهدِ مالک برای شلیک وجود ندارد",
                self._cap_line(cap)]
        d = _read_json(self.reminders_path, {}) or {}
        item = None
        for it in d.get("items") or []:
            if it.get("id") == rid:
                item = it
                break
        if item is None:
            return VERDICT_PENDING, [
                OWNER_PREFIX + f"آیتمِ {_ltr(rid)} در store پیدا نشد",
                self._cap_line(cap)]
        fired_ts = item.get("fired_ts")
        if not item.get("fired") or not fired_ts:
            due = item.get("due")
            return VERDICT_PENDING, [
                OWNER_PREFIX + f"{_ltr(rid)} هنوز شلیک نشده (fired=False)"
                + (f" · موعد {_ltr(datetime.fromtimestamp(float(due)).strftime('%H:%M'))}"
                   if due else ""),
                self._cap_line(cap)]
        ev = [OWNER_PREFIX + f"شلیک ثبت شد — {_ltr(rid)} · fired_ts="
              f"{_ltr(datetime.fromtimestamp(float(fired_ts)).strftime('%H:%M:%S'))}"]
        # تحویل = ردیفی با **hash ِ همان متنِ یادآوری** (ممیزی: «یک کارت آن
        # حوالی بود» تحویل نیست — دکتر/قلب هر ۲۰-۳۰ دقیقه DM می‌فرستند).
        # مرکز دقیقاً `_scrub(fire_text(it))` را می‌فرستد و tg_send_log از همان
        # متن digest می‌سازد؛ fire_text خالص است — نویسنده و خواننده یک متن.
        expect_sha = None
        try:
            import reminders as _rm   # noqa: WPS433 — lazy، فقط رندرِ خالص
            expect_sha = tg_send_log.digest(_rm.fire_text(item))
        except Exception:  # noqa: BLE001 — رندرِ ناموفق = تحویل اثبات‌ناپذیر
            expect_sha = None
        rows = []
        if expect_sha:
            rows = [r for r in self._foreign_dm_rows(st,
                                                     float(fired_ts) - 60.0)
                    if str(r.get("sha") or "") == expect_sha
                    and abs(float(r.get("ts") or 0) - float(fired_ts)) <= 300.0]
        if rows:
            self._claim_dm_row(st, "P4B", rows[0])
            ev.append("و ردیفِ DM با sha ِ خودِ متنِ یادآوری "
                      f"({_ltr(expect_sha)}) — "
                      f"ts={_ltr(round(float(rows[0].get('ts') or 0), 1))}")
            return VERDICT_PASS, ev
        ev.append("ولی ردیفی با sha ِ متنِ همین یادآوری در tg-send-log نیست "
                  "(کارتِ نزدیکِ همان لحظه کافی نیست — تحویل اثبات نشد)")
        return VERDICT_PENDING, ev

    def _verify_p5(self, st: dict, rec: dict) -> tuple:
        """PASS فقط با سه سند (ممیزی ۰۷-۳۱، P5 FALSE-PASS): مسیرِ ask-vault
        هیچ آرتیفکتِ اختصاصی نمی‌نویسد (ask_vault.query لاگ ندارد)، پس:
          ۱) cursor ِ outer از لحظهٔ درخواست جلو رفته باشد (پیامی مصرف شد)؛
          ۲) ردیفِ DM ِ bot_role=outer ِ نه-از-ما با sha ای که در ۲۴ ساعتِ
             قبل از درخواست دیده نشده (کارتِ تکراریِ دوره‌ای نیست)؛
          ۳) sha ِ ردیف با متنِ یادآوریِ خودکاشتهٔ P4A یکی نباشد — شلیکِ
             همان یادآوری داخلِ پنجرهٔ P5 دقیقاً سناریوی سبزِ کاذبِ ممیزی بود.
        متنِ ورودی را نمی‌بینیم؛ این حداکثرِ صداقتِ در دسترس است و باقیِ
        ابهام PARTIAL می‌ماند، نه PASS."""
        since = float(rec.get("prompt_sent_ts") or 0)
        cap = self._proof(rec, self._prove_ask_vault)
        ev = [self._cap_line(cap)]
        before = (rec.get("meta") or {}).get("offset_at_prompt")
        now_off = self._outer_offset()
        advanced = (isinstance(before, int) and isinstance(now_off, int)
                    and now_off > before)
        old_shas = {str(r.get("sha") or "")
                    for r in self._send_rows(since - 86400.0, until=since)}
        reminder_sha = None
        try:
            rid = (st["phases"].get("P4A") or {}).get("meta", {}).get("reminder_id")
            if rid:
                d = _read_json(self.reminders_path, {}) or {}
                for it in d.get("items") or []:
                    if it.get("id") == rid:
                        import reminders as _rm   # noqa: WPS433
                        reminder_sha = tg_send_log.digest(_rm.fire_text(it))
                        break
        except Exception:  # noqa: BLE001
            reminder_sha = None
        rows = [r for r in self._foreign_dm_rows(st, since)
                if str(r.get("bot_role") or "") == "outer"
                and str(r.get("sha") or "") not in old_shas
                and str(r.get("sha") or "") != (reminder_sha or "")]
        if rows and advanced:
            self._claim_dm_row(st, "P5", rows[0])
            ev.insert(0, OWNER_PREFIX + "آپدیت مصرف شد "
                      f"({_ltr(before)}→{_ltr(now_off)}) و پاسخِ DM ِ outer ِ "
                      "تازه‌محتوا آمد — "
                      f"ts={_ltr(round(float(rows[0].get('ts') or 0), 1))} "
                      f"sha={_ltr(rows[0].get('sha'))} "
                      "(محتوایی که در ۲۴س قبل تکرار نشده و یادآوریِ خودمان نیست)")
            return VERDICT_PASS, ev
        if rows:
            ev.insert(0, OWNER_PREFIX + "ردیفِ DM ِ تازه‌محتوا هست ولی cursor "
                      "تکان نخورده — هیچ پیامی مصرف نشده؛ کارتِ خودجوش است")
            return VERDICT_PENDING, ev
        if advanced:
            # آپدیتِ مصرف‌شده می‌تواند تپِ یک دکمه باشد نه جملهٔ «از والت بپرس»
            # — پنجره باز می‌ماند؛ سرِ پایانِ صبر حکم از اثباتِ درون‌فرایندی
            # می‌آید (CAPABILITY-OK)، نه از حدس.
            ev.insert(0, OWNER_PREFIX + "آپدیتی مصرف شد ولی پاسخِ DM ِ "
                      "نسبت‌دادنی نیامد (تپِ دکمه از پیامِ متنی جداشدنی نیست)")
            return VERDICT_PENDING, ev
        ev.insert(0, OWNER_PREFIX + "نه cursor جلو رفته نه ردیفِ DM ِ "
                  "outer ِ تازه‌محتوا هست")
        return VERDICT_PENDING, ev

    def _verify_p6(self, st: dict, rec: dict) -> tuple:
        """ممیزی ۰۷-۳۱ (P6 FALSE-PASS، با سه نمونهٔ زنده): digestِ دوره‌ای
        (stream=center)، کارتِ پا (leg-card-*) و کارتِ لوله (lead) همگی در
        همان topic=22 می‌نشینند و «topic درست بود» منبع نیست. PASS فقط با
        استریمی که در مجموعهٔ خودمختار نیست؛ و چون پاسخِ فرمانِ گروه امروز
        خودش stream=center دارد، ردیفِ center صادقانه «نسبت‌ندادنی» گزارش
        می‌شود — نه سبز (حکمِ پایانی از اثباتِ درون‌فرایندی می‌آید)."""
        since = float(rec.get("prompt_sent_ts") or 0)
        cap = self._proof(rec, self._prove_leg_command)
        topic = rec.get("meta", {}).get("topic")
        used = set(self._consumed(st, "group_rows"))
        ambiguous = None
        for r in self._send_rows(since):
            if str(r.get("surface") or "") != "group":
                continue
            if self._is_ours(st, r):
                continue
            if topic is None or r.get("topic") != topic:
                continue
            key = f"{r.get('ts')}|{r.get('sha')}"
            if key in used:
                continue
            stream = str(r.get("stream") or "")
            if (not stream or stream in _AUTONOMOUS_GROUP_STREAMS
                    or stream.startswith(_AUTONOMOUS_GROUP_PREFIXES)):
                ambiguous = ambiguous or r
                continue            # digest/کارتِ پا/لوله — یا نسبت‌ندادنی
            self._claim(st, "P6", "group_rows", key)
            return VERDICT_PASS, [
                OWNER_PREFIX + "پاسخِ گروهی با استریمِ غیرِ خودمختار در تاپیکِ "
                f"{_fa(r.get('topic'))} — ts={_ltr(round(float(r.get('ts') or 0), 1))}"
                f" stream={_ltr(stream)}",
                self._cap_line(cap)]
        if ambiguous is not None:
            return VERDICT_PENDING, [
                OWNER_PREFIX + "ردیفِ گروهی در تاپیک هست ولی استریمش "
                f"({_ltr(ambiguous.get('stream'))}) همان استریمِ digest/کارتِ "
                "خودمختار است — از پاسخِ فرمان جداشدنی نیست؛ سبز ادعا نمی‌شود",
                self._cap_line(cap)]
        return VERDICT_PENDING, [
            OWNER_PREFIX + f"هیچ ردیفِ surface=group با topic={_fa(topic)} در پنجره نیست",
            self._cap_line(cap)]

    def _verify_p7(self, st: dict, rec: dict) -> tuple:
        cap = self._proof(rec, self._prove_leg_resolve)
        since = float(rec.get("prompt_sent_ts") or 0)
        before = rec.get("meta", {}).get("blocked_before") or {}
        ids = list(before.get("blocked_ids") or [])
        if not ids:
            # ممیزی ۰۷-۳۱ (P7 latent): فیلترِ خالی خودش را خاموش می‌کرد و هر
            # کارِ قدیمیِ مارکردار (بی‌هیچ قیدِ زمانی) PASS ِ فوری می‌شد.
            # پیش‌نیازِ فاز غایب است ⇒ BLOCKED، نه نمره‌دادنِ روی هیچ.
            return VERDICT_BLOCKED, [
                OWNER_PREFIX + "در لحظهٔ درخواست هیچ کارِ BLOCKED ای در "
                + _ltr("legs/lead-tasks.json") + " نبود — فاز آزمودنی نیست "
                "(فیلترِ خالی هرگز «همه‌چیز» نمی‌شود)",
                self._cap_line(cap)]
        d = _read_json(self.lead_tasks_path, {}) or {}
        for t in d.get("tasks") or []:
            if t.get("id") not in ids:
                continue
            if t.get("state") == "BLOCKED":
                continue
            try:
                updated = float(t.get("updated") or 0)
            except (TypeError, ValueError):
                updated = 0.0
            if updated < since:
                continue        # مارکرِ کهنه — رفعِ مانعِ دیروز شاهدِ امروز نیست
            if "➕ اطلاعات مالک" in str(t.get("text") or ""):
                return VERDICT_PASS, [
                    OWNER_PREFIX + "کارِ گیرکرده باز شد — "
                    f"{_ltr(t.get('id'))} · state={_ltr(t.get('state'))}"
                    " · متن نشانِ «➕ اطلاعات مالک» گرفت و updated بعد از درخواست است",
                    self._cap_line(cap)]
        return VERDICT_PENDING, [
            OWNER_PREFIX + "در " + _ltr("legs/lead-tasks.json")
            + " هنوز کاری از BLOCKED (با updated ِ بعد از درخواست) بیرون نیامده",
            self._cap_line(cap)]

    def _verify_p8(self, st: dict, rec: dict) -> tuple:
        """ممیزی ۰۷-۳۱ (P8 FALSE-PASS): research_loop خودش autonomous ردیفِ
        accepted-measurement می‌نویسد (self_run=True؛ ۳۰+ ردیفِ زنده). پس
        «هر ردیفِ غیرِ delivered» رأی نیست. رأیِ مالک = ردیفی که (۱)
        payload.source با tg- شروع شود (مهرِ verdict_recorder ِ دکمه)، (۲)
        payload.self_run نداشته باشد، و (۳) به **همان لیدِ مصنوعیِ همین فاز**
        (lead_id/correlation/proposal) جوش بخورد. کارتِ لید هم قابلیتِ لوله
        است نه مشاهدهٔ مالک — برچسبش جدا شد."""
        since = float(rec.get("prompt_sent_ts") or 0)
        cap = self._proof(rec, self._prove_lead_card)
        ev = []
        used = set(self._consumed(st, "group_rows"))
        card = [r for r in self._send_rows(since)
                if str(r.get("stream") or "") == "lead"
                and not self._is_ours(st, r)
                and f"{r.get('ts')}|{r.get('sha')}" not in used]
        if card:
            self._claim(st, "P8", "group_rows",
                        f"{card[0].get('ts')}|{card[0].get('sha')}")
            ev.append("لوله: کارتِ لید فرستاده شد — رسیدِ stream=lead ts="
                      f"{_ltr(round(float(card[0].get('ts') or 0), 1))}"
                      " (کارِ خودکارِ لوله، نه تپِ مالک)")
        else:
            ev.append("لوله: هنوز هیچ رسیدِ stream=lead در پنجره نیست "
                      "(ضربانِ لوله ~۳۰-۴۰ دقیقه)")
        cand = (rec.get("meta") or {}).get("candidate") or {}
        cand_lid = str(cand.get("lead_id") or "").strip()
        owner_votes, foreign_votes = [], []
        for v in self._outcome_rows(since):
            pl = v.get("payload") if isinstance(v.get("payload"), dict) else {}
            if pl.get("self_run"):
                continue                    # اندازه‌گیریِ خودگردانِ research
            if not str(pl.get("source") or "").startswith("tg-"):
                continue                    # فقط مهرِ دکمهٔ تلگرام رأیِ مالک است
            if cand_lid and cand_lid in {str(v.get("lead_id") or ""),
                                         str(v.get("correlation_id") or ""),
                                         str(v.get("proposal_id") or "")}:
                owner_votes.append(v)
            else:
                foreign_votes.append(v)
        if owner_votes and cand_lid:
            v = owner_votes[0]
            ev.append(OWNER_PREFIX + "رأیِ مالک روی همین لیدِ آزمایشی ثبت شد — "
                      f"outcomes.db event_id={_ltr(v.get('event_id'))} "
                      f"type={_ltr(v.get('event_type'))} "
                      f"source={_ltr((v.get('payload') or {}).get('source'))} "
                      f"lead={_ltr(v.get('lead_id'))}")
            ev.append(self._cap_line(cap))
            return VERDICT_PASS, ev
        if not cand_lid:
            ev.append(OWNER_PREFIX + "لیدِ مصنوعی شناسه نگرفت — هیچ رأی‌ای "
                      "قابلِ‌اتصال به این فاز نیست")
        elif foreign_votes:
            ev.append(OWNER_PREFIX + "رأیِ tg ِ تازه‌ای هست ولی به لیدِ "
                      f"آزمایشیِ {_ltr(cand_lid)} وصل نیست — شمرده نمی‌شود")
        else:
            ev.append(OWNER_PREFIX + "هیچ رأیِ مالک‌مهرِ (source=tg-*) تازه‌ای در "
                      + _ltr("state/outcomes/outcomes.db") + " نیست")
        ev.append(self._cap_line(cap))
        return VERDICT_PENDING, ev

    def _verify_p9(self, st: dict, rec: dict) -> tuple:
        """تپِ مالک = خطِ hits ِ **بیرون از پنجرهٔ پروبِ خودمان**.

        بدونِ این تفکیک، دو ضربهٔ اثباتِ درون‌فرایندی خودشان «مالک داشبورد را
        باز کرد» خوانده می‌شدند — دقیقاً همان سبزِ کاذبی که P1 یک‌بار خورد."""
        since = float(rec.get("prompt_sent_ts") or 0)
        cap = self._proof(rec, self._prove_miniapp)
        win = (cap or {}).get("hit_window") or []
        hits = []
        for h in _read_jsonl(self.miniapp_hits_path):
            try:
                ts = float(h.get("ts") or 0)
            except (TypeError, ValueError):
                continue
            if ts < since:
                continue
            if len(win) == 2 and float(win[0]) <= ts <= float(win[1]):
                continue                       # ضربهٔ خودِ پروب، نه تپِ مالک
            hits.append(h)
        if not hits:
            return VERDICT_PENDING, [
                OWNER_PREFIX + "هیچ خطی در " + _ltr("telegram/miniapp-hits.jsonl")
                + " بعد از درخواست (جز ضربهٔ خودِ پروب)",
                self._cap_line(cap)]
        # ممیزی ۰۷-۳۱ (P9 «قوی‌ترین سبزِ کاذب»): تونل عمومی است، درخواستِ ما
        # خودِ URL را می‌فرستد و کراولرِ preview ِ تلگرام/اسکنرها همان لحظه
        # ردیف می‌سازند — همه بدونِ auth. تپِ مالک = فقط ردیفِ authed روی
        # مسیرِ api (دروازه authed را تنها بعد از عبورِ initData از دیوارِ
        # HMAC ِ مالک، و تنها روی /api/miniapp، True می‌زند).
        owner_hits = [h for h in hits
                      if h.get("authed")
                      and str(h.get("path") or "").startswith("/api/")]
        if owner_hits:
            ev = [OWNER_PREFIX + f"{_fa(len(owner_hits))} درخواستِ authed روی "
                  f"{_ltr(owner_hits[-1].get('path'))} — initData ِ معتبرِ مالک "
                  "از دیوارِ HMAC گذشت (کراولر/اسکنر نمی‌تواند)"]
            ev.append(f"(کلِ ردیف‌های نه-از-پروب: {_fa(len(hits))})")
            ev.append(self._cap_line(cap))
            return VERDICT_PASS, ev
        return VERDICT_PENDING, [
            OWNER_PREFIX + f"{_fa(len(hits))} ردیفِ نه-از-پروب هست ولی هیچ‌کدام "
            "authed نیست — تونلِ عمومی را هر کراولر/اسکنری می‌زند؛ بدونِ "
            "initData «مالک باز کرد» ادعا نمی‌شود",
            self._cap_line(cap)]

    def _verify_p10(self, st: dict, rec: dict) -> tuple:
        cap = self._proof(rec, self._prove_qbudget)
        qid = rec.get("meta", {}).get("qid")
        if not qid:
            return self._timeout_verdict(rec), [
                OWNER_PREFIX + "سؤالی برای مالک ثبت نشد (فلگ/بودجه)",
                self._cap_line(cap)]
        d = _read_json(self.qbudget_path, {}) or {}
        for it in d.get("queue") or []:
            if it.get("id") != qid:
                continue
            ev = [f"سؤال {_ltr(qid)} ثبت شد · asked={_ltr(it.get('asked'))}"]
            if it.get("answer"):
                when = ""
                try:
                    when = datetime.fromtimestamp(
                        float(it.get("answered_ts"))).strftime("%H:%M")
                except (TypeError, ValueError, OSError):
                    when = "؟"
                ev.append(OWNER_PREFIX + "جواب ثبت شد — "
                          f"answered_ts={_ltr(when)}"
                          f" · «{_esc(str(it.get('answer'))[:60])}»")
                ev.append(self._cap_line(cap))
                return VERDICT_PASS, ev
            ev.append(OWNER_PREFIX + "هنوز جوابی روی آن نیست (ریپلای به همان پیام لازم است)")
            ev.append(self._cap_line(cap))
            return VERDICT_PENDING, ev
        return VERDICT_PENDING, [
            OWNER_PREFIX + f"{_ltr(qid)} در store پیدا نشد", self._cap_line(cap)]

    def _verify_p11(self, st: dict, rec: dict) -> tuple:
        """فازِ سیستمی. دو اصلاحِ ممیزی ۰۷-۳۱: (۱) wrap_hour از **همان**
        `reminders.load_config()` می‌آید که brief._hours می‌خواند — دو خوانندهٔ
        جدا یعنی روزی دو حقیقت؛ (۲) ادعای «ردیفِ DM ِ متناظر» فقط با sha ِ
        متنِ بازساختهٔ خودِ جمع‌بندی (brief.evening_text خالص است) — «هر
        کارتی بعد از ۲۱:۲۵» متناظر نیست و claim ِ آن، ردیف را از بقیه می‌دزدید.
        سندِ اصلیِ ارسال خودِ cursor است: brief.beat آن را فقط بعد از
        send ِ strict (mid ِ واقعی) جلو می‌برد."""
        now = self.now()
        wrap_h = 21.5
        try:
            import reminders as _rm   # noqa: WPS433 — همان صداکنندهٔ brief
            wrap_h = float((_rm.load_config() or {}).get("wrap_hour", 21.5))
        except Exception:  # noqa: BLE001 — سقوط به خواندنِ مستقیمِ فایل
            cfg = _read_json(self.reminders_cfg_path, {}) or {}
            try:
                wrap_h = float(cfg.get("wrap_hour", 21.5))
            except (TypeError, ValueError):
                wrap_h = 21.5
        dt = datetime.fromtimestamp(now)
        h = dt.hour + dt.minute / 60.0
        day = dt.strftime("%Y-%m-%d")
        due_txt = f"{int(wrap_h):02d}:{int(round((wrap_h % 1) * 60)):02d}"
        if h < wrap_h:
            return VERDICT_WAIT, [f"هنوز {_ltr(due_txt)} نشده — "
                                  f"ساعتِ الان {_ltr(dt.strftime('%H:%M'))}"]
        ccfg = self._center_cfg()
        cursor = str(ccfg.get("last_evening_day") or "")
        ev = [f"مکان‌نمای شب در center-config: {_ltr(cursor or '∅')} (امروز {_ltr(day)})"]
        if cursor != day:
            return VERDICT_PENDING, ev + ["یعنی جمع‌بندیِ شب هنوز نرفته"]
        ev.append("cursor فقط بعد از ارسالِ strict (mid ِ واقعی) جلو می‌رود — "
                  "خودِ ارسال مستند است")
        wrap_ts = datetime(dt.year, dt.month, dt.day, int(wrap_h),
                           int((wrap_h % 1) * 60)).timestamp() - 300
        expect_sha = None
        try:
            import brief as _bf   # noqa: WPS433 — رندرِ خالص، صفر ارسال
            expect_sha = tg_send_log.digest(_bf.evening_text(now=now, cfg=ccfg))
        except Exception:  # noqa: BLE001
            expect_sha = None
        matched = None
        if expect_sha:
            for r in self._foreign_dm_rows(st, wrap_ts):
                if str(r.get("sha") or "") == expect_sha:
                    matched = r
                    break
        if matched is not None:
            self._claim_dm_row(st, "P11", matched)
            ev.append("و ردیفِ DM با sha ِ خودِ متنِ جمع‌بندی — ts="
                      f"{_ltr(round(float(matched.get('ts') or 0), 1))}")
        else:
            ev.append("ردیفی با sha ِ متنِ بازساخته پیدا نشد (متنِ شب به "
                      "دادهٔ لحظهٔ ارسال وابسته است) — ردیفِ دلبخواه ادعا/مصرف "
                      "نمی‌شود")
        return VERDICT_PASS, ev

    def _verify_p12(self, st: dict, rec: dict) -> tuple:
        return VERDICT_PASS, list(rec.get("evidence") or []) + ["گزارشِ نهایی رفت"]

    # ─── پروب‌های کمکی ─────────────────────────────────────────────────────
    def _probe_env(self) -> dict:
        """محیط: پروسه‌ها زنده‌اند؟ فلگ‌ها بارند؟ تونل تازه است؟ pinها هستند؟"""
        now = self.now()
        lines, ok = [], True

        org = _read_json(self.organism_state_path, {}) or {}
        org_ts = _iso_to_ts(org.get("ts"))
        org_age = (now - org_ts) if org_ts else None
        if org_age is None or org_age > 900:
            ok = False
        lines.append(f"ارگانیسم: ضربان {_fa(org.get('beat', '؟'))} · تازگی "
                     + _age_str(org_age))

        cfg = self._center_cfg()
        # ⚠️ ۰۷-۳۱: نسخهٔ اول `cfg["last_pulse"]` را «نبض» خواند — آن cursor ِ
        # کارتِ خانهٔ **ساعتی** است، پس ۱۷ دقیقه کهنگی طبیعی بود و P0 حکمِ
        # DEGRADED ِ کاذب داد. نبضِ زندگیِ مرکز فایلِ pulse/tg-center.json است
        # (همانی که واچ‌داگ می‌خوانَد): هر تکرارِ حلقه اتمیک نوشته می‌شود.
        pulse_p = self.center_config_path.parent.parent / "pulse" / "tg-center.json"
        pulse_age, pulse_pid = None, cfg.get("boot_receipt_pid", "؟")
        try:
            pulse_age = now - pulse_p.stat().st_mtime
            _pj = json.loads(pulse_p.read_text("utf-8-sig"))
            pulse_pid = _pj.get("pid", pulse_pid)
        except (OSError, ValueError, TypeError):
            pulse_age = None
        if pulse_age is None or pulse_age > 420:
            ok = False
        lines.append("مرکزِ تلگرام: نبض " + _age_str(pulse_age)
                     + f" · PID {_fa(pulse_pid)}")

        pids = []
        for name, f in (("مرکز", "flags-loaded-center.json"),
                        ("ارگانیسم", "flags-loaded-organism.json"),
                        ("کورتکس", "flags-loaded-cortex.json"),
                        ("live", "flags-loaded-live.json")):
            d = _read_json(_state_root() / f, {}) or {}
            if d.get("pid"):
                pids.append(f"{name}={_fa(d['pid'])}")
        lines.append("PIDها: " + (" · ".join(pids) if pids else "؟"))

        flags = (_read_json(self.flags_path, {}) or {}).get("flags") or {}
        missing = [f for f in _ARMED_FLAGS if str(flags.get(f, "")) != "1"]
        hot = [f for f in _DISARMED_FLAGS if str(flags.get(f, "")) == "1"]
        if missing:
            ok = False
        lines.append("فلگ‌ها: "
                     + (f"{_fa(len(_ARMED_FLAGS))} مسلح ✅"
                        if not missing else "غایب → " + _ltr(", ".join(missing)))
                     + (" · ⚠️ روشنِ ناخواسته: " + _ltr(", ".join(hot)) if hot else ""))

        mu = _read_json(self.miniapp_url_path, {}) or {}
        turl = str(mu.get("url") or "")
        t_age = None
        try:
            t_age = now - self.miniapp_url_path.stat().st_mtime
        except OSError:
            pass
        lines.append("تونلِ مینی‌اپ: " + ("هست" if turl.startswith("https://") else "غایب")
                     + " · سنِ فایل " + _age_str(t_age))

        pins = [k for k in ("home_message_id", "guide_message_id",
                            "status_message_id", "dm_guide_message_id")
                if cfg.get(k)]
        lines.append(f"کارت‌های پین‌شده: {_fa(len(pins))}/۴ حاضر")

        lines.append("نسخه: " + _ltr(_git_short_head(self.org_root)))
        return {"ok": ok, "lines": lines}

    def _lead_task_snapshot(self) -> dict:
        d = _read_json(self.lead_tasks_path, {}) or {}
        return {"blocked_ids": [t.get("id") for t in (d.get("tasks") or [])
                                if t.get("state") == "BLOCKED"]}

    # ── چارچوبِ اثباتِ قابلیت ────────────────────────────────────────────────
    def _proof(self, rec: dict, fn) -> dict:
        """اثبات را **یک‌بار** می‌دود و در meta می‌نشاند (تیک‌های بعدی رایگان).

        شکلِ خروجی: {"ok": bool, "blocked": bool، "line": str}.
        استثنا = دادهٔ صادق، نه کرش: «قابلیت: خطا — <type>: <msg>»."""
        cap = (rec.get("meta") or {}).get("capability")
        if isinstance(cap, dict) and cap.get("line"):
            return cap
        try:
            cap = fn()
            if not isinstance(cap, dict):
                cap = {"ok": False, "line": "اثبات چیزی برنگرداند"}
        except Exception as e:  # noqa: BLE001 — شکستِ اثبات هرگز تیک را نمی‌کشد
            cap = {"ok": False, "line": f"خطا — {type(e).__name__}: {e}"[:220]}
        rec.setdefault("meta", {})["capability"] = cap
        return cap

    def _cap_line(self, cap: dict) -> str:
        return CAP_PREFIX + str((cap or {}).get("line") or "—")

    def _timeout_verdict(self, rec: dict) -> str:
        """حکمِ پایانِ صبر: شاهدِ مالک نیامد — حالا اثباتِ قابلیت حرف می‌زند.

        اثبات پاس ⇒ CAPABILITY-OK (سیستم سالم، مالک نبود)؛ اثبات خطا ⇒ BROKEN
        (نقصِ واقعی)؛ پیش‌نیازِ ساختاری (فلگ/URL) غایب ⇒ BLOCKED؛ اثبات‌ناپذیر
        ⇒ همان TIMEOUT ِ قدیمی."""
        cap = (rec.get("meta") or {}).get("capability")
        if not isinstance(cap, dict) or not cap.get("line"):
            return VERDICT_TIMEOUT
        if cap.get("ok"):
            return VERDICT_CAPABILITY_OK
        if cap.get("blocked"):
            return VERDICT_BLOCKED
        return VERDICT_BROKEN

    # ── اثبات‌های per-phase (همه روی ماژولِ تولیدیِ واقعی، همه ایزوله) ───────
    def _prove_capture_text(self) -> dict:
        """P2 — `capture.handle` روی «ثبت: خرید رنگ ۵۰ دلار» در والتِ **موقت**.

        سه چیز را با هم می‌سنجد: نوتِ خام ساخته می‌شود، فرانت‌مترش
        message_id/chat_id دارد، و تکرارِ همان پیام dedup می‌شود (§۹)."""
        import capture   # noqa: WPS433 — lazy
        if os.environ.get(capture.FLAG_CAPTURE, "0") != "1":
            return {"ok": False, "blocked": True,
                    "line": f"فلگِ {capture.FLAG_CAPTURE} خاموش است — capture اصلاً صدا نمی‌شود"}
        tmp = Path(tempfile.mkdtemp(prefix="journey-capture-"))
        try:
            msg = {"message_id": 900001, "chat": {"id": 900999},
                   "text": "ثبت: خرید رنگ ۵۰ دلار"}
            deps = {"vault_root": str(tmp), "now": self.now()}
            r1 = capture.handle(dict(msg), deps=deps)
            if not r1.get("handled") or not r1.get("path"):
                return {"ok": False, "line": f"handle چیزی ننوشت ({r1})"[:200]}
            txt = Path(r1["path"]).read_text("utf-8", errors="replace")
            missing = [k for k in ("message_id: 900001", "chat_id: 900999")
                       if k not in txt]
            if missing:
                return {"ok": False,
                        "line": "فرانت‌مترِ نوت ناقص است — " + _ltr(", ".join(missing))}
            r2 = capture.handle(dict(msg), deps=deps)
            notes = list(tmp.joinpath(*RAW_SUBDIR).glob("*.md"))
            if not r2.get("dup") or len(notes) != 1:
                return {"ok": False,
                        "line": f"dedup نشد — {_fa(len(notes))} نوت، dup={r2.get('dup')}"}
            return {"ok": True,
                    "line": "capture ِ متن سالم — نوتِ "
                            + _ltr(Path(r1["path"]).name)
                            + f" با message_id/chat_id · ack «{_esc(r1.get('ack'))}»"
                            " · ارسالِ دوم dedup شد"}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _prove_capture_media(self) -> dict:
        """P3 — همان مسیر با یک **ویسِ** ساختگی (file_id+duration).

        قراردادِ سخت: نوت باید file_id و نشانِ صادقِ [voice] داشته باشد و
        **هیچ transcript ِ جعلی** نه در نوت باشد نه در ack."""
        import capture   # noqa: WPS433
        if os.environ.get(capture.FLAG_CAPTURE, "0") != "1":
            return {"ok": False, "blocked": True,
                    "line": f"فلگِ {capture.FLAG_CAPTURE} خاموش است"}
        tmp = Path(tempfile.mkdtemp(prefix="journey-voice-"))
        try:
            fid = "AwACAgQAAxkJourneyProbe"
            msg = {"message_id": 900002, "chat": {"id": 900999},
                   "voice": {"file_id": fid, "duration": 7}}
            r = capture.handle(msg, deps={"vault_root": str(tmp), "now": self.now()})
            if not r.get("handled") or not r.get("path"):
                return {"ok": False, "line": f"ویس ثبت نشد ({r})"[:200]}
            txt = Path(r["path"]).read_text("utf-8", errors="replace")
            if f"file_id: {fid}" not in txt:
                return {"ok": False, "line": "file_id در فرانت‌متر ننشست"}
            if "[voice]" not in txt:
                return {"ok": False, "line": "نشانِ [voice] در نوت نیست"}
            if "(بدون متن)" not in txt:
                return {"ok": False,
                        "line": "بدنهٔ نوت متنی دارد که مالک نفرستاده — بوی transcript ِ جعلی"}
            ack = str(r.get("ack") or "")
            if "متن‌سازی" not in ack:
                return {"ok": False,
                        "line": f"ack دربارهٔ نبودِ متن‌سازی ساکت است: «{_esc(ack)}»"[:180]}
            return {"ok": True,
                    "line": "capture ِ رسانه سالم — نوتِ "
                            + _ltr(Path(r["path"]).name)
                            + " با file_id و نشانِ [voice] · بدونِ transcript ِ جعلی"
                            f" · ack «{_esc(ack)}»"}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _prove_reminders(self) -> dict:
        """P4A/P4B — کلِ قوسِ یادآوری روی `reminders` ِ واقعی، در state ِ موقت.

        (۱) parse_when ِ «۱۵ دقیقه دیگه…» = now+۹۰۰ ± ۲ ثانیه
        (۲) add + beat با ساعتِ تزریقیِ بعد از موعد ⇒ fired_ts و متن به send_fn
        (۳) ساعتِ ۲۳:۳۰ ⇒ عادی معوق می‌شود ولی «فوری» رد می‌شود (رأی ۸)."""
        import reminders as rm   # noqa: WPS433
        if os.environ.get(rm.FLAG, "0") != "1":
            return {"ok": False, "blocked": True,
                    "line": f"فلگِ {rm.FLAG} خاموش است"}
        tmp = Path(tempfile.mkdtemp(prefix="journey-reminders-"))
        try:
            with _TmpState(tmp):
                day = datetime.fromtimestamp(self.now())
                base = day.replace(hour=10, minute=0, second=0,
                                   microsecond=0).timestamp()
                due, cleaned = rm.parse_when("۱۵ دقیقه دیگه یادم بنداز قرص",
                                             now=base)
                if due is None or abs(float(due) - (base + 900)) > 2.0:
                    return {"ok": False,
                            "line": f"parse_when موعدِ ۱۵ دقیقه را نفهمید (due={_ltr(due)})"}
                it = rm.add(cleaned or "قرص", due_ts=due, scope="dm", now=base)
                if not it or not it.get("id"):
                    return {"ok": False, "line": "add چیزی ذخیره نکرد"}
                got = []
                n = rm.beat(now=base + 901,
                            send_dm_fn=lambda t, rid: got.append((t, rid)),
                            send_leg_fn=lambda *_a: None)
                if n != 1 or not got or "قرص" not in got[0][0]:
                    return {"ok": False,
                            "line": f"شلیک نشد یا متن نرسید (n={_fa(n)}, got={_fa(len(got))})"}
                fired = [x for x in rm.list_open() if x.get("id") == it["id"]]
                if not fired or not fired[0].get("fired_ts"):
                    return {"ok": False, "line": "fired_ts روی آیتم ننشست"}
                quiet_ts = day.replace(hour=23, minute=30, second=0,
                                       microsecond=0).timestamp()
                calm = rm.add("قرصِ معمولی", due_ts=quiet_ts - 60,
                              scope="dm", now=quiet_ts - 120)
                urgent = rm.add("فوری: قرصِ قلب", due_ts=quiet_ts - 60,
                                scope="dm", now=quiet_ts - 120)
                got2 = []
                n2 = rm.beat(now=quiet_ts,
                             send_dm_fn=lambda t, rid: got2.append((t, rid)),
                             send_leg_fn=lambda *_a: None)
                ids2 = [x[1] for x in got2]
                if n2 != 1 or ids2 != [urgent["id"]]:
                    return {"ok": False,
                            "line": "پنجرهٔ سکوتِ ۲۳:۳۰ درست عمل نکرد — "
                                    f"شلیک‌شده‌ها {_ltr(ids2)}"}
                still = [x for x in rm.list_open() if x.get("id") == calm["id"]]
                if not still or still[0].get("fired"):
                    return {"ok": False,
                            "line": "یادآوریِ عادی در پنجرهٔ سکوت دور ریخته شد (باید معوق بماند)"}
                fa_when = datetime.fromtimestamp(base + 900).strftime("%H:%M")
                return {"ok": True,
                        "line": "یادآوری سالم — parse «۱۵ دقیقه دیگه»→"
                                + _ltr(fa_when)
                                + f" · شلیک با fired_ts و متنِ «{_esc(got[0][0][:28])}»"
                                " · ۲۳:۳۰ عادی معوق شد و فوری رد شد"}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _prove_leg_command(self) -> dict:
        """P6 — `leg_commands.classify` روی هر پنج فرمانِ کارتِ سفر، و یک
        **جملهٔ کار** که هرگز نباید بلعیده شود (درسِ بیش‌بستِ LEG_ALIASES)."""
        import leg_commands as lc   # noqa: WPS433
        expect = (("وضعیت", "status"), ("صف", "queue"),
                  ("گزارش امروز", "report"), ("قدم بعدی", "next"),
                  ("مانع چیست", "blockers"))
        bad = [(t, lc.classify(t)) for t, want in expect if lc.classify(t) != want]
        if bad:
            return {"ok": False,
                    "line": "فرمانِ طبیعی نگاشت نشد — " + _ltr(str(bad)[:120])}
        work = "دیوار اتاق را رنگ بزن"
        swallowed = lc.classify(work)
        if swallowed is not None:
            return {"ok": False,
                    "line": f"جملهٔ کار به‌جای Task فرمان شد ({_ltr(swallowed)}) — کار گم می‌شود"}
        return {"ok": True,
                "line": f"فرمانِ طبیعی سالم — {_fa(len(expect))} فرمان درست نگاشت شد"
                        " و «دیوار اتاق را رنگ بزن» کار ماند (بلعیده نشد)"}

    def _prove_leg_resolve(self) -> dict:
        """P7 — قوسِ رفعِ مانع روی `leg_tasks` ِ واقعی، در پوشهٔ موقت:
        add → BLOCKED با سؤال → resolve_blocked(جواب) ⇒ از BLOCKED بیرون
        می‌آید و متن نشانِ «➕ اطلاعات مالک» می‌گیرد."""
        import leg_tasks as lt   # noqa: WPS433
        tmp = Path(tempfile.mkdtemp(prefix="journey-legtasks-"))
        try:
            with _TmpState(tmp, leg_tasks=True):
                now = self.now()
                t = lt.add("lead", "کارِ آزمایشیِ سفرِ پذیرش", now=now)
                if not t:
                    return {"ok": False, "line": "add کاری نساخت"}
                b = lt.set_state("lead", t["id"], lt.BLOCKED,
                                 question="محلهٔ پروژه کجاست؟", now=now + 1)
                if not b or b.get("state") != lt.BLOCKED:
                    return {"ok": False, "line": "گذار به BLOCKED نشد"}
                r = lt.resolve_blocked("lead", t["id"], "Parramatta", now=now + 2)
                if not r:
                    return {"ok": False, "line": "resolve_blocked چیزی برنگرداند"}
                if r.get("state") == lt.BLOCKED:
                    return {"ok": False, "line": "کار هنوز BLOCKED است"}
                if "➕ اطلاعات مالک" not in str(r.get("text") or ""):
                    return {"ok": False, "line": "جوابِ مالک به متنِ کار نچسبید"}
                return {"ok": True,
                        "line": "رفعِ مانع سالم — " + _ltr(t["id"])
                                + f" از BLOCKED به {_ltr(r.get('state'))} رفت"
                                " و «➕ اطلاعات مالک: Parramatta» به متن چسبید"}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _prove_lead_card(self) -> dict:
        """P8 — ساختِ کارتِ «لیدِ آماده» بدونِ هیچ ارسالی.

        `lead_pipeline._card_text` تابعِ **خالص** است (همان که beat ِ تولیدی
        صدا می‌زند)؛ ورودی‌اش را از `lead_scorer.score_lead` و
        `lead_research.enrich` ِ واقعی می‌گیریم. صفر I/O، صفر شبکه، صفر send."""
        import lead_pipeline as lp   # noqa: WPS433
        import lead_research as lr   # noqa: WPS433
        import lead_scorer as ls     # noqa: WPS433
        lead = {
            "source": "acceptance-journey",
            "description": ("Strata remedial render and paint of common property "
                            "walls and balcony balustrades across 18 units for the "
                            "owners corporation; interior and exterior repaint, "
                            "approx 2400 m2, budget guidance 95000 AUD, works "
                            "needed next month."),
            "address": "12 Sample St, Parramatta NSW 2150",
            "cost_of_development": 95000, "size_m2": 2400,
            "contact": {"email": "journey@example.invalid"},
        }
        sc = ls.score_lead(lead)
        research = lr.enrich(lead)
        if sc.action != "draft":
            return {"ok": False,
                    "line": f"لیدِ strata مسیرِ کارت نگرفت — امتیاز {_fa(sc.score)}"
                            f" action={_ltr(sc.action)}"}
        if lr.is_stuck(research):
            return {"ok": False,
                    "line": "تحقیق لید را گیر دانست — " + _ltr(",".join(research.get("missing") or []))}
        card = lp._card_text("LEAD-JOURNEY-PROBE", sc, None, research)
        if "لیدِ آماده" not in card or "LEAD-JOURNEY-PROBE" not in card:
            return {"ok": False, "line": "کارت ساخته شد ولی شکلش کارتِ لید نیست"}
        return {"ok": True, "card_chars": len(card),
                "line": f"ماشینِ لید سالم — امتیاز {_fa(sc.score)}/۱۰۰ (draft)"
                        f" · تحقیق بی‌مانع · کارتِ {_fa(len(card))} کاراکتری ساخته شد"
                        " (بدونِ هیچ ارسالی)"}

    def _prove_miniapp(self) -> dict:
        """P9 — تنها اثباتی که سرتاسری است و به مالک هیچ نیازی ندارد:
        خودِ تونل را از بیرون صدا می‌زنیم. `/miniapp` باید ۲۰۰ بدهد (شِلِ
        بی‌داده) و `/api/miniapp` بدونِ initData باید ۴۰۳ بدهد (دیوارِ HMAC).

        ⚠️ این دو ضربه در `miniapp-hits.jsonl` هم می‌نشینند — پنجرهٔ زمانی‌شان
        ثبت می‌شود تا `_verify_p9` آن‌ها را **به‌عنوان تپِ مالک نشمارد**.
        (پنجره با ساعتِ همین پروسه ساخته می‌شود و دروازه هم با `time.time()`
        مهر می‌زند — در تولید یک ساعت‌اند؛ ±۳ ثانیه حاشیهٔ لغزش است.)"""
        d = _read_json(self.miniapp_url_path, {}) or {}
        url = str(d.get("url") or "").strip().rstrip("/")
        if not url.startswith("https://"):
            return {"ok": False, "blocked": True,
                    "line": "URL ِ تونل در miniapp-url.json نیست"}
        t0 = self.now()
        shell = self._http_fn(url + "/miniapp")
        api = self._http_fn(url + "/api/miniapp")
        window = [t0 - 3.0, self.now() + 3.0]
        if shell.get("status") != 200:
            return {"ok": False, "hit_window": window,
                    "line": f"{_ltr(url)}/miniapp کدِ {_ltr(shell.get('status'))} داد"
                            + (f" ({_ltr(shell.get('error'))})" if shell.get("error") else "")}
        if api.get("status") != 403:
            return {"ok": False, "hit_window": window,
                    "line": "دیوارِ /api/miniapp بدونِ initData کدِ "
                            f"{_ltr(api.get('status'))} داد — انتظار ۴۰۳ بود"}
        return {"ok": True, "hit_window": window,
                "line": "تونل از بیرون سالم — /miniapp=۲۰۰ (شِل) و "
                        "/api/miniapp بدونِ initData=۴۰۳ (دیوارِ HMAC بسته)"}

    def _prove_qbudget(self) -> dict:
        """P10 — چرخهٔ کاملِ بودجهٔ سؤال روی store ِ موقت:
        submit → pending همان را می‌دهد → mark_asked بودجه می‌سوزاند و از
        pending بیرونش می‌برد → record_answer رفت‌وبرگشت می‌کند."""
        import question_budget as qb   # noqa: WPS433
        if not qb.enabled():
            return {"ok": False, "blocked": True,
                    "line": f"فلگِ {qb.FLAG} خاموش است"}
        tmp = Path(tempfile.mkdtemp(prefix="journey-qbudget-"))
        try:
            with _TmpState(tmp):
                now = self.now()
                used0 = qb.used(now)
                r = qb.submit("سؤالِ آزمایشیِ سفرِ پذیرش؟", context="اثباتِ قابلیت",
                              goal="سنجشِ چرخهٔ بودجه", now=now)
                if not r or not r.get("item"):
                    return {"ok": False, "line": "submit چیزی ثبت نکرد"}
                qid = r["item"]["id"]
                p = qb.pending(now)
                if not p or p.get("id") != qid:
                    return {"ok": False,
                            "line": f"pending سؤالِ تازه را نداد (p={_ltr((p or {}).get('id'))})"}
                a = qb.mark_asked(qid, now=now + 1)
                if not a or not a.get("asked"):
                    return {"ok": False, "line": "mark_asked بودجه را مصرف نکرد"}
                if qb.used(now) != used0 + 1:
                    return {"ok": False,
                            "line": f"شمارندهٔ بودجه تکان نخورد ({_fa(qb.used(now))})"}
                if (qb.pending(now) or {}).get("id") == qid:
                    return {"ok": False, "line": "سؤالِ تحویل‌شده هنوز در pending است"}
                ans = qb.record_answer(qid, "نقاشی — چون نقدِ امروز از آن‌جاست.",
                                       now=now + 2)
                if not ans or not str(ans.get("answer") or "").startswith("نقاشی"):
                    return {"ok": False, "line": "record_answer جواب را برنگرداند"}
                return {"ok": True,
                        "line": "بودجهٔ سؤال سالم — " + _ltr(qid)
                                + f" ثبت شد ({_ltr(r.get('status'))})، pending دیدش،"
                                f" mark_asked بودجه را به {_fa(qb.used(now))} برد،"
                                " و جواب رفت‌وبرگشت کرد"}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _prove_ask_vault(self) -> dict:
        """اثباتِ در-پروسهٔ بازیابی: `ask_vault.query` روی والتِ **واقعی**،
        فقط-خواندنی، k کوچک، با ask_fn ِ تزریقی ⇒ صفر تماسِ مدل، صفر خرج.
        صادقانه: این «بازیابی» را اثبات می‌کند نه «تولیدِ جواب» را."""
        try:
            import ask_vault as av   # noqa: WPS433 — lazy
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "line": f"import ناموفق ({type(e).__name__})"}
        if not av.enabled():
            return {"ok": False, "blocked": True,
                    "line": "فلگِ OCTOPUS_TG_ASK_VAULT خاموش است"}

        def _stub(_kind, _prompt, **_kw):
            return {"ok": True, "text": "(اثباتِ بازیابی — مدل صدا زده نشد)",
                    "tier": "local"}
        try:
            r = av.query("امروز چه چیزی ساخته شد؟", vault_root=str(self.org_root),
                         ask_fn=_stub, k=3)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "line": f"query استثنا داد ({type(e).__name__})"}
        srcs = list(r.get("sources") or [])
        if not srcs:
            return {"ok": False,
                    "line": "بازیابی صفر منبع داد (reason=" + str(r.get("reason") or "—") + ")"}
        return {"ok": True, "sources": srcs,
                "line": f"بازیابی {_fa(len(srcs))} منبعِ واقعی داد — "
                        + _ltr(" ، ".join(srcs[:3]))}

    def _submit_synthetic_lead(self) -> dict:
        """یک کاندیدِ **مصنوعیِ** برچسب‌دار به تنها درِ ورودیِ لید.

        امتیازِ ۸۳ (strata remedial + paint + recurring buyer) ⇒ مسیرِ draft ⇒
        کارتِ «لیدِ آماده». channel=synthetic_test در EffectorGate سختاً بلاک
        است و outbound هم disarmed — هیچ پیامی به هیچ مشتری نمی‌رود."""
        try:
            import lead_candidate_inbox as lci   # noqa: WPS433 — lazy
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "status": "import_error", "reason": type(e).__name__}
        scope = ("Strata remedial render and paint of common property walls and "
                 "balcony balustrades across 18 units for the owners corporation; "
                 "interior and exterior repaint, approx 2400 m2, budget guidance "
                 "95000 AUD, works needed next month.")
        stamp = datetime.fromtimestamp(self.now()).strftime("%Y%m%d-%H%M")
        cand = {
            "source": {"channel": "synthetic_test",
                       "received_at": datetime.fromtimestamp(self.now()).isoformat()},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit",
                        "evidence": "acceptance-journey synthetic probe",
                        "compliance_reason": "owner-run self-test"},
            "request": {"scope_text": scope},
            "property": {"address": "12 Sample St, Parramatta NSW 2150",
                         "suburb": "Parramatta"},
            "contact": {"name": "Journey Probe", "organisation": "Sample Strata Plan",
                        "email": "journey@example.invalid",
                        "preferred_channel": "email"},
        }
        try:
            return lci.submit_candidate(cand, source_id=f"acceptance-journey-{stamp}")
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "status": "exception", "reason": type(e).__name__}

    def _outcome_rows(self, since: float) -> list:
        """رأیِ پایدارِ تازه در outcomes.db (فقط‌خواندنی؛ delivered = تحویل نه رأی)."""
        p = self.outcomes_db_path
        if not p.exists():
            return []
        out = []
        con = None
        try:
            con = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True, timeout=3)
            rows = con.execute(
                "SELECT event_id, proposal_id, leg_id, lead_id, event_type, "
                "verdict, recorded_at, correlation_id, payload_json "
                "FROM outcomes ORDER BY rowid DESC LIMIT 60"
            ).fetchall()
        except sqlite3.Error:
            return []
        finally:
            if con is not None:
                try:
                    con.close()
                except sqlite3.Error:
                    pass
        for r in rows:
            ts = _iso_to_ts(r[6])
            if ts is None or ts < float(since):
                continue
            if str(r[4] or "") == "delivered":
                continue
            try:
                payload = json.loads(r[8]) if r[8] else {}
            except (ValueError, TypeError):
                payload = {}
            out.append({"event_id": r[0], "proposal_id": r[1], "leg_id": r[2],
                        "lead_id": r[3], "event_type": r[4], "verdict": r[5],
                        "recorded_at": r[6], "correlation_id": r[7],
                        "payload": payload if isinstance(payload, dict) else {}})
        return out

    # ─── گزارشِ نهایی ──────────────────────────────────────────────────────
    def _group_of(self, verdict: str) -> str:
        """حکم → یکی از چهار گروهِ کارنامه. سه گروهِ اصلیِ خواستهٔ مالک، به‌علاوهٔ
        یک گروهِ باقی‌مانده برای فازی که نه دیده شد نه اثباتِ در-پروسه داشت —
        وگرنه همان فازها بی‌صدا از کارنامه می‌افتادند."""
        v = str(verdict or VERDICT_NOT_RUN)
        if v == VERDICT_PASS:
            return GROUP_SEEN
        if v == VERDICT_CAPABILITY_OK:
            return GROUP_CAPABLE
        if v == VERDICT_BROKEN:
            return GROUP_BROKEN
        return GROUP_UNKNOWN

    def report_groups(self, st: dict) -> dict:
        """{سرگروه: [(phase, rec), …]} — منبعِ یگانهٔ شمارش‌های کارنامه."""
        out = {GROUP_SEEN: [], GROUP_CAPABLE: [], GROUP_BROKEN: [],
               GROUP_UNKNOWN: []}
        for ph in _PHASES:
            if ph["key"] == _FINAL_KEY:
                continue
            rec = (st.get("phases") or {}).get(ph["key"]) or {}
            out[self._group_of(rec.get("verdict"))].append((ph, rec))
        return out

    def compose_report(self, st: dict) -> str:
        """کارنامهٔ فارسی، **سه‌گروهیِ صریح** (خواستِ مالک ۰۷-۳۱ عصر):

            ✅ کار کرد و دیدی · 🟢 قابلیت سالم، تپِ تو نیامد · 🔴 خراب

        و یک گروهِ چهارم برای «نه دیده شد، نه اثبات‌پذیر بود». هر خطِ شاهد
        آرتیفکتِ خودش را نگه می‌دارد. شاهدها از قبل escape/isolate شده‌اند —
        این‌جا دوباره escape نمی‌شوند (وگرنه &amp;amp; می‌شد)."""
        icon = {VERDICT_PASS: "✅", VERDICT_PENDING: "⏳", VERDICT_TIMEOUT: "⌛️",
                VERDICT_NOT_DUE: "🕘", VERDICT_BLOCKED: "🚫",
                VERDICT_WAIT: "⏳", VERDICT_NOT_RUN: "▫️",
                VERDICT_CAPABILITY_OK: "🟢", VERDICT_BROKEN: "🔴",
                VERDICT_PARTIAL: "🟠", VERDICT_DEGRADED: "🩹"}
        groups = self.report_groups(st)
        n = {k: len(v) for k, v in groups.items()}
        graded = sum(n.values())
        started = st.get("started_at")
        dur = _age_str(self.now() - float(started)) if started else "؟"
        lines = [REPORT_TITLE,
                 f"مدت: {dur} · فاز: {_fa(graded)} · "
                 f"نسخه: {_ltr(_git_short_head(self.org_root))}",
                 f"✅ {_fa(n[GROUP_SEEN])} · 🟢 {_fa(n[GROUP_CAPABLE])} · "
                 f"🔴 {_fa(n[GROUP_BROKEN])} · ⌛️ {_fa(n[GROUP_UNKNOWN])}",
                 "──────────"]
        blurb = {
            GROUP_SEEN: "قابلیت سالم بود و تپِ خودت هم ثبت شد.",
            GROUP_CAPABLE: "خودِ سیستم همین‌جا اثبات شد؛ فقط تپِ تو نیامد "
                           "— یعنی «تو نبودی»، نه «خراب است».",
            GROUP_BROKEN: "این‌ها واقعاً ایراد دارند — اثباتِ درون‌فرایندی هم شکست.",
            GROUP_UNKNOWN: "نه شاهدی از تو دیدم، نه اثباتِ درون‌فرایندی ممکن بود.",
        }
        for head in (GROUP_SEEN, GROUP_CAPABLE, GROUP_BROKEN, GROUP_UNKNOWN):
            rows = groups[head]
            lines.append(f"<b>{head}</b> ({_fa(len(rows))})")
            if not rows:
                lines.append("   — هیچ")
                continue
            lines.append("   " + blurb[head])
            for ph, rec in rows:
                v = str(rec.get("verdict") or VERDICT_NOT_RUN)
                ev = [str(e) for e in (rec.get("evidence") or []) if str(e).strip()]
                lines.append(f"{icon.get(v, '▫️')} <b>{ph['key']}</b> "
                             f"{ph['title']} — {v}")
                for e in (ev[:3] or ["بدونِ شاهد"]):
                    lines.append("   " + e[:180])
                errs = rec.get("errors") or []
                if errs:
                    lines.append("   ⚠️ " + _esc(str(errs[-1])[:120]))
        lines += ["──────────", "<b>کارهای بازِ تو</b>"]
        lines += ["▸ " + x for x in self._owner_needs(st)]
        lines += ["", "🟢 یعنی سیستم را همین‌جا آزمودم و کار کرد؛ فقط تپِ تو "
                  "ثبت نشد. 🔴 یعنی واقعاً باید درست شود."]
        return "\n".join(lines)

    def _owner_needs(self, st: dict) -> list:
        needs = []
        p8 = (st["phases"].get("P8") or {}).get("verdict")
        if p8 != VERDICT_PASS:
            needs.append("رأیِ ✅/❌ روی کارتِ لید — بدونِ آن حلقهٔ یادگیریِ لید بسته نمی‌شود")
        needs.append("ارسالِ بیرونیِ لید هنوز <b>خاموش</b> است (OCTOPUS_WIRE_LEAD_OUTBOUND): "
                     "برای مسلح‌کردن هم رأیِ سقفِ روزانه لازم است هم اعتبارِ SMTP/ایمیل")
        needs.append("سقفِ روزانهٔ outbound را باید خودت عدد بدهی (منشور، رأی ۱۷)")
        p9 = (st["phases"].get("P9") or {}).get("verdict")
        if p9 != VERDICT_PASS:
            needs.append("یک‌بار بازکردنِ داشبورد تا ثابت شود تونل از بیرون هم کار می‌کند")
        p11 = (st["phases"].get("P11") or {}).get("verdict")
        if p11 in (VERDICT_NOT_DUE, VERDICT_WAIT):
            needs.append("جمع‌بندیِ شب هنوز موعدش نرسیده بود — امشب خودش می‌آید")
        return needs

    def _write_report_note(self, report_html: str):
        """همان محتوا در والت، با فرانت‌مترِ معتبرِ قانونِ اساسی §۶."""
        body = re.sub(r"<[^>]+>", "", report_html)
        body = (body.replace("&amp;", "&").replace("&lt;", "<")
                .replace("&gt;", ">").replace(_LRI, "").replace(_PDI, ""))
        now = self.now()
        day = datetime.fromtimestamp(now).strftime("%Y-%m-%d")
        stamp = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H%M")
        fm = ["---", "type: telegram-log", 'project: ""', "status: active",
              "tags: [telegram, acceptance]", f"created: {day}", f"updated: {day}",
              "created_by: agent", "---", "",
              "# کارنامهٔ سفرِ پذیرشِ خودکار", ""]
        p = self.org_root.joinpath(*RAW_SUBDIR[:1]) / f"{stamp} کارنامه سفر پذیرش.md"
        if _atomic_write(p, "\n".join(fm) + body + "\n"):
            return str(p)
        return None

    def _delete_scheduled_task(self) -> dict:
        """خودکشیِ زمان‌بندی — سفر تمام شد، تیکِ بعدی نباید بیاید. fail-soft.

        ممیزی ۰۷-۳۱ (§5b): اول Query (فقط‌خواندنی) — تسکِ نبوده «حذف شد»
        ادعا نمی‌شود و پیامِ صادقانهٔ not-found برمی‌گردد؛ Delete فقط وقتی
        تسک واقعاً هست. سفر هرگز نمی‌گوید خودش را متوقف کرد مگر rc=0."""
        try:
            q = subprocess.run(["schtasks", "/Query", "/TN", self._task_name],
                               capture_output=True, text=True, timeout=30)
            if q.returncode != 0:
                return {"ok": False, "rc": q.returncode, "found": False,
                        "msg": (f"task not found: {self._task_name} — "
                                "چیزی حذف نشد؛ اگر تسکی با نامِ دیگر زنده است، "
                                "هر ۱۵ دقیقه بیدار می‌شود (بی‌اثر چون done=True)")}
            r = subprocess.run(["schtasks", "/Delete", "/TN", self._task_name, "/F"],
                               capture_output=True, text=True, timeout=30)
            return {"ok": r.returncode == 0, "rc": r.returncode, "found": True,
                    "msg": (r.stdout or r.stderr or "").strip()[:160]}
        except Exception as e:  # noqa: BLE001 — نشد که نشد؛ گزارش می‌دهیم
            return {"ok": False, "rc": None, "found": None,
                    "msg": f"{type(e).__name__}"}

    # ─── تیک ───────────────────────────────────────────────────────────────
    def tick(self) -> dict:
        st = self.load_state()
        now = self.now()
        summary = {"acted": [], "sends": 0, "done": bool(st.get("done"))}
        if st.get("done"):
            return summary
        if not st.get("started_at"):
            st["started_at"] = now
        st["ticks"] = int(st.get("ticks") or 0) + 1
        st["last_tick_ts"] = now
        # claim ِ حکم‌های برگشته آزاد می‌شود (ممیزی §۴ — ردیفِ دزدیده‌شدهٔ P1).
        self._release_stale_claims(st)

        # سقفِ کل: بعد از deadline مستقیم به گزارشِ نهایی (هر چه هست، همان است).
        if (now - float(st["started_at"]) >= self._deadline_s
                and int(st.get("phase_idx") or 0) < _FINAL_IDX):
            self._force_finish(st)
            summary["forced"] = True

        sends = 0
        for _step in range(MAX_STEPS_PER_TICK):
            idx = int(st.get("phase_idx") or 0)
            if idx >= len(_PHASES):
                st["done"] = True
                break
            ph = _PHASES[idx]
            rec = self._rec(st, ph["key"])

            if rec.get("prompt_sent_ts") is None:
                if ph["sends"] and sends >= MAX_SENDS_PER_TICK:
                    break
                ok = True
                if ph["sends"]:
                    sends += 1
                    rec.setdefault("meta", {})["prompt_blocked"] = False
                    try:
                        ok = self._prompt(ph["key"], st, rec)
                    except Exception as e:  # noqa: BLE001 — یک فاز کلِ تیک را نمی‌کشد
                        rec["errors"].append(f"prompt {type(e).__name__}: {e}"[:200])
                        ok = False
                if not ok:
                    # شکستِ ارسال ⇒ PENDING و **هرگز** جلو رفتنِ مکان‌نما.
                    rec["attempts"] = int(rec.get("attempts") or 0) + 1
                    rec["verdict"] = VERDICT_PENDING
                    summary["acted"].append(f"{ph['key']}:send-failed")
                    # تنها استثنا (مستند): فازِ پایانی. اگر گزارش بعد از
                    # MAX_ATTEMPTS هم نرفت، دیگر تا ابد تیک نمی‌زنیم — نوتِ
                    # والت را می‌نویسیم، تسک را حذف می‌کنیم و تمام. هیچ
                    # ادعای موفقیتی نمی‌شود؛ verdict همان TIMEOUT می‌ماند.
                    if (ph["key"] == _FINAL_KEY
                            and rec["attempts"] >= MAX_ATTEMPTS):
                        rec["verdict"] = VERDICT_TIMEOUT
                        self._finish_without_delivery(st, rec)
                        st["done"] = True
                        summary["acted"].append(f"{ph['key']}:undelivered-finish")
                        break
                    # ممیزی §5a: درخواستی که **ساختاراً** ساخته نمی‌شود (فلگ/
                    # URL/config غایب — نه شکستِ شبکه) نباید کلِ سفر را تا
                    # deadline قفل کند: بعد از MAX_ATTEMPTS حکمِ صادقِ BLOCKED
                    # می‌گیرد و مکان‌نما رد می‌شود. شکستِ ارسالِ خالص (تلگرام
                    # قطع) همان رفتارِ قدیم را دارد: PENDING و صفر پیشروی.
                    if (rec.get("meta", {}).get("prompt_blocked")
                            and rec["attempts"] >= MAX_ATTEMPTS):
                        rec["verdict"] = VERDICT_BLOCKED
                        rec["evidence"] = rec.get("evidence") or []
                        rec["evidence"].append(
                            "درخواستِ فاز ساختاراً ساخته نشد — "
                            + _esc(str((rec.get("errors") or ["؟"])[-1])[:140]))
                        st["phase_idx"] = idx + 1
                        summary["acted"].append(f"{ph['key']}:prompt-blocked")
                        continue
                    break
                rec["prompt_sent_ts"] = now
                rec["verdict"] = VERDICT_PENDING
                summary["acted"].append(f"{ph['key']}:prompted")
                if not ph["immediate"]:
                    break

            try:
                verdict, ev = self._verify(ph["key"], st, rec)
            except Exception as e:  # noqa: BLE001
                rec["errors"].append(f"verify {type(e).__name__}: {e}"[:200])
                verdict, ev = VERDICT_PENDING, [f"سنجش استثنا داد: {type(e).__name__}"]
            rec["evidence"] = [str(x) for x in (ev or [])]

            if verdict in _TERMINAL:
                rec["verdict"] = verdict
                st["phase_idx"] = idx + 1
                summary["acted"].append(f"{ph['key']}:{verdict}")
                continue
            if verdict == VERDICT_WAIT:
                rec["verdict"] = VERDICT_PENDING
                summary["acted"].append(f"{ph['key']}:wait")
                break
            # PENDING — تلاش فقط وقتی شمرده می‌شود که پنجره واقعاً بسته شده باشد.
            if now - float(rec["prompt_sent_ts"]) >= float(ph["window_s"]):
                rec["attempts"] = int(rec.get("attempts") or 0) + 1
                if rec["attempts"] >= MAX_ATTEMPTS:
                    # پایانِ صبر: اگر اثباتِ درون‌فرایندی داریم، حکم از آن
                    # می‌آید (CAPABILITY-OK / BROKEN / BLOCKED) نه TIMEOUT ِ کور.
                    rec["verdict"] = self._timeout_verdict(rec)
                    st["phase_idx"] = idx + 1
                    summary["acted"].append(f"{ph['key']}:{rec['verdict']}")
                    continue
            rec["verdict"] = VERDICT_PENDING
            summary["acted"].append(f"{ph['key']}:pending")
            break

        if int(st.get("phase_idx") or 0) >= len(_PHASES):
            st["done"] = True
        summary["sends"] = sends
        summary["done"] = bool(st.get("done"))
        summary["phase_idx"] = int(st.get("phase_idx") or 0)
        self.save_state(st)
        return summary

    # اثباتِ درون‌فرایندیِ هر فاز — برای force-finish هم (ممیزی §6 ردیف ۱۶):
    # «۷ فاز را نرسیدم بسنجم» با «هر ۱۳ قابلیت سالم است؛ مالک ۲ تا را تپ کرد»
    # زمین تا آسمان فرق دارد. فازِ بی‌درخواست هم قابلیتش را همین‌جا می‌سنجد.
    _PROOF_FNS = {"P2": "_prove_capture_text", "P3": "_prove_capture_media",
                  "P4A": "_prove_reminders", "P4B": "_prove_reminders",
                  "P5": "_prove_ask_vault", "P6": "_prove_leg_command",
                  "P7": "_prove_leg_resolve", "P8": "_prove_lead_card",
                  "P9": "_prove_miniapp", "P10": "_prove_qbudget"}

    def _force_finish(self, st: dict) -> None:
        """سقفِ زمان خورد: هر فازِ ناتمام صادقانه مهر می‌خورد، بعد گزارشِ نهایی."""
        for i, ph in enumerate(_PHASES):
            if i >= _FINAL_IDX:
                break
            rec = self._rec(st, ph["key"])
            if rec.get("verdict") in _TERMINAL:
                continue
            if ph["key"] == "P11":
                rec["verdict"] = VERDICT_NOT_DUE
                rec["evidence"] = rec.get("evidence") or [
                    "سفر قبل از موعدِ جمع‌بندیِ شب تمام شد — نه سنجیده شد، نه ادعا شد"]
            elif rec.get("prompt_sent_ts") is None:
                fn_name = self._PROOF_FNS.get(ph["key"])
                if fn_name:
                    try:
                        cap = self._proof(rec, getattr(self, fn_name))
                    except Exception:  # noqa: BLE001
                        cap = None
                    rec["verdict"] = self._timeout_verdict(rec)
                    rec["evidence"] = [
                        OWNER_PREFIX + "نوبتِ درخواست نرسید (سقفِ زمانِ سفر) — "
                        "از مالک هرگز خواسته نشد",
                        self._cap_line(cap)]
                else:
                    rec["verdict"] = VERDICT_NOT_RUN
                    rec["evidence"] = ["نوبتش نرسید (سقفِ زمانِ سفر)"]
            else:
                rec["verdict"] = self._timeout_verdict(rec)
                if not rec.get("evidence"):
                    rec["evidence"] = ["شاهدی در پنجره دیده نشد"]
        st["phase_idx"] = _FINAL_IDX

    # ─── چاپِ وضعیت (فقط‌خواندنی) ──────────────────────────────────────────
    def status(self) -> dict:
        st = self.load_state()
        return {"done": bool(st.get("done")), "ticks": st.get("ticks"),
                "phase_idx": st.get("phase_idx"),
                "phases": {k: (v or {}).get("verdict")
                           for k, v in (st.get("phases") or {}).items()},
                "state_path": str(self.state_path)}


# ─── CLI ─────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="سفرِ پذیرشِ بدونِ ناظر (یک تیک)")
    ap.add_argument("--tick", action="store_true", help="یک تیکِ سفر (پیش‌فرض)")
    ap.add_argument("--status", action="store_true", help="فقط چاپِ وضعیت (صفر ارسال)")
    args = ap.parse_args(argv)
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001 — نبودِ .env = کلاینتِ not-wired، نه crash
        pass
    j = Journey()
    if args.status and not args.tick:
        print(json.dumps(j.status(), ensure_ascii=False, indent=1))
        return 0
    out = j.tick()
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
