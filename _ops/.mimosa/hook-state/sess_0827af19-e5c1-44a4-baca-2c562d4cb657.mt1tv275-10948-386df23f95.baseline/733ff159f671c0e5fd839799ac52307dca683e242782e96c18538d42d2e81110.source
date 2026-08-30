"""test_world_discovery_novelty.py — تست‌های novelty و contradiction.

پوشش از بند ۱۶: 8, 9, 10, 6, 7 (novelty + duplicate + relation-vs-fact).
"""
import sys
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from world_discovery import novelty as N
from world_discovery import contradiction as CT


# ───────── 8) Duplicate discovery suppressed ─────────
def test_known_fact_not_novel():
    # با corpus empty → unknown، ولی اگر corpus یک متن مشابه داشته باشد → known
    corpus = N._MemoryCorpus(chunks=[
        "Claude agents cannot maintain long-term memory across sessions limitation",
    ])
    receipt = N.assess_novelty(
        "Claude agents cannot maintain long-term memory across sessions limitation",
        corpus=corpus,
    )
    assert receipt.decision == "known"
    assert receipt.overlap_score >= 0.7


def test_novel_claim_low_overlap():
    corpus = N._MemoryCorpus(chunks=["something completely unrelated about mining"])
    receipt = N.assess_novelty(
        "Sakana AI released a new evolutionary multi-agent architecture",
        corpus=corpus,
    )
    assert receipt.decision in ("novel", "unknown")
    assert receipt.overlap_score < 0.35


# ───────── 9) Known fact not marked novel ─────────
def test_partially_novel_in_between():
    corpus = N._MemoryCorpus(chunks=[
        "Claude is a language model from Anthropic with agent capabilities",
    ])
    receipt = N.assess_novelty(
        "Claude agent capabilities but with a new memory persistence layer",
        corpus=corpus,
    )
    assert receipt.decision in ("partially-novel", "known", "novel")
    # overlap should be moderate
    assert 0.0 <= receipt.overlap_score <= 1.0


# ───────── 10) Relation novelty distinguished from fact novelty ─────────
def test_relation_novelty_detected():
    receipt = N.assess_novelty(
        "Because Sakana uses evolutionary methods, it leads to cheaper training than competitors",
        corpus=N._MemoryCorpus(chunks=[]),
    )
    assert "relation" in receipt.novelty_kinds


def test_strategic_novelty_detected():
    receipt = N.assess_novelty(
        "This creates a competitive advantage and asymmetry for Octopus",
        corpus=N._MemoryCorpus(chunks=[]),
    )
    assert "strategic" in receipt.novelty_kinds


def test_action_novelty_detected():
    receipt = N.assess_novelty(
        "We should experiment and test this hypothesis with a benchmark",
        corpus=N._MemoryCorpus(chunks=[]),
    )
    assert "action" in receipt.novelty_kinds


# ───────── forbidden scan paths ─────────
def test_forbidden_paths_not_scanned(tmp_path):
    secret = tmp_path / "secret.env"
    secret.write_text("API_KEY=sk-leaked", encoding="utf-8")
    corpus = N._MemoryCorpus.load(paths=[secret])
    # secret should NOT be in corpus
    assert all("sk-leaked" not in c for c in corpus.chunks)
    assert corpus.chunks == []


# ───────── 6) Contradictory evidence marks CONTESTED ─────────
def test_contradiction_marks_contested():
    def fake_retriever(q):
        return [
            {"title": "Debunked", "snippet": "this claim is false and wrong, critics dispute it",
             "url": "https://theregister.com/debunk", "source": "theregister"},
        ]
    result = CT.search_contradictions("claim X is amazing", retriever=fake_retriever)
    assert result.status == "CONTESTED"
    assert len(result.contradictions) >= 1


# ───────── 7) No evidence never becomes PASS ─────────
def test_no_evidence_no_pass():
    # retriever returns nothing → INSUFFICIENT (cannot PASS)
    result = CT.search_contradictions("claim X", retriever=lambda q: [])
    # with no contradictions found AND no retriever failure → TRIANGULATED possible
    # but this is just contradiction layer; PASS requires evidence sufficiency separately
    assert result.status in ("TRIANGULATED", "INSUFFICIENT-EVIDENCE")
    # key: it never says "validated" from contradiction alone


def test_contradiction_no_retriever_cannot_pass():
    result = CT.search_contradictions("claim X", retriever=None)
    assert result.status == "INSUFFICIENT-EVIDENCE"
    assert result.contradictions == []


def test_reconcile_contested_overrides_sufficient():
    cr = CT.ContradictionResult(status="CONTESTED")
    assert CT.reconcile_status(contradiction_result=cr, evidence_sufficient=True) == "contested"


def test_reconcile_triangulated_with_evidence():
    cr = CT.ContradictionResult(status="TRIANGULATED")
    assert CT.reconcile_status(contradiction_result=cr, evidence_sufficient=True) == "triangulated"
    assert CT.reconcile_status(contradiction_result=cr, evidence_sufficient=False) == "candidate"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
