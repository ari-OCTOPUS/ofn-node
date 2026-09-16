#!/usr/bin/env python3
"""memtest_live.py - three-axis live memory health test on a FIXTURE COPY.

Axes (per deep-walk D1/D2 bottlenecks):
  signal - word richness of the last N records exposed to decisions
  use    - the decisions_changed>0 equivalent on the REAL schema:
             spine.db    : decided / proposal-issued funnel
             organism.db : lessons/episodes ratio + future_use_count>0 receipts
  vault  - FTS5 health + literal 'spine' match count (C-DW29-02 diagnosis)

Safety: source DB is opened mode=ro and copied via the SQLite Online Backup
API into --out. No write ever touches the source. Exit: 0 healthy, 2
bottleneck confirmed, 1 error. Report shape mirrors memtest_live_sandbox_report.json.
"""
import argparse, hashlib, json, sqlite3, sys, time
from pathlib import Path

FTS_SHADOW = ("_fts_config", "_fts_content", "_fts_data", "_fts_docsize", "_fts_idx", "_fts")

def backup_copy(src: str, dst: Path) -> float:
    """Online backup: page-batched (lock released between steps), restart-safe.

    pages=64/sleep=0.2 per the board profile (SD/eMMC + busy writer): the source
    read-lock is held only during each 64-page step; concurrent writers force a
    transparent restart of the copy rather than a corrupt image."""
    t0 = time.time()
    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=10)
    source.execute("pragma busy_timeout=5000")
    target = sqlite3.connect(str(dst))
    with target:
        source.backup(target, pages=64, sleep=0.2)
    source.close()
    # post-copy, non-negotiable: the fixture must be well-formed AND queryable
    chk = target.execute("pragma integrity_check").fetchone()[0]
    pages = target.execute("pragma page_count").fetchone()[0]
    target.close()
    if chk != "ok" or pages <= 0:
        raise RuntimeError(f"fixture failed hardening: integrity_check={chk!r} page_count={pages}")
    return round(time.time() - t0, 3)

def logical_tables(con):
    rows = [r[0] for r in con.execute(
        "select name from sqlite_master where type='table'")]
    return [t for t in rows
            if not t.startswith("sqlite_")
            and not any(t.endswith(s) or t == s[:-1] for s in FTS_SHADOW)]

def words(text: str):
    return [w for w in str(text or "").split() if w.strip()]

def axis_signal(con, mode, max_sample):
    picks = {
        "memory":  [("memory", "content")],
        "spine":   [("events", None)],        # text = event_type + subject (SpineReadStore mapping)
        "organism": [("utterances", None), ("inner_speech", None), ("episodes", None)],
    }
    for table, col in picks.get(mode, []):
        if table not in logical_tables(con):
            continue
        cols = [r[1] for r in con.execute(f'pragma table_info("{table}")')]
        if mode == "spine":  # reconstruct the live read-loop projection
            text_col = "(event_type+subject)"
            proj = con.execute(
                "select event_type, subject from events order by rowid desc limit ?",
                (max_sample,)).fetchall()
            rows = [f"{et} {su or ''}".strip() for et, su in proj]
        else:
            text_col = col or next((c for c in ("text", "content", "fact", "statement",
                                                "body_json", "payload_json") if c in cols), None)
            if text_col is None:
                continue
            rows = [r[0] for r in con.execute(
                f'select "{text_col}" from "{table}" order by rowid desc limit {max_sample}')]
        n = len(rows)
        if not n:
            continue
        wc = [len(words(r)) for r in rows]
        single = sum(1 for c in wc if c <= 1)
        ratio = round(single / n, 4)
        avg = round(sum(wc) / n, 2)
        return {"table": table, "text_col": text_col, "sample": n,
                "single_word_ratio": ratio, "avg_words": avg,
                "signal_ratio": round(1 - ratio, 4),
                "pass": ratio <= 0.5 and avg >= 2.0}
    return {"pass": None, "note": "no text-bearing table for this mode"}

def axis_use(con, mode):
    out = {"pass": None}
    if mode == "spine":
        g = dict(con.execute(
            "select event_type, count(*) from events group by 1").fetchall())
        prop, dec = g.get("proposal-issued", 0), g.get("decided", 0)
        rej = g.get("rejected", 0)
        ratio = round(dec / prop, 4) if prop else None
        out.update({"proposal_issued": prop, "decided": dec, "rejected": rej,
                    "decided_ratio": ratio,
                    "pass": bool(prop) and ratio is not None and ratio >= 0.5})
    elif mode == "organism":
        eps = con.execute("select count(*) from episodes").fetchone()[0]
        les = con.execute("select count(*) from lessons").fetchone()[0]
        ratio_pct = round(100 * les / eps, 3) if eps else None
        fu = con.execute(
            "select count(*) from memory_read_receipts where future_use_count > 0"
        ).fetchone()[0] if "memory_read_receipts" in logical_tables(con) else None
        de = con.execute("select count(*) from decision_evidence").fetchone()[0] \
            if "decision_evidence" in logical_tables(con) else None
        out.update({"episodes": eps, "lessons": les, "lesson_ratio_pct": ratio_pct,
                    "future_use_positive_receipts": fu, "decision_evidence": de,
                    "pass": ratio_pct is not None and ratio_pct >= 1.0
                            and (fu or 0) >= 1})
    return out

def axis_vault(con):
    fts = next((r[0] for r in con.execute(
        "select name from sqlite_master where type='table' and name like '%_fts'")), None)
    if not fts:
        return {"pass": None, "note": "no FTS table in this schema"}
    rows = con.execute(f'select count(*) from "{fts}"').fetchone()[0]
    try:
        vocab = con.execute(
            f'select count(distinct term) from "{fts}_idx"').fetchone()[0]
    except sqlite3.OperationalError:
        vocab = None
    try:
        match_spine = con.execute(
            f"select count(*) from \"{fts}\" where memory_fts match 'spine'"
            if fts == "memory_fts" else
            f'select count(*) from "{fts}" where {fts} match \'spine\'').fetchone()[0]
        query_ok = True
    except sqlite3.OperationalError as e:
        match_spine, query_ok = None, False
        return {"fts_table": fts, "rows": rows, "vocab_terms": vocab,
                "query_ok": False, "error": str(e), "pass": False}
    return {"fts_table": fts, "rows": rows, "vocab_terms": vocab,
            "match_spine": match_spine,
            "pass": query_ok and rows > 0}

def detect_mode(con):
    ts = set(logical_tables(con))
    if "episodes" in ts and "lessons" in ts: return "organism"
    if "memory" in ts and "events" not in ts: return "memory"
    if "events" in ts and "memory" not in ts: return "spine"
    return "unknown"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--node", required=True)
    ap.add_argument("--out", default="evidence")
    ap.add_argument("--max-sample", type=int, default=200)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    src_sha = hashlib.sha256(Path(a.src).read_bytes()).hexdigest()[:6]
    fixture = out / f"fixture-{Path(a.src).name}-{src_sha}.db"
    try:
        copy_s = backup_copy(a.src, fixture)
        con = sqlite3.connect(f"file:{fixture}?mode=ro", uri=True)
        mode = detect_mode(con)
        rep = {"src": a.src, "fixture": str(fixture), "node": a.node,
               "mode": mode, "src_sha256_6": src_sha,
               "table_count": len(logical_tables(con)),
               "copy_seconds": copy_s,
               "signal": axis_signal(con, mode, a.max_sample),
               "use": axis_use(con, mode),
               "vault": axis_vault(con)}
        con.close()
        axes = [rep[k].get("pass") for k in ("signal", "use", "vault")]
        failed = [k for k, v in zip(("signal", "use", "vault"), axes) if v is False]
        rep["_verdict"] = ("LIVE_MEMORY_HEALTHY" if not failed and any(a is True for a in axes)
                           else f"LIVE_MEMORY_BOTTLENECK:{'+'.join(failed) or 'no_axis_measured'}")
        rep_path = out / f"memtest_live_{a.node}_{mode}_report.json"
        rep_path.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0 if not failed else 2)
    except Exception as ex:
        print(json.dumps({"error": f"{type(ex).__name__}: {ex}", "src": a.src}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
