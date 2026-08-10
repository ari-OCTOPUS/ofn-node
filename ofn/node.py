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

import calendar
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

from .adapters.boot import BootReport, closed_gates_for
from .adapters.facts import FactStore
from .adapters.ledger import Ledger
from .adapters.outbox import APPROVED_MANUAL, Outbox
from .adapters.products import (ProductError, ProductStore, money_view,
                                net_margin_aud, piece_slug, verdicts)
from .adapters.studio_store import EARLIEST_PLAUSIBLE_EPOCH_S, StudioError
from .adapters.cycle_parsing import json_dumps_safe, parse_candidates
from .kernel.audience import ownership_ratio, revenue_mix
from .kernel.consent import may_publish, subjects_needing_attention
from .kernel.outreach import drafts_for as outreach_drafts
from .kernel.domain import (
    Action, Confidence, Decision, PackSpec, RiskTier, TenantId,
)
from .adapters.advisor import MIN_SAMPLE as ADVISOR_MIN_SAMPLE
from .adapters.advisor import Advisor, render_for_screen
from .kernel.callbudget import CallBudget
from .kernel.errors import FailClosedError
from .kernel.probe import QUESTIONS as PROBE_QUESTIONS
from .kernel.routing import RouteRequest, Rung
from .kernel.photos import ALLOWED_EDGES
from .kernel.photos import original_path as original_photo_path
from .kernel.photos import relative_path as photo_path
from .kernel.photos import inspect as photo_inspect
from .kernel.gates import admit, executable
from .kernel.questions import Question, is_stale, plan, readiness
from .kernel.quota import NodeQuota
from .kernel.tenancy import TenantRegistry, TenantScope
from .worker import Job


MAX_TEXT_ANSWER = 2000
OWNER_RISK_ITEM_LIMIT = 100

# Where a studio post is judged to be going. One value today because one
# platform is configured; it is a constant here rather than a literal at each
# call site so that adding a second is one edit, not a search.
DEFAULT_PLATFORM = "instagram"

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
    studio: object | None = None      # StudioStore
    consent: object | None = None     # ConsentStore
    media: object | None = None       # MediaStore
    audience: object | None = None    # AudienceStore
    marketing: object | None = None   # MarketingStore
    painting: object | None = None    # LeadStore
    assistant: object | None = None   # StudioAssistantStore
    backup_root: str | None = None
    # Path to the state directory, so sysmetrics can read the filesystem
    # holding the SQLite databases. Optional: metrics just omit disk figures
    # if it is empty.
    state_dir: str = ""
    # Phase A of the brain wiring: the owner's own surface only. No partner
    # data reaches this, and the studio path is deliberately NOT connected
    # until the extraction layer exists — "we will add the guard later" is
    # the sentence guards do not get added after.
    worker: object | None = None      # Worker
    call_budget: object | None = None # CallBudget
    # Phase C: the studio surface may now ask, because the
    # extraction layer exists. Synchronous rather than queued —
    # one short question, and the queue is for background work.
    router: object | None = None      # ModelRouter
    advisor: object | None = None     # Advisor
    # Marketing platform integration: durable inbox for webhook payloads
    inbox: object | None = None        # MarketingInbox
    # Inbound HTTP rate limiter — process-scoped, in-memory, per-tenant.
    # Defaults to a sane window; can be overridden in construction for tests.
    rate_limiter: object | None = None # InboundRateLimiter
    # Connector/inbox metrics — in-memory counters, read by observability.
    connector_metrics: object | None = None  # ConnectorMetrics
    # Connector registry: connector_id → Connector (O3). Empty in production
    # until a real vendor is approved; tests inject FakeConnector.
    connectors: Mapping[str, object] = field(default_factory=dict)
    # O10 read-only pilot state: vendor + tenant + cursor + receipts.
    # Dormant (empty) until Ari's decisions; populated by run.py wiring.
    pilot_state: object | None = None    # PilotState
    pilot: object | None = None          # ReadOnlyPilot
    # O11 real-publish config (set by run.py from config; never printed).
    _telegram_channel_id: str = ""
    _telegram_token: str = ""

    # ── gates ─────────────────────────────────────────────────────────────
    @property
    def closed_gates(self) -> tuple[str, ...]:
        """Base gates plus anything this boot added (e.g. SAFE MODE)."""
        if self.boot is None:
            return self.base_closed_gates
        return closed_gates_for(self.boot, self.base_closed_gates)

    # ── owner surface facade (phase H) ─────────────────────────────────────
    @property
    def owner(self):
        """The owner surface as one unit: `node.owner.status()`, etc.

        Delegates to this node — behaviour identical to calling the methods
        directly. This is the seam the gradual extract will cut along
        (finding 81); see ofn/adapters/owner_reads.py.
        """
        from .adapters.owner_reads import OwnerReads
        return OwnerReads(self)

    def evidence_for(self, scope: TenantScope) -> Mapping[str, Confidence]:
        """What is known, with anything past its re-ask date treated as
        unknown.

        Staleness is applied here rather than in the kernel because deciding
        it needs a clock, and the kernel has none. `plan` then re-asks with
        no change to it at all.

        Some answers go quietly out of date. Late GST registration means
        owing tax on every sale since the day registration was due — even on
        money never collected for it. An answer given once and never asked
        again is an answer that ages without anybody noticing.
        """
        pack = self.registry.pack(scope.tenant)
        known = dict(self.facts.evidence(scope, list(pack.required_facts)))
        now = self.now_epoch_s()
        for key in list(known):
            period = (pack.question_meta.get(key) or {}).get("ask_every")
            if period is None:
                continue
            age = self._fact_age_seconds(scope, key, now)
            if age is not None and is_stale(period, age):
                del known[key]
        return known

    def _fact_age_seconds(self, scope: TenantScope, key: str,
                          now_epoch_s: int) -> int | None:
        """How long ago this was last observed, or None if never."""
        subject, _, predicate = key.partition(".")
        fact = self.facts.current(scope, subject, predicate)
        seen = getattr(fact, "observed_at", None) if fact else None
        if not seen:
            return None
        try:
            stamp = time.strptime(str(seen)[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
        return max(0, now_epoch_s - int(calendar.timegm(stamp)))

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



    # ── brain, phase A: the owner's surface only ──────────────────────────
    def brain_status(self) -> dict:
        """What the thinking layer is, right now. Owner-only.

        Reports absence as absence. A panel that shows a healthy brain
        because nobody checked is worse than one that shows nothing.
        """
        if self.worker is None:
            return {"wired": False, "why": "worker not attached"}
        out = {"wired": True, **dict(self.worker.status())}
        if self.call_budget is not None:
            out["budget"] = self.call_budget.report(self.now_epoch_s())
        return out

    def run_brain_probe(self, scope: TenantScope) -> dict:
        """Ask the questions this node already knows the answers to.

        The first thing put in front of a model must not be something with no
        way of checking it — that is how a pipeline gets declared working on
        the strength of an answer nobody could grade. Every outcome here
        teaches: agreement means the pipe and the model are both worth
        something, disagreement is a broken pipe or a substituted model, and
        either is a finding.
        """
        if self.worker is None:
            return {"ok": False, "error": "مغز وصل نیست"}
        now = self.now_epoch_s()
        queued = []
        for question in PROBE_QUESTIONS:
            job = Job(tenant=scope.tenant.value, task=f"probe:{question.key}",
                      prompt=question.prompt,
                      # One per day per question. A probe that can be spammed
                      # is a way to spend the budget on nothing.
                      idem_key=f"probe:{question.key}:{now // 86_400}",
                      max_rung=Rung.REMOTE, estimated_tokens=200)
            if self.worker.submit(scope, job):
                queued.append(question.key)
        return {"ok": True, "queued": queued,
                "note": "پاسخ‌ها در لجر می‌نشینند؛ نتیجه را از brain_status بخوان"}

    def ask_owner_question(self, scope: TenantScope, prompt: str) -> dict:
        """One question from the owner's panel, in the owner's own words.

        Phase A on purpose: this carries the owner's data and nobody else's.
        The partner surfaces stay disconnected from the brain until the
        extraction layer exists, because the window in which the pipe is
        connected and the guard is not is exactly the window a bug needs.
        """
        if self.worker is None:
            return {"ok": False, "error": "مغز وصل نیست"}
        text = str(prompt or "").strip()
        if not text:
            return {"ok": False, "error": "سؤال خالی است"}
        if len(text) > MAX_TEXT_ANSWER:
            return {"ok": False, "error": "سؤال بلندتر از حد مجاز است"}
        now = self.now_epoch_s()
        if self.call_budget is not None and not self.call_budget.allows(
                Rung.REMOTE, now):
            return {"ok": False, "error": "سقف تماس امروز پر شده"}
        job = Job(tenant=scope.tenant.value, task="owner:ask", prompt=text,
                  idem_key=f"owner:{now}:{abs(hash(text)) % 10**8}",
                  max_rung=Rung.REMOTE)
        return {"ok": bool(self.worker.submit(scope, job))}

    # ── studio surface ────────────────────────────────────────────────────
    def _studio(self):
        if self.studio is None or self.consent is None or self.media is None:
            raise ProductError("استودیو در دسترس نیست")
        return self.studio


    def _next_draft_id(self, tenant: str) -> str:
        """A new id, from the store's high-water mark.

        Sequential and readable, because it becomes a directory name under
        the media root and appears in the ledger. It used to be derived from
        the drafts that exist, which is the `next_sku` bug for the third
        time: a deleted row is exactly the one that derivation can no longer
        see, so it hands its id — and its media directory — to a new post.
        """
        return self.studio.next_draft_id(tenant)

    def _self_subject(self, tenant: str) -> str:
        """The partner herself, as a consent subject.

        Created on first use rather than by hand, because the alternative is
        that `draft_subjects` stays empty until somebody remembers — and the
        whole point of that table is that it cannot be reconstructed later.

        A subject is not a release. This makes her *declared*; whether she
        has agreed to a platform is still a document the owner records, and
        the gate still refuses until it exists.
        """
        sid = "self"
        try:
            self.consent.add_subject(tenant, sid, "خودم",
                                     now_epoch_s=self.now_epoch_s())
        except Exception:
            pass          # already there, which is the normal case
        return sid

    def studio_board(self, scope: TenantScope) -> dict:
        """Everything one screen needs, in one request.

        One call rather than four because the shell shows a single decision:
        four requests would let the parts arrive out of order and render a
        card whose consent state belongs to a different draft.
        """
        tenant = scope.tenant.value
        store = self._studio()
        now = self.now_epoch_s()
        drafts = []
        for d in store.drafts(tenant):
            if d.status in ("published", "abandoned"):
                continue
            people = self.consent.subjects_in_draft(d.draft_id)
            docs = self.consent.releases_for([s.subject_id for s in people])
            gaps = subjects_needing_attention(
                people, docs, platform=DEFAULT_PLATFORM, now_epoch_s=now)
            drafts.append({
                "draft_id": d.draft_id,
                "collection_id": d.collection_id,
                "caption": d.caption,
                "status": d.status,
                "media": [{"position": pos, "ref": ref}
                          for pos, ref in store.media_of(d.draft_id)],
                "subjects": [{"id": s.subject_id, "label": s.display_label}
                             for s in people],
                # The gate's answer, not the ingredients of it. A shell that
                # rebuilt this from the parts would be a second implementation
                # of the rule, and the two would disagree eventually.
                "consent_ok": not gaps and bool(people),
                "consent_gaps": {k: v.value for k, v in gaps.items()},
            })
        return {
            "drafts": drafts,
            "collections": [{"id": c.collection_id, "label": c.label,
                             "genre": c.genre,
                             "sensitivity": c.sensitivity.value}
                            for c in store.collections(tenant)],
            "platform": DEFAULT_PLATFORM,
        }

    def create_draft(self, scope: TenantScope, user_id: str,
                     body: Mapping[str, object]) -> dict:
        store = self._studio()
        tenant = scope.tenant.value
        # Minted here, not sent by the shell. A client-chosen id is a client
        # -chosen filesystem path once media lands under it, and two phones
        # would eventually pick the same one.
        draft_id = self._next_draft_id(tenant)
        try:
            store.add_draft(
                tenant, draft_id,
                collection_id=(str(body["collection_id"])
                               if body.get("collection_id") else None),
                caption=(str(body["caption"]) if body.get("caption") else None),
                now_epoch_s=self.now_epoch_s())
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}

        # Every draft records who is in it, from the first one, even while
        # the answer is always the same person. The day a second person
        # appears, a table that exists gains a row; a table that does not
        # exist cannot reconstruct the history built until then.
        people = list(body.get("subjects") or []) or [self._self_subject(tenant)]
        for sid in people:
            try:
                self.consent.add_to_draft(draft_id, str(sid),
                                          added_by=f"partner:{user_id}",
                                          now_epoch_s=self.now_epoch_s())
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        self.ledger.append(scope, "DRAFT_CREATED", {
            "draft_id": draft_id, "actor": f"partner:{user_id}",
        }, self.now_iso())
        return {"ok": True, "draft_id": draft_id}

    def attach_media(self, scope: TenantScope, user_id: str, draft_id: str,
                     body: Mapping[str, object]) -> dict:
        """Store the two renditions the browser made.

        The original is not kept. Archiving it was meant to prove what was
        published and does not: if a 1600px rendition is what goes out, the
        original never went. `media_sent` records the hash of what actually
        left, and every original kept would be one more sensitive file at
        rest on a disk that is not encrypted.
        """
        store = self._studio()
        tenant = scope.tenant.value
        written = {}
        try:
            position = body.get("position", 0)
            renditions = body.get("renditions") or {}
            if not isinstance(renditions, Mapping):
                raise FailClosedError("renditions must be an object")
            for edge in ALLOWED_EDGES:
                text = renditions.get(str(edge))
                if not text:
                    raise FailClosedError(f"رساله‌ی {edge} نیامده")
                payload = photo_inspect(str(text))
                written[edge] = self.media.write_rendition(
                    tenant, draft_id, position, edge, payload)
            store.attach_media(draft_id, position, written[max(ALLOWED_EDGES)])
        except (FailClosedError, StudioError) as exc:
            # The renditions were written to disk before the DB row. If the
            # DB step failed, those files are orphans — delete them so a
            # failed attach does not leave media pointing at nothing.
            import os as _os
            for ref in written.values():
                try:
                    path = self.media.absolute(str(ref))
                    if _os.path.exists(path):
                        _os.remove(path)
                except Exception:
                    pass
            return {"ok": False, "error": str(exc)}
        # Mutation paired with its record (finding 13): renditions are on
        # disk and the draft references them — say so in the ledger.
        self.ledger.append(scope, "DRAFT_MEDIA_ATTACHED", {
            "draft_id": draft_id, "position": position,
        }, self.now_iso())
        return {"ok": True, "position": position,
                "refs": {str(k): v for k, v in written.items()}}

    def publish_draft(self, scope: TenantScope, user_id: str, draft_id: str,
                      body: Mapping[str, object]) -> dict:
        """Queue a post for the owner. Nothing leaves the board here.

        The consent gate is evaluated in this method rather than trusted from
        the shell. A screen can be stale, edited, or replayed; the ledger
        entry that follows has to be true about the moment it was written.
        """
        store = self._studio()
        platform = str(body.get("platform") or DEFAULT_PLATFORM)
        try:
            draft = store.draft(draft_id)
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}

        people = self.consent.subjects_in_draft(draft_id)
        docs = self.consent.releases_for([s.subject_id for s in people])
        verdict = may_publish(people, docs, platform=platform,
                              now_epoch_s=self.now_epoch_s())
        if not verdict.allowed:
            self.ledger.append(scope, "PUBLISH_REFUSED", {
                "draft_id": draft_id, "platform": platform,
                "why": verdict.why,
                "blocked": [b.subject_id for b in verdict.blocks],
                "actor": f"partner:{user_id}",
            }, self.now_iso())
            return {"ok": False, "error": verdict.why,
                    "blocked": [b.subject_id for b in verdict.blocks]}

        if not store.media_of(draft_id):
            return {"ok": False, "error": "این پیش‌نویس هیچ رسانه‌ای ندارد"}

        # Publishing a picture of a person is irreversible and leaves the
        # device. There is no configuration that makes this anything but red.
        gate = self._gate_enqueue(
            scope, f"draft:{draft_id}:{platform}", "PUBLISH_POST",
            {"draft_id": draft_id, "platform": platform,
             "caption": draft.caption,
             "media": [ref for _, ref in store.media_of(draft_id)]},
            RiskTier.RED, self.now_iso())
        if not gate["ok"]:
            return gate
        queued = gate["queued"]
        store.set_status(draft_id, "queued")
        self.ledger.append(scope, "PUBLISH_QUEUED", {
            "draft_id": draft_id, "platform": platform,
            "duplicate": not queued, "actor": f"partner:{user_id}",
        }, self.now_iso())
        return {"ok": True, "queued": queued, "status": "queued"}

    def record_felt(self, scope: TenantScope, user_id: str, draft_id: str,
                    body: Mapping[str, object]) -> dict:
        """Her own reading of a post, before any platform figure.

        Stored with its timestamp whether or not a number has already
        arrived. Refusing would lose the answer; the stamp is what lets an
        analysis decide later whether it may use it.
        """
        store = self._studio()
        try:
            rating = body.get("rating")
            draft = store.record_felt_right(
                draft_id, rating if isinstance(rating, int) else -1,
                now_epoch_s=self.now_epoch_s())
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        # Mutation paired with its record (finding 13): her reading is a
        # fact about the post; the ledger says when it was recorded.
        self.ledger.append(scope, "FELT_RECORDED", {
            "draft_id": draft_id, "rating": rating,
        }, self.now_iso())
        return {"ok": True, "trustworthy": draft.rating_is_trustworthy}


    # ── studio reading, tier 0 ────────────────────────────────────────────
    def studio_measurements(self, scope: TenantScope) -> dict:
        """Numbers about her work. Nothing that is not a number.

        Built here rather than inside the advisor so the advisor keeps one
        job — refusing anything that is not evidence — and cannot also be the
        thing that decides what counts as evidence.
        """
        tenant = scope.tenant.value
        drafts = self.studio.drafts(tenant) if self.studio else []
        posted = [d for d in drafts if d.status in ("queued", "published")]
        media = [len(self.studio.media_of(d.draft_id)) for d in posted] \
            if self.studio else []
        rated = [d.felt_right for d in drafts
                 if d.rating_is_trustworthy and d.felt_right is not None]
        captions = [len(d.caption or "") for d in posted if d.caption]
        return {
            "posts_counted": len(posted),
            "window_days": 90,
            "media_per_post": (sum(media) / len(media)) if media else 0,
            "median_caption_chars": (sorted(captions)[len(captions) // 2]
                                     if captions else 0),
            # Only ratings given before any platform figure arrived. The rest
            # are reflections of the number and would make any correlation
            # look stronger than it is.
            "felt_right_mean": (sum(rated) / len(rated)) if rated else 0,
            "felt_right_counted": len(rated),
        }

    def studio_reading(self, scope: TenantScope) -> dict:
        """What has been said, and whether anything new can be asked.

        Reading is free and always answers. Asking costs money and is a
        separate call — a screen that spends on every open is a screen
        nobody can afford to leave open.
        """
        tenant = scope.tenant.value
        found = self.studio.findings(tenant) if self.studio else []
        measured = self.studio_measurements(scope)
        return {
            "findings": found,
            "sample": measured["posts_counted"],
            "enough": measured["posts_counted"] >= ADVISOR_MIN_SAMPLE,
            "needed": ADVISOR_MIN_SAMPLE,
        }

    def set_draft_labels(self, scope: TenantScope, user_id: str,
                         draft_id: str, body: Mapping[str, object]) -> dict:
        """Tag a post with what it is, from the pack's closed vocabulary.

        Recorded from the first post on purpose. The only moment a post's
        style is known is when she makes it, and a vocabulary added in three
        months leaves those three months uncomparable for ever — which are
        exactly the months a new account spends finding out what works.
        """
        if self.studio is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        pack = self.registry.pack(scope.tenant)
        raw = body.get("labels")
        if not isinstance(raw, (list, tuple)):
            return {"ok": False, "error": "برچسب‌ها باید فهرست باشند"}
        try:
            chosen = self.studio.set_labels(draft_id, raw,
                                            allowed=pack.content_labels)
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        # Mutation paired with its record (finding 13).
        self.ledger.append(scope, "DRAFT_LABELS_SET", {
            "draft_id": draft_id, "labels": chosen,
        }, self.now_iso())
        return {"ok": True, "labels": chosen}

    def add_to_library(self, scope: TenantScope, user_id: str,
                       body: Mapping[str, object]) -> dict:
        """A photo arrives and goes into her library, not into a post.

        This used to create a draft and hang the photo off it, which made
        every shot a post before she had decided anything. A picture taken
        today and used next month had nowhere to be in between.

        The original is kept — this is her archive (D-14 revisited). The two
        renditions are what a screen and a platform get.
        """
        if self.studio is None or self.media is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        tenant = scope.tenant.value
        media_id = self.studio.next_media_id(tenant)
        try:
            renditions = body.get("renditions") or {}
            if not isinstance(renditions, Mapping):
                raise FailClosedError("renditions must be an object")
            biggest = photo_inspect(str(renditions[str(max(ALLOWED_EDGES))]))
            for edge in ALLOWED_EDGES:
                text = renditions.get(str(edge))
                if not text:
                    raise FailClosedError(f"اندازهٔ {edge} نیامده")
                self.media.write_rendition(
                    tenant, media_id, 0, edge, photo_inspect(str(text)))
            original = body.get("original")
            kept = False
            if original:
                self.media.write_original(tenant, media_id, 0,
                                          photo_inspect(str(original)))
                kept = True
            # Clamped rather than trusted. The value is a clock on somebody
            # else's phone, and a photo dated in 2087 sorts above everything
            # she owns for ever. Out of range means unknown, which the column
            # can say; there is no repair that would be honest here.
            taken = body.get("taken_at")
            now = self.now_epoch_s()
            if not isinstance(taken, int) or isinstance(taken, bool) \
                    or not EARLIEST_PLAUSIBLE_EPOCH_S <= taken <= now:
                taken, source = None, ""
            else:
                source = str(body.get("taken_source") or "")
            self.studio.add_media(
                tenant, media_id, mime=biggest.media_type,
                byte_size=biggest.max_decoded_bytes, has_original=kept,
                now_epoch_s=now, taken_at=taken, taken_source=source,
                collection_id=(str(body["album"]) if body.get("album") else None))
        except (FailClosedError, StudioError, KeyError) as exc:
            # Nothing half-written survives: the row is the last thing
            # written, so a failure leaves files with no record and the id
            # unspent rather than a record pointing at nothing.
            self.media.remove_piece(tenant, media_id)
            return {"ok": False, "error": str(exc) or "عکس ذخیره نشد"}
        self.ledger.append(scope, "MEDIA_ADDED", {
            "media_id": media_id, "original_kept": kept,
            "actor": f"partner:{user_id}",
        }, self.now_iso())
        return {"ok": True, "media_id": media_id, "original_kept": kept}

    def set_media_labels(self, scope: TenantScope, media_id: str,
                         body: Mapping[str, object]) -> dict:
        """Tag a photo from the pack's closed vocabulary.

        On the photo rather than the post: she tags a shot in the gallery
        weeks before it becomes anything, and one photo used twice would
        otherwise carry two separate descriptions of one image.
        """
        if self.studio is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        raw = body.get("labels")
        if not isinstance(raw, (list, tuple)):
            return {"ok": False, "error": "برچسب‌ها باید فهرست باشند"}
        pack = self.registry.pack(scope.tenant)
        try:
            chosen = self.studio.set_media_labels(
                scope.tenant.value, media_id, raw,
                allowed=pack.content_labels)
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        # Mutation paired with its record (finding 13).
        self.ledger.append(scope, "MEDIA_LABELS_SET", {
            "media_id": media_id, "labels": chosen,
        }, self.now_iso())
        return {"ok": True, "labels": chosen}

    def describe_media(self, scope: TenantScope, media_id: str,
                       body: Mapping[str, object]) -> dict:
        """Her sentence and her mark on one shot.

        Separate from `set_media_labels` on purpose. The vocabulary is closed
        and answers "which side of which axis is this"; a note is open and
        answers "why I want the next one like this". Folding them into one
        call would mean saving a rating had to restate every label, and a
        request that restates everything is a request that can silently undo
        something it was never shown.
        """
        if self.studio is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        note = body.get("note")
        rating = body.get("rating")
        category = body.get("category")
        if note is None and rating is None and category is None:
            return {"ok": False, "error": "چیزی برای ثبت نیست"}
        try:
            item = self.studio.describe_media(
                scope.tenant.value, media_id,
                note=None if note is None else str(note),
                rating=None if rating is None else rating,
                category=None if category is None else str(category))
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "media": item}

    def create_album(self, scope: TenantScope, user_id: str,
                     body: Mapping[str, object]) -> dict:
        """A new album, named by her, during the session that needs it.

        Albums could only be created by whoever seeded the database, which
        meant an archiving session could file photos into categories nobody
        had thought of yet — and "where does this go?" is answered while
        looking at the photo, not the week before.

        `sensitivity` is not a field here. It is `restricted`, the same way
        it is for a collection made anywhere else (D-15); making an album
        general is a separate, deliberate act.
        """
        if self.studio is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        label = str(body.get("label") or "").strip()
        if not label:
            return {"ok": False, "error": "نام آلبوم خالی است"}
        if len(label) > 60:
            return {"ok": False, "error": "نام آلبوم خیلی بلند است"}
        tenant = scope.tenant.value
        try:
            album = self.studio.add_collection(
                tenant, self.studio.next_collection_id(tenant), label,
                genre=str(body.get("genre") or ""),
                now_epoch_s=self.now_epoch_s())
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        self.ledger.append(scope, "ALBUM_CREATED", {
            "album": album.collection_id, "actor": f"partner:{user_id}",
        }, self.now_iso())
        return {"ok": True, "album": {"id": album.collection_id,
                                      "label": album.label,
                                      "genre": album.genre,
                                      "sensitivity": album.sensitivity.value}}

    def delete_album(self, scope: TenantScope, user_id: str, album_id: str) -> dict:
        if self.studio is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        try:
            moved = self.studio.delete_collection(scope.tenant.value, album_id)
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        self.ledger.append(scope, "ALBUM_DELETED", {"album": album_id, "photos_unfiled": moved, "actor": f"partner:{user_id}"}, self.now_iso())
        return {"ok": True, "album": album_id, "photos_unfiled": moved}

    def delete_media(self, scope: TenantScope, user_id: str, media_id: str) -> dict:
        if self.studio is None or self.media is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        try:
            # Tombstone order: inventory the files FIRST, then delete the
            # files, then drop the DB row. If file deletion fails, the DB
            # row survives and the photo is recoverable — the previous order
            # (DB first) left a sensitive file on disk with no row pointing
            # at it, which is how a photo becomes unreachable but undeletable.
            gone = self.studio.drop_media(scope.tenant.value, media_id)
            if gone is None:
                return {"ok": False, "error": "این عکس پیدا نشد"}
            # drop_media succeeded — the row is gone. Now the files; if this
            # fails the DB row is already removed, so log loudly rather than
            # pretending the photo is fully deleted.
            files = self.media.remove_piece(scope.tenant.value, media_id)
            backups = self.media.purge_from_backups(self.backup_root, scope.tenant.value, media_id) if self.backup_root else 0
        except (StudioError, FailClosedError) as exc:
            return {"ok": False, "error": str(exc)}
        self.ledger.append(scope, "MEDIA_DELETED", {"media_id": media_id, "files": files, "backups": backups, "actor": f"partner:{user_id}"}, self.now_iso())
        return {"ok": True, "media_id": media_id, "files_deleted": files, "backups_deleted": backups}

    def file_media(self, scope: TenantScope, media_id: str,
                   body: Mapping[str, object]) -> dict:
        """Put a photo in an album, or take it out of one.

        Separate from `set_media_labels` even though an archiving screen
        changes both at once: an album is where a photo lives and a label is
        what it shows, and one failing must not silently undo the other.
        """
        if self.studio is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        raw = body.get("album")
        # An absent key and an explicit null both mean "no album". A screen
        # that omits the field to mean "leave it alone" would need a third
        # value, and there is no such request.
        album = None if raw in (None, "", False) else str(raw)
        try:
            filed = self.studio.set_media_collection(
                scope.tenant.value, media_id, album)
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        # Mutation paired with its record (finding 13).
        self.ledger.append(scope, "MEDIA_FILED", {
            "media_id": media_id, "album": album,
        }, self.now_iso())
        return {"ok": True, "album": filed}

    def studio_marketing(self, scope: TenantScope) -> dict:
        """The marketing tab: what the weekly cycle sees, studio-scoped.

        This is the snapshot the senior-architect review asked for, built
        to one rule: it shows the studio brain and a *safe* global-health
        summary, never the owner brain, never secrets, never another leg's
        data. The partner is a partner, not an admin.

        What is here is read-only and derived: the current week's focus,
        observed trends, the scout's memory size (counts only — never the
        ideas' titles, which belong to her), and which gates are closed.
        """
        tenant = scope.tenant.value
        now = self.now_epoch_s()

        # The marketing summary, if the store is wired. Before the first
        # cycle this is empty, which is an honest answer — "nothing yet".
        marketing = {}
        if self.marketing is not None:
            marketing = self.marketing.summary(tenant)

        # Gates the studio leg cares about, as open/closed only. The raw
        # gate set is node-wide config; here we surface only the ones that
        # touch this leg, and only their state, never their internals.
        closed = set(self.base_closed_gates)
        gates = {
            "secret_rotation": "closed" if "secret_rotation" in closed else "open",
            "partner_precondition": "closed" if "partner_precondition" in closed else "open",
        }
        # The publish wire is always off until M5; saying so plainly is
        # better than letting the UI guess.
        gates["wire_publish"] = "off"
        gates["owner_release"] = "off"

        # Brain modules: derived from real state, not a hardcoded 'ok'.
        # A partner reading "marketing_scout: last_run=never" learns the
        # cycle is wired but has not run; "platform_matrix: 11 platforms"
        # confirms the policy is loaded. None of this leaks config — only
        # presence and counts, the way a partner's surface should.
        brain: dict[str, object] = {}
        brain["marketing_store"] = ("loaded" if self.marketing is not None
                                    else "unwired")
        # The marketing cycle's last run, from the store's current week.
        wk = (marketing or {}).get("current_week")
        brain["marketing_cycle"] = {
            "current_week": wk["week_id"] if wk else None,
            "status": wk["status"] if wk else "never_run",
        }
        # Platform matrix: loaded count, not the rules themselves.
        try:
            from .adapters.platform_matrix_loader import (
                default_matrix_path, load_matrix)
            from .adapters.platforms import available_platforms
            m = load_matrix(default_matrix_path())
            available = available_platforms()
            # Three counts, because three different things are true at once:
            #   policy_known  — how many platforms the policy matrix names.
            #                   Eleven does not mean eleven live outputs; it
            #                   means "we have a rule for each of these".
            #   available     — how many have adapter *code* on this node.
            #                   Code exists, could be armed, but isn't yet.
            #   armed         — how many the node actually built and holds.
            #                   Today this is zero: no adapter is instantiated
            #                   until OwnerRelease is wired (M5). A partner
            #                   reading "armed: 0" learns nothing leaves yet,
            #                   which is the fact that matters.
            brain["platform_matrix"] = {
                "loaded": True,
                "platform_count": len(m.rules),
                "platform_policy_known_count": len(m.rules),
                "platform_adapter_available_count": len(available),
                "platform_adapter_armed_count": 0,
            }
        except Exception:
            brain["platform_matrix"] = {"loaded": False}
        # Trend sources: none wired today, but the shape is honest about it.
        sources = getattr(self, "_marketing_sources", None)
        if sources is not None and hasattr(sources, "sources"):
            brain["trend_sources"] = {"enabled": len(sources.sources)}
        else:
            brain["trend_sources"] = {"enabled": 0}
        # Consent store presence.
        brain["consent"] = ("loaded" if self.consent is not None
                            else "unwired")
        # The hosted brain: configured (key present) or not. We do NOT report
        # the key, the endpoint, or any token — only whether the rung is
        # armed. This is the one piece a partner benefits from knowing:
        # "the brain is not armed yet, so the weekly focus is manual".
        router_armed = False
        if self.router is not None:
            try:
                st = self.worker.status() if self.worker is not None else {}
                router_armed = bool(st.get("remote", {}).get("present", False)) \
                    if isinstance(st.get("remote"), dict) else False
            except Exception:
                router_armed = False
        brain["hosted_brain"] = {"armed": router_armed}

        return {
            "now": now,
            "viewer": {"role": "partner", "scope": "studio"},
            "gates": gates,
            "brain_modules": brain,
            "marketing": marketing,
        }

    def run_marketing_cycle(self, scope: TenantScope, *,
                            week_id: str, starts_at: int, style_id: str,
                            terms: tuple[str, ...] = (),
                            now_epoch_s: int) -> dict:
        """Run one weekly marketing cycle, wired to the hosted brain.

        This is the entry point the weekly timer calls. It does three things:

          1. Gathers observations from the configured trend sources (none
             wired yet → empty harvest, which is an honest quiet week, not
             an error).
          2. Asks the model for candidate ideas, giving it the scout's brief
             (the focus question + the rejection list). The brief carries
             *no* Saba data — only keys and counts — so zero-class research
             holds even with the model in the loop.
          3. Runs the cycle: triage against persisted memory, persist fresh
             as PROPOSED, open the week with the focus.

        What it does NOT do, on purpose: it does not publish, route to
        platforms, or touch the outbox. Surviving triage makes an idea a
        proposal for the partner, not a post.

        Fail-closed throughout: if the brain is absent (no API key), the
        cycle records its observations and opens the week with the focus
        derived from gaps, and notes that no candidates were produced. A
        week without the model is a quiet week, not a dead node.
        """
        if self.marketing is None:
            return {"ok": False, "error": "بازاریابی وصل نیست"}
        tenant = scope.tenant.value

        # Load the persisted memory to derive the research focus — *before*
        # spending a token, so the question we ask the model comes from
        # measured gaps rather than novelty.
        memory = self.marketing.load_memory(tenant)

        # The cycle object. Sources are wired later; today it is empty,
        # which the cycle handles (a quiet harvest).
        from .adapters.trend_sources import TrendAggregator, TrendQuery
        from .adapters.weekly_cycle import WeeklyCycle
        cycle = WeeklyCycle(self.marketing,
                            getattr(self, "_marketing_sources", None)
                            or TrendAggregator(()))

        # Ask the model for candidate ideas. The brief is the only thing
        # that goes out, and it carries keys and counts, never images or
        # names. If the router or the key is absent, we get no candidates
        # and the cycle still runs (focus derived, week opened).
        candidates = ()
        brain_note = ""
        if self.router is not None:
            from .kernel.marketing_scout import brief as scout_brief
            focus_qs = []  # derived inside the cycle; here we hand the model
            # the rejection list and the rule, which is what stops loops.
            brief_text = json_dumps_safe(scout_brief(memory))
            prompt = (
                "You are a content-strategy researcher for a faceless Persian "
                "beauty and foot-care creator (wellness/beauty framing only; "
                "no sexual solicitation, no explicit content, no direct adult "
                "subscription links, no minors). The weekly style is "
                f"'{style_id}'.\n\n"
                "Return STRICT JSON ONLY — no prose, no markdown fences. "
                "Schema:\n"
                '{"candidates":[{"key":"stable_slug",'
                '"title":"short english title",'
                '"style_id":"' + style_id + '",'
                '"framing":"beauty|wellness|educational|behind_the_scenes|community",'
                '"confidence":0.0_to_1.0}]}\n\n'
                "Rules:\n"
                "- Up to 3 candidates, each a distinct idea.\n"
                "- 'key' is a lowercase hyphenated slug, stable across weeks.\n"
                "- Do NOT predict future trends. Propose only ideas grounded "
                "in currently-observable beauty/foot-care/wellness practice.\n"
                "- Do NOT re-propose anything in the rejected list below.\n"
                f"- Rejected (skip): {brief_text}\n"
                "Return only the JSON object."
            )
            try:
                result = self.router.ask(
                    scope.tenant,
                    RouteRequest(task="studio:marketing-research",
                                 max_rung=Rung.REMOTE, estimated_tokens=600),
                    prompt, now_epoch_s=now_epoch_s)
                if not getattr(result, "refused", False):
                    candidates = parse_candidates(
                        getattr(result, "text", ""),
                        now_epoch_s=now_epoch_s)
                    brain_note = (f"مدل {len(candidates)} ایده پیشنهاد داد"
                                  if candidates
                                  else "مدل ایده‌ای نداد")
                else:
                    brain_note = "مغز جواب نداد (کلید غایب یا سهمیه پر)"
            except Exception as exc:  # network, parse, anything
                brain_note = f"مغز در دسترس نبود: {type(exc).__name__}"
        else:
            brain_note = "مغز وصل نیست"

        # Run the cycle with whatever candidates we have (possibly none).
        result = cycle.run(
            tenant=tenant, week_id=week_id, starts_at=starts_at,
            style_id=style_id,
            query=TrendQuery(terms=terms),
            candidates=candidates,
            tried_styles=getattr(scope, "tried_styles", None) or {},
            now_epoch_s=now_epoch_s,
        )

        return {
            "ok": True,
            "week_id": result.week_id,
            "style_id": result.style_id,
            "focus_text": result.focus_text,
            "observations_kept": result.observations_kept,
            "fresh_candidates": len(result.fresh_candidates),
            "refused_count": result.refused_count,
            "brain": brain_note,
        }

    def _consent_for_platform(self, draft_id: str, platform: str, *,
                              now_epoch_s: int) -> str | None:
        """Is everyone in this draft consented for this platform?

        Returns None when consent is clear, or a refusal rule string when not.
        Mirrors the studio_board consent computation but per-platform and as
        a single verdict, because send_to_outbox needs one yes/no per variant
        rather than a screen of gaps. The rule string names *why* it refused
        so the partner sees the cause, not just "no".
        """
        if self.consent is None:
            return "consent:no-consent-store"
        people = self.consent.subjects_in_draft(draft_id)
        if not people:
            # "Nobody declared" is not "nobody in it" — the fleet.judge rule.
            return "consent:no-subject-declared"
        docs = self.consent.releases_for(
            [s.subject_id for s in people])
        verdict = may_publish(people, docs, platform=platform,
                              now_epoch_s=now_epoch_s)
        if not verdict.allowed:
            # The verdict's `why` is human-readable prose; pull the first
            # block's reason if there is one, else the summary.
            return ("consent:" + (verdict.blocks[0].reason.value
                    if verdict.blocks else "blocked"))
        return None

    def send_to_outbox(self, scope: TenantScope, user_id: str,
                       draft_id: str, platforms: tuple[str, ...], *,
                       framing: str = "beauty",
                       adult_label: bool = False) -> dict:
        """Route a draft into the outbox as one variant per platform.

        This is the partner's "send" action — but it sends to the outbox,
        never to a platform. Every variant is screened first; only the ones
        that pass become outbox items, each as RED (publishing is always
        irreversible, third-party, and out of the machine). The release
        switch — not this method — decides whether anything ever leaves the
        outbox, and it is off by default.

        Idempotency: the outbox key is the content router's idempotency key,
        so a double-send of the same draft to the same platform is a no-op
        (returns False for that platform), not a double post.
        """
        from .adapters.platform_matrix_loader import (
            default_matrix_path, load_matrix)
        from .adapters.content_router import ContentRouter, DraftForRouting
        from .kernel.domain import RiskTier
        tenant = scope.tenant.value
        store = self._studio()
        try:
            draft = store.draft(draft_id)
        except Exception:
            return {"ok": False, "error": "پیش‌نویس پیدا نشد"}
        # Sensitivity from the collection, fail-closed to restricted.
        sensitivity = "restricted"
        if draft.collection_id and hasattr(store, "collection"):
            coll = store.collection(draft.collection_id)
            if coll is not None:
                sensitivity = coll.sensitivity.value
        if sensitivity == "restricted":
            return {"ok": False,
                    "error": "محتوای محدود هرگز از دستگاه خارج نمی‌شود"}
        caption = (draft.caption or "").strip()
        if not caption:
            return {"ok": False, "error": "کپشن خالی است"}

        matrix = load_matrix(default_matrix_path())
        router = ContentRouter(matrix)
        variants = router.route(
            DraftForRouting(draft_id=draft_id, caption_seed=caption,
                            sensitivity=sensitivity, style_id="publish",
                            media_refs=()),
            platforms, framing=framing, adult_label=adult_label)

        sent: list[dict] = []
        for v in variants:
            if not v.screen.ok:
                sent.append({"platform": v.platform, "queued": False,
                             "rule": v.screen.rule})
                continue
            # Consent: every person in the draft must be covered by a live
            # release for THIS platform. General-sensitivity is necessary
            # but not sufficient — the senior-architect review's point.
            # may_publish refuses: no subject, no release, expired, revoked,
            # out-of-scope. Each variant is checked for its own platform,
            # because a release that covers 'bluesky' does not cover 'instagram'.
            consent_rule = self._consent_for_platform(
                draft_id, v.platform, now_epoch_s=self.now_epoch_s())
            if consent_rule is not None:
                sent.append({"platform": v.platform, "queued": False,
                             "rule": consent_rule})
                continue
            # The outbox payload carries everything a future publisher needs,
            # and nothing it does not: no secrets, no other tenants.
            payload = {"draft_id": draft_id, "platform": v.platform,
                       "caption": v.caption,
                       "hashtags": list(v.hashtags),
                       "framing": v.framing,
                       "adult_label": v.adult_label,
                       "idempotency_key": v.idempotency_key,
                       "requested_by": user_id}
            gate = self._gate_enqueue(
                scope, v.idempotency_key, "studio:publish", payload,
                RiskTier.RED, self.now_iso())
            if not gate["ok"]:
                return gate
            queued = gate["queued"]
            # Record the variant in the marketing store for the audit trail.
            if self.marketing is not None:
                import time as _t
                self.marketing.record_variant(
                    tenant, draft_id=draft_id, platform=v.platform,
                    caption=v.caption, hashtags=v.hashtags,
                    framing=v.framing, adult_label=v.adult_label,
                    screen_ok=True, screen_rule=v.screen.rule,
                    screen_reasons=v.screen.reasons, risk_color=v.screen.risk,
                    idempotency_key=v.idempotency_key,
                    variant_id=f"{tenant}:{v.idempotency_key[:16]}",
                    now_epoch_s=self.now_epoch_s())
            sent.append({"platform": v.platform, "queued": queued,
                         "rule": v.screen.rule,
                         "idempotency_key": v.idempotency_key[:12] + "…"})

        queued_count = sum(1 for s in sent if s["queued"])
        # Mutation paired with its record (finding 13): the enqueues above
        # write to the outbox; this ledger event is the trace of WHY.
        self.ledger.append(scope, "STUDIO_PUBLISH_VARIANTS", {
            "draft_id": draft_id,
            "queued": queued_count,
            "total": len(sent),
        }, self.now_iso())
        return {"ok": True, "draft_id": draft_id,
                "queued": queued_count, "results": sent}

    def route_preview(self, scope: TenantScope, draft_id: str,
                      platforms: tuple[str, ...], *,
                      framing: str = "beauty",
                      adult_label: bool = False) -> dict:
        """Show, for one draft, which platforms would accept or refuse it.

        Read-only: nothing is written, nothing is queued. This is the
        partner's preview before she decides — "if I send this, where does
        it land and where does it get refused, and why?". The 'why' is the
        point: a screen that said only 'blocked' would leave her guessing
        whether to rewrite the caption, change the framing, or give up on
        that platform for this content.

        The variants are produced by the content router against the loaded
        platform matrix, so the verdicts here are exactly the verdicts a
        send-to-outbox would get — no separate 'would it really' path.
        """
        from .adapters.platform_matrix_loader import (
            default_matrix_path, load_matrix)
        from .adapters.content_router import ContentRouter, DraftForRouting
        tenant = scope.tenant.value
        store = self._studio()
        # `draft(draft_id)` is keyed by id alone (tenant is implicit in the
        # id space); it raises StudioError if missing, which we treat as
        # "no draft yet" so the preview still works on an unsaved caption.
        try:
            draft = store.draft(draft_id) if hasattr(store, "draft") \
                else None
        except Exception:
            draft = None
        # Sensitivity lives on the draft's collection, not the draft itself.
        # A draft with no collection, or a missing draft, is restricted by
        # default — fail-closed is the whole point of sensitivity.
        sensitivity = "restricted"
        if draft is not None and draft.collection_id and \
                hasattr(store, "collection"):
            coll = store.collection(draft.collection_id)
            if coll is not None:
                sensitivity = coll.sensitivity.value
        if sensitivity == "restricted":
            # Restricted content can never leave; the preview says so for
            # every platform rather than pretending each refused it for a
            # different reason.
            return {"platforms": {
                p: {"ok": False,
                    "rule": "advisor:restricted-never-leaves",
                    "reasons": [], "risk": "RED"}
                for p in platforms}}
        caption = (draft.caption if draft is not None else None) or ""
        caption = caption.strip() or "preview"
        matrix = load_matrix(default_matrix_path())
        router = ContentRouter(matrix)
        variants = router.route(
            DraftForRouting(draft_id=draft_id, caption_seed=caption,
                            sensitivity=sensitivity, style_id="preview",
                            media_refs=()),
            platforms, framing=framing, adult_label=adult_label)
        return {"platforms": {
            v.platform: {"ok": v.screen.ok, "rule": v.screen.rule,
                         "reasons": list(v.screen.reasons),
                         "risk": v.screen.risk}
            for v in variants}}

    def studio_gallery(self, scope: TenantScope) -> dict:
        """Her library: albums, and what is in them.

        Photo bytes are not in here. The list carries ids and a size, and a
        screen fetches each thumbnail on its own — a gallery of fifty photos
        inlined as base64 would be a two-megabyte JSON response on a phone
        network, and every one of those bytes would be re-sent on every
        refresh.
        """
        tenant = scope.tenant.value
        if self.studio is None:
            return {"albums": [], "photos": []}
        return {
            "albums": [{"id": c.collection_id, "label": c.label,
                        "genre": c.genre, "sensitivity": c.sensitivity.value}
                       for c in self.studio.collections(tenant)],
            "photos": self.studio.gallery(tenant),
            "vocabulary": list(self.registry.pack(scope.tenant).content_labels),
        }

    def studio_media(self, scope: TenantScope, media_id: str, size: str):
        """One rendition of one photo, to her, over an authenticated request.

        Only the two browser-made sizes are reachable. The original is on
        disk and is hers, but it is not on a URL: a link that serves a full
        original is one that can be opened by anything holding a session, and
        the export path is the deliberate way to take originals off the node.
        """
        from .adapters.http_api import Response
        if self.studio is None or self.media is None:
            return Response(404, {"error": "not found"})
        try:
            edge = int(size)
        except (TypeError, ValueError):
            return Response(400, {"error": "bad size"})
        if edge not in ALLOWED_EDGES:
            return Response(404, {"error": "not found"})
        tenant = scope.tenant.value
        known = {p["media_id"] for p in self.studio.gallery(
            tenant, include_archived=True)}
        if media_id not in known:
            # Checked against her own library rather than against the
            # filesystem: a path that exists is not the same question as a
            # photo that is hers.
            return Response(404, {"error": "not found"})
        try:
            rel = photo_path(tenant, media_id, 0, edge)
            data = self.media.read(rel)
        except (FailClosedError, OSError):
            return Response(404, {"error": "not found"})
        return Response(200, raw=data, content_type="image/jpeg")

    def export_album(self, scope: TenantScope, collection_id: str):
        """One album, as a zip she can take anywhere.

        Per album rather than the whole archive: a whole-archive zip on this
        hardware is a long request that holds a connection open and builds a
        file bigger than the free memory, and it is not the thing she would
        actually reach for. An album is a job that finishes.

        Originals where they exist, because that is the point of an export.
        """
        import io
        import zipfile

        from .adapters.http_api import Response
        if self.studio is None or self.media is None:
            return Response(404, {"error": "not found"})
        tenant = scope.tenant.value
        if self.studio.collection(collection_id) is None:
            return Response(404, {"error": "not found"})
        photos = self.studio.gallery(tenant, collection_id=collection_id,
                                     include_archived=True)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
            for item in photos:
                mid = item["media_id"]
                for rel, name in self._export_members(tenant, mid, item):
                    try:
                        zf.writestr(name, self.media.read(rel))
                    except OSError:
                        continue      # a row without its file is not fatal
        return Response(200, raw=buf.getvalue(),
                        content_type="application/zip",
                        headers={"Content-Disposition":
                                 f'attachment; filename="{collection_id}.zip"'})

    def _export_members(self, tenant: str, media_id: str, item: Mapping):
        """What goes in the zip for one photo, and under what name.

        JPEGs are stored uncompressed in the archive: they are already
        compressed, and re-compressing them costs CPU on a board with four
        cores and buys almost nothing.
        """
        if item.get("has_original"):
            ext = "png" if item.get("mime") == "image/png" else "jpg"
            yield (original_photo_path(tenant, media_id, 0,
                                       str(item.get("mime") or "image/jpeg")),
                   f"{media_id}/original.{ext}")
        for edge in ALLOWED_EDGES:
            yield (photo_path(tenant, media_id, 0, edge),
                   f"{media_id}/{edge}.jpg")

    def studio_overview(self, scope: TenantScope) -> dict:
        """The third tab: how the work is going, for a creator not a marketer.

        Counts and one comparison, no funnels and no projections. Everything
        here is something she could count herself if she had the patience —
        which is what makes it checkable, and what stops it becoming a
        dashboard that says things nobody can verify.
        """
        tenant = scope.tenant.value
        pack = self.registry.pack(scope.tenant)
        drafts = self.studio.drafts(tenant) if self.studio else []
        by_status: dict[str, int] = {}
        for d in drafts:
            by_status[d.status] = by_status.get(d.status, 0) + 1

        tried = self.studio.label_counts(tenant) if self.studio else {}
        out_there = (self.studio.label_counts(
            tenant, statuses=("queued", "published")) if self.studio else {})

        subs = self.audience.subscribers(tenant) if self.audience else []
        totals = (self.audience.revenue_totals(tenant)
                  if self.audience else {})
        snap = self.audience.latest_snapshot(tenant) if self.audience else []

        return {
            "posts": by_status,
            "labels_vocabulary": list(pack.content_labels),
            "labels_tried": tried,
            "labels_published": out_there,
            "subscribers": len(subs),
            # None rather than zero wherever nothing has been measured: a
            # business with no audience does not have a bad ownership ratio,
            # and an account that has earned nothing has no revenue mix.
            "ownership_ratio": ownership_ratio(snap),
            "revenue_mix": revenue_mix(totals) if totals else None,
            "waiting_for_a_message": len(outreach_drafts(
                subs, now_epoch_s=self.now_epoch_s())),
        }

    def studio_guidance(self, scope: TenantScope) -> dict:
        """The second tab: what to try next, and what would be learned.

        With an empty account there is no data to draw a conclusion from, and
        inventing one is the single thing this advisor exists not to do. So
        when the sample is too small it does not apologise and go blank — it
        proposes the test instead.

        That is a real answer rather than a placeholder: knowing which two
        things to vary, and tagging both, is what makes the next month
        comparable at all. A reading needs posts; an experiment needs only a
        decision.
        """
        tenant = scope.tenant.value
        pack = self.registry.pack(scope.tenant)
        reading = self.studio_reading(scope)
        if reading["enough"]:
            return {"mode": "reading", **reading}

        tried = self.studio.label_counts(tenant) if self.studio else {}
        vocabulary = list(pack.content_labels)
        # Pairs, in the order the pack lists them: each is one axis she can
        # vary on purpose. The first axis she has not tried both sides of is
        # the one worth proposing, because a comparison needs two sides.
        pairs = [(vocabulary[i], vocabulary[i + 1])
                 for i in range(0, len(vocabulary) - 1, 2)]
        suggest = next((p for p in pairs
                        if not (tried.get(p[0]) and tried.get(p[1]))), None)
        return {
            "mode": "experiment",
            "sample": reading["sample"],
            "needed": reading["needed"],
            "vocabulary": vocabulary,
            "tried": tried,
            "suggested_axis": list(suggest) if suggest else [],
            "why": ("برای مقایسه باید از هر دو طرف یک محور، چند تا ساخته "
                    "باشید. تا آن وقت هر نتیجه‌ای حدس است."),
        }

    def request_studio_reading(self, scope: TenantScope) -> dict:
        """Ask for one reading. Tier 0: numbers and labels, never a pixel.

        Every refusal below is a real answer rather than an error to be
        smoothed over. "Not enough posts yet" is the true state of a business
        that has just started, and inventing a reading for it would be the
        one thing this whole advisor exists not to do.
        """
        if self.router is None or self.advisor is None:
            return {"ok": False, "error": "مشاور وصل نیست"}
        now = self.now_epoch_s()
        if self.call_budget is not None and not self.call_budget.allows(
                Rung.REMOTE, now):
            return {"ok": False, "error": "سقف تماس امروز پر شده"}

        measured = self.studio_measurements(scope)
        try:
            request = self.advisor.prepare(
                measured, sample=measured["posts_counted"],
                window_days=measured["window_days"])
        except FailClosedError as exc:
            return {"ok": False, "error": str(exc)}

        if self.call_budget is not None:
            self.call_budget.record(Rung.REMOTE, now)
        result = self.router.ask(
            scope.tenant, RouteRequest(task="studio:reading",
                                       max_rung=Advisor.rung_for(request)),
            request.render(), now_epoch_s=now)
        if getattr(result, "refused", None):
            return {"ok": False, "error": "مشاور جواب نداد"}

        finding = self.advisor.interpret(request, getattr(result, "text", ""),
                                         key="weekly")
        if finding is None:
            # Declining is not failing. A model that says the numbers are not
            # enough has done the right thing, and recording that as advice
            # would make it look like a suggestion with no content.
            return {"ok": True, "finding": None,
                    "note": "مشاور گفت این اعداد برای نتیجه‌گیری کافی نیستند"}

        self.studio.record_finding(
            scope.tenant.value, key=finding.key, claim=finding.claim,
            sample=finding.provenance.sample,
            window_days=finding.provenance.window_days, now_epoch_s=now)
        return {"ok": True, "finding": render_for_screen(finding)}

    def judge_studio_finding(self, scope: TenantScope, key: str,
                             disposition: str) -> dict:
        """Her verdict on a suggestion. A hard rejection is final."""
        if self.studio is None:
            return {"ok": False, "error": "استودیو در دسترس نیست"}
        try:
            self.studio.judge_finding(scope.tenant.value, key, disposition)
        except StudioError as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True}

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
        # Whether her hours are inside `cogs_aud` at all. Read from the pack
        # rather than hardcoded, so that the day a labour term is declared
        # again the screens go back to saying "profit" without an edit here.
        time_counted = bool(pack.labour_hours_field and pack.labour_rate_field)
        view = money_view(p, gst_rate=rate, gst_known=known,
                          time_counted=time_counted)
        # One computation, one answer. The screen, the export and the verdict
        # all read these, so they cannot drift apart.
        out.update(view)
        # Which photo slots this piece has. Sent with the row rather than
        # fetched separately, so the shell cannot render a piece whose photo
        # count belongs to a different one.
        out["photos"] = (self.products.media_of(p.tenant_id, p.sku)
                         if self.products is not None else [])
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
                "gst_known": gst[0], "gst_rate": gst[1],
                # Beside `gst_known` because it is the same kind of fact: a
                # gap the screen must label rather than paper over. The form
                # reads it while a piece is still being typed, before any row
                # exists to carry it.
                "time_counted": bool(pack.labour_hours_field
                                     and pack.labour_rate_field)}

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

    def delete_product(self, scope: TenantScope, actor: str, sku: str,
                       *, reason: str) -> dict:
        """Remove a piece and write down that it was removed.

        Deliberately not reachable over HTTP. Nothing in the partner shells
        deletes anything, and a delete button is not a small feature: it is
        the one action where a mistap costs work that cannot be re-derived.
        This exists for the operator, called deliberately, with a reason that
        goes into the ledger beside the piece it removed.

        The ledger entry carries the whole row, not a reference to it. A
        deletion recorded as "ZM-0001 was deleted" is a note that something
        used to be somewhere; the row itself is what lets somebody put it
        back.
        """
        try:
            piece = self._pieces().delete(scope.tenant.value, sku)
        except ProductError as exc:
            return {"ok": False, "error": str(exc)}
        self.ledger.append(scope, "PRODUCT_DELETED", {
            "sku": piece.sku,
            "reason": reason,
            "actor": actor,
            "removed": {k: getattr(piece, k)
                        for k in piece.__dataclass_fields__ if k != "id"},
        }, self.now_iso())
        return {"ok": True, "sku": piece.sku, "name": piece.name}

    def attach_product_photo(self, scope: TenantScope, user_id: str, sku: str,
                             body: Mapping[str, object]) -> dict:
        """Store the two browser-made renditions of one photo of a piece.

        The original is not kept — D-A settled that: it stays on her phone,
        which is the one place it is already backed up and the one place a
        theft of this board cannot reach.

        The piece must exist first. A media row pointing at nothing is a file
        nothing will ever clean up, and for a photo of somebody's work that
        is a file nobody knows they still have.
        """
        if self.products is None or self.media is None:
            raise ProductError("انبار محصولات در دسترس نیست")
        tenant = scope.tenant.value
        piece = self.products.get(tenant, sku)
        if piece is None:
            return {"ok": False, "error": f"قطعه‌ای با کد «{sku}» پیدا نشد"}
        # `ZM-0001` is what she reads; `zm-0001` is what may be a directory.
        slug = piece_slug(sku)
        try:
            position = body.get("position", 0)
            renditions = body.get("renditions") or {}
            if not isinstance(renditions, Mapping):
                raise FailClosedError("renditions must be an object")
            written = {}
            for edge in ALLOWED_EDGES:
                text = renditions.get(str(edge))
                if not text:
                    raise FailClosedError(f"اندازهٔ {edge} نیامده")
                payload = photo_inspect(str(text))
                written[edge] = self.media.write_rendition(
                    tenant, slug, position, edge, payload)
            biggest = photo_inspect(str(renditions[str(max(ALLOWED_EDGES))]))
            self.products.attach_media(
                tenant, sku, position, mime=biggest.media_type,
                byte_size=biggest.max_decoded_bytes,
                now_iso=self.now_iso())
        except (FailClosedError, ProductError) as exc:
            return {"ok": False, "error": str(exc)}
        self.ledger.append(scope, "PRODUCT_PHOTO", {
            "sku": sku, "position": position, "actor": f"partner:{user_id}",
        }, self.now_iso())
        return {"ok": True, "position": position,
                "photos": self.products.media_of(tenant, sku)}

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

    def studio_assistant_chat(self, scope: TenantScope, body: Mapping[str, object]) -> dict:
        if self.assistant is None:
            return {"ok": False, "error": "حافظهٔ دستیار وصل نیست"}
        q = str(body.get("message") or "").strip()[:800]
        # Scrubbed BEFORE it is persisted: chat turns are stored locally and
        # may later feed shared memory, so identifying data must not land in
        # either. The scrub is visible to the caller so Saba knows her phone
        # number was not stored as typed.
        from .kernel.scrub import scrub as _scrub
        scrubbed = _scrub(q)
        if not scrubbed.clean:
            q = scrubbed.text
            self._assistant_scrub_hits = getattr(
                self, "_assistant_scrub_hits", 0) + 1
        out = self.assistant.answer_local(scope.tenant.value, q)
        # The assistant may echo the user's own words back — scrub the
        # answer too, so no identifying data survives into the turn store.
        ans = _scrub(str(out.get("answer", ""))).text
        turn = self.assistant.record_chat(scope.tenant.value, q, ans, out.get("sources", []), now_epoch_s=self.now_epoch_s())
        return {"ok": True, "turn_id": turn, **out}

    def studio_assistant_suggest(self, scope: TenantScope) -> dict:
        if self.assistant is None:
            return {"ok": False, "error": "حافظهٔ دستیار وصل نیست"}
        out = self.assistant.answer_local(scope.tenant.value, "")
        return {"ok": True, **out}

    def studio_assistant_history(self, scope: TenantScope) -> dict:
        if self.assistant is None:
            return {"ok": False, "error": "حافظهٔ دستیار وصل نیست"}
        return {"ok": True, "turns": self.assistant.chat_history(scope.tenant.value, limit=30)}

    def update_studio_assistant(self, scope: TenantScope) -> dict:
        if self.assistant is None:
            return {"ok": False, "error": "حافظهٔ دستیار وصل نیست"}
        out = self.assistant.answer_local(scope.tenant.value, "نور ایده محتوا امنیت قیمت")
        n = self.assistant.ingest_text(scope.tenant.value, "daily", "آپدیت روزانه", out.get("answer", ""), now_epoch_s=self.now_epoch_s())
        self.assistant.record_run(scope.tenant.value, "daily", "ok", f"{n} chunks", now_epoch_s=self.now_epoch_s())
        # Mutation paired with its record (finding 13).
        self.ledger.append(scope, "ASSISTANT_DAILY_UPDATED", {
            "chunks": n,
        }, self.now_iso())
        return {"ok": True, "chunks": n}

    # ── hypno edge model (UNIFY phase L) ──────────────────────────────────
    # The pure edge math lives in ofn/kernel/edge.py (copied from hypno,
    # stdlib only). These methods serve the same endpoints hypno ran on
    # port 8895, inside OFN. The daily verdict is stored as a fact so the
    # three-red-days rule and history read work without a second store.

    def hypno_edge_decision(self, body: Mapping[str, object]) -> dict:
        """Twelve scores → pole decomposition (body/self/superorganism)."""
        from .kernel.edge import decision_source
        def _f(key: str, default: float = 5.0) -> float:
            try:
                return float(body.get(key, default))
            except (TypeError, ValueError):
                return default
        try:
            result = decision_source(
                _f("V"), _f("P"), _f("K"), _f("D"), _f("H"), _f("E"),
                _f("F"), _f("M"), _f("U"), _f("C"), _f("sleep_debt"),
                _f("stress"))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True,
                "dominant": result.verdict,
                "healthy": result.healthy,
                "ai": result.ai, "si": result.si, "bi": result.bi}

    def hypno_edge_daily(self, scope: TenantScope,
                         body: Mapping[str, object]) -> dict:
        """B/C/X scores → daily verdict, stored for the three-red-days rule."""
        from .kernel.edge import daily_verdict
        try:
            B = int(body.get("B", 0))
            C = int(body.get("C", 0))
            X = int(body.get("X", 0))
        except (TypeError, ValueError):
            return {"ok": False, "error": "امتیازها باید عدد باشند"}
        verdict = daily_verdict(B, C, X)
        day = self.now_iso()[:10]
        payload = {"B": B, "C": C, "X": X, "verdict": verdict.verdict,
                   "day": day}
        # Store as a fact keyed by day: predicate=edge_daily:<day> so each
        # day keeps its own row (assert_fact supersedes same-key rows).
        self.facts.assert_fact(
            scope, "hypno", f"edge_daily:{day}", payload,
            confidence=Confidence.MEASURED,
            observed_at=self.now_iso(), source="hypno:edge_daily")
        # Three red days in a row is the warning rule — use the edge model's
        # own three_red_days, which counts زرد/قرمز (bad) days.
        from .kernel.edge import three_red_days
        daily = [f for f in self.facts.all_active(scope)
                 if f.subject == "hypno"
                 and f.predicate.startswith("edge_daily:")
                 and (f.value or {}).get("day", "") <= day]
        daily.sort(key=lambda f: (f.value or {}).get("day", ""))
        verdicts = [(f.value or {}).get("verdict", "") for f in daily]
        red_verdict = three_red_days(verdicts)
        return {"ok": True,
                "verdict": verdict.verdict, "advice": verdict.advice,
                "three_red_days": red_verdict.verdict == "قرمز"}

    def hypno_edge_history(self, scope: TenantScope,
                           limit: int = 30) -> dict:
        """Recent daily verdicts for the owner."""
        daily = [f for f in self.facts.all_active(scope)
                 if f.subject == "hypno"
                 and f.predicate.startswith("edge_daily:")]
        daily.sort(key=lambda f: (f.value or {}).get("day", ""))
        rows = daily[-limit:]
        out = []
        for f in rows:
            v = dict(f.value or {})
            out.append({"day": v.get("day", ""),
                        "value": v,
                        "recorded_at": f.observed_at})
        return {"ok": True, "entries": out}

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

    def _owner_business(self, tenant: TenantId | str, *,
                        include_missing: bool = False) -> dict:
        """One business as an explicit, owner-safe projection.

        The registry knows a tenant's mechanical shape, not its public name or
        whether the real-world business is active.  Those fields therefore stay
        explicitly unresolved instead of being inferred from pack membership.
        """
        scope = self.registry.scope(tenant)
        pack = self.registry.pack(scope.tenant)
        evidence = self.evidence_for(scope)
        done, total = readiness(pack, evidence)
        counts = dict(self.outbox.counts(scope))
        now = self.now_epoch_s()
        row = {
            "id": scope.tenant.value,
            "identity": {"display_name": None, "status": "not_canonical"},
            "operational_status": {"value": None, "status": "not_modeled"},
            "capacity_units_per_week": pack.capacity_units_per_week,
            "readiness": {"done": done, "total": total},
            "missing_fact_count": total - done,
            "decision_counts": {
                name: int(counts.get(name, 0))
                for name in ("pending", "in_flight", "held", "sent", "failed")
            },
            "audit_event_count": self.ledger.count(scope),
            "gates": {
                "declared": list(pack.gates),
                "closed": [g for g in pack.gates if g in self.closed_gates],
            },
            "quota": {
                "ceiling": self.quota.tenant_ceiling(scope.tenant),
                "spent": self.quota.spent(now, scope.tenant),
                "remaining": self.quota.remaining(now, scope.tenant),
                "persistence": "process_memory",
                "resets_on_restart": True,
            },
            "locale": {
                "id": pack.locale.id,
                "currency_code": pack.locale.currency.code,
                "timezone": pack.locale.timezone,
            },
        }
        if include_missing:
            row["missing_fact_keys"] = [
                key for key, need in sorted(pack.required_facts.items())
                if not ((have := evidence.get(key)) is not None
                        and have.meets(need))
            ]
        return row

    def owner_businesses(self) -> dict:
        """All registered businesses, sorted and measured from local state."""
        return {
            "observed_at": self.now_iso(),
            "businesses": [self._owner_business(t) for t in self.registry],
        }

    def owner_business_snapshot(self, business_id: str) -> dict | None:
        """Safe detail for one known business, or None for an unknown id."""
        if business_id not in self.registry:
            return None
        scope = self.registry.scope(business_id)
        head = self.ledger.head(scope)
        return {
            "observed_at": self.now_iso(),
            "business": self._owner_business(
                business_id, include_missing=True),
            "ledger_head": None if head is None else {
                "seq": head.seq,
                "ts": head.ts,
                "hash_prefix": head.hash[:16],
            },
        }

    def owner_core_snapshot(self) -> dict:
        """Live core state, with process-local and unmeasured facts labelled."""
        now = self.now_epoch_s()
        boot = None
        if self.boot is not None:
            severity = {"ok": 0, "warn": 0, "critical": 0}
            failed_names = []
            for check in self.boot.checks:
                severity[check.severity.value] += 1
                if check.severity.value != "ok":
                    failed_names.append(check.name)
            boot = {
                "status": "startup_snapshot",
                "ok": self.boot.ok,
                "mode": self.boot.mode.value,
                "check_counts": severity,
                "failed_check_names": failed_names,
                "recovered_outbox": self.boot.recovered_outbox,
            }
        worker_status = dict(self.worker.status()) if self.worker is not None else {}
        return {
            "observed_at": self.now_iso(),
            "liveness": {
                "status": "live" if self.healthy() else "failed",
                "source": "live_ledger_read",
            },
            "boot": boot,
            "killed": self.killed,
            "closed_gates": list(self.closed_gates),
            "quota": {
                **dict(self.quota.snapshot(now)),
                "persistence": "process_memory",
                "resets_on_restart": True,
            },
            "worker": {
                "attached": self.worker is not None,
                "queued": int(worker_status.get("queued", 0)),
                "parked": int(worker_status.get("parked", 0)),
                "persistence": "process_memory",
                "reconstructed_after_restart": False,
            },
            "watchdog": {"status": "unknown", "reason": "not_exposed"},
            "brain": {
                "attachment_status": ("attached" if self.worker is not None
                                      else "not_attached"),
                "provider_reachability": "unknown",
            },
        }

    def owner_risks(self, limit: int = OWNER_RISK_ITEM_LIMIT) -> dict:
        """Bounded, payload-free view of the actionable human queue.

        This is deliberately labelled partial.  GREEN work does not enter the
        outbox and denied proposals live in the audit ledger, so claiming this
        is a complete risk register would be false.
        """
        limit = max(0, min(int(limit), OWNER_RISK_ITEM_LIMIT))
        items: list[dict] = []
        states = {"pending": 0, "held": 0}
        tiers = {tier.value: 0 for tier in RiskTier}
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            aggregate = self.outbox.actionable_counts(scope)
            for state, count in aggregate["by_state"].items():
                states[state] = states.get(state, 0) + int(count)
            for tier, count in aggregate["by_tier"].items():
                tiers[tier] = tiers.get(tier, 0) + int(count)
            candidates = [
                (item, "pending")
                for item in self.outbox.pending(scope, limit=limit)
            ] + [
                (item, "held")
                for item in self.outbox.held(scope, limit=limit)
            ]
            for item, state in candidates:
                items.append({
                    "id": item.idem_key,
                    "business_id": item.tenant,
                    "kind": item.kind,
                    "tier": item.tier.value,
                    "state": state,
                    "created_at": item.created_at,
                    "needs_second_confirmation": item.tier is RiskTier.RED,
                })
        items.sort(key=lambda item: (
            item["created_at"], item["business_id"], item["id"]),
            reverse=True)
        visible_items = items[:limit]
        total_actionable = states["pending"] + states["held"]
        return {
            "observed_at": self.now_iso(),
            "coverage": "actionable_queue",
            "completeness": "partial",
            "counts": {**states, "by_tier": tiers},
            "items": visible_items,
            # The item reads above are bounded, while these counts cover the
            # complete queue.  Comparing only with ``len(items)`` would report
            # "not truncated" once every per-tenant read had hit its own cap.
            "items_truncated": total_actionable > len(visible_items),
        }

    @staticmethod
    def _ledger_reason_code(ok: bool, reason: str) -> str:
        if ok:
            return "verified"
        text = reason.casefold()
        if "sequence gap" in text:
            return "sequence_gap"
        if "prev_hash" in text or "broken link" in text:
            return "broken_link"
        if "content edited" in text or "hash" in text:
            return "content_mismatch"
        return "verification_failed"

    def owner_ledger_summary(self) -> dict:
        """Hash-chain health and counts; never event payloads or finance."""
        rows = []
        total = 0
        all_ok = True
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            count = self.ledger.count(scope)
            head = self.ledger.head(scope)
            ok, reason = self.ledger.verify(scope)
            total += count
            all_ok = all_ok and ok
            rows.append({
                "business_id": tenant.value,
                "event_count": count,
                "head": None if head is None else {
                    "seq": head.seq, "ts": head.ts,
                    "hash_prefix": head.hash[:16],
                },
                "verification": {
                    "ok": ok,
                    "reason_code": self._ledger_reason_code(ok, reason),
                },
            })
        return {
            "observed_at": self.now_iso(),
            "kind": "audit_event_ledger",
            "event_count": total,
            "verification": {
                "ok": all_ok,
                "reason_code": "verified" if all_ok else "verification_failed",
            },
            "businesses": rows,
        }

    def owner_snapshot(self) -> dict:
        """Compact home read model; detail stays behind dedicated endpoints."""
        risks = self.owner_risks(limit=0)
        ledger = self.owner_ledger_summary()
        worker_status = dict(self.worker.status()) if self.worker is not None else {}
        return {
            "snapshot_version": "phase2-owner-v1",
            "observed_at": self.now_iso(),
            "availability": {
                "status": "partial",
                "reasons": [
                    "partner_activity_not_measured",
                    "mini_app_health_not_measured",
                    "calibration_not_persisted",
                ],
            },
            "business_count": len(self.registry),
            "decision_counts": {
                "pending": risks["counts"]["pending"],
                "held": risks["counts"]["held"],
            },
            "core": {
                "liveness_status": "live" if self.healthy() else "failed",
                "liveness_source": "live_ledger_read",
                "killed": self.killed,
            },
            "ledger": {
                "kind": ledger["kind"],
                "event_count": ledger["event_count"],
                "verification_status": ledger["verification"]["reason_code"],
            },
            "automation": {
                "thinking": {
                    "attached": self.worker is not None,
                    "queued": int(worker_status.get("queued", 0)),
                    "parked": int(worker_status.get("parked", 0)),
                    "persistence": "process_memory",
                },
                "state_machine": "not_implemented",
            },
            "calibration": {
                "action_score": None,
                "sample_count": None,
                "persisted": False,
                "status": "not_implemented",
            },
            "links": {
                "businesses": "/api/v1/owner/businesses",
                "partners": "/api/v1/owner/partners",
                "mini_apps": "/api/v1/owner/mini-apps",
                "core": "/api/v1/owner/core/snapshot",
                "risks": "/api/v1/owner/risks",
                "ledger": "/api/v1/owner/ledger/summary",
                "painting": "/api/v1/owner/painting/dashboard",
                "mini_webs": "/api/v1/owner/mini-webs",
                "telegram": "/api/v1/owner/telegram",
            },
        }

    def owner_metrics(self) -> dict:
        """Live system metrics: temperature, RAM, load, uptime, disk.

        Read fresh on every call — the panel polls every 30s, and a cached
        reading shown next to a just-pressed kill switch is exactly the
        decision-made-against-the-wrong-screen failure this panel is built
        to prevent. Returns ok=False if the metrics module is absent, rather
        than crashing the panel poll.
        """
        try:
            from .adapters import sysmetrics
            return {"ok": True, **sysmetrics.snapshot(self.state_dir or "")}
        except Exception as exc:
            return {"ok": False, "error": f"metrics unavailable: {exc}"}

    def owner_workboard(self) -> dict:
        """The owner's daily workboard — a read-only projection over the
        canonical stores (O4). No parallel DB: every count below is a query
        against the store that owns that data.

        Sections:
          - today: what needs the owner's hand (approvals, manual completions)
          - lead: follow-ups due, open leads
          - ziman: ready-to-list pieces, stale pieces
          - studio: drafts blocked/ready
          - gaps: held/failed inbox + outbox, ledger gaps
          - missing_facts: per-leg facts the owner has not answered
        """
        now = self.now_iso()
        out: dict[str, object] = {
            "ok": True, "generated_at": now,
            "today": {"approvals": 0, "manual_pending": 0},
            "lead": {}, "ziman": {}, "studio": {},
            "gaps": {"inbox_held": 0, "outbox_held": 0,
                     "ledger_gaps": getattr(self, "_inbox_ledger_gaps", 0)},
            "missing_facts": {},
        }

        # ── outbox: approvals + manual pending ────────────────────────────
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            out["today"]["approvals"] += len(self.outbox.pending(scope))
            out["today"]["manual_pending"] += len(
                self.outbox.approved_manual(scope))
            out["gaps"]["outbox_held"] += len(self.outbox.held(scope))

        # ── inbox: held/failed per tenant (no raw bodies) ─────────────────
        if self.inbox is not None:
            try:
                for tenant in self.registry:
                    counts = self.inbox.counts(tenant.value)
                    out["gaps"]["inbox_held"] += counts.get("held", 0)
            except Exception:
                pass

        # ── lead: open leads + missing required facts ─────────────────────
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            pack = self.registry.pack(tenant)
            evidence = self.evidence_for(scope)
            missing = [k for k, need in sorted(pack.required_facts.items())
                       if not ((h := evidence.get(k)) is not None
                               and h.meets(need))]
            if missing:
                out["missing_facts"][tenant.value] = missing
        if self.painting is not None:
            try:
                leads = self.painting.list_leads("lead", limit=100)
                out["lead"] = {
                    "open": sum(1 for l in leads
                                if l.get("status") in
                                ("new", "review", "contacted", "quoted")),
                    "hot": sum(1 for l in leads
                               if l.get("temperature") == "hot"),
                }
            except Exception:
                out["lead"] = {"open": None, "hot": None,
                               "why": "not_measured"}
        if self.products is not None:
            try:
                pieces = self.products.list("ziman")
                out["ziman"] = {
                    "ready_to_list": sum(
                        1 for p in pieces
                        if p.get("state") in ("photo_ready", "ready")),
                    "stale": sum(
                        1 for p in pieces
                        if p.get("verdicts") and "stale" in p.get("verdicts")),
                }
            except Exception:
                out["ziman"] = {"ready_to_list": None, "stale": None,
                                "why": "not_measured"}
        if self.studio is not None:
            try:
                drafts = self.studio.drafts("studio")
                out["studio"] = {
                    "drafts": len(drafts or []),
                    "ready": sum(1 for d in (drafts or [])
                                 if d.get("status") == "ready"),
                }
            except Exception:
                out["studio"] = {"drafts": None, "ready": None,
                                 "why": "not_measured"}
        return out

    def owner_growth_workbench(self) -> dict:
        """Manual-first growth workbench (O8).

        A read-only facade over the EXISTING per-business workflows — no new
        DB. Each business has its experiment vocabulary mapped onto its own
        store:
          - lead: painting_campaigns + lead outcomes
          - ziman: product listing/sale lifecycle
          - studio: marketing week + draft variants
        Every figure is measured or explicitly not_measured — no vanity
        counts and no invented KPIs.
        """
        out: dict[str, object] = {
            "ok": True, "generated_at": self.now_iso(),
            "lead": {"campaigns": [], "measured_outcomes": 0,
                     "not_measured": []},
            "ziman": {"ready_to_list": 0, "sold": 0, "measured_margin": 0,
                      "margin_blocked": 0},
            "studio": {"week": None, "drafts": 0, "measured": 0},
        }

        # ── lead: campaigns from painting_campaigns ──────────────────────
        if self.painting is not None:
            try:
                campaigns = self.painting.campaigns("lead") or []
                out["lead"]["campaigns"] = [
                    {"campaign_id": c.get("campaign_id"),
                     "title": c.get("title"),
                     "status": c.get("status"),
                     "owner": c.get("owner") or "—"}
                    for c in campaigns[:20]]
                out["lead"]["measured_outcomes"] = sum(
                    1 for c in campaigns
                    if c.get("status") in ("won", "lost", "completed"))
            except Exception:
                out["lead"]["not_measured"].append("campaigns")

        # ── ziman: listing + sale lifecycle from products ────────────────
        if self.products is not None:
            try:
                pieces = self.products.list("ziman")
                # 'for_sale' = priced and listed; 'ready' is the lane name
                # in the megaprompt — the closest real state is for_sale.
                out["ziman"]["ready_to_list"] = sum(
                    1 for p in pieces
                    if p.state in ("for_sale", "ready", "photo_ready"))
                out["ziman"]["sold"] = sum(
                    1 for p in pieces if p.state == "sold")
                # Margin measured only where COGS and a price exist.
                out["ziman"]["measured_margin"] = sum(
                    1 for p in pieces
                    if p.state == "sold" and p.cogs_aud is not None
                    and p.price_primary_aud is not None)
            except Exception:
                out["ziman"]["not_measured"] = ["products"]

        # ── studio: marketing week + drafts ──────────────────────────────
        if self.marketing is not None:
            try:
                week = self.marketing.current_week("studio")
                out["studio"]["week"] = (
                    {"week_id": week.get("week_id"),
                     "status": week.get("status"),
                     "style": week.get("style_id"),
                     "focus": week.get("focus_text")}
                    if week else None)
            except Exception:
                out["studio"]["week"] = None
        if self.studio is not None:
            try:
                out["studio"]["drafts"] = len(
                    self.studio.drafts("studio") or [])
            except Exception:
                pass
        return out

    def public_catalog(self) -> dict:
        """Read-only public catalog (O9) — PREPARED, NOT SERVED.

        The route for this is NOT wired: public activation requires Ari's
        five preconditions (path/domain, privacy text, follow-up owner,
        service area + offer, runbook review). This method is the payload
        builder only — called by a route that does not exist yet.

        No PII: only name, price, state and description of for_sale pieces.
        """
        if self.products is None:
            return {"ok": False, "error": "catalog unavailable"}
        pieces = []
        try:
            for p in self.products.list("ziman"):
                if p.state != "for_sale":
                    continue
                pieces.append({
                    "sku": p.sku, "name": p.name,
                    "description": p.description,
                    "price_primary_aud": p.price_primary_aud,
                })
        except Exception:
            return {"ok": False, "error": "catalog read failed"}
        return {"ok": True, "items": pieces, "count": len(pieces),
                "activated": False}

    def pilot_run(self) -> dict:
        """One bounded read-only pass of the O10 pilot, if wired.

        Returns pilot:disabled when no pilot is wired (the default until
        Ari's decisions) — never a fabricated success.
        """
        if self.pilot is None:
            return {"ok": False, "rule": "pilot:disabled",
                    "error": "pilot not wired"}
        return self.pilot.run()

    def owner_observability(self) -> dict:
        """Inbox visibility for the owner's panel — what this node holds.

        Returns:
            ok: always True (the read itself succeeded)
            webhook_route: True — POST /api/v1/webhooks/ is wired
            vendors_connected: currently always [] — no real vendor is
                connected; this is the honest value, not a placeholder
            tenants: per-tenant inbox counts (pending/processed/failed/depth)

        Not measured here: vendor health (no vendor exists). That key is
        deliberately absent rather than fabricated — the panel must not read
        health where nothing was measured.

        No secrets, no raw webhook bodies, no PII — only counts and statuses.
        """
        out: dict[str, object] = {
            "ok": True,
            "webhook_route": True,          # POST /api/v1/webhooks/ is wired
            "vendors_connected": [],        # no real vendor yet — honest []
            "inbox_ledger_gaps": getattr(self, "_inbox_ledger_gaps", 0),
            "tenants": {},
        }
        # O10 pilot status: honest enabled/disabled + last run, never a
        # fabricated success. No token, no raw data.
        if self.pilot is not None and self.pilot_state is not None:
            out["pilot"] = {
                "enabled": self.pilot.enabled(),
                "vendor": self.pilot_state.connector_id,
                "tenant": self.pilot_state.tenant,
                "cursor": self.pilot_state.cursor or None,
                "last_run_at": self.pilot_state.last_run_at or None,
                "receipts": len(self.pilot_state.receipts),
            }
        # Connector metrics, when wired: counts since boot per connector.
        if self.connector_metrics is not None:
            out["connectors"] = dict(self.connector_metrics.snapshot())
        if self.inbox is not None:
            try:
                for tenant in self.registry:
                    t = tenant.value
                    counts = self.inbox.counts(t)
                    depth = self.inbox.depth(t)
                    out["tenants"][t] = {
                        "inbox_pending": counts.get("pending", 0),
                        "inbox_processed": counts.get("processed", 0),
                        "inbox_failed": counts.get("failed", 0),
                        "inbox_depth": depth,
                        # Backlog flag: depth crossing the threshold is the
                        # local signal the panel and a future alert can key
                        # on. Threshold is deliberately small — there is no
                        # real vendor yet, so ANY sustained backlog is news.
                        "inbox_backlog": depth >= 10,
                    }
            except Exception:
                out["inbox_error"] = "inbox read failed"
        else:
            out["inbox_error"] = "inbox not wired"
        return out

    def _gate_enqueue(self, scope: TenantScope, idem_key: str, kind: str,
                      payload: Mapping[str, object], tier, now_iso: str) -> dict:
        """The single choke point for direct outbox writes.

        Every enqueue that bypasses `propose()` (publish_draft, send_to_outbox,
        send_lead_reply, send_lead_quote) must go through here. The kill switch
        is checked first: if the node is killed, nothing reaches the outbox
        from any path. This does NOT re-run admit/risk/quota — these paths are
        all RED and already require human approval downstream. The gate here
        is specifically the kill switch, which is the one thing a direct
        enqueue was missing.

        Returns {"ok": True, "queued": bool} on success, or
        {"ok": False, "error": ..., "rule": ...} if killed.
        """
        if self.killed:
            return {"ok": False, "error": "kill switch engaged",
                    "rule": "gate:kill-switch"}
        queued = self.outbox.enqueue(scope, idem_key, kind, payload, tier, now_iso)
        return {"ok": True, "queued": queued}

    # ── webhook / connector infrastructure ──────────────────────────────────
    def handle_webhook(self, tenant_name: str | None,
                        connector_id: str,
                        headers: Mapping[str, str],
                        body: bytes) -> dict:
        """Accept an inbound webhook payload and store it in the inbox.

        Called from the HTTP layer before authentication (webhooks are HMAC-
        signed, not session-authenticated). Tenant and connector come from
        the path.

        O3 — real security, no vendor yet:
          - unknown connector → reject (fail closed)
          - connector.verify() must pass; a connector without a verifier
            rejects everything
          - normalise() reduces the payload to safe fields; the raw body is
            stored only as a hash
          - vendor_event_id comes from the connector, not urandom

        Returns a dict with "ok", "status", and optionally "inbox_id" and
        "correlation_id".
        """
        from .adapters.correlation import generate, from_header
        from .adapters.inbound_rate import InboundRateLimiter

        def _metric(name: str, cid: str = "") -> None:
            """Record a connector metric; no-op when metrics are not wired."""
            if self.connector_metrics is not None:
                getattr(self.connector_metrics, name)(cid or "default")

        # No tenant from host resolution — try path-based tenant in the URL.
        if not tenant_name or tenant_name not in self.registry:
            _metric("record_rejected")
            return {"ok": False, "error": "unknown tenant",
                    "status": "rejected"}

        cid = from_header(dict(headers)) or generate()
        if self.inbox is None:
            _metric("record_rejected")
            return {"ok": False, "error": "inbox not wired",
                    "correlation_id": cid, "status": "rejected"}

        # Rate limit: one process-scoped limiter, keyed by tenant.
        if self.rate_limiter is not None:
            verdict = self.rate_limiter.check(tenant_name)
            if not verdict.allowed:
                _metric("record_rejected")
                return {"ok": False, "error": "rate limited",
                        "correlation_id": cid, "status": "rejected",
                        "retry_after_s": verdict.retry_after_s}

        # O3: connector lookup. Unknown connector = reject — a webhook
        # without a known connector is either misrouted or a probe.
        connector = self.connectors.get(connector_id or "")
        if connector is None:
            _metric("record_rejected")
            return {"ok": False, "error": "unknown connector",
                    "correlation_id": cid, "status": "rejected",
                    "rule": "webhook:unknown-connector"}

        _metric("record_inbound", connector_id)

        # O3: signature verification — the connector's own verifier.
        try:
            verdict = connector.verify(body, dict(headers))
        except Exception as exc:
            _metric("record_rejected", connector_id)
            return {"ok": False, "error": f"verifier failed: {exc}",
                    "correlation_id": cid, "status": "rejected",
                    "rule": "webhook:verify-error"}
        if not verdict.valid:
            _metric("record_rejected", connector_id)
            return {"ok": False, "error": "signature invalid",
                    "correlation_id": cid, "status": "rejected",
                    "rule": "webhook:signature-invalid"}

        # O3: normalise to safe fields; drop raw payload entirely.
        scope = self.registry.scope(tenant_name)
        try:
            event = connector.normalise(scope, body, dict(headers), cid)
        except Exception as exc:
            _metric("record_rejected", connector_id)
            return {"ok": False, "error": f"normalise failed: {exc}",
                    "correlation_id": cid, "status": "rejected",
                    "rule": "webhook:normalise-error"}
        if event is None:
            _metric("record_rejected", connector_id)
            return {"ok": False, "error": "payload not for this connector",
                    "correlation_id": cid, "status": "rejected",
                    "rule": "webhook:not-for-connector"}

        now = self.now_iso()
        inbox_id = event.vendor_event_id or cid
        # Store hash + safe fields only (never raw bytes).
        try:
            stored = self.inbox.store(
                tenant=tenant_name,
                connector_id=connector_id,
                vendor=event.vendor,
                vendor_event_id=inbox_id,
                correlation_id=cid,
                body=body,          # store() hashes it; raw never persisted
                inbox_id=inbox_id,
                now_iso=now,
                event_type=event.event_type,
            )
        except Exception:
            _metric("record_failed", connector_id)
            return {"ok": False, "error": "inbox store failed",
                    "correlation_id": cid, "status": "rejected"}
        if not stored:
            _metric("record_rejected", connector_id)
            return {"ok": False, "error": "duplicate webhook",
                    "correlation_id": cid, "status": "rejected"}

        _metric("record_processed", connector_id)

        try:
            self.ledger.append(scope, "WEBHOOK_RECEIVED", {
                "inbox_id": inbox_id,
                "correlation_id": cid,
                "vendor": event.vendor,
                "connector": connector_id,
            }, now)
        except Exception as exc:
            self._inbox_ledger_gaps = getattr(self, "_inbox_ledger_gaps", 0) + 1
            import sys
            print(f"  ⚠ webhook stored but ledger append failed: {exc}",
                  file=sys.stderr)

        return {"ok": True, "status": "accepted",
                "inbox_id": inbox_id, "correlation_id": cid}

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
        # The kill switch must block approval even on already-queued items.
        # Without this, a killed node could still claim and (eventually) send
        # anything already in the outbox, defeating the purpose of the switch.
        if self.killed and approve:
            return {"ok": False, "error": "kill switch engaged",
                    "rule": "gate:kill-switch"}
        tenant_name, _, key = item_id.partition(":")
        if not key or tenant_name not in self.registry:
            return {"ok": False, "error": "unknown item"}
        scope = self.registry.scope(tenant_name)
        item = self.outbox.get(scope, key)
        if item is None:
            return {"ok": False, "error": "unknown item"}

        now = self.now_iso()
        if not approve:
            # Explicit rejected state (O2), alias-compatible: old reports
            # read failed/rejected the same way, but the state is now real.
            if self.outbox.reject(scope, key, now, note="rejected by owner"):
                self.ledger.append(scope, "VERDICT",
                                   {"item": key, "approved": False}, now)
                return {"ok": True, "status": "rejected"}
            # Fallback for states reject() refuses (terminal): mark_failed
            # keeps old behaviour for held/in_flight items.
            self.outbox.mark_failed(scope, key, now, note="rejected by owner")
            self.ledger.append(scope, "VERDICT",
                               {"item": key, "approved": False}, now)
            return {"ok": True, "status": "rejected"}

        gate = executable(
            Decision(True, item.tier, "queued", rule="queued"),
            human_approved=True, confirmed_twice=confirmed_twice)
        if not gate.allowed:
            return {"ok": False, "error": gate.reason, "rule": gate.rule}

        # O2: approval is approval ONLY. It must NOT claim() — no sender
        # exists, so in_flight would strand the item forever. The item waits
        # in approved_manual until a human completes it manually.
        approved = self.outbox.approve_manual(
            scope, key, now, approved_by="owner")
        if not approved:
            # Item was not pending (e.g. already approved) — say so.
            return {"ok": False, "error": "item is not pending approval",
                    "rule": "outbox:not-pending"}
        self.ledger.append(scope, "VERDICT", {
            "item": key, "approved": True, "tier": item.tier.value,
            "delivery_mode": "manual",
        }, now)
        return {"ok": True, "status": "approved_manual",
                "delivery_mode": "manual"}

    # ── manual dispatch (operations launch O2) ────────────────────────────
    def owner_outbox_packet(self, item_id: str) -> dict:
        """The exact manual packet a human is about to send (read-only).

        Built from the approved item's payload; nothing is mutated. The
        packet hash is the witness the completion receipt carries.
        """
        tenant_name, _, key = item_id.partition(":")
        if not key or tenant_name not in self.registry:
            return {"ok": False, "error": "unknown item"}
        scope = self.registry.scope(tenant_name)
        item = self.outbox.get(scope, key)
        if item is None or item.status != APPROVED_MANUAL:
            return {"ok": False, "error": "item is not approved for manual"}
        from .adapters.manual_dispatch import ManualPacket
        payload = dict(item.payload or {})
        text = str(payload.get("text") or payload.get("caption")
                   or payload.get("message") or "")
        packet = ManualPacket(
            idem_key=key, tenant=tenant_name, kind=item.kind,
            text=text,
            target=str(payload.get("to") or payload.get("target") or ""),
            channels=(str(payload.get("channel") or ""),),
            meta={k: v for k, v in payload.items()
                  if k not in ("text", "caption", "message", "to", "target",
                               "channel")},
        )
        return {"ok": True, "packet": {
            "idem_key": key, "kind": item.kind, "text": text,
            "target": packet.target, "channels": list(packet.channels),
            "sha256": packet.sha256(),
        }}

    def owner_outbox_complete(self, item_id: str, body: Mapping[str, object],
                              *, confirmed_twice: bool = False) -> dict:
        """Record that a human manually delivered an approved item.

        Idempotent: a second completion is a no-op, never a duplicate
        effect. RED items still need the second confirmation. The packet
        hash must match the packet endpoint's — the receipt is a witness,
        not a claim.
        """
        tenant_name, _, key = item_id.partition(":")
        if not key or tenant_name not in self.registry:
            return {"ok": False, "error": "unknown item"}
        scope = self.registry.scope(tenant_name)
        item = self.outbox.get(scope, key)
        if item is None:
            return {"ok": False, "error": "unknown item"}
        if item.status != APPROVED_MANUAL:
            return {"ok": False, "error": "item is not approved for manual",
                    "rule": "outbox:not-approved-manual"}
        # Kill + gates re-checked at completion (rule 5).
        if self.killed:
            return {"ok": False, "error": "kill switch engaged",
                    "rule": "gate:kill-switch"}
        if item.tier is RiskTier.RED and not confirmed_twice:
            return {"ok": False, "error": "completion needs second confirmation",
                    "rule": "release:awaiting-second-confirm"}
        channel = str(body.get("channel") or "manual")[:40]
        packet_sha = str(body.get("packet_sha256") or "")[:64]
        external_ref = str(body.get("external_ref_digest") or "")[:64]
        completed = self.outbox.complete_manual(
            scope, key, self.now_iso(),
            completed_by=str(body.get("completed_by") or "owner")[:80],
            channel=channel, packet_sha256=packet_sha,
            external_ref_digest=external_ref)
        if not completed:
            return {"ok": False, "error": "item not in approved_manual state"}
        self.ledger.append(scope, "MANUAL_COMPLETED", {
            "item": key, "channel": channel,
            "packet_sha256": packet_sha or None,
        }, self.now_iso())
        return {"ok": True, "status": "manual_completed",
                "completed_at": self.now_iso()}

    def owner_approved_manual(self) -> list[dict]:
        """Approved items waiting for a human to complete them, per leg."""
        out: list[dict] = []
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            for item in self.outbox.approved_manual(scope):
                out.append({
                    "id": item.idem_key,
                    "tenant": item.tenant,
                    "kind": item.kind,
                    "tier": item.tier.value,
                    "payload": dict(item.payload),
                    "approved_at": item.approved_at,
                    "needs_double_confirm": item.tier is RiskTier.RED,
                })
        return out

    # ── real publish (O11, Ari approved 2026-08-10) ───────────────────────
    # The ONLY real send path. Everything before it is enforced here, in
    # code, at call time — never assumed:
    #   - require_release_context() must be green (gates + two-step)
    #   - dry_run=True returns the diff WITHOUT touching the network
    #   - one tenant (studio) + one platform (telegram_channel) + cap 1
    #   - the channel id and token come from config at call time
    def set_telegram_channel(self, channel_id: str) -> dict:
        """Record the broadcast channel (owner-only; not a secret — it is
        visible in the channel's public URL). After this, publish works."""
        cid = str(channel_id or "").strip()
        if not cid:
            return {"ok": False, "error": "channel id required"}
        self._telegram_channel_id = cid
        # Mutation paired with its record (finding 13): who set the channel
        # and when matters as much as the id itself.
        self.ledger.append(self.registry.scope("studio"),
                           "TELEGRAM_CHANNEL_SET", {
                               "channel_id": cid,
                           }, self.now_iso())
        return {"ok": True, "channel_id": cid}

    def publish_to_telegram(self, scope: TenantScope, *, idem_key: str,
                            caption: str, dry_run: bool = True,
                            confirmed_twice: bool = False) -> dict:
        from .kernel.release_switch import (
            ReleaseContext, require_release_context,
        )
        # Build the release context from THIS node's real state.
        ctx = ReleaseContext(
            owner_confirmed_step1=True,
            owner_confirmed_step2=confirmed_twice,
            secret_rotation_open="secret_rotation" not in self.closed_gates,
            partner_precondition_open=(
                "partner_precondition" not in self.closed_gates),
            kill_switch_active=self.killed,
            sensitivity="general",
            consent_ok=True,
            platform_ok=True,
            rate_limit_ok=True,
            idempotency_unused=True,
            ledger_ready=True,
        )
        verdict = require_release_context(ctx)
        if not verdict.ok:
            return {"ok": False, "error": "release blocked",
                    "rule": verdict.rule, "risk": verdict.risk}
        # One item cap: this path publishes exactly one message per call.
        if len(caption) > 4096:
            return {"ok": False, "error": "caption too long",
                    "rule": "publish:caption-too-long"}
        channel_id = str(getattr(self, "_telegram_channel_id", "") or "")
        if not channel_id:
            return {"ok": False, "error": "channel not configured",
                    "rule": "publish:no-channel"}
        from .adapters.platforms.telegram_channel import (
            TelegramChannelAdapter,
        )
        adapter = TelegramChannelAdapter(channel_id)
        from .adapters.platforms.base import PublishRequest
        req = PublishRequest(
            platform="telegram_channel", idempotency_key=idem_key,
            caption=caption, dry_run=dry_run)
        # Token at call time, from config (never printed/logged).
        token = str(self._telegram_token or "")
        result = adapter.publish(req, token=token)
        if result.ok:
            self.ledger.append(scope, "TELEGRAM_PUBLISHED", {
                "idem": idem_key, "dry_run": dry_run,
                "external_id": result.external_id,
            }, self.now_iso())
        else:
            self.ledger.append(scope, "TELEGRAM_PUBLISH_REFUSED", {
                "idem": idem_key, "rule": result.rule, "dry_run": dry_run,
            }, self.now_iso())
        return {"ok": result.ok, "rule": result.rule,
                "external_id": result.external_id, "dry_run": dry_run}

    # ── consent administration (O7) ────────────────────────────────────────
    # Owner-only: partners may see gaps and request review, but only the
    # owner records releases or revokes them. Only digest/location/scope/
    # time — never document bytes.

    def owner_consent_subjects(self, tenant: str = "studio") -> dict:
        if self.consent is None:
            return {"ok": False, "error": "consent not wired"}
        scope = self.registry.scope(tenant)
        subjects = self.consent.subjects(scope.tenant.value)
        return {"ok": True, "subjects": [
            {"subject_id": s.subject_id, "label": s.display_label}
            for s in subjects]}

    def owner_consent_gaps(self, tenant: str = "studio") -> dict:
        """Drafts whose subjects lack a live release for their platform."""
        if self.consent is None or self.studio is None:
            return {"ok": False, "error": "consent not wired"}
        scope = self.registry.scope(tenant)
        drafts = self.studio.drafts(scope.tenant.value) or []
        gaps = []
        for d in drafts:
            did = d.draft_id if hasattr(d, "draft_id") else d.get("draft_id")
            subjects = self.consent.subjects_in_draft(did)
            releases = self.consent.releases_for(
                [s.subject_id for s in subjects])
            missing = [s.subject_id for s in subjects
                       if not any(r.subject_id == s.subject_id
                                  for r in releases)]
            if missing:
                gaps.append({"draft_id": did, "missing_subjects": missing})
        return {"ok": True, "gaps": gaps}

    def owner_consent_add_subject(self, body: Mapping[str, object],
                                  tenant: str = "studio") -> dict:
        if self.consent is None:
            return {"ok": False, "error": "consent not wired"}
        scope = self.registry.scope(tenant)
        sid = str(body.get("subject_id") or "").strip()
        label = str(body.get("label") or "").strip()
        if not sid or not label:
            return {"ok": False, "error": "subject_id and label required"}
        try:
            self.consent.add_subject(scope.tenant.value, sid, label,
                                     now_epoch_s=self.now_epoch_s())
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "subject_id": sid}

    def owner_consent_add_release(self, body: Mapping[str, object],
                                  tenant: str = "studio") -> dict:
        if self.consent is None:
            return {"ok": False, "error": "consent not wired"}
        scope = self.registry.scope(tenant)
        rid = str(body.get("release_id") or "").strip()
        sid = str(body.get("subject_id") or "").strip()
        plat = str(body.get("scope") or "").strip()
        if not rid or not sid or not plat:
            return {"ok": False, "error": "release_id, subject_id, scope required"}
        try:
            self.consent.record_release(
                rid, sid, scope=plat, signed_at=int(body.get("signed_at")
                                                    or self.now_epoch_s()),
                document_ref=str(body.get("document_ref") or "owner-recorded"),
                document_sha256=str(body.get("document_sha256") or "")
                or ("0" * 64),
                recorded_by="owner")
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "release_id": rid}

    def owner_consent_revoke(self, release_id: str,
                             tenant: str = "studio") -> dict:
        if self.consent is None:
            return {"ok": False, "error": "consent not wired"}
        scope = self.registry.scope(tenant)
        try:
            self.consent.revoke(release_id, now_epoch_s=self.now_epoch_s())
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "release_id": release_id, "revoked": True}

    # ── kill switch ───────────────────────────────────────────────────────
    # The panic button. `killed=True` makes `admit()` refuse every action at
    # gate:kill-switch (gates.py:55), before quota or risk are even computed.
    # This is the one control the owner must always be able to reach.
    #
    # Engage is one tap and fail-safe: the system moves *toward* safety, so
    # speed matters more than ceremony. Release is two-step because it is
    # re-entering risk — the same rule that governs every RED action.
    #
    # State lives in process memory; a restart disengages (killed=False by
    # default). That is the correct failure mode: a rebooted organism comes
    # back running, and if the owner wanted it halted they press the button
    # again. Persisting `killed=True` across reboots would be the bug — an
    # owner who reboots to "fix" a stuck state would find nothing fixed.
    # The *audit trail* persists, in the pre-provisioned release_switch_events
    # table, so "when did this happen and why" survives the restart.
    def engage_kill(self, *, reason: str, owner_id: str,
                    session_id: str) -> dict:
        """Panic button. Halts all outbound activity immediately."""
        if self.killed:
            return {"ok": True, "status": "already-engaged"}
        self.killed = True
        self._record_release_event(
            "kill_switch_on", reason, owner_id, session_id)
        return {"ok": True, "status": "engaged", "killed": True}

    def release_kill(self, *, reason: str, owner_id: str, session_id: str,
                     confirmed_twice: bool) -> dict:
        """Re-arm. Two-step because release is re-entering risk."""
        if not self.killed:
            return {"ok": True, "status": "already-released", "killed": False}
        if not confirmed_twice:
            return {"ok": False,
                    "error": "release needs two-step confirmation",
                    "rule": "release:awaiting-second-confirm"}
        self.killed = False
        self._record_release_event(
            "kill_switch_off", reason, owner_id, session_id)
        return {"ok": True, "status": "released", "killed": False}

    def _record_release_event(self, event_type: str, reason: str,
                              owner_id: str, session_id: str) -> None:
        """Write the audit row and log to the ledger of every leg.

        Kill switch is a node-wide decision with a node-wide effect, so it is
        recorded under the first tenant (the same convention
        `painting_dashboard` uses for cross-tenant surfaces) AND logged to
        every leg's ledger — so a partner reviewing their own history sees
        that something halted their work, even though they did not trigger it.
        """
        now = self.now_iso()
        now_epoch = self.now_epoch_s()
        if self.marketing is not None:
            first_tenant = next(iter(self.registry))
            try:
                self.marketing.record_release_event(
                    first_tenant.value,
                    event_type=event_type, owner_id=owner_id,
                    session_id=session_id,
                    reason=reason or "(no reason given)",
                    now_epoch_s=now_epoch,
                )
            except Exception:
                # The audit table is best-effort: a schema mismatch or a
                # locked DB must not prevent the kill itself from taking
                # effect. The ledger write below is the durable record.
                pass
        payload = {"event": event_type, "reason": reason or "(no reason given)",
                   "owner": owner_id}
        for tenant in self.registry:
            scope = self.registry.scope(tenant)
            self.ledger.append(scope, "KILL_SWITCH", payload, now)


    # ── painting lead CRM ─────────────────────────────────────────────────
    def _lead_scope(self) -> TenantScope | None:
        if "lead" not in self.registry:
            return None
        return self.registry.scope("lead")

    def painting_leads(self, *, status: str = "", q: str = "", limit: int = 50) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        return {"ok": True, "leads": self.painting.list_leads(scope.tenant.value, status=status, q=q, limit=limit)}

    def painting_dashboard(self) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        self.painting.ensure_seed_channels(scope.tenant.value, self.now_iso())
        if hasattr(self.painting, "ensure_seed_modules"):
            self.painting.ensure_seed_modules(scope.tenant.value, self.now_iso())
        if hasattr(self.painting, "ensure_source_registry"):
            try:
                import os
                path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "painting_source_registry.json")
                with open(path, "r", encoding="utf-8") as fh:
                    self.painting.ensure_source_registry(scope.tenant.value, json.load(fh).get("sources", []), self.now_iso())
            except Exception as exc:
                import sys
                print(f"WARN painting_source_registry load failed: {exc}", file=sys.stderr)
        return {"ok": True, **self.painting.dashboard(scope.tenant.value), "mini_webs": self.owner_mini_webs_summary(), "telegram": self.owner_telegram_summary()}

    def create_painting_lead(self, body: Mapping[str, object], *, actor: str = "owner") -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.create_lead(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            lead = out.get("lead") or {}
            self.ledger.append(scope, "LEAD_CAPTURED", {
                "lead_id": lead.get("lead_id"),
                "source": lead.get("source"),
                "score": lead.get("score"),
                "actor": actor,
            }, self.now_iso())
        return out

    def update_painting_lead(self, lead_id: str, body: Mapping[str, object], *, actor: str = "owner") -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.update_lead(scope.tenant.value, lead_id, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "LEAD_UPDATED", {
                "lead_id": lead_id,
                "status": (out.get("lead") or {}).get("status"),
                "actor": actor,
            }, self.now_iso())
        return out

    # ── lead outbound: reply / quote ─────────────────────────────────────
    # Mirrors the studio publish path (`publish_draft`, node.py:480). A partner
    # composes a reply or quote; it goes into the outbox as RED (it leaves the
    # device and may carry PII) and lands in the owner's queue for approval.
    # Nothing is sent until the owner double-confirms — same fail-closed door
    # studio uses. A pure internal note never leaves the device, so it is
    # captured as an interaction + ledger row and needs no approval.
    _REPLY_CHANNELS = {"note", "sms", "email"}

    def send_lead_reply(self, lead_id: str, body: Mapping[str, object],
                        *, actor: str = "partner") -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        lead = self.painting.get(scope.tenant.value, lead_id)
        if not lead:
            return {"ok": False, "error": "لید پیدا نشد"}
        channel = str(body.get("channel") or "note").strip().lower()
        if channel not in self._REPLY_CHANNELS:
            return {"ok": False, "error": "کانال جواب درست نیست"}
        message = str(body.get("message") or "").strip()
        if not message:
            return {"ok": False, "error": "متن جواب خالی است"}
        if len(message) > 2000:
            message = message[:2000]
        now = self.now_iso()
        actor_tag = f"{actor}"

        # A note stays inside the node — reversible, no PII leaves. Capture it
        # as an interaction on the lead and record a ledger row. No outbox.
        if channel == "note":
            self.painting.create_interaction(scope.tenant.value, {
                "lead_id": lead_id,
                "channel": "note",
                "kind": "partner_note",
                "person": lead.get("customer_name") or "",
                "subject": "یادداشت پارتنر",
                "body": message,
                "status": "done",
            }, now_iso=now)
            self.ledger.append(scope, "LEAD_NOTE_CAPTURED", {
                "lead_id": lead_id, "actor": actor_tag,
            }, now)
            return {"ok": True, "kind": "note"}

        # SMS/email leave the device and may contain the customer's name,
        # phone, or address — that is always RED (irreversible + PII), so it
        # goes through the owner-approval gate like a studio publish.
        digest = hashlib.sha1(
            f"{channel}|{message}".encode("utf-8")).hexdigest()[:16]
        idem = f"lead-reply:{lead_id}:{channel}:{digest}"
        payload = {
            "lead_id": lead_id,
            "channel": channel,
            "message": message,
            "customer_name": lead.get("customer_name") or "",
            "to": lead.get("phone") if channel == "sms" else lead.get("email"),
        }
        gate = self._gate_enqueue(
            scope, idem, "lead:reply", payload, RiskTier.RED, now)
        if not gate["ok"]:
            return gate
        queued = gate["queued"]
        self.ledger.append(scope, "LEAD_REPLY_QUEUED", {
            "lead_id": lead_id, "channel": channel,
            "duplicate": not queued, "actor": actor_tag,
        }, now)
        # If the lead was still untouched, mark it as contacted so the pipeline
        # reflects reality. This mirrors studio's draft→queued transition.
        if lead.get("status") == "new":
            self.painting.update_lead(scope.tenant.value, lead_id,
                                      {"status": "contacted"}, now_iso=now)
        return {"ok": True, "queued": queued, "kind": channel}

    def send_lead_quote(self, lead_id: str, body: Mapping[str, object],
                        *, actor: str = "partner") -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        lead = self.painting.get(scope.tenant.value, lead_id)
        if not lead:
            return {"ok": False, "error": "لید پیدا نشد"}
        # A price is money and irreversible — there is no configuration that
        # makes a quote anything but RED.
        try:
            amount = float(body.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        if amount <= 0:
            return {"ok": False, "error": "قیمت درست نیست"}
        if amount > 1_000_000:
            return {"ok": False, "error": "قیمت خیلی بزرگ است"}
        note = str(body.get("note") or "").strip()[:800]
        items = body.get("items") or []
        now = self.now_iso()
        actor_tag = f"{actor}"
        digest = hashlib.sha1(
            f"quote|{amount}|{note}".encode("utf-8")).hexdigest()[:16]
        idem = f"lead-quote:{lead_id}:{digest}"
        payload = {
            "lead_id": lead_id,
            "amount": amount,
            "note": note,
            "items": items if isinstance(items, list) else [],
            "customer_name": lead.get("customer_name") or "",
        }
        gate = self._gate_enqueue(
            scope, idem, "lead:quote", payload, RiskTier.RED, now)
        if not gate["ok"]:
            return gate
        queued = gate["queued"]
        self.ledger.append(scope, "LEAD_QUOTE_QUEUED", {
            "lead_id": lead_id, "amount": amount,
            "duplicate": not queued, "actor": actor_tag,
        }, now)
        if lead.get("status") in ("new", "contacted", "review"):
            self.painting.update_lead(scope.tenant.value, lead_id,
                                      {"status": "quoted"}, now_iso=now)
        return {"ok": True, "queued": queued}

    def upsert_painting_channel(self, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.upsert_channel(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_CHANNEL_UPSERT", {"channel": out.get("channel")}, self.now_iso())
        return out

    def upsert_painting_campaign(self, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.upsert_campaign(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_CAMPAIGN_UPSERT", {"campaign": out.get("campaign")}, self.now_iso())
        return out

    def upsert_painting_module(self, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.upsert_module(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_MODULE_UPSERT", {"module": out.get("module")}, self.now_iso())
        return out

    def create_painting_interaction(self, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.create_interaction(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_INTERACTION_CAPTURED", {"interaction": out.get("interaction"), "channel": body.get("channel")}, self.now_iso())
        return out

    def update_painting_interaction(self, interaction_id: str, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.update_interaction(scope.tenant.value, interaction_id, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_INTERACTION_UPDATED", {"interaction": interaction_id}, self.now_iso())
        return out

    def create_painting_account(self, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.create_account(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_B2B_ACCOUNT_UPSERT", {"account": out.get("account"), "recommendation": out.get("recommendation")}, self.now_iso())
        return out

    def create_painting_tender(self, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.create_tender(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_TENDER_UPSERT", {"tender": out.get("tender"), "recommendation": out.get("recommendation")}, self.now_iso())
        return out

    def create_painting_vendor_application(self, body: Mapping[str, object]) -> dict:
        if self.painting is None:
            return {"ok": False, "error": "ذخیره‌ساز لید وصل نیست"}
        scope = self._lead_scope()
        if scope is None:
            return {"ok": False, "error": "پک لید نقاشی روی این نود نیست"}
        out = self.painting.create_vendor_application(scope.tenant.value, body, now_iso=self.now_iso())
        if out.get("ok"):
            self.ledger.append(scope, "PAINTING_VENDOR_APP_UPSERT", {"application": out.get("application"), "status": out.get("status")}, self.now_iso())
        return out

    def owner_mini_webs_summary(self) -> dict:
        return {
            "hosts": [
                {"id": "owner", "host": "panel.master-painting.com", "port": 8794, "role": "owner", "purpose": "کنترل پنل"},
                {"id": "lead", "host": "lead.master-painting.com", "port": 8792, "role": "partner", "purpose": "مینی‌وب لید نقاشی"},
                {"id": "studio", "host": "studio.master-painting.com", "port": 8793, "role": "partner", "purpose": "استودیو"},
                {"id": "app", "host": "app.master-painting.com", "port": 8793, "role": "partner", "purpose": "مسیر /sabaapp"},
                {"id": "ziman", "host": "ziman.master-painting.com", "port": 8791, "role": "partner", "purpose": "زیمان"},
                {"id": "hypno", "host": "hypno.master-painting.com", "port": 8895, "role": "external", "purpose": "سرویس جداگانه hypno"},
            ],
            "note": "سلامت host از کانفیگ تونل گزارش می‌شود؛ توکن‌ها و شناسه‌های حساب نمایش داده نمی‌شوند.",
        }

    def owner_telegram_summary(self) -> dict:
        return {
            "bots": [
                {"id": "owner", "configured": True, "surface": "پنل مالک"},
                {"id": "lead", "configured": True, "surface": "مینی‌اپ لید نقاشی"},
                {"id": "studio", "configured": True, "surface": "استودیو"},
                {"id": "studio_partner", "configured": True, "surface": "ورود شریک استودیو"},
                {"id": "ziman", "configured": True, "surface": "زیمان"},
            ],
            "identifiers": "omitted",
            "tokens": "omitted",
        }

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
        # Every store that owns a SQLite Pool must be closed here. A store
        # omitted from this list leaks its connection until the process exits
        # — which on a long-running board means WAL files grow without bound.
        stores = [self.ledger, self.facts, self.outbox, self.painting,
                  self.products, self.studio, self.consent,
                  self.audience, self.marketing, self.assistant]
        if self.inbox is not None:
            stores.append(self.inbox)
        for store in stores:
            if store is None:
                continue
            try:
                store.close()
            except Exception as exc:
                # Log rather than swallow: a close failure on shutdown is
                # rare enough to be worth seeing, and silent masking is what
                # hid the missing stores in the first place.
                import sys
                print(f"  ⚠ close failed for {type(store).__name__}: {exc}",
                      file=sys.stderr)
