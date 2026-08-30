#!/usr/bin/env python3
"""actuator.py — 🦾 Motor Cortex با سه حالتِ shadow → dry-run → live
(gapِ #۲ در OCTOPUS-ACTUATION-ALIGNMENT §۳.۲؛ طراحیِ §۵.۲ همان سند).

فلسفه: «موجودِ زنده ولی فلج» را به «موجودی با سیستمِ حرکتیِ کامل ولی ترمزِ دستیِ
انسانی» تبدیل می‌کند. سه حالت:

  shadow  — پیش‌فرض. فقط لاگ می‌کند «would dispatch X» + درفتِ propose-only.
  dry-run — شبیه‌سازیِ کاملِ تحویل: ack، retry/backoff، circuit-breaker، dead-letter.
  live    — 🔴 ساختاراً قفل. شرط‌ها (همه با هم): G0 روی دیسک CLOSED + مهرِ انسانیِ
            00 - Control/GATE-STAMP-GO + پرچمِ env + عدمِ KILL/HALT. هر کدام fail →
            ActuationLocked + ثبت در VERDICT_QUEUE.md + رویدادِ gates.actuation.blocked.
            و حتی اگر همه پاس شوند: این build عمداً **هیچ adapterِ زنده‌ای ندارد**
            (NotImplementedError) — سوییچِ نهایی فقط با کدی است که خودِ آری بعد از
            Branch A و چکِ حقوقی اضافه می‌کند. (هم‌قرارداد با master_agent_boundary
            در CONTROL-MANIFEST: هیچ agentی نمی‌تواند outward اجرا یا self-approve کند.)

delivery confirmation + dead-letter (§۳.۲): هر dispatch یک DeliveryReceipt برمی‌گرداند؛
شکستِ نهایی → dead_letter.jsonl (هیچ چیز بی‌صدا گم نمی‌شود).

$0 · stdlib-only · صفر importِ شبکه (ساختاراً آفلاین).
"""
from __future__ import annotations

import json
import os
import time
import datetime as _dt
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from . import config
from .capabilities import GateState

MODES = ("shadow", "dry_run", "live")
_LIVE_FLAG = "OCTOPUS_WIRE_PF_ACTUATOR_LIVE"        # فقط "1" (قرارداد flag)


class ActuationLocked(RuntimeError):
    """هر تلاشِ live پشتِ گیت — با دلیلِ صریح."""


@dataclass
class ActionRequest:
    """درخواستِ اقدام — content-free (فقط metadata/tag؛ هرگز متن هویت‌دار/محتوا)."""
    kind: str                       # مثلا "post-draft" | "dm-draft" | "kpi-note"
    channel: str                    # "reddit" | "x" | "of" | "internal"
    tag: str = ""
    payload_ref: str = ""           # ارجاع به فایلِ draft (نه خودِ محتوا)
    correlation: str = ""


@dataclass
class DeliveryReceipt:
    ok: bool
    mode: str
    attempts: int = 0
    ack: bool = False
    reason: str = ""
    dead_letter: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class CircuitBreaker:
    """per-channel: بعد از N شکست، مدار برای cooldown باز می‌ماند (§۳.۲)."""

    def __init__(self, threshold: int = 3, cooldown_s: float = 600.0):
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self._fail: dict[str, list[float]] = {}

    def record_failure(self, channel: str) -> None:
        self._fail.setdefault(channel, []).append(time.time())

    def record_success(self, channel: str) -> None:
        self._fail.pop(channel, None)

    def allow(self, channel: str) -> bool:
        fails = [t for t in self._fail.get(channel, [])
                 if time.time() - t < self.cooldown_s]
        self._fail[channel] = fails
        return len(fails) < self.threshold


class Actuator:
    """Motor cortex. bus/telemetry تزریق‌پذیر (تست). حالتِ پیش‌فرض: shadow."""

    def __init__(self, bus=None, telemetry=None, mode: str = "shadow",
                 project_root: str | Path | None = None,
                 state_dir: str | Path | None = None,
                 breaker: CircuitBreaker | None = None,
                 fail_channels: frozenset[str] = frozenset()):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        self.mode = mode
        self.bus = bus
        self.telemetry = telemetry
        self.root = Path(project_root) if project_root else Path(config.PF_ROOT)
        base = Path(state_dir) if state_dir else Path(config.ensure_pf_state())
        base.mkdir(parents=True, exist_ok=True)
        self.dead_letter_path = base / "dead_letter.jsonl"
        self.breaker = breaker or CircuitBreaker()
        self._fail_channels = fail_channels      # شبیه‌سازِ شکست در dry-run (تست)

    # ── کمکی‌ها ──
    def _emit(self, event: str, msg: str, **kw) -> None:
        if self.bus is not None:
            self.bus.safe_publish(event, "legs", msg, **kw)

    def _kill_or_halt(self) -> str:
        """KILL/HALT files = ترمزِ اضطراری (قراردادِ موجودِ langar/studio)."""
        for p, label in ((self.root / "langar" / "KILL", "langar/KILL"),
                         (self.root / "studio" / "HALT", "studio/HALT"),
                         (Path(config.VAULT) / "_ops" / "STOP-ORGANISM", "_ops/STOP-ORGANISM")):
            try:
                if p.exists():
                    return label
            except OSError:
                continue
        return ""

    # ── propose (همیشه مجاز — propose-only ذاتی) ──
    def propose(self, action: ActionRequest, meta: dict | None = None) -> Path:
        """درفتِ propose-only در drafts-awaiting-gate/ — content-free metadata.
        خروجی: مسیرِ فایلِ درفت. تصمیم/انتشار همیشه با انسان."""
        ddir = self.root / "drafts-awaiting-gate"
        ddir.mkdir(parents=True, exist_ok=True)
        import secrets as _sec
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = ddir / f"draft-{action.kind}-{action.channel}-{stamp}-{_sec.token_hex(2)}.json"
        doc = {"kind": action.kind, "channel": action.channel, "tag": action.tag,
               "created": stamp, "mode": self.mode, "status": "awaiting-human-gate",
               "meta": meta or {}, "note": "propose-only — hiç outward action"}
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        self._emit("legs.actuation.proposed", f"draft queued: {action.kind}@{action.channel}",
                   status="success", approval_state="required",
                   payload={"payload_ref": str(path.name), "tag": action.tag})
        return path

    # ── dispatch ──
    def dispatch(self, action: ActionRequest) -> DeliveryReceipt:
        t0 = time.time()
        halted = self._kill_or_halt()
        if halted:
            self._emit("gates.actuation.blocked", f"kill/halt active: {halted}",
                       status="blocked", level="WARN", gate_name="kill_switch",
                       gate_reason=halted)
            return self._finish(action, DeliveryReceipt(
                ok=False, mode=self.mode, reason=f"kill-switch: {halted}"), t0)

        if self.mode == "shadow":
            self._emit("legs.actuation.skipped",
                       f"[SHADOW] would dispatch {action.kind} → {action.channel}",
                       status="skipped", approval_state="not_required",
                       payload={"tag": action.tag})
            return self._finish(action, DeliveryReceipt(
                ok=True, mode="shadow", attempts=0, ack=False,
                reason="shadow: logged only — nothing left the machine"), t0)

        if self.mode == "dry_run":
            return self._finish(action, self._dry_run(action), t0)

        # mode == "live" → دیوارِ چندلایه
        self._assert_live_allowed(action)
        # اگر به اینجا رسید یعنی همه‌ی گیت‌ها پاس شده‌اند — و باز هم:
        raise NotImplementedError(
            "live adapters intentionally NOT shipped in this build; "
            "adding them is a human-only step after Branch A + licensed legal check")

    # ── dry-run: شبیه‌سازیِ کاملِ مسیرِ تحویل ──
    def _dry_run(self, action: ActionRequest) -> DeliveryReceipt:
        if not self.breaker.allow(action.channel):
            self._emit("legs.actuation.blocked", f"circuit open: {action.channel}",
                       status="blocked", level="WARN")
            return DeliveryReceipt(ok=False, mode="dry_run",
                                   reason="circuit-breaker open")
        attempts = 0
        for attempt in range(1, 3):                       # حداکثر ۲ تلاش
            attempts = attempt
            simulated_ok = action.channel not in self._fail_channels
            if simulated_ok:
                self.breaker.record_success(action.channel)
                self._emit("legs.actuation.simulated",
                           f"[DRY-RUN] {action.kind} → {action.channel} ack",
                           status="success", duration_ms=1)
                return DeliveryReceipt(ok=True, mode="dry_run",
                                       attempts=attempts, ack=True,
                                       reason="simulated end-to-end ack")
            self.breaker.record_failure(action.channel)
            self._emit("legs.actuation.retrying",
                       f"[DRY-RUN] attempt {attempt} failed", status="retrying",
                       level="WARN")
        # dead-letter — هیچ شکستی بی‌صدا گم نمی‌شود
        try:
            with open(self.dead_letter_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), **asdict(action)},
                                   ensure_ascii=False) + "\n")
        except OSError:
            pass
        return DeliveryReceipt(ok=False, mode="dry_run", attempts=attempts,
                               reason="simulated failure ×2", dead_letter=True)

    # ── دیوارِ live (fail-closed؛ بدونِ مسیرِ خطایی که True بدهد) ──
    def _assert_live_allowed(self, action: ActionRequest) -> None:
        reasons: list[str] = []
        gates = GateState.load()
        if gates.outward_locked:
            reasons.append(gates.reason)
        if os.environ.get(_LIVE_FLAG, "0") != "1":
            reasons.append(f"env {_LIVE_FLAG}!=1")
        if reasons:
            reason = " | ".join(reasons)
            self._emit("gates.actuation.blocked", f"LIVE refused: {action.kind}",
                       status="blocked", level="WARN", gate_name="gate0_outward",
                       gate_reason=reason, approval_state="required")
            self._queue_verdict(action, reason)
            raise ActuationLocked(reason)

    def _queue_verdict(self, action: ActionRequest, reason: str) -> None:
        """append-only به VERDICT_QUEUE.md — سینیِ رأی، نه مجوز (طبق manifest)."""
        vq = self.root / "VERDICT_QUEUE.md"
        line = (f"\n- [ ] **VQ-ACT-{_dt.date.today().isoformat()}** — تلاشِ live برای "
                f"`{action.kind}@{action.channel}` رد شد (fail-closed). دلیل: {reason}. "
                f"تصمیم: فقط انسان؛ پیش‌نیاز: Branch A روی دیسک + چک حقوقی + GATE-STAMP-GO.")
        try:
            with open(vq, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass

    def _finish(self, action: ActionRequest, r: DeliveryReceipt, t0: float) -> DeliveryReceipt:
        if self.telemetry is not None:
            try:
                self.telemetry.record(
                    job_id=f"{action.kind}:{action.channel}", organ="legs",
                    duration_ms=int((time.time() - t0) * 1000),
                    outcome="ok" if r.ok else ("blocked" if "kill" in r.reason or "circuit" in r.reason else "failed"),
                    error="" if r.ok else r.reason)
            except Exception:  # noqa: BLE001
                pass
        return r
