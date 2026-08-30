#!/usr/bin/env python3
"""test_epistemics_receipt_chain.py — ADR-039 Commit 2: tamper-evident receipt chain + provenance.

پوششِ تست‌های اجباریِ ADR §11 که C2 ممکنشان می‌کند:
  #9  زنجیرهٔ receipt با prev_hash غلط         → detect (chain_break)
  #10 write بیرونِ outputs/epistemics/          → refuse (path confinement)
  #12 نتیجه با seed/hash یکسان                 → replayable (byte-identical stores)
به‌علاوه: tamper detection، segment signing، classify_initiation (self/human/mixed).

سبکِ harness: هم‌الگو با test_epistemic_schemas.py (module-level FAILED + check()).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from epistemics.schemas import (  # noqa: E402
    BindHashes,
    EvidenceReceipt,
    GateDecision,
    GateOutcome,
    Initiator,
    ProvenanceEdge,
)
from epistemics.canonical import GENESIS, payload_hash  # noqa: E402
from epistemics.receipt_store import (  # noqa: E402
    ReceiptStore,
    sign_segment,
    verify_segment,
)
from epistemics.provenance import (  # noqa: E402
    ProvenanceWriter,
    classify_initiation,
    load_edges,
)

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if cond:
        print(f"  OK {name}")
    else:
        FAILED += 1
        print(f"  FAIL {name}: {detail}")


# ============================================================================
# builders
# ============================================================================
def _binds(**over) -> BindHashes:
    base = dict(
        git_sha="abc1234", material_hash="m" * 16, config_hash="c" * 16,
        environment_hash="e" * 16, seed_set_hash="s" * 16, command_hash="cmd" * 6,
        artifact_hashes={"out.jsonl": "a" * 16},
    )
    base.update(over)
    return BindHashes(**base)


def _receipt(parent_hash: str = GENESIS, **over) -> EvidenceReceipt:
    """receipt با canonical_payload_hashِ درستِ باز-محاسبه‌شده."""
    base = dict(
        receipt_id="R-1", plan_id="P-1", claim_id="CLM-1", binds=_binds(),
        parent_receipt_hash=parent_hash, produced_by="epistemic_sandbox_runner",
        produced_at="2026-08-13T00:00:00Z", verdict="pending",
        canonical_payload_hash="placeholder",
    )
    base.update(over)
    tmp = EvidenceReceipt(**base)
    base["canonical_payload_hash"] = payload_hash(tmp.model_dump(mode="json"))
    return EvidenceReceipt(**base)


def _edge(**over) -> ProvenanceEdge:
    base = dict(
        edge_id="E-1", claim_id="CLM-1", trigger_source="telemetry",
        initiator=Initiator.SELF,
    )
    base.update(over)
    return ProvenanceEdge(**base)


def _tmpstore(suffix: str = ".jsonl"):
    """یک مسیرِ tmp برای store (confine=False چون خارجِ _ops/epistemics است)."""
    d = Path(tempfile.mkdtemp(prefix="epi-c2-"))
    return d / f"store{suffix}"


# ============================================================================
# ReceiptStore — append + chain + tamper
# ============================================================================
def t_receipt_append_one_ok():
    p = _tmpstore()
    st = ReceiptStore(p, confine=False)
    st.append(_receipt(GENESIS))
    v = st.verify()
    check("append one receipt ok", v.ok and v.n_records == 1, v.reason)


def t_receipt_chain_two_linked():
    p = _tmpstore()
    st = ReceiptStore(p, confine=False)
    st.append(_receipt(GENESIS))
    tip = st.tip()
    st.append(_receipt(tip))           # parent = tipِ رکوردِ اول
    v = st.verify()
    check("two receipts linked ok", v.ok and v.n_records == 2, v.reason)


def t_receipt_wrong_parent_blocked():     # §11 #9
    p = _tmpstore()
    st = ReceiptStore(p, confine=False)
    st.append(_receipt(GENESIS))
    tip = st.tip()
    bad = _receipt("WRONG-PARENT")        # parent_receipt_hash != tip
    blocked = False
    try:
        st.append(bad)
    except ValueError:
        blocked = True
    check("wrong parent_receipt_hash blocked (§11 #9)", blocked, "expected ValueError")


def t_receipt_tamper_detected():
    p = _tmpstore()
    st = ReceiptStore(p, confine=False)
    st.append(_receipt(GENESIS, binds=_binds(git_sha="abc1234")))
    # محتوای receipt را در فایل دستکاری کن (بدونِ hash).
    txt = p.read_text(encoding="utf-8")
    txt = txt.replace("abc1234", "abc1235")   # git_sha عوض شد
    p.write_text(txt, encoding="utf-8")
    v = st.verify()
    check("content tamper detected", not v.ok and "hash_mismatch" in v.reason, v.reason)


def t_receipt_chain_break_detected():      # §11 #9 (linkage)
    p = _tmpstore()
    st = ReceiptStore(p, confine=False)
    st.append(_receipt(GENESIS))
    tip = st.tip()
    st.append(_receipt(tip))
    # prev_hashِ رکوردِ دوم را در فایل خراب کن.
    lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    import json as _json
    rec1 = _json.loads(lines[1])
    rec1["prev_hash"] = "TAMPERED-LINK"
    lines[1] = _json.dumps(rec1, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    v = st.verify()
    check("chain link tamper detected (§11 #9)", not v.ok and "chain_break" in v.reason, v.reason)


def t_receipt_replay_deterministic():      # §11 #12
    p1, p2 = _tmpstore(), _tmpstore()
    s1 = ReceiptStore(p1, confine=False)
    s2 = ReceiptStore(p2, confine=False)
    r1 = _receipt(GENESIS)
    s1.append(r1)
    s2.append(r1)
    t1 = s1.tip()
    r2 = _receipt(t1)
    s1.append(r2)
    s2.append(r2)
    check("replay byte-identical (§11 #12)",
          p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8"),
          "two stores with same inputs differ")


def t_receipt_path_confinement_refused():  # §11 #10
    evil = Path(tempfile.gettempdir()) / "epi-evil-outside.jsonl"
    refused = False
    try:
        ReceiptStore(evil, confine=True)        # خارجِ _ops/epistemics و outputs/epistemics
    except RuntimeError:
        refused = True
    check("out-of-bounds store path refused (§11 #10)", refused, "expected RuntimeError")
    if evil.exists():
        evil.unlink(missing_ok=True)


def t_receipt_decision_persisted_alongside():
    p = _tmpstore()
    st = ReceiptStore(p, confine=False)
    d = GateDecision(decision_id="D-1", receipt_id="R-1", claim_id="CLM-1",
                     outcome=GateOutcome.SUPPORTED, belief_delta_log_odds=1.2)
    st.append(_receipt(GENESIS), decision=d)
    import json as _json
    rec = _json.loads(p.read_text(encoding="utf-8").strip())
    check("decision persisted with receipt", rec.get("decision", {}).get("outcome") == "SUPPORTED")


# ============================================================================
# segment signing
# ============================================================================
def t_segment_sign_verify_ok():
    key = b"owner-segment-key"
    recs = [{"a": 1}, {"b": 2}]
    sig = sign_segment(recs, key)
    check("segment sign+verify ok", verify_segment(recs, key, sig))


def t_segment_tamper_detected():
    key = b"owner-segment-key"
    recs = [{"a": 1}]
    sig = sign_segment(recs, key)
    check("tampered segment rejected",
          not verify_segment([{"a": 2}], key, sig))


def t_segment_wrong_key_rejected():
    sig = sign_segment([{"a": 1}], b"key-A")
    check("wrong key rejected", not verify_segment([{"a": 1}], b"key-B", sig))


# ============================================================================
# ProvenanceWriter + classify_initiation
# ============================================================================
def t_provenance_append_edge_ok():
    p = _tmpstore()
    pw = ProvenanceWriter(p, confine=False)
    pw.append_edge(_edge())
    v = pw.verify()
    check("provenance append ok", v.ok and v.n_records == 1, v.reason)


def t_provenance_chain_two():
    p = _tmpstore()
    pw = ProvenanceWriter(p, confine=False)
    pw.append_edge(_edge(edge_id="E-1"))
    pw.append_edge(_edge(edge_id="E-2"))
    v = pw.verify()
    check("provenance two edges chained", v.ok and v.n_records == 2, v.reason)


def t_provenance_tamper_detected():
    p = _tmpstore()
    pw = ProvenanceWriter(p, confine=False)
    pw.append_edge(_edge(claim_id="CLM-1"))
    txt = p.read_text(encoding="utf-8").replace("CLM-1", "CLM-9")
    p.write_text(txt, encoding="utf-8")
    v = pw.verify()
    check("provenance tamper detected", not v.ok and "hash_mismatch" in v.reason, v.reason)


def t_classify_self_initiated():
    edges = [
        {"initiator": "self", "trigger_source": "telemetry"},
        {"initiator": "self", "trigger_source": "system"},
    ]
    check("classify self_initiated", classify_initiation(edges) == "self_initiated")


def t_classify_human_prompted():           # یالِ human ⇒ دیگر self-initiation نیست
    edges = [{"initiator": "human", "human_prompt_id": "HP-1", "trigger_source": "human_prompt"}]
    check("classify human_prompted", classify_initiation(edges) == "human_prompted")


def t_classify_mixed():
    edges = [
        {"initiator": "self", "trigger_source": "telemetry"},
        {"initiator": "human", "human_prompt_id": "HP-1", "trigger_source": "human_prompt"},
    ]
    check("classify mixed (honest label)", classify_initiation(edges) == "mixed")


def t_classify_human_prompt_id_alone_flags_human():
    # حتی اگر initiator=self، بودنِ human_prompt_id ⇒ human edge (ADR §2).
    edges = [{"initiator": "self", "human_prompt_id": "HP-1", "trigger_source": "telemetry"}]
    check("human_prompt_id flags human edge",
          classify_initiation(edges) in ("human_prompted", "mixed"))


def t_classify_empty_unknown():
    check("classify empty → unknown", classify_initiation([]) == "unknown")


def t_load_edges_roundtrip():
    p = _tmpstore()
    pw = ProvenanceWriter(p, confine=False)
    pw.append_edge(_edge(edge_id="E-1", claim_id="CLM-1"))
    pw.append_edge(_edge(edge_id="E-2", claim_id="CLM-2"))
    edges = load_edges(p)
    check("load_edges roundtrip", len(edges) == 2 and edges[0]["edge_id"] == "E-1"
          and edges[1]["edge_id"] == "E-2")


# ============================================================================
def main():
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            global FAILED
            FAILED += 1
            print(f"  CRASH {name}: {type(exc).__name__}: {exc}")
    total = len(tests)
    print(f"\n{'OK' if not FAILED else 'FAIL'} test_epistemics_receipt_chain: "
          f"{total - FAILED}/{total} (failed={FAILED})")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
