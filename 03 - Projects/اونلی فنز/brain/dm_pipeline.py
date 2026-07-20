#!/usr/bin/env python3
"""dm_pipeline.py — Project-F · صفِ DMِ HITL (Human-In-The-Loop).

**هدف:** AI فقط draft می‌زند؛ آری قبل از ارسال تأیید می‌کند؛ هیچ DM خودکار ارسال
نمی‌شود. این safety net #1 پلنِ لانچ (2026-07-16) است: خطرِ ban پلتفرم (OF ToS)
را به صفر می‌رساند چون هرگز autonomous chat نیست.

جریان:
    draft (AI/الگو) → pending_review → approve/reject (آری) →
    ready_for_manual_send (payload برای copy-paste دستی)

**مرزِ سخت:** هیچ متدِ send/dm/deliver وجود ندارد. این ماژول هرگز به Telegram/OF/
پلتفرم وصل نمی‌شود. خروجیِ نهایی = payload متنی که آری با دست copy-paste می‌کند.

content-free · صفر PII · stdlib-only · fail-closed (garded با همان banned-copy list
از acquisition_pipeline برای parity).
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
DEFAULT_STORE = _HERE / "dm_queue.json"

# audit ‏HITL (اختیاری — fail-soft)
try:
    from audit import audit_append
except ImportError:  # pragma: no cover
    audit_append = None  # type: ignore

# کانال‌هایی که DM رویشان می‌رود (پلتفرم‌های destination).
DM_CHANNELS = ("of", "fansly", "feetfinder", "reddit", "x")

# پاریته با acquisition_pipeline._BANNED_COPY — containment/rule #6/PII guard.
_BANNED_DM = (
    "اونلی", "onlyfans", "fansly", "صبا", "saba",
    "sydney", "سیدنی", "harbour", "harbor", "bondi", "nsw", "melbourne", "opera house",
    "persian", "iranian",
    # DM-specific: هرگز به بیرون از پلتفرم هدایت نکن (rule #3 — payment only in-platform).
    "paypal", "cashapp", "venmo", "bank transfer", "crypto", "bitcoin", "usdt",
    "wire", "zelle", "western union",
)
_FLAG = "(DM flagged: containment/rule#3/rule#6 — بازنویسی لازم)"

# نوع‌های DM (نقشِ پیام — برای categorize).
DM_KINDS = ("welcome", "followup", "ppv_offer", "winback", "custom_reply", "general")


def _now() -> float:
    return time.time()


class DmPipeline:
    """صفِ DMِ HITL. AI draft می‌زند، آری تأیید می‌کند، ارسال = دستی.

    **هیچ متدِ send/deliver/transmit وجود ندارد.** این فقط یک صف است که
    ``ready`` آیتم‌ها را برای copy-paste دستی آماده می‌کند."""

    def __init__(self, store_path: str | Path | None = None):
        self._store = Path(store_path) if store_path else DEFAULT_STORE
        self._lock = threading.RLock()   # 2026-07-20: هم‌زمانی امن
        self._items = self._load()

    # ── persistence (atomic از 2026-07-20؛ قبلاً write_text خام بود) ─────
    def _load(self) -> list:
        try:
            if self._store.exists():
                d = json.loads(self._store.read_text("utf-8"))
                return d if isinstance(d, list) else []
        except (OSError, ValueError):
            pass
        return []

    def _save(self) -> None:
        try:
            with self._lock:
                self._store.parent.mkdir(parents=True, exist_ok=True)
                tmp = self._store.with_suffix(".tmp")
                tmp.write_text(
                    json.dumps(self._items, ensure_ascii=False, indent=2),
                    encoding="utf-8")
                tmp.replace(self._store)
        except OSError:
            pass

    def _find(self, item_id: str):
        for i in self._items:
            if i.get("id") == item_id:
                return i
        return None

    # ── DM copy guard (rule #3 + #6 / containment / PII) ─────────────────
    @staticmethod
    def _copy_ok(text: str) -> bool:
        low = (text or "").lower()
        return not any(b in low for b in _BANNED_DM)

    @classmethod
    def _dm_clean(cls, body: str, subject: str = "") -> bool:
        """همهٔ فیلدهای خروجی باید از گارد رد شوند."""
        return cls._copy_ok(body) and cls._copy_ok(subject)

    # ── draft (AI/الگو → صفِ review) ─────────────────────────────────────
    def draft(self, channel: str, kind: str, body: str,
              subject: str = "", context_note: str = "",
              proposed_by: str = "ai") -> dict:
        """ساختنِ یک DM draft برای review آری.

        - channel: مقصد (of/fansly/...)
        - kind: نقشِ پیام (welcome/followup/...)
        - body: متنِ اصلیِ پیام
        - context_note: یادداشتِ محتوای‌آزاد برای آری (مثلاً «به fan X جواب بده»)

        خروجی: ``pending_review`` (نه ارسال). آری بعداً approve/reject می‌کند."""
        ch = channel.lower().strip() if channel else "of"
        if ch not in DM_CHANNELS:
            ch = "of"
        kd = kind.lower().strip() if kind else "general"
        if kd not in DM_KINDS:
            kd = "general"
        # dedup (2026-07-20): md5 روی متنِ *خام* body+channel — draft تکراریِ pending دوباره صف نمی‌شود
        key = hashlib.md5(
            f"{str(body).strip().lower()}|{ch}".encode("utf-8")).hexdigest()
        with self._lock:
            for i in self._items:
                if i.get("status") == "pending_review" and i.get("dedup") == key:
                    return {"ok": True, "id": i["id"], "status": "pending_review",
                            "flagged": bool(i.get("flagged")), "duplicate": True}
            flagged = not self._dm_clean(body, subject)
            item = {
                "id": "DM-" + uuid.uuid4().hex[:10],
                "status": "pending_review",
                "channel": ch,
                "kind": kd,
                "subject": (_FLAG if flagged else str(subject)[:120]),
                "body": (_FLAG if flagged else str(body)[:1000]),
                "context_note": str(context_note)[:200],   # یادداشتِ داخلی، هرگز ارسال نمی‌شود
                "flagged": flagged,
                "proposed_by": str(proposed_by)[:24],
                "created": _now(),
                "approved_by": None,
                "dedup": key,
                "sent_at": None,   # وقتی آری گفت «فرستادم» دستی ثبت می‌شود
            }
            self._items.append(item)
            self._save()
        return {"ok": True, "id": item["id"], "status": "pending_review",
                "flagged": flagged}

    # ── queries ──────────────────────────────────────────────────────────
    def pending(self) -> list:
        return [i for i in self._items if i.get("status") == "pending_review"]

    def ready(self) -> list:
        return [i for i in self._items if i.get("status") == "ready_for_manual_send"]

    def by_status(self, status: str) -> list:
        return [i for i in self._items if i.get("status") == status]

    # ── HITL one-tap: approve / reject ───────────────────────────────────
    def approve(self, item_id: str, actor: str = "operator") -> dict:
        """تأییدِ آری → payload آماده برای copy-paste دستی.

        **خاطر:** این متد هنوز چیزی *ارسال* نمی‌کند. فقط وضعیت را به
        ``ready_for_manual_send`` می‌برد و payload نهایی را برمی‌گرداند.
        آری بعد از ارسال دستی، ``mark_sent`` را صدا می‌زند تا آمار کامل شود."""
        it = self._find(item_id)
        if it is None:
            return {"ok": False, "error": "not found"}
        if it.get("flagged"):
            return {"ok": False, "error": "DM flagged (containment) — بازنویسی لازم پیش از approve"}
        if it.get("status") not in ("pending_review", "ready_for_manual_send"):
            return {"ok": False, "error": f"cannot approve from {it.get('status')}"}
        # belt-and-suspenders: گاردِ نهایی
        if not self._dm_clean(it.get("body", ""), it.get("subject", "")):
            it["status"] = "rejected"
            it["reject_reason"] = "containment at approve (fail-closed)"
            self._save()
            return {"ok": False, "error": "DM failed containment guard at approve (fail-closed)"}
        it["status"] = "ready_for_manual_send"
        it["approved_by"] = str(actor)[:24]
        it["approved_at"] = _now()
        self._save()
        if audit_append:
            audit_append("dm_approve", {"id": item_id, "actor": actor,
                                        "status": "ready_for_manual_send",
                                        "channel": it.get("channel", ""),
                                        "kind": it.get("kind", "")})
        return {"ok": True, "id": item_id, "status": "ready_for_manual_send",
                "payload": {"channel": it["channel"], "subject": it.get("subject", ""),
                            "body": it["body"]},
                "auto_sent": False,
                "note": "payload برای ارسالِ دستی. خودت copy-paste کن — این ماژول هیچ‌وقت ارسال نمی‌کند."}

    def reject(self, item_id: str, reason: str = "") -> dict:
        it = self._find(item_id)
        if it is None:
            return {"ok": False, "error": "not found"}
        it["status"] = "rejected"
        it["reject_reason"] = str(reason)[:120]
        self._save()
        return {"ok": True, "id": item_id, "status": "rejected"}

    def mark_sent(self, item_id: str) -> dict:
        """ثبتِ اینکه آری payload را دستی فرستاده. فقط برای آمار/گزارش."""
        it = self._find(item_id)
        if it is None:
            return {"ok": False, "error": "not found"}
        if it.get("status") != "ready_for_manual_send":
            return {"ok": False, "error": f"must be ready_for_manual_send (current: {it.get('status')})"}
        it["status"] = "sent"
        it["sent_at"] = _now()
        self._save()
        return {"ok": True, "id": item_id, "status": "sent"}

    # ── admin digest ─────────────────────────────────────────────────────
    def admin_digest(self) -> dict:
        return {
            "pending_review": len(self.pending()),
            "ready_for_manual_send": len(self.ready()),
            "sent": len(self.by_status("sent")),
            "rejected": len(self.by_status("rejected")),
            "flagged": len([i for i in self._items if i.get("flagged")]),
            "auto_send": False,   # همیشه False — این ماژول هرگز خودکار ارسال نمی‌کند
            "next": "review در تلگرام؛ ارسال = دستیِ آری پس از approve",
        }
