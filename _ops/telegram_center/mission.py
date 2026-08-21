#!/usr/bin/env python3
"""mission.py — Mission Genome برای کنترل تلگرامیِ خودکدنویسیِ امن.

ایدهٔ اصلی: هر خواستهٔ مالک از تلگرام، قبل از اینکه دکمه یا اجرای پراکنده شود، به یک
Mission قابل‌ردیابی تبدیل می‌شود:

    Intent → Mission → Action Card → Approval → Execution → Report

این ماژول عمداً **propose-only** است:
  - Mission و state می‌سازد/به‌روزرسانی می‌کند.
  - action/risk/fitness/test/review را ثبت می‌کند.
  - هیچ patch واقعی را apply نمی‌کند و هیچ فرمان پرخطری اجرا نمی‌کند.

ناوردی‌ها:
  - stdlib-only، import-time خالص.
  - هر write اتمیک و fail-soft.
  - محتوا/PII ذخیره نمی‌شود؛ owner_intent خلاصه و scrub/sanitize می‌شود.
  - اعمال code.apply/code.rollback همیشه approval-required در action_graph است.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
try:
    import opslib  # type: ignore
except Exception:  # noqa: BLE001 — fallback فقط برای import-time در محیط‌های ناقص
    opslib = None  # type: ignore

try:
    import action_graph  # noqa: E402
except Exception:  # noqa: BLE001 — package import fallback
    from . import action_graph  # type: ignore  # noqa: E402
try:
    import mission_contract as _mission_contract  # noqa: E402
except Exception:  # noqa: BLE001
    _mission_contract = None  # type: ignore

_SCHEMA_VERSION = 1
_BASE_STATE = (opslib.STATE_DIR if opslib is not None else (_OPS / "state"))
_STATE_DIR = _BASE_STATE / "telegram" / "missions"
_MISSIONS_JSON = _STATE_DIR / "missions.json"
_AUDIT_JSONL = _STATE_DIR / "mission-audit.jsonl"

_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")
_ALLOWED_STATES = (
    "created", "planned", "patched", "tested", "reviewed",
    "awaiting_owner", "approved", "applied", "monitored", "done", "reverted", "rejected",
)

# VQ-MISSION-RECONCILE-001 قدمِ ۱ (۰۷-۳۱): تا امروز set_state هر عضوِ
# _ALLOWED_STATES را از هر وضعی می‌پذیرفت (done→created قانونی بود!) در حالی که
# دنیای canonical (mission_contract) گذارِ اجباری دارد. حالت: **annotate-first** —
# گذارِ خارج از جدول بلاک نمی‌شود (رفتارِ زندهٔ تلگرام دست‌نخورده) ولی روی خودِ
# mission و در audit علامت می‌خورد تا دادهٔ واقعی جمع شود؛ سفت‌کردن = رأیِ مالک.
LEGAL_TRANSITIONS_12 = {
    "created": ("planned", "awaiting_owner", "rejected"),
    "planned": ("patched", "tested", "awaiting_owner", "rejected"),
    "patched": ("tested", "rejected"),
    "tested": ("reviewed", "awaiting_owner", "rejected"),
    "reviewed": ("awaiting_owner", "approved", "rejected"),
    "awaiting_owner": ("approved", "rejected"),
    "approved": ("applied", "rejected"),
    "applied": ("monitored", "done", "reverted"),
    "monitored": ("done", "reverted"),
    "done": (), "reverted": (), "rejected": (),
}


def can_transition_12(old: str, new: str) -> bool:
    """گذارِ قانونیِ Genome. ناشناخته = غیرقانونی (fail-closed در قضاوت، نه در ثبت)."""
    return str(new) in LEGAL_TRANSITIONS_12.get(str(old), ())

# کلمات فارسی/انگلیسی برای intentهای mission-level. اینها مکمل intent.py هستند.
_CODE_KWS = (
    "کد", "کدنویسی", "patch", "diff", "باگ", "bug", "fix", "درست کن",
    "بساز", "اضافه کن", "وصل کن", "دکمه", "callback", "تلگرامو بهتر", "بهتر کن",
)
_TEST_KWS = ("تست", "test", "verify", "چک کن", "fitness", "سبز", "سالم")
_APPLY_KWS = ("اعمال", "apply", "merge", "اجرا کن")
_LEARN_KWS = ("یاد بگیر", "از این به بعد", "دیگه", "ترجیح", "منوی طولانی", "سبک")
_EVOLVE_KWS = ("جهش", "evolve", "mutation", "tournament", "تکامل")


def _now_iso() -> str:
    if opslib is not None:
        try:
            return opslib.now_iso()
        except Exception:  # noqa: BLE001
            pass
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def _scrub_text(s: object, cap: int = 220) -> str:
    """خلاصهٔ امن برای owner_intent/title. خط آلوده کامل redact می‌شود."""
    txt = " ".join(str(s if s is not None else "").split())[:cap]
    low = txt.lower()
    if any(b in low or b in txt for b in _BANNED_ECHO):
        return "(redacted:containment)"
    # حذف control chars؛ فارسی/emoji مجاز می‌مانند.
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", txt)


def _esc(s: object) -> str:
    """HTML escape برای کارت‌های تلگرام."""
    return html.escape(str(s if s is not None else ""))


def _safe_id(raw: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.\-]", "-", str(raw or ""))[:80].strip("-_.")
    return clean or "unknown"


def _atomic_write_json(path: Path, data: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, path)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _load_state() -> dict:
    # Wave B (owner order 2026-08-21): mission sweep must not do raw
    # Path.read_text in the hot loop — bounded read; stall/malformed -> empty.
    try:
        import config_manager as _cm  # noqa: WPS433
        d = _cm.bounded_json_read(_MISSIONS_JSON)
        if not isinstance(d, dict):
            return {"schema_version": _SCHEMA_VERSION, "missions": []}
        if not isinstance(d.get("missions"), list):
            d["missions"] = []
        d.setdefault("schema_version", _SCHEMA_VERSION)
        return d
    except Exception:  # noqa: BLE001 — fail-soft
        return {"schema_version": _SCHEMA_VERSION, "missions": []}


def _save_state(state: dict) -> bool:
    # سقف نگهداری برای جلوگیری از رشد بی‌نهایت؛ جدیدترین‌ها نگه داشته می‌شوند.
    missions = [m for m in state.get("missions", []) if isinstance(m, dict)]
    state["missions"] = missions[-300:]
    state["schema_version"] = _SCHEMA_VERSION
    return _atomic_write_json(_MISSIONS_JSON, state)


def _audit(event: str, **kw) -> None:
    try:
        _AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": _now_iso(), "event": event, **kw}
        with open(_AUDIT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def infer_mission_type(text: str) -> str:
    """متن آزاد مالک → نوع mission درشت‌دانه."""
    low = str(text or "").lower()
    if any(k in low for k in _EVOLVE_KWS):
        return "evolution"
    if any(k in low for k in _LEARN_KWS):
        return "preference"
    if any(k in low for k in _APPLY_KWS) and (any(k in low for k in _CODE_KWS) or any(k in low for k in _TEST_KWS)):
        return "code_apply_request"
    if any(k in low for k in _TEST_KWS):
        return "verification"
    if any(k in low for k in _CODE_KWS):
        return "self_coding"
    return "general"


def actions_for_type(mission_type: str) -> list[str]:
    """نوع mission → action graph پیشنهادی."""
    mt = str(mission_type or "general")
    if mt == "self_coding":
        return ["code.plan", "code.patch", "doctor.review", "epistemics.review", "code.test", "code.diff", "code.apply"]
    if mt == "code_apply_request":
        return ["code.test", "doctor.review", "epistemics.review", "code.apply"]
    if mt == "verification":
        return ["code.test", "doctor.review"]
    if mt == "evolution":
        return ["evolution.propose", "code.test", "doctor.review", "evolution.select"]
    if mt == "preference":
        return ["mission.next"]
    return ["mission.next"]


def build_plan(mission_type: str) -> list[dict]:
    """طرح استاندارد از action specs."""
    plan = []
    for idx, aid in enumerate(actions_for_type(mission_type), 1):
        spec = action_graph.get(aid)
        plan.append({
            "step": idx,
            "action": aid,
            "label": spec.get("label", aid),
            "risk": spec.get("risk", "high"),
            "requires_approval": bool(spec.get("requires_approval")),
            "handler": spec.get("handler", ""),
            "tests": list(spec.get("tests") or []),
        })
    return plan


def fitness_template(mission_type: str) -> dict:
    """fitness اولیه؛ بعداً با نتایج واقعی tests/reviews/owner تکمیل می‌شود."""
    mt = str(mission_type or "general")
    return {
        "tests_passed": None,
        "doctor_ok": None,
        "epistemic_ok": None,
        "owner_acceptance": None,
        "rollback_available": any(action_graph.get(a).get("rollback") for a in actions_for_type(mt)),
        "risk": action_graph.max_risk(actions_for_type(mt)),
        "measured_lift": 0.0,
        "score": 0.0,
    }


def create_mission(owner_intent: str, *, source: str = "telegram", organ: str | None = None,
                   mission_type: str | None = None) -> dict:
    """Mission جدید بساز و در state ذخیره کن. خروجی خود mission است."""
    mt = mission_type or infer_mission_type(owner_intent)
    safe_intent = _scrub_text(owner_intent)
    stamp = _now_stamp()
    digest = hashlib.sha256((safe_intent + stamp + str(time.time_ns())).encode("utf-8")).hexdigest()[:8]
    mid = f"M-{stamp}-{digest}"
    actions = actions_for_type(mt)
    risk = action_graph.max_risk(actions)
    trace_id = (_mission_contract.new_trace_id() if _mission_contract is not None
                else hashlib.sha256((mid + "|trace").encode()).hexdigest())
    mission = {
        "id": mid,
        "mission_id": mid,
        "task_id": f"task-{digest}",
        "trace_id": trace_id,
        "tenant_id": "personal",
        "project_id": str(organ or "octopus-core"),
        "scope": "project",
        "policy_version": "octopus-policy.v1",
        "schema_version": _SCHEMA_VERSION,
        "source": _scrub_text(source, 40) or "telegram",
        "owner_intent": safe_intent,
        "mission_type": mt,
        "organ": organ or ("telegram_center" if mt in ("general", "preference") else "cortex"),
        "risk": risk,
        "state": "created",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "plan": build_plan(mt),
        "actions": actions,
        "patches": [],
        "tests": [],
        "doctor_review": None,
        "epistemic_review": None,
        "approval": "required" if any(action_graph.get(a).get("requires_approval") for a in actions) else "not_required",
        "rollback": {"available": bool(fitness_template(mt)["rollback_available"]), "ref": None},
        "fitness": fitness_template(mt),
        "notes": [],
    }
    state = _load_state()
    state["missions"].append(mission)
    _save_state(state)
    _audit("mission.created", id=mid, mission_type=mt, risk=risk)
    return mission


def list_missions(*, states: tuple[str, ...] | None = None, limit: int = 10) -> list[dict]:
    """جدیدترین missionها."""
    st = _load_state()
    missions = [m for m in st.get("missions", []) if isinstance(m, dict)]
    if states:
        allowed = set(states)
        missions = [m for m in missions if m.get("state") in allowed]
    try:
        lim = max(1, int(limit))
    except (TypeError, ValueError):
        lim = 10
    return list(reversed(missions))[:lim]


def get(mid: str) -> dict | None:
    sid = _safe_id(mid)
    for m in _load_state().get("missions", []):
        if isinstance(m, dict) and m.get("id") == sid:
            return m
    return None


def _update(mid: str, mutate) -> dict | None:
    sid = _safe_id(mid)
    st = _load_state()
    for idx, m in enumerate(st.get("missions", [])):
        if isinstance(m, dict) and m.get("id") == sid:
            new = mutate(dict(m))
            if not isinstance(new, dict):
                return None
            new["updated_at"] = _now_iso()
            st["missions"][idx] = new
            _save_state(st)
            return new
    return None


def set_state(mid: str, new_state: str, note: str = "") -> dict | None:
    """state مأموریت را با validation عوض کن.

    annotate-first (۰۷-۳۱): گذارِ خارج از LEGAL_TRANSITIONS_12 ثبت می‌شود ولی
    بلاک نمی‌شود — علامتِ `illegal_transitions` روی mission + `legal:false` در
    audit، تا الگوی واقعیِ گذارها قبل از سفت‌کردن سنجیده شود."""
    ns = str(new_state or "")
    if ns not in _ALLOWED_STATES:
        return None
    legal_holder = {"ok": True, "from": ""}

    def mut(m: dict) -> dict:
        old = str(m.get("state") or "")
        legal_holder["from"] = old
        if old and not can_transition_12(old, ns):
            legal_holder["ok"] = False
            m.setdefault("illegal_transitions", []).append(
                {"from": old, "to": ns, "ts": _now_iso()})
            m["illegal_transitions"] = m["illegal_transitions"][-10:]
        m["state"] = ns
        if note:
            m.setdefault("notes", []).append({"ts": _now_iso(), "note": _scrub_text(note, 200)})
        return m

    out = _update(mid, mut)
    if out:
        _audit("mission.state", id=out["id"], state=ns,
               legal=legal_holder["ok"], prev=legal_holder["from"])
    return out


def record_test(mid: str, name: str, passed: bool, detail: str = "") -> dict | None:
    """ثبت نتیجهٔ تست/fitness."""
    def mut(m: dict) -> dict:
        rec = {"name": _scrub_text(name, 80), "passed": bool(passed),
               "detail": _scrub_text(detail, 180), "ts": _now_iso()}
        m.setdefault("tests", []).append(rec)
        tests = [t for t in m.get("tests", []) if isinstance(t, dict)]
        if tests:
            m.setdefault("fitness", fitness_template(m.get("mission_type")))
            m["fitness"]["tests_passed"] = all(bool(t.get("passed")) for t in tests)
        if m.get("state") in ("created", "planned", "patched"):
            m["state"] = "tested"
        return m
    out = _update(mid, mut)
    if out:
        _audit("mission.test", id=out["id"], name=_scrub_text(name, 80), passed=bool(passed))
    return out


def record_review(mid: str, reviewer: str, ok: bool, detail: str = "") -> dict | None:
    """ثبت review دکتر/اپیستمیک."""
    rv = str(reviewer or "doctor").lower()

    def mut(m: dict) -> dict:
        rec = {"ok": bool(ok), "detail": _scrub_text(detail, 220), "ts": _now_iso()}
        if rv.startswith("epi"):
            m["epistemic_review"] = rec
            m.setdefault("fitness", fitness_template(m.get("mission_type")))
            m["fitness"]["epistemic_ok"] = bool(ok)
        else:
            m["doctor_review"] = rec
            m.setdefault("fitness", fitness_template(m.get("mission_type")))
            m["fitness"]["doctor_ok"] = bool(ok)
        m["state"] = "reviewed"
        return m
    out = _update(mid, mut)
    if out:
        _audit("mission.review", id=out["id"], reviewer=rv, ok=bool(ok))
    return out


def set_owner_verdict(mid: str, approved: bool) -> dict | None:
    """ثبت verdict مالک برای mission؛ اجرای واقعی انجام نمی‌دهد."""
    def mut(m: dict) -> dict:
        m["approval"] = "approved" if approved else "rejected"
        m.setdefault("fitness", fitness_template(m.get("mission_type")))
        m["fitness"]["owner_acceptance"] = bool(approved)
        m["state"] = "approved" if approved else "rejected"
        return m
    out = _update(mid, mut)
    if out:
        _audit("mission.owner_verdict", id=out["id"], approved=bool(approved))
    return out


def add_note(mid: str, note: str) -> dict | None:
    """یادداشت content-free روی mission؛ برای دکمه‌هایی که فقط درخواست/صف را ثبت می‌کنند."""
    def mut(m: dict) -> dict:
        m.setdefault("notes", []).append({"ts": _now_iso(), "note": _scrub_text(note, 220)})
        return m
    out = _update(mid, mut)
    if out:
        _audit("mission.note", id=out["id"])
    return out


def compute_fitness(mission: dict) -> dict:
    """fitness ساده و شفاف از شواهد موجود."""
    m = mission if isinstance(mission, dict) else {}
    f = dict(m.get("fitness") if isinstance(m.get("fitness"), dict) else fitness_template(m.get("mission_type")))
    score = 0.0
    weights = {
        "tests_passed": 0.35,
        "doctor_ok": 0.20,
        "epistemic_ok": 0.15,
        "owner_acceptance": 0.25,
        "rollback_available": 0.05,
    }
    for k, w in weights.items():
        v = f.get(k)
        if v is True:
            score += w
        elif v is False:
            score -= w
    # risk penalty محافظه‌کار
    risk = str(f.get("risk") or m.get("risk") or "medium")
    score -= {"read": 0.0, "low": 0.02, "medium": 0.08, "high": 0.18}.get(risk, 0.18)
    f["score"] = round(score, 3)
    return f


def refresh_fitness(mid: str) -> dict | None:
    def mut(m: dict) -> dict:
        m["fitness"] = compute_fitness(m)
        return m
    return _update(mid, mut)


def cockpit_summary(limit: int = 5) -> dict:
    """خلاصهٔ cockpit برای render/center."""
    missions = list_missions(limit=limit)
    counts: dict[str, int] = {}
    for m in _load_state().get("missions", []):
        if isinstance(m, dict):
            counts[str(m.get("state", "unknown"))] = counts.get(str(m.get("state", "unknown")), 0) + 1
    priority = None
    for m in missions:
        if m.get("state") not in ("done", "reverted", "rejected"):
            priority = {"id": m.get("id"), "title": m.get("owner_intent"),
                        "state": m.get("state"), "risk": m.get("risk"),
                        "next_action": (m.get("plan") or [{}])[0].get("action") if m.get("plan") else None}
            break
    return {"counts": counts, "recent": missions, "priority": priority}


def mission_card(mid: str | None = None) -> tuple[str, list]:
    """کارت HTML + کیبورد برای یک mission یا لیست missionها."""
    if mid:
        m = get(mid)
        if not m:
            return "🧬 مأموریت پیدا نشد.", [[{"text": "🔙 مأموریت‌ها", "callback_data": "mn:ms"}]]
        fit = compute_fitness(m)
        lines = [f"🧬 <b>Mission</b> <code>{_esc(m['id'])}</code>",
                 f"وضعیت: <code>{_esc(m.get('state'))}</code> · ریسک: <code>{_esc(m.get('risk'))}</code>",
                 f"نیت: {_esc(m.get('owner_intent'))}",
                 f"Fitness: <code>{_esc(fit.get('score'))}</code>"]
        if m.get("doctor_review"):
            lines.append(f"🩺 Doctor: {'✅' if m['doctor_review'].get('ok') else '❌'}")
        if m.get("epistemic_review"):
            lines.append(f"🔎 Evidence: {'✅' if m['epistemic_review'].get('ok') else '❌'}")
        kb = [[{"text": "🧪 تست/fitness", "callback_data": f"ms:test:{m['id']}"},
               {"text": "🩺 review", "callback_data": f"ms:review:{m['id']}"}],
              [{"text": "✅ تأیید mission", "callback_data": f"ms:approve:{m['id']}"},
               {"text": "❌ رد", "callback_data": f"ms:reject:{m['id']}"}],
              [{"text": "🔙 مأموریت‌ها", "callback_data": "mn:ms"}]]
        return "\n".join(lines), kb

    s = cockpit_summary()
    lines = ["🧬 <b>Mission Genome</b>"]
    pr = s.get("priority")
    if pr:
        lines.append(f"اولویت: <code>{_esc(pr['id'])}</code> · {_esc(pr['state'])} · {_esc(pr['risk'])}")
        lines.append(_esc(str(pr.get("title") or "")[:120]))
    else:
        lines.append("فعلاً مأموریت باز ندارم.")
    counts = s.get("counts") or {}
    if counts:
        lines.append(" · ".join(f"{_esc(k)}:{_esc(v)}" for k, v in sorted(counts.items())))
    kb: list = []
    for m in s.get("recent", [])[:5]:
        mid_safe = _safe_id(str(m.get("id", "?")))
        state_safe = _scrub_text(m.get("state"), 24)
        kb.append([{"text": f"🧬 {mid_safe[-17:]} · {state_safe}",
                    "callback_data": f"ms:open:{mid_safe}"}])
    kb.append([{"text": "🔙 منو", "callback_data": "mn:menu"}])
    return "\n".join(lines), kb


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="*", help="create mission from text")
    args = ap.parse_args()
    if args.text:
        print(json.dumps(create_mission(" ".join(args.text)), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(cockpit_summary(), ensure_ascii=False, indent=2))
