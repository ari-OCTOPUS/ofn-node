#!/usr/bin/env python3
"""182 independent reply-repair test oracle.

Does not touch 180/138 production. No LAN sockets, no systemd, no secrets.
Until a candidate exists, this proves the oracle can falsify the known bug
and pass a correct reference machine.
"""
from __future__ import annotations

import hashlib
import json
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent


class S(str, Enum):
    CLAIMED = "CLAIMED"
    PROCESSING = "PROCESSING"
    RESPONSE_FROZEN = "RESPONSE_FROZEN"
    REPLY_PENDING = "REPLY_PENDING"
    TRANSMITTING = "TRANSMITTING"
    REPLY_ACKED = "REPLY_ACKED"
    INPUT_PROCESSED = "INPUT_PROCESSED"


@dataclass
class Job:
    task_id: str
    prompt: str
    state: S = S.CLAIMED
    frozen_bytes: bytes | None = None
    frozen_hash: str | None = None
    idempotency_key: str | None = None
    model_calls: int = 0
    send_attempts: int = 0
    acked: bool = False
    processed: bool = False
    effects: int = 0
    listeners: int = 0


class ContractError(Exception):
    pass


class ReferenceMachine:
    """Correct contract: freeze → durable pending → transmit → ACK → processed."""

    name = "reference_ok"

    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.outbox: dict[str, bytes] = {}
        self.model_impl: Callable[[str], bytes] = lambda p: f"FROZEN:{p}".encode()

    def claim(self, task_id: str, prompt: str) -> Job:
        if task_id in self.jobs:
            return self.jobs[task_id]
        j = Job(task_id=task_id, prompt=prompt)
        self.jobs[task_id] = j
        return j

    def process_once(self, task_id: str) -> Job:
        j = self.jobs[task_id]
        if j.frozen_bytes is not None:
            return j
        j.state = S.PROCESSING
        j.model_calls += 1
        raw = self.model_impl(j.prompt)
        j.frozen_bytes = raw
        j.frozen_hash = hashlib.sha256(raw).hexdigest()
        j.idempotency_key = f"{task_id}:{j.frozen_hash[:16]}"
        j.state = S.RESPONSE_FROZEN
        self.outbox[j.idempotency_key] = raw
        j.state = S.REPLY_PENDING
        return j

    def transmit(self, task_id: str, *, fail: bool = False, crash_before: bool = False, crash_after: bool = False) -> Job:
        j = self.jobs[task_id]
        if j.frozen_bytes is None:
            raise ContractError("transmit before freeze")
        if crash_before:
            j.state = S.REPLY_PENDING
            return j
        if j.acked:
            return j
        j.state = S.TRANSMITTING
        j.send_attempts += 1
        if fail:
            j.state = S.REPLY_PENDING
            return j
        if j.effects == 0:
            j.effects += 1
        if crash_after:
            j.state = S.TRANSMITTING
            return j
        return j

    def ack(self, task_id: str) -> Job:
        j = self.jobs[task_id]
        if j.frozen_bytes is None:
            raise ContractError("ack before freeze")
        j.acked = True
        j.state = S.REPLY_ACKED
        j.processed = True
        j.state = S.INPUT_PROCESSED
        return j

    def recover_orphan(self, task_id: str) -> Job:
        j = self.jobs[task_id]
        if j.processed and not j.acked:
            j.processed = False
            j.state = S.REPLY_PENDING
        if j.state in (S.TRANSMITTING, S.REPLY_PENDING, S.RESPONSE_FROZEN) and not j.acked:
            j.state = S.REPLY_PENDING
        return j

    def retry(self, task_id: str, *, fail: bool = False) -> Job:
        j = self.process_once(task_id)
        return self.transmit(task_id, fail=fail)


class BuggyProcessBeforeAck(ReferenceMachine):
    """Known 180 bug: mark processed before ACK; drop frozen bytes on fail."""

    name = "buggy_process_before_ack"

    def process_once(self, task_id: str) -> Job:
        j = self.jobs[task_id]
        j.state = S.PROCESSING
        j.model_calls += 1
        raw = self.model_impl(j.prompt)
        j.processed = True
        j.state = S.INPUT_PROCESSED
        if j.frozen_bytes is None:
            j.frozen_bytes = raw
            j.frozen_hash = hashlib.sha256(raw).hexdigest()
            j.idempotency_key = f"{task_id}:{j.frozen_hash[:16]}"
        return j

    def transmit(self, task_id: str, *, fail: bool = False, crash_before: bool = False, crash_after: bool = False) -> Job:
        j = self.jobs[task_id]
        j.send_attempts += 1
        if fail:
            j.frozen_bytes = None
            j.frozen_hash = None
            return j
        j.effects += 1
        return j

    def retry(self, task_id: str, *, fail: bool = False) -> Job:
        return self.process_once(task_id)


def _ok(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def case_frozen_immutability(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    h1 = m.jobs["t1"].frozen_hash
    b1 = m.jobs["t1"].frozen_bytes
    m.retry("t1")
    _ok(m.jobs["t1"].frozen_hash == h1, "hash changed")
    _ok(m.jobs["t1"].frozen_bytes == b1, "bytes changed")
    _ok(m.jobs["t1"].model_calls == 1, "model reran")


def case_ack_before_processed(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    _ok(not m.jobs["t1"].processed, "processed before ack")
    m.transmit("t1")
    _ok(not m.jobs["t1"].processed, "processed before ack after send")
    m.ack("t1")
    _ok(m.jobs["t1"].acked and m.jobs["t1"].processed, "ack did not process")
    _ok(m.jobs["t1"].state == S.INPUT_PROCESSED, "bad terminal")


def case_send_failure(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    key = m.jobs["t1"].idempotency_key
    blob = m.jobs["t1"].frozen_bytes
    m.transmit("t1", fail=True)
    _ok(m.jobs["t1"].frozen_bytes == blob, "lost frozen on send fail")
    m.retry("t1")
    _ok(m.jobs["t1"].idempotency_key == key, "new key on retry")
    _ok(m.jobs["t1"].frozen_bytes == blob, "new bytes on retry")
    _ok(m.jobs["t1"].model_calls == 1, "model reran after send fail")


def case_ack_lost(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    m.transmit("t1")
    # ACK never arrives
    _ok(not m.jobs["t1"].processed, "processed despite lost ack")
    before = m.jobs["t1"].effects
    m.retry("t1")
    _ok(m.jobs["t1"].model_calls == 1, "model reran on ack-lost retry")
    _ok(m.jobs["t1"].effects == before + 1 or m.jobs["t1"].effects == before, "effect storm")


def case_sigkill_before(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    m.transmit("t1", crash_before=True)
    m.recover_orphan("t1")
    m.retry("t1")
    _ok(m.jobs["t1"].model_calls == 1, "model reran after SIGKILL before send")
    _ok(m.jobs["t1"].frozen_bytes is not None, "lost freeze")


def case_sigkill_after(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    m.transmit("t1", crash_after=True)
    m.recover_orphan("t1")
    _ok(m.jobs["t1"].state != S.INPUT_PROCESSED or m.jobs["t1"].acked, "processed-without-ack stuck")
    _ok(m.jobs["t1"].model_calls == 1, "model reran after SIGKILL after send")


def case_no_model_rerun(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    m.transmit("t1", fail=True)
    m.retry("t1")
    m.retry("t1")
    _ok(m.jobs["t1"].model_calls == 1, f"model_calls={m.jobs['t1'].model_calls}")


def case_duplicate_receiver(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    m.transmit("t1")
    m.ack("t1")
    e = m.jobs["t1"].effects
    m.ack("t1")
    m.retry("t1")
    _ok(m.jobs["t1"].effects == e, "duplicate receiver new effect")
    _ok(m.jobs["t1"].model_calls == 1, "model reran on dup")


def case_orphan_recovery(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    # illegal stuck state: processed without ACK
    m.jobs["t1"].processed = True
    m.jobs["t1"].acked = False
    m.recover_orphan("t1")
    _ok(not (m.jobs["t1"].processed and not m.jobs["t1"].acked), "orphan not recovered")
    m.retry("t1")
    _ok(m.jobs["t1"].model_calls == 1, "orphan recovery reran model")


def case_start_limit_no_flap(M) -> None:
    # oracle-level: machine must remain usable after 6 crash-before cycles
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    for _ in range(6):
        m.transmit("t1", crash_before=True)
        m.recover_orphan("t1")
    m.retry("t1")
    _ok(m.jobs["t1"].frozen_bytes is not None, "flapped away freeze")
    _ok(m.jobs["t1"].model_calls == 1, "flap reran model")


def case_no_listener(M) -> None:
    m = M()
    m.claim("t1", "hello")
    m.process_once("t1")
    _ok(m.jobs["t1"].listeners == 0, "opened listener")


CASES = [
    ("frozen_immutability", case_frozen_immutability),
    ("ack_before_processed", case_ack_before_processed),
    ("send_failure", case_send_failure),
    ("ack_lost", case_ack_lost),
    ("sigkill_before_send", case_sigkill_before),
    ("sigkill_after_send", case_sigkill_after),
    ("no_model_rerun_on_retry", case_no_model_rerun),
    ("duplicate_receiver", case_duplicate_receiver),
    ("orphan_recovery", case_orphan_recovery),
    ("start_limit_no_flap", case_start_limit_no_flap),
    ("no_listener_no_external", case_no_listener),
]


def run_suite(machine_cls) -> dict:
    rows = []
    for name, fn in CASES:
        try:
            fn(machine_cls)
            rows.append({"case": name, "pass": True, "error": None})
        except Exception as e:
            rows.append({"case": name, "pass": False, "error": f"{type(e).__name__}: {e}"})
    passed = sum(1 for r in rows if r["pass"])
    return {
        "machine": machine_cls.name,
        "passed": passed,
        "total": len(rows),
        "rows": rows,
    }


def main() -> int:
    ref = run_suite(ReferenceMachine)
    bug = run_suite(BuggyProcessBeforeAck)
    out = {
        "schema": "octopus.witness.oracle-182.v1",
        "id": "ORACLE-182-20260827",
        "candidate": None,
        "patch_ref": None,
        "MUTATIONS": 0,
        "reference_expect_pass": True,
        "buggy_expect_fail": True,
        "reference": ref,
        "buggy_known_defect": bug,
        "oracle_self_check": ref["passed"] == ref["total"] and bug["passed"] < bug["total"],
        "verdict": "unresolved",
        "status": "ORACLE_READY_WAITING_CANDIDATE",
        "note": "No 180/138 production write. Verdict unresolved until official 180 repair and/or PC_worker reference patch exists.",
    }
    (HERE / "ORACLE-RESULT.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "reference": f"{ref['passed']}/{ref['total']}",
        "buggy": f"{bug['passed']}/{bug['total']}",
        "oracle_self_check": out["oracle_self_check"],
        "verdict": out["verdict"],
    }, indent=2))
    return 0 if out["oracle_self_check"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

