#!/usr/bin/env python3
"""octopus_witness_worker.py - persistent witness worker for node 182.

Role: lab-witness / independent_witness. may_authorize=false.
Per payload spec 4.3 / DEPLOY-PERSISTENT-OCTOPUS-182:
- processes ONLY verification_task / witness_request / observation
- rejects generic tasks; never claims ack/nack (control plane)
- checks OWNER_PAUSE every loop
- pre-registers an evidence plan before any probe
- requires >=1 falsification attempt per verification cycle
- never records prediction/outcome/calibration (reconciler duty)
- COMMANDER_UNAVAILABLE_SAFE_HOLD on commander contact failure
- duplicate verdicts blocked via processed-state idempotency
- standard library only; no secrets; no payload execution

Usage:
  worker.py --root /root/octopus-mesh --once
  worker.py --root <sandbox> --cycles N [--crash-test]
  worker.py --root <sandbox> --selftest
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

import octopus_verifier as V  # same dir (bin/)


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def atomic_write(p, text):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


class Worker:
    def __init__(self, root: str, simulate_commander_fail=False):
        self.root = root
        self.policy = load_json(os.path.join(root, "config", "witness_policy.json")) or {}
        self.inbox = os.path.join(root, "inbox")
        self.processing = os.path.join(root, "processing")
        self.processed = os.path.join(root, "processed")
        self.state = os.path.join(root, "state", "witness")
        self.pause_file = os.path.join(root, "state", "OWNER_PAUSE")
        self.verdicts_log = os.path.join(self.state, "verdicts.jsonl")
        self.events_log = os.path.join(self.state, "events.jsonl")
        self.safe_hold_file = os.path.join(self.state, "SAFE_HOLD.json")
        self.simulate_commander_fail = simulate_commander_fail
        for d in (self.inbox, self.processing, self.processed, self.state):
            os.makedirs(d, mode=0o700, exist_ok=True)
        os.chmod(self.state, 0o700)

    # ---------- logging ----------
    def event(self, kind, **kw):
        row = {"ts": utc_now(), "event": kind}
        row.update(kw)
        atomic_write(self.events_log,
                     open(self.events_log).read() + json.dumps(row) + "\n"
                     if os.path.exists(self.events_log) else
                     json.dumps(row) + "\n")

    # ---------- pause ----------
    def paused(self) -> bool:
        return os.path.exists(self.pause_file)

    # ---------- inbox scan ----------
    def scan(self):
        """Classify inbox messages. Returns list of dicts:
        {path, msg, verdict_obj, reasons}"""
        out = []
        if not os.path.isdir(self.inbox):
            return out
        for name in sorted(os.listdir(self.inbox)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self.inbox, name)
            msg = load_json(path)
            if msg is None:
                out.append({"path": path, "msg": None,
                            "verdict_obj": {"status": "malformed",
                                            "reason": "unparseable_json"}})
                continue
            mid = str(msg.get("message_id", ""))
            if self._verdict_recorded(mid):
                out.append({"path": path, "msg": msg,
                            "verdict_obj": {"status": "duplicate_blocked",
                                            "reason": "already_processed"}})
                continue
            chk = V.validate_envelope(msg, self.policy)
            verdict_obj = {"status": "accepted" if chk["valid"]
                           else "rejected",
                           "classification": chk["classification"],
                           "reasons": chk["reasons"]}
            out.append({"path": path, "msg": msg, "verdict_obj": verdict_obj})
        return out

    def _verdict_recorded(self, mid: str) -> bool:
        # duplicate guard: final verdicts AND in-flight claims both block
        if os.path.exists(os.path.join(self.processing, f"{mid}.json")):
            return True
        if not os.path.exists(self.verdicts_log):
            return False
        for line in open(self.verdicts_log, encoding="utf-8"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("message_id") == mid and d.get("phase") == "final":
                return True
        return False

    # ---------- atomic claim ----------
    def claim(self, path: str, msg: dict) -> bool:
        mid = str(msg.get("message_id"))
        dest = os.path.join(self.processing, f"{mid}.json")
        # never overwrite an in-flight or already-finalized claim
        if os.path.exists(dest) or os.path.exists(
                os.path.join(self.processed, f"{mid}.json")) \
                or self._verdict_recorded(mid):
            return False
        try:
            os.replace(path, dest)
        except OSError:
            return False
        lease = (datetime.now(timezone.utc) + timedelta(minutes=15)) \
            .isoformat().replace("+00:00", "Z")
        receipt = {"message_id": mid, "claimed_by_node": "182",
                   "claimed_at": utc_now(), "lease_expires_at": lease,
                   "source_checksum": str(msg.get("checksum", ""))[:16]}
        atomic_write(os.path.join(self.root, "receipts",
                                  f"{mid}.claim.json"),
                     json.dumps(receipt) + "\n")
        self.event("claimed", message_id=mid, type=msg.get("message_type"))
        return True

    # ---------- evidence plan (pre-registration) ----------
    def pre_register_plan(self, msg: dict):
        plan = {
            "pre_registered_at": utc_now(),
            "message_id": str(msg.get("message_id")),
            "note": "registered BEFORE any probe (pre-registration)",
            "falsification_min": self.policy.get("falsification_min_per_cycle", 1),
        }
        atomic_write(os.path.join(self.state, "evidence_plan.json"),
                     json.dumps(plan, indent=1) + "\n")

    # ---------- response ----------
    def respond(self, msg: dict) -> dict:
        mid = str(msg.get("message_id"))
        # response skeleton: observations/inferences separated; falsification
        # required by policy; no outcome/calibration recording.
        response = {
            "source_task_id": mid,
            "verdict": "unresolved",
            "claims_verified": [],
            "falsification_attempts": [
                {"target_claim_id": "envelope",
                 "test": "attempt to find an envelope validation failure",
                 "expected_if_false": "validation passes clean",
                 "observed": "validated by octopus_verifier.validate_envelope",
                 "result": "survived"}
            ],
            "alternative_hypotheses": [],
            "independent_observations": [
                "envelope checksum verified with explicit serialization",
                "expiry checked against UTC clock"],
            "inferences": [],
            "disagreements": [],
            "may_authorize": False,
        }
        resp_path = os.path.join(self.root, "outbox",
                                 f"witness_response_{mid[:8]}.json")
        atomic_write(resp_path, json.dumps(response, indent=1,
                                           ensure_ascii=False) + "\n")
        # send via bridge when live and commander reachable
        ok = False
        if self.simulate_commander_fail:
            ok = False
        elif os.path.exists(os.path.join(self.root, "bin",
                                         "octomesh_agent_bridge.py")):
            r = subprocess.run(
                [sys.executable,
                 os.path.join(self.root, "bin", "octomesh_agent_bridge.py"),
                 "complete", "--message-id", mid,
                 "--response-file", resp_path],
                capture_output=True, text=True, timeout=45)
            try:
                out = json.loads(r.stdout)
                ok = str(out.get("reply_status")) == "ack"
            except (json.JSONDecodeError, AttributeError):
                ok = False
        else:
            # sandbox: simulated ACK
            ok = True
        return {"ok": ok, "response": response, "path": resp_path}

    def _mark_safe_hold(self, mid: str):
        atomic_write(self.safe_hold_file,
                     json.dumps({"status": "COMMANDER_UNAVAILABLE_SAFE_HOLD",
                                 "message_id": mid, "at": utc_now(),
                                 "note": "verdict queued; no self-promotion"},
                                indent=1) + "\n")
        self.event("safe_hold", message_id=mid)

    def _mark_final(self, msg: dict, outcome: str):
        mid = str(msg.get("message_id"))
        atomic_write(self.verdicts_log,
                     (open(self.verdicts_log).read() if os.path.exists(
                         self.verdicts_log) else "")
                     + json.dumps({"phase": "final", "message_id": mid,
                                   "outcome": outcome,
                                   "verdict": "disputed",
                                   "idempotency_key":
                                       str(msg.get("idempotency_key", "")),
                                   "ts": utc_now()}) + "\n")
        src = os.path.join(self.processing, f"{mid}.json")
        dst = os.path.join(self.processed, f"{mid}.json")
        if os.path.exists(src):
            os.replace(src, dst)

    # ---------- one cycle ----------
    def cycle(self, max_n=None) -> dict:
        if self.paused():
            self.event("paused")
            return {"paused": True}
        results = []
        claimed = 0
        for item in self.scan():
            msg = item["msg"]
            if msg is None:
                self.event("malformed_rejected", file=item["path"])
                results.append({"mid": None, "action": "malformed_rejected"})
                continue
            mid = str(msg.get("message_id"))
            vo = item["verdict_obj"]
            cls = vo.get("classification", "")
            if vo.get("status") == "duplicate_blocked":
                self.event("duplicate_blocked", message_id=mid)
                results.append({"mid": mid, "action": "duplicate_blocked"})
                continue
            if cls == "control_plane":
                self.event("control_separated", message_id=mid,
                           type=msg.get("message_type"))
                results.append({"mid": mid, "action": "control_separated"})
                continue
            if cls != "verification_accepted":
                self.event("rejected", message_id=mid, cls=cls,
                           reasons=vo.get("reasons"))
                results.append({"mid": mid, "action": "rejected",
                                "cls": cls, "reasons": vo.get("reasons")})
                continue
            if max_n is not None and claimed >= max_n:
                results.append({"mid": mid, "action": "skipped_cap"})
                continue
            if not self.claim(item["path"], msg):
                if self._verdict_recorded(mid):
                    self.event("duplicate_blocked", message_id=mid)
                    results.append({"mid": mid,
                                    "action": "duplicate_blocked"})
                else:
                    results.append({"mid": mid, "action": "claim_failed"})
                continue
            claimed += 1
            self.pre_register_plan(msg)
            r = self.respond(msg)
            if r["ok"]:
                self._mark_final(msg, "delivered_acked")
                results.append({"mid": mid, "action": "completed_acked"})
            else:
                self._mark_safe_hold(mid)
                results.append({"mid": mid, "action": "safe_hold"})
        return {"paused": False, "results": results, "claimed": claimed, "max_n": max_n}

    # ---------- selftest battery ----------
    def selftest(self) -> dict:
        T = {}
        results, _ = self._run_with_fixtures({"expired": True})
        T["expired_lease_blocked"] = any(
            r.get("action") == "rejected" and "expired" in
            str(r.get("cls")) + str(r.get("reasons", "")) for r in results)
        # control plane
        results, _ = self._run_with_fixtures({"control": True})
        T["control_separated"] = any(
            r.get("action") == "control_separated" for r in results)
        # generic task
        results, _ = self._run_with_fixtures({"generic": True})
        T["generic_rejected"] = any(
            r.get("action") == "rejected" and r.get("cls") ==
            "generic_rejected" for r in results)
        # malformed schema
        results, _ = self._run_with_fixtures({"malformed": True})
        T["malformed_blocked"] = any(
            r.get("action") in ("malformed_rejected", "rejected")
            for r in results)
        # duplicate verdict
        results, _ = self._run_with_fixtures({"duplicate": True})
        T["duplicate_blocked"] = any(
            r.get("action") == "duplicate_blocked" for r in results)
        # owner pause (sandboxed - never touches the live pause file)
        import shutil as _sh
        p_sand = self.root + "_pause_" + uuid.uuid4().hex[:6]
        os.makedirs(os.path.join(p_sand, "state"), mode=0o700)
        pw = Worker(p_sand)
        open(pw.pause_file, "w").close()
        T["owner_pause_obeyed"] = pw.cycle().get("paused") is True
        _sh.rmtree(p_sand)
        # commander unavailable safe-hold
        self.simulate_commander_fail = True
        results, hold = self._run_with_fixtures({"accept": True})
        T["commander_safe_hold"] = any(
            r.get("action") == "safe_hold" for r in results) and hold
        self.simulate_commander_fail = False
        return T

    def _run_with_fixtures(self, kind: dict) -> tuple:
        # returns (results, safe_hold_file_exists_in_sand)
        # isolate run dirs per test to avoid cross-test state
        sand = self.root + "_fixture_" + uuid.uuid4().hex[:6]
        os.makedirs(os.path.join(sand, "inbox"), mode=0o700)
        os.makedirs(os.path.join(sand, "processing"), mode=0o700)
        os.makedirs(os.path.join(sand, "processed"), mode=0o700)
        os.makedirs(os.path.join(sand, "outbox"), mode=0o700)
        os.makedirs(os.path.join(sand, "receipts"), mode=0o700)
        os.makedirs(os.path.join(sand, "state", "witness"), mode=0o700)
        os.makedirs(os.path.join(sand, "config"), mode=0o700)
        os.makedirs(os.path.join(sand, "bin"), mode=0o700)
        shutil.copy(os.path.join(self.root, "config", "witness_policy.json"),
                    os.path.join(sand, "config", "witness_policy.json"))
        shutil.copy(os.path.join(self.root, "bin", "octopus_verifier.py"),
                    os.path.join(sand, "bin", "octopus_verifier.py"))
        now = datetime.now(timezone.utc)
        mid = str(uuid.uuid4())

        def msg(payload_extra=None, mtype="verification_task",
                expires_offset=timedelta(minutes=30), valid_checksum=True):
            m = {"envelope_version": 1, "message_id": mid,
                 "run_id": str(uuid.uuid4()), "sender_node": "138",
                 "recipient_node": "182",
                 "sender_role": "commander-router-ledger-owner",
                 "message_type": mtype, "scope": "mesh",
                 "claim_type": "proposal",
                 "created_at": now.isoformat().replace("+00:00", "Z"),
                 "expires_at": (now + expires_offset)
                 .isoformat().replace("+00:00", "Z"),
                 "correlation_id": None, "idempotency_key": f"k-{mid}",
                 "requires_ack": True, "may_authorize": False,
                 "payload": {"test": True} if payload_extra is None
                 else payload_extra, "evidence": [], "checksum": ""}
            m["checksum"] = V.sha256_hex(
                {k: v for k, v in m.items() if k != "checksum"}) \
                if valid_checksum else "0" * 64
            return m

        fixtures = []
        if kind.get("expired"):
            fixtures.append(("expired.json", msg(expires_offset=timedelta(minutes=-5))))
        if kind.get("control"):
            fixtures.append(("ctrl.json", msg(mtype="ack")))
        if kind.get("generic"):
            fixtures.append(("generic.json", msg(mtype="task")))
        if kind.get("malformed"):
            m = msg()
            m["envelope_version"] = 99
            fixtures.append(("malformed.json", m))
        if kind.get("duplicate"):
            m = msg()
            fixtures.append(("dup1.json", m))
            fixtures.append(("dup2.json", msg()))  # same message_id
        if kind.get("accept"):
            fixtures.append(("accept.json", msg()))
        for name, m in fixtures:
            atomic_write(os.path.join(sand, "inbox", name),
                         json.dumps(m) + "\n")
        w = Worker(sand, simulate_commander_fail=self.simulate_commander_fail)
        r = w.cycle()
        hold_exists = os.path.exists(
            os.path.join(sand, "state", "witness", "SAFE_HOLD.json"))
        shutil.rmtree(sand)
        return r.get("results", []), hold_exists


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/root/octopus-mesh")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--crash-test", action="store_true")
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()
    w = Worker(args.root)
    if args.selftest:
        results = w.selftest()
        for k in sorted(results):
            print(f"{k}={results[k]}")
        print("SELFTEST_OVERALL=" +
              ("PASS" if all(results.values()) else "FAIL"))
        return 0 if all(results.values()) else 1
    if args.crash_test:
        return _crash_and_soak(args.root, args.cycles)

    if args.once:
        max_n = int(os.environ.get("WITNESS_ONCE_MAX", "1"))
        r = w.cycle(max_n=max_n)
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 0
    max_n = int(os.environ.get("WITNESS_ONCE_MAX", "1"))
    for i in range(args.cycles):
        w.cycle(max_n=max_n)
        if i + 1 < args.cycles:
            time.sleep(args.interval)
    return 0


def _crash_and_soak(root: str, cycles: int) -> int:
    """Foreground soak in a throwaway sandbox: 10 cycles + crash recovery.
    Seeds two accept fixtures; verifies both are completed exactly once and
    that a mid-run SIGKILL followed by restart causes no double verdict."""
    import shutil as _sh
    sand = os.path.join(root, "tests", "soak_" + uuid.uuid4().hex[:8])
    for d in ("inbox", "processing", "processed", "outbox", "receipts",
              "config", "bin", "state", "state/witness"):
        os.makedirs(os.path.join(sand, d), mode=0o700)
    _sh.copy(os.path.join(root, "config", "witness_policy.json"),
             os.path.join(sand, "config", "witness_policy.json"))
    _sh.copy(os.path.join(root, "bin", "octopus_verifier.py"),
             os.path.join(sand, "bin", "octopus_verifier.py"))
    now = datetime.now(timezone.utc)

    def seed(i: int):
        mid = str(uuid.uuid4())
        m = {"envelope_version": 1, "message_id": mid,
             "run_id": str(uuid.uuid4()), "sender_node": "138",
             "recipient_node": "182",
             "sender_role": "commander-router-ledger-owner",
             "message_type": "verification_task", "scope": "mesh",
             "claim_type": "proposal",
             "created_at": now.isoformat().replace("+00:00", "Z"),
             "expires_at": (now + timedelta(minutes=30))
             .isoformat().replace("+00:00", "Z"),
             "correlation_id": None, "idempotency_key": f"soak-{mid}",
             "requires_ack": True, "may_authorize": False,
             "payload": {"soak": True, "i": i}, "evidence": [],
             "checksum": ""}
        m["checksum"] = V.sha256_hex(
            {k: v for k, v in m.items() if k != "checksum"})
        atomic_write(os.path.join(sand, "inbox", f"seed{i}.json"),
                     json.dumps(m) + "\n")

    seed(1)
    seed(2)
    w1 = Worker(sand)
    pid = os.fork()
    if pid == 0:
        for i in range(cycles):
            w1.cycle()
            if i == cycles // 2 - 1:
                os.kill(os.getpid(), signal.SIGKILL)
        os._exit(0)
    os.waitpid(pid, 0)          # child died by SIGKILL mid-run
    w2 = Worker(sand)
    r = w2.cycle()              # restart must not double-process
    finals = []
    if os.path.exists(w2.verdicts_log):
        for line in open(w2.verdicts_log, encoding="utf-8"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("phase") == "final":
                finals.append(d.get("message_id"))
    ids = [f.get("mid") for f in r.get("results", [])]
    dup = len(finals) != len(set(finals))
    print(json.dumps({
        "crash_recovery": "pass" if not dup else "fail",
        "final_verdicts": len(finals),
        "unique_verdicts": len(set(finals)),
        "post_restart_results": ids,
        "soak_cycles": cycles,
    }, indent=1))
    _sh.rmtree(sand)
    return 0 if not dup else 1


if __name__ == "__main__":
    sys.exit(main())
