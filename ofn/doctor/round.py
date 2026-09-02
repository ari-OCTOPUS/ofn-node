#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""round — the read-only doctor round over a source vault.

There is no write mode and no flag that enables one: the module does not
import anything that can mutate the source tree. Proof of read-only-ness is
structural (no mutating API) and evidential (integrity manifests of every
file the round opened, before==after, recorded in the receipt).
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .contract_map import CONTRACT_SOURCE_SHA256, extract_gaps, load_contract

__all__ = [
    "SourceNotFoundError", "Finding", "RoundResult", "DoctorRound",
    "tree_hash",
]

SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

SKIP_DIRS = {
    ".git", ".claude", ".pytest_cache", "__pycache__", "node_modules",
    "99-ARCHIVE", "_Archive", "_github-export", "_Duplicates", "_zip-verify",
}

# Policy (canonical-vault, 2026-09-02): the owner-board CURRENT-TRUTH is the
# canonical content holder; OCTOPUS\\CURRENT-TRUTH.md is a separate machine
# lineage written by _ops. Both are legitimately content-bearing.
EXEMPT_MIRRORS = (
    "06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md",
    "OCTOPUS/CURRENT-TRUTH.md",
)
POINTER_MARKERS = ("mirror-cleanup-20260902", "99-ARCHIVE")
MIRROR_SIZE_LIMIT = 600  # bytes; a pointer redirect is tiny

_REF_RE = re.compile(r"`([^`\s]+\.(?:md|json|ya?ml|csv|py))`")
_WIKI_RE = re.compile(r"\[\[([^\]|]+)")


class SourceNotFoundError(RuntimeError):
    """The declared source root does not exist — fail closed, no scan."""


@dataclass
class Finding:
    id: str
    category: str
    severity: str
    title: str
    evidence_path: str
    evidence_sha256: str
    detail: str
    proposed_action: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")


@dataclass
class RoundResult:
    vault_root: str
    findings: list[Finding] = field(default_factory=list)
    files_opened: list[str] = field(default_factory=list)
    manifest_before: dict[str, str] = field(default_factory=dict)
    manifest_after: dict[str, str] = field(default_factory=dict)
    changed_sources: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def to_machine_json(self) -> dict:
        return {
            "vault_root": self.vault_root,
            "findings": [asdict(f) for f in self.findings],
            "stats": self.stats,
            "changed_sources": self.changed_sources,
            "read_only_proven": not self.changed_sources,
            "files_opened": len(self.files_opened),
        }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "x"


def _build_index(root: Path, cap: int = 3) -> tuple[set[str], dict[str, list[str]]]:
    """One walk of the vault: relpath set + basename → up to `cap` locations."""
    relpaths: set[str] = set()
    basenames: dict[str, list[str]] = {}
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        parts = set(rel.parts)
        if parts & SKIP_DIRS or "__pycache__" in p.name or not p.is_file():
            continue
        rp = rel.as_posix()
        relpaths.add(rp)
        basenames.setdefault(p.name, [])
        if len(basenames[p.name]) < cap:
            basenames[p.name].append(rp)
    return relpaths, basenames


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_hash(root: Path, skip: set[str] | None = None) -> str:
    """Hash of the full tree state (names+bytes) — used by tests to prove immutability."""
    skip = skip or SKIP_DIRS
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        parts = set(p.relative_to(root).parts)
        if parts & skip or "__pycache__" in p.name:
            continue
        h.update(str(p.relative_to(root)).encode("utf-8"))
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


class DoctorRound:
    """Read-only scanner. `checks` injectable for tests; defaults are the four."""

    def __init__(self, checks: list | None = None):
        self._checks = checks if checks is not None else [
            self.mirror_check, self.dead_ref_check, self.root_junk_check,
            self.contract_gap_check,
        ]

    # ------------------------------------------------------------- plumbing
    def _open(self, root: Path, rel: str, opened: dict[str, str]) -> bytes | None:
        """Read a file exactly once; record first-access hash; classify failures."""
        path = root / rel
        try:
            data = path.read_bytes()
        except PermissionError:
            self._findings.append(Finding(
                id=f"PERMDENIED-{_slug(rel)}", category="permission", severity="MEDIUM",
                title=f"unreadable source: {rel}", evidence_path=rel,
                evidence_sha256="", detail="PermissionError while reading",
                proposed_action="grant read access or exclude explicitly; never bypass",
            ))
            return None
        except OSError as e:
            self._findings.append(Finding(
                id=f"IOERROR-{_slug(rel)}", category="io", severity="MEDIUM",
                title=f"unreadable source: {rel}", evidence_path=rel,
                evidence_sha256="", detail=f"{type(e).__name__}: {e}",
                proposed_action="inspect path; doctor never retries blindly",
            ))
            return None
        opened[rel] = sha256_bytes(data)
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            self._findings.append(Finding(
                id=f"MALFORMED-{_slug(rel)}", category="malformed", severity="MEDIUM",
                title=f"non-utf8 source: {rel}", evidence_path=rel,
                evidence_sha256=opened[rel], detail="file is not valid UTF-8",
                proposed_action="classify encoding with the owner; no auto-conversion",
            ))
        return data

    def _walk(self, root: Path, max_depth: int = 6):
        for p in sorted(root.rglob("*")):
            rel = p.relative_to(root)
            if len(rel.parts) > max_depth:
                continue
            if set(rel.parts[:-1]) & SKIP_DIRS or rel.parts[0] in SKIP_DIRS:
                continue
            yield p, rel.as_posix()

    # --------------------------------------------------------------- checks
    def mirror_check(self, root: Path, opened: dict[str, str]) -> None:
        """Canonical-vault policy: CURRENT-TRUTH mirrors must be pointers now."""
        for p, rel in self._walk(root):
            if p.name != "CURRENT-TRUTH.md" or not p.is_file():
                continue
            if rel in EXEMPT_MIRRORS:
                continue
            data = self._open(root, rel, opened)
            if data is None:
                continue
            text = data.decode("utf-8", errors="replace")
            is_pointer = any(m in text for m in POINTER_MARKERS)
            if not is_pointer and len(data) > MIRROR_SIZE_LIMIT:
                self._findings.append(Finding(
                    id=f"MIRROR-{_slug(rel)}", category="mirror", severity="HIGH",
                    title=f"content-bearing CURRENT-TRUTH mirror: {rel}",
                    evidence_path=rel, evidence_sha256=opened[rel],
                    detail=(f"{len(data)} bytes, no pointer marker "
                            f"({', '.join(POINTER_MARKERS)})"),
                    proposed_action=("reduce to pointer per canonical policy "
                                     "(owner ruling; via PR/artifact only)"),
                ))

    def dead_ref_check(self, root: Path, opened: dict[str, str]) -> None:
        """References inside 01-TRUTH must resolve inside the vault.

        Resolution ladder (a false 'dead' claim is worse than silence):
        exact root-relative → exact source-relative → wildcard glob →
        unique-basename index over the whole vault. Zero hits at every
        rung = dead; hits only at the basename rung = relocated/unanchored.
        """
        truth_dir = root / "01-TRUTH"
        if not truth_dir.is_dir():
            return
        relpaths, basenames = _build_index(root)
        for p in sorted(truth_dir.glob("*.md")):
            rel = p.relative_to(root).as_posix()
            data = self._open(root, rel, opened)
            if data is None:
                continue
            text = data.decode("utf-8", errors="replace")
            refs = [m for m in _REF_RE.findall(text)] + [
                m.strip() for m in _WIKI_RE.findall(text)
                if m.strip().endswith((".md", ".json", ".yaml", ".csv", ".py"))
            ]
            src_dir = p.parent
            for ref in dict.fromkeys(refs):
                if self._ref_resolves(root, src_dir, ref, relpaths):
                    continue
                base = ref.replace("\\", "/").rsplit("/", 1)[-1]
                candidates = basenames.get(base, [])
                if candidates:
                    self._findings.append(Finding(
                        id=f"RELOCATED-{_slug(rel)}-{_slug(ref)}", category="deadref",
                        severity="LOW",
                        title=f"unanchored reference in {rel}: {ref}",
                        evidence_path=rel, evidence_sha256=opened[rel],
                        detail=f"path does not resolve, but basename exists at: "
                               f"{', '.join(candidates[:3])}",
                        proposed_action="re-anchor the reference to its real path "
                                        "(proposal; never auto-edit the vault)",
                    ))
                else:
                    self._findings.append(Finding(
                        id=f"DEADREF-{_slug(rel)}-{_slug(ref)}", category="deadref",
                        severity="MEDIUM",
                        title=f"dead reference in {rel}: {ref}",
                        evidence_path=rel, evidence_sha256=opened[rel],
                        detail=f"no match at any resolution rung under {root} "
                               f"(root-relative, source-relative, wildcard, basename)",
                        proposed_action="repair the reference or archive the claim "
                                        "(proposal; never auto-edit the vault)",
                    ))

    @staticmethod
    def _ref_resolves(root: Path, src_dir: Path, ref: str, relpaths: set[str]) -> bool:
        import fnmatch as _fn
        ref = ref.replace("\\", "/")
        if any(ch in ref for ch in "*?["):
            pat = ref
            return any(_fn.fnmatch(rp, pat) or _fn.fnmatch(rp, f"*/{pat}")
                       for rp in relpaths)
        if ref in relpaths:
            return True
        src_rel = (src_dir / ref).resolve()
        try:
            src_rel = src_rel.relative_to(root.resolve()).as_posix()
        except ValueError:
            return False
        return src_rel in relpaths

    def root_junk_check(self, root: Path, opened: dict[str, str]) -> None:
        """Known shell-redirect junk at the vault root (never delete — archive)."""
        def _is_junk(name: str) -> bool:
            return (
                (name.startswith("debug-") or name == "debug.log") and name.endswith(".log")
                or name.startswith(("FAIL,", "PASS,", "check("))
                or "gate_e2e(" in name
            )
        for p in sorted(root.iterdir()):
            if p.is_file() and _is_junk(p.name):
                data = self._open(root, p.name, opened)
                self._findings.append(Finding(
                    id=f"JUNK-{_slug(p.name)}", category="junk", severity="LOW",
                    title=f"shell-redirect junk at vault root: {p.name}",
                    evidence_path=p.name,
                    evidence_sha256=opened.get(p.name, ""),
                    detail="byproduct of a shell quoting bug; not vault content",
                    proposed_action="move to 99-ARCHIVE with archive_ prefix "
                                    "(AGENTS.md §7; owner/lane artifact, no deletion)",
                ))

    def contract_gap_check(self, root: Path, opened: dict[str, str]) -> None:
        """The doctor reads its own contract and registers its missing organs."""
        contract = load_contract()
        gaps = extract_gaps(contract)
        if not gaps:
            return
        by_area: dict[str, int] = {}
        for g in gaps:
            by_area[g["area"]] = by_area.get(g["area"], 0) + 1
        detail = "; ".join(f"{a}={n}" for a, n in sorted(by_area.items()))
        self._findings.append(Finding(
            id="CONTRACT-GAPS", category="contract", severity="LOW",
            title="contract gaps feed the self-backlog",
            evidence_path="ofn/doctor/contract/LAB-DOCTOR-CONTRACT.yaml",
            evidence_sha256=CONTRACT_SOURCE_SHA256,
            detail=f"{len(gaps)} gaps ({detail}); source vault: "
                   f"LAB-DOCTOR-CONTRACT.yaml @ {CONTRACT_SOURCE_SHA256[:12]}",
            proposed_action="upsert into self-backlog; scheduling needs owner ruling",
        ))

    # ------------------------------------------------------------------ run
    def run(self, vault_root: Path | str) -> RoundResult:
        root = Path(vault_root)
        if not root.is_dir():
            raise SourceNotFoundError(f"source root does not exist: {root}")
        t0 = time.monotonic()
        self._findings: list[Finding] = []
        opened: dict[str, str] = {}
        for check in self._checks:
            check(root, opened)

        manifest_after: dict[str, str] = {}
        for rel in opened:
            p = root / rel
            if p.exists():
                try:
                    manifest_after[rel] = sha256_bytes(p.read_bytes())
                except OSError:
                    manifest_after[rel] = "<unreadable>"
        changed = [r for r in opened if manifest_after.get(r) not in (opened[r], "<unreadable>")]
        by_sev: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        for f in self._findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
        return RoundResult(
            vault_root=str(root),
            findings=self._findings,
            files_opened=list(opened),
            manifest_before=dict(opened),
            manifest_after=manifest_after,
            changed_sources=changed,
            stats={
                "findings": len(self._findings),
                "by_severity": by_sev,
                "by_category": by_cat,
                "files_opened": len(opened),
                "duration_s": round(time.monotonic() - t0, 3),
                "read_only_proven": not changed,
            },
        )
