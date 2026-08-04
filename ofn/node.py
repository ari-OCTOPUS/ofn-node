"""The Node: one object that wires the kernel to the adapters.

This is the only place that knows about every layer at once, and it is
deliberately thin. It holds no policy — every decision it makes is delegated
to the kernel, and every side effect goes through an adapter. If a rule ever
appears in this file, it belongs somewhere else.

What it does own is the *sequence*: an answer from a partner becomes a fact,
then a ledger entry, then possibly a decision for the owner. Getting that
sequence wrong is how a system ends up with a fact nobody can explain, or a
ledger that disagrees with the state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from .adapters.boot import BootReport, closed_gates_for
from .adapters.facts import FactStore
from .adapters.ledger import Ledger
from .adapters.outbox import Outbox
from .adapters.products import (ProductError, ProductStore, money_view,
                                net_margin_aud, verdicts)
from .kernel.domain import (
    Action, Confidence, Decision, PackSpec, RiskTier, TenantId,
)
from .kernel.gates import admit, executable
from .kernel.questions import Question, plan, readiness
from .kernel.quota import NodeQuota
from .kernel.tenancy import TenantRegistry, TenantScope


MAX_TEXT_ANSWER = 2000

# Persian and Arabic-Indic digits, in the order 0-9. A phone keyboard set to
# Persian produces ۱۲۵, and a form that silently refuses it is a form that
# blames the partner for using her own language.
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

# `labour_hours` and `hourly_rate_aud` are deliberately absent: the two
# questions behind them were removed, so the API no longer accepts them. The
# columns stay in the file — dropping one rewrites the table, and an unread
# column costs nothing — but nothing writes them again.
_PRODUCT_NUMERIC = ("materials_cost_aud", "packaging_cost_aud",
                    "price_primary_aud", "price_secondary_aud")
_PRODUCT_NULLABLE = {"price_primary_aud", "price_secondary_aud"}


def _normalise_numbers(body: Mapping[str, object]) -> dict:
    """Accept ۱۲۵ and 125 and "125" as the same number.

    Done at the boundary rather than in the shell so that the rule holds for
    every caller, and only for fields that are numbers anyway — a name
    containing digits is left exactly as she typed it.
    """
    out = dict(body)
    for key in _PRODUCT_NUMERIC:
        raw = out.get(key)
        if not isinstance(raw, str):
            continue
        text = raw.translate(_DIGITS).replace(",", "").replace("٬", "").strip()
        if not text:
            out[key] = None if key in _PRODUCT_NULLABLE else 0.0
            continue
        try:
            out[key] = float(text)
        except ValueError:
            pass          # leave it; the store refuses it with a clear message
    return out


def _rejects(meta: Mapping[str, object], value: object) -> str | None:
    """Why this answer is not acceptable, or None if it is.

    The pack states the range a number may take and the set a choice may come
    from. Not enforcing that here would make those declarations decorative:
    the endpoint is reachable by anyone holding a partner session, and a
    capacity of one billion is a promise the business cannot keep, written
    into the fact store as owner-confirmed truth.
    """
    options = meta.get("options")
    if options:
        if str(value) not in [str(o) for o in options]:
            return "value is not one of the offered choices"
        return None

    low, high = meta.get("min"), meta.get("max")
    if low is not None or high is not None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "this question expects a number"
        if low is not None and value < low:
            return f"value is below the minimum of {low}"
        if high is not None and value > high:
            return f"value is above the maximum of {high}"
        return None

    if isinstance(value, str) and len(value) > MAX_TEXT_ANSWER:
        return "answer is too long"
    return None


@dataclass
class Node:
    registry: TenantRegistry
    quota: NodeQuota
    ledger: Ledger
    facts: FactStore
    outbox: Outbox
    now_epoch_s: Callable[[], int]
    now_iso: Callable[[], str]
    base_closed_gates: tuple[str, ...] = ()
    boot: BootReport | None = None
    killed: bool = False
    products: ProductStore | None = None

    # ── gates ─────────────────────────────────────────────────────────────
    @property
    def closed_gates(self) -> tuple[str, ...]:
        """Base gates plus anything this boot added (e.g. SAFE MODE)."""
        if self.boot is None:
            return self.base_closed_gates
        return closed_gates_for(self.boot, self.base_closed_gates)

    def evidence_for(self, scope: TenantScope) -> Mapping[str, Confidence]:
        pack = self.registry.pack(scope.tenant)
        return self.facts.evidence(scope, list(pack.required_facts))

    # ── partner surface ───────────────────────────────────────────────────
    def questions_for(self, scope: TenantScope, user_id: str) -> list[dict]:
        """What this partner should be asked, as plain JSON for the shell.

        The kernel decides *which* facts are missing; the pack supplies the
        sentence a person reads. They are merged here rather than in the shell
        so that a question and its wording cannot drift apart across four
        separately-edited HTML files.
        """
        pack = self.registry.pack(scope.tenant)
        qs: Sequence[Question] = plan(pack, self.evidence_for(scope))
        out: list[dict] = []
        for q in qs:
            meta = dict(pack.question_meta.get(q.key, {}))
            kind = q.kind.value
            # Wording wins over inference: a fact the naming rule reads as a
            # number is a choice the moment the pack lists options for it.
            if meta.get("options"):
                kind = "choice"
            item = {
                "key": q.key,
                "kind": kind,
                "why": q.why,
                "missing": q.is_missing,
                "current": q.have.value if q.have else None,
                # Falls back to the key so a partner is never shown a blank
                # card — ugly beats invisible.
                "label": meta.get("label") or q.key,
                "has_label": "label" in meta,
            }
            for extra in ("hint", "unit", "options", "min", "max", "default",
                          "placeholder"):
                if extra in meta:
                    item[extra] = meta[extra]
            out.append(item)
        return out

    def status_for(self, scope: TenantScope) -> dict:
        """Everything a mini-app needs for its first frame. Local reads only."""
        pack = self.registry.pack(scope.tenant)
        done, total = readiness(pack, self.evidence_for(scope))
        counts = self.outbox.counts(scope)
        return {
            "tenant": scope.tenant.value,
            "capacity_per_week": pack.capacity_units_per_week,
            "readiness": {"done": done, "total": total},
            "pending_decisions": counts.get("pending", 0),
            "held": counts.get("held", 0),
            "safe_mode": "safe_mode" in self.closed_gates,
            # `time.hourly_floor` used to travel here to pre-fill the hourly
            # rate field. That question is gone, and so is this.
            "facts": {k: v for k, v in (
                ("sales.days_before_worry",
                 self._fact_value(scope, "sales", "days_before_worry")),
            ) if v is not None},
        }

    def _fact_value(self, scope: TenantScope, subject: str, predicate: str):
        fact = self.facts.current(scope, subject, predicate)
        return None if fact is None else fact.value

    # ── products ──────────────────────────────────────────────────────────
    def _pieces(self) -> ProductStore:
        if self.products is None:
            raise ProductError("انبار محصولات در دسترس نیست")
        return self.products

    def _stale_after(self, scope: TenantScope) -> int | None:
        """How long is too long — her answer, or nothing.

        The pack no longer carries a number for this. Ninety days was a
        guess, and a guess that paints a warning on her work is worse than
        no warning: she learns the flag is noise and stops reading it.
        """
        raw = self._fact_value(scope, "sales", "days_before_worry")
        try:
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    def _gst(self, scope: TenantScope, pack: PackSpec) -> tuple[bool, float]:
        """(known, rate) for this business — from her answer, not a setting.

        The market's rate lives in the locale. Whether this business charges
        it is asked, because getting it wrong moves every margin by about the
        width of the band between healthy and losing money.
        """
        raw = self._fact_value(scope, "business", "gst_registered")
        if raw is None:
            return False, 0.0
        registered = str(raw).strip() in ("بله", "yes", "true", "True", "1")
        return True, (pack.locale.tax_rate if registered else 0.0)

    def _decorated(self, pack: PackSpec, p, today: str,
                   stale_after: int | None,
                   gst: tuple[bool, float] = (False, 0.0)) -> dict:
        """One piece as the shell reads it: the row, plus what it means.

        The verdicts are computed here rather than in the shell so that the
        panel, the list and any export all say the same thing about the same
        piece. A rule duplicated in a template is a rule that will disagree
        with itself.
        """
        out = p.as_dict(today)
        known, rate = gst
        view = money_view(p, gst_rate=rate, gst_known=known)
        # One computation, one answer. The screen, the export and the verdict
        # all read these, so they cannot drift apart.
        out.update(view)
        out["verdicts"] = list(verdicts(
            p, today, stale_after_days=stale_after,
            quick_sale_days=pack.quick_sale_days,
            loses_money=view["loses_money"]))
        try:
            out["net_margin_aud"] = net_margin_aud(p, pack.channel_fees)
        except ProductError as exc:
            # A sold piece on a channel whose fee nobody has configured. Say
            # so instead of printing a margin the business does not keep.
            out["net_margin_aud"] = None
            out["net_margin_blocked"] = str(exc)
        return out

    def products_for(self, scope: TenantScope) -> dict:
        pack = self.registry.pack(scope.tenant)
        today = self.now_iso()[:10]
        stale_after = self._stale_after(scope)
        gst = self._gst(scope, pack)
        rows = [self._decorated(pack, p, today, stale_after, gst)
                for p in self._pieces().list(scope.tenant.value)]
        return {"products": rows, "currency": pack.locale.currency.code,
                "symbol": pack.locale.currency.symbol,
                "gst_known": gst[0], "gst_rate": gst[1]}

    def create_product(self, scope: TenantScope, user_id: str,
                       body: Mapping[str, object]) -> dict:
        pack = self.registry.pack(scope.tenant)
        fields = _normalise_numbers(body)
        try:
            piece = self._pieces().create(
                scope.tenant.value, pack.sku_prefix, fields,
                now_iso=self.now_iso())
        except ProductError as exc:
            return {"ok": False, "error": str(exc)}
        self.ledger.append(scope, "PRODUCT_CREATED", {
            "sku": piece.sku, "name": piece.name,
            "cogs_aud": piece.cogs_aud,
            "price_primary_aud": piece.price_primary_aud,
            "price_secondary_aud": piece.price_secondary_aud,
            "actor": f"partner:{user_id}",
        }, self.now_iso())
        return {"ok": True,
                "product": self._decorated(pack, piece, self.now_iso()[:10],
                                           self._stale_after(scope),
                                           self._gst(scope, pack))}

    def update_product(self, scope: TenantScope, user_id: str, sku: str,
                       body: Mapping[str, object]) -> dict:
        pack = self.registry.pack(scope.tenant)
        changes = _normalise_numbers(body)
        try:
            before, after = self._pieces().update(
                scope.tenant.value, sku, changes, now_iso=self.now_iso())
        except ProductError as exc:
            return {"ok": False, "error": str(exc)}

        # Only what actually moved. A ledger entry restating twenty unchanged
        # fields buries the one that changed.
        moved = {k: {"before": getattr(before, k), "after": getattr(after, k)}
                 for k in after.__dataclass_fields__
                 if getattr(before, k) != getattr(after, k) and k != "updated_at"}
        self.ledger.append(scope, "PRODUCT_UPDATED", {
            "sku": sku, "changed": moved, "actor": f"partner:{user_id}",
        }, self.now_iso())
        return {"ok": True,
                "product": self._decorated(pack, after, self.now_iso()[:10],
                                           self._stale_after(scope),
                                           self._gst(scope, pack))}

    def submit_answer(self, scope: TenantScope, user_id: str,
                      body: Mapping[str, object]) -> dict:
        """Record a partner's answer as a fact, then ledger it.

        The fact is written first and the ledger entry second, on purpose: a
        crash between them leaves a fact whose provenance is thin, which is
        recoverable. The reverse order would leave a ledger claiming a fact
        that does not exist, which is a lie in the audit trail.

        Confidence is `OWNER_CONFIRMED` because a partner *is* the authority
        for their own business — this is the one path where a human statement
        becomes ground truth rather than an input to be verified.
        """
        key = str(body.get("key", ""))
        if "." not in key:
            return {"ok": False, "error": "unknown question"}
        pack = self.registry.pack(scope.tenant)
        if key not in pack.required_facts:
            # Only questions the pack actually asked may be answered. Without
            # this, the endpoint is a way to write arbitrary facts.
            return {"ok": False, "error": "unknown question"}
        if "value" not in body:
            return {"ok": False, "error": "no value"}

        bad = _rejects(pack.question_meta.get(key, {}), body["value"])
        if bad:
            return {"ok": False, "error": bad}

        subject, _, predicate = key.partition(".")
        now = self.now_iso()
        fact = self.facts.assert_fact(
            scope, subject, predicate, body["value"],
            Confidence.OWNER_CONFIRMED, observed_at=now,
            source=f"partner:{user_id}")
        self.ledger.append(scope, "FACT", {
            "key": key, "value": body["value"], "fact_id": fact.id,
            "confidence": Confidence.OWNER_CONFIRMED.value,
            "source": f"partner:{user_id}",
        }, now)

        done, total = readiness(pack, self.evidence_for(scope))
        return {"ok": True, "key": key,
                "readiness": {"done": done, "total": total},
                "remaining": self.questions_for(scope, user_id)}

    # ── decisions ─────────────────────────────────────────────────────────
    def propose(self, scope: TenantScope, action: Action,
                payload: Mapping[str, object], idem_key: str) -> Decision:
        """Judge an action and, if it needs a human, queue it.

        GREEN never reaches the outbox: it has already run. Only things that
        need a finger are queued, so the owner's list is exactly the set of
        things waiting on them and nothing else.
        """
        pack = self.registry.pack(scope.tenant)
        d = admit(action, pack, self.quota,
                  now_epoch_s=self.now_epoch_s(), killed=self.killed,
                  closed_gates=self.closed_gates)
        now = self.now_iso()
        self.ledger.append(scope, "PROPOSE", {
            "action": action.name, "allowed": d.allowed,
            "tier": d.tier.value, "rule": d.rule, "reason": d.reason,
        }, now)
        if d.allowed and d.needs_human:
            self.outbox.enqueue(scope, idem_key, action.name, payload,
                                d.tier, now)
        return d

    def owner_queue(self) -> list[dict]:
        """Every leg's pending decisions, newest business first.

        This is the one place that crosses tenant boundaries, and it is
        owner-only by construction: the HTTP layer gates the route, and the
        method takes no tenant argument that a partner could supply.
        """
        out: list[dict] = []
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            for item in self.outbox.pending(scope):
                out.append({
                    "id": item.idem_key,
                    "tenant": item.tenant,
                    "kind": item.kind,
                    "tier": item.tier.value,
                    "payload": dict(item.payload),
                    "created_at": item.created_at,
                    "needs_double_confirm": item.tier is RiskTier.RED,
                })
            for item in self.outbox.held(scope):
                out.append({
                    "id": item.idem_key, "tenant": item.tenant,
                    "kind": item.kind, "tier": item.tier.value,
                    "payload": dict(item.payload), "created_at": item.created_at,
                    "held": True, "note": item.note,
                    "needs_double_confirm": True,
                })
        return out

    def owner_status(self) -> dict:
        """Everything the owner's panel shows, measured rather than assumed.

        The panel used to draw these numbers from nothing — a fabricated
        temperature beside a fabricated token count beside a real-looking
        approve button. A control surface that invents its own readings is
        worse than no control surface, because it is trusted. Every field
        below comes from a local read of state this node actually holds; if a
        value cannot be read it is absent, and the panel says so.
        """
        now = self.now_epoch_s()
        legs = []
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            pack = self.registry.pack(tenant)
            evidence = self.evidence_for(scope)
            done, total = readiness(pack, evidence)
            counts = self.outbox.counts(scope)
            legs.append({
                "tenant": tenant.value,
                "capacity_per_week": pack.capacity_units_per_week,
                "readiness": {"done": done, "total": total},
                "pending": counts.get("pending", 0),
                "held": counts.get("held", 0),
                "sent": counts.get("sent", 0),
                "failed": counts.get("failed", 0),
                "events": self.ledger.count(scope),
                "gates": list(pack.gates),
                "blocked_gates": [g for g in pack.gates
                                  if g in self.closed_gates],
                "missing_facts": [k for k, need in
                                  sorted(pack.required_facts.items())
                                  if not ((h := evidence.get(k)) is not None
                                          and h.meets(need))],
            })

        boot = None
        if self.boot is not None:
            boot = {
                "ok": self.boot.ok,
                "mode": self.boot.mode.value,
                "summary": self.boot.summary(),
                "recovered_outbox": self.boot.recovered_outbox,
                "checks": [{"name": c.name, "severity": c.severity.value,
                            "detail": c.detail} for c in self.boot.checks],
            }

        return {
            "legs": legs,
            "closed_gates": list(self.closed_gates),
            "quota": dict(self.quota.snapshot(now)),
            "boot": boot,
            "killed": self.killed,
        }

    def recent_events(self, limit: int = 40) -> list[dict]:
        """The ledger tail across every leg, newest first.

        Owner-only, and owner-only by construction: like `owner_queue`, it
        takes no tenant argument a partner could supply.
        """
        out: list[dict] = []
        per_leg = max(1, limit)
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            for event in self.ledger.read(scope, limit=per_leg):
                out.append({
                    "tenant": event.tenant, "seq": event.seq, "ts": event.ts,
                    "kind": event.kind, "payload": dict(event.payload),
                    "hash": event.hash[:12],
                })
        out.sort(key=lambda e: (e["ts"], e["seq"]), reverse=True)
        return out[:limit]

    def owner_decide(self, item_id: str, approve: bool,
                     confirmed_twice: bool) -> dict:
        """Apply the owner's verdict. RED still needs the second confirmation.

        The item id carries its tenant prefix, which is how this resolves the
        scope without trusting a separate field that could disagree with it.
        """
        tenant_name, _, key = item_id.partition(":")
        if not key or tenant_name not in self.registry:
            return {"ok": False, "error": "unknown item"}
        scope = self.registry.scope(tenant_name)
        item = self.outbox.get(scope, key)
        if item is None:
            return {"ok": False, "error": "unknown item"}

        now = self.now_iso()
        if not approve:
            self.outbox.mark_failed(scope, key, now, note="rejected by owner")
            self.ledger.append(scope, "VERDICT",
                               {"item": key, "approved": False}, now)
            return {"ok": True, "status": "rejected"}

        gate = executable(
            Decision(True, item.tier, "queued", rule="queued"),
            human_approved=True, confirmed_twice=confirmed_twice)
        if not gate.allowed:
            return {"ok": False, "error": gate.reason, "rule": gate.rule}

        claimed = self.outbox.claim(scope, key, now)
        self.ledger.append(scope, "VERDICT", {
            "item": key, "approved": True, "tier": item.tier.value,
            "claimed": claimed,
        }, now)
        return {"ok": True, "status": "approved", "claimed": claimed}

    # ── health ────────────────────────────────────────────────────────────
    def healthy(self) -> bool:
        """Liveness probe for the watchdog. Must touch real state, not a flag.

        Reading the ledger head proves the database answers and the file is
        still there — the two ways this process most plausibly becomes a
        running-but-useless shell.
        """
        try:
            for tenant in self.registry:
                self.ledger.count(self.registry.scope(tenant))
            return True
        except Exception:
            return False

    def close(self) -> None:
        for store in (self.ledger, self.facts, self.outbox):
            try:
                store.close()
            except Exception:
                pass
