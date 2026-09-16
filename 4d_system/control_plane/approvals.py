"""
control_plane/approvals.py — v3: approvalِ زنده فقط برای high-risk (flag-gated).

اصولِ سخت:
  • flag: CONTROL_PLANE_APPROVALS_LIVE — default-off. خاموش = فقط mirror
    (رفتارِ v1/v2)؛ هیچ تصمیمی از این ماژول رد نمی‌شود.
  • هیچ مکانیزمِ applyِ جدیدی وجود ندارد: approve/reject دقیقاً همان توابعِ
    امنِ موجودِ brain.self_code را صدا می‌زند (TCB check + stale + بازاسکنِ
    ایستا + sandbox test + tamper detection همه آن‌جا می‌ماند).
  • double-confirm: بدونِ confirmed=True هیچ تصمیمی اجرا نمی‌شود
    («همیشه دیف را نشان بده» — UI اول دیف را نشان می‌دهد، بعد تیک، بعد دکمه).
  • evidence trail: هر تلاش (حتی ردشده‌ها) در
    outputs/control_plane/approvals_log.jsonl ثبت می‌شود — append-only.
  • low-risk هرگز از این‌جا گیت نمی‌خورد؛ این سطح فقط برای policy level ≥ 3 است.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from control_plane.flags import flag
from control_plane.policy import evaluate

SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_DIR = SYSTEM_ROOT / "outputs" / "control_plane"
AUDIT_FILE = "approvals_log.jsonl"


def approvals_live() -> bool:
    return flag("CONTROL_PLANE_APPROVALS_LIVE")


def _audit(record: dict[str, Any], audit_dir: Path | None) -> str:
    d = audit_dir or DEFAULT_AUDIT_DIR
    d.mkdir(parents=True, exist_ok=True)
    p = d / AUDIT_FILE
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return str(p)


def decide_self_code(pid: str, decision: str, note: str = "", *,
                     confirmed: bool = False, actor: str = "owner-ui",
                     audit_dir: Path | None = None) -> dict[str, Any]:
    """تصمیمِ approve/reject روی یک پیشنهادِ self_code — از مسیرِ امنِ موجود.

    ترتیبِ گیت‌ها: اعتبارِ decision → flag → double-confirm → مسیرِ امنِ self_code.
    هر تلاش audit می‌شود، حتی تلاش‌های ردشده.
    """
    pol = evaluate("self_code_approve")
    rec: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "kind": "self_code",
        "pid": pid,
        "decision": decision,
        "note": (note or "")[:300],
        "actor": actor,
        "confirmed": bool(confirmed),
        "flag_live": approvals_live(),
        "policy_action": pol.action_type,
        "policy_level": pol.level,
    }
    if decision not in ("approve", "reject"):
        rec["result"] = {"ok": False, "reason": f"decision نامعتبر: {decision!r}"}
    elif not approvals_live():
        rec["result"] = {"ok": False,
                         "reason": "CONTROL_PLANE_APPROVALS_LIVE خاموش است (default-off) — "
                                   "این سطح فعلاً فقط mirror است"}
    elif not confirmed:
        rec["result"] = {"ok": False,
                         "reason": "double-confirm لازم است: اول دیف را ببین، بعد تیکِ تأیید"}
    else:
        # مسیرِ امنِ موجود — هیچ applyِ جدیدی در control plane نیست. try/except تا
        # هر تلاش (حتی خطای import/IO/…) در evidence-trail ثبت شود (نه skip بی‌صدا).
        try:
            from brain import self_code
            res = (self_code.approve(pid) if decision == "approve"
                   else self_code.reject(pid, note))
            rec["result"] = {"ok": bool(res.get("ok")), "reason": res.get("reason", "")}
        except Exception as e:
            rec["result"] = {"ok": False, "reason": f"خطای مسیرِ امن: {type(e).__name__}: {e}"}
    rec["audit_path"] = _audit(rec, audit_dir)
    return rec


def resolve_bus_approval(new_state: str, *, confirmed: bool = False,
                         actor: str = "owner-ui",
                         audit_dir: Path | None = None) -> dict[str, Any]:
    """approve/reject آخرین approvalِ معلقِ event bus — با همان تابعِ موجودِ events."""
    pol = evaluate("self_code_approve")  # همان سطحِ high-risk برای هر approval
    rec: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "kind": "bus",
        "new_state": new_state,
        "actor": actor,
        "confirmed": bool(confirmed),
        "flag_live": approvals_live(),
        "policy_action": pol.action_type,
        "policy_level": pol.level,
    }
    if new_state not in ("approved", "rejected"):
        rec["result"] = {"ok": False, "reason": f"state نامعتبر: {new_state!r}"}
    elif not approvals_live():
        rec["result"] = {"ok": False,
                         "reason": "CONTROL_PLANE_APPROVALS_LIVE خاموش است (default-off)"}
    elif not confirmed:
        rec["result"] = {"ok": False, "reason": "double-confirm لازم است"}
    else:
        try:
            from brain import events
            ok = events.resolve_latest_approval(new_state)
            rec["result"] = {"ok": bool(ok),
                             "reason": "ثبت شد" if ok else "approval معلقی پیدا نشد"}
        except Exception as e:
            rec["result"] = {"ok": False, "reason": f"خطای events: {type(e).__name__}: {e}"}
    rec["audit_path"] = _audit(rec, audit_dir)
    return rec


def proposal_diff(pid: str, max_lines: int = 400) -> str:
    """دیفِ unified از original.py/new.py یک پیشنهاد — read-only.

    دکترین: «سبزشدنِ اسکن ≠ بی‌خطر — همیشه دیف را نشان بده.»
    """
    import difflib
    pdir = SYSTEM_ROOT / "outputs" / "self_code_proposals" / pid
    try:
        a = (pdir / "original.py").read_text(encoding="utf-8",
                                             errors="replace").splitlines()
        b = (pdir / "new.py").read_text(encoding="utf-8",
                                        errors="replace").splitlines()
    except OSError:
        return "(دیف در دسترس نیست)"
    diff = list(difflib.unified_diff(a, b, fromfile="original", tofile="new",
                                     lineterm=""))
    if len(diff) > max_lines:
        diff = diff[:max_lines] + [f"… ({len(diff) - max_lines} خطِ دیگر بریده شد)"]
    return "\n".join(diff) if diff else "(بدون تفاوت)"


def audit_tail(limit: int = 20, audit_dir: Path | None = None) -> list[dict]:
    """آخرین رکوردهای evidence trail (جدیدترین آخر)."""
    p = (audit_dir or DEFAULT_AUDIT_DIR) / AUDIT_FILE
    if not p.exists():
        return []
    out: list[dict] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-limit:]:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        return []
    return out
