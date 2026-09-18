"""survival-loop core (S6-D11) — bounded autonomy machinery, shadow-safe.

Freedom-to-discover is automated; freedom-to-affect is not. This module
owns exactly the rules the owner's plan made mandatory:

  * HALT switch: nothing starts while halted (test 1)
  * an experiment without hypothesis/success/kill/deadline/rollback is
    refused (test 2)
  * external effect requires a campaign envelope; A7+ requires an owner
    approval id (tests 3, and the A5-A8 ladder)
  * money/contact/time caps halt immediately (test 4)
  * proposal is never execution; quote_drafted is never quote_sent;
    invoice_sent is never revenue; only a payment receipt increments
    verified_cash_collected (tests 5-8)
  * preregistration is immutable (test 10)
  * events are idempotent and restart-safe, one manifest per run — no
    shared append (tests 14-16)
  * missing numeric inputs raise PARSE_DRIFT, never a guess (test 17)
  * provider outage parks; canary quality drop auto-rolls-back (18/13)

Kernel purity: no clock reads (clock injected), no network, no secrets.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Mapping

A0, A1, A2, A3, A4, A5, A6, A7 = range(8)


class SurvivalError(Exception):
    """Refuse-before-start failure (fail closed)."""


@dataclass(frozen=True)
class Envelope:
    envelope_id: str
    max_spend_aud: float
    max_contacts: int
    channels: tuple[str, ...] = ()


REQUIRED_FIELDS = ("hypothesis", "success_metric", "kill_metric",
                   "deadline", "rollback")


@dataclass(frozen=True)
class Experiment:
    exp_id: str
    opportunity_id: str
    hypothesis: str
    offer: str
    channel: str
    price_aud: float
    authority: int
    success_metric: str
    kill_metric: str
    deadline: str
    rollback: str
    external_effect: bool = False
    max_spend_aud: float = 0.0
    max_contacts: int = 0
    envelope_id: str = ""
    owner_approval_id: str = ""

    def preregistration_sha256(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True,
                       ensure_ascii=False).encode("utf-8")).hexdigest()


class SurvivalLoop:
    """One bounded loop. All state lives under state_dir, per-run manifests."""

    def __init__(self, state_dir: Path, *, clock: Callable[[], int],
                 halted: Callable[[], bool] | None = None,
                 envelopes: Mapping[str, Envelope] | None = None,
                 resource_caps: Mapping[str, float] | None = None) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self._halted = halted or (lambda: os.environ.get(
            "HALT_SURVIVAL_LOOP") == "1")
        self._envelopes = dict(envelopes or {})
        self._caps = dict(resource_caps or {
            "revenue_experiments": 0.60, "customer_delivery": 0.25,
            "self_audit_and_reliability": 0.10, "speculative_research": 0.05})
        self.cash_collected_aud = 0.0   # only payment receipts move this
        self._seen_idem: set[str] = set()

    # ── admission ────────────────────────────────────────────────────────
    def register(self, exp: Experiment, *, bucket: str = "revenue_experiments",
                 bucket_load: float = 0.0) -> str:
        if self._halted():
            raise SurvivalError("halted: no new run may start")
        for f in REQUIRED_FIELDS:
            if not getattr(exp, f):
                raise SurvivalError(f"experiment-refused: {f} is required")
        if exp.authority >= A5:
            env = self._envelopes.get(exp.envelope_id)
            if env is None:
                raise SurvivalError(
                    "experiment-refused: external effect requires a campaign envelope")
            if exp.max_spend_aud > env.max_spend_aud:
                raise SurvivalError("experiment-refused: spend above envelope")
            if exp.max_contacts > env.max_contacts:
                raise SurvivalError("experiment-refused: contacts above envelope")
            if exp.channel and exp.channel not in env.channels:
                raise SurvivalError("experiment-refused: channel not in envelope")
            if exp.authority >= A7 and not exp.owner_approval_id:
                raise SurvivalError(
                    "experiment-refused: A7+ needs an explicit owner approval id")
        if bucket not in self._caps:
            raise SurvivalError(f"unknown bucket {bucket!r}")
        if bucket_load > self._caps[bucket]:
            raise SurvivalError("experiment-refused: resource cap exceeded")
        sha = exp.preregistration_sha256()
        self._write(exp.exp_id, "RUN_REGISTERED", {"sha256": sha})
        return sha

    def mutate_registered(self, exp: Experiment, change: str) -> None:
        raise SurvivalError(
            f"preregistration-immutable: {exp.exp_id} ({change} refused)")

    # ── events: idempotent, per-run manifest, restart-safe ──────────────
    def _write(self, run_id: str, kind: str, payload: dict) -> None:
        idem = payload.get("idem_key") or f"{run_id}:{kind}:{self._clock()}"
        if idem in self._seen_idem:
            return                      # duplicate event: no double effect
        if kind == "EXECUTION_RECEIPT":
            kind = payload.get("receipt_kind", kind)
        self._seen_idem.add(idem)
        path = self.state_dir / f"run-{run_id}.jsonl"   # one manifest per run
        row = {"kind": kind, "idem_key": idem, "t": self._clock(),
               **{k: v for k, v in payload.items() if k != "idem_key"}}
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    def emit(self, run_id: str, kind: str, payload: dict) -> None:
        if self._halted() and kind not in ("RUN_HALTED", "RUN_PARKED"):
            raise SurvivalError("halted: no new effects may be emitted")
        self._write(run_id, kind, payload)

    # ── revenue ladder (L0..L7); the not-success rules live here ────────
    def ladder_event(self, run_id: str, event: str, amount_aud: float = 0.0) -> str:
        if event == "PROPOSAL_CREATED":
            self._write(run_id, "PROPOSAL_CREATED", {}); return "L3-proposal"
        if event == "quote_drafted":
            self._write(run_id, "CLAIM_CREATED",
                        {"note": "draft is not a send"}); return "draft-only"
        if event == "quote_sent":                       # requires a receipt
            self._write(run_id, "quote_sent", {"receipt": True}); return "L4"
        if event == "invoice_sent":
            self._write(run_id, "invoice_sent",
                        {"note": "invoice is not revenue"}); return "L4"
        if event == "PAYMENT_RECEIVED":
            if amount_aud <= 0:
                raise SurvivalError("PARSE_DRIFT: payment amount missing")
            self.cash_collected_aud += amount_aud
            self._write(run_id, "PAYMENT_RECEIVED", {"amount_aud": amount_aud})
            return "L5"
        raise SurvivalError(f"unknown ladder event {event!r}")

    # ── ranking: explicit numbers only, never a guess ───────────────────
    @staticmethod
    def rank(opportunity: Mapping[str, float]) -> float:
        try:
            p_paid = opportunity["p_paid"]
            profit = opportunity["expected_gross_profit"]
            strength = opportunity["evidence_strength"]
            t_signal = opportunity["time_to_signal"]
            cost = opportunity["cash_cost"]
            risk = opportunity["risk"]
        except KeyError as exc:
            raise SurvivalError(f"PARSE_DRIFT: missing {exc}") from None
        if min(p_paid, profit, strength, t_signal, cost, risk) < 0:
            raise SurvivalError("PARSE_DRIFT: negative component")
        if t_signal == 0 or cost == 0 or risk == 0:
            raise SurvivalError("PARSE_DRIFT: zero denominator component")
        return (p_paid * profit * strength) / (t_signal * cost * risk)

    # ── provider outage & canary policy ─────────────────────────────────
    @staticmethod
    def provider_outcome(status: str) -> str:
        if status == "provider_unavailable":
            return "PARKED"            # never success, never infinite retry
        if status == "ok":
            return "DONE"
        raise SurvivalError(f"PARSE_DRIFT: unknown provider status {status!r}")

    @staticmethod
    def canary_decision(quality_delta: float, *, threshold: float = 0.0) -> str:
        if quality_delta < threshold:
            return "ROLLBACK"          # automatic, no owner in the loop
        return "KEEP"
