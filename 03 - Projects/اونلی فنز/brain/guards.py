#!/usr/bin/env python3
"""guards.py — Project-F · safety-net state stores برای لانچِ gated.

دو لایهٔ fail-closed که جلوی خرابیِ زودهنگام را می‌گیرند (پلن لانچ 2026-07-16):

  1. ``WarmupGuard`` — تا وقتی Reddit karma از آستانهٔ مشخصی نرسیده، هیچ آیتمی که
     «فروش» است (شاملِ link/PPV/paywall) نباید finalize شود. دلیل: آکانتِ تازه +
     لینکِ فروش = shadowban در <۷۲ ساعت (تأییدِ P3 reddit-engine).

  2. ``ChannelLocks`` — kill-switch اتوماتیک: هر warning پلتفرمی یک کانال را قفل
     می‌کند تا پاک‌سازی دستی؛ دو warning در یک کانال = کلِ قیف stop تا verdict.
     این همان «platform-warning kill-switch» ای است که PROMPT-NEXT-AGENT خواست ولی
     تا حالا سیم‌نشده بود.

هر دو stores: JSON file-based (restart-safe) · fail-closed (فایل خراب = محتاطانه‌ترین
حالت) · صفر PII · صفر اکشنِ بیرونی · stdlib-only.

نکتهٔ مهم: این ماژول **هیچ‌چیز را خودکار پست/مسدود نمی‌کند**. فقط state نگه
می‌دارد و پاسخِ yes/no می‌دهد. تصمیم‌گیرنده = pipeline.finalize() و langar.handle().
"""
from __future__ import annotations

import json
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent           # brain/
_PROJECT_ROOT = _HERE.parent                       # Project-F/
DEFAULT_GUARDS_DIR = _PROJECT_ROOT / "langar"      # کنارِ langar_log/cost_meter

# آستانهٔ پیش‌فرضِ کارما برای بازشدنِ warm-up guard (قابل‌بازنویسی با config).
DEFAULT_KARMA_THRESHOLD = 20

# کانال‌هایی که warm-up guard رویشان فعال است (X/OF نیازی به کارما ندارند، ولی
# تا G1 باز گذاشته می‌شوند — جدول جدا).
WARMUP_CHANNELS = ("reddit",)

# عباراتِ «فروش» — اگه در hook/caption/tag باشد، آیتم فروشی محسوب می‌شود.
# content-free: کلماتِ عامِ فروش، نه هویت/پلتفرم.
_SALE_MARKERS = (
    "link in bio", "bio link", "onlyfans", "fansly", "feetfinder", "linktr",
    "allmylinks", "subscribe", "ppv", "unlock", "tip menu", "custom request",
    "$5", "$10", "$15", "$8", "buy", "purchase", "pay", "premium",
    "DM me", "message me for", "slide into",
)


def _now() -> float:
    return time.time()


def _load_json(path: Path, default):
    """fail-soft loader — فایل غایب/خراب = default."""
    try:
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            return d if isinstance(d, type(default)) else default
    except (json.JSONDecodeError, OSError):
        pass
    return default


def _save_json(path: Path, data) -> None:
    """atomic write — fail-soft (هرگز crash ندهد)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


class WarmupGuard:
    """نگهبانِ warm-up: جلوی finalizeِ آیتمِ فروشی تا رسیدنِ کارما به آستانه.

    State در ``reddit_state.json`` نگه‌داری می‌شود:
      {"reddit_karma": 0, "updated_at": ..., "history": [...], "threshold_met": false}

    fail-closed: اگه state خوانده نشود، آستانه محقق‌نشده فرض می‌شود (deny)."""

    def __init__(self, state_path: str | Path | None = None,
                 karma_threshold: int = DEFAULT_KARMA_THRESHOLD):
        self._path = Path(state_path) if state_path else (DEFAULT_GUARDS_DIR / "reddit_state.json")
        self._threshold = max(1, int(karma_threshold))

    def _state(self) -> dict:
        return _load_json(self._path, {
            "reddit_karma": 0,
            "updated_at": None,
            "threshold_met": False,
            "history": [],
        })

    def _save(self, state: dict) -> None:
        _save_json(self._path, state)

    def get_karma(self) -> int:
        """کارمای ثبت‌شده (۰ اگه هیچ)."""
        return int(self._state().get("reddit_karma", 0))

    def threshold(self) -> int:
        return self._threshold

    def threshold_met(self) -> bool:
        """True اگه کارما به آستانه رسیده باشد (cache از state)."""
        s = self._state()
        # هم از مقدارِ زنده و هم از flag استفاده کن (defensive).
        return bool(s.get("reddit_karma", 0) >= self._threshold
                    or s.get("threshold_met") is True)

    def set_karma(self, karma: int, note: str = "") -> dict:
        """ثبتِ کارمای دستی (آری هر جمعه از داشبورد می‌خواند)."""
        karma = max(0, int(karma))
        s = self._state()
        history = list(s.get("history", []))
        history.append({"karma": karma, "ts": _now(), "note": note[:80]})
        # فقط ۲۰ آخر را نگه دار (جلوگیری از رشد).
        history = history[-20:]
        s["reddit_karma"] = karma
        s["threshold_met"] = karma >= self._threshold
        s["updated_at"] = _now()
        s["history"] = history
        self._save(s)
        return {"ok": True, "karma": karma, "threshold_met": s["threshold_met"]}

    # ── guards/gates ─────────────────────────────────────────────────────
    @staticmethod
    def is_sale_item(hook: str = "", caption: str = "", tag: str = "") -> bool:
        """آیا این آیتم حاوی نشانهٔ فروش است؟ (content-free heuristic)."""
        blob = f"{hook} {caption} {tag}".lower()
        return any(m.lower() in blob for m in _SALE_MARKERS)

    def link_allowed(self, channel: str, hook: str = "", caption: str = "", tag: str = "") -> tuple[bool, str]:
        """آیا finalize این آیتم مجاز است؟

        بازگشتی: (allowed, reason). ``allowed=False`` یعنی fail-closed.
        - کانالِ غیر-WARMUP → همیشه مجاز (X/OF خودشان warm-up جدا دارند).
        - کانالِ WARMUP + آیتمِ غیرفروشی → مجاز (SFW posts برای کارما‌سازی OK).
        - کانالِ WARMUP + آیتمِ فروشی + کارما<آستانه → **deny** (fail-closed).
        - کانالِ WARMUP + آیتمِ فروشی + کارما≥آستانه → مجاز.
        """
        if channel not in WARMUP_CHANNELS:
            return True, "channel not under warm-up guard"
        if not self.is_sale_item(hook, caption, tag):
            return True, "non-sale item — warm-up safe"
        if self.threshold_met():
            return True, f"karma threshold met ({self.get_karma()}/{self._threshold})"
        return False, (f"warm-up guard: sale item on {channel} blocked — "
                       f"karma {self.get_karma()}/{self._threshold} "
                       f"(post SFW content first to build karma)")


class ChannelLocks:
    """kill-switch اتوماتیک per-channel. هر warning یک کانال را lock می‌کند.

    State در ``channel_locks.json``:
      {"channels": {"reddit": {"warnings": [...], "locked": true, "locked_until": null}}, ...}

    قاعده:
      - ۱ warning → کانال lock تا ``/clear_warning <channel>`` دستی.
      - ≥۲ warning → کانال lock + ``full_stop=True`` (کلِ قیف stop تا verdict آری).

    fail-closed: فایل خراب → فرض می‌کنیم همه‌چیز locked است."""

    MAX_WARNINGS_BEFORE_FULL_STOP = 2

    def __init__(self, state_path: str | Path | None = None):
        self._path = Path(state_path) if state_path else (DEFAULT_GUARDS_DIR / "channel_locks.json")

    def _state(self) -> dict:
        default = {"channels": {}, "full_stop": False, "full_stop_reason": "", "updated_at": None}
        s = _load_json(self._path, default)
        # اگه فایل خراب بود و dict برگشت ولی کلیدها غایب بود، کامل کن.
        s.setdefault("channels", {})
        s.setdefault("full_stop", False)
        s.setdefault("full_stop_reason", "")
        s.setdefault("updated_at", None)
        return s

    def _save(self, state: dict) -> None:
        state["updated_at"] = _now()
        _save_json(self._path, state)

    def _chan(self, state: dict, channel: str) -> dict:
        ch = channel.lower().strip()
        if ch not in state["channels"]:
            state["channels"][ch] = {"warnings": [], "locked": False, "locked_until": None}
        return state["channels"][ch]

    def report_warning(self, channel: str, reason: str = "", severity: str = "warning") -> dict:
        """ثبتِ یک warning پلتفرمی. channel را lock می‌کند و شاید full_stop."""
        ch = channel.lower().strip()
        s = self._state()
        c = self._chan(s, ch)
        entry = {"ts": _now(), "reason": reason[:160], "severity": severity[:24]}
        c["warnings"].append(entry)
        c["locked"] = True
        c["locked_until"] = None   # تا clear دستی
        # ≥۲ warning در یک کانال → full_stop کلِ قیف
        if len(c["warnings"]) >= self.MAX_WARNINGS_BEFORE_FULL_STOP:
            s["full_stop"] = True
            s["full_stop_reason"] = (f"channel '{ch}' hit "
                                     f"{len(c['warnings'])} warnings — operator verdict required")
        self._save(s)
        return {
            "ok": True, "channel": ch,
            "warning_count": len(c["warnings"]),
            "locked": True,
            "full_stop": s["full_stop"],
        }

    def clear_warning(self, channel: str) -> dict:
        """باز کردنِ lock یک کانال (فقط اگه full_stop نباشد)."""
        ch = channel.lower().strip()
        s = self._state()
        if s.get("full_stop"):
            return {"ok": False, "error": "full_stop active — operator must /clear_full_stop"}
        c = s["channels"].get(ch)
        if not c:
            return {"ok": False, "error": f"channel '{ch}' has no warnings"}
        c["locked"] = False
        self._save(s)
        return {"ok": True, "channel": ch, "cleared": True}

    def clear_full_stop(self) -> dict:
        """باز کردنِ full_stop — فقط با verdict صریح اپراتور. همهٔ lockها پاک می‌شوند."""
        s = self._state()
        s["full_stop"] = False
        s["full_stop_reason"] = ""
        for ch, c in s["channels"].items():
            c["locked"] = False
        self._save(s)
        return {"ok": True, "cleared_all": True}

    def channel_locked(self, channel: str) -> bool:
        """آیا کانال locked است؟ (fail-closed اگه full_stop)."""
        s = self._state()
        if s.get("full_stop"):
            return True
        ch = channel.lower().strip()
        c = s["channels"].get(ch)
        return bool(c and c.get("locked"))

    def full_stop_active(self) -> bool:
        return bool(self._state().get("full_stop"))

    def snapshot(self) -> dict:
        """خلاصه برای UI — صفر PII، فقط counts/status."""
        s = self._state()
        chans = {}
        for ch, c in s["channels"].items():
            chans[ch] = {
                "warnings": len(c.get("warnings", [])),
                "locked": bool(c.get("locked")),
                "last_reason": (c.get("warnings", [{}])[-1].get("reason", "") if c.get("warnings") else ""),
            }
        return {
            "full_stop": s.get("full_stop", False),
            "full_stop_reason": s.get("full_stop_reason", ""),
            "channels": chans,
            "updated_at": s.get("updated_at"),
        }


# ── ترکیب: یک تابع کمکی برای pipeline.finalize() ──────────────────────────
def check_all_guards(channel: str, hook: str = "", caption: str = "", tag: str = "",
                     warmup: WarmupGuard | None = None,
                     locks: ChannelLocks | None = None) -> tuple[bool, str]:
    """بررسیِ همهٔ guardها برای یک finalize. بازگشتی: (allowed, reason).

    ترتیب (fail-closed در هر مرحله):
      1. full_stop فعال؟ → deny
      2. کانال locked؟ → deny
      3. warm-up guard → deny اگه فروشی و کارما کم
    """
    if locks is not None:
        if locks.full_stop_active():
            return False, f"full_stop active: {locks.snapshot().get('full_stop_reason', 'operator verdict required')}"
        if locks.channel_locked(channel):
            return False, f"channel '{channel}' locked — /clear_warning {channel} to resume"
    if warmup is not None:
        ok, reason = warmup.link_allowed(channel, hook, caption, tag)
        if not ok:
            return False, reason
    return True, "ok"
