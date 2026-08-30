#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_cartographer.py — pure SyncRun → SyncStatus mapper for LEG-SYNC.

This is intentionally separate from cartographer_leg.py. The existing CartographerLeg is
an architecture-map staleness sentinel; this module is the top-level status mapper required
by MEGAPROMPT-LEG-SYNC-2026-08-02.

Contract:
  * pure: no I/O, no imports from live subsystems, no mutation of the input run.
  * total: every input, including None / malformed dicts / unknown states, returns a dict.
  * never throws across the boundary.
  * status priority: failed → blocked → running → done → pending.
  * progress is always clamped to [0, 100]; done is only legal with first_reply_id.
"""
from __future__ import annotations

_ALLOWED_PHASES = {
    "init", "module_build", "authorization", "draft", "first_reply",
    "done", "blocked", "failed",
}
_ALLOWED_STUDIO = {"not_started", "queued", "building", "ready", "failed", "blocked"}
_ALLOWED_LEAD = {
    "not_started", "awaiting_authorization", "authorized", "drafting",
    "draft_ready", "awaiting_first_reply", "first_reply_ready", "rejected",
    "failed", "blocked",
}
_PROGRESS_FLOORS = {
    "init": 5,
    "module_build": 20,
    "authorization": 40,
    "draft": 60,
    "first_reply": 85,
    "done": 100,
    "blocked": 35,
    "failed": 35,
}


def _d(value):
    return value if isinstance(value, dict) else {}


def _lst(value):
    return value if isinstance(value, list) else []


def _s(value, default=""):
    return value if isinstance(value, str) else default


def _num(value, default=0):
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _clamp_progress(value) -> int:
    n = _num(value, 0)
    if n < 0:
        return 0
    if n > 100:
        return 100
    return int(round(n))


def _err(phase, code, message, recoverable=True):
    return {
        "phase": phase,
        "code": code,
        "message": message,
        "recoverable": bool(recoverable),
    }


def _public_errors(run_errors, extra):
    out = []
    for e in _lst(run_errors):
        if not isinstance(e, dict):
            continue
        out.append({
            "phase": _s(e.get("phase"), "unknown"),
            "code": _s(e.get("code"), "ERROR"),
            "message": _s(e.get("message"), _s(e.get("error"), "error")),
            "recoverable": bool(e.get("recoverable", True)),
        })
    out.extend(extra)
    return out


def _derive_phase(studio_state, lead_state, stored_phase):
    if stored_phase in ("failed", "blocked", "done"):
        return stored_phase
    if lead_state == "first_reply_ready":
        return "done"
    if lead_state in ("draft_ready", "awaiting_first_reply"):
        return "first_reply"
    if lead_state in ("authorized", "drafting"):
        return "draft"
    if lead_state in ("awaiting_authorization", "rejected"):
        return "authorization"
    if studio_state in ("queued", "building", "blocked", "failed"):
        return "module_build"
    if studio_state == "ready":
        return "authorization"
    return "init"


def _message_and_action(state, phase, studio_state, lead_state, errors):
    if state == "failed":
        msg = (errors[0]["message"] if errors else "Sync run failed.")
        return msg, {"type": "retry", "label": "رفع خطا و اجرای دوباره"}
    if state == "done":
        return "همگام‌سازی کامل شد و first-reply آماده است.", {"type": "none", "label": "کاری لازم نیست"}
    if state == "blocked":
        if lead_state == "awaiting_authorization" or phase == "authorization":
            return "در انتظار تأیید lead برای ادامهٔ draft.", {
                "type": "human_authorization",
                "label": "تأیید یا رد درخواست lead",
            }
        if studio_state == "blocked" or phase == "module_build":
            return "ساخت ماژول در studio_pf قرارداد اجرایی ندارد و نیازمند اقدام انسانی است.", {
                "type": "human_authorization",
                "label": "ساخت skeleton از _Templates و ثبت دستی طبق PROJECT.md",
            }
        if errors:
            return errors[0]["message"], {"type": "fix_input", "label": "اصلاح ورودی/وضعیت"}
        return "فرایند در وضعیت ناسازگار یا ناقص متوقف شده است.", {
            "type": "fix_input",
            "label": "اصلاح state و اجرای دوباره",
        }
    if state == "running":
        if phase == "module_build":
            return "ماژول در studio_pf در حال ساخت/پیگیری است.", {"type": "wait", "label": "منتظر تکمیل ساخت بمانید"}
        if phase == "draft":
            return "draft در ماشین lead در حال آماده‌سازی است.", {"type": "wait", "label": "منتظر draft بمانید"}
        if phase == "first_reply":
            return "first-reply در حال آماده‌سازی است.", {"type": "wait", "label": "منتظر first-reply بمانید"}
        return "فرایند در حال اجراست.", {"type": "wait", "label": "منتظر مرحلهٔ بعد بمانید"}
    return "فرایند هنوز شروع نشده یا منتظر ورودی اولیه است.", {"type": "wait", "label": "sync را اجرا کنید"}


def status(run) -> dict:
    """Return a stable SyncStatus dict for any SyncRun-like input."""
    try:
        r = _d(run)
        studio = _d(r.get("studio_pf"))
        lead = _d(r.get("lead"))
        stored_status = _d(r.get("status"))
        extra_errors = []

        run_id = _s(r.get("run_id"), "missing-run-id")
        trace_id = _s(r.get("trace_id"), "missing-trace-id")
        if run_id == "missing-run-id":
            extra_errors.append(_err("init", "RUN_ID_MISSING", "run_id وجود ندارد.", True))
        if trace_id == "missing-trace-id":
            extra_errors.append(_err("init", "TRACE_ID_MISSING", "trace_id وجود ندارد.", True))

        studio_state = _s(studio.get("state"), "not_started")
        lead_state = _s(lead.get("state"), "not_started")
        if studio_state not in _ALLOWED_STUDIO:
            extra_errors.append(_err("module_build", "UNKNOWN_STUDIO_STATE",
                                     f"studio_pf.state ناشناخته است: {studio_state}", True))
            studio_state = "blocked"
        if lead_state not in _ALLOWED_LEAD:
            extra_errors.append(_err("authorization", "UNKNOWN_LEAD_STATE",
                                     f"lead.state ناشناخته است: {lead_state}", True))
            lead_state = "blocked"

        stored_phase = _s(stored_status.get("phase"), "")
        if stored_phase and stored_phase not in _ALLOWED_PHASES:
            extra_errors.append(_err("blocked", "UNKNOWN_PHASE",
                                     f"status.phase ناشناخته است: {stored_phase}", True))
            stored_phase = "blocked"

        raw_progress = stored_status.get("progress", _PROGRESS_FLOORS.get(stored_phase or "init", 0))
        if _num(raw_progress, 0) != _clamp_progress(raw_progress):
            extra_errors.append(_err("blocked", "PROGRESS_OUT_OF_RANGE",
                                     "progress خارج از بازهٔ 0..100 بود و clamp شد.", True))
        progress = _clamp_progress(raw_progress)

        errors = _public_errors(r.get("errors"), extra_errors)

        phase = _derive_phase(studio_state, lead_state, stored_phase)
        artifacts = {
            "module_id": studio.get("module_id"),
            "draft_id": lead.get("draft_id"),
            "first_reply_id": lead.get("first_reply_id"),
        }
        artifacts = {k: v for k, v in artifacts.items() if v}

        # Contract inconsistencies become visible blocked/failed statuses.
        if studio_state == "ready" and not studio.get("module_id"):
            errors.append(_err("module_build", "MODULE_READY_WITHOUT_MODULE_ID",
                               "studio_pf آماده است اما module_id ندارد.", True))
        if lead_state == "draft_ready" and not lead.get("draft_id"):
            errors.append(_err("draft", "DRAFT_READY_WITHOUT_DRAFT_ID",
                               "lead در وضعیت draft_ready است اما draft_id ندارد.", True))
        if lead_state in ("draft_ready", "awaiting_first_reply", "first_reply_ready") and not studio.get("module_id"):
            errors.append(_err("draft", "LEAD_ARTIFACT_WITHOUT_MODULE_ID",
                               "lead artifact بدون module_id معتبر ثبت شده است.", True))
        if lead_state in ("draft_ready", "awaiting_first_reply", "first_reply_ready") and not lead.get("authorization_id"):
            errors.append(_err("authorization", "LEAD_ARTIFACT_WITHOUT_AUTHORIZATION",
                               "lead artifact بدون authorization_id معتبر ثبت شده است.", True))
        if lead_state == "first_reply_ready" and not lead.get("first_reply_id"):
            errors.append(_err("first_reply", "FIRST_REPLY_READY_WITHOUT_ID",
                               "first_reply_ready بدون first_reply_id معتبر است.", True))
        if lead_state == "first_reply_ready" and not lead.get("draft_id"):
            errors.append(_err("first_reply", "FIRST_REPLY_WITHOUT_DRAFT_ID",
                               "first_reply_ready بدون draft_id معتبر است.", True))
        if stored_phase == "done" and not lead.get("first_reply_id"):
            errors.append(_err("done", "DONE_WITHOUT_FIRST_REPLY_ID",
                               "status.phase=done بدون first_reply_id رد شد.", True))

        nonrecoverable = [e for e in errors if e.get("recoverable") is False]
        has_error = bool(errors)

        if nonrecoverable or studio_state == "failed" or lead_state == "failed":
            public_state = "failed"
            phase = "failed" if phase in ("done", "blocked") else phase
            progress = min(progress, 95)
        elif has_error or studio_state == "blocked" or lead_state in ("blocked", "rejected", "awaiting_authorization"):
            public_state = "blocked"
            if phase == "done":
                phase = "blocked"
            progress = min(progress, 95)
        elif lead_state in ("drafting", "awaiting_first_reply") or studio_state in ("queued", "building"):
            public_state = "running"
            progress = max(progress, _PROGRESS_FLOORS.get(phase, 10))
            progress = min(progress, 95)
        elif lead_state == "first_reply_ready" and lead.get("first_reply_id"):
            public_state = "done"
            phase = "done"
            progress = 100
        elif studio_state == "ready" or lead_state in ("authorized", "draft_ready"):
            public_state = "running"
            progress = max(progress, _PROGRESS_FLOORS.get(phase, 10))
            progress = min(progress, 95)
        else:
            public_state = "pending"
            phase = phase if phase in _ALLOWED_PHASES else "init"
            progress = min(progress, 10)

        # Never pair done with an error, and never output done without first_reply_id.
        if public_state == "done" and (errors or not lead.get("first_reply_id")):
            public_state = "blocked"
            phase = "blocked"
            progress = min(progress, 95)
            if not lead.get("first_reply_id"):
                errors.append(_err("first_reply", "DONE_WITHOUT_FIRST_REPLY_ID",
                                   "done بدون first_reply_id رد شد.", True))

        message, next_action = _message_and_action(public_state, phase, studio_state, lead_state, errors)
        out = {
            "run_id": run_id,
            "trace_id": trace_id,
            "state": public_state,
            "phase": phase,
            "progress": _clamp_progress(progress),
            "message": message,
            "next_action": next_action,
            "artifacts": artifacts,
        }
        if errors:
            out["errors"] = errors
        return out
    except Exception as exc:  # noqa: BLE001 — total function, never throw.
        return {
            "run_id": "missing-run-id",
            "trace_id": "missing-trace-id",
            "state": "blocked",
            "phase": "blocked",
            "progress": 0,
            "message": f"status mapper failed safely: {type(exc).__name__}",
            "next_action": {"type": "fix_input", "label": "اصلاح SyncRun"},
            "errors": [_err("blocked", "STATUS_EXCEPTION", type(exc).__name__, True)],
            "artifacts": {},
        }


if __name__ == "__main__":
    import json
    print(json.dumps(status({}), ensure_ascii=False, indent=2))
