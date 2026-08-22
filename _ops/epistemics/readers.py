"""Read-ONLY adapters for the off-loop epistemics layer.

Minimal reversible wiring (2026-08-23): produce non-null samples from real
on-disk evidence when present. Fail-closed: missing/corrupt sources return
None/[] so metrics degrade instead of crashing. NEVER writes. NEVER claims
phenomenal self-awareness / consciousness.

Verified live sources (OPS-relative + backup-relative, fail-closed):
  - doctor uniqueness receipts: state/doctor/poller-uniqueness-latest.json (+ .jsonl)
  - outbox counts: state/telegram/loop/outbox/*.json (telegram-outbox/1 state)
  - self_audit matrix: state/cortex/audit-matrix.json
  - self_accuracy trail: state/doctor/self-accuracy.jsonl (twin baseline)
  - topology extras: CURRENT-HARDWARE, Board2 legs map, doctor box-latest roles,
    wave/OrangePi/Board2 evidence dirs (fail-closed; no invented edges)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

# OPS root = parent of this package (_ops). Overridable for fixtures.
_DEFAULT_OPS = Path(__file__).resolve().parent.parent


def ops_root(override: Optional[Path | str] = None) -> Path:
    if override is not None:
        return Path(override)
    env = os.environ.get("OPS_DIR") or os.environ.get("EPISTEMICS_OPS_ROOT")
    if env:
        return Path(env)
    return _DEFAULT_OPS


def _load_json(path: Path) -> Optional[Any]:
    try:
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None


def _load_jsonl(path: Path, limit: int = 500) -> list:
    out: list = []
    try:
        if not path.is_file():
            return out
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if len(out) >= limit:
                    break
    except OSError:
        return []
    return out


def _p(ops: Path, *parts: str) -> Path:
    return ops.joinpath(*parts)


def uniqueness_latest_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "doctor", "poller-uniqueness-latest.json")


def uniqueness_jsonl_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "doctor", "poller-uniqueness.jsonl")


def outbox_dir(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "telegram", "loop", "outbox")


def audit_matrix_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "cortex", "audit-matrix.json")


def self_accuracy_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "doctor", "self-accuracy.jsonl")


def fitness_history_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "fitness-history.json")


def telemetry_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "telemetry-latest.json")


def debate_dir(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "debate")


def read_fitness_history(ops: Optional[Path] = None) -> Optional[Any]:
    return _load_json(fitness_history_path(ops))


def read_telemetry(ops: Optional[Path] = None) -> Optional[Any]:
    return _load_json(telemetry_path(ops))


def read_debate(ops: Optional[Path] = None) -> list:
    d = debate_dir(ops)
    if not d.is_dir():
        return []
    out = []
    try:
        names = sorted(os.listdir(d))
    except OSError:
        return []
    for name in names:
        rec = _load_json(d / name)
        if rec is not None:
            out.append(rec)
    return out


def read_uniqueness_receipts(ops: Optional[Path] = None) -> list:
    """Doctor uniqueness receipts (latest + jsonl). Fail-closed on miss."""
    rows: list = []
    latest = _load_json(uniqueness_latest_path(ops))
    if isinstance(latest, dict):
        rows.append(latest)
    for rec in _load_jsonl(uniqueness_jsonl_path(ops)):
        if isinstance(rec, dict):
            key = (rec.get("beat"), rec.get("checked_at_unix"))
            if any((r.get("beat"), r.get("checked_at_unix")) == key for r in rows):
                continue
            rows.append(rec)
    return rows


def read_outbox_records(ops: Optional[Path] = None) -> list:
    """telegram-outbox/1 records from on-disk outbox dir."""
    d = outbox_dir(ops)
    if not d.is_dir():
        return []
    out = []
    try:
        files = sorted(d.glob("*.json"))
    except OSError:
        return []
    for fp in files:
        rec = _load_json(fp)
        if isinstance(rec, dict) and rec.get("state"):
            out.append(rec)
    return out


def read_outbox_counts(ops: Optional[Path] = None) -> dict:
    """{state: count} over outbox; empty dict if none."""
    counts: dict[str, int] = {}
    for rec in read_outbox_records(ops):
        st = str(rec.get("state") or "")
        if not st:
            continue
        counts[st] = counts.get(st, 0) + 1
    return counts


def read_self_audit(ops: Optional[Path] = None) -> Optional[dict]:
    """self_audit audit-matrix.v1 snapshot. None if missing/invalid."""
    data = _load_json(audit_matrix_path(ops))
    if not isinstance(data, dict):
        return None
    if "tally" not in data and "items" not in data:
        return None
    return data


def read_self_accuracy(ops: Optional[Path] = None) -> list:
    return [r for r in _load_jsonl(self_accuracy_path(ops), limit=1000) if isinstance(r, dict)]


def read_state_labels(ops: Optional[Path] = None) -> list:
    """Labels for identifiability (N_eff): outbox + audit + uniqueness."""
    labels: list = []
    for rec in read_outbox_records(ops):
        st = rec.get("state")
        if st:
            labels.append(f"outbox:{st}")
    audit = read_self_audit(ops)
    if audit:
        items = audit.get("items") or []
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict) and it.get("status"):
                    labels.append(f"audit:{it['status']}")
        tally = audit.get("tally") or {}
        if isinstance(tally, dict):
            for status, n in tally.items():
                try:
                    n_i = int(n)
                except (TypeError, ValueError):
                    continue
                labels.extend([f"audit_tally:{status}"] * max(0, min(n_i, 200)))
    for rec in read_uniqueness_receipts(ops):
        labels.append("uniq:ok" if rec.get("ok") else "uniq:fail")
        checks = rec.get("checks") or {}
        if isinstance(checks, dict):
            for name, val in checks.items():
                labels.append(f"uniq:{name}:{'1' if val else '0'}")
    return labels


def read_channel_pairs(ops: Optional[Path] = None) -> list:
    """Paired (X, Y) samples for channel MI from on-disk evidence only."""
    pairs: list = []
    for rec in read_uniqueness_receipts(ops):
        checks = rec.get("checks") or {}
        if isinstance(checks, dict):
            for name, val in checks.items():
                pairs.append((str(name), 1 if val else 0))
        pairs.append(("receipt_ok", 1 if rec.get("ok") else 0))
    for rec in read_outbox_records(ops):
        st = str(rec.get("state") or "")
        if not st:
            continue
        y = 1 if st == "CONFIRMED" else 0
        pairs.append((st, y))
    audit = read_self_audit(ops)
    if audit:
        for it in audit.get("items") or []:
            if not isinstance(it, dict):
                continue
            st = str(it.get("status") or "")
            if not st:
                continue
            bound = 1 if it.get("evidence_bound") else 0
            pairs.append((st, bound))
    return pairs


def backup_root(ops: Optional[Path] = None) -> Path:
    """Backup/SoT root = parent of OPS (_ops)."""
    return ops_root(ops).parent


def hardware_pointer_path(ops: Optional[Path] = None) -> Path:
    return backup_root(ops) / "07 - Knowledge" / "octopus" / "CURRENT-HARDWARE.md"


def boards_legs_map_path(ops: Optional[Path] = None) -> Path:
    return (
        backup_root(ops)
        / "06-EVIDENCE"
        / "BOARD2-LEGS-VERIFY-MAP-2026-08-22"
        / "RESULT.json"
    )


def doctor_box_latest_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "doctor", "box-latest.json")


def registry_latest_path(ops: Optional[Path] = None) -> Path:
    return _p(ops_root(ops), "state", "registry", "registry-latest.json")


# Wave / OrangePi / Board2 evidence dirs -> capability nodes (edge iff dir exists).
_WAVE_EVIDENCE_NODES: tuple[tuple[str, str, str], ...] = (
    ("wave0_soft", "orangepi", "OCTOPUS-WAVE0-SOFT-ESTOP-UNLOCK-2026-08-23"),
    ("mqtt_local", "orangepi", "OCTOPUS-ORANGEPI-MQTT-1883-ENABLE-ABD-2026-08-22"),
    ("esp32_feeds", "orangepi", "OCTOPUS-ORANGEPI-ESP32-INET-DATA-START-2026-08-22"),
    ("torch", "orangepi", "OCTOPUS-ORANGEPI-TORCH-EXECUTE-2026-08-22"),
    ("ckpt348", "orangepi", "OCTOPUS-CKPT348-OWNER-SIGN-2026-08-22"),
    ("board2_status", "board2", "BOARD2-STATUS-REFRESH-2026-08-23"),
    ("board2_canonical", "board2", "BOARD2-CANONICAL-MAP-2026-08-22"),
)

# doctor/box/box.py::_default_agents roles; used only when box-latest exists.
_DOCTOR_BOX_ROLES: tuple[str, ...] = (
    "Warden",
    "Archivist",
    "Dreamer",
    "Skeptic",
    "Integrator",
    "null-dreamer",
)


def _evidence_dir_ok(backup: Path, dirname: str) -> bool:
    d = backup / "06-EVIDENCE" / dirname
    if not d.is_dir():
        return False
    try:
        return any(d.iterdir())
    except OSError:
        return False


class _TopoGraph:
    """Named undirected adjacency builder. Callers add only evidenced edges."""

    def __init__(self) -> None:
        self._idx: dict[str, int] = {}
        self._edges: set[tuple[int, int]] = set()

    def add_node(self, name: str) -> int:
        if name not in self._idx:
            self._idx[name] = len(self._idx)
        return self._idx[name]

    def add_edge(self, a: str, b: str) -> None:
        if a == b:
            return
        i = self.add_node(a)
        j = self.add_node(b)
        self._edges.add((min(i, j), max(i, j)))

    def adjacency(self) -> Optional[list]:
        n = len(self._idx)
        if n < 2:
            return None
        A = [[0.0] * n for _ in range(n)]
        for i, j in self._edges:
            A[i][j] = A[j][i] = 1.0
        return A

    @property
    def n_nodes(self) -> int:
        return len(self._idx)

    @property
    def n_edges(self) -> int:
        return len(self._edges)

    @property
    def node_names(self) -> list[str]:
        inv = [""] * len(self._idx)
        for name, i in self._idx.items():
            inv[i] = name
        return inv


def _add_uniqueness_subgraph(g: _TopoGraph, ops: Optional[Path]) -> None:
    receipts = read_uniqueness_receipts(ops)
    if not receipts:
        return
    rec = receipts[0]
    checks = rec.get("checks") if isinstance(rec.get("checks"), dict) else {}
    one_c = bool(checks.get("one_center_pid"))
    one_l = bool(checks.get("one_active_lease"))
    one_k = bool(checks.get("one_tg_poller_lock"))
    agree = bool(checks.get("pids_agree"))
    if "one_center_pid" in checks:
        g.add_node("uniq:center")
    if "one_active_lease" in checks:
        g.add_node("uniq:lease")
    if "one_tg_poller_lock" in checks:
        g.add_node("uniq:lock")
    if one_c and one_l:
        g.add_edge("uniq:center", "uniq:lease")
    if one_c and one_k:
        g.add_edge("uniq:center", "uniq:lock")
    if one_l and one_k:
        g.add_edge("uniq:lease", "uniq:lock")
    if agree and one_c and one_l and one_k:
        g.add_edge("uniq:center", "uniq:lease")
        g.add_edge("uniq:center", "uniq:lock")
        g.add_edge("uniq:lease", "uniq:lock")


def _add_hardware_map(g: _TopoGraph, ops: Optional[Path]) -> None:
    path = hardware_pointer_path(ops)
    try:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
    except OSError:
        text = ""
    if not text:
        return
    low = text.lower()
    has_laptop = "laptop" in low
    has_opi = ("orange pi" in low) or ("orangepi" in low)
    has_b2 = "board2" in low
    if not (has_laptop or has_opi or has_b2):
        return
    if has_laptop:
        g.add_node("hw:laptop")
    if has_opi:
        g.add_node("hw:orangepi")
    if has_b2:
        g.add_node("hw:board2")
    if has_laptop and has_opi:
        g.add_edge("hw:laptop", "hw:orangepi")
    if has_laptop and has_b2:
        g.add_edge("hw:laptop", "hw:board2")


def _add_boards_legs(g: _TopoGraph, ops: Optional[Path]) -> None:
    data = _load_json(boards_legs_map_path(ops))
    if not isinstance(data, dict):
        return
    mapping = data.get("mapping")
    if not isinstance(mapping, dict) or not mapping:
        return
    host = "hw:board2" if "hw:board2" in g._idx else "board2"
    g.add_node(host)
    for leg in mapping.keys():
        name = str(leg or "").strip()
        if not name:
            continue
        node = "board2_leg:" + "".join(
            c if c.isalnum() or c in "-_" else "_" for c in name
        )
        g.add_edge(host, node)


def _add_doctor_box_nodes(g: _TopoGraph, ops: Optional[Path]) -> None:
    latest = _load_json(doctor_box_latest_path(ops))
    if not isinstance(latest, dict):
        return
    report = latest.get("report") if isinstance(latest.get("report"), dict) else {}
    if not (report.get("stepped") or latest.get("beat") is not None):
        return
    roles = list(_DOCTOR_BOX_ROLES)
    for r in roles:
        g.add_node(f"doctor:{r}")
    g.add_edge("doctor:Warden", "doctor:Archivist")
    leaves = [r for r in roles if r not in ("Warden", "Archivist")]
    for r in leaves:
        g.add_edge("doctor:Archivist", f"doctor:{r}")
    import random

    rng = random.Random(42)
    leaf_ids = [f"doctor:{r}" for r in leaves]
    if len(leaf_ids) > 1:
        for _ in range(min(2, len(leaf_ids))):
            a, b = rng.sample(leaf_ids, 2)
            g.add_edge(a, b)


def _add_wave_evidence_nodes(g: _TopoGraph, ops: Optional[Path]) -> None:
    backup = backup_root(ops)
    for node_id, host_key, dirname in _WAVE_EVIDENCE_NODES:
        if not _evidence_dir_ok(backup, dirname):
            continue
        if host_key == "orangepi":
            host = "hw:orangepi" if "hw:orangepi" in g._idx else "orangepi"
        elif host_key == "board2":
            host = "hw:board2" if "hw:board2" in g._idx else "board2"
        else:
            host = host_key
        g.add_edge(host, f"wave:{node_id}")


def _add_registry_live_organs(g: _TopoGraph, ops: Optional[Path]) -> None:
    data = _load_json(registry_latest_path(ops))
    if not isinstance(data, dict):
        return
    ents = data.get("entities")
    if not isinstance(ents, list):
        return
    live_organs = []
    for e in ents:
        if not isinstance(e, dict):
            continue
        if e.get("entity_type") != "Organ":
            continue
        if str(e.get("live_state") or "").lower() != "live":
            continue
        lid = str(e.get("logical_id") or "").strip()
        if not lid:
            continue
        live_organs.append(lid.rsplit(":", 1)[-1])
    if not live_organs:
        return
    if "hw:laptop" in g._idx:
        hub = "hw:laptop"
    elif "uniq:center" in g._idx:
        hub = "uniq:center"
    else:
        return
    for org in live_organs:
        g.add_edge(hub, f"organ:{org}")


def read_topology(ops: Optional[Path] = None) -> Optional[Any]:
    """Adjacency from on-disk topology sources (fail-closed, no invented edges).

    Sources (union): uniqueness probe; CURRENT-HARDWARE; Board2 legs map;
    doctor box roles (box-latest); wave/OrangePi/Board2 evidence dirs;
    registry live organs edged to evidenced SoT hub.

    Returns None if fewer than 2 nodes after merge.
    """
    g = _TopoGraph()
    _add_uniqueness_subgraph(g, ops)
    _add_hardware_map(g, ops)
    _add_boards_legs(g, ops)
    _add_doctor_box_nodes(g, ops)
    _add_wave_evidence_nodes(g, ops)
    _add_registry_live_organs(g, ops)
    return g.adjacency()


def read_topology_meta(ops: Optional[Path] = None) -> dict:
    """Diagnostic metadata for evidence packs (read-only)."""
    g = _TopoGraph()
    _add_uniqueness_subgraph(g, ops)
    _add_hardware_map(g, ops)
    _add_boards_legs(g, ops)
    _add_doctor_box_nodes(g, ops)
    _add_wave_evidence_nodes(g, ops)
    _add_registry_live_organs(g, ops)
    A = g.adjacency()
    return {
        "n_nodes": g.n_nodes,
        "n_edges": g.n_edges,
        "nodes": g.node_names,
        "has_adjacency": A is not None,
        "sources_probed": {
            "uniqueness": bool(read_uniqueness_receipts(ops)),
            "hardware_pointer": hardware_pointer_path(ops).is_file(),
            "boards_legs_map": boards_legs_map_path(ops).is_file(),
            "doctor_box_latest": doctor_box_latest_path(ops).is_file(),
            "registry_latest": registry_latest_path(ops).is_file(),
        },
    }


def read_self_vs_twin(ops: Optional[Path] = None) -> Optional[dict]:
    """Paired errors for SOG from self_accuracy + self_audit tally.

    FUNCTIONAL only — not a consciousness / phenomenal claim.
    """
    err_self: list[float] = []
    err_other: list[float] = []

    for rec in read_self_accuracy(ops):
        try:
            acc = float(rec.get("accuracy"))
        except (TypeError, ValueError):
            continue
        acc = max(0.0, min(1.0, acc))
        err_self.append(1.0 - acc)
        # twin: constant 0.5 accuracy baseline (uninformed)
        err_other.append(0.5)

    audit = read_self_audit(ops)
    if audit:
        tally = audit.get("tally") if isinstance(audit.get("tally"), dict) else {}
        n = int(audit.get("n") or 0) or sum(int(v or 0) for v in tally.values())
        if n > 0:
            missing = int(tally.get("Missing") or 0)
            unknown = int(tally.get("Unknown") or 0)
            partial = int(tally.get("Partial") or 0)
            not_done = missing + unknown + partial
            err_self.append(not_done / float(n))
            # uninformed twin predicts nothing useful -> error 1.0
            err_other.append(1.0)

    if not err_self or not err_other:
        return None
    n = min(len(err_self), len(err_other))
    return {
        "err_self": err_self[:n],
        "err_other": err_other[:n],
        "note": (
            "FUNCTIONAL paired errors from self_accuracy + audit-matrix; "
            "NOT a consciousness claim."
        ),
    }


# Legacy path constants (relative); kept for docs/grep compatibility.
FITNESS_HISTORY = "state/fitness-history.json"
DEBATE_DIR = "debate"
TELEMETRY = "state/telemetry-latest.json"
RECONCILE_DIR = "reconcile"
DOCTOR_DIR = "doctor"
