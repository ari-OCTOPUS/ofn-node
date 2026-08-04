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
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from .adapters.boot import BootReport, closed_gates_for
from .adapters.facts import FactStore
from .adapters.ledger import Ledger
from .adapters.outbox import Outbox
from .adapters.products import (ProductError, ProductStore, money_view,
                                net_margin_aud, piece_slug, verdicts)
from .adapters.studio_store import StudioError
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

    # ── gates ─────────────────────────────────────────────────────────────
    @property
    def closed_gates(self) -> tuple[str, ...]:
        """Base gates plus anything this boot added (e.g. SAFE MODE)."""
        if self.boot is None:
            return self.base_closed_gates
        return closed_gates_for(self.boot, self.base_closed_gates)

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
        try:
            position = body.get("position", 0)
            renditions = body.get("renditions") or {}
            if not isinstance(renditions, Mapping):
                raise FailClosedError("renditions must be an object")
            written = {}
            for edge in ALLOWED_EDGES:
                text = renditions.get(str(edge))
                if not text:
                    raise FailClosedError(f"رساله‌ی {edge} نیامده")
                payload = photo_inspect(str(text))
                written[edge] = self.media.write_rendition(
                    tenant, draft_id, position, edge, payload)
            store.attach_media(draft_id, position, written[max(ALLOWED_EDGES)])
        except (FailClosedError, StudioError) as exc:
            return {"ok": False, "error": str(exc)}
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
        queued = self.outbox.enqueue(
            scope, f"draft:{draft_id}:{platform}", "PUBLISH_POST",
            {"draft_id": draft_id, "platform": platform,
             "caption": draft.caption,
             "media": [ref for _, ref in store.media_of(draft_id)]},
            RiskTier.RED, self.now_iso())
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
            self.studio.add_media(
                tenant, media_id, mime=biggest.media_type,
                byte_size=biggest.max_decoded_bytes, has_original=kept,
                now_epoch_s=self.now_epoch_s(),
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
        return {"ok": True, "labels": chosen}

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
