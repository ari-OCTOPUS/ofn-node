"""Witness minting: same binding in, same id out, one line per request.

The witness file is evidence, so the properties under test are the ones
evidence needs. The id is a function of the inputs alone — no clock, no
counter — so the same run minted twice is the same request. Repeating a
mint appends nothing and returns the original record, timestamp and all.
The clock is injected, so a test can prove `created_at` came from the
caller and not from the machine.

And the pass types stay separate: minting records STRUCTURAL_PASS, full
stop. EXECUTABLE_PASS exists as a name so other code can reference it, but
this module has no path that writes it — an executable pass is the owner's
claim to make, not the witness's.
"""

import hashlib
import json
import os
import unittest

from ofn.adapters.witness_mint import (
    EXECUTABLE_PASS,
    PASS_TYPES,
    REQUESTS_FILENAME,
    SCHEMA_NAME,
    STRUCTURAL_PASS,
    mint_witness_request,
    request_id_for,
)
from tests.tmpdir import temp_dir

RUN = "run-138-1"
ARTIFACT = b"artifact bytes for the spine"
PAYLOAD = b"payload bytes for the spine"
POLICY = "policy-2026-08"
SCHEMA_V = "business_source.v1"
T1 = "2026-08-28T00:00:00Z"
T2 = "2026-08-28T01:00:00Z"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_request_id() -> str:
    material = "\x1f".join((RUN, sha(ARTIFACT), sha(PAYLOAD),
                            POLICY, SCHEMA_V))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class WitnessMintTests(unittest.TestCase):
    def setUp(self):
        self.state = temp_dir(self)
        self.state_file = os.path.join(self.state, REQUESTS_FILENAME)

    def mint(self, *, now=T1, state=None, artifact=ARTIFACT, payload=PAYLOAD):
        return mint_witness_request(RUN, artifact, payload, POLICY, SCHEMA_V,
                                    state or self.state, now_utc=now)

    def read_lines(self):
        # Skips unparseable lines the same way the minter does; the torn-
        # write test relies on both agreeing that junk is skippable.
        lines = []
        with open(self.state_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return lines

    def test_binding_recorded(self):
        out = self.mint()
        self.assertTrue(out["created"])
        self.assertEqual(out["schema"], SCHEMA_NAME)
        self.assertEqual(out["request_id"], expected_request_id())
        self.assertEqual(out["run_id"], RUN)
        self.assertEqual(out["artifact_sha256"], sha(ARTIFACT))
        self.assertEqual(out["payload_sha256"], sha(PAYLOAD))
        self.assertEqual(out["policy_version"], POLICY)
        self.assertEqual(out["schema_version"], SCHEMA_V)
        self.assertEqual(out["created_at"], T1)
        (line,) = self.read_lines()
        self.assertEqual(line["request_id"], out["request_id"])
        # The binding tuple, not the raw bytes, is what the file carries.
        raw = open(self.state_file, "rb").read()
        self.assertNotIn(ARTIFACT, raw)
        self.assertNotIn(PAYLOAD, raw)

    def test_request_id_is_deterministic_function_of_binding(self):
        # Any one input changing must change the id.
        base = request_id_for(RUN, ARTIFACT, PAYLOAD, POLICY, SCHEMA_V)
        self.assertNotEqual(base, request_id_for(
            "run-138-2", ARTIFACT, PAYLOAD, POLICY, SCHEMA_V))
        self.assertNotEqual(base, request_id_for(
            RUN, b"different", PAYLOAD, POLICY, SCHEMA_V))
        self.assertNotEqual(base, request_id_for(
            RUN, ARTIFACT, b"different", POLICY, SCHEMA_V))
        self.assertNotEqual(base, request_id_for(
            RUN, ARTIFACT, PAYLOAD, "policy-2027-01", SCHEMA_V))
        self.assertNotEqual(base, request_id_for(
            RUN, ARTIFACT, PAYLOAD, POLICY, "other.v2"))
        self.assertEqual(base, request_id_for(
            RUN, ARTIFACT, PAYLOAD, POLICY, SCHEMA_V))

    def test_duplicate_mint_is_idempotent(self):
        first = self.mint()
        second = self.mint(now=T2)     # even with a different clock
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertFalse(second["created"])
        # The original record is returned untouched — including created_at.
        self.assertEqual(second["created_at"], T1)
        self.assertEqual(len(self.read_lines()), 1)
        # No second file, and the one file has the one line.
        self.assertEqual(os.listdir(self.state), [REQUESTS_FILENAME])

    def test_clock_is_injectable(self):
        a = mint_witness_request(RUN, ARTIFACT, PAYLOAD, POLICY, SCHEMA_V,
                                 os.path.join(self.state, "a"),
                                 now_utc=T1)
        b = mint_witness_request(RUN, ARTIFACT, PAYLOAD, POLICY, SCHEMA_V,
                                 os.path.join(self.state, "b"),
                                 now_utc=T2)
        self.assertEqual(a["created_at"], T1)
        self.assertEqual(b["created_at"], T2)
        self.assertEqual(a["request_id"], b["request_id"])

    def test_structural_and_executable_stay_separate(self):
        self.assertIn(STRUCTURAL_PASS, PASS_TYPES)
        self.assertIn(EXECUTABLE_PASS, PASS_TYPES)
        self.assertNotEqual(STRUCTURAL_PASS, EXECUTABLE_PASS)
        out = self.mint()
        # What minting says: the artifact existed, bound to this run. Only.
        self.assertEqual(out["pass_type"], STRUCTURAL_PASS)
        (line,) = self.read_lines()
        self.assertEqual(line["pass_type"], STRUCTURAL_PASS)
        # And there is no executable/owner-approval field to fill in later.
        for key in line:
            self.assertNotIn("executable", key)
            self.assertNotIn("owner", key)
            self.assertNotIn("approval", key)

    def test_torn_prior_line_does_not_block_a_mint(self):
        # A fragment from a crash years ago, ending in a newline so the
        # next append starts a clean line — the only kind of torn write an
        # appender can coexist with.
        with open(self.state_file, "w", encoding="utf-8") as fh:
            fh.write('{"schema": "witness_request.v1", "request_i\n')
        out = self.mint()
        self.assertTrue(out["created"])
        # The fragment is still there, unrepaired — the log is append-only
        # — and the new record is one clean, parseable line after it.
        (line,) = self.read_lines()
        self.assertEqual(line["request_id"], out["request_id"])
        with open(self.state_file, encoding="utf-8") as fh:
            raw = fh.read()
        self.assertIn('"request_i\n', raw)
        self.assertEqual(raw.count("\n"), 2)


if __name__ == "__main__":
    unittest.main()
