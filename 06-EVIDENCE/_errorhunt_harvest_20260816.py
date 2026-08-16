#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ERRORHUNT harvest — read-only, 7-day window ending 2026-08-16.

Writes:
  06-EVIDENCE/ERRORHUNT-RAW-2026-08-16.json
  06-EVIDENCE/ERRORHUNT-RAW-2026-08-16.md
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

VAULT = Path(r"F:\backup")
CUTOFF = datetime(2026, 8, 9, 0, 0, 0)  # local naive; we also accept ISO Z
CUTOFF_ISO = "2026-08-09"
NOW = datetime.now().replace(microsecond=0)
OUT_JSON = VAULT / "06-EVIDENCE" / "ERRORHUNT-RAW-2026-08-16.json"
OUT_MD = VAULT / "06-EVIDENCE" / "ERRORHUNT-RAW-2026-08-16.md"

# Secret-ish substrings to redact from samples (names only, never values).
REDACT = re.compile(r"(ghp_|github_pat_|sk-|BOT_TOKEN|api[_-]?key)[=:]?\s*\S+", re.I)


def in_window_str(s: str) -> bool:
    if not s:
        return False
    s = s.strip()
    # Accept 2026-08-09..., 2026-08-09T..., epoch-ish skip
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", s)
    if not m:
        return False
    return m.group(1) >= CUTOFF_ISO


def sample(text: str, n: int = 180) -> str:
    t = " ".join((text or "").split())
    t = REDACT.sub("<redacted>", t)
    return t[:n]


def add(events, source, kind, ts, text, extra=None):
    rec = {
        "ts": ts or "",
        "source": source,
        "kind": kind,
        "text": sample(text),
    }
    if extra:
        rec["extra"] = extra
    events.append(rec)


def parse_ts_prefix(line: str) -> str:
    m = re.match(r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})", line)
    return m.group(1) if m else ""


# ---------- text logs ----------
def harvest_text_log(path: Path, events, source, patterns):
    """patterns: list of (regex, kind). First match wins."""
    if not path.exists():
        add(events, source, "missing-source", "", f"file missing: {path}")
        return
    compiled = [(re.compile(p, re.I), k) for p, k in patterns]
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                ts = parse_ts_prefix(line)
                if ts and not in_window_str(ts):
                    continue
                if not ts:
                    # keep if file is small-window (daemon logs are all 08-16)
                    # skip undated unless the file mtime is in window — handled by caller
                    pass
                for rx, kind in compiled:
                    if rx.search(line):
                        add(events, source, kind, ts, line)
                        break
    except OSError as e:
        add(events, source, "read-error", "", str(e))


def harvest_jsonl(path: Path, events, source, classify):
    if not path.exists():
        add(events, source, "missing-source", "", f"file missing: {path}")
        return
    n_bad = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    n_bad += 1
                    continue
                ts = str(
                    obj.get("ts")
                    or obj.get("timestamp")
                    or obj.get("time")
                    or obj.get("created")
                    or ""
                )
                if ts and not in_window_str(ts):
                    continue
                kind, text = classify(obj)
                if kind:
                    add(events, source, kind, ts, text)
        if n_bad:
            add(events, source, "jsonl-decode-fail", "", f"{n_bad} bad json lines")
    except OSError as e:
        add(events, source, "read-error", "", str(e))


def harvest_governor_md(path: Path, events):
    if not path.exists():
        return
    cur_ts = ""
    buf = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", line)
            if m:
                if cur_ts and in_window_str(cur_ts) and buf:
                    text = " ".join(buf)
                    if re.search(r"خطا|error|fail|⚠️|🔴|crash", text, re.I):
                        add(events, "governor-alerts.md", "governor-alert", cur_ts, text)
                cur_ts = m.group(1)
                buf = []
            else:
                buf.append(line.strip())
        if cur_ts and in_window_str(cur_ts) and buf:
            text = " ".join(buf)
            if re.search(r"خطا|error|fail|⚠️|🔴|crash", text, re.I):
                add(events, "governor-alerts.md", "governor-alert", cur_ts, text)


def harvest_sqlite_dashboard(events):
    db = VAULT / "4d_system" / "outputs" / "4d_experiments.db"
    if not db.exists():
        add(events, "4d_experiments.db", "missing-source", "", "db missing")
        return
    uri = f"file:{db.as_posix()}?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True)
        con.execute("PRAGMA query_only=ON")
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        extra = {"tables": tables}
        if "dashboard_events" in tables:
            cols = [r[1] for r in con.execute("PRAGMA table_info(dashboard_events)")]
            extra["dashboard_cols"] = cols
            # status=error and event_name containing error/readback
            q = """
            SELECT timestamp, event_name, status, message
            FROM dashboard_events
            WHERE timestamp >= '2026-08-09'
              AND (
                lower(coalesce(status,'')) IN ('error','fail','failed','blocked')
                OR lower(coalesce(event_name,'')) LIKE '%error%'
                OR lower(coalesce(message,'')) LIKE '%error%'
                OR lower(coalesce(message,'')) LIKE '%یافت نشد%'
                OR event_name = 'memory.readback'
              )
            ORDER BY timestamp
            """
            try:
                rows = con.execute(q).fetchall()
            except sqlite3.OperationalError:
                # column names may differ — inspect
                add(events, "dashboard_events", "schema-mismatch", "", str(cols), extra)
                rows = []
            for ts, name, status, msg in rows:
                kind = f"dash:{name}:{status or '?'}"
                add(events, "dashboard_events", kind, str(ts or ""), str(msg or name))
            # aggregates
            try:
                agg = con.execute(
                    """SELECT event_name, status, COUNT(*)
                       FROM dashboard_events
                       WHERE timestamp >= '2026-08-09'
                       GROUP BY 1,2
                       ORDER BY 3 DESC LIMIT 40"""
                ).fetchall()
                extra["agg_top"] = [{"event": a, "status": b, "n": c} for a, b, c in agg]
            except sqlite3.OperationalError:
                pass
            try:
                rb = con.execute(
                    """SELECT
                         SUM(CASE WHEN timestamp < '2026-08-16T05:00' THEN 1 ELSE 0 END),
                         SUM(CASE WHEN timestamp < '2026-08-16T05:00'
                                  AND status!='ok' THEN 1 ELSE 0 END),
                         SUM(CASE WHEN timestamp >= '2026-08-16T05:00' THEN 1 ELSE 0 END),
                         SUM(CASE WHEN timestamp >= '2026-08-16T05:00'
                                  AND status='ok' THEN 1 ELSE 0 END)
                       FROM dashboard_events
                       WHERE event_name='memory.readback'"""
                ).fetchone()
                extra["readback_split"] = {
                    "pre_0500_n": rb[0], "pre_0500_fail": rb[1],
                    "post_0500_n": rb[2], "post_0500_ok": rb[3],
                }
            except sqlite3.OperationalError:
                pass
        if "hypotheses" in tables:
            extra["hyp_status"] = [
                {"status": s, "n": n}
                for s, n in con.execute(
                    "SELECT status, COUNT(*) FROM hypotheses GROUP BY 1").fetchall()
            ]
        add(events, "4d_experiments.db", "db-summary", NOW.isoformat(timespec="seconds"),
            "sqlite summary", extra)
        con.close()
    except Exception as e:  # noqa: BLE001
        add(events, "4d_experiments.db", "db-error", "", f"{type(e).__name__}: {e}")


def harvest_flaky(events):
    d = VAULT / "_ops" / "tests" / "_flaky"
    if not d.exists():
        add(events, "_flaky", "missing-source", "", "dir missing")
        return
    n = 0
    recent = []
    for p in d.glob("*.txt"):
        n += 1
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        if mtime >= CUTOFF:
            recent.append((mtime.isoformat(timespec="seconds"), p.name, p.stat().st_size))
            add(events, "_flaky", "flaky-file", mtime.isoformat(timespec="seconds"),
                p.name)
    add(events, "_flaky", "flaky-summary", NOW.isoformat(timespec="seconds"),
        f"total_files={n} in_window={len(recent)}")


def harvest_doctor(events):
    base = VAULT / "OCTOPUS-DOCTOR" / "90-_meta" / "state"

    def cls_outbox(obj):
        st = str(obj.get("status") or obj.get("state") or obj.get("ok") or "")
        if str(st).lower() in {"error", "fail", "failed", "rejected", "false", "0"}:
            return "outbox-rejected", json.dumps(obj, ensure_ascii=False)[:180]
        err = obj.get("error") or obj.get("err")
        if err:
            return "outbox-error", str(err)
        return None, ""

    def cls_inbox(obj):
        st = str(obj.get("status") or obj.get("verdict") or "")
        if "reject" in st.lower() or "error" in st.lower() or "ignore" in st.lower():
            return "inbox-rejected", json.dumps(obj, ensure_ascii=False)[:180]
        return None, ""

    harvest_jsonl(base / "tg-outbox.jsonl", events, "doctor-tg-outbox", cls_outbox)
    harvest_jsonl(base / "tg-inbox.jsonl", events, "doctor-tg-inbox", cls_inbox)
    vitals = base / "doctor-vitals.json"
    if vitals.exists():
        try:
            v = json.loads(vitals.read_text(encoding="utf-8"))
            add(events, "doctor-vitals", "vitals", "", json.dumps(v, ensure_ascii=False)[:300])
        except Exception as e:  # noqa: BLE001
            add(events, "doctor-vitals", "read-error", "", str(e))


def harvest_pep(events):
    def cls(obj):
        verdict = str(obj.get("verdict") or obj.get("decision") or obj.get("action") or "")
        if verdict.lower() in {"deny", "reject", "error"} or "deny" in json.dumps(obj).lower():
            return "pep-deny", json.dumps(obj, ensure_ascii=False)[:200]
        return "pep-event", json.dumps(obj, ensure_ascii=False)[:120]
    harvest_jsonl(VAULT / "_ops" / "state" / "telegram-pep-shadow.jsonl",
                  events, "telegram-pep-shadow", cls)


def harvest_organ_gate(events):
    def cls(obj):
        if obj.get("allow") is False or obj.get("ok") is False:
            return "organ-denied", json.dumps(obj, ensure_ascii=False)[:200]
        return None, ""
    harvest_jsonl(VAULT / "_ops" / "budget" / "organ-gate-log.jsonl",
                  events, "organ-gate-log", cls)


def harvest_paid_timeout(events):
    def cls(obj):
        return "paid-timeout-alert", json.dumps(obj, ensure_ascii=False)[:200]
    harvest_jsonl(VAULT / "_ops" / "state" / "paid-timeout-alerts.jsonl",
                  events, "paid-timeout-alerts", cls)


def harvest_events_jsonl(events):
    def cls(obj):
        st = str(obj.get("status") or obj.get("level") or obj.get("severity") or "")
        name = str(obj.get("event") or obj.get("type") or obj.get("kind") or "")
        blob = json.dumps(obj, ensure_ascii=False)
        if re.search(r"error|fail|wedge|halt|crash", st + name + blob[:200], re.I):
            return f"ops-event:{name or st or 'error'}", blob[:200]
        return None, ""
    harvest_jsonl(VAULT / "_ops" / "state" / "events.jsonl", events, "events.jsonl", cls)


def harvest_tg_send(events):
    def cls(obj):
        ok = obj.get("ok")
        err = obj.get("error") or obj.get("description") or obj.get("err")
        if ok is False or err:
            return "tg-send-fail", json.dumps(obj, ensure_ascii=False)[:200]
        return None, ""
    harvest_jsonl(VAULT / "_ops" / "state" / "tg-send-log.jsonl",
                  events, "tg-send-log", cls)


def harvest_watchdog_json(events):
    p = VAULT / "_ops" / "state" / "cortex-watchdog.json"
    if p.exists():
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            add(events, "cortex-watchdog.json", "snapshot",
                datetime.fromtimestamp(obj.get("last_check", 0)).isoformat(timespec="seconds")
                if obj.get("last_check") else "",
                json.dumps(obj))
        except Exception as e:  # noqa: BLE001
            add(events, "cortex-watchdog.json", "read-error", "", str(e))
    st = VAULT / "4d_system" / "outputs" / "daemon_state.json"
    if st.exists():
        try:
            obj = json.loads(st.read_text(encoding="utf-8"))
            add(events, "daemon_state.json", "snapshot",
                str(obj.get("last_tick_at") or obj.get("resumed_at") or ""),
                json.dumps({k: obj.get(k) for k in
                            ("pid", "errors_this_run", "paused", "generation",
                             "kernel", "stopped_at", "resumed_at")},
                           ensure_ascii=False))
        except Exception as e:  # noqa: BLE001
            add(events, "daemon_state.json", "read-error", "", str(e))


def harvest_poisoning(events):
    p = VAULT / "06-EVIDENCE" / "POISONING-WATCH-4d.md"
    if not p.exists():
        add(events, "POISONING-WATCH", "missing-source", "", "file missing")
        return
    text = p.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n## ", text)
    for b in blocks:
        m = re.match(r"(\d{4}-\d{2}-\d{2}T[^\n]+)", b)
        if not m:
            continue
        ts = m.group(1)
        if not in_window_str(ts):
            continue
        verd = ""
        vm = re.search(r"حکم:\s*(.+)", b)
        if vm:
            verd = vm.group(1).strip()
        kind = "poisoning-ok" if "🟢" in verd else "poisoning-alert"
        add(events, "POISONING-WATCH", kind, ts, verd + " " + sample(b, 240))


def harvest_scheduled_tasks_note(events):
    # We cannot always query schtasks here; record file evidence of last watch runs.
    for name in ("watchdog.log", "live-watchdog-log.txt", "miniapp-watchdog-log.txt",
                 "tg-center-watchdog-log.txt", "watchdog-log.txt"):
        p = VAULT / "_ops" / "state" / name
        if p.exists():
            add(events, name, "mtime",
                datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                f"size={p.stat().st_size}")


def cluster(events):
    buckets = defaultdict(list)
    for e in events:
        key = f"{e['source']}::{e['kind']}"
        buckets[key].append(e)
    out = []
    for key, items in buckets.items():
        tss = [i["ts"] for i in items if i.get("ts")]
        tss.sort()
        out.append({
            "key": key,
            "count": len(items),
            "first": tss[0] if tss else "",
            "last": tss[-1] if tss else "",
            "sample": items[0]["text"],
        })
    out.sort(key=lambda x: -x["count"])
    return out


def write_md(events, clusters, notes):
    lines = [
        "---",
        "type: evidence",
        "session: ERRORHUNT-RAW",
        "created: 2026-08-16",
        "window: 2026-08-09 .. 2026-08-16",
        "mode: read-only harvest",
        "---",
        "",
        "# ERRORHUNT RAW — 2026-08-16",
        "",
        f"- harvested_at: {NOW.isoformat(timespec='seconds')} local",
        f"- window_start: {CUTOFF_ISO}",
        f"- event_rows: {len(events)}",
        f"- cluster_keys: {len(clusters)}",
        "",
        "## Notes / coverage",
        "",
    ]
    for n in notes:
        lines.append(f"- {n}")
    lines += ["", "## Clusters (source::kind)", "",
              "| count | first | last | key | sample |",
              "|---:|---|---|---|---|"]
    for c in clusters:
        samp = c["sample"].replace("|", "/")[:120]
        lines.append(f"| {c['count']} | {c['first']} | {c['last']} | `{c['key']}` | {samp} |")
    lines += ["", "## JSON", "",
              "Companion: `ERRORHUNT-RAW-2026-08-16.json` (full rows, redacted samples).",
              ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    events = []
    notes = []

    daemon_pat = [
        (r"readback failed|یافت نشد", "readback-fail"),
        (r"memory\.readback.*\[error", "readback-fail"),
        (r"memory\.readback.*\[ok", "readback-ok"),
        (r"REFERENCE_DIR", "reference-dir-warn"),
        (r"unauthenticated requests to the HF Hub", "hf-unauth-warn"),
        (r"HTTP/1\.1 404", "hf-404"),
        (r"Relevance scores must be between 0 and 1", "rag-score-warn"),
        (r"\bERROR\b", "daemon-error"),
        (r"\bWARNING\b", "daemon-warning"),
        (r"task\.blocked", "task-blocked"),
        (r"integrity", "kernel-integrity"),
        (r"not-configured", "notify-not-configured"),
    ]
    for name in ("daemon-launch.err.log", "daemon-launch2.err.log", "daemon-launch3.err.log"):
        harvest_text_log(VAULT / "4d_system" / "outputs" / name, events, name, daemon_pat)

    harvest_text_log(VAULT / "_ops" / "state" / "watchdog-log.txt", events, "watchdog-log.txt", [
        (r"REVIVE", "cortex-revive"),
        (r"STOP-CORTEX", "stop-cortex"),
        (r"HALT-ALL|architect-STOP", "global-halt"),
        (r"dead \(miss", "cortex-dead-miss"),
        (r"Force", "cortex-force"),
        (r"wedge", "cortex-wedge"),
        (r"launched RUN-CORTEX", "cortex-launch"),
    ])
    harvest_text_log(VAULT / "_ops" / "state" / "miniapp-watchdog-log.txt", events,
                     "miniapp-watchdog-log.txt", [
        (r"alive=False", "tunnel-restart"),
        (r"error|fail", "miniapp-error"),
    ])
    harvest_text_log(VAULT / "_ops" / "state" / "live-watchdog-log.txt", events,
                     "live-watchdog-log.txt", [
        (r"HALT-ALL|architect-STOP", "live-halt-no-revive"),
        (r"down", "live-down-launch"),
        (r"error|fail", "live-error"),
    ])
    harvest_text_log(VAULT / "_ops" / "state" / "tg-center-watchdog-log.txt", events,
                     "tg-center-watchdog-log.txt", [
        (r"HUNG", "center-hung"),
        (r"STOP-TG-CENTER", "stop-tg-center"),
        (r"HALT-ALL|architect-STOP", "center-halt-no-revive"),
        (r"down", "center-down-launch"),
        (r"orphan", "center-orphan-reap"),
        (r"error|fail", "center-error"),
    ])
    harvest_text_log(VAULT / "_ops" / "state" / "watchdog.log", events, "watchdog.log", [
        (r"down|dead|REVIVE|HALT|error|fail", "organism-watchdog-event"),
    ])

    harvest_governor_md(VAULT / "_ops" / "governor" / "governor-alerts.md", events)
    harvest_sqlite_dashboard(events)
    harvest_flaky(events)
    harvest_doctor(events)
    harvest_pep(events)
    harvest_organ_gate(events)
    harvest_paid_timeout(events)
    harvest_events_jsonl(events)
    harvest_tg_send(events)
    harvest_watchdog_json(events)
    harvest_poisoning(events)
    harvest_scheduled_tasks_note(events)

    notes.append("DBs opened uri mode=ro + PRAGMA query_only")
    notes.append("secrets redacted from samples (token prefixes only)")
    notes.append("daemon-launch*.err.log exist only for 2026-08-16 boots (gen1/2/3)")
    notes.append("_flaky: files whose mtime is inside window, not necessarily new flakes")

    clusters = cluster(events)
    payload = {
        "harvested_at": NOW.isoformat(timespec="seconds"),
        "window_start": CUTOFF_ISO,
        "n_events": len(events),
        "n_clusters": len(clusters),
        "clusters": clusters,
        "events": events,
        "notes": notes,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(events, clusters, notes)
    print(f"events={len(events)} clusters={len(clusters)}")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    for c in clusters[:25]:
        print(f"{c['count']:6d}  {c['key'][:80]}  {c['first']} → {c['last']}")


if __name__ == "__main__":
    main()
