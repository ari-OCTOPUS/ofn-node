#!/usr/bin/env python3
"""lead_pipeline.py — Lane G (منشور TG-UI ۲۰۲۶-۰۷-۳۱، رأی ۱۳/۱۷/۱۸): ارکستراتورِ ماشینِ لید.

حلقهٔ کاملِ منشور در یک beat:
    کشف → تحقیق → امتیاز → پیش‌نویس → [ارسالِ سقف‌دار: قوسِ جداگانهٔ گیت/worker]
    → پیگیری → گیر = سؤالِ آزادِ فارسی (کارتِ 🚧 ِ leg_tasks موجود) → لیدِ آماده = کارت در 🎨

مرزها (هم‌راستا با نامتغیرهای consent — هرگز ضعیف نمی‌شوند):
  · این ماژول **هیچ ارسالِ خروجی به مشتری ندارد** — فقط کارت به مالک (از راهِ send_fn ِ
    تزریقی؛ تولید = مسیرِ approval_channel با stream="lead"). ارسالِ واقعی فقط از قوسِ
    verdict→lead_effect_gate→outbound_worker (سقفِ روزانهٔ ۱۰، رأی مالک ۲۰۲۶-۰۷-۳۱).
  · market_signal (و هر کاندیدِ بدونِ رضایت) هرگز دکمهٔ رأی نمی‌گیرد — کارتِ آماده فقط
    برای لیدی که consent_firewall.may_outreach تأیید کند دکمه دارد؛ رأیِ approve هم تازه
    واردِ گیتِ per-effect می‌شود (deny ِ دوباره در عمق).
  · flag OCTOPUS_WIRE_LEAD_PIPELINE (پیش‌فرض خاموش) = بی‌اثرِ مطلق. halt مقدم بر flag.
  · state ِ خودش: state/legs/lead-pipeline.json (اتمیک tmp+os.replace).
  · headless در تست: بدونِ send_fn هیچ کارتی نمی‌رود؛ clock تزریق‌پذیر (now=ثانیه).

دکمه‌های کارتِ آماده = **همان** فعل‌های موجودِ live_loop (`prop:ok/no/later:<pb1-token>`) —
هیچ verb ِ نو، هیچ dispatch ِ نو: توکنِ stateless (proposal_token، نیازمندِ OCTOPUS_CB_SECRET)
+ تحویلِ durable (proposal_registry، پشتِ OCTOPUS_WIRE_VERDICT_OUTCOME) → تپِ مالک از مسیرِ
rehydrate ِ live_loop به _record_durable_verdict + _fire_lead_effect_hook ِ **موجود** می‌رسد.
هر دو پیش‌نیاز غایب → کارتِ بی‌دکمه (advisory، صادقانه)، هرگز دکمهٔ مرده.

stdlib-only؛ صفر شبکه؛ صفر خرج.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib                    # noqa: E402
import consent_firewall as cf    # noqa: E402
import lead_research             # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_PIPELINE"
MAX_PER_BEAT = 3                 # سقفِ کاندید در هر beat (ضدِ سیل)
FOLLOWUP_AFTER_DAYS = 3.0        # پیش‌نویسِ ارسال‌شدهٔ بی‌جواب پس از ۳ روز → پیگیری
_DAY_S = 86400.0


def enabled() -> bool:
    """flag خاموش (پیش‌فرض) = no-op مطلق."""
    return os.environ.get(FLAG, "0") == "1"


# ── state (اتمیک، STATE_DIR-relative) ─────────────────────────────────────────────
def _state_path() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-pipeline.json"


def _load_state() -> dict:
    try:
        d = json.loads(_state_path().read_text("utf-8"))
        if isinstance(d, dict):
            d.setdefault("stuck", {})
            d.setdefault("followups", {})
            return d
    except (OSError, ValueError):
        pass
    return {"stuck": {}, "followups": {}}


def _save_state(st: dict) -> None:
    try:
        p = _state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: نبودِ state فقط idempotency را ضعیف می‌کند، نه beat را


# ── importهای path-safe ِ لایه‌های دیگر ──────────────────────────────────────────
def _leg_tasks():
    """leg_tasks (لایهٔ Task ِ گروه — کارتِ 🚧 + ریپلای=رفعِ مانع). None = در دسترس نیست."""
    try:
        _tc = str(_HERE.parent / "telegram_center")
        if _tc not in sys.path:
            sys.path.insert(0, _tc)
        import leg_tasks as _lt   # noqa: WPS433
        return _lt
    except Exception:  # noqa: BLE001
        return None


def _outcomes_path() -> None:
    _oc = str(_HERE.parent / "outcomes")
    if _oc not in sys.path:
        sys.path.insert(0, _oc)


# ── کمکی‌ها ──────────────────────────────────────────────────────────────────────
def _rebuild_candidate(lead: dict) -> dict:
    """کاندیدِ سازگار با consent_firewall از فایلِ inbox — هم‌الگوی lead_effect_gate.bridge_from_inbox."""
    cb = lead.get("candidate") if isinstance(lead.get("candidate"), dict) else {}
    return {"source": {"channel": lead.get("source")},
            "candidate_type": cb.get("candidate_type"),
            "consent": cb.get("consent") or {},
            "request": cb.get("request") or {}}


def _card_text(lead_id: str, sc, quote: "dict | None", research: dict) -> str:
    """کارتِ لیدِ آماده (رأی ۱۸) — ScoredLead.card + خلاصهٔ کوت + خلاصهٔ تحقیق."""
    lines = ["🎨 <b>لیدِ آماده</b> — رأیِ تو ارسال نیست؛ فقط ورود به گیتِ سقف‌دار",
             "──────────", sc.card()]
    if quote and quote.get("ok"):
        bd = quote.get("breakdown") or {}
        rng = bd.get("total_incl_gst") or [0, 0]
        try:
            lines.append(f"📄 کوت {quote.get('qt_number')}: "
                         f"AU${float(rng[0]):,.0f}–{float(rng[1]):,.0f} (incl GST، draft)")
        except (TypeError, ValueError, IndexError):
            lines.append(f"📄 کوت {quote.get('qt_number')} (draft)")
    lines.append("🔬 " + str(research.get("summary") or "")[:200])
    lines.append(f"🆔 <code>{lead_id}</code>")
    return "\n".join(lines)


def _ready_keyboard(proposal_id, lead_id, amount: float, deps: dict) -> "dict | None":
    """دکمه‌های رأی = فعل‌های موجودِ live_loop (prop:ok/no/later:<pb1>). فقط وقتی
    توکنِ stateless mint شود **و** تحویل durable ثبت شود؛ وگرنه None (کارتِ بی‌دکمه —
    هرگز دکمهٔ مرده)."""
    pid = str(proposal_id or "").strip()
    if not pid:
        return None
    try:
        _outcomes_path()
        import proposal_token as _pt        # noqa: WPS433 — stdlib، صفر I/O
        import proposal_registry as _pr     # noqa: WPS433
        owner = (deps or {}).get("owner") or os.environ.get("TELEGRAM_OWNER_CHAT_ID") or ""
        tok = _pt.mint(pid, owner)
        if not tok:
            return None
        rec = _pr.record_delivery_durably({
            "proposal_id": pid, "amount": float(amount or 0.0), "kind": "lead_ready",
            "leg_id": "lead", "correlation_id": str(lead_id or ""),
            "mission_id": None, "lead_id": str(lead_id or "")})
        if not rec.get("recorded"):
            return None
        return {"inline_keyboard": [[
            {"text": "✅ آره", "callback_data": f"prop:ok:{tok}"},
            {"text": "❌ نه", "callback_data": f"prop:no:{tok}"},
            {"text": "⏳ بعداً", "callback_data": f"prop:later:{tok}"},
        ]]}
    except Exception:  # noqa: BLE001 — دکمه هرگز کارت را نمی‌کشد
        return None


def _send_card(deps: dict, text: str, keyboard: "dict | None" = None) -> bool:
    """ارسالِ کارت فقط از send_fn ِ تزریقی (تولید = approval_channel با stream="lead").
    بدونِ send_fn = headless (تست) — صادقانه False."""
    fn = (deps or {}).get("send_fn")
    if not callable(fn):
        return False
    try:
        return bool(fn(text, keyboard=keyboard, stream="lead"))
    except Exception:  # noqa: BLE001 — کانالِ خراب هرگز beat را نمی‌کشد
        return False


# ─── VQ-DEAD-LEAD-BUTTONS-001 → سیم‌کشیِ صداکننده (۲۰۲۶-۰۸-۰۷) ──────────────────
# `legs/lead_card.py` سازنده و تحویل‌دهندهٔ کارتِ تعاملی (📞 lcall / 📤 ldraft) را
# از ۰۸-۰۱ دارد و `center.py._handle_callback` از ۰۸-۰۴ آن دو فعل را routes می‌کند
# (regression: test_lead_card_buttons_live.py) — ولی هیچ صداکنندهٔ تولیدی
# `lead_card.render()`/`deliver()` را صدا نمی‌زد؛ `lead_scorer.ScoredLead.card()`
# فقط متنِ `lead_card.card_text()` را (بی‌کیبورد) داخلِ کارتِ رأیِ prop:ok/no/later
# می‌گذاشت. آن دو کارت **مخاطبِ متفاوت** دارند — یکی رأیِ «آیا این لید وارد گیتِ
# ارسال بشود؟» (`_card_text`/`_ready_keyboard`)، این‌یکی ابزارِ عملیِ «زنگ بزن /
# پیش‌نویس را مرور کن» برایِ همان لید — پس card_text() جایگزین نمی‌شود، این کارت
# **علاوه‌بر** آن به‌صورتِ پیامِ نوی جدا می‌رود.
#
# صفر اثرِ بیرونیِ نو: `lead_card.deliver()` فقط از همان send_fn ِ تزریقی
# (approval_channel، stream="lead") استفاده می‌کند — هیچ transport ِ تازه، هیچ
# ایمیل/SMTP. `has_send_button()` قبل از هر ارسالی داخلِ خودِ `lead_card.deliver`
# دوباره چک می‌شود (کمربند و بند شلوار). flag: OCTOPUS_WIRE_LEAD_CARD_CONTACT
# (پیش‌فرض خاموش) — خاموش ⇒ `lead_card.enabled()` False ⇒ این تابع فوراً برمی‌گردد،
# بدونِ حتی یک import ِ اضافه؛ خروجیِ beat برای هر تستِ امروز بایت‌به‌بایت همان است.
def _send_contact_card(lead_id: str, lead: dict, sc, deps: dict, out: dict) -> None:
    """کارتِ تعاملیِ لید (render()+deliver()، دکمه‌های lcall/ldraft) — جدا از
    کارتِ رأی. هرگز beat را نمی‌کشد؛ هرگز چیزی نمی‌فرستد اگر flag خاموش باشد یا
    send_fn نباشد."""
    try:
        import lead_card as _lc   # noqa: WPS433 — lazy، هم‌پوشه، تا env ِ تست اثر کند
        if not _lc.enabled():
            return
        fn = (deps or {}).get("send_fn")
        if not callable(fn):
            return
        fr = lead.get("first_reply") if isinstance(lead.get("first_reply"), dict) else None
        payload = _lc.render(lead, scored=sc, lead_id=lead_id, first_reply=fr,
                              verbs_ready=_lc.SAFE_VERBS)
        res = _lc.deliver(fn, payload)
        if res.get("sent"):
            out["contact_cards_sent"] = out.get("contact_cards_sent", 0) + 1
    except Exception:  # noqa: BLE001 — کارتِ تعاملی هرگز کارتِ رأی/beat را نمی‌کشد
        pass


def _iso_to_ts(iso: str) -> "float | None":
    import datetime as _dt   # noqa: WPS433
    try:
        return _dt.datetime.fromisoformat(str(iso)).timestamp()
    except (TypeError, ValueError):
        return None


def _replied(lead_key: str) -> bool:
    """آیا در funnel.db برای این لید/attribution رویدادِ customer.replied هست؟ خطا → False
    (پیگیریِ اضافه بهتر از پیگیریِ گم‌شده — و خودِ کارت باز هم human-gated است)."""
    store = None
    try:
        _outcomes_path()
        import funnel_store as _fs   # noqa: WPS433
        store = _fs.FunnelStore()
        rows = store.events_for_lead(str(lead_key))
        return any(r[1] == "customer.replied" for r in rows)
    except Exception:  # noqa: BLE001
        return False
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass


# ── مرحله‌ها ─────────────────────────────────────────────────────────────────────
def _make_stuck(lead_id: str, lead: dict, research: dict, st: dict, out: dict,
                now: float) -> None:
    """گیر = کارِ BLOCKED با سؤالِ آزادِ فارسی — سوارِ مکانیکِ موجودِ 🚧 + ریپلای=رفعِ مانع."""
    lt = _leg_tasks()
    question = lead_research.stuck_question(research)
    task_id = None
    if lt is not None:
        desc = str(lead.get("description") or "")[:80]
        t = lt.add("lead", f"🎨 لیدِ {lead_id[:12]}: {desc}", now=now)
        if t:
            b = lt.set_state("lead", t["id"], lt.BLOCKED, question=question, now=now)
            task_id = (b or t)["id"]
    st["stuck"][str(lead_id)] = {"task_id": task_id, "lead": lead,
                                 "question": question, "since": now}
    out["stuck"] += 1


def _process_ready(lead_id: str, lead: dict, sc, research: dict, deps: dict,
                   out: dict) -> None:
    """امتیازِ draft → پیش‌نویسِ کوت (اگر پا هست) → کارتِ آماده در 🎨 (رأی ۱۸)."""
    quote = None
    proposal_id = None
    amount = 0.0
    lead_leg = (deps or {}).get("lead_leg")
    if lead_leg is not None:
        try:
            r = lead_leg.intake(
                str(lead.get("applicant") or lead.get("address")
                    or str(lead.get("description", ""))[:60]).strip(),
                float(lead.get("expected_aud") or 0.0), cell="lead.doer",
                description=str(lead.get("description", ""))[:200],
                day=lead.get("day"))
            if r.get("ok") and r.get("attribution_id"):
                import lead_quote   # noqa: WPS433 — lazy، هم‌پوشه
                quote = lead_quote.create_quote(
                    lead_leg, r["attribution_id"],
                    lead_quote.lead_to_intake(lead, sc.as_dict()))
                if quote.get("ok"):
                    proposal_id = quote.get("proposal_id") or r["attribution_id"]
                    bd = quote.get("breakdown") or {}
                    rng = bd.get("total_incl_gst") or [0]
                    try:
                        amount = float(rng[0])
                    except (TypeError, ValueError, IndexError):
                        amount = 0.0
        except Exception:  # noqa: BLE001 — کوت هرگز کارت را نمی‌کشد
            pass
    text = _card_text(lead_id, sc, quote, research)
    kb = None
    # دکمهٔ رأی فقط برای لیدی که قانوناً می‌تواند بیرون برود (consent) — دفاعِ لایهٔ کارت؛
    # گیتِ per-effect بعداً دوباره و مستقل چک می‌کند.
    if proposal_id and cf.may_outreach(_rebuild_candidate(lead)):
        kb = _ready_keyboard(proposal_id, lead_id, amount, deps)
    if _send_card(deps, text, kb):
        out["cards_sent"] += 1
    out["ready"] += 1
    # کارتِ تعاملیِ جدا (lcall/ldraft) — همان لید، مخاطبِ متفاوت. پیش‌فرض بی‌اثر
    # (OCTOPUS_WIRE_LEAD_CARD_CONTACT خاموش).
    _send_contact_card(lead_id, lead, sc, deps, out)


def _process_one(lead_id: str, lead: dict, deps: dict, st: dict, out: dict,
                 now: float) -> str:
    """یک کاندید از تحقیق تا آماده/گیر. خروجی: برچسبِ نتیجه (برای سایدکارِ mark_processed)."""
    research = lead_research.enrich(lead, ask_fn=(deps or {}).get("ask_fn"))
    # دفاعِ رده‌ی رضایت: سیگنالِ بازار هرگز واردِ قوسِ draft/کارت نمی‌شود (R1) —
    # فایلِ top-level ِ market_signal فقط از producer ِ متخاصم ممکن است؛ رد و ثبت.
    if cf.classify(_rebuild_candidate(lead)) == "market_signal":
        out["signals"] += 1
        return "market_signal_refused"
    import lead_scorer   # noqa: WPS433 — lazy، هم‌پوشه
    sc = lead_scorer.score_lead(lead)
    if sc.action == "skip":
        # آشغال/بی‌ربط سؤالِ مالک نمی‌شود — بودجهٔ سؤال برای لیدِ بالقوه است.
        out["skip"] = out.get("skip", 0) + 1
        return "skip"
    if lead_research.is_stuck(research):
        _make_stuck(lead_id, lead, research, st, out, now)
        return "stuck"
    if sc.action != "draft":
        out[sc.action] = out.get(sc.action, 0) + 1
        return sc.action
    _process_ready(lead_id, lead, sc, research, deps, out)
    return "ready"


def _revive_answered(deps: dict, st: dict, out: dict, now: float) -> None:
    """کارِ BLOCKEDی که مالک با ریپلای جواب داد (BLOCKED→WORKING با «➕ اطلاعات مالک»)
    → در beat ِ بعدی با جوابِ ضمیمه دوباره تحقیق/امتیاز می‌شود."""
    lt = _leg_tasks()
    if lt is None or not st.get("stuck"):
        return
    marker = "➕ اطلاعات مالک:"
    open_tasks = {t.get("id"): t for t in lt.queue("lead")}
    for lead_id in list(st["stuck"].keys()):
        entry = st["stuck"][lead_id]
        task = open_tasks.get(entry.get("task_id"))
        if task is None:                      # DONE/لغو/گم‌شده → دیگر پیگیری نمی‌کنیم
            st["stuck"].pop(lead_id, None)
            continue
        if task.get("state") != lt.WORKING or marker not in str(task.get("text") or ""):
            continue                          # هنوز جواب نگرفته
        answer = str(task.get("text") or "").rsplit(marker, 1)[-1].strip()
        lead = dict(entry.get("lead") or {})
        if answer:
            lead["description"] = (str(lead.get("description") or "")
                                   + " " + answer).strip()
            if not str(lead.get("address") or "").strip():
                lead["address"] = answer[:120]   # سؤالِ اول همیشه آدرس بود
        research = lead_research.enrich(lead, ask_fn=(deps or {}).get("ask_fn"))
        if lead_research.is_stuck(research):
            lt.set_state("lead", task["id"], lt.BLOCKED,
                         question=lead_research.stuck_question(research), now=now)
            entry["lead"] = lead
            continue
        lt.set_state("lead", task["id"], lt.DONE,
                     result="اطلاعات کامل شد — لید واردِ امتیازدهی شد", now=now)
        st["stuck"].pop(lead_id, None)
        out["revived"] += 1
        import lead_scorer   # noqa: WPS433
        sc = lead_scorer.score_lead(lead)
        if sc.action == "draft":
            _process_ready(lead_id, lead, sc, research, deps, out)
        else:
            out[sc.action] = out.get(sc.action, 0) + 1


def _followups(deps: dict, st: dict, out: dict, now: float) -> None:
    """پیش‌نویسِ ارسال‌شدهٔ ≥۳ روز پیش بدونِ customer.replied → کارتِ پیگیری (همان مسیرِ
    کارتِ تأیید — هیچ ارسالِ مستقیم). یک پیگیری در هر پنجرهٔ ۳روزه per draft."""
    drafts_dir = opslib.STATE_DIR / "legs" / "lead-drafts"
    if not drafts_dir.is_dir():
        return
    for p in sorted(drafts_dir.glob("*.json")):
        try:
            rec = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(rec, dict) or rec.get("schema") != "lead-quote.v1" \
                or not rec.get("sent"):
            continue
        aid = str(rec.get("attribution_id") or "")
        sent_ts = _iso_to_ts(rec.get("sent_ts") or rec.get("ts"))
        if not aid or sent_ts is None or (now - sent_ts) < FOLLOWUP_AFTER_DAYS * _DAY_S:
            continue
        fu = st["followups"].get(aid) or {}
        last = float(fu.get("last") or 0.0)
        if last and (now - last) < FOLLOWUP_AFTER_DAYS * _DAY_S:
            continue                          # همین پنجره قبلاً پیگیری شده
        if _replied(aid):
            continue                          # مشتری جواب داده — پیگیریِ خودکار نه
        days = int((now - sent_ts) // _DAY_S)
        text = ("⏰ <b>پیگیریِ کوت</b> — "
                f"<code>{rec.get('qt_number') or aid}</code>\n"
                f"{days} روز از ارسال گذشته و جوابی در قیف ثبت نشده.\n"
                "پیش‌نویسِ پیگیری آماده است — رأیِ تو = ورود به گیتِ سقف‌دارِ ارسال.")
        if _send_card(deps, text):
            st["followups"][aid] = {"last": now, "count": int(fu.get("count") or 0) + 1}
            out["followups"] += 1


# ── beat ─────────────────────────────────────────────────────────────────────────
def beat(*, now=None, deps=None) -> dict:
    """یک ضربانِ کاملِ ماشینِ لید. همیشه dict؛ هرگز استثنا؛ هرگز ارسالِ خروجی.

    deps (همه اختیاری — headless بدونشان):
      send_fn(text, keyboard=None, stream="lead") -> bool   کانالِ کارت (تولید: approval_channel)
      lead_leg   LeadLeg برای intake/draft_quote (بدونش: کارتِ آماده بدونِ کوت)
      ask_fn     LLMِ محلیِ اختیاریِ تحقیق ($0)
      owner      chat_id ِ مالک برای mint ِ توکنِ دکمه‌ها
    """
    if not enabled():
        return {"ok": False, "status": "flag_off"}
    try:
        kill = opslib.master_halted() or opslib.halted() or (
            "STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else None)
    except Exception:  # noqa: BLE001 — ابهام در halt = halt
        kill = "halt_probe_error"
    if kill:
        return {"ok": False, "status": "halted", "reason": str(kill)}
    now = float(now if now is not None else time.time())
    deps = deps or {}
    out = {"ok": True, "sensed": 0, "ready": 0, "stuck": 0, "cards_sent": 0,
           "contact_cards_sent": 0, "followups": 0, "revived": 0, "signals": 0,
           "duplicates": 0}
    st = _load_state()
    try:
        import lead_sense   # noqa: WPS433 — lazy، هم‌پوشه
        _revive_answered(deps, st, out, now)
        for path, lead in lead_sense.read_inbox(limit=MAX_PER_BEAT):
            out["sensed"] += 1
            if lead_sense.seen_before(lead):
                lead_sense.mark_processed(path, lead, {"duplicate": True})
                out["duplicates"] += 1
                continue
            lead_id = str(lead.get("lead_id") or path.stem)
            try:
                label = _process_one(lead_id, lead, deps, st, out, now)
            except Exception as e:  # noqa: BLE001 — یک لیدِ بد بقیه را نکشد
                label = f"error:{type(e).__name__}"
                out["errors"] = out.get("errors", 0) + 1
            lead_sense.mark_processed(path, lead, {"pipeline": label})
        _followups(deps, st, out, now)
    except Exception as e:  # noqa: BLE001 — beat هرگز caller را نمی‌کشد
        out["ok"] = False
        out["error"] = type(e).__name__
    _save_state(st)
    return out


if __name__ == "__main__":
    print(json.dumps({"enabled": enabled(),
                      "note": "پشتِ OCTOPUS_WIRE_LEAD_PIPELINE؛ کارت فقط با send_fn ِ تزریقی."},
                     ensure_ascii=False))
