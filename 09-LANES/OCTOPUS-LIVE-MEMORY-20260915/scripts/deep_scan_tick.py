#!/usr/bin/env python3
"""deep_scan_tick — the organism's living memory of its own unfinished work.

Modes (all in one --tick run):
  probe_runtime   collect runtime facts (queue, breakers, fleet-jobs, units...)
  parse_mirror    OPTIONAL vault mirror: checklists, frontmatter, OPEN-WORK, status words
  prune           re-verify each open finding against its anchor -> lifecycle events
  grow            new findings (capped, deduped, anchor-mandatory) -> open events
  reconcile       vault<->runtime discrepancy classes, both sides quoted
  rank            U*R + C/5
  report          bounded delta -> reports/ + current-truth block (NOT auto-appended)
  dashboard       top active / top discrepancies / top owner-gated

Discipline (anti-noise-factory, per owner risk note):
  - every finding carries a verifiable anchor; candidates without one are quarantined
  - MAX_NEW_PER_TICK / MAX_PARSE_FILES / MAX_REPORT_LINES hard caps
  - findings-events.jsonl is append-only and never rewritten
  - re-runs are idempotent: an identical observation never creates a duplicate
  - lifecycle: open -> verified -> queued -> executed -> resolved | abandoned

Exit codes: 0 ok, 1 config/fatal, 2 partial (some collectors failed, still reported).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/ari/ofn/state/deep-scan")
OPS = Path("/home/ari/ofn/state/ops-agent/state")
CONFIG_PATH = ROOT / "config.json"

DEFAULTS = {
    "max_new_per_tick": 15,
    "max_parse_files": 400,
    "max_report_lines": 30,
    "mirror_dir": str(ROOT / "vault-mirror"),
    "mirror_max_age_hours": 24 * 14,  # older mirror -> data marked stale, still parsed
    "default_scores": {"U": 2, "R": 3, "C": 3},
    "rank_formula": "U*R + C/5",
}

TS = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# ------------------------------------------------------------------ io helpers
def load_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def append_event(ev: dict) -> None:
    ev = {"at": TS, **ev}
    with open(ROOT / "findings-events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def rank(scores: dict) -> float:
    return scores["U"] * scores["R"] + scores["C"] / 5.0


# ------------------------------------------------------------------ seed import
def import_seed(seed_path: Path, current: dict) -> int:
    data = load_json(seed_path)
    if not data:
        return 0
    known = set(current.get("findings", {}))
    n = 0
    for item in data.get("items", []):
        fid = item["id"]
        if fid in known:
            continue
        append_event({
            "finding_id": fid, "event": "open",
            "title": item["title"],
            "map_class": item.get("map_class", "UNKNOWN"),
            "schema_class": item.get("class", "OPEN_WORK"),
            "evidence": {
                "source_type": "runtime" if ":138:" in item["source"]["path"] or item["source"]["path"].startswith("138:") else "vault",
                "path": item["source"]["path"],
                "anchor": item["source"]["anchor"],
                "phrase": item.get("evidence_of_unfinished", "")[:200],
            },
            "scores": {"U": item.get("U", 2), "R": item.get("R", 3), "C": item.get("C", 3)},
            "needs_review": False,
            "seed": True,
        })
        n += 1
    return n


# ------------------------------------------------------------------ runtime probes
def probe_runtime(collector_errors: list) -> dict:
    """Read-only runtime collectors. Each returns (facts, candidates)."""
    facts = {"probed_at": TS, "candidates": []}

    def cand(fid, title, cls, path, anchor, phrase, U=2, R=3, C=3):
        facts["candidates"].append({
            "dedupe_key": f"{fid}",
            "finding_id": fid,
            "title": title, "map_class": cls,
            "evidence": {"source_type": "runtime", "path": path, "anchor": anchor, "phrase": phrase[:200]},
            "scores": {"U": U, "R": R, "C": C},
        })

    # 1. executed-but-not-retired canary requests (self-stale class)
    try:
        canary = {p.name for p in (OPS / "canary-requests").glob("*.json")}
        executed = {p.name for p in (OPS / "executed").glob("*.json")}
        superseded = {p.name for p in (OPS / "superseded-tasks").glob("*.json")}
        facts["queue"] = {"canary": sorted(canary), "executed": sorted(executed), "superseded": sorted(superseded)}
    except OSError as e:
        collector_errors.append(f"queue:{e}")

    # 2. breaker states via ops_agent import (read-only call)
    try:
        sys.path.insert(0, "/home/ari/ofn/state/ops-agent")
        import ops_agent as O  # noqa
        facts["breakers"] = {
            "B5": O.budget_allows("B5", "storage-cache"),
            "RY": O.budget_allows("RY", "ofn-agents"),
        }
        if facts["breakers"]["B5"][0] is False:
            cand("R-BREAKER-B5", f"B5 circuit breaker OPEN: {facts['breakers']['B5'][1]}",
                 "EXECUTOR", "138:budget_allows('B5')", "live probe",
                 f"budget_allows('B5') = {facts['breakers']['B5']}", U=3, R=3, C=4)
        if facts["breakers"]["RY"][0] is False and "CIRCUIT" in facts["breakers"]["RY"][1]:
            cand("R-BREAKER-RY", f"B8(RY) circuit breaker OPEN: {facts['breakers']['RY'][1]}",
                 "EXECUTOR", "138:budget_allows('RY')", "live probe",
                 f"budget_allows('RY') = {facts['breakers']['RY']}", U=5, R=4, C=4)
    except Exception as e:  # noqa
        collector_errors.append(f"breakers:{e}")

    # 3. fleet-jobs lifecycle histogram
    try:
        rows = [json.loads(l) for l in open("/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl") if l.strip()]
        hist = {}
        for r in rows:
            hist[r.get("state", "?")] = hist.get(r.get("state", "?"), 0) + 1
        facts["fleet_jobs"] = hist
        nonterm = sum(v for k, v in hist.items() if k not in ("CLOSED", "REJECTED"))
        if nonterm > 30:
            cand("R-FLEETJOBS-STUCK", f"fleet-jobs bus: {nonterm}/{len(rows)} rows non-terminal {hist}",
                 "EXECUTOR", "138:fleet-jobs/fleet_jobs.jsonl", "state histogram",
                 f"non-terminal={nonterm} of {len(rows)}", U=4, R=5, C=3)
    except OSError as e:
        collector_errors.append(f"fleet_jobs:{e}")

    # 4. failed units
    try:
        out = subprocess.run(["systemctl", "list-units", "--type=service", "--state=failed",
                              "--no-legend", "--no-pager"], capture_output=True, text=True, timeout=15)
        failed = [l.split()[0] for l in out.stdout.splitlines() if l.strip()]
        facts["failed_units"] = failed
        for unit in failed:
            cand(f"R-UNIT-FAILED-{unit}", f"systemd unit FAILED: {unit}", "INFRA",
                 "138:systemctl list-units --state=failed", unit, f"unit {unit} failed",
                 U=2, R=4, C=5)
    except Exception as e:  # noqa
        collector_errors.append(f"units:{e}")

    # 5. memory + tg-inbox + revenue counters
    try:
        facts["fleet_facts_rows"] = sum(1 for _ in open("/home/ari/ofn/state/fleet-memory/fleet_facts.jsonl"))
    except OSError:
        facts["fleet_facts_rows"] = None
    try:
        facts["tg_inbox_rows"] = sum(1 for _ in open("/home/ari/ofn/state/tg-inbox/tg-inbox.jsonl"))
    except OSError:
        facts["tg_inbox_rows"] = 0

    # 6. kill-switch markers (presence = resolved-halt condition worth knowing)
    facts["halt_markers"] = [str(p) for p in
                             (Path("/home/ari/ofn/state/autonomy/STOP-AUTONOMY"),
                              Path("/etc/octopus-ops-halt")) if p.exists()]
    return facts


# ------------------------------------------------------------------ vault mirror parsing
STATUS_WORDS = re.compile(r"\b(PENDING|NOT_RUN|NOT_STARTED|NOT_ATTEMPTED|PROPOSED|awaiting|status:\s*open)\b", re.I)
CHECKLIST_OPEN = re.compile(r"^\s*-\s+\[ \]")
FRONTMATTER = re.compile(r"^---\s*$")


def parse_mirror(cfg: dict, collector_errors: list) -> dict:
    mdir = Path(cfg["mirror_dir"])
    out = {"mirror": str(mdir), "available": False, "files_parsed": 0, "candidates": [],
           "checklist_open": 0, "frontmatter_open": 0, "status_word_hits": 0}
    if not mdir.is_dir():
        out["disposition"] = "SKIPPED_OPTIONAL_SOURCE_UNAVAILABLE"
        return out
    newest = 0.0
    files = []
    for p in mdir.rglob("*"):
        if p.suffix.lower() not in (".md", ".json"):
            continue
        if any(part in ("worktree", "sources", "__pycache__", ".git") for part in p.parts):
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        newest = max(newest, mtime)
        files.append(p)
    out["mirror_age_hours"] = round((time.time() - newest) / 3600, 1) if newest else None
    out["data_stale"] = bool(out["mirror_age_hours"] and out["mirror_age_hours"] > cfg["mirror_max_age_hours"])
    out["available"] = True
    files.sort(key=lambda p: -p.stat().st_mtime)

    def cand(fid, title, cls, path, anchor, phrase, U=2, R=3, C=3):
        out["candidates"].append({
            "dedupe_key": fid, "finding_id": fid, "title": title[:160], "map_class": cls,
            "evidence": {"source_type": "vault", "path": str(path), "anchor": anchor,
                         "phrase": phrase[:200]},
            "scores": {"U": U, "R": R, "C": C}, "needs_review": True,
        })

    for p in files[: cfg["max_parse_files"]]:
        out["files_parsed"] += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            collector_errors.append(f"mirror-read:{p}:{e}")
            continue
        rel = str(p.relative_to(mdir))
        # OPEN-WORK.json items
        if p.name == "OPEN-WORK.json":
            data = load_json(p)
            for item in (data or {}).get("items", []):
                if str(item.get("id", "")).startswith("OW-"):
                    cand(f"V-OW-{rel}-{item['id']}",
                         f"{item.get('title','?')[:120]}",
                         item.get("map_class", "UNKNOWN").split("/")[0],
                         rel, f"OPEN-WORK item {item['id']}",
                         str(item.get("evidence_of_unfinished", item.get("title", "")))[:160])
            continue
        lines = text.splitlines()
        in_fm = len(lines) > 0 and FRONTMATTER.match(lines[0] or "")
        if in_fm:
            for ln in lines[1:40]:
                if ln.strip() == "---":
                    break
                m = re.match(r"status:\s*(open|draft|planned|active)\s*$", ln.strip(), re.I)
                if m:
                    out["frontmatter_open"] += 1
                    cand(f"V-FM-{rel}", f"frontmatter status={m.group(1)}: {rel}",
                         "OBSIDIAN", rel, "frontmatter status", f"status: {m.group(1)}")
                    break
        for i, ln in enumerate(lines):
            if CHECKLIST_OPEN.match(ln):
                out["checklist_open"] += 1
                # aggregate per-file to avoid 1-finding-per-bullet noise
                cand(f"V-CHK-{rel}", f"unticked checklist bullets in {rel} (first: {ln.strip()[:60]})",
                     "OPEN_WORK", rel, f"line {i+1}: {ln.strip()[:60]}", ln.strip()[:120])
                break  # one finding per file is enough; count continues below
        cnt = sum(1 for ln in lines if CHECKLIST_OPEN.match(ln))
        if cnt:
            for c in out["candidates"]:
                if c["dedupe_key"] == f"V-CHK-{rel}":
                    c["title"] = f"{cnt} unticked checklist bullets in {rel}"
        if STATUS_WORDS.search(text) and not CHECKLIST_OPEN.search(text):
            m = STATUS_WORDS.search(text)
            out["status_word_hits"] += 1
            cand(f"V-SW-{rel}", f"status-word {m.group(1)} in {rel}", "OPEN_WORK",
                 rel, m.group(0), m.group(0)[:120])
    # dedupe candidates within this tick by key
    seen = {}
    for c in out["candidates"]:
        seen.setdefault(c["dedupe_key"], c)
    out["candidates"] = list(seen.values())
    return out


def normalize_vault_path(raw: str, mirror: str) -> Path:
    """Map a vault evidence path (laptop or mirror form) onto the mirror tree."""
    p = str(raw).replace("\\", "/")
    for prefix in ("f:/backup/", "/f/backup/", "f:backup/"):
        if p.lower().startswith(prefix):
            p = p[len(prefix):]
            break
    p = p.lstrip("/")
    return Path(mirror) / p


# ------------------------------------------------------------------ lifecycle engine
def rebuild_current() -> dict:
    """Derive current state from the append-only event log."""
    findings = {}
    order = {"open": 0, "verified": 1, "queued": 2, "executed": 3, "resolved": 4, "abandoned": 5}
    terminal = {"resolved", "abandoned"}
    events_path = ROOT / "findings-events.jsonl"
    if not events_path.exists():
        return {"generated_at": TS, "findings": {}}
    for line in open(events_path, encoding="utf-8"):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        fid = ev.get("finding_id")
        if not fid:
            continue
        f = findings.setdefault(fid, {"finding_id": fid, "state": None, "history": []})
        f["history"].append({"event": ev.get("event"), "at": ev.get("at")})
        e = ev.get("event")
        if e in order:
            cur = f["state"]
            if cur in terminal:
                continue  # terminal states are sticky unless explicitly reopened
            if cur is None or order[e] >= order[cur]:
                f["state"] = e
        for k in ("title", "map_class", "schema_class", "evidence", "scores", "needs_review"):
            if k in ev:
                f[k] = ev[k]
    for f in findings.values():
        f["rank"] = rank(f.get("scores", DEFAULTS["default_scores"]))
    return {"generated_at": TS, "findings": findings}


def request_refs() -> dict:
    """Map finding-tag -> request file for lifecycle promotion (evidence graph)."""
    refs = {}
    for d in ("canary-requests", "executed", "superseded-tasks"):
        p = OPS / d
        if not p.is_dir():
            continue
        for f in p.glob("*.json"):
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in re.finditer(r"\[F-[A-Z0-9-]+\]", text):
                refs.setdefault(m.group(0)[1:-1], []).append(f"{d}/{f.name}")
    return refs


# ------------------------------------------------------------------ tick
def tick() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    cfg = {**DEFAULTS, **(load_json(CONFIG_PATH) or {})}
    collector_errors: list = []

    current = rebuild_current()
    index_open_before = {fid for fid, f in current["findings"].items() if f["state"] in ("open", "verified", "queued")}

    rt = probe_runtime(collector_errors)
    mir = parse_mirror(cfg, collector_errors)

    # ---- prune / verify runtime findings against fresh probes
    pruned = []
    rt_flat = json.dumps(rt, ensure_ascii=False)
    for fid, f in list(current["findings"].items()):
        if f["state"] not in ("open", "verified"):
            continue
        ev = f.get("evidence", {})
        if ev.get("source_type") == "runtime":
            key = {"R-BREAKER-B5": ("B5", True), "R-BREAKER-RY": ("RY", True),
                   "R-FLEETJOBS-STUCK": ("fleet_jobs", True)}.get(fid)
            if key:
                fact_now = json.dumps((rt.get("breakers", {}) if key[0] in ("B5", "RY") else rt.get("fleet_jobs")), ensure_ascii=False)
                cleared = (key[0] == "B5" and rt["breakers"]["B5"][0] is True) or \
                          (key[0] == "RY" and rt["breakers"]["RY"][0] is True) or \
                          (key[0] == "fleet_jobs" and sum(v for k, v in rt["fleet_jobs"].items()
                                                           if k not in ("CLOSED", "REJECTED")) <= 30)
                if cleared:
                    append_event({"finding_id": fid, "event": "resolved",
                                  "why": f"runtime condition cleared at {TS}",
                                  "evidence": {"source_type": "runtime", "path": "138:probe", "anchor": key[0], "phrase": fact_now[:160]}})
                    pruned.append(fid)
                elif f["state"] == "open":
                    append_event({"finding_id": fid, "event": "verified",
                                  "why": "condition re-observed this tick",
                                  "evidence": {"source_type": "runtime", "path": "138:probe", "anchor": key[0], "phrase": fact_now[:160]}})
                    pruned.append(fid)
        elif ev.get("source_type") == "vault" and mir["available"]:
            src = normalize_vault_path(ev.get("path", ""), mir["mirror"])
            if not src.exists():
                if f["state"] == "open":
                    append_event({"finding_id": fid, "event": "verified",
                                  "why": "SOURCE_ABSENT in mirror (moved/removed upstream)",
                                  "evidence": {**ev, "checked_at": TS}})
                    pruned.append(fid)
                continue
            try:
                text = src.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            anchor = ev.get("anchor", "")
            am = re.match(r"line (\d+): (.*)", anchor)
            if am:
                ln = text.splitlines()
                i = int(am.group(1)) - 1
                now_line = ln[i].strip() if 0 <= i < len(ln) else ""
                was_open = "[ ]" in am.group(2)
                now_open = "[ ]" in now_line
                if was_open and not now_open and now_line and f["state"] == "open":
                    append_event({"finding_id": fid, "event": "resolved",
                                  "why": f"checklist bullet now: {now_line[:60]}",
                                  "evidence": {**ev, "phrase": now_line[:120], "checked_at": TS, "sha256": sha256_file(src)}})
                    pruned.append(fid)

    # ---- request-reference promotion (evidence graph: finding tag in request files)
    refs = request_refs()
    promoted = []
    for fid, reqs in refs.items():
        f = current["findings"].get(fid)
        if not f or f["state"] not in ("open", "verified"):
            continue
        if any(r.startswith("executed/") for r in reqs):
            append_event({"finding_id": fid, "event": "executed",
                          "why": "referencing canary request is in executed/",
                          "evidence": {"request_refs": reqs}})
            promoted.append((fid, "executed"))
        elif any(r.startswith("canary-requests/") for r in reqs):
            append_event({"finding_id": fid, "event": "queued",
                          "why": "referencing canary request queued",
                          "evidence": {"request_refs": reqs}})
            promoted.append((fid, "queued"))

    # ---- grow (capped, deduped, anchor-mandatory)
    existing_keys = set(current["findings"])
    grown = []
    for c in rt["candidates"] + mir["candidates"]:
        if len(grown) >= cfg["max_new_per_tick"]:
            break
        if not c.get("evidence", {}).get("anchor"):
            append_event({"finding_id": c.get("finding_id", "?"), "event": "quarantined",
                          "why": "candidate without anchor", "title": c.get("title", "")[:120]})
            continue
        if c["dedupe_key"] in existing_keys:
            continue
        append_event({"finding_id": c["finding_id"], "event": "open",
                      "title": c["title"], "map_class": c.get("map_class", "UNKNOWN"),
                      "evidence": c["evidence"], "scores": c.get("scores", DEFAULTS["default_scores"]),
                      "needs_review": c.get("needs_review", True)})
        grown.append(c["finding_id"])
        existing_keys.add(c["dedupe_key"])

    # ---- rebuild + rank + dashboard
    current = rebuild_current()
    findings = current["findings"]
    active = [f for f in findings.values() if f["state"] in ("open", "verified", "queued", "executed")]
    active.sort(key=lambda f: -f["rank"])

    discrepancies = []
    if not mir["available"]:
        discrepancies.append({"class": "OPTIONAL_SOURCE_UNAVAILABLE",
                              "detail": f"vault mirror absent at {mir['mirror']} — vault-side findings not re-verified this tick"})
    if mir.get("data_stale"):
        discrepancies.append({"class": "MIRROR_DATA_STALE",
                              "detail": f"mirror newest file age {mir['mirror_age_hours']}h exceeds {cfg['mirror_max_age_hours']}h"})
    # runtime-vs-docs heuristics (bounded, both sides named)
    if rt.get("tg_inbox_rows") == 0:
        discrepancies.append({"class": "DOCS_CLAIM_RUNTIME_IDLE",
                              "detail": "tg-inbox 0 rows: owner-dialogue chain built (docs) but carries no traffic (runtime)"})

    owner_gated = [f for f in active if f["state"] == "open"
                   and re.search(r"owner|مالک|decision|رأی|vote|GO-", f.get("title", ""), re.I)][:10]

    dashboard = {
        "generated_at": TS, "rank_formula": cfg["rank_formula"],
        "counts": {"total_findings": len(findings),
                   "active": len(active),
                   "by_state": {s: sum(1 for f in findings.values() if f["state"] == s)
                                for s in ("open", "verified", "queued", "executed", "resolved", "abandoned", "quarantined")}},
        "top_active": [{"id": f["finding_id"], "rank": f["rank"], "state": f["state"],
                        "title": f.get("title", "")[:140], "class": f.get("map_class")} for f in active[:10]],
        "dangerous_discrepancies": discrepancies[:10],
        "owner_gated_top": [{"id": f["finding_id"], "title": f.get("title", "")[:140]} for f in owner_gated],
        "runtime_facts": {"breakers": rt.get("breakers"), "fleet_jobs": rt.get("fleet_jobs"),
                          "failed_units": rt.get("failed_units"), "fleet_facts_rows": rt.get("fleet_facts_rows"),
                          "tg_inbox_rows": rt.get("tg_inbox_rows"), "halt_markers": rt.get("halt_markers")},
        "mirror": {k: mir.get(k) for k in ("available", "files_parsed", "checklist_open",
                                           "frontmatter_open", "status_word_hits", "mirror_age_hours", "data_stale")},
        "collector_errors": collector_errors,
    }
    (ROOT / "DASHBOARD.json").write_text(json.dumps(dashboard, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "findings-current.json").write_text(json.dumps(current, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---- bounded delta report + CURRENT-TRUTH-ready block (never auto-appended)
    delta = {
        "tick_at": TS,
        "resolved_or_verified": pruned[:cfg["max_report_lines"]],
        "promoted": [{"id": i, "to": s} for i, s in promoted][:cfg["max_report_lines"]],
        "new": grown[:cfg["max_report_lines"]],
        "new_capped_out": max(0, len(rt["candidates"]) + len(mir["candidates"]) - cfg["max_new_per_tick"]),
        "collector_errors": collector_errors,
    }
    rp = ROOT / "reports" / f"deep-scan-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    rp.write_text(json.dumps(delta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [f"> 🧠 **deep-scan-tick {TS}** — active {dashboard['counts']['active']}/{dashboard['counts']['total_findings']}"
             f" · new {len(delta['new'])} (cap {cfg['max_new_per_tick']}) · resolved/verified {len(delta['resolved_or_verified'])}"
             f" · promoted {len(delta['promoted'])}"
             f" · mirror {'parsed ' + str(mir.get('files_parsed')) + ' files' if mir['available'] else 'SKIPPED_OPTIONAL_SOURCE_UNAVAILABLE'}"
             + (f" · ⚠️ collectors failed: {len(collector_errors)}" if collector_errors else "")]
    (ROOT / "reports" / "current-truth-delta-block.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"tick": TS, "new": len(grown), "pruned": len(pruned), "promoted": len(promoted),
                      "active": dashboard["counts"]["active"], "errors": collector_errors}, ensure_ascii=False))
    return 2 if collector_errors else 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: deep_scan_tick.py --tick | --import-seed <path>")
        return 1
    if sys.argv[1] == "--import-seed":
        ROOT.mkdir(parents=True, exist_ok=True)
        current = rebuild_current()
        n = import_seed(Path(sys.argv[2]), current)
        print(json.dumps({"seed_imported": n}))
        return 0
    if sys.argv[1] == "--tick":
        return tick()
    print("unknown mode")
    return 1


if __name__ == "__main__":
    sys.exit(main())
