#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build CLAIMS_LEDGER.csv — the C×A claims lattice, realized as a data artifact.

Corpus mandate: raw corpus N §13 demands a CLAIMS_LEDGER; GEOMETRY.md §6 defines
the two orthogonal ordinal ladders it realizes — C0..C4 (evidence CONTENT) and
A0..A4 (evidence TRUST, here proxied by the project's [FACT]/[EST] tags). Every
claim is a point on that lattice with an epistemic tag.

Deterministic, stdlib-only. Parses:
  - adr/ADR-*.md          -> one row per ADR verdict (defensive regex over the
                             ADR header bullets + verdict tables)
  - specs/*.yaml          -> one row per INTENTIONALLY-FAILING spec (a spec that
                             literally declares itself broken/expected-to-FAIL)

Discipline (locked):
  * NEVER invent a number — every value is extracted literally from the files.
  * If a field is not literally present, write "unknown".
  * Output is byte-deterministic given the same input files (sorted iteration,
    no timestamps, fixed line terminator).

Usage:  python tools/build_claims_ledger.py
Output: CLAIMS_LEDGER.csv at the repository root (UTF-8, LF).
"""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "adr"
SPEC_DIR = ROOT / "specs"
OUT_PATH = ROOT / "CLAIMS_LEDGER.csv"

COLUMNS = [
    "claim_id", "claim", "c_level", "verdict", "primary_metric",
    "primary_value", "evidence_tag", "source", "spec", "seed_family", "caveats",
]

UNKNOWN = "unknown"
MACHINE_VERDICTS = ("INTEGRATE", "OPTIMIZE", "REJECTED", "DISCARD")

# number with optional sign; U+2212 (−) is the true minus some ADR tables use
NUM = r"[+\-−]?\d+(?:\.\d+)?"
# C-ladder coordinate, single ("C0") or range/pair ("C0–C3", "C0/C1"); en dash,
# hyphen and slash all appear in the corpus
C_LEVEL = r"C[0-4](?:\s*[–—/\-]\s*C?[0-4])?"
# a seed family: 4-7 digit base, optional range, optional trailing "+"
FAMILY = r"\d{4,7}(?:\s*[–—\-]\s*\d{4,7})?\s*\+?"


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def _norm_num(s: str) -> str:
    return s.replace("−", "-")


def _clean(text: str, limit: int = 220) -> str:
    """Collapse a literal extract to one CSV-friendly line (no invention)."""
    t = text.replace("`", "")
    t = re.sub(r"\*\*?", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = t.strip(" ;·-—").strip()
    if len(t) > limit:
        t = t[: limit - 1].rstrip() + "…"
    return t if t else UNKNOWN


def _section(md: str, heading_re: str) -> str:
    """Return the body of the first `## <heading>` matching heading_re."""
    m = re.search(rf"^##\s+{heading_re}", md, re.M)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s+", md[start:], re.M)
    return md[start:start + nxt.start()] if nxt else md[start:]


# --------------------------------------------------------------------------- #
# ADR field extractors (regex over headers / verdict tables — defensive)
# --------------------------------------------------------------------------- #

def _adr_claim(md: str) -> str:
    m = re.search(r"^#\s+ADR-\d+\s*[–—\-]+\s*(.+)$", md, re.M)
    return _clean(m.group(1)) if m else UNKNOWN


def _adr_verdict(md: str) -> str:
    m = re.search(r"machine verdict\s*\*{0,2}([A-Z]+)\*{0,2}", md)
    if m and m.group(1) in MACHINE_VERDICTS:
        return m.group(1)
    if re.search(r"\*\*Status:\*\*\s*Accepted", md):
        return "accepted"
    return UNKNOWN


def _adr_primary_metric(md: str) -> str:
    m = re.search(
        r"\*\*Decision rule \(GO/NO-GO\):\*\*\s*`?([A-Za-z_][A-Za-z0-9_]*)`?\s*<",
        md,
    )
    return m.group(1) if m else UNKNOWN


def _adr_primary_value(verdict_md: str) -> str:
    """First bolded number in the verdict table's primary (bold-labelled) row;
    falls back to any bolded table number, then to `= **x**` prose."""
    def bold_num(cells: list[str]) -> str | None:
        for c in cells:
            m = re.search(rf"\*\*\s*({NUM})\s*\*\*", c)
            if m:
                return _norm_num(m.group(1))
        return None

    fallback = None
    for line in verdict_md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or re.match(r"^:?-{2,}", cells[0]):
            continue  # markdown separator row
        val = bold_num(cells[1:])
        if val is None:
            continue
        if cells[0].startswith("**"):
            return val  # bold first cell == the primary condition row
        if fallback is None:
            fallback = val
    if fallback is not None:
        return fallback
    m = re.search(rf"=\s*\*\*({NUM})\*\*", verdict_md)
    return _norm_num(m.group(1)) if m else UNKNOWN


def _adr_evidence_tag(verdict_md: str, primary_value: str) -> str:
    if primary_value == UNKNOWN:
        return UNKNOWN
    if "[FACT" in verdict_md:
        return "FACT"
    if "[EST" in verdict_md:
        return "EST"
    return UNKNOWN


def _adr_spec(md: str) -> str:
    m = re.search(r"^-\s*\*\*Specs?:\*\*\s*(.+)$", md, re.M)
    if not m:
        return UNKNOWN
    m2 = re.search(r"specs/[A-Za-z0-9_]+\.ya?ml", m.group(1))
    return m2.group(0) if m2 else UNKNOWN


def _adr_c_level(md: str) -> str:
    scope = _section(md, r"(?:Honest\s+)?[Ss]cope\b.*$")
    for blob in (scope, md):
        if not blob:
            continue
        for m in re.finditer(C_LEVEL, blob):
            val = re.sub(r"\s+", "", m.group(0))
            if val != "C4":  # scope is never phenomenal; skip firewall mentions
                return val
    return UNKNOWN


def _adr_seed_family(md: str, verdict_md: str) -> str:
    generic = rf"(?:famil(?:y|ies)|suites?|universes)\s+`?\**({FAMILY})"
    m = re.search(generic, verdict_md)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    # gap may wrap across one line break (e.g. "confirmatory run uses the
    # **disjoint** fresh\nfamily `985500–985504`" in ADR-014)
    m = re.search(
        rf"(?:confirmatory|fresh)[\s\S]{{0,60}}?famil(?:y|ies)\s+`?\**({FAMILY})", md
    )
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m = re.search(generic, md)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m = re.search(r"(\d+\s+temporal cuts)", md)  # ADR-008: chronological cuts
    if m:
        return _clean(m.group(1))
    return UNKNOWN


_CAVEAT_PATTERNS = [
    # ordered cascade; first literal hit wins
    r"\*\*Scope caveat \(locked\):\*\*\s*(.+?)(?=\n\s*\n|\n[-#|]|\Z)",
    r"\*\*Honest caveat:\*\*\s*(.+?)(?=\n\s*\n|\n[-#|]|\Z)",
    r"^##\s+Confirmed caveats.*?\n+\s*1\.\s+(.+?)(?=\n\s*\n|\n\s*2\.|\Z)",
    r"\*\*Disclosure[^:*]*:\*\*\s*(.+?)(?=\n\s*\n|\n[-#|]|\Z)",
    r"Honest reading[^\n:]*:\**\s*(.+?)(?=\n\s*\n|\n[-#|]|\Z)",
    r"Reading:\s*(.+?)(?=\n\s*\n|\n[-#|]|\Z)",
    r"scoped to\s+(.+?)(?=\n\s*\n|\n[-#|]|\Z)",
]


def _adr_caveats(md: str) -> str:
    for pat in _CAVEAT_PATTERNS:
        m = re.search(pat, md, re.M | re.S)
        if m:
            return _clean(m.group(1))
    m = re.search(r"\*\*Status:\*\*\s*[^\n(]*\(([^)]+)\)", md)
    if m:
        return _clean(m.group(1))
    return UNKNOWN


def parse_adr(path: Path) -> dict:
    md = path.read_text(encoding="utf-8")
    verdict_md = _section(md, r"Verdict\b")
    num = re.search(r"ADR-(\d+)", path.name)
    claim_id = f"ADR-{num.group(1)}" if num else path.stem
    primary_value = _adr_primary_value(verdict_md)
    return {
        "claim_id": claim_id,
        "claim": _adr_claim(md),
        "c_level": _adr_c_level(md),
        "verdict": _adr_verdict(md),
        "primary_metric": _adr_primary_metric(md),
        "primary_value": primary_value,
        "evidence_tag": _adr_evidence_tag(verdict_md, primary_value),
        "source": f"adr/{path.name}",
        "spec": _adr_spec(md),
        "seed_family": _adr_seed_family(md, verdict_md),
        "caveats": _adr_caveats(md),
    }


# --------------------------------------------------------------------------- #
# intentionally-failing specs (FAIL-by-design rows)
# --------------------------------------------------------------------------- #

def _spec_is_fail_by_design(text: str) -> bool:
    """A spec earns a row ONLY if it literally declares the intent to fail."""
    declares_intent = bool(
        re.search(r"(?i)deliberately", text) or "عمداً" in text  # عمداً
    )
    return declares_intent and "FAIL" in text


def _spec_idea(text: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^idea:\s*(.*)$", line)
        if not m:
            continue
        inline = m.group(1).strip()
        if inline and inline not in (">", "|", ">-", "|-"):
            return _clean(re.sub(r"\s+#.*$", "", inline))
        block: list[str] = []
        for cont in lines[i + 1:]:
            if cont.strip() == "":
                break
            if not re.match(r"^\s+", cont):
                break
            block.append(cont.strip())
        return _clean(" ".join(block)) if block else UNKNOWN
    return UNKNOWN


def _spec_metric_name(text: str) -> str:
    m = re.search(r"^metric:\s*$((?:\n[ \t]+.*)+)", text, re.M)
    if not m:
        return UNKNOWN
    m2 = re.search(r"^\s+name:\s*(.*)$", m.group(1), re.M)
    if not m2:
        return UNKNOWN
    name = re.sub(r"\s+#.*$", "", m2.group(1)).strip().strip("\"'").strip()
    return name if name else UNKNOWN


def _spec_caveat(text: str) -> str:
    for line in text.splitlines():
        if line.lstrip().startswith("#") and ("FAIL" in line or "BROKEN" in line):
            return _clean(line.lstrip().lstrip("#").strip())
    return UNKNOWN


def parse_failing_spec(path: Path, adr_texts: dict[str, str]) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not _spec_is_fail_by_design(text):
        return None
    source = f"specs/{path.name}"  # fallback: the spec declares itself
    for adr_name in sorted(adr_texts):
        if path.name in adr_texts[adr_name]:
            source = f"adr/{adr_name}"
            break
    evidence = UNKNOWN
    if "[EST" in text:
        evidence = "EST"
    elif "[FACT" in text:
        evidence = "FACT"
    c_level = UNKNOWN
    for m in re.finditer(C_LEVEL, text):
        val = re.sub(r"\s+", "", m.group(0))
        if val != "C4":
            c_level = val
            break
    return {
        "claim_id": f"SPEC-{path.stem}",
        "claim": _spec_idea(text),
        "c_level": c_level,
        "verdict": "FAIL-by-design",
        "primary_metric": _spec_metric_name(text),
        "primary_value": UNKNOWN,   # no run can exist: that is the point
        "evidence_tag": evidence,
        "source": source,
        "spec": f"specs/{path.name}",
        "seed_family": UNKNOWN,
        "caveats": _spec_caveat(text),
    }


# --------------------------------------------------------------------------- #
# build + serialize
# --------------------------------------------------------------------------- #

def build_rows() -> list[dict]:
    adr_paths = sorted(ADR_DIR.glob("ADR-*.md"), key=lambda p: p.name)
    rows = [parse_adr(p) for p in adr_paths]
    adr_texts = {p.name: p.read_text(encoding="utf-8") for p in adr_paths}
    for spec_path in sorted(SPEC_DIR.glob("*.yaml"), key=lambda p: p.name):
        row = parse_failing_spec(spec_path, adr_texts)
        if row is not None:
            rows.append(row)
    return rows


def serialize_rows(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow([row[c] for c in COLUMNS])
    return buf.getvalue()


def main() -> int:
    rows = build_rows()
    csv_text = serialize_rows(rows)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(csv_text)

    n_adr = sum(1 for r in rows if r["claim_id"].startswith("ADR-"))
    n_spec = len(rows) - n_adr
    verdicts: dict[str, int] = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1

    print(f"CLAIMS_LEDGER.csv written: {len(rows)} rows "
          f"({n_adr} ADR verdicts + {n_spec} fail-by-design specs)")
    print("verdict counts: " + ", ".join(
        f"{k}={v}" for k, v in sorted(verdicts.items())))

    dirty = False
    for r in rows:
        missing = [c for c in COLUMNS if r[c] == UNKNOWN]
        if missing:
            dirty = True
            print(f"  [fields not found -> unknown] {r['claim_id']}: "
                  + ", ".join(missing))
    if not dirty:
        print("all fields extracted for every row")
    return 0


if __name__ == "__main__":
    sys.exit(main())
