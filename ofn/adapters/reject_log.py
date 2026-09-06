"""reject_log — append-only JSONL of RUN_REJECTED start refusals.

The run store refuses ``RUN_REJECTED`` (it is not a run event). This
adapter is the I/O body for that vocabulary slot: one refused start
produces one durable line, owner-private, fsynced. Replay is
read-only. Nothing here grants ``send_authorized``, ``quote_sent``,
or ``campaign_envelope_ready``.

The log is a side ledger. It never writes into ``events.jsonl``. A
recorded refusal does not burn the envelope's idempotency key.

HALT stops STARTS. Recording the refusal is the halt's witness, so
this log has no halt parameter of its own.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator, Optional

from ofn.kernel import events as ev
from ofn.kernel.errors import FailClosedError
from ofn.kernel.rejection import grants_send, make_rejection

SEND_OR_READY = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


class RejectLog:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        self._log = self.root / "refusals.jsonl"
        self._seq = 0
        self._ids: set[str] = set()
        self._expected_seq = 1
        self._load()

    def _refuse_nonregular_log(self) -> None:
        if self._log.is_symlink():
            raise FailClosedError(
                f"refusals.jsonl is a symlink at {self._log} — "
                "refusing write-through")
        if self._log.exists() and not self._log.is_file():
            raise FailClosedError(
                f"refusals.jsonl is not a regular file at {self._log}")

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
                        f"corrupt reject log line {lineno} in {self._log}"
                    ) from None
                self._require_record(rec, lineno=lineno)
                seq = rec.get("seq")
                if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
                    raise FailClosedError(
                        f"reject log line {lineno} missing or invalid seq")
                if seq != self._expected_seq:
                    raise FailClosedError(
                        f"seq gap at line {lineno}: expected "
                        f"{self._expected_seq}, got {seq!r}")
                self._expected_seq = seq + 1
                self._seq += 1
                eid = rec.get("refusal_id")
                if isinstance(eid, str) and eid.strip():
                    if eid in self._ids:
                        raise FailClosedError(
                            f"duplicate refusal_id: {eid!r}")
                    self._ids.add(eid)

    @staticmethod
    def _require_record(rec: object, *, lineno: int) -> None:
        if not isinstance(rec, dict):
            raise FailClosedError(
                f"reject log line {lineno} is not an object")
        kind = rec.get("kind")
        if kind != ev.RUN_REJECTED:
            raise FailClosedError(
                f"reject log line {lineno} is not RUN_REJECTED: {kind!r}")
        if kind in ev.FORBIDDEN_EFFECT_KINDS:
            raise FailClosedError(
                f"forbidden effect kind on reject log line {lineno}: {kind!r}")
        payload = rec.get("payload")
        if payload is not None:
            smuggled = ev.payload_forbidden_effect(payload)
            if smuggled is not None:
                raise FailClosedError(
                    f"payload smuggles forbidden effect name on line "
                    f"{lineno}: {smuggled!r}")

    def _mint_refusal_id(self) -> str:
        for _ in range(8):
            eid = "rej-" + os.urandom(8).hex()
            if eid not in self._ids:
                return eid
        raise FailClosedError("refusal_id mint exhausted — refusing a collision")

    def record(self, event: dict) -> str:
        """Append one RUN_REJECTED. Returns the minted refusal_id.

        The caller event is re-validated through ``make_rejection`` so a
        hand-built dict cannot smuggle a sealed name. Ready/authorized/
        sent names are refused. The run store is never opened.
        """
        if grants_send() is not False:
            raise FailClosedError("reject_log must not grant send")
        if not isinstance(event, dict):
            raise FailClosedError(f"rejection event must be a mapping: {event!r}")
        kind = event.get("kind")
        if kind is not None and kind != ev.RUN_REJECTED:
            raise FailClosedError(
                f"reject_log accepts only RUN_REJECTED, not {kind!r}")
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            raise FailClosedError(
                f"rejection payload must be a mapping: {payload!r}")
        checked = make_rejection(
            run_id=event.get("run_id") if isinstance(event.get("run_id"), str)
            else "",
            reason=payload.get("reason") if isinstance(payload.get("reason"), str)
            else "",
            now_epoch_s=event.get("ts") if isinstance(event.get("ts"), int)
            and not isinstance(event.get("ts"), bool) else 0,
            idempotency_key=(
                payload.get("idempotency_key")
                if isinstance(payload.get("idempotency_key"), str) else ""
            ),
        )
        blob = json.dumps(checked, ensure_ascii=False)
        if any(name in blob for name in SEND_OR_READY):
            raise FailClosedError(
                "rejection mentioned a send/ready state — "
                "this log does not grant send_authorized")
        self._refuse_nonregular_log()
        rec = {
            "refusal_id": self._mint_refusal_id(),
            "seq": self._seq + 1,
            "kind": checked["kind"],
            "run_id": checked["run_id"],
            "ts": checked["ts"],
            "payload": dict(checked["payload"]),
            "ref": checked.get("ref"),
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
        self._seq += 1
        self._ids.add(rec["refusal_id"])
        self._expected_seq = self._seq + 1
        return rec["refusal_id"]

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
                        f"corrupt reject log line {lineno} in {self._log}"
                    ) from None
                self._require_record(rec, lineno=lineno)
                seq = rec.get("seq")
                if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
                    raise FailClosedError(
                        f"reject log line {lineno} missing or invalid seq")
                if seq != expected_seq:
                    raise FailClosedError(
                        f"seq gap at line {lineno}: expected "
                        f"{expected_seq}, got {seq!r}")
                expected_seq = seq + 1
                yield rec

    def grants_send_payload(self, payload: Optional[dict] = None) -> bool:
        """A refusal stamp is never a send authorization. Structurally False."""
        if payload is not None:
            blob = json.dumps(payload, ensure_ascii=False)
            if any(name in blob for name in SEND_OR_READY):
                raise FailClosedError(
                    "rejection mentioned a send/ready state — "
                    "this log does not grant send_authorized")
        return False
