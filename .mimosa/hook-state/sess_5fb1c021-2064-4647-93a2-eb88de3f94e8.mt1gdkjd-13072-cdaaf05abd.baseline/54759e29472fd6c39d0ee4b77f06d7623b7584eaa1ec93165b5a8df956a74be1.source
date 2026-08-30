"""Pure domain types. stdlib-only by invariant (no numpy/networkx here)."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "Note", "ScanReport", "LinkGraph", "RepresentationScore", "BakeoffReport",
    "LinkProposal", "ProposalStatus", "QuarantinedText", "PipelineResult",
]


class ProposalStatus(str, Enum):
    """Mirrors nbb_cp: nothing is ever applied without a human verdict (INV-2)."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class QuarantinedText:
    """INV-9 — text crossing a trust boundary is DATA, never instructions.

    Vault note bodies are untrusted input. Wrapping them makes it impossible to
    pass one to an LLM by accident: ``str()`` returns the delimited form and the
    raw body is only reachable via the explicit ``.unwrap_for_parsing()`` call,
    which is used solely by the regex link parser.
    """
    _body: str
    source: str

    def unwrap_for_parsing(self) -> str:
        return self._body

    def __str__(self) -> str:           # pragma: no cover - defensive
        return (f"<<<UNTRUSTED_VAULT_CONTENT source={self.source!r} "
                f"len={len(self._body)}>>>")

    __repr__ = __str__


@dataclass
class Note:
    """One markdown note. `rel_path` is vault-relative, POSIX-normalised."""
    rel_path: str
    stem: str
    folder: str
    depth: int
    size_bytes: int
    mtime: float
    ctime: float
    n_chars: int = 0
    n_words: int = 0
    fm_type: str | None = None
    fm_status: str | None = None
    tags: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.rel_path.lower()


@dataclass
class ScanReport:
    """Inventory result. Deliberately reports what it *skipped* — no silent caps."""
    root: str
    scanned_at: str
    elapsed_s: float
    n_dirs_walked: int
    n_files_seen: int
    n_markdown: int
    bytes_markdown: int
    excluded_dirs: list[str]
    excluded_hits: dict[str, int] = field(default_factory=dict)
    skipped_too_large: list[str] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    cap_hit: bool = False
    per_top_folder: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LinkGraph:
    """Undirected link graph plus the directed edges it was built from."""
    nodes: list[str]                                   # rel_path keys, stable order
    edges: list[tuple[int, int]]                       # undirected, i<j, deduped
    directed: list[tuple[int, int]] = field(default_factory=list)
    broken: list[tuple[str, str]] = field(default_factory=list)   # (source, unresolved target)
    ambiguous: list[tuple[str, str, int]] = field(default_factory=list)
    resolution_stats: dict[str, int] = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.nodes)

    @property
    def m(self) -> int:
        return len(self.edges)

    def degree(self) -> list[int]:
        d = [0] * self.n
        for a, b in self.edges:
            d[a] += 1
            d[b] += 1
        return d

    def fingerprint(self) -> str:
        h = hashlib.sha256()
        for a, b in self.edges:
            h.update(f"{a},{b};".encode())
        return h.hexdigest()[:16]


@dataclass
class RepresentationScore:
    name: str
    auc_mean: float
    auc_std: float
    ap_mean: float
    ap_std: float
    n_splits: int
    seconds: float
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class BakeoffReport:
    n_nodes: int
    n_edges: int
    test_frac: float
    seeds: list[int]
    scores: list[RepresentationScore]
    winner: str | None
    winner_beats_baseline_by: float | None
    baseline: str
    control_auc: float | None
    control_ok: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class LinkProposal:
    """A *proposal*, never an action. Applying it requires a human verdict."""
    source: str
    target: str
    score: float
    rank: int
    evidence: dict[str, Any] = field(default_factory=dict)
    status: ProposalStatus = ProposalStatus.PROPOSED

    @property
    def proposal_id(self) -> str:
        return "kre-" + hashlib.sha1(
            f"{self.source}->{self.target}".encode()).hexdigest()[:12]


@dataclass
class PipelineResult:
    scan: ScanReport
    graph_summary: dict[str, Any]
    bakeoff: BakeoffReport | None
    proposals: list[LinkProposal]
    out_dir: str
    artifacts: dict[str, str] = field(default_factory=dict)
