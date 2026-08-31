"""The Model Router: wires the routing policy to real brains.

Every call out of the node goes through `ModelRouter.ask()`, which does, in
this order and no other:

    1. scrub the prompt                 nothing identifying leaves, ever
    2. check the quota                  before spending, not after
    3. call the rung                    starting at the cheapest
    4. record the spend                  with the invisible-token multiplier
    5. escalate only if asked            and only within policy

Step 1 comes first so that even a rejected request has already been stripped —
a prompt that never leaves is still a prompt that was assembled, and the habit
of assembling clean prompts is what survives refactoring.

Step 4 records *before* returning. A crash between the call and the
bookkeeping would otherwise give back free tokens on the next boot, which is
the failure mode that turns a budget into a suggestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Protocol, Sequence

from ..kernel.domain import TenantId, TokenSpend
from ..kernel.errors import FailClosedError
from ..kernel.quota import NodeQuota
from ..kernel.routing import (
    RouteDecision, RouteRequest, Rung, may_escalate, start_rung, token_estimate,
)
from ..kernel.scrub import ScrubResult, scrub


@dataclass(frozen=True)
class BrainReply:
    """What a rung returns.

    `insufficient` is the only thing that authorises spending more money, so
    it is a deliberate, explicit field rather than something inferred from the
    length or shape of `text`. A brain that is merely brief has not asked for
    help.
    """

    text: str
    insufficient: bool = False
    visible_tokens: int = 0
    orchestration_tokens: int = 0
    # What actually answered, taken from the provider's own response where it
    # says so. NOT the name we asked for — see `requested`.
    model: str = ""
    # What we asked for. Kept beside the answer so the two can be compared:
    # an endpoint that remaps, substitutes or silently serves something else
    # is otherwise invisible, and every provenance claim in this project
    # rests on the recorded name being the one that replied.
    requested: str = ""

    @property
    def model_matched_request(self) -> bool | None:
        """None when the provider did not say. Unknown is not agreement."""
        if not self.model or not self.requested:
            return None
        return self.model.split(":")[0] == self.requested


class Brain(Protocol):
    def answer(self, task: str, prompt: str) -> BrainReply: ...


@dataclass
class RouterResult:
    text: str
    rung: Rung | None
    path: tuple[str, ...] = ()
    spend: int = 0
    scrubbed: ScrubResult | None = None
    refused: str = ""
    # The machine-readable rule behind a refusal, when there is one — the
    # quota's rule name or the routing policy's. The worker uses this to
    # tell a deterministic denial (retrying cannot help) from a transient
    # one (retrying is the only thing that can).
    refused_code: str = ""
    # What the last rung said it was, per the provider's own response —
    # "fugu:http-401", "fugu:unreachable", "fugu:no-choice". A parked job
    # whose only explanation is "capped" hides whether the provider was
    # refusing, unreachable, or returning shapes nobody parsed.
    provider_note: str = ""

    @property
    def ok(self) -> bool:
        return not self.refused


class ModelRouter:
    """Cheapest-first routing with a hard budget and no implicit escalation."""

    def __init__(
        self,
        brains: Mapping[Rung, Brain],
        quota: NodeQuota,
        *,
        on_event: Callable[[str, Mapping[str, object]], None] | None = None,
    ) -> None:
        if Rung.RULES not in brains:
            raise FailClosedError("a rules rung is required — the router must "
                                  "always have a free path that cannot fail open")
        self._brains = dict(brains)
        self._quota = quota
        self._on_event = on_event

    def _emit(self, kind: str, payload: Mapping[str, object]) -> None:
        if self._on_event is not None:
            self._on_event(kind, payload)

    def ask(
        self,
        tenant: TenantId,
        req: RouteRequest,
        prompt: str,
        *,
        now_epoch_s: int,
    ) -> RouterResult:
        """Answer `prompt`, spending as little as policy allows."""
        cleaned = scrub(prompt)
        if not cleaned.clean:
            self._emit("SCRUB", {"tenant": tenant.value,
                                 "findings": dict(cleaned.findings)})

        decision = start_rung(req)
        if not decision.allowed or decision.rung is None:
            return RouterResult("", None, refused=decision.reason,
                                refused_code=decision.rule,
                                scrubbed=cleaned)

        rung = decision.rung
        path: list[str] = []
        total_spend = 0
        last_text = ""
        last_model_note = ""

        while True:
            if rung not in self._brains:
                # A missing rung is not an error to route around — routing
                # around it is exactly how a cheap tier silently becomes a
                # paid one.
                reply = BrainReply(text="", insufficient=True)
                path.append(f"{rung.value}:absent")
            else:
                gate = self._charge(tenant, req, rung, now_epoch_s)
                if not gate.allowed:
                    return RouterResult(last_text, rung, tuple(path),
                                        total_spend, cleaned,
                                        refused=gate.reason,
                                        refused_code=gate.rule,
                                        provider_note=last_model_note)
                reply = self._brains[rung].answer(req.task, cleaned.text)
                spent = self._record(tenant, rung, reply, now_epoch_s)
                total_spend += spent
                if reply.insufficient:
                    last_model_note = reply.model
                path.append(f"{rung.value}:{'insufficient' if reply.insufficient else 'ok'}")
                if reply.text:
                    last_text = reply.text
                if not reply.insufficient:
                    return RouterResult(reply.text, rung, tuple(path),
                                        total_spend, cleaned)

            step = may_escalate(rung, req,
                                lower_reported_insufficient=reply.insufficient)
            if not step.allowed or step.rung is None:
                return RouterResult(last_text, rung, tuple(path), total_spend,
                                    cleaned,
                                    refused=("" if last_text else step.reason),
                                    refused_code=("" if last_text
                                                  else step.rule),
                                    provider_note=("" if last_text
                                                   else last_model_note))
            self._emit("ESCALATE", {"tenant": tenant.value,
                                    "from": rung.value, "to": step.rung.value,
                                    "reason": step.reason})
            rung = step.rung

    # ── money ─────────────────────────────────────────────────────────────
    def _charge(self, tenant: TenantId, req: RouteRequest, rung: Rung,
                now_epoch_s: int) -> RouteDecision:
        """Admission for one rung, judged on billed cost."""
        est = token_estimate(req, rung)
        if est <= 0:
            return RouteDecision(rung, True, "free rung", rule="route:free")
        d = self._quota.check(tenant, est, now_epoch_s)
        if not d.allowed:
            self._emit("QUOTA_DENY", {"tenant": tenant.value,
                                      "rung": rung.value, "reason": d.reason})
            return RouteDecision(None, False, d.reason, rule=d.rule)
        return RouteDecision(rung, True, "within quota", rule="route:quota-ok")

    def _record(self, tenant: TenantId, rung: Rung, reply: BrainReply,
                now_epoch_s: int) -> int:
        """Book the spend immediately, before the answer is handed back."""
        if not rung.costs_quota() or reply.visible_tokens <= 0:
            return 0
        spend = TokenSpend(visible=reply.visible_tokens,
                           orchestration=reply.orchestration_tokens)
        cost = self._quota.record(tenant, spend, now_epoch_s)
        self._emit("SPEND", {
            "tenant": tenant.value, "rung": rung.value, "model": reply.model,
            # Recorded whenever the provider named something other than what
            # was asked for. Absent means they agreed; it is never absent
            # because nobody looked.
            **({"requested_model": reply.requested}
               if reply.model_matched_request is False else {}),
            "visible": reply.visible_tokens,
            "orchestration_reported": reply.orchestration_tokens,
            "billed": cost,
        })
        return cost


# ── a rules rung that always exists ──────────────────────────────────────
class RulesBrain:
    """Deterministic answers. Zero tokens, zero latency, fully auditable.

    Most of what this node does — classifying an inbound message, checking a
    service radius, deciding whether capacity remains — is a lookup, not a
    judgement. Routing those through a model would be slower, costlier, and
    less explainable than a dictionary.
    """

    def __init__(self, handlers: Mapping[str, Callable[[str], str | None]]) -> None:
        self._handlers = dict(handlers)

    def answer(self, task: str, prompt: str) -> BrainReply:
        handler = self._handlers.get(task)
        if handler is None:
            return BrainReply("", insufficient=True)
        out = handler(prompt)
        if out is None:
            return BrainReply("", insufficient=True)
        return BrainReply(out, insufficient=False, model="rules")
