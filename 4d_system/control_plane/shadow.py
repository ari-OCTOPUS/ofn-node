"""
control_plane/shadow.py — v2: Shadow Policy (فقط گزارش، هیچ enforcement).

policy ladder را روی جریانِ واقعیِ رویدادها (dashboard_events) اجرا می‌کند و
می‌گوید «اگر حاکمیت live بود، برای هر رویداد چه تصمیمی گرفته می‌شد» — به‌علاوه‌ی
مقایسه با آنچه واقعاً رخ داده (approval simulation):

  • agreement        — سیستمِ فعلی همان‌جایی گیت گذاشته که policy می‌خواست.
  • ungated_high_risk — policy می‌گوید approval لازم بود ولی رویداد بی‌گیت بود.
  • over_gated       — سیستم گیت گذاشته جایی که policy لازم نمی‌دانست (اطلاعی).

قواعدِ سخت:
  • فقط SELECT از bus؛ هیچ نوشتنی جز گزارشِ خودش در outputs/control_plane/_reports.
  • deterministic: با همان محتوای DB، همان تصمیم‌ها (زمانِ تولید فقط در متادیتا).
  • رویدادِ قابلِ‌نگاشت‌نبودن → needs_review، هرگز silent-pass.
  • flag: CONTROL_PLANE_SHADOW_POLICY (default-off) فقط اجرای خودکارِ UI را
    روشن می‌کند؛ خودِ تحلیل همیشه on-demand و بی‌خطر است.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from control_plane.flags import flag
from control_plane.policy import Level, evaluate
from control_plane.snapshot import budget_status, DEFAULT_OUT

SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = SYSTEM_ROOT / "outputs" / "4d_experiments.db"
DEFAULT_REPORT_DIR = SYSTEM_ROOT / "outputs" / "control_plane" / "_reports"

# نگاشتِ agent_id → action_type (رفتارِ امروزِ سیستم — verified در discovery)
AGENT_ACTION: dict[str, str] = {
    "explore": "write_outputs", "real": "write_outputs", "synthesize": "write_outputs",
    "conclude": "write_outputs", "mutate": "write_outputs", "frontier": "write_outputs",
    "vault": "write_outputs", "autoloop": "write_outputs",
    "create": "memory_write",
    "introspect": "read_only", "guard": "read_only", "system": "read_only",
    "evolve": "strategy_apply",
    # aliasهای تاریخیِ روی bus — verified در اولین shadow run واقعی (2026-07-11:
    # ۶۳ رویداد creative + ۲۸ رویداد guardrail)؛ ui/tab_dashboard._MODE_LABEL هم
    # هر دو املا را همان حالت‌های create/guard می‌داند.
    "creative": "memory_write", "guardrail": "read_only",
}

_CODE_HINTS = ("کد", "پیشنهاد", "pid", "self_code")

# اسکنِ متنِ summary برای actionهای مخرب/high-risk. bus فیلدِ action-type ندارد،
# پس یک اکشنِ واقعاً مخرب به‌صورتِ task.completed با متنِ آزاد ظاهر می‌شود؛ بدونِ
# این اسکن، classifier کورِ ساختاری بود (همه‌ی agentها → اکشنِ low-risk). هر کلید
# به یک action_type از policy.ACTION_POLICY نگاشت می‌شود (اولین تطابق برنده).
_DESTRUCTIVE_MARKERS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("self_code apply", "self-code apply", "اعمالِ کد", "applied self", "apply به run.py",
      "کدِ زنده", "کد اعمال"), "self_code_apply"),
    (("delete", "drop table", "rm -rf", "wipe", "truncate", "remove", "purge",
      "erase", "overwrite", "reset", "حذفِ داده", "پاک‌سازیِ", "حذف", "پاک کردن",
      "بازنویسیِ", "صفر کردن"), "delete_data"),
    (("run.py", "core/", "guardrails", "__init__", "تغییرِ TCB", "change tcb"), "change_tcb"),
    ((".env", "secret", "token", "credential", "رمز", "کلیدِ api"), "change_env_or_secrets"),
    (("publish", "انتشار", "send email", "ارسالِ ایمیل", "post to", "منتشر"),
     "external_send_publish"),
    (("cross-project", "بین‌پروژه", "cross project"), "cross_project_write"),
    (("subprocess", "os.system", "shell=true", "اجرای فرمانِ بیرونی", "run external"),
     "run_external_command"),
    (("model promotion", "ارتقای مدل", "promote model"), "model_promotion"),
    (("restore backup", "بازگردانیِ بکاپ", "backup restore"), "backup_restore"),
)


def _scan_destructive(summary: str) -> str | None:
    """تطبیقِ کلیدواژه‌ی مخرب. برای واژه‌های تک‌کلمه‌ی انگلیسی word-boundary به‌کار
    می‌رود تا زیررشته‌های بی‌ربط (preset↛reset، swipe↛wipe) اشتباهاً flag نشوند؛
    عبارت‌های چندکلمه‌ای و فارسی با substring. best-effort روی متنِ آزاد."""
    s = (summary or "").lower()
    for keys, action in _DESTRUCTIVE_MARKERS:
        for k in keys:
            kl = k.lower()
            if kl.isascii() and kl.isalpha():   # تک‌واژه‌ی انگلیسی → مرزِ *چپ* فقط:
                # صرف‌ها را می‌گیرد (delete→deleted، wipe→wiped، token→tokens) ولی
                # زیررشته‌ی وسطِ کلمه را نه (preset↛reset، swipe↛wipe).
                if re.search(r"\b" + re.escape(kl), s):
                    return action
            elif kl in s:                        # عبارت/فارسی → substring
                return action
    return None


def shadow_enabled() -> bool:
    return flag("CONTROL_PLANE_SHADOW_POLICY")


def classify_event(row: dict[str, Any]) -> dict[str, Any]:
    """یک رویدادِ bus → تصمیمِ shadow (pure؛ بدونِ I/O و بدونِ زمانِ حال)."""
    agent = (row.get("agent_id") or "").strip()
    name = row.get("event_name") or ""
    summary = row.get("summary") or ""
    approval_state = row.get("approval_state") or "unknown"

    if name == "approval.required":
        # سیستم خودش درخواستِ تأیید کرده؛ نوعش را حدسِ محافظه‌کارانه می‌زنیم
        if any(h in summary for h in _CODE_HINTS):
            action = "self_code_approve"
        else:
            action = f"approval_event:{agent or 'unknown'}"  # ناشناخته → needs_review
    else:
        # اول متنِ summary را برای اکشنِ مخرب اسکن کن؛ اگر بود، همان (high-risk)
        # برنده است — وگرنه نگاشتِ agent (که low-risk است).
        action = _scan_destructive(summary) or AGENT_ACTION.get(
            agent, f"agent:{agent or 'unknown'}")

    res = evaluate(action)

    gated = approval_state in ("pending", "approved", "rejected")
    if res.requires_approval and not gated:
        agreement, mismatch = False, "ungated_high_risk"
    elif (not res.requires_approval) and approval_state == "pending":
        agreement, mismatch = True, "over_gated"      # سخت‌گیریِ اضافه — اطلاعی
    else:
        agreement, mismatch = True, ""

    return {
        "event_id": row.get("id"),
        "timestamp": row.get("timestamp"),
        "trace_id": row.get("trace_id"),
        "agent_id": agent,
        "event_name": name,
        "status": row.get("status"),
        "approval_state": approval_state,
        "action_type": res.action_type,
        "level": res.level,
        "level_name": res.level_name,
        "requires_approval": res.requires_approval,
        "needs_review": res.needs_review,
        "agreement": agreement,
        "mismatch": mismatch,
        "is_failure": name == "task.failed",
        "summary": summary[:120],
    }


def _failure_streaks(decisions: list[dict]) -> dict[str, int]:
    """بیشینه‌ی شکستِ پیاپی به‌ازای هر agent (روی ترتیبِ زمانی)."""
    streak: dict[str, int] = {}
    best: dict[str, int] = {}
    for d in decisions:
        a = d["agent_id"] or "?"
        if d["is_failure"]:
            streak[a] = streak.get(a, 0) + 1
            best[a] = max(best.get(a, 0), streak[a])
        else:
            streak[a] = 0
    return {a: n for a, n in best.items() if n >= 3}


def _budget_shadow(out: Path) -> dict[str, Any]:
    """شبیه‌سازیِ policy روی خرج: ≥۸۰٪ سقف → هشدار؛ سقف‌پر → approval لازم."""
    b = budget_status(out)
    if b.get("status") != "OK":
        return {"verdict": "UNKNOWN", "detail": b}
    cap = max(1, int(b.get("cap", 1)))
    used = int(b.get("cloud_calls", 0))
    ratio = used / cap
    if ratio >= 1.0:
        level = int(Level.REQUIRE_APPROVAL)
        verdict = "WOULD_REQUIRE_APPROVAL (budget_increase)"
    elif ratio >= 0.8:
        level = int(Level.SOFT_WARN)
        verdict = "SOFT_WARN (نزدیکِ سقف)"
    else:
        level = int(Level.OBSERVE)
        verdict = "OK"
    return {"verdict": verdict, "level": level, "used": used, "cap": cap,
            "ratio": round(ratio, 3)}


def run_shadow(db: Path | None = None,
               out: Path | None = None,
               report_dir: Path | None = None,
               limit: int = 500,
               write_reports: bool = True) -> dict[str, Any]:
    """تحلیلِ shadow روی آخرین رویدادها + (اختیاری) نوشتنِ گزارش در مسیرِ خودش."""
    db = db or DEFAULT_DB
    out = out or DEFAULT_OUT
    if not db.exists():
        return {"status": "UNKNOWN", "reason": "bus در دسترس نیست"}
    try:
        conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(
                "SELECT id, timestamp, trace_id, agent_id, event_name, status,"
                " summary, approval_state FROM dashboard_events"
                " ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
        finally:
            conn.close()
    except sqlite3.Error as e:
        return {"status": "UNKNOWN", "reason": f"{type(e).__name__}"}
    rows.reverse()  # ترتیبِ زمانی برای streak

    decisions = [classify_event(r) for r in rows]

    by_level: dict[str, int] = {}
    by_action: dict[str, int] = {}
    for d in decisions:
        by_level[d["level_name"]] = by_level.get(d["level_name"], 0) + 1
        by_action[d["action_type"]] = by_action.get(d["action_type"], 0) + 1

    would_approve = [d for d in decisions if d["requires_approval"]]
    needs_review = [d for d in decisions if d["needs_review"]]
    disagreements = [d for d in decisions if d["mismatch"] == "ungated_high_risk"]
    over_gated = sum(1 for d in decisions if d["mismatch"] == "over_gated")

    report: dict[str, Any] = {
        "status": "OK",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "shadow_flag_enabled": shadow_enabled(),
        "window": {
            "n": len(decisions),
            "min_event_id": decisions[0]["event_id"] if decisions else None,
            "max_event_id": decisions[-1]["event_id"] if decisions else None,
        },
        "summary": {
            "analyzed": len(decisions),
            "by_level": by_level,
            "by_action": by_action,
            "would_require_approval": len(would_approve),
            "needs_review": len(needs_review),
            "ungated_high_risk": len(disagreements),
            "over_gated": over_gated,
            "failure_streaks_ge3": _failure_streaks(decisions),
            "budget_shadow": _budget_shadow(out),
        },
        "disagreements": disagreements[:20],
        "would_require_approval_sample": would_approve[:10],
        "needs_review_sample": needs_review[:10],
    }

    if write_reports:
        rd = report_dir or DEFAULT_REPORT_DIR
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "shadow_policy.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        with open(rd / "shadow_decisions.jsonl", "w", encoding="utf-8") as f:
            for d in decisions:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        (rd / "shadow_policy.md").write_text(_render_md(report), encoding="utf-8")
        report["report_json"] = str(rd / "shadow_policy.json")
        report["report_md"] = str(rd / "shadow_policy.md")
    return report


def _render_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    w = report["window"]
    lines = [
        "# Shadow Policy — «اگر live بود چه می‌شد»",
        f"_تولید: {report['generated_at']} · رویدادهای {w['min_event_id']}–{w['max_event_id']}"
        f" (n={w['n']}) · فقط گزارش، هیچ enforcement_",
        "",
        f"- تحلیل‌شده: **{s['analyzed']}**",
        f"- approval لازم می‌شد: **{s['would_require_approval']}**",
        f"- needs_review (نگاشت‌ناپذیر): **{s['needs_review']}**",
        f"- ⛔ high-risk بی‌گیت: **{s['ungated_high_risk']}**",
        f"- سخت‌گیریِ اضافه (over-gated): {s['over_gated']}",
        f"- بودجه: {s['budget_shadow'].get('verdict')}"
        f" ({s['budget_shadow'].get('used', '?')}/{s['budget_shadow'].get('cap', '?')})",
        "",
        "## توزیعِ سطح‌ها",
    ]
    for lv, n in sorted(s["by_level"].items()):
        lines.append(f"- {lv}: {n}")
    if s["failure_streaks_ge3"]:
        lines += ["", "## شکست‌های پیاپی (≥۳)"] + [
            f"- {a}: {n} پیاپی" for a, n in s["failure_streaks_ge3"].items()]
    if report["disagreements"]:
        lines += ["", "## ⛔ ناسازگاری‌ها (ungated high-risk)"]
        for d in report["disagreements"]:
            lines.append(f"- #{d['event_id']} {d['agent_id']}/{d['event_name']}"
                         f" → {d['action_type']} (L{d['level']}) · {d['summary'][:60]}")
    else:
        lines += ["", "هیچ high-risk بی‌گیتی دیده نشد ✅"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    rep = run_shadow()
    if rep.get("status") != "OK":
        print("UNKNOWN:", rep.get("reason"))
    else:
        print(json.dumps(rep["summary"], ensure_ascii=False, indent=1))
        print("report:", rep.get("report_md"))
