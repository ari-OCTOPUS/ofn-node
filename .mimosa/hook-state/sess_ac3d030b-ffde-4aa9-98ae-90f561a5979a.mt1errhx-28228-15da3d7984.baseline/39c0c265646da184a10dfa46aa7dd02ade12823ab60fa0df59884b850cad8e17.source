#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4d_system class caller counts + 7-day effect logs. Read-only."""
from __future__ import annotations

import ast
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"F:/backup")
D4 = ROOT / "4d_system"
OPS = ROOT / "_ops"

SKIP = {"tests", "__pycache__", "nbb-cp-kre", "src"}  # src/nbb_cp is separate product


def is_test(p: Path) -> bool:
    if "tests" in {x.lower() for x in p.parts}:
        return True
    return p.name.startswith("test_") or p.endswith("_test.py") if False else (
        p.name.startswith("test_") or p.name.endswith("_test.py")
    )


def class_defs(src: str):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and not n.name.startswith("_"):
            out.append((n.name, n.lineno, (getattr(n, "end_lineno", n.lineno) or n.lineno) - n.lineno + 1))
    return out


def collect_py(base: Path):
    prod, tests = [], []
    for f in base.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        if set(f.parts) & {"nbb-cp-kre"}:
            continue
        if is_test(f):
            tests.append(f)
        else:
            # skip 4d_system/src (nbb_cp product) for this sweep — separate stack
            if "src" in f.relative_to(base).parts and base.name == "4d_system":
                continue
            prod.append(f)
    return prod, tests


def count_name(name: str, texts: dict[str, str], self_rel: str) -> list[tuple[str, int]]:
    pat = re.compile(r"\b" + re.escape(name) + r"\b")
    hits = []
    for rel, txt in texts.items():
        if rel == self_rel:
            continue
        n = len(pat.findall(txt))
        if n:
            hits.append((rel, n))
    return hits


def jsonl_since(path: Path, days=7, ts_keys=("ts", "timestamp", "t", "at", "when")):
    if not path.exists():
        return {"path": str(path), "exists": False}
    cut = datetime.now(timezone.utc) - timedelta(days=days)
    n_all = 0
    n_win = 0
    kinds = Counter()
    samples = []
    for line in path.read_text("utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        n_all += 1
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = None
        for k in ts_keys:
            if k in d:
                ts = d[k]
                break
        if ts is None and isinstance(d, dict):
            for k, v in d.items():
                if "time" in k.lower() or k in ("ts", "when"):
                    ts = v
                    break
        ok = False
        if isinstance(ts, (int, float)):
            try:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                ok = dt >= cut
            except (OSError, ValueError, OverflowError):
                ok = True  # unparsable → count in window conservatively? no, skip
                ok = False
        elif isinstance(ts, str):
            s = ts.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                ok = dt >= cut
            except ValueError:
                # prefix compare
                ok = ts[:10] >= cut.date().isoformat()
        if ok:
            n_win += 1
            kind = d.get("kind") or d.get("method") or d.get("event") or d.get("action") or d.get("type") or "?"
            kinds[str(kind)[:40]] += 1
            if len(samples) < 3:
                samples.append({k: d.get(k) for k in list(d)[:8]})
    st = path.stat()
    return {
        "rel": str(path.relative_to(ROOT)).replace("\\", "/"),
        "exists": True,
        "bytes": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "rows_all": n_all,
        "rows_7d": n_win,
        "kinds_7d": dict(kinds.most_common(12)),
        "sample_keys": samples[:1],
    }


def main():
    prod, tests = collect_py(D4)
    prod_text = {}
    for f in prod:
        try:
            prod_text[str(f.relative_to(ROOT)).replace("\\", "/")] = f.read_text("utf-8", errors="replace")
        except OSError:
            pass
    test_text = {}
    for f in tests:
        try:
            test_text[str(f.relative_to(ROOT)).replace("\\", "/")] = f.read_text("utf-8", errors="replace")
        except OSError:
            pass

    rows = []
    for f in prod:
        rel = str(f.relative_to(ROOT)).replace("\\", "/")
        src = prod_text.get(rel, "")
        for name, lineno, span in class_defs(src):
            ph = count_name(name, prod_text, rel)
            th = count_name(name, test_text, rel)
            n_prod = sum(x[1] for x in ph)
            n_test = sum(x[1] for x in th)
            rows.append({
                "rel": rel,
                "name": name,
                "lineno": lineno,
                "span": span,
                "mtime": datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"),
                "prod_hits": n_prod,
                "prod_files": [x[0] for x in ph[:8]],
                "test_hits": n_test,
                "test_files": [x[0] for x in th[:6]],
                "unwired": n_prod == 0,
            })
    rows.sort(key=lambda r: (not r["unwired"], -int(r["test_hits"] > 0), -r["span"]))

    # consolidation.json shape
    cons = D4 / "outputs" / "self_evolved" / "consolidation.json"
    cons_info = {}
    if cons.exists():
        try:
            data = json.loads(cons.read_text("utf-8"))
            if isinstance(data, list):
                cons_info = {"type": "list", "n": len(data), "keys0": list(data[0]) if data and isinstance(data[0], dict) else None}
            elif isinstance(data, dict):
                cons_info = {"type": "dict", "keys": list(data)[:20], "n_insights": len(data.get("insights") or data.get("cycles") or [])}
        except Exception as e:
            cons_info = {"error": type(e).__name__}

    neural = OPS / "neural" / "consolidation.json"
    neural_info = {}
    if neural.exists():
        try:
            data = json.loads(neural.read_text("utf-8"))
            if isinstance(data, list):
                neural_info = {"type": "list", "n": len(data)}
            elif isinstance(data, dict):
                # common shape: {cycles: [...]} or last cycle
                cyc = data.get("cycles") or data.get("history") or data.get("insights")
                neural_info = {"type": "dict", "keys": list(data)[:16], "n_cycles": len(cyc) if isinstance(cyc, list) else None}
        except Exception as e:
            neural_info = {"error": type(e).__name__}

    # sqlite 4d events last 7d for effect-like names
    db = D4 / "outputs" / "4d_experiments.db"
    ev = {}
    if db.exists():
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            names = con.execute("SELECT event_name, COUNT(*) FROM dashboard_events GROUP BY 1 ORDER BY 2 DESC").fetchall()
            ev["event_counts"] = names[:25]
            cut = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            recent = con.execute(
                "SELECT event_name, COUNT(*) FROM dashboard_events WHERE timestamp >= ? GROUP BY 1 ORDER BY 2 DESC",
                (cut,),
            ).fetchall()
            ev["event_counts_7d"] = recent[:25]
            ev["n_7d"] = sum(x[1] for x in recent)
        except Exception as e:
            ev["error"] = f"{type(e).__name__}: {e}"
        finally:
            con.close()

    daemon = {}
    dsp = D4 / "outputs" / "daemon_state.json"
    if dsp.exists():
        try:
            daemon = json.loads(dsp.read_text("utf-8"))
        except Exception as e:
            daemon = {"error": type(e).__name__}

    out = {
        "prod_files": len(prod),
        "test_files": len(tests),
        "classes": len(rows),
        "unwired": sum(1 for r in rows if r["unwired"]),
        "unwired_with_tests": sum(1 for r in rows if r["unwired"] and r["test_hits"] > 0),
        "rows_unwired": [r for r in rows if r["unwired"]],
        "rows_wired_sample": [r for r in rows if not r["unwired"]][:15],
        "consolidation_4d": cons_info,
        "consolidation_ops": neural_info,
        "daemon_state_keys": list(daemon)[:30] if isinstance(daemon, dict) else None,
        "daemon_pid": daemon.get("pid") if isinstance(daemon, dict) else None,
        "daemon_last_tick": daemon.get("last_tick_at") if isinstance(daemon, dict) else None,
        "events": ev,
        "effects": {
            "pep_shadow": jsonl_since(OPS / "state" / "telegram-pep-shadow.jsonl"),
            "tg_send": jsonl_since(OPS / "state" / "tg-send-log.jsonl"),
            "paid_calls": jsonl_since(OPS / "state" / "paid-calls.jsonl"),
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
