#!/usr/bin/env python3
"""S1-PARALLEL-ATTACK-V1 / L-D witnesses 2+3 (sandbox, node 182, read-only for prod).

Witness-2 (exactly-once activation): reproduces the GAP-02 mechanism — a systemd
PathExists unit re-firing while the watched file exists — using a VOLATILE toy
unit pair under /run/systemd/system watching a sandbox dir. The service's action
mimics the patched apply script: classify then CONSUME (move the fixture away).
Expected: exactly 1 activation, 0 re-fires within the observation window.
Rollback: stop+rm the volatile units (gone on reboot anyway), delete sandbox.

Witness-3 (crash boundary): unit test of the REAL _consume_bundle() from the
LIVE apply_signed_inbound.py (imported as a module, INBOUND/CONSUMED constants
pointed at the sandbox):
  a) consumes an existing bundle dir exactly once (returns dest, source gone)
  b) idempotent on second call (source absent -> None, no crash)
  c) reversal path: move back restores the original tree byte-identically
  d) mid-move crash safety: shutil.move across same fs is rename(2) = atomic;
     verified by asserting no partial dest can exist for a same-fs move
     (documented property; no synthetic partial state is manufactured).

Production-signed fixture ceremony (real key over /var/lib/octopus/inbound)
remains PENDING an owner/laptop signature — registered, not blocking.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/opt/octopus/scripts")
import apply_signed_inbound as APPLY  # noqa: E402

SB = Path("/var/lib/octopus/state/s1pa-attack/w2w3")
TOY_PATH = "/run/systemd/system/s1pa-w2.path"
TOY_SVC = "/run/systemd/system/s1pa-w2.service"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), str(detail)[:200]))
    print("%-38s %-5s %s" % (name, "PASS" if ok else "FAIL", str(detail)[:120]))


def witness2_toy_path():
    inbound = SB / "inbound"
    consumed = SB / "consumed"
    reports = SB / "reports"
    for d in (inbound, consumed, reports):
        d.mkdir(parents=True, exist_ok=True)
    fixture = inbound / "FIXTURE.json.sig"
    fixture.write_text("TOY-SIGNED-FIXTURE")
    helper = SB / "toy-consume.sh"
    helper.write_text(
        "#!/bin/sh\n"
        "echo \"classified-$(date -u +%%Y%%m%%dT%%H%%M%%SZ)\" >> %s/runs.log\n"
        "mv %s %s/consumed-FIXTURE-$(date -u +%%Y%%m%%dT%%H%%M%%SZ)\n"
        % (reports, fixture, consumed))
    helper.chmod(0o755)
    # NOTE: no % specifiers inside the unit file itself (systemd expands them);
    # all logic lives in the helper script.
    Path(TOY_PATH).write_text(
        "[Unit]\nDescription=S1PA witness2 toy PathExists trigger\n"
        "[Path]\nPathExists=%s\nUnit=s1pa-w2.service\n[Install]\nWantedBy=multi-user.target\n" % fixture)
    Path(TOY_SVC).write_text(
        "[Unit]\nDescription=S1PA witness2 toy classify+consume\n"
        "[Service]\nType=oneshot\nExecStart=/bin/sh %s\n" % helper)
    subprocess.run(["systemctl", "daemon-reload"], check=True, timeout=30)
    subprocess.run(["systemctl", "start", "s1pa-w2.path"], check=True, timeout=30)
    # systemd path units poll ~ every 0.1-2s (default); watch for refires
    deadline = time.time() + 100
    while time.time() < deadline:
        if (reports / "runs.log").exists() and (reports / "runs.log").read_text().count("classified-") >= 1 and not fixture.exists():
            break
        time.sleep(2)
    time.sleep(30)  # refire observation window after consumption
    runs = 0
    if (reports / "runs.log").exists():
        runs = (reports / "runs.log").read_text().count("classified-")
    consumed_n = len(list(consumed.iterdir()))
    check("W2_exactly_one_activation", runs == 1, "runs=%d consumed=%d fixture_gone=%s" %
          (runs, consumed_n, not fixture.exists()))
    check("W2_no_refire_after_consume", runs == 1 and consumed_n == 1,
          "runs=%d consumed_entries=%d" % (runs, consumed_n))
    subprocess.run(["systemctl", "stop", "s1pa-w2.path"], timeout=30)
    for p in (TOY_PATH, TOY_SVC):
        try:
            Path(p).unlink()
        except OSError:
            pass
    subprocess.run(["systemctl", "daemon-reload"], check=True, timeout=30)
    return runs


def witness3_consume_unit():
    inbound = SB / "in3"
    consumed = SB / "co3"
    for d in (inbound, consumed):
        d.mkdir(parents=True, exist_ok=True)
    bundle = inbound / "SIGNED-TEST-BUNDLE"
    inner = bundle / "test.json.sig"
    bundle.mkdir(parents=True, exist_ok=True)
    inner.write_text('{"fixture":true}')
    APPLY.INBOUND = inbound
    APPLY.CONSUMED = consumed
    dest1 = APPLY._consume_bundle(bundle, "w3-test")
    check("W3a_consume_once", bool(dest1) and not bundle.exists() and
          (consumed / Path(dest1).name / "test.json.sig").read_text() == '{"fixture":true}',
          "dest=%s" % dest1)
    dest2 = APPLY._consume_bundle(bundle, "w3-test-again")
    check("W3b_idempotent_absent_source", dest2 is None, "second=%s" % dest2)
    # c) reversal restores byte-identical tree
    shutil.move(dest1, str(bundle))
    check("W3c_reversal_restores", bundle.is_dir() and inner.read_text() == '{"fixture":true}',
          "bundle back at %s" % bundle)
    # d) atomicity: same-filesystem move uses rename(2) — no partial state window.
    same_fs = bundle.stat().st_dev == consumed.stat().st_dev
    check("W3d_samefs_rename_atomic", same_fs, "st_dev equal=%s" % same_fs)


def main():
    if SB.exists():
        shutil.rmtree(str(SB))
    SB.mkdir(parents=True)
    w2_runs = witness2_toy_path()
    witness3_consume_unit()
    fails = [r for r in RESULTS if not r[1]]
    verdict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "witness": "2+3 sandbox",
               "passed": len(RESULTS) - len(fails), "total": len(RESULTS),
               "w2_runs": w2_runs,
               "pending_owner": "production-signed fixture over real inbound (signature ceremony)"}
    (SB / "W2W3-VERDICT.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
