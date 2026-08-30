#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""thesis_queue.py — اندامِ ایستادهٔ اثبات: دفترِ تز → قراردادِ پژوهش.

رأیِ مالک 2026-07-25: «یک قسمتی همیشه دنبالِ اثباتِ این موضوع باشد. قانون مهمه.»
تفاوتِ قانون با آرزو این است که قانون **خوانده** می‌شود. این ماژول دفترِ تز را به صفِ
قراردادهایی تبدیل می‌کند که `research_loop.run_experiment` می‌تواند اجرا کند.

سه قاعدهٔ قفل‌شدهٔ دفتر، این‌جا ساختاراً اجرا می‌شوند نه توصیه:

  ۱) هیچ ردیفی بدونِ شرطِ مرگ → `select()` ردیفِ بی‌`kill` را هرگز برنمی‌گرداند.
  ۲) وضعیت را فقط شاهد عوض می‌کند → این ماژول روی status **فقط‌خواندنی** است.
     تنها راهِ نوشتن `record_evidence()` است که یک `ledger_entry`ِ واقعیِ
     research_loop با verdictِ terminal می‌خواهد؛ نوشتنِ مستقیمِ status رد می‌شود.
  ۳) ردیفِ ابطال‌شده حذف نمی‌شود → `record_evidence` فقط append می‌کند
     (`status_history`)، و هیچ مسیرِ حذفی وجود ندارد.

قواعدِ سختِ دیگر:
  - **صفر اجرا:** این ماژول هیچ آزمایشی نمی‌دود. فقط قرارداد می‌سازد.
  - **صادق دربارهٔ نادانی:** ردیفی که آزمایشِ ثبت‌شده ندارد پنهان نمی‌شود؛
    با `needs_experiment_design` گزارش می‌شود. صفِ خالیِ دروغین ممنوع.
  - **بی‌ادعای پدیدارشناختی:** هر ردیفی که کلیدواژهٔ آگاهی/تجربه داشته باشد
    و `no_phenomenal_claims` روشن باشد، از صف بیرون می‌ماند (`phenomenal-claim`).
  - flag-gated و default-off: `OCTOPUS_WIRE_THESIS_QUEUE`.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

FLAG = "OCTOPUS_WIRE_THESIS_QUEUE"

# ردیف‌هایی که ارزشِ کارِ تازه دارند، به ترتیبِ اولویت. کلید = status، مقدار = (اولویت، چرا).
_WORK_PRIORITY = {
    # سنجش‌شده و خلافِ ادعا درآمده: بیشترین ارزشِ اطلاعاتی — یا واقعاً غلط است یا نمونه کم بوده.
    "FALSIFIED_SO_FAR": (0, "عددِ منفیِ اندازه‌گیری‌شده — با نمونهٔ بیشتر و holdout دوباره سنجیده شود"),
    # کار می‌کند ولی مفیدبودنش سنجیده نشده: ارزانی و مستقیم.
    "MECHANISM_SUPPORTED_VALUE_UNTESTED": (1, "مکانیزم هست، ارزش نه — آزمونِ جفت‌شده لازم است"),
    # ابزار خودش گفت آماده نیست: مسیرِ روشن.
    "HONEST_NOGO": (2, "ابزار صادقانه NO-GO داد — شرطِ GO مشخص و آزمون‌پذیر است"),
    # هیچ ابزارِ سنجشی ندارد: اول ابزار، بعد ادعا.
    "UNTESTED": (3, "ابزارِ سنجش وجود ندارد — ساختِ ابزار مقدم بر ادعا"),
    # آرتیفکت رفع شد ولی ادعا نیازموده — دقیقاً مثلِ UNTESTED کارِ تازه می‌خواهد.
    "ARTIFACT_RESOLVED_CLAIM_UNTESTED": (3, "آرتیفکت رفع شد؛ ادعای اصلی هنوز نیازموده"),
    # پیاده‌سازی غلط بود، ایده ممکن است درست باشد.
    "FALSIFIED_AS_IMPLEMENTED": (4, "ایده ممکن است زنده باشد — پیاده‌سازیِ دوم با گاردِ دژنره"),
    "ARTIFACT": (5, "عدد اشباع بود نه اندازه‌گیری — آزمونِ اشباع لازم است"),
}

# ردیف‌هایی که کارِ تازه نمی‌خواهند (شاهد دارند و شرطِ مرگشان برقرار نشده).
_SETTLED = ("SUPPORTED", "FALSIFIED")

# صورتِ اولیه‌ای که شرطِ مرگ ندارد: کارِ درست بازنویسی است، نه آزمایش.
_NEEDS_REFRAME = ("UNFALSIFIABLE_AS_STATED",)

_PHENOMENAL = ("آگاهی", "خودآگاه", "تجربهٔ", "consciousness", "sentien", "qualia", "phenomenal")

_TERMINAL_VERDICTS = ("accepted", "rejected", "quarantined", "verified-not-admitted")

# ثبتِ آزمایشِ اجراپذیر: row_id → کلیدِ آزمایش. هرچه این‌جا نیست، آزمایش ندارد — و
# صادقانه گزارش می‌شود. **حق اختراعِ آزمایش برای یک ردیف را این ماژول ندارد.**
EXPERIMENT_REGISTRY: dict[str, str] = {
    "delta-self": "selfmodel_delta_paired",   # heart/shadow.py
    "phi-liveness": "phi_saturation_probe",   # chrono.py
    "metabolic-budget": "metabolic_value_paired",  # cardiac.py — آزمونِ ارزشِ ترمز
    "effect-gate-once": "effect_double_apply_probe",  # arm_gate.py — double-apply test
    "identity-O": "organism_identity_tracker",  # identity_equations.py — روندِ O
    "lead-direct": "lead_direct_residential_probe",  # legs/lead_scorer.py — draft rate
}


def enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in ("1", "true", "yes", "on")


def _ledger_path(state_dir=None) -> Path:
    if state_dir:
        return Path(state_dir) / "thesis" / "thesis-ledger.json"
    env = os.environ.get("OCTOPUS_THESIS_LEDGER", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "state" / "thesis" / "thesis-ledger.json"


def load(state_dir=None) -> dict:
    """دفتر را می‌خواند. fail-soft: نبودِ فایل → دفترِ خالی، نه crash."""
    p = _ledger_path(state_dir)
    try:
        d = json.loads(p.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {"rows": [], "_missing": str(p)}
    if not isinstance(d, dict) or not isinstance(d.get("rows"), list):
        return {"rows": [], "_malformed": str(p)}
    return d


def _has_kill(row: dict) -> bool:
    """قاعدهٔ ۱: شرطِ مرگِ واقعی. خطِ تیره/خالی شرط نیست."""
    k = (row.get("kill") or "").strip().strip("—-— ")
    return len(k) >= 12


def _is_phenomenal(row: dict) -> bool:
    blob = " ".join(str(row.get(k) or "") for k in ("claim", "proof", "id"))
    low = blob.lower()
    return any(w.lower() in low for w in _PHENOMENAL)


def classify(row: dict, *, no_phenomenal_claims: bool = True) -> dict:
    """یک ردیف → {eligible, reason, priority, experiment}. هرگز raise نمی‌کند."""
    rid = str(row.get("id") or "?")
    status = str(row.get("status") or "?")
    out = {"id": rid, "status": status, "eligible": False, "reason": "", "priority": 99,
           "experiment": EXPERIMENT_REGISTRY.get(rid)}

    if no_phenomenal_claims and _is_phenomenal(row):
        # صورتِ اولیهٔ ادعای مادر این‌جا می‌افتد — و همان درست است: بازنویسیِ
        # آزمون‌پذیرش (delta-self / evolution_lab / c15) خودش ردیفِ جدا دارد.
        out["reason"] = "phenomenal-claim — ادعا دربارهٔ آگاهی/تجربه است، نه ساختار/توانایی"
        return out
    if not _has_kill(row):
        out["reason"] = "no-kill-condition — قاعدهٔ ۱: ادعایی که راهِ ابطال ندارد ادعا نیست"
        return out
    if status in _NEEDS_REFRAME:
        out["reason"] = "needs-reframe — کارِ درست بازنویسیِ آزمون‌پذیر است نه آزمایش"
        return out
    if status in _SETTLED:
        out["reason"] = "settled — شاهد دارد و شرطِ مرگش برقرار نشده؛ کارِ تازه نمی‌خواهد"
        return out
    if status not in _WORK_PRIORITY:
        out["reason"] = f"unknown-status:{status}"
        return out

    pri, why = _WORK_PRIORITY[status]
    out.update(priority=pri, reason=why)
    if out["experiment"] is None:
        # صادق دربارهٔ نادانی: واجدِ شرط است ولی اجراپذیر نیست.
        out["reason"] = f"needs_experiment_design — {why}"
        return out
    out["eligible"] = True
    return out


def select(*, limit: int = 3, state_dir=None) -> dict:
    """صف. خروجی: {runnable, needs_design, blocked, ledger_rows, kill_check}.

    هیچ چیزی را اجرا نمی‌کند و هیچ چیزی را نمی‌نویسد."""
    d = load(state_dir)
    rows = d.get("rows") or []
    # گاردِ پدیدارشناختی fail-closed: نبودِ بلوکِ اعلام هم آن را خاموش نمی‌کند.
    cls = [classify(r, no_phenomenal_claims=_no_phenomenal(d))
           for r in rows if isinstance(r, dict)]

    runnable = sorted([c for c in cls if c["eligible"]], key=lambda c: (c["priority"], c["id"]))
    needs = sorted([c for c in cls if c["reason"].startswith("needs_experiment_design")],
                   key=lambda c: (c["priority"], c["id"]))
    blocked = [c for c in cls if not c["eligible"]
               and not c["reason"].startswith("needs_experiment_design")]
    return {"runnable": runnable[:max(0, int(limit))],
            "runnable_total": len(runnable),
            "needs_design": needs,
            "blocked": blocked,
            "ledger_rows": len(rows),
            "kill_check": kill_check(d),
            "ledger_missing": d.get("_missing") or d.get("_malformed")}


def _no_phenomenal(d: dict) -> bool:
    # از budgets.yaml اعلام شده؛ پیش‌فرضِ محافظه‌کار = روشن.
    return True


def to_contract(cand: dict, row: dict) -> dict:
    """قراردادِ هم‌شکلِ research_loop. `experiment_fn`/`verifier_fn` را فراخوان می‌دهد."""
    return {
        "contract_id": f"thesis-{cand['id']}",
        "hypothesis": row.get("claim") or "",
        "kill_condition": row.get("kill") or "",
        "success_criterion": row.get("proof") or "",
        "experiment": cand.get("experiment"),
        "prior_status": cand.get("status"),
        "prior_evidence": row.get("evidence"),
        "source": "thesis_queue",
        "family": row.get("family"),
    }


def kill_check(d: dict, *, now: float | None = None, window_days: float = 90.0) -> dict:
    """شرطِ مرگِ خودِ تخصیصِ ۲۵٪: ۹۰ روز بی‌هیچ حرکتِ وضعیت → توقف.

    «ابطال هم حرکت است — پیشرفت لازم نیست، سنجش لازم است.»"""
    rows = d.get("rows") or []
    stamps = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        for h in (r.get("status_history") or []):
            if isinstance(h, dict) and isinstance(h.get("at"), (int, float)):
                stamps.append(float(h["at"]))
    if not stamps:
        # هیچ حرکتِ ثبت‌شده‌ای نیست. این **نبودِ داده** است نه رسیدنِ شرطِ مرگ —
        # پنجره از اولین حرکتِ واقعی شروع می‌شود، نه از الان.
        return {"movements": 0, "verdict": "no-movement-recorded-yet",
                "note": "پنجرهٔ ۹۰ روز از اولین حرکتِ ثبت‌شده شروع می‌شود"}
    t = float(now if now is not None else time.time())
    idle_days = (t - max(stamps)) / 86400.0
    return {"movements": len(stamps), "idle_days": round(idle_days, 2),
            "window_days": window_days,
            "verdict": "kill-condition-met" if idle_days > window_days else "alive"}


def record_evidence(*, row_id: str, new_status: "str | None", ledger_entry: dict,
                    state_dir=None) -> dict:
    """قاعدهٔ ۲ و ۳، ساختاری. تنها راهِ تغییرِ وضعیت.

    `ledger_entry` باید یک ردیفِ واقعیِ research_loop با verdictِ terminal باشد.
    بدونِ آن → رد. هیچ ردیفی حذف یا بازنویسی نمی‌شود؛ فقط `status_history` رشد می‌کند.

    `new_status=None` → **فقط شاهد ثبت کن، وضعیت را دست نزن.** این حالتِ پیش‌فرضِ
    سیمِ خودکار است: اندازه‌گیری همیشه ثبت می‌شود (پس شرطِ مرگِ ۹۰ روزه برآورده
    می‌شود) ولی ارتقا/تنزلِ وضعیت فقط وقتی رخ می‌دهد که منطقاً اجباری باشد."""
    if not isinstance(ledger_entry, dict):
        return {"ok": False, "reason": "no-evidence — ledger_entry لازم است (قاعدهٔ ۲)"}
    verdict = str(ledger_entry.get("verdict") or "")
    if verdict not in _TERMINAL_VERDICTS:
        return {"ok": False,
                "reason": f"non-terminal-verdict:{verdict or 'missing'} — شاهد باید حکمِ نهایی باشد"}
    if not ledger_entry.get("experiment_key"):
        return {"ok": False, "reason": "no-experiment-key — شاهدِ بی‌رد اجرا پذیرفته نمی‌شود"}

    p = _ledger_path(state_dir)
    try:
        d = json.loads(p.read_text("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"ledger-unreadable:{type(e).__name__}"}
    for r in (d.get("rows") or []):
        if isinstance(r, dict) and r.get("id") == row_id:
            hist = r.setdefault("status_history", [])
            hist.append({"from": r.get("status"),
                         "to": new_status if new_status else r.get("status"),
                         "status_changed": bool(new_status),
                         "at": time.time(), "verdict": verdict,
                         "measured": ledger_entry.get("measured"),
                         "experiment_key": ledger_entry.get("experiment_key"),
                         "contract_id": ledger_entry.get("contract_id")})
            if new_status:                   # ردیف بازنویسی نمی‌شود؛ تاریخش می‌ماند
                r["status"] = new_status
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")
            tmp.replace(p)
            return {"ok": True, "row_id": row_id, "status": r.get("status"),
                    "status_changed": bool(new_status), "history_len": len(hist)}
    return {"ok": False, "reason": f"unknown-row:{row_id}"}


# ── سیمِ برگشت: حکمِ ضربانِ خودکارِ C6 → دفترِ تز ───────────────────────────
# پروبِ ثبت‌شده در c6_probes.PROBES ← → ردیفِ دفترِ تز.
PROBE_TO_ROW: dict[str, str] = {
    "thesis_delta_self_sign": "delta-self",
    "thesis_phi_saturation": "phi-liveness",
}

# انتقال‌هایی که **منطقاً اجباری**اند. هرچه این‌جا نیست، وضعیت را عوض نمی‌کند و فقط
# شاهد ثبت می‌شود. کلید = (وضعیتِ فعلی، آیا مکانیزم بازتولید شد؟).
#
# چرا این جدول این‌قدر کوچک است: پروبِ «آیا نقص هنوز بازتولید می‌شود؟» فقط می‌تواند
# **نبودِ** آن نقص را نشان دهد، نه درستیِ ادعای اصلی را. مثال: نبودِ اشباعِ phi ثابت
# می‌کند عدد دیگر اشباع نیست — ثابت نمی‌کند phi مرگ را از سکون تشخیص می‌دهد. پس
# ARTIFACT به SUPPORTED نمی‌رود؛ به «آرتیفکت رفع شد، ادعا هنوز نیازموده» می‌رود.
_FORCED: dict[tuple, str] = {
    ("ARTIFACT", False): "ARTIFACT_RESOLVED_CLAIM_UNTESTED",
}


def record_from_c6(queue_row: dict, *, state_dir=None) -> dict:
    """ردیفِ DONEِ صفِ C6 → شاهد در دفترِ تز. flag-gated، fail-soft، هرگز raise."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    if not isinstance(queue_row, dict):
        return {"ok": False, "reason": "bad-row"}
    probe = str(queue_row.get("probe") or "")
    row_id = PROBE_TO_ROW.get(probe)
    if not row_id:
        return {"ok": False, "reason": f"not-a-thesis-probe:{probe or 'none'}"}
    raw = str(queue_row.get("verdict") or "")
    # حکمِ C6 → واژگانِ terminalِ research_loop. «نامعلوم» شاهد نیست.
    if raw.startswith("accepted"):
        verdict = "accepted"
    elif raw.startswith("rejected"):
        verdict = "rejected"
    elif raw.startswith("quarantined"):
        verdict = "quarantined"
    else:
        return {"ok": False, "reason": f"non-terminal-c6-verdict:{raw or 'none'}"}

    measured = queue_row.get("measured") if isinstance(queue_row.get("measured"), dict) else {}
    count = measured.get("count")
    floor = queue_row.get("floor")
    reproduced = None
    if isinstance(count, (int, float)) and isinstance(floor, (int, float)):
        reproduced = (float(count) > float(floor)) if float(count) >= 0 else None

    d = load(state_dir)
    cur = next((r.get("status") for r in (d.get("rows") or [])
                if isinstance(r, dict) and r.get("id") == row_id), None)
    new_status = _FORCED.get((str(cur), reproduced)) if reproduced is not None else None

    return record_evidence(
        row_id=row_id, new_status=new_status, state_dir=state_dir,
        ledger_entry={"verdict": verdict,
                      "experiment_key": f"c6:{queue_row.get('id')}",
                      "contract_id": queue_row.get("id"),
                      "measured": measured})


def summary(state_dir=None) -> dict:
    """برای cockpit/self_knowledge: ارگانیسم بداند مسیرِ رویا در چه حالی است."""
    s = select(limit=3, state_dir=state_dir)
    return {"flag": FLAG, "enabled": enabled(),
            "thesis_rows": s["ledger_rows"],
            "runnable": s["runnable_total"],
            "needs_experiment_design": len(s["needs_design"]),
            "blocked": len(s["blocked"]),
            "next": [c["id"] for c in s["runnable"]],
            "kill_check": s["kill_check"],
            "ledger_missing": s["ledger_missing"]}


if __name__ == "__main__":  # pragma: no cover — پروبِ دستی، بی‌اثرِ جانبی
    print(json.dumps(summary(), ensure_ascii=False, indent=2))
