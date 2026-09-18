#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static harvest-vs-run boundary scan. Lane D-S0-HUNT.

Reads F:\\ofn-node from disk. Does not import ofn.agents, does not call
cycle(), does not start ofn.run / ingest_server / harvester, does not
touch the network, and does not set flags.

Usage:
  python harvest_boundary_probe.py
  python harvest_boundary_probe.py --out receipts/harvest-boundary-....json
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import socket
from datetime import datetime, timezone
from pathlib import Path

OFN = Path(r"F:\ofn-node")

SKIP_DIR_NAMES = frozenset({
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".pytest_cache", ".mypy_cache", ".cursor",
    "data",  # runtime sqlite / state — not source labels
})
SCAN_SUFFIXES = frozenset({
    ".py", ".md", ".yaml", ".yml", ".json", ".js", ".txt", ".html",
})
# Do not open credential-shaped names (values never printed anyway).
SKIP_NAME_RE = re.compile(
    r"(?i)(\.env($|\.)|credentials|secret|id_rsa|id_ed25519|\.pem$|\.key$)"
)

DEAD_PATTERNS = (
    ("DEAD SOURCE", re.compile(r"DEAD SOURCE")),
    ("dead_source", re.compile(r"dead_source", re.I)),
    ("dead-source", re.compile(r"dead-source", re.I)),
    ("dead source", re.compile(r"\bdead source\b", re.I)),
)

HARVEST_NAME_RE = re.compile(r"(?i)(harvest|buynsw|buysw|imap_listener)")
RUN_IMPORT_HIT_RE = re.compile(
    r"(?i)\b(harvest|imap|buynsw|buysw|ofn\.agents|agents\.)"
)
BIND_RE = re.compile(r"(?i)\b(bind|listen|0\.0\.0\.0|127\.0\.0\.1)\b")
PORT_RE = re.compile(r"\b87(?:91|92|93|94|95|96)\b")
FLAG_RE = re.compile(r"\b(?:OCTOPUS_WIRE_|OFN_WIRE_|OFN_KEEP_GATES_OPEN)[A-Z0-9_]*")
URL_RE = re.compile(r"https?://[^\s\"']+")
MAIN_RE = re.compile(r"""if\s+__name__\s*==\s*['\"]__main__['\"]""")

HARVEST_REL = (
    "ofn/agents/demand_harvest.py",
    "ofn/agents/h1_harvest.py",
    "ofn/agents/h1_buysw.py",
    "ofn/agents/h1_buysw_dom.py",
    "ofn/agents/nsw_ocp_harvest.py",
    "ofn/agents/seek_harvest.py",
    "ofn/agents/imap_listener.py",
    "tools/ingest_buynsw_batch.py",
)

INGEST_CANDIDATES = (
    "tools/buynsw-harvester/ingest_server.py",
    "tools/ingest_server.py",
    "ingest_server.py",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _quote(line: str, limit: int = 140) -> str:
    text = " ".join(line.strip().split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def parse_run_imports(run_py: Path) -> dict:
    src = run_py.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src, filename=str(run_py))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.append(f"{mod}.{alias.name}" if mod else alias.name)
    hits = [name for name in imports if RUN_IMPORT_HIT_RE.search(name)]
    text_hits = []
    for i, line in enumerate(src.splitlines(), 1):
        if RUN_IMPORT_HIT_RE.search(line) and not line.lstrip().startswith("#"):
            # comments already excluded; keep only import-looking lines
            stripped = line.lstrip()
            if stripped.startswith(("import ", "from ")):
                text_hits.append({"line": i, "quote": _quote(line)})
    return {
        "path": str(run_py),
        "bytes": run_py.stat().st_size,
        "import_count": len(imports),
        "imports": imports,
        "harvest_imap_buynsw_import_hits": hits,
        "harvest_imap_buynsw_import_line_hits": text_hits,
        "wired_into_run": bool(hits or text_hits),
    }


def scan_module(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    urls = URL_RE.findall(text)
    flags = sorted(set(FLAG_RE.findall(text)))
    ports = sorted(set(PORT_RE.findall(text)))
    binds = []
    for i, line in enumerate(text.splitlines(), 1):
        if BIND_RE.search(line):
            binds.append({"line": i, "quote": _quote(line)})
    dead = []
    for label, cre in DEAD_PATTERNS:
        for i, line in enumerate(text.splitlines(), 1):
            if cre.search(line):
                dead.append({"pattern": label, "line": i, "quote": _quote(line)})
    return {
        "path": str(path),
        "exists": True,
        "bytes": path.stat().st_size,
        "has_dunder_main": bool(MAIN_RE.search(text)),
        "urls": urls,
        "flag_names": flags,
        "port_literals": ports,
        "bind_or_listen_lines": binds,
        "dead_source_hits": dead,
    }


def walk_dead_hits(root: Path) -> list[dict]:
    hits: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if SKIP_NAME_RE.search(path.name):
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            matched = [label for label, cre in DEAD_PATTERNS if cre.search(line)]
            if not matched:
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            hits.append({
                "rel": rel,
                "abs": str(path),
                "line": i,
                "patterns": matched,
                "quote": _quote(line),
            })
    return hits


def harvest_paths(root: Path) -> list[dict]:
    rows = []
    agents = root / "ofn" / "agents"
    if agents.is_dir():
        for path in sorted(agents.iterdir()):
            if path.is_file() and path.suffix == ".py" and HARVEST_NAME_RE.search(path.name):
                rows.append({
                    "rel": str(path.relative_to(root)).replace("\\", "/"),
                    "bytes": path.stat().st_size,
                    "via": "ofn/agents filename",
                })
    extra = [
        root / "tools" / "buynsw-harvester",
        root / "tools" / "ingest_buynsw_batch.py",
    ]
    for path in extra:
        if path.is_dir():
            rows.append({
                "rel": str(path.relative_to(root)).replace("\\", "/"),
                "kind": "dir",
                "file_count": sum(1 for p in path.iterdir() if p.is_file()),
                "via": "known harvest tree",
            })
        elif path.is_file():
            rows.append({
                "rel": str(path.relative_to(root)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "via": "known harvest tree",
            })
        else:
            rows.append({
                "rel": str(path.relative_to(root)).replace("\\", "/"),
                "exists": False,
                "via": "known harvest tree",
            })
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Static harvest vs ofn.run probe")
    ap.add_argument("--ofn", default=str(OFN), help="ofn-node root")
    ap.add_argument("--out", default="", help="write JSON receipt here")
    args = ap.parse_args(argv)

    root = Path(args.ofn)
    run_py = root / "ofn" / "run.py"

    run_info = parse_run_imports(run_py) if run_py.is_file() else {
        "path": str(run_py), "exists": False, "wired_into_run": None,
    }

    modules = {}
    for rel in HARVEST_REL:
        path = root / rel.replace("/", "\\")
        modules[rel] = scan_module(path) if path.is_file() else {
            "path": str(path), "exists": False,
        }

    ingest = {}
    for rel in INGEST_CANDIDATES:
        path = root / rel.replace("/", "\\")
        ingest[rel] = {
            "exists": path.is_file(),
            "path": str(path),
            "bytes": path.stat().st_size if path.is_file() else 0,
        }

    dead_hits = walk_dead_hits(root) if root.is_dir() else []
    # Collapse to one row per file for the summary table (first hit kept).
    dead_by_file: dict[str, dict] = {}
    for hit in dead_hits:
        dead_by_file.setdefault(hit["rel"], hit)

    receipt = {
        "schema": "octopus.d-s0-hunt.harvest-boundary.v1",
        "lane": "D-S0-HUNT",
        "measured_at_utc": _now_iso(),
        "host": socket.gethostname(),
        "scope": "this_host_only",
        "claim_type": "observation",
        "network": "none",
        "started": {
            "ofn.run": False,
            "demand_harvest": False,
            "ingest_server": False,
            "buynsw-harvester": False,
        },
        "ofn_root": str(root),
        "run_py": run_info,
        "harvest_module_paths": harvest_paths(root) if root.is_dir() else [],
        "harvest_modules": modules,
        "ingest_server_candidates": ingest,
        "dead_source_hit_count": len(dead_hits),
        "dead_source_file_count": len(dead_by_file),
        "dead_source_hits": dead_hits,
        "dead_source_first_per_file": list(dead_by_file.values()),
        "note": (
            "ABSENT on this laptop is body_not_on_this_host, "
            "not system-wide missing. Laptop != board 180."
        ),
    }

    text = json.dumps(receipt, indent=2, ensure_ascii=False)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    # Console is often cp1252 on this laptop — ASCII summary only.
    print("probe=harvest_boundary_probe")
    print("lane=D-S0-HUNT")
    print(f"host={receipt['host']}")
    print("scope=this_host_only")
    print("network=none")
    print(f"run_py_exists={run_py.is_file()}")
    print(f"run_import_count={run_info.get('import_count', 0)}")
    print(f"run_harvest_imap_buynsw_wired={run_info.get('wired_into_run')}")
    print(f"run_harvest_imap_buynsw_hits={run_info.get('harvest_imap_buynsw_import_hits')}")
    print(f"dead_source_hit_count={receipt['dead_source_hit_count']}")
    print(f"dead_source_file_count={receipt['dead_source_file_count']}")
    print(f"ingest_server_in_tree={any(v.get('exists') for v in ingest.values())}")
    if args.out:
        print(f"wrote={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
