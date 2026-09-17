#!/usr/bin/env python3
"""Negative + positive test suite for the hardened mirror receiver v2 (182).

S1-PARALLEL-ATTACK-V1 lane L-A. Runs against a THROWAWAY home via
OCTOPUS_MIRROR_HOME — never touches /var/lib/mirror-138 production state.
Generates its own ed25519 test keypair; no real secrets involved.

Exit 0 only if every case passes.
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

RECEIVER = os.environ.get("RECEIVER_V2", "/var/lib/octopus/state/s1pa-attack/octopus-mirror-receive-v2")
POLICY_SPEC_JSON = (
    '{"allow":["api-budget/budget-ledger.jsonl","api-budget/config/<name>.json",'
    '"api-budget/config/<name>.jsonl","revenue-drive/season-meter.json"],'
    '"max_age_seconds":172800,"max_file_bytes":52428800,"max_files":64,'
    '"max_future_skew_seconds":900,"max_total_bytes":209715200,'
    '"mirror_id":"S1-MONEY-138-182","namespace":"octopus-mirror-manifest",'
    '"policy_version":"mirror-policy-v2-20260917","quarantine_cap_entries":100,'
    '"receipt_policy":"RECEIVED+HASH-MATCH ONLY; REPLAY-VALID NOT CLAIMED (S1-GAP-02C)",'
    '"replay_bridge":"FORBIDDEN"}'
)
POLICY_SHA = hashlib.sha256(POLICY_SPEC_JSON.encode()).hexdigest()
T = None
KEY = None
RESULTS = []


def now_iso(offset_s=0):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).strftime("%Y-%m-%dT%H:%M:%SZ")


def setup():
    global T, KEY
    T = Path(tempfile.mkdtemp(prefix="mirror-v2-test-"))
    KEY = T / "testkey"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(KEY)],
                   check=True, capture_output=True)
    trusted = T / "trusted"
    trusted.mkdir()
    pub = (T / "testkey.pub").read_text().split()
    (trusted / "allowed_signers").write_text("mirror-138 %s %s\n" % (pub[0], pub[1]))
    (T / "staging").mkdir()
    return T


def canonical_scope(files):
    canon = "".join("{} {}\n".format(f["path"], f["sha256"])
                    for f in sorted(files, key=lambda x: x["path"]))
    return hashlib.sha256(canon.encode()).hexdigest()


def build_manifest(files, seq=1, prev="GENESIS", sent_offset_s=0, **over):
    m = {
        "schema": "octopus-mirror-manifest.v1",
        "mirror_id": "S1-MONEY-138-182",
        "namespace": "octopus-mirror-manifest",
        "epoch": 1,
        "sequence": seq,
        "prev_manifest_sha256": prev,
        "sent_at_utc": now_iso(sent_offset_s),
        "sender": "node-138",
        "receiver": "node-182-witness",
        "scope_sha256": canonical_scope(files),
        "files_count": len(files),
        "policy_version": "mirror-policy-v2-20260917",
        "policy_sha256": POLICY_SHA,
        "files": files,
    }
    m.update(over)
    return m


_NONCE = [0]


def fresh_files():
    """Unique payload content per case — the receiver rejects duplicate SCOPE
    (same data re-pushed) per lane L-G order, so every case that must reach the
    ledger/sequence stage needs fresh bytes."""
    _NONCE[0] += 1
    tag = "n%d" % _NONCE[0]
    spec = [("api-budget/budget-ledger.jsonl", ('{"t":"%s"}\n' % tag).encode()),
            ("revenue-drive/season-meter.json", ('{"t":"%s"}\n' % tag).encode())]
    files = [{"path": r, "sha256": hashlib.sha256(c).hexdigest(), "bytes": len(c)}
             for r, c in spec]
    return spec, files


def make_files(spec=None):
    """spec: list of (relpath, content-bytes). Default healthy pair."""
    if spec is None:
        spec = [("api-budget/budget-ledger.jsonl", b'{"x":1}\n'),
                ("revenue-drive/season-meter.json", b'{"y":2}\n')]
    files = []
    for rel, content in spec:
        files.append({"path": rel, "sha256": hashlib.sha256(content).hexdigest(),
                      "bytes": len(content)})
    return spec, files


def make_tar(spec, manifest, sign=True, extra_members=(), tamper_manifest=False):
    d = T / "bundle"
    if d.exists():
        shutil.rmtree(str(d))
    payload = d / "payload"
    payload.mkdir(parents=True)
    for rel, content in spec:
        p = payload / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    mjson = json.dumps(manifest, indent=2) + "\n"
    (d / "manifest.json").write_text(mjson, encoding="utf-8")
    if sign:
        subprocess.run(["ssh-keygen", "-Y", "sign", "-q", "-f", str(KEY),
                        "-n", "octopus-mirror-manifest", str(d / "manifest.json")],
                       check=True, capture_output=True)
    if tamper_manifest:
        (d / "manifest.json").write_text(mjson.replace('"sequence"', '"sequence_x"'),
                                         encoding="utf-8")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        tf.add(str(payload), arcname="payload")  # ensure payload/ dir member exists even when empty
        for root, _dirs, fnames in os.walk(str(payload)):
            for fn in sorted(fnames):
                full = os.path.join(root, fn)
                tf.add(full, arcname="payload/" + os.path.relpath(full, str(payload)))
        tf.add(str(d / "manifest.json"), arcname="manifest.json")
        if (d / "manifest.json.sig").exists():
            tf.add(str(d / "manifest.json.sig"), arcname="manifest.json.sig")
        for arcname, target, kind in extra_members:
            ti = tarfile.TarInfo(arcname)
            if kind == "symlink":
                ti.type = tarfile.SYMTYPE
                ti.linkname = target
                tf.addfile(ti)
            elif kind == "file":
                ti.size = len(target)
                tf.addfile(ti, io.BytesIO(target))
    return buf.getvalue()


def run_receiver(tar_bytes, env_over=None):
    env = dict(os.environ)
    env["OCTOPUS_MIRROR_HOME"] = str(T)
    env.update(env_over or {})
    p = subprocess.run([sys.executable, RECEIVER], input=tar_bytes, capture_output=True,
                       env=env, timeout=60)
    try:
        out = json.loads(p.stdout.decode())
    except Exception:
        out = {"status": "NONJSON", "raw": p.stdout.decode(errors="replace")[:200],
               "stderr": p.stderr.decode(errors="replace")[:200]}
    return out


def current_ledger_seq():
    p = T / "state" / "ledger.json"
    if not p.is_file():
        return 0
    return json.loads(p.read_text())["sequence"]


def current_ledger_prev():
    p = T / "state" / "ledger.json"
    if not p.is_file():
        return "GENESIS"
    return json.loads(p.read_text())["last_manifest_sha256"]


def case(name, expect_status, expect_reason_prefix, tar_bytes, env_over=None):
    out = run_receiver(tar_bytes, env_over)
    ok = out.get("status") == expect_status and (
        expect_reason_prefix is None or str(out.get("reason", "")).startswith(expect_reason_prefix))
    RESULTS.append((name, ok, out.get("status"), out.get("reason", "")))
    print("%-34s %-5s got=%s reason=%s" % (name, "PASS" if ok else "FAIL",
                                           out.get("status"), out.get("reason", "")[:70]))


def main():
    setup()
    spec, files = make_files()

    # P1 happy path
    m = build_manifest(files, seq=1, prev="GENESIS")
    case("P1_happy", "RECEIVED+HASH-MATCH", None, make_tar(spec, m))
    assert current_ledger_seq() == 1, "ledger must advance to 1"
    prev1 = current_ledger_prev()

    # N1 exact-duplicate DATA under a fresh manifest (new timestamp, same scope)
    m_d = build_manifest(files, seq=1, prev="GENESIS", sent_offset_s=5)
    case("N1_duplicate_manifest", "REJECTED", "duplicate_manifest",
         make_tar(spec, m_d))

    # N2 duplicate filename within manifest
    files_dup = files + [dict(files[0])]
    m2 = build_manifest(files_dup, seq=2, prev=prev1)
    m2["scope_sha256"] = canonical_scope(files)  # honest scope, dup entries inside
    case("N2_duplicate_manifest_entry", "REJECTED", "duplicate_manifest_entry",
         make_tar(spec, m2))

    # N3 stale sequence (fresh data, same seq as ledger)
    spec3, files3 = fresh_files()
    m3 = build_manifest(files3, seq=1, prev=prev1, sent_offset_s=10)
    case("N3_sequence_stale", "REJECTED", "sequence_stale", make_tar(spec3, m3))

    # N4 sequence gap
    spec4, files4 = fresh_files()
    m4 = build_manifest(files4, seq=3, prev=prev1, sent_offset_s=10)
    case("N4_sequence_gap", "REJECTED", "sequence_gap", make_tar(spec4, m4))

    # N5 wrong prev hash
    spec5, files5 = fresh_files()
    m5 = build_manifest(files5, seq=2, prev="a" * 64, sent_offset_s=10)
    case("N5_prev_hash_mismatch", "REJECTED", "prev_hash_mismatch", make_tar(spec5, m5))

    # N6 symlink inside payload
    m6 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10)
    case("N6_symlink", "REJECTED", "symlink_rejected",
         make_tar(spec, m6, extra_members=[("payload/api-budget/evil", "../../etc/passwd", "symlink")]))

    # N7 extra file on disk not in manifest
    m7 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10)
    case("N7_file_not_in_manifest", "REJECTED", "file_not_in_manifest",
         make_tar(spec, m7, extra_members=[("payload/api-budget/config/ghost.json",
                                           b'{"ghost":true}', "file")]))

    # N8 traversal path in manifest
    files_trav = [{"path": "../evil.json", "sha256": hashlib.sha256(b"x").hexdigest(), "bytes": 1}]
    m8 = build_manifest(files_trav, seq=2, prev=prev1, sent_offset_s=10)
    case("N8_traversal", "REJECTED", "path_not_allowlisted", make_tar([], m8))

    # N9 absolute path in manifest
    files_abs = [{"path": "/etc/octopus/evil.json", "sha256": hashlib.sha256(b"x").hexdigest(), "bytes": 1}]
    m9 = build_manifest(files_abs, seq=2, prev=prev1, sent_offset_s=10)
    case("N9_absolute_path", "REJECTED", "path_not_allowlisted", make_tar([], m9))

    # N10 per-file size cap (env cap 1024)
    big = b"A" * 2048
    spec10 = [("api-budget/budget-ledger.jsonl", big)]
    files10 = [{"path": spec10[0][0], "sha256": hashlib.sha256(big).hexdigest(), "bytes": len(big)}]
    m10 = build_manifest(files10, seq=2, prev=prev1, sent_offset_s=10)
    case("N10_size_cap", "REJECTED", "size_cap_exceeded",
         make_tar(spec10, m10), env_over={"OCTOPUS_MIRROR_MAX_FILE": "1024"})

    # N11 total cap (env cap 2048, two files of 1.5k)
    c = b"B" * 1500
    spec11 = [("api-budget/budget-ledger.jsonl", c), ("revenue-drive/season-meter.json", c)]
    files11 = [{"path": r, "sha256": hashlib.sha256(c).hexdigest(), "bytes": len(c)}
               for r, _ in spec11]
    m11 = build_manifest(files11, seq=2, prev=prev1, sent_offset_s=10)
    case("N11_total_cap", "REJECTED", "total_cap_exceeded",
         make_tar(spec11, m11), env_over={"OCTOPUS_MIRROR_MAX_TOTAL": "2048"})

    # N12 stale manifest (3 days old)
    m12 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=-3 * 86400)
    case("N12_stale_manifest", "REJECTED", "stale_manifest", make_tar(spec, m12))

    # N13 future skew (1h ahead)
    m13 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=3600)
    case("N13_future_manifest", "REJECTED", "future_manifest", make_tar(spec, m13))

    # N14 tampered after signing
    m14 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10)
    case("N14_bad_signature", "REJECTED", "manifest_signature_invalid",
         make_tar(spec, m14, tamper_manifest=True))

    # N15 wrong policy version
    m15 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10,
                         policy_version="mirror-policy-v0-1999")
    case("N15_policy_version", "REJECTED", "policy_version_mismatch", make_tar(spec, m15))

    # N16 wrong mirror_id
    m16 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10,
                         mirror_id="S9-EVIL-138-182")
    case("N16_mirror_id", "REJECTED", "mirror_id_mismatch", make_tar(spec, m16))

    # N17 scope lie
    m17 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10,
                         scope_sha256="f" * 64)
    case("N17_scope_mismatch", "REJECTED", "scope_mismatch", make_tar(spec, m17))

    # N18 files_count lie
    m18 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10,
                         files_count=99)
    case("N18_files_count", "REJECTED", "files_count_mismatch", make_tar(spec, m18))

    # N19 count cap (env cap 2, manifest carries 3 by duplicating path variants)
    c3 = b'{"z":3}\n'
    spec19 = [("api-budget/budget-ledger.jsonl", c3),
              ("api-budget/config/a.json", c3),
              ("api-budget/config/b.jsonl", c3)]
    files19 = [{"path": r, "sha256": hashlib.sha256(c3).hexdigest(), "bytes": len(c3)}
               for r, _ in spec19]
    m19 = build_manifest(files19, seq=2, prev=prev1, sent_offset_s=10)
    case("N19_count_cap", "REJECTED", "count_cap_exceeded",
         make_tar(spec19, m19), env_over={"OCTOPUS_MIRROR_MAX_FILES": "2"})

    # N20 wrong sender identity
    m20 = build_manifest(files, seq=2, prev=prev1, sent_offset_s=10,
                         sender="node-999")
    case("N20_sender_identity", "REJECTED", "sender_identity_mismatch", make_tar(spec, m20))

    # N21 static no-replay-bridge: receiver must not reference sensorium/replay machinery
    src = Path(RECEIVER).read_text(encoding="utf-8")
    bad = [w for w in ("verify_sensorium", "octopus_sensorium", "/opt/octopus",
                       "events.jsonl", "jetstream") if w in src]
    ok21 = not bad
    RESULTS.append(("N21_no_replay_bridge", ok21,
                    "PASS" if ok21 else "FAIL", ",".join(bad)))
    print("%-34s %-5s found=%s" % ("N21_no_replay_bridge", "PASS" if ok21 else "FAIL",
                                   ",".join(bad) or "none"))

    # P2 second happy push chains correctly after all rejections (fresh data)
    prev_now = current_ledger_prev()
    spec22, files22 = fresh_files()
    m22 = build_manifest(files22, seq=2, prev=prev_now, sent_offset_s=10)
    case("P2_chain_continues", "RECEIVED+HASH-MATCH", None, make_tar(spec22, m22))
    assert current_ledger_seq() == 2, "ledger must advance to 2"

    fails = [r for r in RESULTS if not r[1]]
    print("\nSUMMARY: %d/%d passed" % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED CASES:", ", ".join(f[0] for f in fails))
        return 1
    return 0


if __name__ == "__main__":
    rc = main()
    if T is not None:
        shutil.rmtree(str(T), ignore_errors=True)
    sys.exit(rc)
