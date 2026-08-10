#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime.py — AGI2027 control primitives (installed 2026-08-02, ZCode).

Fixed vs the dropped-in PowerShell runner:
  * installed under `_ops/agi2027_control/` — NOT `_octopus/`, which is a live
    infrastructure directory (config/, logs/, manifests/, state/) since 2026-07-18
    and must not gain an `__init__.py` / subpackage from this work.
  * FuguFootprint defaults to scanning `_ops/` only (the §0 megaprompt rule: never
    rglob from F:\\backup — 2 AV engines, 3-6ms/file, has hung the laptop). A
    full-drive scan requires an explicit `root=` opt-in.

stdlib-only, fail-soft. No network in __init__. ProjectFAdapter only calls out
when explicitly approved AND credentials are present (otherwise BLOCKED, no
fake-green). The OutboundWriteAheadLedger is the G-03 protection; it is NOT
auto-wired into live SMTP here — wiring is a NEEDS_OWNER_HOOK documented in the
report, so a "tests pass" verdict is honest about that.

UPDATED 2026-08-07 (redesign scan, phase 6/money): the "0 readers" claim above is
stale. This package is now imported by four production files — telegram_center/
center.py, telegram_center/miniapp_gateway.py, telegram_center/miniapp_state.py,
and legs/lead_outbound_transport.py (re-verified independently via grep on the
live tree this session) — following the miniapp gateway work landed 2026-08-06/07.
The original claim ("Nothing in this package is read by production paths today
... The flags are STAGED, not wired") described the state as of 2026-08-02 and no
longer reflects the live tree.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# Default scan root for footprint = _ops (the §0 rule). NOT the vault root.
DEFAULT_SCAN_ROOT = Path(__file__).resolve().parents[1]  # _ops/agi2027_control -> _ops


def now_ts() -> float:
    return time.time()


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuditLog:
    """fsync append-only audit log. Callers must not write secrets here."""
    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event = dict(event)
        event.setdefault("schema", "octopus.agi2027.audit.v1")
        event.setdefault("ts", now_ts())
        line = json.dumps(event, sort_keys=True, ensure_ascii=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        return event

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        out: List[Dict[str, Any]] = []
        for raw in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except json.JSONDecodeError:
                out.append({"schema": "octopus.agi2027.audit.corrupt_line", "raw": raw})
        return out


class IdempotencyStore:
    """SQLite WAL idempotency: same id+payload => DUPLICATE; same id+diff payload => CONFLICT."""
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # ۲۰۲۶-۰۸-۰۸: check_same_thread=False چون miniapp_gateway این کلاس را از
        # داخلِ _run_with_timeout (thread جدا) صدا می‌زند — بدونِ این ProgrammingError.
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS actions ("
            " action_id TEXT PRIMARY KEY,"
            " payload_hash TEXT NOT NULL,"
            " status TEXT NOT NULL,"
            " result_json TEXT,"
            " created_at REAL NOT NULL,"
            " updated_at REAL NOT NULL)"
        )
        self.conn.commit()

    def begin(self, action_id: str, payload: Any) -> Dict[str, Any]:
        if not action_id:
            return {"state": "BLOCKED", "reason": "missing_action_id"}
        h = stable_hash(payload)
        ts = now_ts()
        try:
            self.conn.execute(
                "INSERT INTO actions(action_id,payload_hash,status,result_json,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?)",
                (action_id, h, "RUNNING", None, ts, ts),
            )
            self.conn.commit()
            return {"state": "NEW", "payload_hash": h}
        except sqlite3.IntegrityError:
            row = self.conn.execute(
                "SELECT payload_hash,status,result_json FROM actions WHERE action_id=?",
                (action_id,),
            ).fetchone()
            if row is None:
                return {"state": "BLOCKED", "reason": "idempotency_row_missing"}
            old_hash, status, result_json = row
            if old_hash == h:
                # ⚠️ ۲۰۲۶-۰۸-۰۵ — ردیفِ مسمومِ RUNNING.
                #
                # `begin` ردیف را با status=RUNNING و result_json=NULL می‌سازد و
                # `settle` فقط **بعد از** اجرای موفق صدا زده می‌شود. اگر بینِ این
                # دو چیزی بترکد (ValueError روی ورودیِ کاربر، قفلِ sqlite، کشته‌شدنِ
                # پروسه) ردیف تا ابد RUNNING/NULL می‌ماند.
                #
                # قبلاً همین حالت DUPLICATE برمی‌گشت، و صداکننده‌ها DUPLICATE را
                # موفقیت می‌شمارند. نتیجه: کاری که **هرگز انجام نشد** برای همیشه
                # «قبلاً ثبت شده» گزارش می‌شد — و چون کلیدِ مینی‌اپ قطعی است، از
                # UI هیچ راهِ بازیابی نبود. راستی‌آزما این را روی یک پایگاهِ موقت
                # اندازه گرفت: صفر ردیفِ داده، صفر خطِ ممیزی، و ok:true.
                #
                # ردیفِ RUNNING با نتیجهٔ تهی **شاهدِ نرسیدن** است، نه شاهدِ تکرار.
                # «تمام‌شده» یعنی یک **تصمیم** گرفته شده — APPLIED/DONE (انجام شد)
                # یا BLOCKED/DENIED (رد شد). این‌ها واقعاً تکراری‌اند.
                # ولی RUNNING ِ بی‌نتیجه (کسی وسطِ کار مرد) و ERROR (تلاش
                # ترکید) هیچ‌کدام تصمیم نیستند؛ تکرارشان باید **دوباره اجرا**
                # شود. اگر شکست قطعی باشد، دوباره همان خطا را می‌گیرد — که
                # از «قبلاً ثبت شده»ی دروغین بی‌نهایت بهتر است.
                if (status == "RUNNING" and not result_json) or status == "ERROR":
                    return {"state": "RETRY", "payload_hash": h, "status": status,
                            "reason": ("previous_attempt_never_settled"
                                       if status == "RUNNING" else "previous_attempt_errored")}
                return {"state": "DUPLICATE", "payload_hash": h, "status": status,
                        "result": json.loads(result_json) if result_json else None}
            return {"state": "CONFLICT", "payload_hash": h, "existing_hash": old_hash, "status": status}

    def settle(self, action_id: str, status: str, result: Any) -> None:
        self.conn.execute(
            "UPDATE actions SET status=?, result_json=?, updated_at=? WHERE action_id=?",
            (status, json.dumps(result, sort_keys=True, ensure_ascii=False), now_ts(), action_id),
        )
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:  # noqa: BLE001
            pass


class PolicyGate:
    """Fail-closed policy gate."""
    forbidden_kinds = {"shell", "freeform_code_exec", "unknown_payload", "unbounded_network"}
    dangerous_kinds = {"send", "publish", "pay", "credential_change",
                       "external_service_call", "permanent_delete", "public_publish"}

    def __init__(self, allowlist: Iterable[str]):
        self.allowlist = set(allowlist)

    def decide(self, action: Dict[str, Any], actor: Dict[str, Any]) -> Dict[str, Any]:
        action_id = action.get("action_id")
        kind = action.get("kind", "unknown_payload")
        if not actor.get("is_owner"):
            return {"allow": False, "reason": "owner_gate_failed"}
        if not action_id:
            return {"allow": False, "reason": "missing_action_id"}
        if action_id not in self.allowlist:
            return {"allow": False, "reason": "not_in_allowlist"}
        if kind in self.forbidden_kinds:
            return {"allow": False, "reason": f"forbidden_kind:{kind}"}
        if action.get("free_shell") or action.get("payload_unknown"):
            return {"allow": False, "reason": "free_shell_or_unknown_payload_denied"}
        if kind in self.dangerous_kinds or action.get("external_effect"):
            if not action.get("owner_approved"):
                return {"allow": False, "reason": "dangerous_action_requires_owner_approval"}
            if not action.get("safety_gate"):
                return {"allow": False, "reason": "dangerous_action_requires_safety_gate"}
        if action.get("irreversible") and not action.get("rollback"):
            return {"allow": False, "reason": "irreversible_without_rollback_denied"}
        return {"allow": True, "reason": "allowed"}


class OutboundWriteAheadLedger:
    """G-03 protection. missing -> sending -> sent | failed | needs_owner.

    Any existing effect_id blocks automatic resend (sending/needs_owner included).
    NOT auto-wired into live SMTP here; see NEEDS_OWNER_HOOK in the report.
    """
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # ۲۰۲۶-۰۸-۰۸: check_same_thread=False — همان علتِ IdempotencyStore بالا.
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS outbound_effects ("
            " effect_id TEXT PRIMARY KEY,"
            " lead_id TEXT NOT NULL,"
            " payload_hash TEXT NOT NULL,"
            " state TEXT NOT NULL,"
            " provider_message_id TEXT,"
            " attempt_count INTEGER NOT NULL DEFAULT 0,"
            " reason TEXT,"
            " created_at REAL NOT NULL,"
            " updated_at REAL NOT NULL)"
        )
        self.conn.commit()

    def row(self, effect_id: str) -> Optional[Dict[str, Any]]:
        r = self.conn.execute(
            "SELECT effect_id,lead_id,payload_hash,state,provider_message_id,"
            "attempt_count,reason,created_at,updated_at FROM outbound_effects WHERE effect_id=?",
            (effect_id,),
        ).fetchone()
        if not r:
            return None
        keys = ["effect_id", "lead_id", "payload_hash", "state", "provider_message_id",
                "attempt_count", "reason", "created_at", "updated_at"]
        return dict(zip(keys, r))

    def begin_sending(self, effect_id: str, lead_id: str, payload: Any) -> Dict[str, Any]:
        h = stable_hash(payload)
        ts = now_ts()
        existing = self.row(effect_id)
        if existing:
            if existing["payload_hash"] != h:
                return {"state": "CONFLICT", "allow_send": False, "existing": existing}
            return {"state": "DUPLICATE", "allow_send": False, "existing": existing}
        self.conn.execute(
            "INSERT INTO outbound_effects(effect_id,lead_id,payload_hash,state,"
            "provider_message_id,attempt_count,reason,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (effect_id, lead_id, h, "sending", None, 1, "write_ahead_before_smtp", ts, ts),
        )
        self.conn.commit()
        return {"state": "NEW", "allow_send": True, "payload_hash": h}

    def can_auto_send(self, effect_id: str, payload: Any) -> Dict[str, Any]:
        existing = self.row(effect_id)
        if not existing:
            return {"allow_send": True, "reason": "no_existing_effect"}
        if existing["payload_hash"] != stable_hash(payload):
            return {"allow_send": False, "reason": "payload_conflict", "state": existing["state"]}
        return {"allow_send": False, "reason": "existing_effect_never_auto_resend", "state": existing["state"]}

    def mark_sent(self, effect_id: str, provider_message_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.row(effect_id):
            return {"ok": False, "reason": "missing_effect"}
        self.conn.execute(
            "UPDATE outbound_effects SET state=?, provider_message_id=?, reason=?, updated_at=? WHERE effect_id=?",
            ("sent", provider_message_id, "smtp_accepted_and_settled", now_ts(), effect_id),
        )
        self.conn.commit()
        return {"ok": True, "state": "sent"}

    def mark_failed(self, effect_id: str, reason: str) -> Dict[str, Any]:
        if not self.row(effect_id):
            return {"ok": False, "reason": "missing_effect"}
        self.conn.execute(
            "UPDATE outbound_effects SET state=?, reason=?, updated_at=? WHERE effect_id=?",
            ("failed", reason, now_ts(), effect_id),
        )
        self.conn.commit()
        return {"ok": True, "state": "failed"}

    def mark_needs_owner(self, effect_id: str, reason: str) -> Dict[str, Any]:
        if not self.row(effect_id):
            return {"ok": False, "reason": "missing_effect"}
        self.conn.execute(
            "UPDATE outbound_effects SET state=?, reason=?, updated_at=? WHERE effect_id=?",
            ("needs_owner", reason, now_ts(), effect_id),
        )
        self.conn.commit()
        return {"ok": True, "state": "needs_owner", "auto_resend": False}

    def recover_pending(self, older_than_seconds: float = 0.0) -> List[Dict[str, Any]]:
        cutoff = now_ts() - older_than_seconds
        rows = self.conn.execute(
            "SELECT effect_id FROM outbound_effects WHERE state='sending' AND updated_at<=?",
            (cutoff,),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for (effect_id,) in rows:
            self.mark_needs_owner(effect_id, "ambiguous_after_restart_or_timeout")
            item = self.row(effect_id)
            if item:
                item["auto_resend"] = False
                item["owner_action_required"] = True
                out.append(item)
        return out

    def owner_resolution(self, effect_id: str, decision: str) -> Dict[str, Any]:
        """Owner-only resolution for ambiguous outbound effects.

        Guard rails:
        * mark_sent/cancel are only valid for ambiguous states (`sending`, `needs_owner`).
        * retry never reuses the same effect_id; it only tells the owner/UI that a new
          owner-approved action/effect id is required.
        * terminal states are never silently rewritten (no sent -> cancelled, no failed -> sent).
        """
        if decision not in {"mark_sent", "retry_with_new_effect_id", "cancel"}:
            return {"ok": False, "reason": "invalid_owner_resolution"}
        row = self.row(effect_id)
        if not row:
            return {"ok": False, "reason": "missing_effect"}
        state = str(row.get("state") or "")
        ambiguous = {"sending", "needs_owner"}
        if decision == "mark_sent":
            if state == "sent":
                return {"ok": True, "state": "sent", "reason": "already_sent"}
            if state not in ambiguous:
                return {"ok": False, "state": state, "reason": "invalid_state_for_mark_sent"}
            return self.mark_sent(effect_id, "owner_marked_sent")
        if decision == "cancel":
            if state == "cancelled":
                return {"ok": True, "state": "cancelled", "reason": "already_cancelled"}
            if state not in ambiguous:
                return {"ok": False, "state": state, "reason": "invalid_state_for_cancel"}
            self.conn.execute(
                "UPDATE outbound_effects SET state=?, reason=?, updated_at=? WHERE effect_id=?",
                ("cancelled", "owner_cancelled_ambiguous_effect", now_ts(), effect_id),
            )
            self.conn.commit()
            return {"ok": True, "state": "cancelled"}
        if state == "sent":
            return {"ok": False, "state": state, "reason": "already_sent_no_retry"}
        return {"ok": True, "state": "needs_new_effect_id",
                "reason": "retry_requires_new_owner_approved_action_id"}

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:  # noqa: BLE001
            pass


class ProjectFAdapter:
    """Real Project-F HTTP adapter, credential-gated. Without creds => BLOCKED (no fake-green)."""
    def __init__(self, base_url_env: str = "PROJECTF_API_BASE_URL",
                 token_env: str = "PROJECTF_API_TOKEN", timeout: int = 20):
        self.base_url_env = base_url_env
        self.token_env = token_env
        self.timeout = timeout

    def status(self) -> Dict[str, Any]:
        base = os.getenv(self.base_url_env, "").strip()
        token = os.getenv(self.token_env, "").strip()
        if not base:
            return {"status": "BLOCKED", "reason": f"missing_{self.base_url_env}",
                    "credential_refs": [self.base_url_env, self.token_env], "fake_green": False}
        if not token:
            return {"status": "BLOCKED", "reason": f"missing_{self.token_env}",
                    "credential_refs": [self.base_url_env, self.token_env], "fake_green": False}
        return {"status": "CONFIGURED", "base_url_ref": self.base_url_env,
                "token_ref": self.token_env, "fake_green": False}

    def build_module(self, spec: Dict[str, Any], external_call_approved: bool = False,
                     safety_gate: bool = False, owner_approved: bool = False) -> Dict[str, Any]:
        st = self.status()
        if st["status"] != "CONFIGURED":
            return {"ok": False, "status": "BLOCKED", "reason": st["reason"],
                    "activation": {"set_env": [self.base_url_env, self.token_env],
                                   "then": "build_module(..., external_call_approved=True, safety_gate=True, owner_approved=True)"},
                    "fake_green": False}
        if not (external_call_approved and safety_gate and owner_approved):
            return {"ok": False, "status": "READY_NOT_CALLED",
                    "reason": "external_call_requires_owner_approval_and_safety_gate",
                    "contract": {"method": "POST", "path": "/build-module",
                                 "input": "ModuleSpec{name,purpose,constraints}",
                                 "output": "ModuleBuild{id,status,artifacts}"},
                    "fake_green": False}
        base = os.getenv(self.base_url_env, "").strip().rstrip("/")
        token = os.getenv(self.token_env, "").strip()
        body = json.dumps({"spec": spec}).encode("utf-8")
        req = urllib.request.Request(base + "/build-module", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = {"raw": raw[:2000]}
                return {"ok": True, "status": "CALLED",
                        "http_status": getattr(resp, "status", None), "body": parsed, "fake_green": False}
        except urllib.error.URLError as exc:
            return {"ok": False, "status": "CALL_FAILED",
                    "reason": str(getattr(exc, "reason", exc)), "fake_green": False}
        except Exception as exc:
            return {"ok": False, "status": "CALL_FAILED", "reason": repr(exc), "fake_green": False}


class AdaptiveValueLedger:
    """Adaptive near-real-time LOW_IMPACT measurement. Never auto-deletes legs."""
    def __init__(self, path: Path):
        self.audit = AuditLog(Path(path))

    def record(self, leg: str, event: str, value_type: str, output_score: float = 0.0,
               cost_score: float = 0.0, risk_score: float = 0.0, owner_visible: bool = True,
               effect_settled: bool = False, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.audit.append({
            "schema": "octopus.agi2027.value.v1", "leg": leg, "event": event,
            "value_type": value_type, "output_score": float(output_score),
            "cost_score": float(cost_score), "risk_score": float(risk_score),
            "owner_visible": bool(owner_visible), "effect_settled": bool(effect_settled),
            "metadata": metadata or {},
        })

    def _adaptive_horizon(self, rows: List[Dict[str, Any]]) -> float:
        if len(rows) <= 3:
            return 3600.0
        times = sorted(float(r.get("ts", 0)) for r in rows)
        gaps = [b - a for a, b in zip(times, times[1:]) if b >= a]
        if not gaps:
            return 3600.0
        avg_gap = sum(gaps) / len(gaps)
        return max(300.0, min(14 * 86400.0, avg_gap * 4.0))

    # RFC-2606/6761 reserved names — a send to these can never be a real customer.
    _RESERVED_DOMAINS = {"example.com", "example.net", "example.org", "localhost"}

    @classmethod
    def _is_fixture(cls, row: Dict[str, Any]) -> bool:
        # Fixture/drill rows (L-WAL-1 write-ahead drills, transport drills against
        # reserved domains) must never count as real-world impact; the raw journal
        # keeps them untouched.
        meta = row.get("metadata") or {}
        if row.get("fixture") is True or meta.get("fixture") is True:
            return True
        if "L-WAL-1" in (str(meta.get("lead_id", "")), str(meta.get("correlation_id", ""))):
            return True
        dom = str(meta.get("to_domain", "")).lower()
        if dom in cls._RESERVED_DOMAINS or dom.endswith((".invalid", ".test", ".example")):
            return True
        return "example.invalid" in json.dumps(row, ensure_ascii=False)

    def score(self, leg: str) -> Dict[str, Any]:
        all_rows = [r for r in self.audit.read_all() if r.get("leg") == leg]
        rows, fixture_excluded = [], 0
        for r in all_rows:
            if self._is_fixture(r):
                fixture_excluded += 1
            else:
                rows.append(r)
        if not rows:
            return {"leg": leg, "verdict": "INSUFFICIENT_SIGNAL", "low_impact": False,
                    "auto_delete": False,
                    "reason": "fixture_only" if fixture_excluded else "no_value_events_yet",
                    "real_events": 0, "fixture_excluded": fixture_excluded,
                    "impact_valid": False}
        ts = now_ts()
        latest = max(float(r.get("ts", 0)) for r in rows)
        horizon = self._adaptive_horizon(rows)
        recent = [r for r in rows if ts - float(r.get("ts", 0)) <= horizon]
        output = sum(float(r.get("output_score", 0)) for r in recent)
        cost = sum(float(r.get("cost_score", 0)) for r in recent)
        risk = sum(float(r.get("risk_score", 0)) for r in recent)
        settled = sum(1 for r in recent if r.get("effect_settled"))
        owner_visible = sum(1 for r in recent if r.get("owner_visible"))
        # "useful" counts real production value (output + settled effects).
        # owner-visible-only (no output, no settled effect) is observation, not value —
        # it must not on its own lift a leg out of LOW_IMPACT.
        useful = output + settled
        burden = cost + risk
        # LOW_IMPACT = meaningful burden with negligible real value.
        low = useful <= 0.0 and burden >= 1.0
        return {"leg": leg, "verdict": "LOW_IMPACT" if low else "USEFUL_OR_UNDER_OBSERVATION",
                "low_impact": bool(low), "auto_delete": False,
                "latest_event_age_seconds": ts - latest, "recent_events": len(recent),
                "output": output, "cost": cost, "risk": risk, "settled_effects": settled,
                "owner_visible_events": owner_visible, "adaptive_horizon_seconds": horizon,
                "real_events": len(rows), "fixture_excluded": fixture_excluded,
                "impact_valid": True}


class FuguFootprint:
    """Measures Fugu references. FIX: defaults to scanning _ops/ only (§0 rule),
    never full F:\\backup. A full-drive scan requires explicit root= opt-in."""
    SKIP = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "_Archive",
            "_Duplicates", "_worktrees", "_sandbox", ".pytest_cache", ".zcode", "site-packages"}
    EXTS = {".py", ".pyi", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg", ".ps1", ".sh"}

    def __init__(self, root: Optional[Path] = None):
        # default = _ops (the §0 rule). Caller must explicitly pass a different root
        # if they truly want a wider scan — and even then a full-drive scan is discouraged.
        self.root = Path(root) if root is not None else DEFAULT_SCAN_ROOT

    def scan(self, max_files: int = 6000) -> Dict[str, Any]:
        scanned = 0
        files_with_fugu = 0
        total_lines = 0
        top: Dict[str, int] = {}
        runtime_refs: List[str] = []
        for p in self.root.rglob("*"):
            if scanned >= max_files:
                break
            if not p.is_file():
                continue
            if any(part in self.SKIP for part in p.parts):
                continue
            if p.suffix.lower() not in self.EXTS:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scanned += 1
            count = 0
            for i, line in enumerate(text.splitlines(), start=1):
                low = line.lower()
                if "fugu" in low:
                    count += 1
                    total_lines += 1
                    if any(k in low for k in ["import", "from ", "fugu.", "subprocess",
                                              "provider", "agent", "model", "cli"]):
                        if len(runtime_refs) < 200:
                            runtime_refs.append(f"{p.relative_to(self.root)}:{i}")
            if count:
                files_with_fugu += 1
                top[str(p.relative_to(self.root))] = count
        return {"scan_root": str(self.root), "scanned_files": scanned,
                "files_with_fugu": files_with_fugu, "total_lines": total_lines,
                "top_files": sorted(top.items(), key=lambda kv: kv[1], reverse=True)[:40],
                "runtime_refs": runtime_refs}


class ManagedFlags:
    """Tiny managed-flags store for the control plane (separate from OCTOPUS-flags.cmd).
    Setting a flag here is STAGED — production code does not read it until wired."""
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def set(self, name: str, value: str) -> Dict[str, Any]:
        d = self._load()
        prev = d.get(name)
        d[name] = value
        self.path.write_text(json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "name": name, "previous": prev, "current": value,
                "rollback": {"name": name, "value": prev}}

    def get(self, name: str, default: Any = None) -> Any:
        return self._load().get(name, default)

    def all(self) -> Dict[str, Any]:
        return self._load()


REPAIRS: Dict[str, Dict[str, Any]] = {
    "repair.g03.writeahead_outbound": {
        "action_id": "repair.g03.writeahead_outbound", "kind": "safe_internal", "risk": "high",
        "summary": "Enable live OutboundWriteAheadLedger at SMTP boundary.",
        "flag": "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL",
        "target": "legs/lead_outbound_transport.py", "reversible": True,
        "rollback": "set OCTOPUS_WIRE_LEAD_OUTBOUND_WAL=0 in managed flags"},
    "repair.telegram.control_plane": {
        "action_id": "repair.telegram.control_plane", "kind": "safe_internal", "risk": "low",
        "summary": "Enable Telegram control-plane adapter flag.", "flag": "OCTOPUS_WIRE_TG_CONTROL",
        "reversible": True, "rollback": "flag rollback"},
    "repair.value.ledger": {
        "action_id": "repair.value.ledger", "kind": "safe_internal", "risk": "low",
        "summary": "Enable adaptive value/impact ledger flag.", "flag": "OCTOPUS_WIRE_VALUE_LEDGER",
        "reversible": True, "rollback": "flag rollback"},
    "repair.g02.backend_summary": {
        "action_id": "repair.g02.backend_summary", "kind": "safe_internal", "risk": "low",
        "summary": "Keep sync_agent backend-only; enable compact internal summary flag.",
        "flag": "OCTOPUS_SYNC_AGENT_BACKEND_SUMMARY", "reversible": True, "rollback": "flag rollback"},
    "repair.projectf.adapter_contract": {
        "action_id": "repair.projectf.adapter_contract", "kind": "adapter", "risk": "medium",
        "summary": "Project-F real adapter; BLOCKED until PROJECTF_API_BASE_URL/TOKEN exist.",
        "reversible": True, "rollback": "remove adapter module or disable caller"},
    "repair.self_improvement.scan": {
        "action_id": "repair.self_improvement.scan", "kind": "read_only", "risk": "none",
        "summary": "Generate owner-gated self-improvement proposals from value ledger.",
        "reversible": True, "rollback": "delete generated proposals"},
}


class ControlPlane:
    """Telegram-facing internal control adapter. Owner-gated, fail-closed, audited."""
    def __init__(self, root: Path):
        self.root = Path(root)
        self.runtime = self.root / "_ops" / "agi2027_runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(self.runtime / "control-audit.jsonl")
        self.flags = ManagedFlags(self.runtime / "managed_flags.json")
        self.idem = IdempotencyStore(self.runtime / "control-actions.sqlite3")
        self.allowlist = sorted(REPAIRS)
        self.policy = PolicyGate(self.allowlist)

    def close(self) -> None:
        """Release SQLite handles so Windows tempdir cleanup can succeed."""
        try:
            self.idem.close()
        except Exception:
            pass
    def list_repairs(self) -> List[Dict[str, Any]]:
        return [dict(v) for v in REPAIRS.values()]

    def get_repair(self, action_id: str) -> Dict[str, Any]:
        item = REPAIRS.get(action_id)
        if not item:
            return {"status": "BLOCKED", "reason": "unknown_repair_action", "action_id": action_id}
        return dict(item)

    def _snippet(self, action_id: str) -> str:
        if action_id == "repair.g03.writeahead_outbound":
            return (
                "from _ops.agi2027_control.runtime import OutboundWriteAheadLedger\n"
                "from pathlib import Path\n"
                "ledger = OutboundWriteAheadLedger(Path('_ops/agi2027_runtime/outbound-effects.sqlite3'))\n"
                "# BEFORE SMTP: gate = ledger.begin_sending(effect_id, lead_id, payload)\n"
                "# IF NOT gate['allow_send']: do not send; return DUPLICATE/CONFLICT/needs_owner\n"
                "# AFTER provider accept: ledger.mark_sent(effect_id, provider_message_id)\n"
                "# ON STARTUP: ledger.recover_pending()  # sending -> needs_owner; never auto-resend\n"
            )
        if action_id == "repair.projectf.adapter_contract":
            return (
                "from _ops.agi2027_control.runtime import ProjectFAdapter\n"
                "# set PROJECTF_API_BASE_URL and PROJECTF_API_TOKEN securely in env\n"
                "# ProjectFAdapter().build_module(spec, external_call_approved=True, safety_gate=True, owner_approved=True)\n"
            )
        return "# no code hook required"

    def _outbound_ledger(self) -> OutboundWriteAheadLedger:
        return OutboundWriteAheadLedger(self.runtime / "outbound-effects.sqlite3")

    def _outbound_status(self) -> Dict[str, Any]:
        ledger = self._outbound_ledger()
        try:
            rows = ledger.conn.execute(
                "SELECT state, COUNT(*) FROM outbound_effects GROUP BY state ORDER BY state"
            ).fetchall()
            latest = ledger.conn.execute(
                "SELECT effect_id, lead_id, state, reason, updated_at "
                "FROM outbound_effects ORDER BY updated_at DESC LIMIT 8"
            ).fetchall()
            return {"ok": True, "status": "OK",
                    "flag": self.flags.get("OCTOPUS_WIRE_LEAD_OUTBOUND_WAL", "0"),
                    "counts": {state: count for state, count in rows},
                    "latest": [
                        {"effect_id": e, "lead_id": l, "state": s, "reason": r, "updated_at": u}
                        for e, l, s, r, u in latest
                    ]}
        finally:
            ledger.close()

    def _outbound_recover(self) -> Dict[str, Any]:
        ledger = self._outbound_ledger()
        try:
            rows = ledger.recover_pending(older_than_seconds=0)
            return {"ok": True, "status": "RECOVERED", "count": len(rows), "rows": rows[:8],
                    "auto_resend": False}
        finally:
            ledger.close()

    def _outbound_resolve(self, effect_id: str, decision: str) -> Dict[str, Any]:
        """Human-in-the-loop resolution for G-03 ambiguous sends.

        This never sends email. `retry` returns a new-action requirement; it does not
        perform the retry. Effect ids are constrained to ledger-safe identifiers.
        """
        safe_effect_id = str(effect_id or "").strip()
        if (not safe_effect_id or len(safe_effect_id) > 160 or
                not re.fullmatch(r"[A-Za-z0-9:_@.\-]+", safe_effect_id)):
            return {"ok": False, "status": "BLOCKED", "reason": "invalid_effect_id"}
        mapped = {
            "mark_sent": "mark_sent",
            "mark-sent": "mark_sent",
            "sent": "mark_sent",
            "cancel": "cancel",
            "retry": "retry_with_new_effect_id",
            "retry_with_new_effect_id": "retry_with_new_effect_id",
        }.get(str(decision or "").strip().lower())
        if mapped is None:
            return {"ok": False, "status": "BLOCKED", "reason": "invalid_owner_decision"}
        ledger = self._outbound_ledger()
        try:
            before = ledger.row(safe_effect_id)
            res = ledger.owner_resolution(safe_effect_id, mapped)
            after = ledger.row(safe_effect_id)
            status = "RESOLVED" if res.get("ok") else "BLOCKED"
            out = {"ok": bool(res.get("ok")), "status": status,
                   "effect_id": safe_effect_id, "decision": mapped,
                   "before_state": (before or {}).get("state"),
                   "after_state": (after or {}).get("state"),
                   "result": res, "auto_resend": False}
            self.audit.append({"event": "outbound_owner_resolution", **out})
            return out
        finally:
            ledger.close()

    def _apply(self, item: Dict[str, Any]) -> Dict[str, Any]:
        action_id = item["action_id"]
        kind = item.get("kind")
        if kind == "safe_internal":
            res = self.flags.set(item["flag"], "1")
            live_wired = item.get("flag") in {
                "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL",
                "OCTOPUS_WIRE_TG_CONTROL",
            }
            return {"ok": True, "status": "APPLIED", "action_id": action_id,
                    "flag": item["flag"], "live_wired": live_wired,
                    "staged_not_wired": not live_wired,
                    "note": ("flag is read by production wiring" if live_wired else
                             "flag staged; no production reader is wired yet"),
                    "rollback": res["rollback"]}
        if kind == "read_only":
            proposals = {"schema": "octopus.agi2027.self_improvement.v1", "ts": now_ts(),
                         "auto_apply": False, "owner_control": "required",
                         "note": "placeholder; real proposals come from value ledger events"}
            p = self.runtime / "self-improvement-proposals.json"
            p.write_text(json.dumps(proposals, indent=2, ensure_ascii=False), encoding="utf-8")
            return {"ok": True, "status": "APPLIED", "action_id": action_id, "report": str(p)}
        if kind in {"code_edit", "adapter"}:
            return {"ok": False,
                    "status": "NEEDS_OWNER_HOOK" if kind == "code_edit" else "BLOCKED_UNTIL_CONFIGURED",
                    "action_id": action_id,
                    "reason": "live code/external API requires exact hook or credentials; no blind patch, no fake-green",
                    "target": item.get("target"), "snippet": self._snippet(action_id), "fake_green": False}
        return {"ok": False, "status": "BLOCKED", "reason": "unknown_kind"}

    def handle(self, text: str, actor: Dict[str, Any]) -> Dict[str, Any]:
        raw = (text or "").strip()
        self.audit.append({"event": "control_input", "text": raw[:200],
                           "actor_owner": bool(actor.get("is_owner"))})
        if not actor.get("is_owner"):
            return {"ok": False, "status": "DENIED", "reason": "owner_gate_failed"}
        if raw in {"/ops", "/ops status"}:
            return {"ok": True, "status": "OK", "repairs": self.allowlist, "flags": self.flags.all(),
                    "commands": ["/repair list", "/repair plan <id>", "/repair execute <id>",
                                 "/repair rollback <id>", "/outbound status", "/outbound recover",
                                 "/outbound mark-sent <effect_id>", "/outbound cancel <effect_id>",
                                 "/outbound retry <effect_id>", "/impact <leg>", "/fugu",
                                 "/ui", "/truth", "/legs", "/approvals"]}
        # PHASE 6 (2026-08-02): /ui launcher — graceful when URL unset (no fake-live).
        if raw in {"/ui", "/open"}:
            url = os.getenv("OCTOPUS_MINIAPP_URL", "").strip()
            if url:
                return {"ok": True, "status": "OK", "title": "Octopus Cockpit",
                        "web_app_url": url, "note": "open MiniApp via Telegram web_app button"}
            return {"ok": True, "status": "CONFIG_NEEDED",
                    "message": "MiniApp URL تنظیم نشده. OCTOPUS_MINIAPP_URL را set کن. "
                               "local/dev: _ops/telegram_center/miniapp/",
                    "note": "read-only cockpit; actions disabled until owner auth"}
        if raw == "/truth":
            # 2026-08-10: drift سندی — نامِ تاریخ‌دارِ کهنه (08-02) را hardcode
            # می‌کرد در حالی که فایل واقعی OCTOPUS/CURRENT-TRUTH.md است. همان
            # الگوی /legs: از resolver مشترک miniapp_state (که env → بی‌تاریخ →
            # تاریخ‌دار را درست پیدا می‌کند) استفاده کن — نه کپیِ مسیر.
            try:
                import sys as _sys
                _tc = str(self.root / "_ops" / "telegram_center")
                if _tc not in _sys.path:
                    _sys.path.insert(0, _tc)
                from miniapp_state import get_current_truth  # type: ignore
                _t = get_current_truth(self.root)
                preview = str(_t.get("preview", "")) if _t.get("status") == "ok" else ""
                return {"ok": True, "status": "OK" if preview else "MISSING",
                        "preview": preview[:600], "reason": _t.get("reason", "")}
            except Exception:  # noqa: BLE001
                return {"ok": True, "status": "MISSING", "preview": "",
                        "reason": "truth_resolver_unavailable"}
        if raw == "/legs":
            try:
                import sys as _sys
                _tc = str(self.root / "_ops" / "telegram_center")
                if _tc not in _sys.path:
                    _sys.path.insert(0, _tc)
                from miniapp_state import get_legs_state  # type: ignore
                return {"ok": True, "status": "OK", "legs": get_legs_state(self.root).get("legs", {})}
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "status": "ERROR", "reason": f"{type(exc).__name__}"}
        if raw == "/approvals":
            try:
                import sys as _sys
                _tc = str(self.root / "_ops" / "telegram_center")
                if _tc not in _sys.path:
                    _sys.path.insert(0, _tc)
                from miniapp_state import get_approvals_state  # type: ignore
                return {"ok": True, "status": "OK", **get_approvals_state(self.root)}
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "status": "ERROR", "reason": f"{type(exc).__name__}"}
        if raw == "/repair list":
            return {"ok": True, "status": "OK", "repairs": self.list_repairs()}
        if raw in {"/outbound", "/outbound status"}:
            return self._outbound_status()
        if raw == "/outbound recover":
            return self._outbound_recover()
        if raw in {"/projectf", "/projectf status"}:
            return {"ok": True, "status": "OK", "projectf": ProjectFAdapter().status()}
        parts = raw.split()
        if len(parts) >= 3 and parts[0] == "/outbound" and parts[1] in {"mark-sent", "sent", "cancel", "retry"}:
            return self._outbound_resolve(parts[2], parts[1])
        if len(parts) >= 3 and parts[0] == "/repair" and parts[1] == "plan":
            item = self.get_repair(parts[2])
            return {"ok": item.get("status") != "BLOCKED", "status": "PLAN", "repair": item}
        if len(parts) >= 3 and parts[0] == "/repair" and parts[1] == "execute":
            action_id = parts[2]
            item = self.get_repair(action_id)
            if item.get("status") == "BLOCKED":
                return {"ok": False, "status": "BLOCKED", "reason": item.get("reason"), "action_id": action_id}
            policy_kind = "internal_control" if item.get("kind") in {"safe_internal", "read_only"} else "code_repair"
            decision = self.policy.decide({**item, "kind": policy_kind, "owner_approved": True,
                                           "safety_gate": True, "action_id": action_id}, actor)
            if not decision["allow"]:
                return {"ok": False, "status": "DENIED", "reason": decision["reason"], "action_id": action_id}
            key = "exec:" + action_id + ":" + stable_hash(item)
            idem = self.idem.begin(key, {"action_id": action_id, "item": item})
            if idem["state"] in {"DUPLICATE", "CONFLICT", "BLOCKED"}:
                return {"ok": idem["state"] == "DUPLICATE", "status": idem["state"], "idempotency": idem}
            result = self._apply(item)
            self.idem.settle(key, result.get("status", "DONE"), result)
            self.audit.append({"event": "repair_execute", "action_id": action_id, "result": result})
            return result
        if len(parts) >= 3 and parts[0] == "/repair" and parts[1] == "rollback":
            action_id = parts[2]
            item = self.get_repair(action_id)
            if item.get("kind") == "safe_internal" and item.get("flag"):
                res = self.flags.set(item["flag"], "0")
                self.audit.append({"event": "repair_rollback", "action_id": action_id})
                return {"ok": True, "status": "ROLLED_BACK", "flag": item["flag"], "detail": res}
            return {"ok": False, "status": "MANUAL_ROLLBACK",
                    "reason": "restore from _ops/patch_backups or remove exact hook", "action_id": action_id}
        if len(parts) >= 2 and parts[0] == "/impact":
            return {"ok": True, "status": "OK",
                    "impact": AdaptiveValueLedger(self.runtime / "value-ledger.jsonl").score(parts[1])}
        if raw == "/fugu":
            return {"ok": True, "status": "OK", "fugu": FuguFootprint().scan()}
        return {"ok": False, "status": "UNKNOWN_COMMAND", "reason": "fail_closed"}

