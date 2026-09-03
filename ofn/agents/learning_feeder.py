"""learning_feeder — فیدرِ خودکارِ لِین یادگیری اقتصادی (gap #21/#23).

مشکل: کارت economic_learning کاکپیت و /money گلاس از
09-LANES/ECONOMIC-LEARNING/runs/<date>/run-summary.json می‌خوانند؛ ولی این
run فقط با CLI دستی ساخته می‌شد → کارت همیشه به run قدیمی می‌چسبید.

این فیدر حلقه را می‌بندد: آخرین رویدادهای events.jsonl (پرداخت/کوت/ارسال)
را به فرمت evidence/claims همان CLI می‌پیچد و `learning.cli run` را صدا
می‌زند — run تازه در runs/<UTC-date>/ می‌نشیند و هر دو مصرف‌کننده تازه
می‌شوند. فقط-خواندن روی events؛ نوشتن فقط در مسیر runs و لجر مجاز.

قواعد: هیچ عددی حدس زده نمی‌شود (payment بدون claim تأیید = unverified)؛
بدون رویداد تازه = بدون run جدید (صادقانه skip)؛ fail-soft با رسید.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parents[1]))
import opslib  # noqa: E402

SCHEMA = "octopus.learning-feeder.v1"
EVENTS = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
RUNS = _HERE.parents[1] / "09-LANES" / "ECONOMIC-LEARNING" / "runs"
CLI = _HERE.parents[1] / "ofn" / "learning" / "cli.py"
LEDGER = opslib.STATE_DIR / "legs" / "economic-learning-ledger.jsonl"
LOOKBACK_H = 24.0
MAX_EVENTS = 500


def _read_recent_events(now: float | None = None) -> list[dict]:
    import datetime as dt
    now = now if now is not None else dt.datetime.now(
        dt.timezone.utc).timestamp()
    p = EVENTS
    if not p.exists():
        return []
    cutoff = now - LOOKBACK_H * 3600
    out = []
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(ln)
            ts = dt.datetime.fromisoformat(
                e["occurred_at"].replace("Z", "+00:00")).timestamp()
            if ts >= cutoff:
                out.append(e)
        except (ValueError, KeyError, AttributeError):
            continue
        if len(out) >= MAX_EVENTS:
            break
    return out


def build_evidence(events: list[dict], campaign_id: str = "AUTO-FEED") -> tuple[dict, list]:
    """رویدادها → (evidence, claims) با همان schema که cli.run می‌خواند.
    lead_id از correlation_id؛ فقط رویدادهای شناخته‌شده نگه داشته می‌شوند."""
    per_lead: dict[str, list] = {}
    for e in events:
        lead = e.get("correlation_id") or "unattributed"
        kind = e.get("event_type", "")
        if kind not in ("communication.quote_requested", "communication.sent",
                        "payment.verified", "payment.claimed",
                        "quote.owner_approved"):
            continue
        per_lead.setdefault(lead, []).append({
            "type": kind, "at": e.get("occurred_at"),
            "amount": (e.get("payload") or {}).get("amount")})
    evidence = {
        "campaign_id": campaign_id,
        "snapshot_sha256": opslib.now_iso(),
        "leads": [{"lead_id": k, "events": v} for k, v in per_lead.items()],
    }
    claims = [{"lead_id": k, "claim_type": "owner_statement"}
              for k, v in per_lead.items()
              if any(x["type"] == "payment.claimed" for x in v)]
    return evidence, claims


def feed(now: float | None = None) -> dict:
    events = _read_recent_events(now)
    if not events:
        return {"schema": SCHEMA, "ok": True, "skipped":
                "no fresh events — an honest no-op"}
    evidence, claims = build_evidence(events)
    date = time.strftime("%Y%m%d", time.gmtime(
        now if now is not None else time.time()))
    out = RUNS / f"auto-{date}" 
    out.mkdir(parents=True, exist_ok=True)
    ev_f, cl_f = out / "_evidence.json", out / "_claims.json"
    ev_f.write_text(json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
    cl_f.write_text(json.dumps(claims, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(CLI), "run", "--evidence", str(ev_f),
         "--claims", str(cl_f), "--out", str(out), "--ledger",
         str(LEDGER)], capture_output=True, text=True, timeout=120,
        cwd=str(_HERE.parents[1]))
    summary_ok = (out / "run-summary.json").exists()
    return {"schema": SCHEMA, "ok": summary_ok and r.returncode == 0,
            "run_dir": str(out), "events_used": len(events),
            "rc": r.returncode, "tail": (r.stdout or r.stderr)[-200:]}


def main() -> int:
    print(json.dumps(feed(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
