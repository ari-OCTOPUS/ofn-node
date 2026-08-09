#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""approval_queue_unified.py — صفِ یکپارچهٔ تأییدِ انسانی (HITL) برای OCTOPUS.

⚠️ **DEPRECATED (۲۰۲۶-۰۸-۰۹، رأیِ مالک طبقِ مگاپرامپتِ تناقضات، آیتمِ ب-۱۱).**
retire رسمی: `approval_channel.py` (۴۹۱۷ خط) صفِ تأییدِ واقعیِ زندهٔ باتِ تلگرام
است و کافی است. این فایل کدِ زنده‌ای نمی‌شکند و import نمی‌شود؛ فقط دیگر
هدفِ توسعهٔ تازه نیست — اگر قابلیتِ نویی لازم شد، به approval_channel.py اضافه
شود، نه این‌جا.

⚠️ وضعیتِ واقعی (بازبینی ۲۰۲۶-۰۸-۰۷، grep کاملِ repo): این ماژول **ساخته شده
ولی به مسیرِ خواندنِ باتِ زندهٔ تلگرام سیم‌کشی نشده**. refresh()/main() صفر
صداکننده دارند. حتی اگر دستی صدا زده شوند، سمتِ _ops همیشه خالی برمی‌گردد چون
register_ops_pending()/register_4d_proposal() هم صفر صداکننده دارند و
pending_snapshot.json / rfc_snapshot.json روی دیسک اصلاً وجود ندارند —
approval_channel.py هرگز این helperهای static را صدا نمی‌زند.

منبعِ واقعیِ صفِ تأییدِ باتِ زندهٔ تلگرام (center.py، callbackهای ap:ok:<id> /
ap:no:<id>) این فایل نیست. بات از اینجا می‌خواند:
  _octopus/state/approvals.json — از راهِ _ops/telegram_center/approval_store.py
  (در center.py با نامِ aps_mod import می‌شود؛ ر.ک. load_pending()/approve()/reject()).
اسکیما و مسیرِ approval_store کاملاً جدا از UnifiedQueueItem/UNIFIED_QUEUE_PATH
همین ماژول است — یکی نیستند، اشتباه نگیرید.

تنها مصرف‌کنندهٔ واقعیِ unified-approval-queue.json (که خودش هم هرگز به‌روز
نمی‌شود چون refresh() صدا زده نمی‌شود):
  nervous-system/extract_queue_data.py → queue-data.js → OCTOPUS/admin-telegram
  (پنلِ Queue در داشبوردِ cockpit — نه alert/inline-keyboard باتِ تلگرام)، و آن
  هم فقط با اجرای دستیِ refresh-live-data.bat، نه روی هیچ cadence/beat خودکار.

طراحیِ اصلیِ ماژول (هدف، هنوز محقق نشده): یکپارچه‌سازیِ دو صفِ مجزا در یک API:
  ۱. صفِ _ops (approval_channel.py) — تأییدهای پولی/عملیاتی با EffectorGate
  ۲. صفِ 4d_system (self_code.py) — پیشنهادهای تغییرِ کد

TINV-7: هیچ اثرِ برگشت‌ناپذیری بدونِ appendِ قبلی settle نمی‌شود.
EffectorGate همچنان تنها گلوگاهِ settlement است.

$0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# ─── bootstrap مسیر برای opslib ─────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402

logger = logging.getLogger(__name__)

# ─── مسیرها ──────────────────────────────────────────────────────────────
UNIFIED_QUEUE_PATH = opslib.STATE_DIR / "unified-approval-queue.json"
OPS_APPROVALS_DIR = opslib.STATE_DIR / "telegram" / "approvals"
OPS_APPROVALS_JSONL = OPS_APPROVALS_DIR / "approvals.jsonl"
OPS_PENDING_SNAPSHOT = OPS_APPROVALS_DIR / "pending_snapshot.json"

# مسیرِ 4d_system برای import
FD_ROOT = Path(__file__).resolve().parent.parent.parent / "4d_system"

# ─── ثابت‌ها ─────────────────────────────────────────────────────────────
VALID_STATUSES = frozenset({"pending", "approved", "denied", "settled", "rejected"})
HIGH_PRIORITY_TYPES = frozenset({"money", "security", "critical"})


def _import_4d_brain():
    """import brain.self_code از 4d_system با handlingِ shadowing توسطِ _ops.brain.

    _ops/brain/__init__.py وجود دارد → اگر _ops در sys.path قبل از 4d_system باشد،
    import brain → _ops.brain (shadow). این helper کش را پاک می‌کند و 4d_system را
    به اولِ path می‌برد.
    """
    import sys
    # پاک کردنِ cacheِ brain (تا shadowِ _ops را دور بزند)
    for key in list(sys.modules.keys()):
        if key == "brain" or key.startswith("brain."):
            del sys.modules[key]
    fd_path = str(FD_ROOT)
    if fd_path in sys.path:
        sys.path.remove(fd_path)
    sys.path.insert(0, fd_path)
    import brain.self_code  # noqa: E402
    return brain.self_code


@dataclass
class UnifiedQueueItem:
    """یک آیتم در صفِ یکپارچهٔ تأیید.

    Fields:
        id: unique identifier (از source می‌آید)
        source: "_ops" | "4d_system"
        source_label: برچسبِ نمایشی (Farsi emoji)
        type: "money" | "code_change" | "rfc" | "operational"
        status: "pending" | "approved" | "denied" | "settled"
        summary: توضیحِ کوتاه
        detail: جزئیاتِ تکمیلی
        amount_aud: مبلغ به AUD (برای money items)
        priority: "high" | "medium" | "low"
        created_at: ISO timestamp
        effect_id: EffectorGate effect_id (برای _ops items)
        risk_level: R1..R4
        actions: dict of action_name → callback_data pattern
        gate_status: وضعیتِ authoritative از EffectorGate
    """
    id: str
    source: str
    source_label: str
    type: str
    status: str
    summary: str
    detail: str = ""
    amount_aud: float = 0.0
    priority: str = "medium"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    effect_id: str | None = None
    risk_level: str = "R2"
    actions: dict[str, str] = field(default_factory=dict)
    gate_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> UnifiedQueueItem:
        allowed = cls.__dataclass_fields__
        return cls(**{k: v for k, v in d.items() if k in allowed})


class UnifiedApprovalQueue:
    """صفِ یکپارچهٔ تأیید. دو منبع (_ops + 4d_system) را در یک registry merge می‌کند.

    Usage:
        queue = UnifiedApprovalQueue()
        queue.refresh()  # pull از هر دو منبع
        pending = queue.list_items(status="pending")
        queue.save()     # snapshot به JSON
    """

    def __init__(
        self,
        state_path: Path | str | None = None,
        effect_status_fn: Callable[[str], str | None] | None = None,
    ):
        self.state_path = Path(state_path) if state_path else UNIFIED_QUEUE_PATH
        self._effect_status_fn = effect_status_fn
        self._items: list[UnifiedQueueItem] = []
        self._load()

    # ═══════════════════════════════════════════════════════════════════
    # persistence
    # ═══════════════════════════════════════════════════════════════════

    def _load(self) -> None:
        """بارگذاری از JSON. اگر نباشد → [] (fail-soft)."""
        if not self.state_path.exists():
            self._items = []
            return
        try:
            raw = json.loads(self.state_path.read_text("utf-8"))
            self._items = [
                UnifiedQueueItem.from_dict(i)
                for i in raw.get("items", [])
            ]
            logger.info(
                "UnifiedQueue loaded %d items from %s",
                len(self._items), self.state_path,
            )
        except Exception as exc:  # noqa: BLE001 — fail-soft
            logger.warning("UnifiedQueue load failed: %s", exc)
            self._items = []

    def save(self) -> None:
        """ذخیره به JSON با atomic write (tmp + replace)."""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "generated": datetime.now(timezone.utc).isoformat(),
                "items": [i.to_dict() for i in self._items],
                "counts": self._counts(),
            }
            tmp = self.state_path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp, self.state_path)
            logger.info(
                "UnifiedQueue saved %d items to %s",
                len(self._items), self.state_path,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("UnifiedQueue save failed: %s", exc)
            try:
                opslib.alert(["UnifiedQueue save failed: " + str(exc)])
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════════
    # counts & queries
    # ═══════════════════════════════════════════════════════════════════

    def _counts(self) -> dict[str, Any]:
        pending = [i for i in self._items if i.status == "pending"]
        return {
            "total": len(self._items),
            "pending": len(pending),
            "by_source": self._group_count("source"),
            "by_type": self._group_count("type"),
            "by_status": self._group_count("status"),
            "by_priority": self._group_count("priority"),
            "high_priority": len(
                [i for i in pending if i.priority == "high"]
            ),
            "money_at_risk": sum(
                i.amount_aud for i in pending if i.type == "money"
            ),
        }

    def _group_count(self, key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self._items:
            val = getattr(item, key, "unknown")
            out[val] = out.get(val, 0) + 1
        return out

    def list_items(
        self,
        status: str | None = None,
        source: str | None = None,
        type_: str | None = None,
    ) -> list[UnifiedQueueItem]:
        out = self._items
        if status:
            out = [i for i in out if i.status == status]
        if source:
            out = [i for i in out if i.source == source]
        if type_:
            out = [i for i in out if i.type == type_]
        return list(out)

    def get_item(self, item_id: str) -> UnifiedQueueItem | None:
        for i in self._items:
            if i.id == item_id:
                return i
        return None

    def add_item(self, item: UnifiedQueueItem) -> None:
        if not isinstance(item, UnifiedQueueItem):
            raise TypeError("item must be UnifiedQueueItem")
        self._items.append(item)
        self.save()

    def update_status(self, item_id: str, status: str) -> bool:
        if status not in VALID_STATUSES:
            raise ValueError(f"invalid status: {status}")
        for i in self._items:
            if i.id == item_id:
                i.status = status
                self.save()
                return True
        return False

    def remove_item(self, item_id: str) -> bool:
        orig = len(self._items)
        self._items = [i for i in self._items if i.id != item_id]
        if len(self._items) < orig:
            self.save()
            return True
        return False

    def clear_settled(self, max_age_days: int = 7) -> int:
        """settled/approved/denied items older than max_age_days را حذف می‌کند."""
        now = datetime.now(timezone.utc)
        kept: list[UnifiedQueueItem] = []
        removed = 0
        for i in self._items:
            if i.status in ("settled", "approved", "denied"):
                try:
                    dt = datetime.fromisoformat(i.created_at)
                    if (now - dt).days > max_age_days:
                        removed += 1
                        continue
                except Exception:  # noqa: BLE001
                    pass
            kept.append(i)
        self._items = kept
        if removed:
            self.save()
        return removed

    # ═══════════════════════════════════════════════════════════════════
    # refresh from sources
    # ═══════════════════════════════════════════════════════════════════

    def refresh(self) -> dict[str, Any]:
        """از هر دو منبع می‌خواند، merge می‌کند، reconcile می‌کند، save می‌زند.

        Returns:
            dict with before/after counts and pull results.
        """
        before = len(self._items)
        fd_items = self._pull_4d_system()
        ops_items = self._pull_ops()

        self._merge_items(fd_items + ops_items)
        self._reconcile_gate_status()
        self._reconcile_approvals_jsonl()

        self.save()
        return {
            "before": before,
            "after": len(self._items),
            "pulled_4d": len(fd_items),
            "pulled_ops": len(ops_items),
            "counts": self._counts(),
        }

    def _merge_items(self, new_items: list[UnifiedQueueItem]) -> None:
        existing_ids = {i.id for i in self._items}
        for ni in new_items:
            if ni.id not in existing_ids:
                self._items.append(ni)
                existing_ids.add(ni.id)
            else:
                for ei in self._items:
                    if ei.id == ni.id and ei.status != ni.status:
                        ei.status = ni.status

    def _reconcile_gate_status(self) -> None:
        """اگر effect_status_fn داریم، وضعیتِ gate را روی آیتم‌های _ops apply می‌کنیم.

        Cockpit v2 pattern: effect_status_fn = gate.status_of (authoritative).
        pending در gate → pending در queue
        releasable/settled در gate → approved در queue
        refused در gate → denied در queue
        """
        if self._effect_status_fn is None:
            return
        for i in self._items:
            if i.effect_id and i.source == "_ops":
                try:
                    gs = self._effect_status_fn(i.effect_id)
                    if gs:
                        i.gate_status = gs
                        if gs in ("settled", "releasable") and i.status == "pending":
                            i.status = "approved"
                        elif gs == "refused" and i.status == "pending":
                            i.status = "denied"
                except Exception:  # noqa: BLE001 — fail-soft
                    pass

    def _reconcile_approvals_jsonl(self) -> None:
        """approvals.jsonl را می‌خواند و آیتم‌های تأییدشده را updated می‌کند."""
        if not OPS_APPROVALS_JSONL.exists():
            return
        try:
            lines = OPS_APPROVALS_JSONL.read_text("utf-8").splitlines()
            for line in lines:
                if not line.strip():
                    continue
                rec = json.loads(line)
                eid = rec.get("id", "")
                verdict = rec.get("verdict", "")
                if not eid:
                    continue
                for i in self._items:
                    if i.id == eid and i.status == "pending":
                        if verdict == "ok":
                            i.status = "approved"
                        else:
                            i.status = "denied"
        except Exception as exc:  # noqa: BLE001
            logger.debug("reconcile approvals.jsonl failed: %s", exc)

    # ═══════════════════════════════════════════════════════════════════
    # pull from 4d_system (self_code)
    # ═══════════════════════════════════════════════════════════════════

    def _pull_4d_system(self) -> list[UnifiedQueueItem]:
        """pull از self_code.list_pending(). اگر import نشد → []."""
        try:
            self_code = _import_4d_brain()
            proposals = self_code.list_pending()
            items: list[UnifiedQueueItem] = []
            for p in proposals:
                pid = p.get("id", "")
                if not pid:
                    continue
                items.append(
                    UnifiedQueueItem(
                        id=f"4d-{pid}",
                        source="4d_system",
                        source_label="🌌 ایده‌یاب",
                        type="code_change",
                        status="pending",
                        summary=(p.get("rationale", "") or "")[:200],
                        detail=p.get("target", ""),
                        amount_aud=0.0,
                        priority="medium",
                        created_at=p.get(
                            "created_at",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        risk_level="R2",
                        actions={
                            "approve": f"self_code:approve:{pid}",
                            "reject": f"self_code:reject:{pid}",
                        },
                    )
                )
            return items
        except Exception as exc:  # noqa: BLE001
            logger.debug("pull_4d_system failed: %s", exc)
            return []

    # ═══════════════════════════════════════════════════════════════════
    # pull from _ops (approval_channel + approvals.jsonl)
    # ═══════════════════════════════════════════════════════════════════

    def _pull_ops(self) -> list[UnifiedQueueItem]:
        """pull از _ops: ابتدا pending_snapshot سپس approvals.jsonl."""
        items: list[UnifiedQueueItem] = []

        # ۱) pending_snapshot (اگر approval_channel آن را نوشته باشد)
        if OPS_PENDING_SNAPSHOT.exists():
            try:
                raw = json.loads(OPS_PENDING_SNAPSHOT.read_text("utf-8"))
                for eid, meta in raw.items():
                    items.append(
                        UnifiedQueueItem(
                            id=eid,
                            source="_ops",
                            source_label="🐙 ارگانیسم",
                            type="money"
                            if meta.get("amount_aud", 0) > 0
                            else "operational",
                            status=meta.get("status", "pending"),
                            summary=(meta.get("summary", "") or "")[:200],
                            detail=meta.get("guard", ""),
                            amount_aud=float(meta.get("amount_aud", 0)),
                            priority="high"
                            if meta.get("amount_aud", 0) > 0
                            else "medium",
                            created_at=meta.get(
                                "created_at",
                                datetime.now(timezone.utc).isoformat(),
                            ),
                            effect_id=eid,
                            risk_level="R3"
                            if meta.get("amount_aud", 0) > 0
                            else "R2",
                            actions={
                                "approve": f"app:approve:{eid}:<token>",
                                "reject": f"app:deny:{eid}:<token>",
                            },
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                logger.debug("pull_ops pending_snapshot failed: %s", exc)

        # ۲) RFCهای pending (اگر فایلِ snapshotِ RFC باشد)
        rfc_snapshot = OPS_APPROVALS_DIR / "rfc_snapshot.json"
        if rfc_snapshot.exists():
            try:
                raw = json.loads(rfc_snapshot.read_text("utf-8"))
                for rid, meta in raw.items():
                    items.append(
                        UnifiedQueueItem(
                            id=f"rfc-{rid}",
                            source="_ops",
                            source_label="🐙 ارگانیسم",
                            type="rfc",
                            status=meta.get("status", "pending"),
                            summary=(meta.get("summary", "") or "")[:200],
                            detail=meta.get("change_level", ""),
                            amount_aud=0.0,
                            priority="medium",
                            created_at=meta.get(
                                "created_at",
                                datetime.now(timezone.utc).isoformat(),
                            ),
                            risk_level="R2",
                            actions={
                                "approve": f"rfc:merge:{rid}:<token>",
                                "reject": f"rfc:deny:{rid}:<token>",
                            },
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                logger.debug("pull_ops rfc_snapshot failed: %s", exc)

        return items

    # ═══════════════════════════════════════════════════════════════════
    # delegate actions (approve / reject)
    # ═══════════════════════════════════════════════════════════════════

    def approve(self, item_id: str) -> dict[str, Any]:
        """Approve یک آیتم — delegate به sourceِ مناسب.

        برای _ops: فقط status را به approved تغییر می‌دهد (settle فقط از gate).
        برای 4d_system: self_code.approve() را صدا می‌زند.
        """
        item = self.get_item(item_id)
        if not item:
            return {"ok": False, "reason": "item not found"}
        if item.source == "4d_system":
            return self._approve_4d(item)
        if item.source == "_ops":
            return self._approve_ops(item)
        return {"ok": False, "reason": "unknown source"}

    def reject(self, item_id: str, note: str = "") -> dict[str, Any]:
        """Reject یک آیتم — delegate به sourceِ مناسب."""
        item = self.get_item(item_id)
        if not item:
            return {"ok": False, "reason": "item not found"}
        if item.source == "4d_system":
            return self._reject_4d(item, note)
        if item.source == "_ops":
            return self._reject_ops(item, note)
        return {"ok": False, "reason": "unknown source"}

    def _approve_4d(self, item: UnifiedQueueItem) -> dict[str, Any]:
        try:
            self_code = _import_4d_brain()
            pid = item.id.replace("4d-", "", 1)
            res = self_code.approve(pid)
            if res.get("ok"):
                item.status = "approved"
                self.save()
            return res
        except Exception as exc:  # noqa: BLE001
            logger.error("approve_4d failed: %s", exc)
            return {"ok": False, "reason": str(exc)}

    def _reject_4d(self, item: UnifiedQueueItem, note: str) -> dict[str, Any]:
        try:
            self_code = _import_4d_brain()
            pid = item.id.replace("4d-", "", 1)
            res = self_code.reject(pid, note)
            if res.get("ok"):
                item.status = "denied"
                self.save()
            return res
        except Exception as exc:  # noqa: BLE001
            logger.error("reject_4d failed: %s", exc)
            return {"ok": False, "reason": str(exc)}

    def _approve_ops(self, item: UnifiedQueueItem) -> dict[str, Any]:
        """برای _ops: فقط local status update (settle فقط از EffectorGate)."""
        item.status = "approved"
        self.save()
        return {
            "ok": True,
            "reason": (
                "marked approved in queue. "
                "Settle must go through EffectorGate (TINV-7)."
            ),
        }

    def _reject_ops(self, item: UnifiedQueueItem, note: str = "") -> dict[str, Any]:
        item.status = "denied"
        item.detail = (item.detail + "\nrejected: " + note).strip()
        self.save()
        return {"ok": True, "reason": "marked denied"}

    # ═══════════════════════════════════════════════════════════════════
    # static helpers for source systems to push items
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def register_ops_pending(
        effect_id: str,
        amount_aud: float,
        summary: str,
        guard_verdict: str = "",
        created_at: str = "",
    ) -> None:
        """Helper static: approval_channel.py می‌تواند pending item خود را اینجا register کند.

        Example:
            UnifiedApprovalQueue.register_ops_pending(
                effect_id="abc123",
                amount_aud=50.0,
                summary="تأییدِ publish",
            )
        """
        try:
            queue = UnifiedApprovalQueue()
            queue.add_item(
                UnifiedQueueItem(
                    id=effect_id,
                    source="_ops",
                    source_label="🐙 ارگانیسم",
                    type="money" if amount_aud > 0 else "operational",
                    status="pending",
                    summary=summary[:200],
                    detail=guard_verdict,
                    amount_aud=float(amount_aud),
                    priority="high" if amount_aud > 0 else "medium",
                    created_at=created_at
                    or datetime.now(timezone.utc).isoformat(),
                    effect_id=effect_id,
                    risk_level="R3" if amount_aud > 0 else "R2",
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("register_ops_pending failed: %s", exc)

    @staticmethod
    def register_4d_proposal(
        pid: str,
        target: str,
        rationale: str,
        created_at: str = "",
    ) -> None:
        """Helper static: self_code.py می‌تواند proposal خود را اینجا register کند."""
        try:
            queue = UnifiedApprovalQueue()
            queue.add_item(
                UnifiedQueueItem(
                    id=f"4d-{pid}",
                    source="4d_system",
                    source_label="🌌 ایده‌یاب",
                    type="code_change",
                    status="pending",
                    summary=(rationale or "")[:200],
                    detail=target,
                    amount_aud=0.0,
                    priority="medium",
                    created_at=created_at
                    or datetime.now(timezone.utc).isoformat(),
                    risk_level="R2",
                    actions={
                        "approve": f"self_code:approve:{pid}",
                        "reject": f"self_code:reject:{pid}",
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("register_4d_proposal failed: %s", exc)

    # ═══════════════════════════════════════════════════════════════════
    # export
    # ═══════════════════════════════════════════════════════════════════

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated": datetime.now(timezone.utc).isoformat(),
            "items": [i.to_dict() for i in self._items],
            "counts": self._counts(),
        }


# ═══════════════════════════════════════════════════════════════════════
# convenience functions & CLI
# ═══════════════════════════════════════════════════════════════════════

def refresh() -> dict[str, Any]:
    """تابعِ سطحِ بالا برای refresh از command line."""
    return UnifiedApprovalQueue().refresh()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    result = refresh()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
