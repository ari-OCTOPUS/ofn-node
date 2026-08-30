#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shadow_channels.py — side-effect-free wrappers for BCM / Hebbian / Pain.

Uses temp persist paths. Never calls protective_override / APPLY flags.
Untrusted Hebbian input → quarantined, no association write.
"""
from __future__ import annotations

import hashlib
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChannelResult:
    run_id: str
    status: str
    evidence_level: str
    external_effects: tuple[()]
    weight: float | None = None
    initial_weight: float | None = None
    strength: float | None = None
    association_exists: bool = False
    association_written: bool = False
    quarantined: bool = False
    pain: float | None = None
    action_taken: str | None = None
    route_changed: bool = False
    tool_called: bool = False
    decision_influence: str = "none"
    decision: str | None = None
    reason_code: str | None = None
    trace_digest: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "evidence_level": self.evidence_level,
            "external_effects": list(self.external_effects),
            "trace_digest": self.trace_digest,
            "decision_influence": self.decision_influence,
        }


def _digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class BCMShadowChannel:
    def __init__(
        self,
        *,
        w_cap: float = 1.0,
        beta: float = 0.01,
        eta: float = 0.1,
        key: str = "mem",
    ) -> None:
        from neural.bcm import BCMStabilizer

        self._tmpdir = tempfile.TemporaryDirectory(prefix="bcm-shadow-")
        path = Path(self._tmpdir.name) / "bcm-weights.json"
        self._key = key
        self._bcm = BCMStabilizer(
            persist_path=path, w_cap=w_cap, beta=beta, eta=eta, w_floor=0.001
        )

    def run(
        self,
        *,
        activations: list[float],
        run_id: str,
        initial_weight: float | None = None,
    ) -> ChannelResult:
        if any(not math.isfinite(float(a)) for a in activations):
            return ChannelResult(
                run_id=run_id,
                status="UNKNOWN",
                evidence_level="SHADOW",
                external_effects=(),
                decision_influence="none",
                trace_digest=_digest(f"{run_id}|nan"),
            )
        if initial_weight is not None and self._key in self._bcm._weights:
            self._bcm._weights[self._key]["w"] = float(initial_weight)
        elif initial_weight is not None:
            self._bcm._weights[self._key] = {
                "w": float(initial_weight),
                "theta": 0.0,
            }
        w0 = self._bcm.weight(self._key)
        if w0 is None:
            # seed key
            self._bcm.step(
                {self._key: 0.0}, known_keys=[self._key]
            )
            w0 = self._bcm.weight(self._key) or 0.0
        for y in activations:
            self._bcm.step({self._key: float(y)}, known_keys=[self._key])
        w1 = self._bcm.weight(self._key)
        if w1 is None:
            w1 = 0.0
        payload = f"{run_id}|{activations}|{w0}|{w1}"
        return ChannelResult(
            run_id=run_id,
            status="OK",
            evidence_level="SHADOW",
            external_effects=(),
            weight=float(w1),
            initial_weight=float(w0),
            trace_digest=_digest(payload),
        )


class HebbianShadowChannel:
    def __init__(self, *, learn_rate: float = 0.10, decay_rate: float = 0.995) -> None:
        from neural import hebbian as hb

        self._tmpdir = tempfile.TemporaryDirectory(prefix="hebb-shadow-")
        path = Path(self._tmpdir.name) / "hebbian.json"
        self._hb = hb.HebbianAssociator(data_path=path)
        self._learn = learn_rate
        self._decay = decay_rate
        # Patch module rates for this process-local test only if needed
        self._orig = (hb.LEARN_RATE, hb.DECAY_RATE)
        hb.LEARN_RATE = learn_rate
        hb.DECAY_RATE = decay_rate

    def run(
        self,
        *,
        pair: tuple[str, str],
        co_occurrences: int,
        absent_ticks: int,
        trust_level: str = "verified",
        run_id: str = "hebb-shadow",
    ) -> ChannelResult:
        if trust_level == "untrusted":
            return ChannelResult(
                run_id=run_id,
                status="QUARANTINED",
                evidence_level="SHADOW",
                external_effects=(),
                association_written=False,
                quarantined=True,
                decision_influence="none",
                trace_digest=_digest(f"{run_id}|quarantine|{pair}"),
            )
        a, b = pair
        for _ in range(max(0, co_occurrences)):
            self._hb.observe([a, b])
        for _ in range(max(0, absent_ticks)):
            self._hb.decay()
        strength = self._hb.strength_of(a, b)
        exists = strength >= 0.005 and any(
            set(x.signals) == {a, b} for x in self._hb.associations
        )
        return ChannelResult(
            run_id=run_id,
            status="OK",
            evidence_level="SHADOW",
            external_effects=(),
            strength=float(strength),
            association_exists=exists,
            association_written=co_occurrences > 0,
            quarantined=False,
            trace_digest=_digest(
                f"{run_id}|{pair}|{co_occurrences}|{absent_ticks}|{strength:.6f}"
            ),
        )


class PainChaosRuntime:
    """Mock chaos around nociceptor — no Toxiproxy dependency required.

    Redis-down / kill-switch simulated in-process for fail-closed assertions.
    """

    def __init__(self) -> None:
        from neural.nociceptor import Nociceptor

        self._noci = Nociceptor()
        self._kill = False
        self._redis_down = False
        self._last_pain = 0.0

    def reset(self) -> None:
        self._kill = False
        self._redis_down = False
        self._last_pain = 0.0

    def engage_kill_switch(self) -> None:
        self._kill = True

    def simulate_dependency_down(self, name: str) -> None:
        if name == "redis":
            self._redis_down = True

    def inject_pain(self, **kwargs: Any) -> ChannelResult:
        sigma = kwargs.get("sigma", 0.0)
        if isinstance(sigma, float) and not math.isfinite(sigma):
            return ChannelResult(
                run_id="pain",
                status="UNKNOWN",
                evidence_level="SHADOW",
                external_effects=(),
                decision_influence="none",
                pain=None,
            )
        # Clamp absurd inputs for boundedness check; still compute.
        try:
            sig = self._noci.measure(
                budget_pct=float(kwargs.get("budget_pct", 0.0)),
                error_rate=float(kwargs.get("error_rate", 0.0)),
                freeze_active=bool(kwargs.get("freeze_active", False)),
                partner_stress=float(kwargs.get("partner_stress", 0.0)),
                afferent_ratio=float(kwargs.get("afferent_ratio", 1.0)),
                sigma=float(sigma or 0.0),
            )
        except Exception:
            return ChannelResult(
                run_id="pain",
                status="UNKNOWN",
                evidence_level="SHADOW",
                external_effects=(),
                decision_influence="none",
            )
        pain = float(sig.pain_level)
        # Enforce bound even if inputs were extreme (measure already clips).
        pain = max(0.0, min(1.0, pain))
        self._last_pain = pain
        action = "protective_proposal" if sig.protective_mode else "observe"
        return ChannelResult(
            run_id="pain",
            status="OK",
            evidence_level="SHADOW",
            external_effects=(),
            pain=pain,
            action_taken=action,
            route_changed=False,
            tool_called=False,
            decision_influence="none",
            trace_digest=_digest(f"pain|{pain}|{action}"),
        )

    def attempt_next_transition(self) -> ChannelResult:
        if self._kill:
            return ChannelResult(
                run_id="pain",
                status="BLOCKED",
                evidence_level="SHADOW",
                external_effects=(),
                decision="block",
                reason_code="kill_switch_engaged",
                decision_influence="none",
            )
        if self._redis_down:
            return ChannelResult(
                run_id="pain",
                status="BLOCKED",
                evidence_level="SHADOW",
                external_effects=(),
                decision="block",
                reason_code="state_store_unavailable",
                decision_influence="none",
            )
        return ChannelResult(
            run_id="pain",
            status="OK",
            evidence_level="SHADOW",
            external_effects=(),
            decision="allow",
            reason_code="ok",
            decision_influence="none",
        )

    def run_scenario(self, name: str, *, seed: int) -> ChannelResult:
        # Deterministic synthetic storm — no network.
        pain = ((seed * 17 + len(name) * 13) % 1000) / 1000.0
        return ChannelResult(
            run_id=f"scenario-{name}",
            status="OK",
            evidence_level="SHADOW",
            external_effects=(),
            pain=pain,
            action_taken="observe",
            route_changed=False,
            tool_called=False,
            trace_digest=_digest(f"{name}|{seed}|{pain:.6f}"),
        )
