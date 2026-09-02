# Economic learning lane tests — the 15 owner-mandated scenarios (B4).
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ofn.learning import (  # noqa: E402
    ActionChainLinker, EconomicLearningLedger, ExperimentProposer,
    LessonExtractor, OutcomeScorer, ReceiptVerifier,
)
from ofn.learning.receipts import canonical_json, sha256_text  # noqa: E402
from ofn.learning.scorer import FORBIDDEN_OUTPUT_NAMES  # noqa: E402


def _receipt(pid="PAY-1", amount=120.0, currency="AUD",
             received_at="2026-09-02T03:00:00Z", payer="buyer", source="bank_export"):
    payload = {"payment_id": pid, "amount": amount, "currency": currency,
               "received_at": received_at, "payer": payer}
    return {**payload, "receipt_hash": sha256_text(
        "|".join(str(payload[k]) for k in ("payment_id", "amount", "currency",
                                           "received_at", "payer"))),
            "source": source}


def _events(*kinds):
    return [{"kind": k, "ref": f"ref-{k}", "at": "2026-09-01T12:00:00Z",
             "evidence": f"receipt:{k}"} for k in kinds]


def _chain_with(*kinds, campaign="PAINT-L5-001", lead="lead:1"):
    return ActionChainLinker().build(campaign, lead, _events(*kinds))


# ── 1. real payment with valid hash ─────────────────────────────────────────
def test_01_real_payment_with_valid_hash():
    r = _receipt()
    store = {"PAY-1": r}
    v = ReceiptVerifier(lambda pid: store.get(pid))
    claim = {"payment_id": "PAY-1", "amount": 120.0, "currency": "AUD",
             "received_at": "2026-09-02T03:00:00Z", "source": "campaign",
             "external_receipt_hash": r["receipt_hash"]}
    result = v.verify(claim)
    assert result.verification_status == "VERIFIED"
    assert result.source == "bank_export"           # independent source wins


# ── 2. payment claim without receipt ────────────────────────────────────────
def test_02_claim_without_receipt():
    v = ReceiptVerifier(lambda pid: None)
    result = v.verify({"payment_id": "PAY-X", "amount": 99.0, "source": "campaign"})
    assert result.verification_status == "UNVERIFIED_NO_RECEIPT"
    assert result.is_verified is False


# ── 3. tampered receipt ─────────────────────────────────────────────────────
def test_03_tampered_receipt():
    r = _receipt(amount=120.0)
    store = {"PAY-1": {**r, "amount": 999.0}}       # receipt diverges from claim
    v = ReceiptVerifier(lambda pid: store.get(pid))
    result = v.verify({"payment_id": "PAY-1", "amount": 120.0,
                       "external_receipt_hash": r["receipt_hash"]})
    assert result.verification_status == "TAMPERED"
    # and a wrong claimed hash vs receipt also tampers
    r2 = _receipt(pid="PAY-2")
    store2 = {"PAY-2": r2}
    v2 = ReceiptVerifier(lambda pid: store2.get(pid))
    out = v2.verify({"payment_id": "PAY-2", "external_receipt_hash": "deadbeef"})
    assert out.verification_status == "TAMPERED"


# ── 5. incomplete chain keeps UNKNOWN links ─────────────────────────────────
def test_05_incomplete_chain_keeps_unknown():
    chain = _chain_with("lead", "contact")
    assert chain.complete is False
    assert set(chain.unknown_links()) == {"response", "quote", "payment"}
    assert all(chain.links[k].status == "unknown" for k in chain.unknown_links())


def test_complete_chain():
    chain = _chain_with("lead", "contact", "response", "quote", "payment")
    assert chain.complete is True and chain.unknown_links() == []


# ── 6. zero payments ────────────────────────────────────────────────────────
def test_06_zero_payment_is_lesson_not_success():
    chain = _chain_with("lead", "contact")
    score = OutcomeScorer().score(chain, payment=None)
    assert score.level in ("NO_SIGNAL", "INFO_FAILURE")
    assert score.payment_received_verified is False
    lessons = LessonExtractor().extract(score, _events("lead", "contact"))
    assert len(lessons) == 1
    assert lessons[0].success is False
    assert "not success" in lessons[0].lesson
    assert lessons[0].status == "OPEN"              # stays OPEN


# ── 7. response without quote ───────────────────────────────────────────────
def test_07_response_without_quote():
    score = OutcomeScorer().score(_chain_with("lead", "contact", "response"))
    assert score.level == "RESPONSE_SIGNAL"
    assert score.payment_received_verified is False


# ── 8. quote without payment ────────────────────────────────────────────────
def test_08_quote_without_payment():
    score = OutcomeScorer().score(_chain_with("lead", "contact", "response", "quote"))
    assert score.level == "QUOTE_SIGNAL"
    assert score.payment_received_verified is False


# ── 9. payment without provable lead link ───────────────────────────────────
def test_09_payment_disconnected_from_lead():
    r = _receipt()
    v = ReceiptVerifier(lambda pid: {"PAY-9": r}.get(pid))
    out = v.verify({"payment_id": "PAY-9", "external_receipt_hash": r["receipt_hash"]},
                   linked_to_lead=False)
    assert out.verification_status == "DISCONNECTED"
    score = OutcomeScorer().score(_chain_with("lead", "contact"), payment=out)
    assert score.level != "VERIFIED_REVENUE"
    assert score.payment_received_verified is False


# ── 10. single sample → low confidence, no generalization ───────────────────
def test_10_single_sample_low_confidence():
    chain = _chain_with("lead", "contact", "response", "quote", "payment")
    r = _receipt()
    v = ReceiptVerifier(lambda pid: {"PAY-1": r}.get(pid))
    payment = v.verify({"payment_id": "PAY-1",
                        "external_receipt_hash": r["receipt_hash"]})
    score = OutcomeScorer().score(chain, payment)
    assert score.level == "VERIFIED_REVENUE"
    lesson = LessonExtractor().extract(score, _events("lead", "contact"))[0]
    assert lesson.confidence == "low" and lesson.sample_size == 1
    assert "CORRELATION ONLY" in lesson.lesson          # causation forbidden


# ── 11. counter-evidence mandatory field ────────────────────────────────────
def test_11_counter_evidence_present():
    chain = _chain_with("lead", "contact")
    score = OutcomeScorer().score(chain)
    ev = _events("lead", "contact") + [{"kind": "counter_evidence",
                                        "ref": "bounce:x"}]
    lesson = LessonExtractor().extract(score, ev)[0]
    assert any("bounce" in c for c in lesson.contradicting_evidence)
    # and with no counter evidence the field says so honestly
    plain = LessonExtractor().extract(score, _events("lead", "contact"))[0]
    assert plain.contradicting_evidence == ["none recorded"]


# ── 4 + 12. duplicates + rerun idempotency ──────────────────────────────────
def test_04_and_12_ledger_idempotent(tmp_path):
    led = EconomicLearningLedger(tmp_path / "led.jsonl")
    rec = {"record_id": "R-1", "kind": "score", "outcome": "RECORDED"}
    assert led.append(rec) == "appended"
    assert led.append(dict(rec)) == "duplicate-skipped"
    again = EconomicLearningLedger(tmp_path / "led.jsonl")     # rerun
    assert again.append(dict(rec)) == "duplicate-skipped"
    assert again.counts()["total"] == 1
    assert again.verify()["valid"]


# ── 13. crash recovery ──────────────────────────────────────────────────────
def test_13_crash_recovery_no_orphans(tmp_path):
    p = tmp_path / "led.jsonl"
    row = {"ts": "2026-09-02T00:00:00Z", "record_id": "R-2", "kind": "proposal"}
    row["line_sha256"] = sha256_text(canonical_json(row))     # no outcome = crashed
    p.write_text(canonical_json(row) + "\n", encoding="utf-8")
    led = EconomicLearningLedger(p)                            # load → recover
    assert led.orphans() == 0
    assert led.rows()[-1]["outcome"] == "ESCALATED_TO_OWNER"
    assert led.rows()[-1].get("outcome_note") == "recovered: interrupted_mid_flight"


# ── 14. sensitive proposal escalates to owner ───────────────────────────────
def test_14_sensitive_proposal_escalates():
    r = _receipt()
    chain = _chain_with("lead", "contact", "response", "quote", "payment")
    v = ReceiptVerifier(lambda pid: {"PAY-1": r}.get(pid))
    payment = v.verify({"payment_id": "PAY-1",
                        "external_receipt_hash": r["receipt_hash"]})
    score = OutcomeScorer().score(chain, payment)
    lesson = LessonExtractor().extract(score, _events("lead", "contact"))[0]
    # n=1 success → underpowered queue, not kernel
    prop = ExperimentProposer().propose_from_lesson(lesson)
    assert prop.outcome == "QUEUED_WITH_REASON"
    # vocabulary/kernel targets always escalate
    assert ExperimentProposer().decide_target("ofn/kernel/events.py") == "ESCALATED_TO_OWNER"
    assert ExperimentProposer().decide_target("ofn/learning/") == "PR_CREATED"


# ── 15. nothing ever yields send_authorized ─────────────────────────────────
def test_15_no_send_authorized_anywhere(tmp_path):
    # (a) the scorer refuses by design
    with pytest.raises(RuntimeError):
        OutcomeScorer().authorize()
    # (b) no module output may contain a forbidden effect name as a value/key
    chain = _chain_with("lead", "contact", "response", "quote", "payment")
    r = _receipt()
    v = ReceiptVerifier(lambda pid: {"PAY-1": r}.get(pid))
    payment = v.verify({"payment_id": "PAY-1",
                        "external_receipt_hash": r["receipt_hash"]})
    score = OutcomeScorer().score(chain, payment)
    lessons = LessonExtractor().extract(score, _events("lead", "contact"))
    props = [ExperimentProposer().propose_from_lesson(l) for l in lessons]
    led = EconomicLearningLedger(tmp_path / "x.jsonl")
    for l in lessons:
        led.append({"record_id": l.lesson_id, "kind": "lesson",
                    "outcome": "RECORDED"})
    blobs = [json.dumps([score.as_dict(), [l.as_dict() for l in lessons],
                         [p.__dict__ for p in props], led.rows()],
                        default=str)]
    for name in FORBIDDEN_OUTPUT_NAMES:
        assert f'"{name}"' not in " ".join(blobs), f"forbidden name leaked: {name}"
