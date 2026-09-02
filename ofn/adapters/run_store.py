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

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

from ofn.kernel import events as ev
from ofn.kernel.envelope import RUN_ID_RE, TaskEnvelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.token_ceiling import per_run_fits, tokens_from_payload


class HaltActive(FailClosedError):
    """Raised when create() is called with the kill switch verdict 'halted'.
    Nothing is written — a refused start leaves no half-born run."""


class RunStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        # State dir is owner-private before the first line is written
        # (CLAUDE.md §7-الف). mkdir mode is umask-masked; chmod is the
        # second witness. POSIX-only; Windows has no equivalent bits.
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        self._log = self.root / "events.jsonl"
        self._seq = 0
        self._runs: Set[str] = set()
        self._closed: Dict[str, bool] = {}
        self._by_idem: Dict[str, str] = {}
        self._receipts: Set[str] = set()   # EXECUTION_RECEIPT event_ids
        self._receipt_run: Dict[str, str] = {}  # receipt event_id -> run_id
        self._debited: Set[str] = set()    # receipt event_ids already settled
        self._seen_kind_ref: Set[tuple] = set()  # (kind, ref) already appended
        self._budget_tokens: Dict[str, int] = {}   # run_id -> envelope cap
        self._tokens_consumed: Dict[str, int] = {}  # run_id -> spent
        self._event_ids: Set[str] = set()
        self._allowed_tools: Dict[str, Tuple[str, ...]] = {}
        self._expected_seq = 1
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
                self._require_record(rec, lineno=lineno)
                self._require_seq(rec, lineno=lineno)
                self._seq += 1
                self._index(rec)

    @staticmethod
    def _require_record(rec: object, *, lineno: int) -> None:
        """Schema gate shared by load, append, and replay.

        A JSON object missing `kind`/`run_id`, or carrying an unknown or
        forbidden kind, is not a ledger fact — KeyError is not a verdict.
        """
        if not isinstance(rec, dict):
            raise FailClosedError(
                f"run store line {lineno} is not an object")
        kind = rec.get("kind")
        if kind in ev.FORBIDDEN_EFFECT_KINDS:
            raise FailClosedError(
                f"forbidden effect kind on line {lineno}: {kind!r}")
        if kind not in ev.EVENT_KINDS:
            raise FailClosedError(
                f"unknown or missing event kind on line {lineno}: {kind!r}")
        run_id = rec.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            raise FailClosedError(
                f"run store line {lineno} missing run_id")
        eid = rec.get("event_id")
        if not isinstance(eid, str) or not eid.strip():
            raise FailClosedError(
                f"run store line {lineno} missing event_id")
        payload = rec.get("payload")
        if payload is not None:
            smuggled = ev.payload_forbidden_effect(payload)
            if smuggled is not None:
                raise FailClosedError(
                    f"payload smuggles forbidden effect name on line "
                    f"{lineno}: {smuggled!r}")

    def _require_seq(self, rec: dict, *, lineno: int) -> None:
        seq = rec.get("seq")
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
            raise FailClosedError(
                f"run store line {lineno} missing or invalid seq: {seq!r}")
        if seq != self._expected_seq:
            raise FailClosedError(
                f"seq gap or replay at line {lineno}: expected "
                f"{self._expected_seq}, got {seq!r}")
        self._expected_seq = seq + 1

    def _index(self, rec: dict) -> None:
        eid = rec.get("event_id")
        if isinstance(eid, str) and eid.strip():
            if eid in self._event_ids:
                raise FailClosedError(f"duplicate event_id: {eid!r}")
            self._event_ids.add(eid)
        run_id = rec["run_id"]
        if rec["kind"] != ev.RUN_CREATED and run_id not in self._runs:
            raise FailClosedError(
                f"event for unknown run on load: {run_id!r} kind={rec['kind']!r}")
        if rec["kind"] == ev.RUN_CREATED:
            if run_id in self._runs:
                raise FailClosedError(f"duplicate RUN_CREATED for {run_id!r}")
            self._runs.add(run_id)
            payload = rec.get("payload")
            if not isinstance(payload, dict):
                raise FailClosedError(
                    f"RUN_CREATED payload missing or not an object on {run_id!r}")
            try:
                self._by_idem[payload["idempotency_key"]] = run_id
            except KeyError:
                raise FailClosedError(
                    f"RUN_CREATED missing idempotency_key on {run_id!r}") from None
            cap = payload.get("budget_tokens", 0)
            if not isinstance(cap, int) or isinstance(cap, bool) or cap < 0:
                raise FailClosedError(
                    f"RUN_CREATED budget_tokens not a non-negative int: {cap!r}")
            self._budget_tokens[run_id] = cap
            self._tokens_consumed.setdefault(run_id, 0)
            tools = payload.get("allowed_tools", [])
            if tools is None:
                tools = []
            if not isinstance(tools, list):
                raise FailClosedError(
                    f"RUN_CREATED allowed_tools not a list on {run_id!r}")
            cleaned: List[str] = []
            for tool in tools:
                if not isinstance(tool, str) or not tool.strip():
                    raise FailClosedError(
                        f"RUN_CREATED allowed_tools entry not a name: {tool!r}")
                if ev.is_forbidden_effect_name(tool):
                    raise FailClosedError(
                        f"RUN_CREATED allowed_tools names a sealed effect: "
                        f"{tool!r}")
                cleaned.append(tool)
            self._allowed_tools[run_id] = tuple(cleaned)
        elif rec["kind"] == ev.EXECUTION_RECEIPT:
            eid = rec.get("event_id")
            if not isinstance(eid, str) or not eid.strip():
                raise FailClosedError(
                    f"EXECUTION_RECEIPT missing event_id on {run_id!r}")
            self._receipts.add(eid)
            self._receipt_run[eid] = run_id
        elif rec["kind"] == ev.BUDGET_DEBIT:
            ref = rec.get("ref")
            if not isinstance(ref, str) or not ref.strip():
                raise FailClosedError(
                    f"BUDGET_DEBIT missing ref on {run_id!r}")
            self._debited.add(ref)
            spent = tokens_from_payload(rec.get("payload"))
            self._tokens_consumed[run_id] = (
                self._tokens_consumed.get(run_id, 0) + spent)
        if rec.get("ref"):
            self._seen_kind_ref.add((rec["kind"], rec["ref"]))
        # Close is a state change, not a "ref-less event". A RUN_CLOSED that
        # carries a causal ref must still mark the run closed — otherwise
        # append-after-close is only structural for the no-ref happy path.
        if rec["kind"] == ev.RUN_CLOSED:
            self._closed[run_id] = True
        if rec["kind"] == ev.TOOL_INVOKED:
            payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
            tool = payload.get("tool")
            allow = self._allowed_tools.get(run_id, ())
            if ev.is_forbidden_effect_name(tool):
                raise FailClosedError(
                    f"TOOL_INVOKED names a sealed effect on {run_id!r}")
            if allow and (not isinstance(tool, str) or tool not in allow):
                raise FailClosedError(
                    f"TOOL_INVOKED tool {tool!r} not in allowlist on {run_id!r}")

    # ── writing ─────────────────────────────────────────────────────────
    def _append(self, rec: dict) -> dict:
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n"
        # Durable append: flush + fsync so a crash cannot silently drop
        # the last accepted event. Mode 0600 is the second witness that
        # the ledger is owner-private (root is already 0700).
        with self._log.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.chmod(self._log, 0o600)
        except OSError:
            pass
        self._seq += 1
        self._index(rec)
        return rec

    def _mint_event_id(self) -> str:
        # The boundary mints randomness; adapters are the boundary.
        # Collision against an already-indexed id is refused by reminting,
        # not by writing a duplicate identity.
        for _ in range(8):
            eid = "evt-" + os.urandom(8).hex()
            if eid not in self._event_ids:
                return eid
        raise FailClosedError("event_id mint exhausted — refusing a collision")

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
        payload = {
            "goal": envelope.goal,
            "risk_tier": envelope.risk_tier,
            "authority_level": envelope.authority_level,
            "idempotency_key": envelope.idempotency_key,
            "acceptance_criteria_hash": envelope.acceptance_criteria_hash,
            "budget_tokens": envelope.budget_tokens,
            "budget_aud_cents": envelope.budget_aud_cents,
            "deadline_iso": envelope.deadline_iso,
            "allowed_tools": list(envelope.allowed_tools),
            "parent_evidence": list(envelope.parent_evidence),
        }
        if envelope.rollback_ref:
            payload["rollback_ref"] = envelope.rollback_ref
        if envelope.rollback_plan:
            payload["rollback_plan"] = envelope.rollback_plan
        self._append({
            "event_id": self._mint_event_id(),
            "seq": self._seq + 1,
            "kind": ev.RUN_CREATED,
            "run_id": envelope.run_id,
            "ts": now_epoch_s,
            "payload": payload,
            "ref": None,
        })
        return envelope.run_id

    @staticmethod
    def _stamp_receipt_digest(payload) -> dict:
        """Bind an EXECUTION_RECEIPT to the hash of its caller payload.

        The digest is of the payload *without* ``receipt_sha256`` so a
        caller-supplied digest is a second witness, not a self-hash.
        Missing digest is stamped; a mismatch is refused.
        """
        if payload is None:
            incoming: dict = {}
        elif isinstance(payload, dict):
            incoming = dict(payload)
        else:
            raise FailClosedError(
                f"EXECUTION_RECEIPT payload must be a mapping: {payload!r}")
        claimed = incoming.pop("receipt_sha256", None)
        digest = hashlib.sha256(
            json.dumps(incoming, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if claimed is not None and claimed != digest:
            raise FailClosedError(
                "receipt_sha256 does not match payload — refusing forged digest")
        incoming["receipt_sha256"] = digest
        return incoming

    def append(self, event: dict, *, now_epoch_s: int | None = None) -> str:
        rec = dict(event)
        if now_epoch_s is not None:
            rec["ts"] = now_epoch_s
        kind = rec.get("kind")
        if kind in ev.FORBIDDEN_EFFECT_KINDS:
            raise FailClosedError(
                f"forbidden effect kind: {kind!r} — ready/authorized/sent "
                "are not ledger events")
        if kind not in ev.EVENT_KINDS:
            raise FailClosedError(f"unknown event kind: {kind!r}")
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
            request = tokens_from_payload(rec.get("payload"))
            already = self._tokens_consumed.get(run_id, 0)
            cap = self._budget_tokens.get(run_id, 0)
            if not per_run_fits(cap, already, request):
                raise FailClosedError(
                    f"per-run token ceiling: {already} + {request} > {cap} "
                    f"on {run_id!r} (0 budget authorizes no spend)")
        if rec.get("ref") and (rec["kind"], rec["ref"]) in self._seen_kind_ref:
            # Duplicate delivery of the same logical event: the second copy
            # is refused, not merged — one delivery, one effect. Events
            # without a ref are not distinguishable duplicates by design;
            # their idempotency rides on the envelope's idempotency_key.
            raise FailClosedError(
                f"duplicate event rejected: {rec['kind']} ref={rec['ref']!r} already recorded")
        payload = rec.get("payload")
        smuggled = ev.payload_forbidden_effect(
            payload if payload is not None else {})
        if smuggled is not None:
            raise FailClosedError(
                f"payload smuggles forbidden effect name {smuggled!r}")
        if rec["kind"] == ev.TOOL_INVOKED:
            allow = self._allowed_tools.get(run_id, ())
            tool = payload.get("tool") if isinstance(payload, dict) else None
            if ev.is_forbidden_effect_name(tool):
                raise FailClosedError(
                    f"TOOL_INVOKED cannot name a sealed effect: {tool!r}")
            if allow:
                if not isinstance(tool, str) or tool not in allow:
                    raise FailClosedError(
                        f"TOOL_INVOKED tool {tool!r} not in allowlist {allow!r}")
        if rec["kind"] == ev.EXECUTION_RECEIPT:
            rec["payload"] = self._stamp_receipt_digest(rec.get("payload"))
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
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    # Same fail-closed as _load: a corrupt line is not
                    # skipped, and JSONDecodeError is not leaked.
                    raise FailClosedError(
                        f"corrupt run store line {lineno} in {self._log}") from None
                self._require_record(rec, lineno=lineno)
                seq = rec.get("seq")
                if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
                    raise FailClosedError(
                        f"run store line {lineno} missing or invalid seq")
                yield rec
