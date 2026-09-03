"""halt_log — append-only JSONL of HALT latch transitions.

The flag file is the live switch. This adapter is the I/O body for
the latch history: one assert or clear produces one durable line,
owner-private, fsynced. Replay is read-only. Nothing here grants
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.

The log is a side ledger. It never writes into ``events.jsonl`` and
it never calls ``write_halt`` / ``clear_halt``. A recorded transition
is not a run. Disagreement with the live flag is a visible fact
(``disagrees_with_flag``), not a silent overwrite.

HALT stops STARTS. Recording the switch's own transition is the
second witness, so this log has no halt parameter of its own.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator, Optional

from ofn.adapters import halt_flag
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt_latch import (
    HALT_ASSERTED,
    HALT_CLEARED,
    LatchIndex,
    grants_send,
    make_transition,
)

SEND_OR_READY = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


class HaltLog:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        self._log = self.root / "transitions.jsonl"
        self._seq = 0
        self._ids: set[str] = set()
        self._expected_seq = 1
        self._index = LatchIndex()
        self._load()

    def _refuse_nonregular_log(self) -> None:
        if self._log.is_symlink():
            raise FailClosedError(
                f"transitions.jsonl is a symlink at {self._log} — "
                "refusing write-through")
        if self._log.exists() and not self._log.is_file():
            raise FailClosedError(
                f"transitions.jsonl is not a regular file at {self._log}")

    def _load(self) -> None:
        if not self._log.exists():
            return
        self._refuse_nonregular_log()
        with self._log.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    raise FailClosedError(
                        f"corrupt halt log line {lineno} in {self._log}"
                    ) from None
                self._require_record(rec, lineno=lineno)
                seq = rec.get("seq")
                if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
                    raise FailClosedError(
                        f"halt log line {lineno} missing or invalid seq")
                if seq != self._expected_seq:
                    raise FailClosedError(
                        f"seq gap at line {lineno}: expected "
                        f"{self._expected_seq}, got {seq!r}")
                self._index.record({
                    "kind": rec["kind"],
                    "ts": rec["ts"],
                    "actor": rec["actor"],
                    "note": rec.get("note"),
                })
                self._expected_seq = seq + 1
                self._seq += 1
                tid = rec.get("transition_id")
                if isinstance(tid, str) and tid.strip():
                    if tid in self._ids:
                        raise FailClosedError(
                            f"duplicate transition_id: {tid!r}")
                    self._ids.add(tid)

    @staticmethod
    def _require_record(rec: object, *, lineno: int) -> None:
        if not isinstance(rec, dict):
            raise FailClosedError(
                f"halt log line {lineno} is not an object")
        kind = rec.get("kind")
        if kind not in (HALT_ASSERTED, HALT_CLEARED):
            raise FailClosedError(
                f"halt log line {lineno} is not a latch kind: {kind!r}")
        if kind in SEND_OR_READY:
            raise FailClosedError(
                f"forbidden effect kind on halt log line {lineno}: {kind!r}")
        blob = json.dumps(rec, ensure_ascii=False)
        if any(name in blob for name in SEND_OR_READY):
            raise FailClosedError(
                f"halt log line {lineno} mentioned a send/ready state")

    def _mint_transition_id(self) -> str:
        for _ in range(8):
            tid = "hlt-" + os.urandom(8).hex()
            if tid not in self._ids:
                return tid
        raise FailClosedError(
            "transition_id mint exhausted — refusing a collision")

    def armed(self) -> bool:
        return self._index.armed()

    def record(
        self,
        *,
        kind: str,
        now_epoch_s: int,
        actor: str,
        note: Optional[str] = None,
    ) -> str:
        """Append one latch transition. Returns the minted transition_id.

        The record is re-validated through ``make_transition`` so a
        hand-built dict cannot smuggle a sealed name. The live flag
        is not written. The run store is never opened.
        """
        if grants_send() is not False:
            raise FailClosedError("halt_log must not grant send")
        checked = make_transition(
            kind=kind, now_epoch_s=now_epoch_s, actor=actor, note=note,
        )
        blob = json.dumps(checked, ensure_ascii=False)
        if any(name in blob for name in SEND_OR_READY):
            raise FailClosedError(
                "latch transition mentioned a send/ready state — "
                "this log does not grant send_authorized")
        if not self._index.may_record(checked["kind"]):
            if checked["kind"] == HALT_ASSERTED:
                raise FailClosedError(
                    "HALT_ASSERTED while latch already armed — "
                    "missing HALT_CLEARED is a discrepancy, not a no-op")
            raise FailClosedError(
                "HALT_CLEARED while latch not armed — "
                "stray clear is not an owner decision")
        self._refuse_nonregular_log()
        rec = {
            "transition_id": self._mint_transition_id(),
            "seq": self._seq + 1,
            "kind": checked["kind"],
            "ts": checked["ts"],
            "actor": checked["actor"],
            "note": checked["note"],
        }
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n"
        with self._log.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.chmod(self._log, 0o600)
        except OSError:
            pass
        self._index.record({
            "kind": checked["kind"],
            "ts": checked["ts"],
            "actor": checked["actor"],
            "note": checked["note"],
        })
        self._seq += 1
        self._ids.add(rec["transition_id"])
        self._expected_seq = self._seq + 1
        return rec["transition_id"]

    def replay(self) -> Iterator[dict]:
        """Read-only by construction: never opens the log for writing."""
        if not self._log.exists():
            return
        self._refuse_nonregular_log()
        expected_seq = 1
        with self._log.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    raise FailClosedError(
                        f"corrupt halt log line {lineno} in {self._log}"
                    ) from None
                self._require_record(rec, lineno=lineno)
                seq = rec.get("seq")
                if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
                    raise FailClosedError(
                        f"halt log line {lineno} missing or invalid seq")
                if seq != expected_seq:
                    raise FailClosedError(
                        f"seq gap at line {lineno}: expected "
                        f"{expected_seq}, got {seq!r}")
                expected_seq = seq + 1
                yield rec

    def disagrees_with_flag(self, flag_path: Path) -> bool:
        """Compare this latch history to the live flag file.

        Two independent claims: the flag (I/O predicate) and the
        latch (this log). Disagreement is returned, not repaired.
        """
        flag_halted = halt_flag.halt_flag_active(flag_path)
        return self._index.disagrees_with_flag(flag_halted)

    def grants_send_payload(self, payload: Optional[dict] = None) -> bool:
        """A latch stamp is never a send authorization. Structurally False."""
        if payload is not None:
            blob = json.dumps(payload, ensure_ascii=False)
            if any(name in blob for name in SEND_OR_READY):
                raise FailClosedError(
                    "latch mentioned a send/ready state — "
                    "this log does not grant send_authorized")
        return False
