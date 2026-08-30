"""actuator.py — قلب اجرا / Motor Cortex.

معماری:
  • سه حالت: SHADOW → DRY_RUN → LIVE (هرگز بدون approval)
  • Action lifecycle: pending → approved → executing → completed / failed / rollback_ready
  • intent → approval → execution → result (correlation_id propagation)
  • persist به JSONL — stdlib-only
  • fail-closed: هیچ action بدون approval و audit trace

نقش در استعاره: قلب سوم اختاپوس — پمپ حیاتیٔ اجرا.
  - هر اندام (بازو) intent می‌دهد
  - مرکز (goal brain) approve/reject می‌کند
  - actuator اجرا می‌کند یا شبیه‌سازی
  - telemetry گزارش می‌دهد
"""
from __future__ import annotations

import json
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Optional, List


class ActuatorMode(Enum):
    SHADOW = "shadow"      # فقط log — هیچ execution واقعی
    DRY_RUN = "dry_run"    # simulate execution — check feasibility
    LIVE = "live"          # execution واقعی — نیازمند approval


class ActionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK_READY = "rollback_ready"


class Actuator:
    """Motor Cortex: intent → approval → execution → telemetry.

    Usage:
        act = Actuator(mode=ActuatorMode.DRY_RUN, persist_dir=Path("/tmp/act"))
        result = act.submit("post_draft", {"channel": "reddit", "text": "..."}, actor="ari")
        # result = {"action_id": "ACT-...", "status": "pending", "mode": "dry_run"}
        # سپس act.approve(action_id) یا act.reject(action_id)
    """

    def __init__(self, mode: ActuatorMode = ActuatorMode.SHADOW,
                 approval_callback: Optional[Callable[[str, dict, str], bool]] = None,
                 persist_dir: Optional[Path] = None,
                 on_execute: Optional[Callable[[str, dict, str], dict]] = None):
        self.mode = mode
        self._approval_fn = approval_callback
        self._persist_dir = Path(persist_dir) if persist_dir else None
        self._on_execute = on_execute  # تابع اجرا: (intent, payload, actor) -> result_dict
        self._actions: Dict[str, dict] = {}
        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._load()

    # ── submit (intent) ──────────────────────────────────────────────────────
    def submit(self, intent: str, payload: dict, actor: str = "system",
               correlation_id: Optional[str] = None,
               risk_tier: str = "GREEN") -> dict:
        """intent جدید ثبت می‌کند. برمی‌گرداند action_record."""
        action_id = f"ACT-{uuid.uuid4().hex[:12]}"
        cid = correlation_id or f"CID-{uuid.uuid4().hex[:12]}"
        record = {
            "action_id": action_id,
            "intent": intent,
            "payload": payload,
            "actor": actor,
            "mode": self.mode.value,
            "risk_tier": risk_tier.upper(),
            "correlation_id": cid,
            "status": ActionStatus.PENDING.value,
            "created_at": time.time(),
            "approved_at": None,
            "approved_by": None,
            "executed_at": None,
            "result": None,
            "error": None,
            "rollback_payload": None,
        }
        self._actions[action_id] = record
        self._save()

        # Auto-approve for GREEN in shadow/dry_run; LIVE always needs explicit
        if self.mode in (ActuatorMode.SHADOW, ActuatorMode.DRY_RUN) and risk_tier.upper() == "GREEN":
            return self._auto_approve_and_run(action_id)
        return {"ok": True, "action_id": action_id, "status": record["status"],
                "mode": self.mode.value, "correlation_id": cid,
                "note": "waiting for approval" if self.mode == ActuatorMode.LIVE else "auto-queued"}

    # ── approve / reject (gate) ────────────────────────────────────────────
    def approve(self, action_id: str, approver: str = "owner") -> dict:
        rec = self._actions.get(action_id)
        if not rec:
            return {"ok": False, "error": "action not found"}
        if rec["status"] != ActionStatus.PENDING.value:
            return {"ok": False, "error": f"already {rec['status']}"}
        if self.mode == ActuatorMode.LIVE and self._approval_fn:
            if not self._approval_fn(rec["intent"], rec["payload"], approver):
                rec["status"] = ActionStatus.DENIED.value
                rec["approved_by"] = approver
                rec["approved_at"] = time.time()
                self._save()
                return {"ok": False, "action_id": action_id, "status": "denied",
                        "reason": "approval_callback returned False"}
        rec["status"] = ActionStatus.APPROVED.value
        rec["approved_by"] = approver
        rec["approved_at"] = time.time()
        self._save()
        return self._run(action_id)

    def reject(self, action_id: str, reason: str = "",
               approver: str = "owner") -> dict:
        rec = self._actions.get(action_id)
        if not rec:
            return {"ok": False, "error": "action not found"}
        rec["status"] = ActionStatus.DENIED.value
        rec["approved_by"] = approver
        rec["approved_at"] = time.time()
        rec["error"] = reason or "rejected"
        self._save()
        return {"ok": True, "action_id": action_id, "status": "denied"}

    def rollback(self, action_id: str) -> dict:
        """اگر rollback_payload موجود باشد، intent rollback را ثبت و اجرا می‌کند."""
        rec = self._actions.get(action_id)
        if not rec:
            return {"ok": False, "error": "action not found"}
        rb = rec.get("rollback_payload")
        if not rb:
            return {"ok": False, "error": "no rollback payload recorded"}
        # submit new rollback action
        rb_result = self.submit(
            intent=f"rollback:{rec['intent']}",
            payload=rb,
            actor="system",
            correlation_id=rec.get("correlation_id"),
            risk_tier=rec.get("risk_tier", "GREEN"),
        )
        rec["status"] = ActionStatus.ROLLBACK_READY.value
        self._save()
        return {"ok": True, "action_id": action_id, "rollback_action_id": rb_result["action_id"],
                "status": "rollback_ready"}

    # ── query ──────────────────────────────────────────────────────────────────
    def get(self, action_id: str) -> Optional[dict]:
        return dict(self._actions.get(action_id, {})) if action_id in self._actions else None

    def list_by_status(self, status: Optional[str] = None,
                       since: Optional[float] = None) -> List[dict]:
        out = []
        for rec in self._actions.values():
            if status and rec["status"] != status:
                continue
            if since and rec.get("created_at", 0) < since:
                continue
            out.append(dict(rec))
        return sorted(out, key=lambda x: x.get("created_at", 0), reverse=True)

    # ── internal execution ───────────────────────────────────────────────────
    def _auto_approve_and_run(self, action_id: str) -> dict:
        rec = self._actions[action_id]
        rec["status"] = ActionStatus.APPROVED.value
        rec["approved_by"] = "auto"
        rec["approved_at"] = time.time()
        self._save()
        return self._run(action_id)

    def _run(self, action_id: str) -> dict:
        rec = self._actions[action_id]
        rec["status"] = ActionStatus.EXECUTING.value
        rec["executed_at"] = time.time()
        self._save()

        if self.mode == ActuatorMode.SHADOW:
            result = {"executed": False, "mode": "shadow", "reason": "logged only"}
            rec["status"] = ActionStatus.COMPLETED.value
            rec["result"] = result
            self._save()
            return {"ok": True, "action_id": action_id, "mode": "shadow", "result": result}

        if self.mode == ActuatorMode.DRY_RUN:
            # feasibility check: simulate without side-effects
            feasibility = self._simulate(rec["intent"], rec["payload"])
            result = {"executed": False, "mode": "dry_run", "feasible": feasibility,
                      "reason": "simulated — no real side-effect"}
            rec["status"] = ActionStatus.COMPLETED.value
            rec["result"] = result
            self._save()
            return {"ok": True, "action_id": action_id, "mode": "dry_run", "result": result}

        if self.mode == ActuatorMode.LIVE:
            try:
                if self._on_execute:
                    exec_result = self._on_execute(rec["intent"], rec["payload"], rec["actor"])
                else:
                    exec_result = {"executed": False, "reason": "no on_execute handler bound"}
                rec["result"] = exec_result
                rec["status"] = ActionStatus.COMPLETED.value
                self._save()
                return {"ok": True, "action_id": action_id, "mode": "live", "result": exec_result}
            except Exception as e:
                rec["status"] = ActionStatus.FAILED.value
                rec["error"] = str(e)
                self._save()
                return {"ok": False, "action_id": action_id, "mode": "live", "error": str(e)}

        return {"ok": False, "action_id": action_id, "error": "unknown mode"}

    def _simulate(self, intent: str, payload: dict) -> bool:
        """dry-run feasibility check: intent شناخته‌شده و payload valid؟"""
        known = {"post_draft", "send_dm", "publish_content", "update_price",
                 "start_campaign", "stop_campaign", "test_connection", "rollback"}
        if intent not in known:
            return False
        if not isinstance(payload, dict):
            return False
        return True

    # ── persistence ──────────────────────────────────────────────────────────
    def _save(self) -> None:
        if not self._persist_dir:
            return
        path = self._persist_dir / "actions.jsonl"
        try:
            with open(path, "w", encoding="utf-8") as f:
                for rec in self._actions.values():
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _load(self) -> None:
        path = self._persist_dir / "actions.jsonl"
        if not path.exists():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        self._actions[rec["action_id"]] = rec
                    except (json.JSONDecodeError, KeyError):
                        continue
        except OSError:
            pass
