#!/usr/bin/env python3
"""
manifest_generator.py — Generate a machine-readable manifest of the kernel state.

این ماژول یک manifest.json تولید می‌کند که بدن می‌تواند آن را بخواند.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Kernel root path (absolute, stable for this project)
KERNEL_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = KERNEL_ROOT / "body_bridge" / "output"
MANIFEST_JSON = OUTPUT_DIR / "manifest.json"

INTEGRITY_FILES = [
    KERNEL_ROOT / "rsc.py",
    KERNEL_ROOT / "SENSITIVITY-LADDER.md",
    KERNEL_ROOT / "GEOMETRY.md",
    KERNEL_ROOT / "CLAIMS_LEDGER.csv",
]

# Regex for ADR frontmatter parsing
_RE_ADR_HEADER = re.compile(r"^#\s+(ADR-\d+)\s+[—-]\s+(.*)$", re.MULTILINE)
_RE_STATUS = re.compile(r"\*\*Status:\*\*\s*(.*?)(?:\n|$)", re.IGNORECASE)
_RE_DATE = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
_RE_SPEC = re.compile(r"\*\*Spec(?:s)?:\*\*\s*(.*?)(?:\n|$)", re.IGNORECASE)
_RE_DECISION_RULE = re.compile(r"\*\*Decision rule.*?\*\*\s*(.*?)(?:\n|$)", re.IGNORECASE)
_RE_MACHINE_VERDICT = re.compile(r"machine\s+verdict\s+(?:\*\*)?([A-Z/\-]+)(?:\*\*)?", re.IGNORECASE)
_RE_ACCEPTED = re.compile(r"\bAccepted\b", re.IGNORECASE)
_RE_NO_VERDICT = re.compile(r"no machine verdict applies", re.IGNORECASE)

# Regex for sensitivity ladder sections
_RE_SENSITIVITY_SECTION = re.compile(
    r"###\s*(?:🟢|🟡|🔴)?\s*(LOW|MEDIUM|HIGH)\s*\n(.*?)(?=\n###\s|$)",
    re.DOTALL | re.IGNORECASE,
)

# Regex for seed family in experiments
_RE_SEED_FAMILY = re.compile(r"SEED_FAMILY\s*=\s*[\"']?([^\"'\n]+)")


def _sha256_of_file(path: Path) -> str:
    """Compute SHA256 hex digest of file contents."""
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
    except Exception as e:
        logger.warning("Failed to read %s for hashing: %s", path, e)
        return ""
    return h.hexdigest()


def _parse_adr_frontmatter(text: str) -> dict:
    """Parse ADR markdown text and extract frontmatter fields.

    Returns dict with keys:
        number, title, verdict, date, spec, decision_rule
    """
    if not text or not text.strip():
        return {
            "number": None,
            "title": "",
            "verdict": "UNKNOWN",
            "date": "",
            "spec": "",
            "decision_rule": "",
        }

    # Number and title from first header
    header_match = _RE_ADR_HEADER.search(text)
    if header_match:
        number = header_match.group(1).strip()
        title = header_match.group(2).strip()
    else:
        number = None
        title = ""

    # Status line
    status_match = _RE_STATUS.search(text)
    status = status_match.group(1).strip() if status_match else ""

    # Date
    date_match = _RE_DATE.search(text)
    date = date_match.group(1) if date_match else ""

    # Spec
    spec_match = _RE_SPEC.search(text)
    spec = spec_match.group(1).strip() if spec_match else ""
    spec = spec.strip("`").strip()

    # Decision rule
    decision_rule_match = _RE_DECISION_RULE.search(text)
    decision_rule = decision_rule_match.group(1).strip() if decision_rule_match else ""

    # Verdict extraction
    verdict = "UNKNOWN"
    if _RE_ACCEPTED.search(status) or _RE_NO_VERDICT.search(status):
        verdict = "ACCEPTED"
    else:
        machine_match = _RE_MACHINE_VERDICT.search(status)
        if machine_match:
            verdict = machine_match.group(1).strip().upper()
        else:
            # Fallback: look for bold standalone verdict in status
            bold_match = re.search(r"\*\*([A-Z/\-]+)\*\*", status)
            if bold_match:
                verdict = bold_match.group(1).strip().upper()

    # Normalize accepted
    if verdict.lower() == "accepted":
        verdict = "ACCEPTED"

    return {
        "number": number,
        "title": title,
        "verdict": verdict,
        "date": date,
        "spec": spec,
        "decision_rule": decision_rule,
    }


def _scan_experiments() -> list[dict]:
    """Scan experiments/*.py and return a deterministic sorted list of experiment metadata.

    Excludes __init__.py, demo/ subdirectories, and mock* files.
    """
    experiments_dir = KERNEL_ROOT / "experiments"
    results: list[dict] = []

    if not experiments_dir.exists():
        logger.warning("Experiments directory not found: %s", experiments_dir)
        return results

    for path in sorted(experiments_dir.glob("*.py")):
        name = path.name
        if name == "__init__.py":
            continue
        if "mock" in name.lower():
            continue
        # demo/ files are naturally excluded by *.py glob, but double-check
        if path.parent.name == "demo":
            continue

        content = ""
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to read experiment %s: %s", name, e)

        seed_match = _RE_SEED_FAMILY.search(content)
        seed_family = seed_match.group(1).strip() if seed_match else None

        results.append({
            "name": path.stem,
            "status": "done",
            "last_verdict": "UNKNOWN",
            "seed_family": seed_family,
        })

    return sorted(results, key=lambda x: x["name"])


def _read_sensitivity_ladder() -> dict:
    """Read SENSITIVITY-LADDER.md and return LOW/MEDIUM/HIGH mapping.

    If the file is missing or unreadable, return default summaries.
    """
    path = KERNEL_ROOT / "SENSITIVITY-LADDER.md"
    defaults = {
        "LOW": "read-only",
        "MEDIUM": "edits with rollback note",
        "HIGH": "owner approval required",
    }

    if not path.exists():
        return defaults

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to read sensitivity ladder: %s", e)
        return defaults

    ladder = {}
    for match in _RE_SENSITIVITY_SECTION.finditer(text):
        key = match.group(1).upper()
        value = match.group(2).strip()
        ladder[key] = value

    if not ladder:
        return defaults

    # Ensure all keys exist even if a section was missing
    for k in ("LOW", "MEDIUM", "HIGH"):
        if k not in ladder:
            ladder[k] = defaults[k]

    return ladder


def generate() -> dict:
    """Scan the kernel directory and produce a manifest.json.

    Returns the manifest dict and writes it to MANIFEST_JSON.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Scan ADRs
    adrs: list[dict] = []
    adr_dir = KERNEL_ROOT / "adr"
    if adr_dir.exists():
        for path in sorted(adr_dir.glob("ADR-*.md")):
            try:
                text = path.read_text(encoding="utf-8")
                parsed = _parse_adr_frontmatter(text)
                parsed["filename"] = path.name
                adrs.append(parsed)
            except Exception as e:
                logger.warning("Failed to parse ADR %s: %s", path.name, e)

    # Scan experiments
    experiments = _scan_experiments()

    # Read sensitivity ladder
    sensitivity_ladder = _read_sensitivity_ladder()

    # Compute integrity hashes
    integrity: dict[str, str] = {}
    for fpath in INTEGRITY_FILES:
        if fpath.exists():
            integrity[fpath.name] = _sha256_of_file(fpath)
        else:
            logger.warning("Integrity file missing: %s", fpath)
            integrity[fpath.name] = ""

    manifest = {
        "kernel_name": "Cognitive Kernel 0.1",
        "ring": 2,
        "status": "shadow-attached",
        "autonomy": "L1-propose-only",
        "risk_tier": "green",
        "capabilities": [
            "spec_compilation",
            "falsifiable_experimentation",
            "adr_verdict",
            "claims_ledger",
            "geometric_abstraction",
            "sensitivity_grading",
            "adversarial_review",
        ],
        "experiments": experiments,
        "adrs": adrs,
        "sensitivity_ladder": sensitivity_ladder,
        "commands": {
            "validate": "LOW",
            "run": "LOW",
            "body.write": "HIGH",
            "adr_feed.refresh": "LOW",
            "daemon.start": "HIGH",
            "daemon.stop": "HIGH",
            "dashboard_sync.sync": "LOW",
            "financial": "HIGH",
            "list": "LOW",
            "manifest_generator.generate": "LOW",
            "persistent_config": "HIGH",
            "publish": "HIGH",
            "verdict_stream.refresh": "LOW",
        },
        "interfaces": [
            {
                "description": "Body dashboards may query kernel outputs via read-only SQLite attachments.",
                "name": "read-only SQLite",
                "sensitivity": "LOW",
            },
            {
                "description": "manifest.json, adr_feed.json, verdict_stream.jsonl in body_bridge/output/.",
                "name": "JSON feeds",
                "sensitivity": "LOW",
            },
            {
                "description": "Direct markdown scan of adr/ADR-*.md files (fallback).",
                "name": "ADR directory",
                "sensitivity": "LOW",
            },
            {
                "description": "Python class in body that reads kernel outputs and emits body events.",
                "name": "kernel_consumer",
                "sensitivity": "LOW",
            },
        ],
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "integrity": integrity,
    }

    try:
        MANIFEST_JSON.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("Failed to write manifest.json: %s", e)

    return manifest


def validate_integrity() -> dict:
    """Check if current files match stored hashes in manifest.json.

    Returns a dict with keys:
        valid (bool), reason (str), manifest_exists (bool), details (dict)
    """
    if not MANIFEST_JSON.exists():
        return {
            "valid": False,
            "reason": "manifest_missing",
            "manifest_exists": False,
            "details": {},
        }

    try:
        manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Failed to read manifest.json: %s", e)
        return {
            "valid": False,
            "reason": "manifest_missing",
            "manifest_exists": False,
            "details": {},
        }

    stored = manifest.get("integrity", {})
    details: dict[str, dict] = {}
    all_ok = True

    for fpath in INTEGRITY_FILES:
        filename = fpath.name
        expected = stored.get(filename, "")
        actual = _sha256_of_file(fpath) if fpath.exists() else ""
        ok = bool(expected) and bool(actual) and expected == actual
        details[filename] = {
            "ok": ok,
            "expected": expected,
            "actual": actual,
        }
        if not ok:
            all_ok = False

    return {
        "valid": all_ok,
        "reason": "ok" if all_ok else "integrity_mismatch",
        "manifest_exists": True,
        "details": details,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
    manifest = generate()
    print(f"Manifest generated: {MANIFEST_JSON}")
    print(f"  ADRs: {len(manifest['adrs'])}")
    print(f"  Experiments: {len(manifest['experiments'])}")
    integrity_result = validate_integrity()
    print(f"  Integrity: {integrity_result['reason']}")


if __name__ == "__main__":
    main()
