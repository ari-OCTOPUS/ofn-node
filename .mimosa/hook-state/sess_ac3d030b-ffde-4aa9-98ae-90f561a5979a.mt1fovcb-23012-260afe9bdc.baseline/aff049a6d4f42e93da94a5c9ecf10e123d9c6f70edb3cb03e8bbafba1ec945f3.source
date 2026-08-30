#!/usr/bin/env python3
"""box.py — B0 Box-of-Agents glue: یک میکرو‌جهانِ بستهٔ عددی.

Box = collection of agents + Warden + Archivist + topology + sensors.
تنها خروجی: propose-only metrics/hypotheses. هرگز action/effector/money.
هیچ import از *_gate/chrono/money/genome production."""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from agent_state import AgentState, PsychState, CognitiveState, Energy, clip01
from dynamics import f_cognitive, u_psych, h_memory, global_mood, g_message
from archivist import Archivist, MemoryEntry
from topology import build_topology, Topology
from warden import Warden
from sensors import rho_jacobian, mutual_info, neuralness_score, contradiction_rate


@dataclass
class BoxConfig:
    """پیکربندیِ Box. همه از بیرون set می‌شوند (propose-only config)."""
    E_total: float = 100000.0
    box_fraction: float = 0.02
    memory_cap: int = 50
    k_shortcuts: int = 2
    rho_max: float = 0.98
    max_depth: int = 2
    seed: int = 42


class Box:
    """میکرو‌جهانِ بسته. فقط عدد، $0، sandbox.

    lifecycle: run_tick() یک گام. Warden can_continue() چک می‌کند.
    خروجی: metrics (propose-only). هیچ اثرِ بیرونی."""

    def __init__(self, config: BoxConfig | None = None,
                 agents: list[AgentState] | None = None,
                 warden: Warden | None = None):
        self.config = config or BoxConfig()
        self.agents = agents or self._default_roster()
        self.warden = warden or Warden(
            E_total=self.config.E_total,
            box_fraction=self.config.box_fraction,
            rho_max=self.config.rho_max)
        self.archivist = Archivist(cap=self.config.memory_cap)
        self.memory: list[dict] = []
        self.topology = build_topology(
            [a.role for a in self.agents], self.config.k_shortcuts)
        self.tick_count = 0
        self.rng = random.Random(self.config.seed)
        self.last_rho = 0.5
        self.metrics_history: list[dict] = []

    def _default_roster(self) -> list[AgentState]:
        """راسترِ پایه: Warden + Archivist + Dreamer + Skeptic + Integrator + null."""
        roles = ["Warden", "Archivist", "Dreamer", "Skeptic", "Integrator", "null-dreamer"]
        return [AgentState(agent_id=f"{r.lower()}-0", role=r) for r in roles]

    @property
    def G_t(self) -> dict:
        return global_mood(self.agents)

    def run_tick(self, trace: dict | None = None) -> dict | None:
        """یک گامِ کامل. Warden اول چک می‌کند. اگر deny → None (cycle ended).
        خروجی: metrics snapshot (propose-only)."""
        self.tick_count += 1
        # Warden master gate
        can_go, reason = self.warden.can_continue(self.agents, self.last_rho)
        if not can_go:
            return {"cycle_ended": True, "reason": reason, "tick": self.tick_count}

        t = trace or {}
        load = t.get("errors_24h", 0) / 10.0
        novelty = self.rng.random() * 0.3
        recovery = 0.2
        M_summary = self.archivist.summary_vec()

        all_states = []
        new_msgs = []
        for a in self.agents:
            if a.lifecycle_status in ("quarantined", "idle"):
                continue
            # cognitive update
            a.cognitive.hidden_state = f_cognitive(a.cognitive.hidden_state, M_summary)
            # psych update
            u_psych(a.psych, load=load, recovery=recovery,
                    novelty=novelty, alignment=0.6, distraction=0.1,
                    consistency=0.7, contradiction=0.2)
            a.tick_psych_clip()
            # message
            msg = g_message(a.cognitive.hidden_state, a.psych, M_summary,
                            noise=self.rng.random() * 0.1)
            msg["agent_id"] = a.agent_id
            msg["ts"] = self.tick_count
            new_msgs.append(msg)
            a.metrics.messages_sent += 1
            all_states.extend(a.cognitive.hidden_state + a.psych.as_vector())

        # memory update
        self.memory = h_memory(self.memory, new_msgs, cap=self.config.memory_cap)
        for m in new_msgs:
            self.archivist.append(MemoryEntry(
                topic=m["agent_id"], summary_vec=m.get("content_vec", [0]),
                score=m.get("score", 0.5), ts=m["ts"]))

        # sensors: ρ(J)
        if len(all_states) >= 2:
            from sensors import estimate_jacobian
            # split به sub-sequences برای Jacobian
            half = len(all_states) // 2
            seq = [all_states[:half], all_states[half:]]
            J = estimate_jacobian(seq)
            from sensors import rho_jacobian
            self.last_rho = rho_jacobian(J)

        # safety check
        flagged = self.warden.check_safety(self.agents)

        # metrics snapshot (propose-only)
        snap = {
            "tick": self.tick_count,
            "G_t": self.G_t["G"],
            "mean_stress": self.G_t["mean_stress"],
            "mean_coherence": self.G_t["mean_coherence"],
            "rho_J": round(self.last_rho, 4),
            "memory_size": self.archivist.size,
            "budget_used": self.warden.tokens_spent_total,
            "budget_max": self.warden.E_box_max,
            "edge_count": self.topology.edge_count(),
            "is_full_mesh": self.topology.is_full_mesh(),
            "agents_active": sum(1 for a in self.agents if a.lifecycle_status == "active"),
            "flagged": flagged,
        }
        self.metrics_history.append(snap)
        return snap

    def run_episode(self, n_ticks: int = 10, trace: dict | None = None) -> list[dict]:
        """n_ticks گام. توقف اگر Warden deny کند."""
        snaps = []
        for _ in range(n_ticks):
            s = self.run_tick(trace=trace)
            if s is None:
                break
            snaps.append(s)
            if s.get("cycle_ended"):
                break
        return snaps
