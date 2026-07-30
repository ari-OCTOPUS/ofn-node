#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mission_approval_bridge — مسیرِ گمشدهٔ «کارتِ A3 → صفِ تأییدِ مالک → حکم → دفترِ mission».

ممیزیِ ۰۷-۳۱ شکاف را دقیق نشان داد: planner برای هر OWNER_GATE یک کارتِ کامل
می‌سازد (`owner_gate.make_card`) و goal_action_bridge آن را دور می‌ریخت —
mission با `needs_approval` در دفتر می‌نشست و **هیچ سطحی آن را به مالک
نمی‌رساند و هیچ مسیری حکمِ مالک را برنمی‌گرداند**. حلقهٔ «هدف → برنامه →
اقدامِ مجاز» درست در پلهٔ «مجاز» قطع بود.

این ماژول فقط همان مسیر است، با سه قاعدهٔ سخت:

  ۱) **هیچ قدرتِ اجراییِ نو ساخته نمی‌شود.** A3 یعنی «کاری که مالک باید
     بکند/تأیید کند» (classifier.BASE) و اجرای طبیعی‌اش همین رساندنِ کارت و
     ثبتِ حکم است. approve ِ مالک این‌جا **فقط** وضعِ mission را می‌بندد؛ هیچ
     executor ی صدا زده نمی‌شود (مسیرِ A2+ ساختاراً غایب است — executor.py).
     مجوزِ امضاشدهٔ owner_gate.grant هم عمداً صادر **نمی‌شود**: توکنِ مجوزِ
     بی‌مصرف‌کننده = سطحِ حمله، صفر فایده.
  ۲) **حکم فقط از صفِ تأیید می‌آید** (approval_store — همان صفی که رأی‌هایش
     در پروسهٔ مرکزِ تلگرام و با احرازِ مالک مصرف می‌شود). متنِ آزاد هرگز.
  ۳) **append-only + گذارِ قانونی.** هر تغییرِ وضع یک ردیفِ نو در
     missions.jsonl است و فقط از LEGAL_TRANSITIONS ِ mission_contract می‌گذرد:
     needs_approval → running (کارت در صف) → done/failed (حکمِ مالک).

فلگ `OCTOPUS_WIRE_MISSION_APPROVAL` عمداً در flags.cmd غایب و بیرون از
PAPER_FULL_FLAGS است ⇒ غیاب = واقعاً خاموش. مسلح‌کردن = کارتِ رأیِ مالک
(VQ-MISSION-APPROVAL-001).

$0 · stdlib · صفر شبکه (approval_store فایلِ محلی است) · fail-soft.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_MISSION_APPROVAL"
SCHEMA = "octopus.mission-approval.v1"
JOB_PREFIX = "sgc-mission"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _state_dir() -> Path:
    try:
        import opslib
        return Path(opslib.STATE_DIR) / "test_cycle"
    except Exception:  # noqa: BLE001
        return _OPS / "state" / "test_cycle"


def _cards_dir() -> Path:
    return _state_dir() / "owner_cards"


def _missions_path() -> Path:
    return _state_dir() / "missions.jsonl"


# ── دفترِ mission: کاهشِ append-only → آخرین وضعِ هر mission ────────────────
def _latest_missions() -> dict:
    out: dict = {}
    try:
        for line in _missions_path().read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and d.get("mission_id"):
                out[str(d["mission_id"])] = d
    except OSError:
        pass
    return out


def _append_transition(env: dict, new_status: str, **extra) -> bool:
    """یک ردیفِ گذارِ قانونی به دفتر اضافه کن. غیرقانونی = False، بی‌نوشتن."""
    try:
        import mission_contract as mc
        if not mc.can_transition(str(env.get("status")), new_status):
            return False
        row = dict(env)
        row["status"] = new_status
        row.update(extra)
        row["transition_ts"] = time.time()
        if mc.validate(row):
            return False
        p = _missions_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False


def _card_files() -> list:
    try:
        return sorted(_cards_dir().glob("*.json"))
    except OSError:
        return []


def _save_card(p: Path, rec: dict) -> bool:
    try:
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


# ── sweep: کارتِ stage‌شده → صفِ تأییدِ مالک ────────────────────────────────
def sweep(*, now: "float | None" = None) -> dict:
    """کارت‌های بی‌job را به صفِ تأیید ببر + گذارِ needs_approval→running.

    content-free به سبکِ approval_store: title/type/risk؛ متنِ کامل کارت روی
    دیسک می‌ماند و مالک از خودِ کارتِ mission می‌بیندش."""
    now = float(now if now is not None else time.time())
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    staged = 0
    errors = []
    latest = None
    for p in _card_files():
        try:
            rec = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(rec, dict) or rec.get("staged_job_id") or rec.get("verdict"):
            continue
        mid = str(rec.get("mission_id") or "")
        if not mid:
            continue
        if latest is None:
            latest = _latest_missions()
        env = latest.get(mid)
        if not isinstance(env, dict) or env.get("status") != "needs_approval":
            # دفترِ mission این کارت را نمی‌شناسد یا از این وضع گذشته — honesty
            errors.append({"mission_id": mid, "reason": "no-needs-approval-row"})
            continue
        try:
            import approval_store
            card = rec.get("card") or {}
            jid = approval_store.add_pending({
                "id": f"{JOB_PREFIX}-{mid}",
                "type": "sgc_action",
                "title": str(card.get("intent") or env.get("intent") or
                             env.get("action") or "SGC action")[:160],
                "risk": str(env.get("risk") or "high"),
                "dry_run_report": (f"class={rec.get('classification')} "
                                   f"action={env.get('action')} "
                                   f"target={str(card.get('target') or '')[:120]}"),
                "source": "mission_approval_bridge",
            })
        except Exception as e:  # noqa: BLE001
            errors.append({"mission_id": mid, "reason": f"store:{type(e).__name__}"})
            continue
        if not jid:
            errors.append({"mission_id": mid, "reason": "store-refused"})
            continue
        if not _append_transition(env, "running",
                                  output_refs=[f"owner-card:{p.name}",
                                               f"approval-job:{jid}"]):
            errors.append({"mission_id": mid, "reason": "transition-refused"})
            continue
        rec["staged_job_id"] = jid
        rec["staged_ts"] = now
        if not _save_card(p, rec):
            errors.append({"mission_id": mid, "reason": "card-save-failed"})
            continue
        staged += 1
    out = {"ok": True, "staged": staged}
    if errors:
        out["errors"] = errors[:6]
    return out


# ── collect: حکمِ مالک از صف → دفترِ mission ────────────────────────────────
def collect(*, now: "float | None" = None) -> dict:
    """کارت‌های در-صف را با bucket ِ approval_store آشتی بده و mission را ببند."""
    now = float(now if now is not None else time.time())
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    settled = 0
    errors = []
    latest = None
    for p in _card_files():
        try:
            rec = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(rec, dict) or not rec.get("staged_job_id") or rec.get("verdict"):
            continue
        mid = str(rec.get("mission_id") or "")
        try:
            import approval_store
            job = approval_store.get(str(rec["staged_job_id"]))
        except Exception as e:  # noqa: BLE001
            errors.append({"mission_id": mid, "reason": f"store:{type(e).__name__}"})
            continue
        status = str((job or {}).get("status") or "")
        if status not in ("approved", "rejected", "done"):
            continue                      # هنوز منتظرِ مالک
        if latest is None:
            latest = _latest_missions()
        env = latest.get(mid)
        if not isinstance(env, dict) or env.get("status") != "running":
            errors.append({"mission_id": mid, "reason": "no-running-row"})
            continue
        verdict = "approved" if status in ("approved", "done") else "rejected"
        final = "done" if verdict == "approved" else "failed"
        refs = list(env.get("output_refs") or [])
        refs.append(f"owner-verdict:{verdict}")
        ok = (_append_transition(env, final, output_refs=refs)
              if final == "done" else
              _append_transition(env, final, output_refs=refs,
                                 failure_reason="owner-rejected"))
        if not ok:
            errors.append({"mission_id": mid, "reason": "transition-refused"})
            continue
        rec["verdict"] = verdict
        rec["verdict_ts"] = now
        if not _save_card(p, rec):
            errors.append({"mission_id": mid, "reason": "card-save-failed"})
            continue
        settled += 1
    out = {"ok": True, "settled": settled}
    if errors:
        out["errors"] = errors[:6]
    return out


def beat(*, now: "float | None" = None) -> dict:
    """یک ضربان: اول حکم‌های رسیده، بعد کارت‌های تازه. fail-soft، idempotent."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    c = collect(now=now)
    s = sweep(now=now)
    return {"ok": True, "schema": SCHEMA,
            "settled": c.get("settled", 0), "staged": s.get("staged", 0),
            **({"errors": (c.get("errors") or []) + (s.get("errors") or [])}
               if (c.get("errors") or s.get("errors")) else {})}


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps(beat(), ensure_ascii=False, indent=1))
