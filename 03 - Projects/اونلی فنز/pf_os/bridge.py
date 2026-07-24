#!/usr/bin/env python3
"""bridge.py — پلِ Project-F OS به ارگانیسمِ اختاپوس (one-way، file-based).

این core درخواستِ مالک: «زیرمجموعهٔ اونلی‌فنز باید یک OS باشد که با کل اختاپوس
در ارتباط درست است.» این فایل آن ارتباط است.

قراردادِ file-pubsub (طبقِ _ops/wiring.py::cockpit_requests_beat و commentِ موجود
در _ops/state/saba-bridge.jsonl):
  - فرمت: یک JSON per line (JSONL append-only)
  - محتوا: {"ts": iso, "kind": <event>, "text": <content-free summary>}
  - kinds: draft_submitted, halt, resume, boundary, brain_tick_done,
           notify, kpi, learning_observed
  - writer: این فایل (pf_os)
  - reader (آینده): wiring.py::saba_bridge_beat (طبقِ pingshtein Fase 5B)

نامتغیرِ PII (حیاتی — طبقِ LANE-RULES §3 و قاعده‌ی قفل‌شده‌ی #۷):
  هرگز نام/شهر/محتوا/پلتفرم/PII در این فایل نمی‌نویسیم. فقط kind + summaryِ
  content-free (تعداد/وضعیت). organismِ مرکزی فقط یک تپِ بی‌نام از pf_os می‌بیند.

$0 آفلاین، stdlib-only، fail-soft.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import config

# ─── مسیرِ پل (طبقِ comment موجود در _ops/state/saba-bridge.jsonl) ────────────
def bridge_path() -> Path:
    """مسیرِ فایلِ پل در state ارگانیسمِ مرکزی."""
    return Path(config.OPS_STATE) / "saba-bridge.jsonl"


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ─── kinds مجاز (whitelist — هر چیزی خارج از این reject می‌شود) ───────────────
ALLOWED_KINDS = frozenset({
    "draft_submitted",   # صبا درفتی ثبت کرد
    "halt",              # صبا halt زد
    "resume",            # صبا resume زد
    "boundary",          # صبا محدوده را تنگ‌تر کرد
    "brain_tick_done",   # حلقه‌ی tick pf_os یک دور کامل کرد
    "notify",            # نوتیفِ عمومی از pf_os
    "kpi",               # ثبتِ KPI هفتگی
    "learning_observed", # نتیجه‌ای ثبت شد و مغز یاد گرفت
})


def _atomic_append(line: str) -> bool:
    """append یک خط به saba-bridge.jsonl (طبقِ الگوی opslib.append_jsonl)."""
    try:
        p = bridge_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        return True
    except OSError:
        return False


# ─── فیلترِ PII (defense-in-depth، حتی اگر caller اشتباه کند) ─────────────────
_PII_TERMS = (
    "ari", "saba", "anar", "amber", "yalda",
    "sydney", "stanhope", "mohebiazal", "armin",
    "tehran", "iran",
    "real name", "phone", "address",
)


def _scrub_summary(text: str) -> str:
    """حذفِ هر PII از summary قبل از نوشتن.宁可保守."""
    if not text:
        return ""
    t = str(text)
    tl = t.lower()
    for bad in _PII_TERMS:
        if bad in tl:
            return "[scrubbed]"
    # کپ طول
    return t.strip()[:200]


def publish(kind: str, summary: str = "", count: int = 0,
            extra: Optional[dict] = None) -> bool:
    """نوشتنِ یک event به saba-bridge.jsonl.

    args:
      kind: یکی از ALLOWED_KINDS. چیزِ دیگر reject می‌شود.
      summary: توضیحِ content-free (مثلاً "draft submitted by creator").
               PII می‌گیرد و scrub می‌کند (defense-in-depth).
      count: عددِ مرتبط (مثلاً تعداد درفت‌های pending). برای metric.
      extra: dict اختیاری با فیلدهای اضافه (هرگز PII).

    برمی‌گرداند True اگر نوشته شد.
    """
    if kind not in ALLOWED_KINDS:
        return False
    summary_clean = _scrub_summary(summary)
    record = {
        "ts": _now_iso(),
        "kind": kind,
        "text": summary_clean,
        "source": "pf_os",
        "count": int(count) if count else 0,
    }
    if isinstance(extra, dict):
        # فقط فیلدهای امن را قبول کن (هرگز محتوای raw)
        for k, v in extra.items():
            if k in ("tier", "tag", "platform", "status", "intent"):
                record[k] = str(v)[:40]
    line = json.dumps(record, ensure_ascii=False)
    return _atomic_append(line)


# ─── helpers برای رویدادهای رایج ─────────────────────────────────────────────

def notify_draft_submitted(draft_id: str = "", pending_count: int = 0) -> bool:
    """وقتی صبا درفتی ثبت کرد."""
    return publish("draft_submitted",
                   summary=f"draft submitted (id={draft_id})" if draft_id else "draft submitted",
                   count=pending_count)


def notify_halt() -> bool:
    return publish("halt", summary="creator halted")


def notify_resume() -> bool:
    return publish("resume", summary="creator resumed")


def notify_boundary(change_summary: str = "") -> bool:
    """تغییرِ محدوده — summary باید content-free باشد."""
    return publish("boundary", summary=change_summary or "boundary tightened")


def notify_brain_tick(tick_n: int, intent: str = "", source: str = "") -> bool:
    """پایانِ یک دورِ tick مغز."""
    return publish("brain_tick_done",
                   summary=f"tick {tick_n} completed",
                   count=tick_n,
                   extra={"intent": intent, "status": source} if intent or source else None)


def notify_kpi(week: str, gross_aud: float = 0, posts: int = 0) -> bool:
    """ثبتِ KPI هفتگی — همه content-free (عدد)."""
    return publish("kpi",
                   summary=f"kpi week {week}",
                   count=posts,
                   extra={"tag": week, "tier": f"{gross_aud:g}"})


def notify_learning_observed(tag: str = "", n_obs: int = 0) -> bool:
    """وقتی مغز از نتیجه یاد گرفت."""
    return publish("learning_observed",
                   summary=f"observation recorded (tag={tag})" if tag else "observation recorded",
                   count=n_obs)


# ─── snapshot برای /api/octopus/bridge ───────────────────────────────────────

def snapshot() -> dict:
    """وضعیتِ پل برای /api/octopus/bridge. content-free."""
    p = bridge_path()
    out = {
        "bridge_path": str(p),
        "exists": p.exists(),
        "writable": False,
        "size_bytes": 0,
        "lines_total": 0,
        "last_event": None,
    }
    try:
        if p.exists():
            out["writable"] = os.access(str(p), os.W_OK)
            out["size_bytes"] = p.stat().st_size
            # شمارشِ خط + آخرین event (content-free)
            with open(p, "r", encoding="utf-8") as f:
                last = None
                n = 0
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    n += 1
                    try:
                        rec = json.loads(line)
                        last = {"ts": rec.get("ts"), "kind": rec.get("kind"),
                                "count": rec.get("count", 0)}
                    except ValueError:
                        pass
                out["lines_total"] = n
                out["last_event"] = last
    except OSError:
        pass
    return out
