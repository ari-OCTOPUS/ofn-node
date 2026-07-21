#!/usr/bin/env python3
"""live_loop.py — پاسِ نهاییِ wiring: مغزِ Project-F ↔ کاکپیتِ آری روی یک UnifiedBus.

W-1: route مغزِ Project-F: high-risk → صفِ تأییدِ کاکپیتِ آری؛ verdict → برگشت به مغز+صبا.
W-2: یک bus: legs/gates/doctor/box/rhythm/spectral/sensory/telegram همگی publish/subscribe.
W-3: doctor.run_cycle advisory + rhythm/spectral/afferent به‌عنوان advisory signals.

خطِ قرمز: approve تنها مسیرِ settle · صفر انتشارِ خودکار · دوکلیده · صفر رسانه/PII ·
money قفل/shadow · λ_persist<0 · advisory سیگنال‌ها هرگز اثر نزنند · Project-F containment.

additive؛ stdlib-only؛ $0 آفلاین. مسیرِ قدیمی deprecated نه deleted.
"""
from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent   # _ops
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "budget"))
sys.path.insert(0, str(_HERE / "brain"))

# G3 arc (ported to master 2026-07-18، خاستگاه: شاخهٔ 484bafd). کارتِ پیشنهاد →
# دکمهٔ مالک → outcome → متریک. پشتِ OCTOPUS_WIRE_PROPOSAL_BUTTONS، پیش‌فرض خاموش.
_PROPOSAL_CB_MAX = 500                       # سقفِ نگاشتِ token→پیشنهاد (ارگانیسم ماه‌ها زنده است)
_PROPOSAL_VERBS = {"ok": "approved", "no": "rejected"}   # verbِ دکمه → verdict (later عمداً نیست)
_PROPOSAL_DEFER = "later"                    # «بعداً» تعویق است، نه تصمیم — کارت زنده می‌ماند


@dataclass
class VerdictResult:
    """نتیجهٔ verdict از آری."""
    approved: bool
    effect_id: str
    source: str   # "ari" | "lead-naghshi" | ...
    project: str  # "Project-F" | "Lead-نقاشی" | ...


class LiveLoop:
    """حلقهٔ زندهٔ واحد. همهٔ لایه‌ها روی یک UnifiedBus.
    brain(صبا→مغز→آری) + advisory signals + doctor.

    این wire layer است — هیچ‌کدام از ماژول‌های زیرین را تغییر نمی‌دهد.
    فقط آن‌ها را به هم وصل می‌کند."""

    def __init__(self, bus=None, brain=None, studio=None, cockpit=None,
                 approval_channel=None, doctor=None, effect_status_fn=None,
                 leg=None):
        # bus: اگر نباشد → یک busِ in-memory (تست)
        self.bus = bus or _InMemoryBus()
        self.brain = brain
        self.studio = studio
        self.cockpit = cockpit
        self.channel = approval_channel
        self.doctor = doctor
        # W-3 (2026-07-10): نگهداریِ پا — دیگر پارامترِ leg در wiring drop نمی‌شود.
        # process_lead می‌تواند بدونِ آرگومانِ صریح از همین استفاده کند.
        self.leg = leg
        # P-L6: اگر cockpit موجود است ولی منبعِ status ندارد، effect_status_fn را تزریق کن
        # تا صفِ cockpit به‌جایِ shadow، نمایِ فقط‌خواندنیِ گیتِ تک‌گلوگاه باشد.
        if cockpit is not None and effect_status_fn is not None \
                and getattr(cockpit, "_effect_status_fn", None) is None:
            cockpit._effect_status_fn = effect_status_fn
        self._verdicts: list[VerdictResult] = []
        self._advisory_signals: list[dict] = []
        # G1 fix (2026-07-17): Proposal Router memory. Legs are propose-only and keep
        # proposals locally; the live loop is the delivery spine that dedupes and turns
        # them into owner-visible advisory cards. In-memory by design: no append-only
        # source is rewritten, and no irreversible effect is settled here.
        self._proposal_seen: set[str] = set()
        self._proposal_outcomes: list[dict] = []
        self._proposal_cb: dict[str, dict] = {}   # G3: token→proposal meta (bounded)

        # W-2: ثبتِ advisory subscribers
        self.bus.subscribe(self._on_advisory, event_type="RHYTHM")
        self.bus.subscribe(self._on_advisory, event_type="SPECTRAL")
        self.bus.subscribe(self._on_advisory, event_type="AFFERENT")
        self.bus.subscribe(self._on_advisory, event_type="DOCTOR")

    # ─── W-1: brain → cockpit route ─────────────────────────────────────────────
    def process_project_f_draft(self, draft_title: str, checks: dict | None = None,
                                risk_override: str | None = None) -> dict:
        """درفتِ صبا → مغز → route. high-risk → کاکپیتِ آری.
        low-risk → مستقیم استودیوی صبا.
        خروجی: {routed, guards_passed, submitted_to_ari}."""
        if self.brain is None:
            return {"ok": False, "error": "no brain"}
        # جلسه ۴۶: کنترلِ content-free مالک از کابین — pause = نگه‌داشتنِ روتِ درفت‌های نو.
        # فقط وجودِ فلگ چک می‌شود (هیچ محتوا). صف/پول دست‌نخورده. مسیر با stdlib خالص
        # ساخته می‌شود (هم‌ارزِ STATE_DIR) تا خطِ قرمزِ «بدونِ production import» نشکند.
        try:
            import os as _os
            _sd = _os.environ.get("OPS_DIR") or str(Path(__file__).resolve().parent)
            if (Path(_sd) / "state" / "projectf-paused.flag").exists():
                return {"routed": [], "guards_passed": False,
                        "submitted_to_ari": [], "paused": True}
        except Exception:  # noqa: BLE001 — کنترل نباید حلقه را بکشد
            pass
        result = self.brain.process_draft(draft_title, checks=checks,
                                          risk_override=risk_override)
        # route: اگر چیزی به آری رفت → به صفِ تأییدِ کاکپیت اضافه کن
        submitted = []
        for route in result.get("routed_to", []):
            if route["route"] == "ari" and self.cockpit is not None:
                self.cockpit.add_approval(
                    project="Project-F",
                    action=f"تأییدِ {route['kind']}: {draft_title}",
                    amount_aud=0.0,  # پول قفل
                    guard="pending",
                    effect_id=f"pf-{route['kind']}-{draft_title[:20]}")
                submitted.append(route["kind"])
                # publish روی bus (advisory)
                self.bus.publish("OBSERVE", {
                    "source": "project-f-brain", "route": "ari",
                    "kind": route["kind"], "draft": draft_title,
                    "project": "Project-F"}, actor="brain")
            elif route["route"] == "saba" and self.studio is not None:
                # low-risk → مستقیم استودیو (پیشنهاد)
                self.bus.publish("OBSERVE", {
                    "source": "project-f-brain", "route": "saba",
                    "kind": route["kind"], "draft": draft_title}, actor="brain")
        return {"routed": result.get("routed_to", []),
                "guards_passed": result.get("guards_passed", False),
                "submitted_to_ari": submitted}

    # ─── W-1: verdict از آری → برگشت به مغز + استودیو ──────────────────────────
    def apply_ari_verdict(self, effect_id: str, approved: bool,
                          project: str = "Project-F") -> VerdictResult:
        """verdict از آری → ثبت در آرشیوِ مغز + به‌روزرسانی استودیو.
        approve = human-append (TINV-7) — اما اینجا mock (تست).
        در runtime واقعی، این از approval_channel.dispatch_callback می‌آید."""
        verdict = VerdictResult(approved=approved, effect_id=effect_id,
                                source="ari", project=project)
        self._verdicts.append(verdict)
        # HH-artery (2026-07-21): تأییدِ owner = external-validationِ یک آرتیفکتِ مغز → کانالِ
        # «value»ِ قلب (cognition_effect). این orphanِ recorder را می‌بندد تا producers.velocity_meter
        # ارزشِ واقعی را بخواند. flag OCTOPUS_WIRE_COGNITION_EFFECT خاموش (پیش‌فرض) → record خودش
        # no-op است (بایت‌به‌بایت). فقط validator=owner (بیرونی، هرگز خودسنجی). observability محض —
        # استریمِ خودش را می‌نویسد، هرگز ledger/effector. fail-soft.
        if approved:
            try:
                import os as _os, sys as _sys   # noqa: WPS433
                _hp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "heart")
                if _hp not in _sys.path:
                    _sys.path.insert(0, _hp)
                import cognition_effect as _ce   # noqa: WPS433 — lazy
                _ce.record(project, effect_id, validator="owner", weight_class="decision")
            except Exception:  # noqa: BLE001 — observability هرگز مسیرِ verdict را نمی‌کشد
                pass
        # برگشت به مغز: archive
        if self.brain is not None:
            outcome = "approved" if approved else "rejected"
            self.brain.archive(kind=effect_id.split("-")[1] if "-" in effect_id else "unknown",
                               outcome=outcome)
        # برگشت به استودیو: به‌روزرسانی وضعیت درفت
        if self.studio is not None and approved:
            for d in self.studio._drafts:
                if d.status == "pending":
                    d.status = "approved"   # → انتشارِ درون‌پلتفرم (human-gated)
                    break
        # publish verdict روی bus
        self.bus.publish("OBSERVE", {
            "source": "ari", "verdict": "approve" if approved else "reject",
            "effect_id": effect_id, "project": project}, actor="ari")
        return verdict

    # ─── W-2: advisory signals ──────────────────────────────────────────────────
    def _on_advisory(self, event: dict) -> None:
        """subscriber برای advisory signals. فقط log — هیچ اثر."""
        self._advisory_signals.append(event)

    def _emit_advisory(self, kind: str, payload: dict) -> None:
        """یک سیگنالِ advisory را ثبت کن — بدونِ نوشتن به ledger.
        advisory signals نباید ردیفِ ledger بسازند (آن‌ها فقط observable‌اند).
        مستقیماً _advisory_signals را پر می‌کند + subscriberهای bus را notify
        می‌کند (بدونِ bus.publish که ledger می‌نویسد)."""
        event = {"type": kind, "payload": {**payload, "advisory_only": True},
                 "actor": kind.lower(), "is_human": False,
                 "hash": f"adv-{len(self._advisory_signals):06d}"}
        self._advisory_signals.append(event)
        self._notify_advisory_subscribers(event)

    def _notify_advisory_subscribers(self, event: dict) -> None:
        """Notify bus subscribers without bus.publish.

        This is the missing spinal-cord wire behind G1/G5: advisory events should be
        observable by listeners, but must not create ledger entries or effects. We therefore
        inspect the in-memory subscriber list used by both _InMemoryBus and UnifiedBus and
        skip our own _on_advisory subscriber to avoid double-counting.
        """
        subs = getattr(self.bus, "_subscribers", None)
        if not isinstance(subs, list):
            return
        etype = event.get("type", "")
        for filt, cb in list(subs):
            if filt is not None and filt != etype:
                continue
            if getattr(cb, "__self__", None) is self and getattr(cb, "__func__", None) is LiveLoop._on_advisory:
                continue
            try:
                cb(event)
            except Exception:  # noqa: BLE001 — subscriber خراب نباید نخاع را بکشد
                pass

    def publish_rhythm_advisory(self, rhythm_state: dict) -> None:
        """rhythm.advisory را به‌عنوان advisory منتشر کن (W-3).
        advisory-only — بدونِ نوشتن به ledger."""
        self._emit_advisory("RHYTHM", rhythm_state)

    def publish_spectral_advisory(self, spectral_result: dict) -> None:
        """spectral_mine را به‌عنوان advisory منتشر کن (W-3).
        advisory-only — بدونِ نوشتن به ledger."""
        self._emit_advisory("SPECTRAL", spectral_result)

    def publish_afferent_advisory(self, afferent_status: dict) -> None:
        """afferent_ratio را به‌عنوان advisory منتشر کن (W-3).
        advisory-only — بدونِ نوشتن به ledger."""
        self._emit_advisory("AFFERENT", afferent_status)

    def publish_doctor_advisory(self, doctor_result: dict) -> None:
        """doctor.run_cycle را به‌عنوان advisory منتشر کن (W-3).
        advisory-only — بدونِ نوشتن به ledger."""
        self._emit_advisory("DOCTOR", doctor_result)

    @property
    def advisory_signals(self) -> list[dict]:
        """سیگنال‌های advisory دریافت‌شده. فقط log، هیچ اثر."""
        return list(self._advisory_signals)

    @property
    def verdicts(self) -> list[VerdictResult]:
        return list(self._verdicts)

    # ─── G1/G3: Proposal Router + outcome attribution ──────────────────────────
    @staticmethod
    def _proposal_dict(proposal) -> dict:
        """Normalize a leg Proposal-like object into a dict.

        The router is intentionally structural: legs only need ``to_dict()`` or the common
        attributes from legs/leg.py. Unknown shapes fail-soft into a minimal record rather
        than killing the live loop.
        """
        try:
            if hasattr(proposal, "to_dict"):
                d = proposal.to_dict()
            elif isinstance(proposal, dict):
                d = dict(proposal)
            else:
                d = {
                    "proposal_id": getattr(proposal, "proposal_id", ""),
                    "leg_id": getattr(proposal, "leg_id", "unknown"),
                    "kind": getattr(proposal, "kind", "unknown"),
                    "payload": getattr(proposal, "payload", {}),
                }
            if not isinstance(d.get("payload"), dict):
                d["payload"] = {"value": str(d.get("payload"))[:500]}
            return d
        except Exception:  # noqa: BLE001 — proposal بد نباید router را بکشد
            return {"proposal_id": "", "leg_id": "unknown", "kind": "unknown", "payload": {}}

    @staticmethod
    def _proposal_key(d: dict) -> str:
        return str(d.get("hash") or d.get("proposal_id") or f"{d.get('leg_id')}:{d.get('kind')}:{d.get('payload')}")

    @staticmethod
    def _proposal_score(d: dict) -> tuple:
        """Small deterministic ranking: revenue/quotes first, then reports/content.

        This is not approval. It only decides which owner-visible cards appear first.
        """
        kind = str(d.get("kind", ""))
        payload = d.get("payload") or {}
        amount = 0.0
        for k in ("expected_aud", "amount_aud", "total_incl_gst"):
            try:
                amount = max(amount, float(payload.get(k) or 0.0))
            except (TypeError, ValueError):
                pass
        priority = 3 if "quote" in kind else (2 if amount > 0 else 1)
        return (-priority, -amount, str(d.get("leg_id", "")), str(d.get("proposal_id", "")))

    @staticmethod
    def _safe_card_text(value, limit: int = 700) -> str:
        """Bounded HTML-safe text with a tiny PII scrub for owner-visible proposal cards."""
        s = str(value or "")[:limit]
        s = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[email-redacted]", s, flags=re.I)
        s = re.sub(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)", "[phone-redacted]", s)
        return html.escape(s)

    @staticmethod
    def _proposal_card(d: dict) -> str:
        """Owner-facing Telegram text for a proposal.

        Content is bounded, HTML-escaped, lightly PII-scrubbed, and advisory-only. No callback
        here approves or settles anything; it is just a delivery card so the human has something
        to judge.
        """
        payload = d.get("payload") or {}
        title = payload.get("title") or payload.get("scope") or payload.get("body") or payload.get("claim") or "proposal"
        aid = payload.get("attribution_id") or payload.get("proposal_id") or d.get("proposal_id")
        amount = payload.get("expected_aud") or payload.get("amount_aud") or payload.get("total_incl_gst")
        amount_line = f"\n💰 مقدار/ارزش: AU${float(amount):.2f}" if isinstance(amount, (int, float)) else ""
        return ("📨 <b>پیشنهادِ پا</b> — advisory/propose-only\n"
                "──────────\n"
                f"🦾 پا: <code>{LiveLoop._safe_card_text(d.get('leg_id', 'unknown'), 80)}</code>\n"
                f"📌 نوع: <code>{LiveLoop._safe_card_text(d.get('kind', 'unknown'), 80)}</code>\n"
                f"🆔 id: <code>{LiveLoop._safe_card_text(aid, 120)}</code>{amount_line}\n"
                f"📝 {LiveLoop._safe_card_text(title, 700)}\n"
                "──────────\n"
                "<i>این کارت هیچ اثر بیرونی/settle ندارد. تصمیم واقعی همچنان human-gated است.</i>")

    @staticmethod
    def _proposal_token(proposal_id) -> str:
        """tokenِ کوتاه/امنِ callback برای proposal_id (deterministic، ۱۶ هگز). هش می‌زنیم نه
        truncate: idِ خام ممکن است >۶۴ بایتِ callback_data یا ناامن باشد."""
        import hashlib
        return hashlib.sha256(str(proposal_id or "").encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _proposal_keyboard(token: str) -> dict:
        """کیبوردِ کارتِ پیشنهاد: prop:<verb>:<token> با verb ∈ ok/no/later. schemeِ 'prop'
        عمداً از 'app' (پول، توکن‌دار) جداست تا هرگز به مسیرِ settle نخورد (≈۲۴ بایت)."""
        return {"inline_keyboard": [[
            {"text": "✅ آره", "callback_data": f"prop:ok:{token}"},
            {"text": "❌ نه", "callback_data": f"prop:no:{token}"},
            {"text": "⏳ بعداً", "callback_data": f"prop:later:{token}"},
        ]]}

    @staticmethod
    def _proposal_amount(d: dict) -> float:
        """مبلغِ انتظاریِ پیشنهاد (asking price) از payload — برای متریک، نه settle."""
        payload = d.get("payload") or {}
        for _k in ("expected_aud", "amount_aud", "total_incl_gst"):
            _v = payload.get(_k)
            if isinstance(_v, (int, float)):
                return float(_v)
        return 0.0

    def route_leg_proposals(self, legs=None, *, deliver: bool = True, limit: int = 10) -> dict:
        """Gather/rank/dedupe proposals from legs and optionally deliver owner-visible cards.

        This closes the G1 delivery gap without changing leg autonomy:
        leg.proposals → normalize → dedupe → rank → advisory event → optional Telegram text.
        No proposal is removed from the leg, no approval is inferred, and no effect-release path
        is touched. Delivery itself is tracked as an outcome signal for G3.
        """
        leg_list = []
        if legs is None:
            if self.leg is not None:
                leg_list = [self.leg]
        elif isinstance(legs, (list, tuple, set)):
            leg_list = list(legs)
        else:
            leg_list = [legs]
        candidates = []
        for leg in leg_list:
            try:
                proposals = leg.proposals if hasattr(leg, "proposals") else []
            except Exception:  # noqa: BLE001
                proposals = []
            for p in proposals:
                d = self._proposal_dict(p)
                key = self._proposal_key(d)
                if key in self._proposal_seen:
                    continue
                d["_router_key"] = key
                candidates.append(d)
        candidates.sort(key=self._proposal_score)
        delivered = []
        for d in candidates[:max(0, int(limit))]:
            key = d.pop("_router_key", self._proposal_key(d))
            self._proposal_seen.add(key)
            card = self._proposal_card(d)
            # G3 arc: دکمهٔ اندازه‌گیری پشتِ OCTOPUS_WIRE_PROPOSAL_BUTTONS (پیش‌فرض خاموش).
            # خاموش → kb=None → دقیقاً همان send_text قبلی (byte-identical).
            import os as _os
            kb = None
            if _os.environ.get("OCTOPUS_WIRE_PROPOSAL_BUTTONS") == "1" and d.get("proposal_id"):
                tok = self._proposal_token(d.get("proposal_id"))
                _pl = d.get("payload") if isinstance(d.get("payload"), dict) else {}
                self._proposal_cb[tok] = {"proposal_id": str(d.get("proposal_id")),
                                          "amount": self._proposal_amount(d),
                                          "kind": str(d.get("kind", "unknown")),
                                          "leg_id": str(d.get("leg_id", "unknown")),
                                          "correlation_id": d.get("correlation_id"),
                                          "mission_id": d.get("mission_id"),
                                          # Wave1-A: attribution/lead «اگر موجود» حفظ می‌شود
                                          # تا رأیِ پایدار linkage کامل داشته باشد (هرگز اختراع نه).
                                          "lead_id": _pl.get("attribution_id") or _pl.get("lead_id")}
                if len(self._proposal_cb) > _PROPOSAL_CB_MAX:
                    for _old in list(self._proposal_cb)[:-_PROPOSAL_CB_MAX]:
                        self._proposal_cb.pop(_old, None)
                kb = self._proposal_keyboard(tok)
            sent = False
            if deliver and self.channel is not None and hasattr(self.channel, "send_text"):
                try:
                    if kb is not None:
                        try:
                            sent = bool(self.channel.send_text(card, reply_markup=kb))
                        except TypeError:
                            # کانالی که reply_markup نمی‌شناسد → کارتِ بی‌دکمه، router زنده می‌ماند.
                            sent = bool(self.channel.send_text(card))
                            kb = None
                    else:
                        sent = bool(self.channel.send_text(card))
                except Exception:  # noqa: BLE001 — کارتِ بد نباید router را بکشد
                    sent = False
            event = {"event": "delivered", "proposal_id": d.get("proposal_id"),
                     "leg_id": d.get("leg_id"), "kind": d.get("kind"),
                     "sent": sent, "buttons": kb is not None, "advisory_only": True}
            self._proposal_outcomes.append(event)
            self._emit_advisory("PROPOSAL", {**event, "card": card[:500]})
            # بهداشتِ state (P0-static 2026-07-17): payload خام واردِ خروجیِ router نمی‌شود —
            # organism این را در ORGANISM-STATE.json می‌نویسد که HTTPِ کابین (8771) هم سروش
            # می‌کند؛ کارت جدا و redactشده تحویل شده. فقط شناسه/نوع/ارسال کافی است.
            delivered.append({k: v for k, v in {**d, "sent": sent,
                                                "buttons": kb is not None}.items()
                              if k != "payload"})
        return {"seen_total": len(self._proposal_seen), "new": len(candidates),
                "delivered": len(delivered), "sent": sum(1 for d in delivered if d.get("sent")),
                "proposals": delivered}

    def record_proposal_outcome(self, proposal_id: str, verdict: str, *,
                                source: str = "ari", value_aud: float = 0.0,
                                note: str = "") -> dict:
        """Record a learning outcome for a delivered proposal (G3), not an approval primitive.

        ``verdict`` is measurement vocabulary: approved/rejected/sent/paid/ignored/etc. It does
        not call approval_channel, ledger, spend-enforcement, or effect-release modules. The only
        purpose is to make proposal→human-response measurable so Cortex can learn from acceptance
        rates and lead-to-revenue latency later.
        """
        v = str(verdict or "").strip().lower() or "unknown"
        rec = {"event": "outcome", "proposal_id": str(proposal_id), "verdict": v,
               "source": str(source), "value_aud": max(0.0, float(value_aud or 0.0)),
               "note": str(note)[:500], "advisory_only": True}
        self._proposal_outcomes.append(rec)
        self._emit_advisory("PROPOSAL_OUTCOME", rec)
        return rec

    def record_proposal_outcome_by_token(self, token: str, verb: str) -> dict | None:
        """G3 arc: تپِ دکمهٔ کارت → outcome. از threadِ pollerِ تلگرام صدا زده می‌شود.
        قوسی که تا امروز روی master بریده بود: کارت متنِ بی‌دکمه می‌رفت و رأیِ مالک هیچ‌جا
        نمی‌نشست. مرزها (عمدی): هیچ approve/settle/pay/ledger — فقط record_proposal_outcome
        (measurement-only). tokenِ ناشناخته → None. یک outcome به‌ازای هر پیشنهاد (اولین
        تپِ تصمیم برنده). «بعداً» تصمیم نیست → deferred، کارت زنده می‌ماند."""
        meta = self._proposal_cb.get(str(token or ""))
        if meta is None or meta.get("decided"):
            return None
        v = str(verb or "").strip().lower()
        if v == _PROPOSAL_DEFER:
            self._record_durable_verdict(meta, "deferred", 0.0)   # T2: تعویق هم measurementِ پایدار
            return {"event": "deferred", "proposal_id": meta["proposal_id"],
                    "advisory_only": True}
        mapped = _PROPOSAL_VERBS.get(v)
        if mapped is None:
            return None
        meta["decided"] = mapped
        # HH-artery observability (2026-07-21، پشتِ OCTOPUS_WIRE_COGNITION_EFFECT، flag-off=no-op):
        # تأییدِ owner روی یک پیشنهادِ مغز = external-validation → کانالِ «value»ِ قلب. استریمِ
        # heart-observabilityِ خودش را می‌نویسد؛ **هرگز ledger/effect/pay/approve** — پس مرزِ
        # measurement-onlyِ این تابع (که دربارهٔ money-effect است) دست‌نخورده می‌ماند. گاردِ `decided`
        # بالا idempotency می‌دهد (double-tap این‌جا نمی‌رسد). validator=owner (تپِ owner-gated). fail-soft.
        if mapped == "approved":
            try:
                import os as _os2, sys as _sys2   # noqa: WPS433
                _hp2 = _os2.path.join(_os2.path.dirname(_os2.path.abspath(__file__)), "heart")
                if _hp2 not in _sys2.path:
                    _sys2.path.insert(0, _hp2)
                import cognition_effect as _ce2   # noqa: WPS433 — lazy
                _ce2.record(str(meta.get("leg_id") or "proposal"),
                            str(meta.get("proposal_id") or ""),
                            validator="owner", weight_class="decision")
            except Exception:  # noqa: BLE001 — observability هرگز مسیرِ رأی را نمی‌کشد
                pass
        # ارزش فقط روی «آره» و فقط مبلغِ انتظاریِ خودِ پیشنهاد — proposal_value_aud را می‌جنباند،
        # نه confirmed_revenue. هیچ پولی جابه‌جا نشده؛ فقط مالک گفته «این را ببر جلو».
        value = float(meta.get("amount") or 0.0) if mapped == "approved" else 0.0
        self._record_durable_verdict(meta, mapped, value)         # T2: رأی → outcomes.db پایدار
        return self.record_proposal_outcome(meta["proposal_id"], mapped,
                                            source="ari-button", value_aud=value)

    def _record_durable_verdict(self, meta: dict, verdict: str, value: float) -> None:
        """T2 (ممیزیِ Sol): رأیِ مالک را پایدار (measurement) ثبت کن — پشتِ OCTOPUS_WIRE_VERDICT_OUTCOME.
        منطقِ store/مسیر در verdict_recorder محصور است تا live_loop **لایهٔ wireِ خالص** بماند
        (ساختاراً بدونِ importِ لایهٔ production — ناوردیِ t_no_production_import). flag خاموش → no-op.
        fail-soft؛ صفر settle/ledger/effector. قوسِ شکسته: رأی دیگر با restart گم نمی‌شود."""
        try:
            _op = str(_HERE / "outcomes")
            if _op not in sys.path:
                sys.path.insert(0, _op)
            import verdict_recorder as _vr   # noqa: WPS433 — lazy (این ماژول مجاز به I/O است)
            _vr.record_verdict_durably(
                proposal_id=str(meta.get("proposal_id") or ""), verdict=verdict,
                correlation_id=meta.get("correlation_id"), mission_id=meta.get("mission_id"),
                leg_id=str(meta.get("leg_id") or "unknown"), value_aud_claimed=value,
                lead_id=meta.get("lead_id"))
        except Exception:  # noqa: BLE001 — §۴: ثبتِ رأی هرگز مسیرِ دکمه را نمی‌کشد
            pass

    def proposal_metrics(self) -> dict:
        """Small near-action metric set for learning loops (G3)."""
        delivered = [r for r in self._proposal_outcomes if r.get("event") == "delivered"]
        sent = [r for r in delivered if r.get("sent")]
        outcomes = [r for r in self._proposal_outcomes if r.get("event") == "outcome"]
        positive = {"approved", "sent", "paid", "accepted", "won"}
        approved = [r for r in outcomes if r.get("verdict") in positive]
        revenue = sum(float(r.get("value_aud") or 0.0) for r in outcomes)
        return {"proposals_delivered": len(delivered), "proposal_outcomes": len(outcomes),
                "proposals_sent": len(sent),
                "proposals_fake_delivered": len(delivered) - len(sent),
                "proposal_positive": len(approved),
                "proposal_accept_rate": (len(approved) / len(outcomes)) if outcomes else 0.0,
                "proposal_value_aud": round(revenue, 2)}

    # ─── W-1: Lead-نقاشی path (همان حلقهٔ واحد) ────────────────────────────────
    def process_lead(self, leg=None, lead_name: str = "", expected_aud: float = 0.0,
                     cell: str = "lead.doer") -> dict:
        """لیدِ Lead-نقاشی → همان bus → attribution → CONFIRMED (paper).
        این نشان می‌دهد Lead-نقاشی و Project-F روی یک حلقه می‌چرخند.
        W-3 (2026-07-10): leg=None → از self.leg (تزریق‌شده در ساخت) استفاده می‌شود."""
        leg = leg if leg is not None else self.leg
        if leg is None:
            return {"ok": False, "error": "no leg"}
        intake = leg.intake(lead_name, expected_aud, cell)
        if not intake.get("ok"):
            return intake
        # publish روی bus
        self.bus.publish("OBSERVE", {
            "source": "lead-naghshi", "type": "lead",
            "attribution_id": intake["attribution_id"],
            "amount": expected_aud}, actor="leg")
        return intake

    # ─── sanity: no PII/media leak from brain path ──────────────────────────────
    def verify_no_pii_in_signals(self) -> bool:
        """هیچ رسانه/PII در سیگنال‌های bus نیست."""
        forbidden = ("media", "photo", "video", "face", "identity",
                     "real_name", "email", "phone", "subscriber", "fan_name")
        for sig in self._advisory_signals:
            blob = str(sig).lower()
            for f in forbidden:
                if f in blob:
                    return False
        return True


class _InMemoryBus:
    """busِ in-memory برای تست (بدونِ ledger واقعی).
    همان قراردادِ UnifiedBus ولی بدونِ disk write."""
    def __init__(self):
        self._subscribers: list = []
        self._events: list[dict] = []

    def subscribe(self, callback, event_type: str | None = None) -> None:
        self._subscribers.append((event_type, callback))

    def publish(self, event_type: str, payload: dict, actor: str = "system",
                is_human: bool = False, beat: bool = False) -> dict:
        event = {"type": event_type, "payload": payload, "actor": actor,
                 "is_human": is_human, "hash": f"mem-{len(self._events):06d}"}
        self._events.append(event)
        for filt, cb in self._subscribers:
            if filt is None or filt == event_type:
                try:
                    cb(event)
                except Exception:  # noqa: BLE001
                    pass
        return event

    @property
    def events(self) -> list[dict]:
        return list(self._events)
