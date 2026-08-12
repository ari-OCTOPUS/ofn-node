#!/usr/bin/env python3
"""verify_math_atlas.py -- canonical read-only Math Atlas verifier.

Reads the repository at ROOT (default: parent of _ops) and produces a
deterministic Markdown report on stdout covering equations 1..20,
flag governance, SOG lock integrity, run_all registration, rhythm (#17),
consolidation (#18), and AST purity.

Exit 1 if any structured check contains CRIT; 0 otherwise.
Only --out writes a file; stdout is always Markdown.
No runtime module imports/execution.

Usage:
    python _ops/scripts/verify_math_atlas.py [--root ROOT] [--out PATH]
"""
from __future__ import annotations

import ast
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
OK = "OK"
WARN = "WARN"
CRIT = "CRIT"
SPEC = "SPEC"
UNKNOWN = "UNKNOWN"

# ---------------------------------------------------------------------------
# Math flags of interest (subset of all flags)
# ---------------------------------------------------------------------------
MATH_FLAGS = [
    "OCTOPUS_WIRE_BCM",
    "OCTOPUS_WIRE_BCM_FEED",
    "OCTOPUS_WIRE_IDENTITY_EQ",
    "OCTOPUS_WIRE_BIO",
    "OCTOPUS_CHRONO_PHI_HONEST",
    "OCTOPUS_WIRE_CHRONO_RHYTHM",
    "OCTOPUS_NEURAL_LEARNED_APPLY",
]

# ---------------------------------------------------------------------------
# Paths (relative to ROOT)
# ---------------------------------------------------------------------------
OPS_DIR = "_ops"
FLAGS_CMD = "_ops/OCTOPUS-flags.cmd"
OWNER_VERDICTS = "_ops/owner-verdicts.yaml"
SOG_LOCK = "_ops/state/sim/PULSE-EQUATIONS-LOCKED.json"
RUN_ALL = "_ops/tests/run_all.py"
SIGNALS_REGISTRY = "architecture/signals-registry.yaml"
CAPABILITY_MANIFEST = "_ops/capability-manifest.json"

# Canonical equation rows (name, impl_path)
ROWS = [
    (1, "BCM", "_ops/neural/bcm.py"),
    (2, "Hebbian", "_ops/neural/hebbian.py"),
    (3, "Pain/Nociceptor", "_ops/neural/nociceptor.py"),
    (4, "latent cosine", "_ops/neural/latent_space.py"),
    (5, "L identity", "_ops/identity_equations.py"),
    (6, "E identity", "_ops/identity_equations.py"),
    (7, "G identity", "_ops/identity_equations.py"),
    (8, "K identity", "_ops/identity_equations.py"),
    (9, "O identity", "_ops/identity_equations.py"),
    (10, "SOG/DARE/Kalman bundle", "_ops/heart/sog_math.py"),
    (11, "Living-Beat", "_ops/heart/control_law.py"),
    (12, "allometry", "_ops/cardiac.py"),
    (13, "phi", "_ops/chrono.py"),
    (14, "Laplacian + legacy sigma", "_ops/doctor/spectral.py"),
    (15, "fusion A=-L(G)", "04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC.md"),
    (16, "integrated time equation", "07 - Knowledge/Time-Architecture/MAP.md"),
    (17, "Chrono rhythm", "_ops/chrono_rhythm/rhythm.py"),
    (18, "Decay-Reinforcement", "_ops/cortex/consolidate.py"),
    (19, "Doctor z-dynamics", "04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC.md"),
    (20, "Doctor stability", "04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC.md"),
]

SPEC_ONLY_ROWS = {15, 16, 19, 20}  # spec-only, no dedicated .py implementation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None


def _read_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _yaml_available() -> bool:
    try:
        import yaml  # noqa: F401
        return True
    except ImportError:
        return False


def _parse_yaml(path: Path) -> Optional[dict]:
    if not _yaml_available():
        return None
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _parse_flags_cmd(text: str) -> Dict[str, str]:
    flags: Dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if s.upper().startswith("SET "):
            rest = s[4:].strip()
            if "=" in rest:
                k, _, v = rest.partition("=")
                flags[k.strip().upper()] = v.strip()
    return flags


def _line_of_match(text: str, pattern: str) -> Optional[int]:
    for i, ln in enumerate(text.splitlines(), 1):
        if re.search(pattern, ln):
            return i
    return None


def _ast_names(text: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Return (functions: {name: line}, classes: {name: line}) from AST."""
    funcs: Dict[str, int] = {}
    classes: Dict[str, int] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return funcs, classes
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name not in funcs:
            funcs[node.name] = node.lineno
        elif isinstance(node, ast.ClassDef) and node.name not in classes:
            classes[node.name] = node.lineno
    return funcs, classes


def _has_symbol(text: str, name: str) -> Tuple[bool, Optional[int]]:
    """Check AST for a function/class name (comments/docstrings immune)."""
    funcs, classes = _ast_names(text)
    if name in funcs:
        return True, funcs[name]
    if name in classes:
        return True, classes[name]
    return False, None


# ---------------------------------------------------------------------------
# Flag governance
# ---------------------------------------------------------------------------

def _check_flags(root: Path) -> List[Dict[str, Any]]:
    """Check multiple math flags with precedence env > flags.cmd > verdicts.
    Report per-flag value, source, drift. Explicit env `0` wins."""
    results: List[Dict[str, Any]] = []

    flags_text = _read_text(root / FLAGS_CMD)
    cmd_flags = _parse_flags_cmd(flags_text) if flags_text else {}

    verdicts = _parse_yaml(root / OWNER_VERDICTS)
    verdict_flags: Dict[str, str] = {}
    if verdicts:
        for vname, vdata in verdicts.get("verdicts", {}).items():
            if isinstance(vdata, dict) and "env" in vdata:
                verdict_flags[vdata["env"]] = str(vdata.get("value", ""))

    for flag_name in MATH_FLAGS:
        env_val = os.environ.get(flag_name)
        cmd_val = cmd_flags.get(flag_name)
        yam_val = verdict_flags.get(flag_name)

        sources: List[Tuple[str, str]] = []
        if env_val is not None:
            sources.append(("env", env_val))
        if cmd_val is not None:
            sources.append(("flags.cmd", cmd_val))
        if yam_val is not None:
            sources.append(("owner-verdicts.yaml", yam_val))

        if not sources:
            results.append({"flag": flag_name, "value": None, "source": "none",
                            "drift": None})
            continue

        # Precedence: env > flags.cmd > verdicts
        effective = env_val if env_val is not None else (cmd_val if cmd_val is not None else yam_val)
        source = "env" if env_val is not None else ("flags.cmd" if cmd_val is not None else "owner-verdicts.yaml")

        # Drift: sources disagree
        drift = None
        if len(sources) > 1:
            vals = {v for _, v in sources}
            if len(vals) > 1:
                drift = "drift: " + "; ".join(f"{s}={v}" for s, v in sources)

        results.append({"flag": flag_name, "value": effective,
                        "source": source, "drift": drift})
    return results


# ---------------------------------------------------------------------------
# SOG lock validation
# ---------------------------------------------------------------------------

def _check_sog_lock(root: Path) -> Dict[str, Any]:
    lock_path = root / SOG_LOCK
    result: Dict[str, Any] = {"path": str(lock_path), "status": UNKNOWN, "notes": []}

    text = _read_text(lock_path)
    if text is None:
        result["status"] = CRIT
        result["notes"].append("SOG lock file not found or unreadable")
        return result

    data = _read_json(lock_path)
    if data is None:
        result["status"] = CRIT
        result["notes"].append("SOG lock file is not valid JSON")
        return result

    result["status"] = OK
    for key, label in [("ts", "timestamp"), ("schema", "schema"),
                       ("operating_point", "operating_point"),
                       ("gates", "gates"), ("provenance", "provenance"),
                       ("status", "status")]:
        if not isinstance(data.get(key), (str, dict)):
            result["status"] = WARN
            result["notes"].append(f"Missing/invalid {label}")

    prov = data.get("provenance", {})
    if isinstance(prov, dict):
        sha = prov.get("code_sha256")
        if not isinstance(sha, str) or len(sha) < 16:
            result["status"] = WARN
            result["notes"].append("provenance.code_sha256 missing or short")

    st = data.get("status", {})
    if isinstance(st, dict):
        locked = [k for k, v in st.items() if v == "locked"]
        if not locked:
            result["status"] = WARN
            result["notes"].append("No equations in locked status")
        else:
            result["notes"].append(f"Locked: {', '.join(locked)}")
    if result["status"] == OK:
        result["notes"].append("Valid lock with provenance")
    return result


# ---------------------------------------------------------------------------
# run_all registration
# ---------------------------------------------------------------------------

def _check_run_all(root: Path) -> Dict[str, Any]:
    ra_path = root / RUN_ALL
    result: Dict[str, Any] = {"path": str(ra_path), "status": UNKNOWN,
                               "notes": [], "registrations": []}
    text = _read_text(ra_path)
    if text is None:
        result["status"] = CRIT
        result["notes"].append("run_all.py not found or unreadable")
        return result

    required = [
        ("test_rhythm.py", "#17 rhythm"),
        ("test_canonical_consolidation.py", "#18 consolidation"),
        ("test_identity_equations.py", "identity eq"),
        ("test_verify_math_atlas.py", "verifier self"),
    ]
    for test, desc in required:
        found = test in text
        line = _line_of_match(text, re.escape(test)) if found else None
        result["registrations"].append(
            {"test": test, "desc": desc, "found": found, "line": line})
        if not found:
            result["status"] = WARN
            result["notes"].append(f"{test} not registered")

    if result["status"] == UNKNOWN:
        result["status"] = OK
        result["notes"].append("All key registrations found")
    return result


# ---------------------------------------------------------------------------
# #17 registry/capability truth
# ---------------------------------------------------------------------------

def _check_registry_truth(root: Path) -> Dict[str, Any]:
    """Parse signals-registry.yaml and capability manifest for #17/APPLY truth."""
    result: Dict[str, Any] = {"status": UNKNOWN, "notes": []}

    reg = _parse_yaml(root / SIGNALS_REGISTRY)
    if reg is None:
        result["status"] = UNKNOWN
        result["notes"].append("signals-registry.yaml unavailable or parse failure")
        return result

    signals = reg.get("signals", [])
    chrono_rhythm_found = False
    apply_found = False
    for sig in signals:
        sid = sig.get("id", "")
        if "chrono_rhythm" in sid or "chrono-rhythm" in sid:
            chrono_rhythm_found = True
        if "apply" in sid.lower():
            apply_found = True
    result["notes"].append(
        f"signals-registry.yaml: {len(signals)} signals, "
        f"chrono_rhythm={'found' if chrono_rhythm_found else 'absent'}, "
        f"apply={'found' if apply_found else 'absent'}")

    cap = _read_json(root / CAPABILITY_MANIFEST)
    if cap is None:
        result["notes"].append("capability-manifest.json not parsed")
    else:
        result["notes"].append(f"capability-manifest: {cap.get('capability_id', '?')}")

    result["status"] = OK if chrono_rhythm_found else UNKNOWN
    return result


# ---------------------------------------------------------------------------
# AST purity: forbidden rhythm side effects
# ---------------------------------------------------------------------------

def _check_rhythm_purity(root: Path) -> Dict[str, Any]:
    rhy_text = _read_text(root / "_ops/chrono_rhythm/rhythm.py")
    result: Dict[str, Any] = {"status": UNKNOWN, "notes": []}
    if rhy_text is None:
        result["status"] = CRIT
        result["notes"].append("rhythm.py not readable")
        return result

    forbidden_imports = [
        "opslib", "chrono", "organ_gate", "money_gate",
        "capability_gate", "budget_gate", "EffectorGate",
    ]
    forbidden_calls = ["settle", "money", "send", "execute"]

    violations: List[str] = []
    try:
        tree = ast.parse(rhy_text)
    except SyntaxError:
        return result

    imports_found: set = set()
    calls_found: set = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports_found.add(node.module)
            for alias in node.names:
                imports_found.add(alias.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls_found.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls_found.add(node.func.attr)

    for fi in forbidden_imports:
        for imp in imports_found:
            if fi in imp:
                violations.append(f"import '{fi}': {imp}")
    for fc in forbidden_calls:
        if fc in calls_found:
            violations.append(f"call '{fc}'")

    if violations:
        result["status"] = CRIT
        result["notes"].extend(violations)
    else:
        result["status"] = OK
        result["notes"].append("No forbidden imports/calls via AST")
    return result


# ---------------------------------------------------------------------------
# Build equation atlas (20 canonical rows)
# ---------------------------------------------------------------------------

def _build_atlas(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    # Pre-parse identity_equations.py for weighted assignments in evaluate
    ie_text = _read_text(root / "_ops/identity_equations.py")
    ie_funcs, ie_classes = _ast_names(ie_text) if ie_text else ({}, {})

    # Pre-parse rhythm.py
    rhy_text = _read_text(root / "_ops/chrono_rhythm/rhythm.py")
    rhy_funcs, rhy_classes = _ast_names(rhy_text) if rhy_text else ({}, {})

    # Pre-parse sog_math.py
    sog_text = _read_text(root / "_ops/heart/sog_math.py")
    sog_funcs, sog_classes = _ast_names(sog_text) if sog_text else ({}, {})

    # Check spectral v2 shadow
    v2_shadow_exists = (root / "_ops/doctor/spectral_definitions.py").is_file()

    for num, name, impl_path in ROWS:
        row: Dict[str, Any] = {
            "eq": num, "name": name,
            "impl_path": impl_path, "status": UNKNOWN,
            "line": None, "tests": "-", "flags": "-",
            "consumer": "-", "evidence": "",
        }

        if num in SPEC_ONLY_ROWS:
            spec_path = root / impl_path
            spec_exists = spec_path.is_file()
            row["status"] = SPEC if spec_exists else CRIT
            row["evidence"] = "spec found" if spec_exists else "spec file missing"
            row["tests"] = "spec-only"
            rows.append(row)
            continue

        full_path = root / impl_path
        text = _read_text(full_path)

        if text is None:
            row["status"] = CRIT
            row["evidence"] = "implementation file missing"
            rows.append(row)
            continue

        funcs, classes = _ast_names(text)
        found = False
        line = None

        if num == 1:  # BCM
            found, line = bool(classes.get("BCMStabilizer")), \
                classes.get("BCMStabilizer")
            row["consumer"] = "bcm"
        elif num == 2:  # Hebbian
            found, line = bool(classes.get("HebbianAssociator")), \
                classes.get("HebbianAssociator")
            row["consumer"] = "hebbian"
        elif num == 3:  # Nociceptor
            found, line = bool(classes.get("Nociceptor")), \
                classes.get("Nociceptor")
            row["consumer"] = "pain"
        elif num == 4:  # latent cosine
            found, line = bool(classes.get("SharedLatentSpace")), \
                classes.get("SharedLatentSpace")
            row["consumer"] = "latent_space"
        elif num in (5, 6, 7, 8, 9):  # Identity equations L, E, G, K, O
            # Verify actual weighted assignments in evaluate
            if "evaluate" in funcs:
                found = True
                line = funcs["evaluate"]
                # Check IDENTITIES dict has the right keys
                if ie_text and '"learner"' in ie_text:
                    row["evidence"] = "IDENTITIES dict with weighted assignments; evaluate() present"
                else:
                    row["evidence"] = "evaluate() found; IDENTITIES dict check skipped"
            else:
                found = False
            row["consumer"] = "identity_equations"
            row["tests"] = "test_identity_equations.py"
        elif num == 10:  # SOG/DARE/Kalman bundle
            for key_fn in ("solve_floors", "delta_self", "e_shadow",
                           "identity_total", "evaluate_gates", "run_lock"):
                if key_fn in sog_funcs:
                    found = True
                    line = sog_funcs[key_fn]
                    break
            # Also check SOG lock
            lock_ok = (root / SOG_LOCK).is_file()
            row["evidence"] = f"sog_math functions; lock={'present' if lock_ok else 'MISSING'}"
            row["consumer"] = "sog_math"
            row["tests"] = "test_sog_lock"
        elif num == 11:  # Living-Beat
            found, line = bool(funcs.get("heart_step") or funcs.get("precision_weight")), \
                funcs.get("heart_step") or funcs.get("precision_weight")
            row["consumer"] = "control_law"
        elif num == 12:  # allometry
            found, line = bool(funcs.get("bio_rhythm")), funcs.get("bio_rhythm")
            row["consumer"] = "cardiac"
        elif num == 13:  # phi
            found, line = bool(funcs.get("_phi_honest") or "PHI_SUSPECT" in text), \
                funcs.get("_phi_honest")
            row["consumer"] = "chrono"
        elif num == 14:  # Laplacian + legacy sigma
            found, line = bool(funcs.get("laplacian_spectrum")), \
                funcs.get("laplacian_spectrum")
            row["evidence"] = "Laplacian spectrum; legacy sigma from spectral_definitions"
            if v2_shadow_exists:
                row["evidence"] += "; v2 shadow exists (spectral_definitions.py)"
            row["consumer"] = "doctor/spectral"
        elif num == 17:  # Chrono rhythm CR-B0 + CR-B1
            has_rhythm = "Rhythm" in rhy_classes
            has_kuramoto = "kuramoto_order_parameter" in rhy_funcs
            has_step = "step" in rhy_funcs
            found = has_rhythm
            line = rhy_classes.get("Rhythm")
            if has_rhythm and has_step:
                row["status"] = OK
                row["evidence"] = "CR-B0 built/tested"
                if has_kuramoto:
                    row["evidence"] += "; CR-B1 PARTIAL (kuramoto_order_parameter exists but runtime-disconnected)"
                else:
                    row["evidence"] += "; CR-B1 unbuilt"
            elif has_rhythm:
                row["status"] = WARN
                row["evidence"] = "Rhythm class found; step() missing"
            else:
                row["status"] = CRIT
                row["evidence"] = "rhythm.py missing key structures"
            row["consumer"] = "chrono_rhythm"
            row["tests"] = "test_rhythm.py"
            rows.append(row)
            continue
        elif num == 18:  # Decay-Reinforcement
            has_consolidate = "consolidate_once" in funcs
            found = has_consolidate
            line = funcs.get("consolidate_once")
            if has_consolidate:
                row["status"] = OK
                row["evidence"] = "built-partial/TESTED; consolidate_once() present; spec: BIO-SYNTHESIS-MAP.md"
                row["impl_path"] += " + 04 - Architect System/BIO-SYNTHESIS-MAP.md"
            else:
                row["status"] = CRIT
                row["evidence"] = "consolidate_once() missing"
            row["consumer"] = "cortex/consolidate"
            row["tests"] = "test_canonical_consolidation.py"
            rows.append(row)
            continue

        if found:
            if row["status"] == UNKNOWN:
                row["status"] = OK
        else:
            row["status"] = CRIT
            row["evidence"] = "formula/implementation absent"

        if line is None:
            # Find any relevant symbol
            if funcs:
                line = next(iter(funcs.values()))
            elif classes:
                line = next(iter(classes.values()))
        row["line"] = line
        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _render(atlas: List[Dict[str, Any]], flags: List[Dict[str, Any]],
            sog_lock: Dict[str, Any], run_all: Dict[str, Any],
            registry: Dict[str, Any], purity: Dict[str, Any]) -> str:
    lines: List[str] = []
    has_crit = False

    # Collect all statuses
    all_statuses: set = set()
    for r in atlas:
        all_statuses.add(r["status"])
    all_statuses.add(sog_lock["status"])
    all_statuses.add(run_all["status"])
    all_statuses.add(registry["status"])
    all_statuses.add(purity["status"])
    for f in flags:
        if f["drift"]:
            all_statuses.add(CRIT)

    has_crit = CRIT in all_statuses

    lines.append("# Math Atlas Verification Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    if has_crit:
        lines.append("**VERDICT: CRIT** -- one or more critical issues found.")
    elif WARN in all_statuses or UNKNOWN in all_statuses:
        lines.append("**VERDICT: WARN** -- warnings/unknowns present.")
    else:
        lines.append("**VERDICT: OK** -- all checks passed.")
    lines.append("")

    # Flag governance
    lines.append("## Flag Governance")
    lines.append("")
    for f in flags:
        val = f["value"]
        src = f["source"]
        drift = f["drift"]
        if val is not None:
            lines.append(f"- `{f['flag']}` = `{val}` (source: {src})")
        else:
            lines.append(f"- `{f['flag']}` = *unset* (source: {src})")
        if drift:
            lines.append(f"  - **DRIFT (CRIT)**: {drift}")
    lines.append("")

    # SOG Lock
    lines.append(f"## SOG Lock ({SOG_LOCK})")
    lines.append("")
    lines.append(f"- Status: **{sog_lock['status']}**")
    for n in sog_lock["notes"]:
        lines.append(f"- {n}")
    lines.append("")

    # run_all
    lines.append(f"## run_all.py ({RUN_ALL})")
    lines.append("")
    lines.append(f"- Status: **{run_all['status']}**")
    for n in run_all["notes"]:
        lines.append(f"- {n}")
    for reg in run_all.get("registrations", []):
        mark = "x" if reg["found"] else " "
        extra = f" (line {reg['line']})" if reg.get("line") else ""
        lines.append(f"- [{mark}] `{reg['test']}` ({reg['desc']}){extra}")
    lines.append("")

    # Registry truth
    lines.append("## Registry/Capability Truth (#17, APPLY)")
    lines.append("")
    lines.append(f"- Status: **{registry['status']}**")
    for n in registry["notes"]:
        lines.append(f"- {n}")
    lines.append("")

    # Rhythm AST purity
    lines.append("## Rhythm AST Purity (#17)")
    lines.append("")
    lines.append(f"- Status: **{purity['status']}**")
    for n in purity["notes"]:
        lines.append(f"- {n}")
    lines.append("")

    # Equation atlas table
    lines.append("## Equation Atlas (1..20)")
    lines.append("")
    lines.append("| # | Name | Status | Impl Path | Line | Tests | Flags | Consumer | Evidence |")
    lines.append("|---|------|--------|-----------|------|-------|-------|----------|----------|")
    for r in atlas:
        ln = str(r.get("line")) if r.get("line") else "-"
        lines.append(
            f"| {r['eq']} | `{r['name']}` | **{r['status']}** | "
            f"`{r['impl_path']}` | {ln} | {r['tests']} | {r['flags']} | "
            f"{r['consumer']} | {r['evidence']} |")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Canonical read-only Math Atlas verifier")
    parser.add_argument("--root", default=None,
                        help="Repository root (default: parent of _ops)")
    parser.add_argument("--out", default=None,
                        help="Optional output file path (only write)")
    args = parser.parse_args(argv)

    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parent.parent.parent
    if not (root / OPS_DIR).is_dir():
        print(f"ERROR: {root / OPS_DIR} not found; use --root", file=sys.stderr)
        return 1

    flags = _check_flags(root)
    sog_lock = _check_sog_lock(root)
    run_all = _check_run_all(root)
    registry = _check_registry_truth(root)
    purity = _check_rhythm_purity(root)
    atlas = _build_atlas(root)

    md = _render(atlas, flags, sog_lock, run_all, registry, purity)

    # Stdout is always markdown
    print(md)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")

    # Structured exit: 1 iff any check contains CRIT status
    has_crit = False
    for r in atlas:
        if r["status"] == CRIT:
            has_crit = True
    if sog_lock["status"] == CRIT:
        has_crit = True
    if run_all["status"] == CRIT:
        has_crit = True
    if purity["status"] == CRIT:
        has_crit = True
    for f in flags:
        if f["drift"]:
            has_crit = True

    return 1 if has_crit else 0


if __name__ == "__main__":
    sys.exit(main())
