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
  · **صداقتِ سخت:** شاهدِ غایب = PENDING (تا ۳ تلاش) و بعد TIMEOUT — هرگز PASS.
    هیچ‌وقت ادعا نمی‌کنیم مالک کاری کرده؛ فقط می‌گوییم چه آرتیفکتی دیدیم.
    «قابلیت در-پروسه اثبات شد» از «مالک دید» جدا برچسب می‌خورد.
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
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/telegram_center
_OPS = _HERE.parent                              # _ops
for _p in (str(_OPS), str(_OPS / "budget"), str(_HERE), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import tg_api          # noqa: E402

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
DEFAULT_TASK_NAME = "OctopusAcceptanceJourney"
RAW_SUBDIR = ("10 - Telegram processing", "Raw")

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_LRI, _PDI = "⁦", "⁩"        # ایزولهٔ bidi برای تکه‌های LTR (منشور UX-9)

VERDICT_PASS = "PASS"
VERDICT_PENDING = "PENDING"
VERDICT_TIMEOUT = "TIMEOUT"
VERDICT_WAIT = "WAIT"                  # هنوز موعدش نرسیده — تلاش شمرده نمی‌شود
VERDICT_NOT_DUE = "SCHEDULED-NOT-DUE"
VERDICT_BLOCKED = "BLOCKED"            # پیش‌نیازِ ساختاری غایب (فلگ/پیکربندی)
VERDICT_DEGRADED = "DEGRADED"          # سنجیده شد ولی محیط کامل نبود (P0)
VERDICT_NOT_RUN = "NOT-RUN"

_TERMINAL = (VERDICT_PASS, VERDICT_TIMEOUT, VERDICT_NOT_DUE, VERDICT_BLOCKED,
             VERDICT_DEGRADED)

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
                 org_root=None):
        self._client = client
        self._clock = clock or time.time
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
        v = st.setdefault("consumed", {}).setdefault(bucket, [])
        return v if isinstance(v, list) else []

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

    def _claim_dm_row(self, st: dict, row: dict) -> None:
        self._consumed(st, "dm_rows").append(f"{row.get('ts')}|{row.get('sha')}")

    # ── نوت‌های خامِ capture ────────────────────────────────────────────────
    def _raw_notes_since(self, st: dict, since: float) -> list:
        """(path, frontmatter, body) ِ نوت‌های Raw ِ تازه — مصرف‌شده‌ها کنار."""
        used = set(self._consumed(st, "raw_notes"))
        out = []
        try:
            names = sorted(self.raw_dir.glob("*.md"))
        except OSError:
            return out
        for p in names:
            try:
                if p.stat().st_mtime < float(since) - 1.0:
                    continue
            except OSError:
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
        return self._send(st, txt, label="P1") is not None

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
        return self._send(st, txt, label="P5") is not None

    def _prompt_p6(self, st: dict, rec: dict) -> bool:
        chat, topic = self._group_target("lead")
        if chat is None or topic is None:
            rec["errors"].append("center-config: chat_id/topics.lead غایب")
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
            return False
        snap = self._lead_task_snapshot()
        rec["meta"]["blocked_before"] = snap
        if not snap.get("blocked_ids"):
            rec["errors"].append("هیچ کارِ BLOCKED ای در lead-tasks نیست")
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
            return False
        if not qb.enabled():
            rec["errors"].append("OCTOPUS_TG_QBUDGET خاموش است")
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
            return False
        item = r["item"]
        rec["meta"]["qid"] = item.get("id")
        rec["meta"]["qstatus"] = r.get("status")
        # نکتهٔ قرارداد: `submit` با بودجهٔ آزاد خودش asked=True می‌کند، پس
        # `pending()` ِ مرکز دیگر آن را نمی‌بیند و **هرگز تحویل نمی‌شود**.
        # پس تحویل با خودِ ماست؛ متن عیناً `question_text` است تا مسیرِ
        # ریپلای→`record_answer` ِ مرکز (مارکرِ «سؤالِ اختاپوس» + Q-n) بخورد.
        txt = qb.question_text(item) + "\n\n(۱۰/۱۲ سفرِ آزمون)"
        return self._send(st, txt, label="P10") is not None

    def _prompt_p12(self, st: dict, rec: dict) -> bool:
        report = self.compose_report(st)
        rec["meta"]["report_chars"] = len(report)
        if self._send(st, report, label="P12") is None:
            rec["errors"].append("ارسالِ گزارشِ نهایی ناموفق — تیکِ بعد دوباره")
            return False           # نه نوت، نه حذفِ تسک: هنوز تمام نشده
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
            rec["meta"]["schtask"] = self._delete_scheduled_task()

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
        since = float(rec.get("prompt_sent_ts") or 0)
        rows = self._foreign_dm_rows(st, since)
        if not rows:
            return VERDICT_PENDING, ["هنوز هیچ ردیفِ DM ِ نه-از-ما در tg-send-log"]
        r = rows[0]
        self._claim_dm_row(st, r)
        return VERDICT_PASS, [
            "مشاهدهٔ مالک: مرکز یک پاسخِ DM تولید کرد که ما نفرستادیم — "
            f"tg-send-log ts={_ltr(round(float(r.get('ts') or 0), 1))} "
            f"sha={_ltr(r.get('sha'))} stream={_ltr(r.get('stream'))}"]

    def _verify_p2(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        for p, fm, _txt in self._raw_notes_since(st, since):
            if fm.get("message_id") and fm.get("chat_id"):
                self._consumed(st, "raw_notes").append(p.name)
                rec["meta"]["note"] = p.name
                return VERDICT_PASS, [
                    "مشاهدهٔ مالک: نوتِ خام ساخته شد — " + _ltr(p.name)
                    + f" · message_id={_ltr(fm.get('message_id'))}"
                    f" · chat_id={_ltr(fm.get('chat_id'))}"]
        return VERDICT_PENDING, [
            "هیچ نوتِ تازه‌ای با فرانت‌مترِ message_id/chat_id در "
            + _ltr("/".join(RAW_SUBDIR)) + " نیست"]

    def _verify_p3(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        for p, fm, txt in self._raw_notes_since(st, since):
            media = None
            if fm.get("file_id") or fm.get("duration") is not None:
                media = "voice"
            if "[voice]" in txt:
                media = "voice"
            elif "[photo]" in txt:
                media = "photo"
            if media:
                self._consumed(st, "raw_notes").append(p.name)
                rec["meta"]["note"] = p.name
                ev = ["مشاهدهٔ مالک: نوتِ رسانه — " + _ltr(p.name)
                      + f" · نوع={media}"]
                if fm.get("file_id"):
                    ev.append("file_id در فرانت‌متر حاضر است (ویس)")
                return VERDICT_PASS, ev
        return VERDICT_PENDING, ["نوتِ تازه‌ای با نشانِ [photo]/[voice] پیدا نشد"]

    def _verify_p4a(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        d = _read_json(self.reminders_path, {}) or {}
        for it in reversed(d.get("items") or []):
            try:
                created = float(it.get("created") or 0)
                due = float(it.get("due") or 0)
            except (TypeError, ValueError):
                continue
            if created < since:
                continue
            if not (created + 300 <= due <= created + 3600):
                continue
            rec["meta"]["reminder_id"] = it.get("id")
            rec["meta"]["reminder_due"] = due
            return VERDICT_PASS, [
                "مشاهدهٔ مالک: یادآوری ساخته شد — "
                f"{_ltr(it.get('id'))} · موعد "
                f"{_ltr(datetime.fromtimestamp(due).strftime('%H:%M'))}"
                f" · متن «{_esc(str(it.get('text') or '')[:40])}»"]
        return VERDICT_PENDING, [
            "در " + _ltr("reminders/reminders.json")
            + " هیچ آیتمِ تازه‌ای با موعدِ ۵–۶۰ دقیقهٔ آینده نیست"]

    def _verify_p4b(self, st: dict, rec: dict) -> tuple:
        rid = (st["phases"].get("P4A") or {}).get("meta", {}).get("reminder_id")
        if not rid:
            return VERDICT_BLOCKED, ["P4A یادآوری‌ای نساخت — پیش‌نیازِ این فاز غایب است"]
        d = _read_json(self.reminders_path, {}) or {}
        item = None
        for it in d.get("items") or []:
            if it.get("id") == rid:
                item = it
                break
        if item is None:
            return VERDICT_PENDING, [f"آیتمِ {_ltr(rid)} در store پیدا نشد"]
        fired_ts = item.get("fired_ts")
        if not item.get("fired") or not fired_ts:
            due = item.get("due")
            return VERDICT_PENDING, [
                f"{_ltr(rid)} هنوز شلیک نشده (fired=False)"
                + (f" · موعد {_ltr(datetime.fromtimestamp(float(due)).strftime('%H:%M'))}"
                   if due else "")]
        ev = [f"شلیک ثبت شد — {_ltr(rid)} · fired_ts="
              f"{_ltr(datetime.fromtimestamp(float(fired_ts)).strftime('%H:%M:%S'))}"]
        rows = [r for r in self._foreign_dm_rows(st, float(fired_ts) - 60.0)
                if abs(float(r.get("ts") or 0) - float(fired_ts)) <= 300.0]
        if rows:
            self._claim_dm_row(st, rows[0])
            ev.append("و یک ردیفِ DM ِ نه-از-ما نزدیکِ همان لحظه — "
                      f"ts={_ltr(round(float(rows[0].get('ts') or 0), 1))}")
            return VERDICT_PASS, ev
        ev.append("ولی ردیفِ DM ِ متناظر در tg-send-log پیدا نشد (تحویل اثبات نشد)")
        return VERDICT_PENDING, ev

    def _verify_p5(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        ev = []
        cap = rec.get("meta", {}).get("capability")
        if cap is None:
            cap = self._prove_ask_vault()
            rec["meta"]["capability"] = cap
        ev.append("قابلیت (در-پروسه، نه مشاهدهٔ مالک): " + str(cap.get("line") or ""))
        rows = self._foreign_dm_rows(st, since)
        if rows:
            self._claim_dm_row(st, rows[0])
            ev.insert(0, "مشاهدهٔ مالک: پاسخِ DM ِ نه-از-ما — "
                      f"ts={_ltr(round(float(rows[0].get('ts') or 0), 1))} "
                      f"sha={_ltr(rows[0].get('sha'))}")
            return VERDICT_PASS, ev
        ev.insert(0, "مشاهدهٔ مالک: هنوز ردیفِ DM ِ نه-از-ما نیست")
        return VERDICT_PENDING, ev

    def _verify_p6(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        topic = rec.get("meta", {}).get("topic")
        for r in self._send_rows(since):
            if str(r.get("surface") or "") != "group":
                continue
            if str(r.get("stream") or "") == "edit":
                continue            # تازه‌سازیِ کارتِ پا، نه پاسخ به فرمان
            if self._is_ours(st, r):
                continue
            if topic is None or r.get("topic") != topic:
                continue
            return VERDICT_PASS, [
                "مشاهدهٔ مالک: پاسخِ گروهی در تاپیکِ "
                f"{_fa(r.get('topic'))} — ts={_ltr(round(float(r.get('ts') or 0), 1))}"
                f" stream={_ltr(r.get('stream'))}"]
        return VERDICT_PENDING, [
            f"هیچ ردیفِ surface=group با topic={_fa(topic)} در پنجره نیست"]

    def _verify_p7(self, st: dict, rec: dict) -> tuple:
        before = rec.get("meta", {}).get("blocked_before") or {}
        ids = list(before.get("blocked_ids") or [])
        d = _read_json(self.lead_tasks_path, {}) or {}
        for t in d.get("tasks") or []:
            if ids and t.get("id") not in ids:
                continue
            if t.get("state") == "BLOCKED":
                continue
            if "➕ اطلاعات مالک" in str(t.get("text") or ""):
                return VERDICT_PASS, [
                    "مشاهدهٔ مالک: کارِ گیرکرده باز شد — "
                    f"{_ltr(t.get('id'))} · state={_ltr(t.get('state'))}"
                    " · متن نشانِ «➕ اطلاعات مالک» گرفت"]
        return VERDICT_PENDING, [
            "در " + _ltr("legs/lead-tasks.json")
            + " هنوز کاری از BLOCKED بیرون نیامده (بدونِ «➕ اطلاعات مالک»)"]

    def _verify_p8(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        ev = []
        card = [r for r in self._send_rows(since)
                if str(r.get("stream") or "") == "lead" and not self._is_ours(st, r)]
        if card:
            ev.append("کارتِ لید فرستاده شد — رسیدِ stream=lead ts="
                      f"{_ltr(round(float(card[0].get('ts') or 0), 1))}")
        else:
            ev.append("هنوز هیچ رسیدِ stream=lead در پنجره نیست (ضربانِ لوله ~۳۰-۴۰ دقیقه)")
        verdicts = self._outcome_rows(since)
        if verdicts:
            v = verdicts[0]
            ev.append("رأیِ مالک پایدار ثبت شد — outcomes.db "
                      f"event_id={_ltr(v.get('event_id'))} "
                      f"type={_ltr(v.get('event_type'))} "
                      f"verdict={_ltr(v.get('verdict'))} leg={_ltr(v.get('leg_id'))}")
            return VERDICT_PASS, ev
        ev.append("هیچ رأیِ تازه‌ای در " + _ltr("state/outcomes/outcomes.db") + " نیست")
        return VERDICT_PENDING, ev

    def _verify_p9(self, st: dict, rec: dict) -> tuple:
        since = float(rec.get("prompt_sent_ts") or 0)
        hits = []
        for h in _read_jsonl(self.miniapp_hits_path):
            try:
                if float(h.get("ts") or 0) >= since:
                    hits.append(h)
            except (TypeError, ValueError):
                continue
        if not hits:
            return VERDICT_PENDING, [
                "هیچ خطی در " + _ltr("telegram/miniapp-hits.jsonl") + " بعد از درخواست"]
        authed = [h for h in hits if h.get("authed")]
        ev = [f"دروازه {_fa(len(hits))} درخواست سرو کرد — آخری path="
              f"{_ltr(hits[-1].get('path'))} ok={_ltr(hits[-1].get('ok'))}"]
        if authed:
            ev.append(f"و {_fa(len(authed))} تای آن‌ها initData ِ معتبر داشت "
                      "(یعنی واقعاً از داخلِ تلگرام و از خودِ مالک)")
        else:
            ev.append("ولی هیچ‌کدام authed نبود — شِل باز شد، دادهٔ محافظت‌شده نه")
        return VERDICT_PASS, ev

    def _verify_p10(self, st: dict, rec: dict) -> tuple:
        qid = rec.get("meta", {}).get("qid")
        if not qid:
            return VERDICT_BLOCKED, ["سؤالی ثبت نشد (فلگ/بودجه)"]
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
                ev.append("مشاهدهٔ مالک: جواب ثبت شد — "
                          f"answered_ts={_ltr(when)}"
                          f" · «{_esc(str(it.get('answer'))[:60])}»")
                return VERDICT_PASS, ev
            ev.append("هنوز جوابی روی آن نیست (ریپلای به همان پیام لازم است)")
            return VERDICT_PENDING, ev
        return VERDICT_PENDING, [f"{_ltr(qid)} در store پیدا نشد"]

    def _verify_p11(self, st: dict, rec: dict) -> tuple:
        now = self.now()
        wrap_h = 21.5
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
        rows = self._foreign_dm_rows(st, datetime(dt.year, dt.month, dt.day,
                                                  int(wrap_h),
                                                  int((wrap_h % 1) * 60)).timestamp() - 300)
        if rows:
            self._claim_dm_row(st, rows[0])
            ev.append("و ردیفِ DM ِ متناظر — ts="
                      f"{_ltr(round(float(rows[0].get('ts') or 0), 1))}")
            return VERDICT_PASS, ev
        ev.append("ولی ردیفِ DM ِ متناظر پیدا نشد")
        return VERDICT_PENDING, ev

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
        try:
            pulse_age = now - float(cfg.get("last_pulse") or 0)
        except (TypeError, ValueError):
            pulse_age = None
        if pulse_age is None or pulse_age > 900:
            ok = False
        lines.append("مرکزِ تلگرام: نبض " + _age_str(pulse_age)
                     + f" · PID {_fa(cfg.get('boot_receipt_pid', '؟'))}")

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

    def _prove_ask_vault(self) -> dict:
        """اثباتِ در-پروسهٔ بازیابی: `ask_vault.query` روی والتِ **واقعی**،
        فقط-خواندنی، k کوچک، با ask_fn ِ تزریقی ⇒ صفر تماسِ مدل، صفر خرج.
        صادقانه: این «بازیابی» را اثبات می‌کند نه «تولیدِ جواب» را."""
        try:
            import ask_vault as av   # noqa: WPS433 — lazy
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "line": f"import ناموفق ({type(e).__name__})"}
        if not av.enabled():
            return {"ok": False, "line": "فلگِ OCTOPUS_TG_ASK_VAULT خاموش است"}

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
                "verdict, recorded_at FROM outcomes ORDER BY rowid DESC LIMIT 60"
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
            out.append({"event_id": r[0], "proposal_id": r[1], "leg_id": r[2],
                        "lead_id": r[3], "event_type": r[4], "verdict": r[5],
                        "recorded_at": r[6]})
        return out

    # ─── گزارشِ نهایی ──────────────────────────────────────────────────────
    def compose_report(self, st: dict) -> str:
        """کارنامهٔ فارسیِ یک-پیامی. شاهدها از قبل escape/isolate شده‌اند —
        این‌جا دوباره escape نمی‌شوند (وگرنه &amp;amp; می‌شد)."""
        icon = {VERDICT_PASS: "✅", VERDICT_PENDING: "⏳", VERDICT_TIMEOUT: "⌛️",
                VERDICT_NOT_DUE: "🕘", VERDICT_BLOCKED: "🚫",
                VERDICT_WAIT: "⏳", VERDICT_NOT_RUN: "▫️"}
        graded = [p for p in _PHASES if p["key"] != _FINAL_KEY]
        started = st.get("started_at")
        dur = _age_str(self.now() - float(started)) if started else "؟"
        n_pass = sum(1 for p in graded
                     if (st["phases"].get(p["key"]) or {}).get("verdict") == VERDICT_PASS)
        lines = ["🧪 <b>کارنامهٔ سفرِ پذیرش</b>",
                 f"مدت: {dur} · قبول: {_fa(n_pass)}/{_fa(len(graded))} · "
                 f"نسخه: {_ltr(_git_short_head(self.org_root))}",
                 "──────────"]
        for ph in graded:
            rec = st["phases"].get(ph["key"]) or {}
            v = str(rec.get("verdict") or VERDICT_NOT_RUN)
            ev = [str(e) for e in (rec.get("evidence") or []) if str(e).strip()]
            lines.append(f"{icon.get(v, '▫️')} <b>{ph['key']}</b> {ph['title']} — {v}")
            for e in (ev[:2] or ["بدونِ شاهد"]):
                lines.append("   " + e[:170])
            errs = rec.get("errors") or []
            if errs:
                lines.append("   ⚠️ " + _esc(str(errs[-1])[:120]))
        lines += ["──────────", "<b>چیزهایی که به تو نیاز دارد</b>"]
        lines += ["▸ " + n for n in self._owner_needs(st)]
        lines += ["", "هر ⌛️ یعنی «شاهدی ندیدم»، نه «خراب است» — اگر آن مرحله را",
                  "انجام نداده‌ای، همان توضیحش است. هرکدام را بگو، دوباره می‌سنجم."]
        return _cap_html("\n".join(lines), 3800)

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
        """خودکشیِ زمان‌بندی — سفر تمام شد، تیکِ بعدی نباید بیاید. fail-soft."""
        try:
            r = subprocess.run(["schtasks", "/Delete", "/TN", self._task_name, "/F"],
                               capture_output=True, text=True, timeout=30)
            return {"ok": r.returncode == 0, "rc": r.returncode,
                    "msg": (r.stdout or r.stderr or "").strip()[:160]}
        except Exception as e:  # noqa: BLE001 — نشد که نشد؛ گزارش می‌دهیم
            return {"ok": False, "rc": None, "msg": f"{type(e).__name__}"}

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
                    rec["verdict"] = VERDICT_TIMEOUT
                    st["phase_idx"] = idx + 1
                    summary["acted"].append(f"{ph['key']}:TIMEOUT")
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
                rec["verdict"] = VERDICT_NOT_RUN
                rec["evidence"] = ["نوبتش نرسید (سقفِ زمانِ سفر)"]
            else:
                rec["verdict"] = VERDICT_TIMEOUT
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
