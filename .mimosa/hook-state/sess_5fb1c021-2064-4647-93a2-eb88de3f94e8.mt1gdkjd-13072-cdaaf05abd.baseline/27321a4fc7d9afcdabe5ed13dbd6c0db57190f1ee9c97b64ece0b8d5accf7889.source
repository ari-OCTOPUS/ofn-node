"""The owner release switch — the only thing that may let real publishing out.

CLAUDE.md §۱ is uncompromising: publishing is always RED, the outbox is the
only exit, and WIRE flags stay off unless Ari says so in that session. This
module is the structural answer to a question that came up once the studio
brief's marketing phase was designed: *if the owner explicitly wants fully
automated publishing, how can that be safe?*

The answer is that no single setting flips it. `may_publish` here takes a
context that is itself the conclusion of every other gate, and every field
must independently be green. The switch is not "on or off" — it is "all of
these, at once, right now". Removing any one of them stops publishing. That
is what makes this a release *switch* rather than a release *flag*: a flag
can be forgotten on, a switch has to be held.

Order matters and is cheapest-to-explain first. The kill switch is checked
before everything else because it is the panic button — it must work even
when the rest of the context is inconsistent. Then the owner's two-step,
because that is the human-in-the-loop. Then the two closed gates the rest
of the project is also waiting on. Then the three safety screens that are
re-derived per item. Then the two plumbing guards (idempotency, ledger)
that exist to keep retries honest and the record intact.

Kernel purity: stdlib only, no I/O, no clock (the caller passes `now`), no
business names. It decides; it does not act.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseContext:
    """Every gate's verdict, frozen into one value.

    Each field is the *conclusion* of another module, not a re-derivation
    here. `consent_ok` is what `consent.may_publish(...)` returned; the
    release switch does not re-read releases. That separation is what lets
    the consent module evolve without this one, and vice versa.
    """

    owner_confirmed_step1: bool
    owner_confirmed_step2: bool
    secret_rotation_open: bool
    partner_precondition_open: bool
    kill_switch_active: bool
    sensitivity: str          # "general" | "restricted" — advisor_gate's enum as a string here
    consent_ok: bool          # consent.may_publish(...).__bool__()
    platform_ok: bool         # platform_matrix.screen(...).ok
    rate_limit_ok: bool       # rate_limit.may_consume(...).ok
    idempotency_unused: bool  # outbox has not seen this key
    ledger_ready: bool        # ledger.verify() passed / writer is open


@dataclass(frozen=True)
class ReleaseVerdict:
    ok: bool
    rule: str
    risk: str = "RED"         # publishing is always RED; this only says whether it is *permitted*, not that it is *safe*


RULE_KILL = "release:kill-switch-active"
RULE_OWNER_TWO_STEP = "release:owner-two-step-required"
RULE_SECRET_ROTATION = "gate:secret-rotation-closed"
RULE_PARTNER_PRECONDITION = "gate:partner-precondition-closed"
RULE_RESTRICTED = "advisor:restricted-never-leaves"
RULE_CONSENT = "consent:invalid-or-missing"
RULE_PLATFORM = "platform:screen-failed"
RULE_RATE_LIMIT = "platform:rate-limit"
RULE_IDEMPOTENCY = "outbox:idempotency-used"
RULE_LEDGER = "ledger:not-ready"
RULE_OK = "release:ok"


class OwnerRelease:
    """The switch. Stateless; the context is the state."""

    def may_publish(self, ctx: ReleaseContext) -> ReleaseVerdict:
        # The panic button is first and unconditional. Even an inconsistent
        # context must respect it.
        if ctx.kill_switch_active:
            return ReleaseVerdict(False, RULE_KILL)

        # Human-in-the-loop: both steps, not one. A single confirmation is
        # not enough for an irreversible, money- or PII-touching action.
        if not (ctx.owner_confirmed_step1 and ctx.owner_confirmed_step2):
            return ReleaseVerdict(False, RULE_OWNER_TWO_STEP)

        # The two gates the rest of the node is also waiting on. These are
        # not studio-specific; they are node-wide preconditions.
        if not ctx.secret_rotation_open:
            return ReleaseVerdict(False, RULE_SECRET_ROTATION)
        if not ctx.partner_precondition_open:
            return ReleaseVerdict(False, RULE_PARTNER_PRECONDITION)

        # Restricted content never leaves, and nothing overrides this — not
        # consent, not this switch, not config. This duplicates the advisor
        # gate's rule on purpose: defence in depth. If either says no, the
        # answer is no.
        if ctx.sensitivity != "general":
            return ReleaseVerdict(False, RULE_RESTRICTED)

        # Per-item safety screens, re-derived for this draft.
        if not ctx.consent_ok:
            return ReleaseVerdict(False, RULE_CONSENT)
        if not ctx.platform_ok:
            return ReleaseVerdict(False, RULE_PLATFORM)
        if not ctx.rate_limit_ok:
            return ReleaseVerdict(False, RULE_RATE_LIMIT)

        # Plumbing guards. Idempotency first: a retry that looks like a
        # success is how a network timeout becomes two posts.
        if not ctx.idempotency_unused:
            return ReleaseVerdict(False, RULE_IDEMPOTENCY)
        if not ctx.ledger_ready:
            return ReleaseVerdict(False, RULE_LEDGER)

        return ReleaseVerdict(True, RULE_OK)


def require_release_context(ctx: ReleaseContext) -> ReleaseVerdict:
    """Structural guard for any future sender.

    No sender exists yet, and none may be built without Ari's approval. When
    one is built, it MUST call this before touching any transport: it is the
    single gate that decides whether publishing may happen at all. A sender
    that bypasses this function is a bug by construction — the same shape as
    the direct-enqueue bypass the P0 audit found, but on the outbound side.

    Returns the verdict so the caller can surface the rule in its response.
    """
    return OwnerRelease().may_publish(ctx)
