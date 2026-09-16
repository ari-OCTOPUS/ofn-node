#!/usr/bin/env python3
"""
_ops/synapse/trajectory_monitor.py — P3: مانیتورِ trajectory (زنجیره‌ای، نه تک‌رویداد).

درسِ حادثه‌ی ExploitGym (~۱۷٬۰۰۰ اکشن): گیتِ تک-effect کافی نیست. این ماژول روی
`_ops/state/events.jsonl` سه الگوی زنجیره‌ای را تشخیص می‌دهد:

  1) burst — نرخِ رویدادِ دقیقه‌ی جاری ≥ max(BURST_MIN, BURST_FACTOR × میانه‌ی baseline).
  2) novel-chain — 3-gram از event_nameها در پنجره‌ی اخیر که در baseline دیده نشده
     و دست‌کم یک عضوِ «کمیاب» (فراوانیِ baseline < RARE_FREQ) دارد.
  3) egress-attempt — نشانه‌های شبکه در event_name/summary (substring-match دفاعی).

خروجی: JSONL در `_ops/synapse/out/trajectory-alerts.jsonl` با schemaی
`trajectory.alert.v1` — به‌همان الگوی فایل-basedِ event_bridge، تا با tapِ مالک
به‌عنوانِ «منبع ۵» به `_ops/telegram_center/event_bridge.py` وصل شود
(wiring در این جلسه انجام نشده؛ پیشنهاد در AGENT_QUESTIONS).

قراردادها: پیش‌فرضِ خاموش (TRAJECTORY_MONITOR_ENABLED) · dedup با cursor
(یک امضا در ALERT_DEDUP_SECONDS فقط یک‌بار) · fail-closed (هرگز raise نمی‌کند).
هیچ‌کجا جز out/ خودش نمی‌نویسد. مصرفِ LLM: صفر.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FLAG = "TRAJECTORY_MONITOR_ENABLED"
ALERT_SCHEMA = "trajectory.alert.v1"

BURST_MIN = 10
BURST_FACTOR = 5.0
RARE_FREQ = 0.02
TAIL_N = 2600
TAIL_BYTES = 512 * 1024
ALERT_DEDUP_SECONDS = 3600
MAX_EVIDENCE = 5

EGRESS_MARKERS = (
    "http://", "https://", "socket", "urllib", "requests.",
    "curl", "wget", "egress", "webhook", "api.openai", "huggingface",
)

_HERE = Path(__file__).resolve()
DEFAULT_EVENTS = _HERE.parents[1] / "state" / "events.jsonl"
DEFAULT_OUT = _HERE.parent / "out" / "trajectory-alerts.jsonl"
DEFAULT_CURSOR = _HERE.parent / "out" / "trajectory-cursor.json"


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _tail_events(path: Path, n: int) -> list[dict]:
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            fh.seek(max(0, size - TAIL_BYTES))
            raw = fh.read().decode("utf-8", errors="replace")
        lines = [ln for ln in raw.splitlines() if ln.strip()][-n:]
        out: list[dict] = []
        for ln in lines:
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
        return out
    except Exception:
        return []


def check_once(events: list[dict]) -> list[dict]:
    """هسته‌ی خالصِ تشخیص — ورودی: لیستِ رویدادها؛ خروجی: لیستِ alertها.
    بدونِ I/O؛ deterministic؛ برای تست مستقیم قابل‌استفاده."""
    alerts: list[dict] = []
    if len(events) < 60:
        return alerts

    ts_events = [e for e in events if isinstance(e.get("ts"), (int, float))]
    names = [str(e.get("event_name", "?")) for e in events]

    # ── ۱) burst ────────────────────────────────────────────────────────────
    if len(ts_events) >= 60:
        per_min: Counter[int] = Counter(int(e["ts"] // 60) for e in ts_events)
        minutes = sorted(per_min)
        if len(minutes) >= 3:
            cur = per_min[minutes[-1]]
            base = [per_min[m] for m in minutes[:-1]]
            med = statistics.median(base) if base else 0.0
            threshold = max(BURST_MIN, BURST_FACTOR * max(med, 1.0))
            if cur >= threshold:
                alerts.append({
                    "kind": "burst",
                    "severity": "high" if cur >= 2 * threshold else "medium",
                    "evidence": [
                        {"metric": "events_last_minute", "value": cur},
                        {"metric": "baseline_median", "value": float(med)},
                        {"metric": "threshold", "value": float(threshold)},
                    ],
                    "summary": f"انفجارِ نرخِ رویداد: {cur}/دقیقه در برابرِ میانه‌ی {med:.1f}",
                })

    # ── ۲) novel-chain (3-gram) ──────────────────────────────────────────────
    if len(names) >= 60:
        split = int(len(names) * 0.7)
        base_names, win_names = names[:split], names[split:]
        base_grams = {tuple(base_names[i:i + 3]) for i in range(len(base_names) - 2)}
        freq = Counter(base_names)
        total = max(len(base_names), 1)
        novel: list[tuple[str, ...]] = []
        for i in range(len(win_names) - 2):
            g = tuple(win_names[i:i + 3])
            if g in base_grams:
                continue
            if any(freq.get(tok, 0) / total < RARE_FREQ for tok in g):
                novel.append(g)
        if novel:
            uniq = list(dict.fromkeys(novel))[:MAX_EVIDENCE]
            alerts.append({
                "kind": "novel-chain",
                "severity": "medium",
                "evidence": [
                    {"metric": "novel_3grams", "value": len(novel)},
                    {"metric": "examples", "value": " | ".join("→".join(g) for g in uniq)[:400]},
                ],
                "summary": f"{len(novel)} زنجیره‌ی ۳تاییِ تازه با عضوِ کمیاب در پنجره‌ی اخیر",
            })

    # ── ۳) egress-attempt ───────────────────────────────────────────────────
    recent = events[-300:]
    hits = []
    for e in recent:
        hay = (str(e.get("event_name", "")) + " " + str(e.get("summary", ""))).lower()
        if any(mk in hay for mk in EGRESS_MARKERS):
            hits.append(e)
    if hits:
        agents = sorted({str(h.get("agent_id", "?")) for h in hits})[:MAX_EVIDENCE]
        alerts.append({
            "kind": "egress-attempt",
            "severity": "high",
            "evidence": [
                {"metric": "egress_marker_events", "value": len(hits)},
                {"metric": "agents", "value": ", ".join(agents)},
            ],
            "summary": f"{len(hits)} رویداد با نشانه‌ی شبکه/egress (agents: {', '.join(agents)})",
        })

    return alerts


def _signature(alert: dict) -> str:
    src = json.dumps({"kind": alert["kind"], "evidence": alert["evidence"][:2]},
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]


def _load_cursor(path: Path) -> dict:
    try:
        if path.exists():
            d = json.loads(path.read_text("utf-8"))
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}


def _save_cursor(path: Path, cursor: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(cursor, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        pass


def _append_alerts(out_path: Path, alerts: list[dict]) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("a", encoding="utf-8") as fh:
        for a in alerts:
            fh.write(json.dumps(a, ensure_ascii=False) + "\n")
            n += 1
    return n


def run_once(
    events_path: Path | None = None,
    out_path: Path | None = None,
    cursor_path: Path | None = None,
) -> dict:
    """یک چرخه‌ی کامل: خواندن، تشخیص، dedup، نوشتن. هرگز raise نمی‌کند."""
    if not flag_on():
        return {"ran": False, "reason": "flag-off"}
    try:
        events_path = Path(events_path) if events_path else DEFAULT_EVENTS
        out_path = Path(out_path) if out_path else DEFAULT_OUT
        cursor_path = Path(cursor_path) if cursor_path else DEFAULT_CURSOR

        events = _tail_events(events_path, TAIL_N)
        if not events:
            return {"ran": False, "reason": "no-events"}

        raw_alerts = check_once(events)
        cursor = _load_cursor(cursor_path)
        now = datetime.now(timezone.utc)
        fresh: list[dict] = []
        for a in raw_alerts:
            sig = _signature(a)
            last = cursor.get(sig)
            if last:
                try:
                    last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                    if (now - last_dt).total_seconds() < ALERT_DEDUP_SECONDS:
                        continue
                except Exception:
                    pass
            cursor[sig] = _utc_now_iso()
            a.update({
                "schema": ALERT_SCHEMA,
                "alert_id": f"traj-{now.strftime('%Y%m%d%H%M%S')}-{sig}",
                "ts_utc": _utc_now_iso(),
            })
            fresh.append(a)

        written = _append_alerts(out_path, fresh) if fresh else 0
        _save_cursor(cursor_path, cursor)
        return {"ran": True, "alerts": written, "kinds": [a["kind"] for a in fresh]}
    except Exception as exc:
        return {"ran": False, "reason": f"error:{type(exc).__name__}"}


def self_test() -> dict:
    """تستِ دودِ آفلاین با داده‌ی ساختگی — بدونِ فلگ، بدونِ I/O خارج از tmp."""
    checks: dict[str, bool] = {}

    # baseline: ۱۲۰ دقیقه‌ی آرام (۵ رویداد/دقیقه از ۲ عامل)
    events: list[dict] = []
    t = 1_700_000_000.0
    for m in range(120):
        for k in range(5):
            events.append({"ts": t + m * 60 + k * 7,
                           "event_name": "heartbeat" if k % 2 else "task.completed",
                           "agent_id": f"organ-{k % 2}", "summary": ""})
    checks["calm_no_burst"] = not any(a["kind"] == "burst" for a in check_once(events))

    # burst: دقیقه‌ی آخر ۱۰۰ رویداد
    burst_events = events + [{"ts": t + 121 * 60 + i, "event_name": "task.completed",
                              "agent_id": "organ-9", "summary": ""} for i in range(100)]
    kinds = {a["kind"] for a in check_once(burst_events)}
    checks["burst_detected"] = "burst" in kinds

    # novel-chain: زنجیره‌ی تازه با عضوِ کمیاب
    novel_events = events + [
        {"ts": t + 122 * 60 + i, "event_name": nm, "agent_id": "organ-1", "summary": ""}
        for i, nm in enumerate(["x.rare.open", "y.rare.mid", "z.rare.close"] * 10)
    ]
    checks["novel_chain_detected"] = "novel-chain" in {a["kind"] for a in check_once(novel_events)}

    # egress marker
    eg_events = events + [{"ts": t + 123 * 60 + i, "event_name": "task.completed",
                           "agent_id": "organ-3", "summary": "fetch https://example.com"}
                          for i in range(3)]
    checks["egress_detected"] = "egress-attempt" in {a["kind"] for a in check_once(eg_events)}

    checks["ALL"] = all(checks.values())
    return checks


if __name__ == "__main__":
    if flag_on():
        print(json.dumps(run_once(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
