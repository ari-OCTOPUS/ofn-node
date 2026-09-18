"""Contract fixtures are test-only; none represent actual leads or money."""
import hashlib
import json
import subprocess
import sys

import pytest

from ofn.adapters.receipt import stamp_receipt, verify_receipt
from ofn.adapters.revenue_run import GENESIS, STAGES, make_receipt, replay
from ofn.kernel.errors import FailClosedError


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


POLICY = sha("test-only policy")


def chain(leg="painting", mode="live_observation", count=9):
    records = []
    previous = GENESIS
    for index, stage in enumerate(STAGES[:count]):
        row = make_receipt(
            run_id="test-only-run", leg=leg, stage=stage,
            prev_receipt_sha=previous, policy_sha=POLICY,
            evidence_sha=sha("test-only evidence " + stage),
            producer_id="test-producer", recorded_at_epoch_s=index,
            mode=mode, witness_id="test-witness" if index == 8 else None,
            witness_receipt_sha=sha("test-only witness") if index == 8 else None,
        )
        records.append(row)
        previous = row["receipt_sha256"]
    return records


def restamp(row, **changes):
    body = {k: v for k, v in row.items() if k != "receipt_sha256"}
    body.update(changes)
    return stamp_receipt(body)


@pytest.mark.parametrize("leg", ["ziman", "painting", "studio"])
def test_all_legs_full_structural_replay_never_verifies_cash(leg):
    records = chain(leg)
    result = replay(records, expected_policy_sha=POLICY)
    assert result["chain_complete"] is True
    assert result["cash_verified"] is False
    assert result["may_authorize"] is False
    assert result["external_evidence_status"] == "UNVERIFIED"
    assert verify_receipt(records[-1]) == result["head_receipt_sha"]


def test_dry_run_prefix_stays_incomplete():
    result = replay(chain(mode="dry_run", count=4), expected_policy_sha=POLICY)
    assert result["last_stage"] == "offer_drafted"
    assert result["chain_complete"] is False


@pytest.mark.parametrize("changes", [
    {"run_id": "other-run"}, {"leg": "studio"}, {"mode": "dry_run"},
    {"policy_sha": sha("different policy")}, {"prev_receipt_sha": GENESIS},
    {"stage": "qualified"}, {"recorded_at_epoch_s": -1},
    {"recorded_at_epoch_s": True}, {"evidence_sha": GENESIS},
    {"schema": "revenue_run.v2"}, {"run_id": "raw personal data @ invalid"},
    {"leg": []}, {"stage": {}}, {"policy_sha": 1},
    {"witness_id": "inapplicable-witness"}, {"cash_verified": True},
])
def test_bad_fields_or_chain_bindings_fail_closed(changes):
    records = chain(count=2)
    records[1] = restamp(records[1], **changes)
    with pytest.raises(FailClosedError):
        replay(records, expected_policy_sha=POLICY)


@pytest.mark.parametrize("mutation", ["skip", "repeat", "reorder", "tamper", "reuse", "backwards"])
def test_chain_negative_cases(mutation):
    records = chain()
    if mutation == "skip":
        del records[1]
    elif mutation == "repeat":
        records.append(records[-1])
    elif mutation == "reorder":
        records[1], records[2] = records[2], records[1]
    elif mutation == "tamper":
        records[1]["producer_id"] = "mutated-without-restamping"
    elif mutation == "reuse":
        records[1] = restamp(records[1], evidence_sha=records[0]["evidence_sha"])
    elif mutation == "backwards":
        records[2] = restamp(records[2], recorded_at_epoch_s=0)
    with pytest.raises(FailClosedError):
        replay(records, expected_policy_sha=POLICY)


@pytest.mark.parametrize("changes", [
    {"mode": "dry_run"}, {"witness_id": None},
    {"witness_id": "test-producer"}, {"witness_receipt_sha": GENESIS},
    {"witness_receipt_sha": sha("test-only evidence settled_cash")},
])
def test_settlement_needs_live_observation_and_separate_witness(changes):
    records = chain()
    records[-1] = restamp(records[-1], **changes)
    with pytest.raises(FailClosedError):
        replay(records, expected_policy_sha=POLICY)


def test_missing_digest_and_empty_chain_rejected():
    records = chain(count=1)
    del records[0]["receipt_sha256"]
    for rows in (records, []):
        with pytest.raises(FailClosedError):
            replay(rows, expected_policy_sha=POLICY)


def test_independent_policy_is_required():
    with pytest.raises(FailClosedError):
        replay(chain(), expected_policy_sha=sha("unknown policy"))


@pytest.mark.parametrize("trailer", ["", "\n", "{invalid PRIVATE-MARKER}\n"])
def test_cli_reads_without_writing_and_never_skips_corruption(tmp_path, trailer):
    path = tmp_path / "test-only.jsonl"
    contents = "".join(json.dumps(row) + "\n" for row in chain(count=4)) + trailer
    path.write_text(contents, encoding="utf-8")
    before = path.read_bytes()
    result = subprocess.run(
        [sys.executable, "-m", "tools.replay_revenue_run", str(path),
         "--policy-sha", POLICY], capture_output=True, text=True, check=False,
    )
    assert path.read_bytes() == before
    assert "PRIVATE-MARKER" not in result.stderr
    if trailer:
        assert result.returncode == 2
        assert json.loads(result.stderr)["status"] == "INVALID"
    else:
        assert result.returncode == 0
        assert json.loads(result.stdout)["chain_complete"] is False
