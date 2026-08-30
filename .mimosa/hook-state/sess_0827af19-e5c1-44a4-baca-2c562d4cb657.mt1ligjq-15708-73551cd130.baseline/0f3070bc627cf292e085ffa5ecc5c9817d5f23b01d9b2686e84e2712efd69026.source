#!/usr/bin/env python3
"""capabilities.py — 🗂 Capability Registry + Dynamic Disabled Reason
(gapهای §۳.۴ و §۵.۳/§۵.۴ در OCTOPUS-ACTUATION-ALIGNMENT).

قبلاً منوها hard-code بودند و «چرا این دکمه خاموش است؟» جوابِ runtime نداشت.
حالا هر ماژول خودش را advertise می‌کند و UI (لنگر/استودیو/داشبورد) در render-time
از `capabilities.json` می‌خواند: {name, level, executable, reason}.

نردبانِ حساسیت (§۴ همان سند):
  🟢 low    — فایلِ خام/read-only/shadow → خودِ swarm
  🟡 medium — configِ محلی/spec → خودِ swarm
  🔴 high   — اقدامِ بیرونی/publish/DM/payment/daemon → فقط انسان (آری)

قانونِ سخت (از PROJECT-F-CONTROL-MANIFEST.json، fail-closed مثل orchestrator):
هر capabilityِ 🔴 تا وقتی G0 باز است executable=False — بدونِ استثنا، بدونِ env-bypass.
manifest غایب/خراب = قفل (fail-closed). این آگاهانه سخت‌گیرانه‌تر از UX است.

$0 · stdlib-only.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import config

LEVELS = ("green", "amber", "red")
_GO_STAMP = "GATE-STAMP-GO"          # فایلِ مهرِ انسانی در 00 - Control/


# ─── وضعیتِ گیت‌ها از قراردادِ ماشین‌خوان ────────────────────────────────────
@dataclass
class GateState:
    """خوانشِ fail-closedِ گیت‌ها از PROJECT-F-CONTROL-MANIFEST.json.
    هر خطای خواندن/parse = «قفل» (g0_open=True). هیچ مسیرِ خطایی باز برنمی‌گرداند."""
    g0_open: bool = True
    security_gate_closed: bool = True
    reason: str = "manifest unreadable → fail-closed"

    @classmethod
    def load(cls, manifest_path: str | Path | None = None,
             control_dir: str | Path | None = None) -> "GateState":
        mp = Path(manifest_path) if manifest_path else \
            Path(config.PF_ROOT) / "PROJECT-F-CONTROL-MANIFEST.json"
        st = cls()
        try:
            raw = json.loads(mp.read_text(encoding="utf-8"))
            g0 = str(raw.get("gates", {}).get("G0", {}).get("status", "OPEN"))
            sec = str(raw.get("status_snapshot", {}).get("security_gate", "closed"))
            st.g0_open = g0.strip().upper().startswith("OPEN")
            st.security_gate_closed = not sec.strip().lower().startswith("open")
        except (OSError, ValueError, UnicodeDecodeError):
            return st                                    # fail-closed
        # مهرِ انسانیِ GO (فایل فیزیکی؛ ساختنش کارِ انسان است، نه agent)
        cdir = Path(control_dir) if control_dir else Path(config.PF_ROOT) / "00 - Control"
        stamp = (cdir / _GO_STAMP).exists()
        if st.g0_open:
            st.reason = "🔒 GATE 0 OPEN — تصمیم Branch A/B روی دیسک بسته نشده؛ verdict انسانی لازم"
        elif st.security_gate_closed:
            st.reason = "🔒 Security Gate بسته — چک‌لیست OpSec تیک نخورده"
        elif not stamp:
            st.reason = f"🔒 مهر انسانی غایب — فایل 00 - Control/{_GO_STAMP} فقط با دست آری ساخته می‌شود"
        else:
            st.reason = "gates passed (human-stamped)"
        st._stamp = stamp  # type: ignore[attr-defined]
        return st

    @property
    def outward_locked(self) -> bool:
        """قفلِ کلیِ outward: G0 باز یا security بسته یا مهرِ انسانی غایب → قفل."""
        return self.g0_open or self.security_gate_closed \
            or not getattr(self, "_stamp", False)


# ─── Capability ──────────────────────────────────────────────────────────────
@dataclass
class Capability:
    name: str
    level: str                       # green | amber | red
    desc: str = ""
    organ: str = "legs"
    can_execute: Optional[Callable[[], bool]] = None
    disabled_reason: str = ""        # دلیلِ ایستا (اختیاری)؛ دلیلِ پویا در snapshot

    def __post_init__(self):
        if self.level not in LEVELS:
            raise ValueError(f"level must be one of {LEVELS}: {self.level!r}")


class CapabilityRegistry:
    """ثبت/لغو/عکسِ لحظه‌ای. snapshot → PF_STATE/capabilities.json برای UI."""

    def __init__(self, state_dir: str | Path | None = None,
                 gates: GateState | None = None):
        base = Path(state_dir) if state_dir else Path(config.ensure_pf_state())
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "capabilities.json"
        self._caps: dict[str, Capability] = {}
        self._gates = gates or GateState.load()

    def advertise(self, cap: Capability) -> None:
        self._caps[cap.name] = cap

    def revoke(self, name: str) -> None:
        self._caps.pop(name, None)

    def refresh_gates(self, gates: GateState | None = None) -> None:
        self._gates = gates or GateState.load()

    # ── قلبِ ماجرا: executable + دلیلِ پویا ──
    def resolve(self, name: str) -> dict:
        cap = self._caps.get(name)
        if cap is None:
            return {"name": name, "known": False, "executable": False,
                    "reason": "unknown capability"}
        # 🔴 high: قفلِ outward بر همه‌چیز مقدم است — بدونِ bypass
        if cap.level == "red" and self._gates.outward_locked:
            return {"name": name, "known": True, "level": cap.level,
                    "organ": cap.organ, "executable": False,
                    "reason": self._gates.reason}
        # چکِ پویا (مثل CostMeter.can_spend()==False در §۳.۴)
        if cap.can_execute is not None:
            try:
                ok = bool(cap.can_execute())
            except Exception:  # noqa: BLE001 — چکِ خراب = قفل (fail-closed)
                ok = False
            if not ok:
                return {"name": name, "known": True, "level": cap.level,
                        "organ": cap.organ, "executable": False,
                        "reason": cap.disabled_reason or "can_execute() == False"}
        return {"name": name, "known": True, "level": cap.level,
                "organ": cap.organ, "executable": True, "reason": ""}

    def snapshot(self, write: bool = True) -> dict:
        """عکسِ کاملِ registry (برای render پویا در UI). write=True → capabilities.json."""
        snap = {
            "gates": {"g0_open": self._gates.g0_open,
                      "outward_locked": self._gates.outward_locked,
                      "reason": self._gates.reason},
            "capabilities": [
                {**self.resolve(n), "desc": c.desc}
                for n, c in sorted(self._caps.items())
            ],
        }
        if write:
            try:
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(json.dumps(snap, ensure_ascii=False, indent=2),
                               encoding="utf-8")
                tmp.replace(self.path)
            except OSError:
                pass
        return snap


def default_registry(state_dir: str | Path | None = None,
                     gates: GateState | None = None) -> CapabilityRegistry:
    """registryِ استاندارد nodeِ Project-F — بازتابِ صادقانه‌ی وضعِ فعلی."""
    reg = CapabilityRegistry(state_dir=state_dir, gates=gates)
    reg.advertise(Capability("research.integrate", "green", "تحقیق و یکپارچه‌سازی داخل پوشه", "epistemics"))
    reg.advertise(Capability("draft.compose", "green", "درفتِ propose-only در drafts-awaiting-gate/", "legs"))
    reg.advertise(Capability("kpi.render", "green", "رندر داشبورد KPI (read-only)", "ledger"))
    reg.advertise(Capability("learning.recommend", "green", "پیشنهادِ bandit (propose-only)", "learning"))
    reg.advertise(Capability("shadow.tick", "green", "tick ارکستریتور در shadow", "heart"))
    reg.advertise(Capability("config.local", "amber", "تغییر configِ محلی/spec", "governor"))
    # 🔴 — همه تا بازشدنِ گیت‌ها + مهرِ انسانی قفل‌اند (بدونِ استثنا):
    reg.advertise(Capability("platform.account_create", "red", "ساخت اکانت واقعی", "legs"))
    reg.advertise(Capability("platform.publish", "red", "هر پست/انتشار عمومی", "legs"))
    reg.advertise(Capability("platform.dm_send", "red", "ارسال هر DM", "legs"))
    reg.advertise(Capability("money.move", "red", "هر پرداخت/برداشت", "money"))
    reg.advertise(Capability("daemon.start_live", "red", "استارتِ هر daemon زنده", "governor"))
    return reg
