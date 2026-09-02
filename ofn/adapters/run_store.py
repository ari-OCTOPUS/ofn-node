"""run_store — append-only ledger of runs and their typed events.

The three promises the blueprint demands of P1, encoded structurally:

  append_only          — one JSONL file, opened in append mode; nothing
                         rewrites a line;
  append_after_close   — REJECTED with FailClosedError, including after a
                         store is reopened from disk;
  replay_produces_second_effect == false
                       — replay() is a read-only generator; it has no code
                         path that writes. Idempotency at create() collapses
                         duplicate submissions of the same envelope into the
                         SAME run (one RUN_CREATED), and a second BUDGET_DEBIT
                         against the same EXECUTION_RECEIPT is refused — one
                         verdict, one budget effect.

`create()` takes `halted` as an argument: the scheduler reads the halt flag
(kernel decision, adapter read) and passes the verdict in — the store stays
I/O-minimal and the kill switch stays outside it, readable by itself.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterator, List, Set

from ofn.kernel import events as ev
from ofn.kernel.envelope import RUN_ID_RE, TaskEnvelope
from ofn.kernel.errors import FailClosedError


class HaltActive(FailClosedError):
    """Raised when create() is called with the kill switch verdict 'halted'.
    Nothing is written — a refused start leaves no half-born run."""


class RunStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._log = self.root / "events.jsonl"
        self._seq = 0
        self._runs: Set[str] = set()
        self._closed: Dict[str, bool] = {}
        self._by_idem: Dict[str, str] = {}
        self._receipts: Set[str] = set()   # EXECUTION_RECEIPT event_ids
        self._receipt_run: Dict[str, str] = {}  # receipt event_id -> run_id
        self._debited: Set[str] = set()    # receipt event_ids already settled
        self._seen_kind_ref: Set[tuple] = set()  # (kind, ref) already appended
        self._load()

    # ── loading ─────────────────────────────────────────────────────────
    def _load(self) -> None:
        if not self._log.exists():
            return
        with self._log.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    # Fail-closed on a corrupt ledger: we do not skip what
                    # we cannot verify and pretend to know the state.
                    raise FailClosedError(
                        f"corrupt run store line {lineno} in {self._log}") from None
                self._seq += 1
                self._index(rec)

    def _index(self, rec: dict) -> None:
        run_id = rec["run_id"]
        if rec["kind"] == ev.RUN_CREATED:
            self._runs.add(run_id)
            self._by_idem[rec["payload"]["idempotency_key"]] = run_id
        elif rec["kind"] == ev.EXECUTION_RECEIPT:
            self._receipts.add(rec["event_id"])
            self._receipt_run[rec["event_id"]] = run_id
        elif rec["kind"] == ev.BUDGET_DEBIT:
            self._debited.add(rec["ref"])
        if rec.get("ref"):
            self._seen_kind_ref.add((rec["kind"], rec["ref"]))
        # Close is a state change, not a "ref-less event". A RUN_CLOSED that
        # carries a causal ref must still mark the run closed — otherwise
        # append-after-close is only structural for the no-ref happy path.
        if rec["kind"] == ev.RUN_CLOSED:
            self._closed[run_id] = True

    # ── writing ─────────────────────────────────────────────────────────
    def _append(self, rec: dict) -> dict:
        with self._log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        self._seq += 1
        self._index(rec)
        return rec

    @staticmethod
    def _mint_event_id() -> str:
        # The boundary mints randomness; adapters are the boundary.
        return "evt-" + os.urandom(8).hex()

    def create(self, envelope: TaskEnvelope, *, halted: bool = False,
               now_epoch_s: int = 0) -> str:
        if halted:
            raise HaltActive("kill_switch: run creation refused, nothing written")
        if not RUN_ID_RE.match(envelope.run_id or ""):
            raise FailClosedError(
                f"envelope run_id not boundary-minted: {envelope.run_id!r}")
        existing = self._by_idem.get(envelope.idempotency_key)
        if existing is not None:
            return existing  # idempotent create — no second RUN_CREATED
        self._append({
            "event_id": self._mint_event_id(),
            "seq": self._seq + 1,
            "kind": ev.RUN_CREATED,
            "run_id": envelope.run_id,
            "ts": now_epoch_s,
            "payload": {"goal": envelope.goal,
                        "risk_tier": envelope.risk_tier,
                        "authority_level": envelope.authority_level,
                        "idempotency_key": envelope.idempotency_key,
                        "acceptance_criteria_hash": envelope.acceptance_criteria_hash},
            "ref": None,
        })
        return envelope.run_id

    def append(self, event: dict, *, now_epoch_s: int | None = None) -> str:
        rec = dict(event)
        if now_epoch_s is not None:
            rec["ts"] = now_epoch_s
        run_id = rec.get("run_id")
        if run_id not in self._runs:
            raise FailClosedError(f"unknown run: {run_id!r}")
        if self._closed.get(run_id):
            raise FailClosedError(f"append_after_close REJECTED: {run_id!r}")
        if rec["kind"] == ev.RUN_CREATED:
            raise FailClosedError(
                "RUN_CREATED only via create() — the store is the minter's gate")
        if rec["kind"] == ev.RUN_REJECTED:
            raise FailClosedError("RUN_REJECTED is a refusal record, not a run event")
        if rec["kind"] == ev.BUDGET_DEBIT:
            ref = rec.get("ref")
            if ref not in self._receipts:
                raise FailClosedError(
                    f"BUDGET_DEBIT ref unknown receipt: {ref!r} — one verdict → "
                    "one budget effect starts with a real receipt")
            if self._receipt_run.get(ref) != run_id:
                raise FailClosedError(
                    f"cross-run collision: receipt {ref!r} belongs to run "
                    f"{self._receipt_run.get(ref)!r}, not {run_id!r}")
            if ref in self._debited:
                raise FailClosedError(
                    f"receipt {ref!r} already settled — refusing second budget effect")
        if rec.get("ref") and (rec["kind"], rec["ref"]) in self._seen_kind_ref:
            # Duplicate delivery of the same logical event: the second copy
            # is refused, not merged — one delivery, one effect. Events
            # without a ref are not distinguishable duplicates by design;
            # their idempotency rides on the envelope's idempotency_key.
            raise FailClosedError(
                f"duplicate event rejected: {rec['kind']} ref={rec['ref']!r} already recorded")
        rec["event_id"] = self._mint_event_id()
        rec["seq"] = self._seq + 1
        written = self._append(rec)
        return written["event_id"]

    def close(self, run_id: str, *, now_epoch_s: int) -> str:
        return self.append(
            ev.make_event(ev.RUN_CLOSED, run_id, now_epoch_s=now_epoch_s),
            now_epoch_s=now_epoch_s)

    # ── reading ─────────────────────────────────────────────────────────
    def events_for(self, run_id: str) -> List[dict]:
        return [r for r in self.replay() if r["run_id"] == run_id]

    def replay(self) -> Iterator[dict]:
        """Read-only by construction: this generator never opens the log
        for writing. Replay cannot produce a second effect because replay
        has no effect."""
        if not self._log.exists():
            return
        with self._log.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
