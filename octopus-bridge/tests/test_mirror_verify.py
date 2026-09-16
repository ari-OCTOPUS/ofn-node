#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic tests for A2-001 mirror_verify. Not registered in run_all.py."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from octopus_bridge.mirror_verify import (  # noqa: E402
    EXIT_MALFORMED,
    EXIT_MISMATCH,
    EXIT_PASS,
    canonical_dumps,
    main,
    sha256_bytes,
    sha256_file,
    verify,
)


def write_tree(base: Path, files: dict[str, bytes]) -> None:
    for rel, data in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def manifest_for(tree: Path, rels: list[str], denylist: list[str] | None = None) -> dict:
    entries = []
    for rel in rels:
        p = tree / rel
        entries.append({
            "relative_path": rel.replace("\\", "/"),
            "sha256": sha256_file(p),
            "size_bytes": p.stat().st_size,
            "algorithm": "sha256",
        })
    man = {"schema": "manifest.v1", "algorithm": "sha256", "entries": entries}
    if denylist is not None:
        man["denylist"] = denylist
    return man


def receipt(**kw) -> dict:
    base = {
        "receipt_id": "rcpt_1",
        "schema_version": "receipt.v1",
        "snapshot_id": "snap_ab",
        "manifest_hash": "a" * 64,
        "previous_receipt_hash": None,
        "observed_at": "2026-08-18T00:00:00Z",
        "observer_node": ".191",
        "result": "PASS",
        "report_hash": "b" * 64,
        "integrity_hint": "hash-chain-unkeyed",
    }
    base.update(kw)
    return base


class MirrorVerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="a2-001-"))
        self.tree = self.td / "tree"
        self.tree.mkdir()
        write_tree(self.tree, {
            "hello.txt": b"hello\n",
            "dir/n.txt": b"nested",
        })

    def tearDown(self) -> None:
        shutil.rmtree(self.td, ignore_errors=True)

    def test_golden_pass(self) -> None:
        man = manifest_for(self.tree, ["hello.txt", "dir/n.txt"])
        report = verify(self.tree, man)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["exit_code"], EXIT_PASS)
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["unexpected"], [])
        self.assertEqual(report["mismatches"], [])

    def test_one_byte_tamper(self) -> None:
        man = manifest_for(self.tree, ["hello.txt", "dir/n.txt"])
        (self.tree / "hello.txt").write_bytes(b"HELLO\n")
        report = verify(self.tree, man)
        self.assertEqual(report["result"], "MISMATCH")
        self.assertEqual(report["exit_code"], EXIT_MISMATCH)
        self.assertTrue(any(m["path"] == "hello.txt" for m in report["mismatches"]))

    def test_missing_file(self) -> None:
        man = manifest_for(self.tree, ["hello.txt", "dir/n.txt"])
        (self.tree / "dir" / "n.txt").unlink()
        report = verify(self.tree, man)
        self.assertEqual(report["missing"], ["dir/n.txt"])
        self.assertEqual(report["exit_code"], EXIT_MISMATCH)

    def test_unexpected_file(self) -> None:
        man = manifest_for(self.tree, ["hello.txt", "dir/n.txt"])
        (self.tree / "extra.txt").write_bytes(b"x")
        report = verify(self.tree, man)
        self.assertEqual(report["unexpected"], ["extra.txt"])
        self.assertEqual(report["exit_code"], EXIT_MISMATCH)

    def test_size_mismatch(self) -> None:
        man = manifest_for(self.tree, ["hello.txt"])
        man["entries"][0]["size_bytes"] = 999
        report = verify(self.tree, man)
        self.assertEqual(report["result"], "MISMATCH")
        self.assertTrue(report["mismatches"])

    def test_malformed_manifest(self) -> None:
        bad = self.td / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        out = self.td / "malformed-report.json"
        code = main([
            "verify", "--manifest", str(bad), "--tree", str(self.tree),
            "--out", str(out),
        ])
        self.assertEqual(code, EXIT_MALFORMED)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["result"], "MALFORMED")

    def test_replayed_receipt(self) -> None:
        man = manifest_for(self.tree, ["hello.txt", "dir/n.txt"])
        r1 = receipt(receipt_id="rcpt_dup")
        report = verify(self.tree, man, (r1, [r1]))
        self.assertIn("replayed-receipt:rcpt_dup", report["receipt_issues"])
        self.assertEqual(report["exit_code"], EXIT_MISMATCH)

    def test_out_of_order_receipt(self) -> None:
        man = manifest_for(self.tree, ["hello.txt", "dir/n.txt"])
        first = receipt(receipt_id="rcpt_a", previous_receipt_hash=None)
        h_first = sha256_bytes(canonical_dumps(first))
        second = receipt(
            receipt_id="rcpt_b",
            previous_receipt_hash="c" * 64,  # not h_first
            manifest_hash="d" * 64,
        )
        report = verify(self.tree, man, (second, [first]))
        self.assertTrue(any(x.startswith("out-of-order-receipt:") for x in report["receipt_issues"]))
        self.assertNotEqual(h_first, "c" * 64)

    def test_denylisted_path_exclusion(self) -> None:
        clean = self.td / "deny-tree"
        clean.mkdir()
        write_tree(clean, {"keep.txt": b"k", "secret.private.key": b"nope"})
        man = manifest_for(
            clean, ["keep.txt"],
            denylist=["*private*", "__pycache__/"],
        )
        report = verify(clean, man)
        self.assertEqual(report["result"], "PASS", report)
        self.assertNotIn("secret.private.key", report["unexpected"])

    def test_two_deterministic_runs(self) -> None:
        man = manifest_for(self.tree, ["hello.txt", "dir/n.txt"])
        a = verify(self.tree, man)
        b = verify(self.tree, man)
        self.assertEqual(a, b)
        self.assertEqual(a["report_hash"], b["report_hash"])
        body = {k: v for k, v in a.items() if k != "report_hash"}
        self.assertEqual(a["report_hash"], sha256_bytes(canonical_dumps(body)))


def main_mod() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MirrorVerifyTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main_mod())
