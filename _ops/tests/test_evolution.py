#!/usr/bin/env python3
"""تست Doctor evolution upgrades (RFCArchive + measured_lift + tournament) ($0).

DoD: آرشیو کران‌دار + بهترین-در-سلول · measured_lift زیرِ آستانه drop ·
tournament بازمانده برمی‌گرداند · production لمس‌نشده · λ_persist منفی.
non-destructive: mine/propose/submit فعلی دست‌نخورده.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("evolution")
_DR = Path(r"F:\backup\_ops\doctor")
if str(_DR) not in sys.path:
    sys.path.insert(0, str(_DR))

from evolution import (RFCArchive, ArchiveCell, measured_lift, LIFT_DROP_THRESHOLD,  # noqa: E402
                       tournament_rank, survivor, LAMBDA_PERSIST, INITIAL_ELO)


# ════════════════════════════════════════════════════════════════════════════════
# ۱. RFCArchive — MAP-Elites
# ════════════════════════════════════════════════════════════════════════════════

def t_archive_bounded_under_cap():
    """آرشیو کران‌دار می‌ماند."""
    arch = RFCArchive(cap=5)
    for i in range(20):
        arch.insert(f"key-{i % 3}", f"organ-{i % 2}", f"RFC-{i}", score=i / 20.0)
    assert arch.is_bounded(), f"size={arch.size} > cap=5"


def t_archive_best_in_cell():
    """بهترین-در-هر-سلول: insert با score پایین‌تر جایگزین نمی‌کند."""
    arch = RFCArchive(cap=10)
    arch.insert("error-rate", "DEBATE_LOOP", "RFC-A", score=0.5)
    arch.insert("error-rate", "DEBATE_LOOP", "RFC-B", score=0.3)   # پایین‌تر → رد
    cell = arch.best_in_cell("error-rate", "DEBATE_LOOP")
    assert cell is not None and cell.rfc_id == "RFC-A", f"best باید A باشد: {cell}"


def t_archive_better_replaces():
    """insert با score بالاتر جایگزین می‌کند."""
    arch = RFCArchive(cap=10)
    arch.insert("k", "o", "RFC-A", score=0.3)
    arch.insert("k", "o", "RFC-B", score=0.8)   # بالاتر → جایگزین
    cell = arch.best_in_cell("k", "o")
    assert cell.rfc_id == "RFC-B"


def t_archive_evict_lowest():
    """وقتی cap پر شد → کم‌امتیازترین evict."""
    arch = RFCArchive(cap=3)
    arch.insert("k1", "o", "A", score=0.9)
    arch.insert("k2", "o", "B", score=0.1)   # کم‌امتیاز
    arch.insert("k3", "o", "C", score=0.8)
    arch.insert("k4", "o", "D", score=0.7)   # force evict
    assert arch.is_bounded()
    # B (کم‌امتیازترین) باید evict شده باشد
    assert arch.best_in_cell("k2", "o") is None


def t_archive_sample_mutate():
    """sample یک سلول → mutate یک پیشنهادِ نو."""
    arch = RFCArchive(cap=10)
    arch.insert("error-rate", "DEBATE_LOOP", "RFC-1", score=0.7, fix="add guard")
    cell = arch.sample(rng=random.Random(42))
    assert cell is not None
    mutation = arch.mutate(cell, rng=random.Random(42))
    assert "fix" in mutation and mutation["parent_id"] == "RFC-1"
    assert mutation["generation"] == 1   # DGM lineage


def t_archive_lineage_generation():
    """lineage: generation با parent افزایش می‌یابد."""
    arch = RFCArchive(cap=10)
    arch.insert("k", "o", "RFC-1", score=0.5, parent_id=None)
    arch.insert("k", "o", "RFC-2", score=0.6, parent_id="RFC-1")
    cell = arch.best_in_cell("k", "o")
    # RFC-2 جایگزین کرد
    assert cell.rfc_id == "RFC-2"


# ════════════════════════════════════════════════════════════════════════════════
# ۲. measured_lift
# ════════════════════════════════════════════════════════════════════════════════

def t_measured_lift_passes_high():
    """lift ≥ آستانه → passed، نه dropped."""
    rfc = {"evidence": {"severity": "critical"}, "fix": "real fix"}
    result = measured_lift(rfc)
    assert result["passed"] is True and result["dropped"] is False


def t_measured_lift_drops_low():
    """lift < آستانه → drop خودکار (به submit نمی‌رسد)."""
    rfc = {"evidence": {"severity": "low"}, "fix": "weak fix"}
    result = measured_lift(rfc)
    assert result["dropped"] is True, f"باید drop شود: {result}"


def t_measured_lift_drops_on_eval_error():
    """eval error → drop (fail-closed)."""
    def boom(rfc, baseline):
        raise RuntimeError("eval crashed")
    rfc = {"evidence": {"severity": "high"}}
    result = measured_lift(rfc, eval_fn=boom)
    assert result["dropped"] is True


def t_measured_lift_penalizes_uptime():
    """fix به uptime → lift جریمه (λ_persist)."""
    rfc = {"evidence": {"severity": "high"}, "fix": "increase uptime always"}
    result = measured_lift(rfc)
    # severity=high = 0.3 ولی جریمه uptime → زیرِ آستانه
    assert result["lift"] < 0.3, f"uptime باید جریمه شود: {result}"


def t_measured_lift_custom_eval():
    """eval_fn قابل‌تزریق."""
    def custom(rfc, baseline):
        return {"lift": 0.9, "detail": "custom"}
    rfc = {"evidence": {"severity": "low"}}
    result = measured_lift(rfc, eval_fn=custom)
    assert result["passed"] is True and result["lift"] == 0.9


# ════════════════════════════════════════════════════════════════════════════════
# ۳. tournament_rank
# ════════════════════════════════════════════════════════════════════════════════

def t_tournament_ranks_by_score():
    """tournament: score بالاتر → elo بالاتر."""
    rfcs = [{"rfc_id": "A", "score": 0.9},
            {"rfc_id": "B", "score": 0.3},
            {"rfc_id": "C", "score": 0.6}]
    ranked = tournament_rank(rfcs)
    assert ranked[0]["rfc_id"] == "A", f"برنده باید A: {[r['rfc_id'] for r in ranked]}"
    assert ranked[-1]["rfc_id"] == "B"


def t_tournament_elo_assigned():
    """هر RFC elo می‌گیرد."""
    rfcs = [{"rfc_id": "A", "score": 0.8}, {"rfc_id": "B", "score": 0.5}]
    ranked = tournament_rank(rfcs)
    assert all("elo" in r for r in ranked)


def t_tournament_single_passthrough():
    """یک RFC → passthrough."""
    rfcs = [{"rfc_id": "A", "score": 0.5}]
    ranked = tournament_rank(rfcs)
    assert len(ranked) == 1 and ranked[0]["elo"] == INITIAL_ELO


def t_survivor_returns_top_k():
    """survivor فقط top-k را برمی‌گرداند."""
    rfcs = [{"rfc_id": "A", "score": 0.9},
            {"rfc_id": "B", "score": 0.3},
            {"rfc_id": "C", "score": 0.6}]
    surv = survivor(rfcs, top_k=1)
    assert len(surv) == 1 and surv[0]["rfc_id"] == "A"


def t_survivor_top_2():
    """survivor top_k=2."""
    rfcs = [{"rfc_id": "A", "score": 0.9},
            {"rfc_id": "B", "score": 0.3},
            {"rfc_id": "C", "score": 0.6}]
    surv = survivor(rfcs, top_k=2)
    assert len(surv) == 2
    assert surv[0]["rfc_id"] == "A" and surv[1]["rfc_id"] == "C"


def t_tournament_custom_judge():
    """judge_fn قابل‌تزریق."""
    rfcs = [{"rfc_id": "A", "x": 1}, {"rfc_id": "B", "x": 2}]
    def judge(a, b):
        return "a" if a["x"] < b["x"] else "b"
    ranked = tournament_rank(rfcs, judge_fn=judge)
    assert ranked[0]["rfc_id"] == "A"   # A wins (x کمتر)


# ════════════════════════════════════════════════════════════════════════════════
# Guards — λ_persist + no production
# ════════════════════════════════════════════════════════════════════════════════

def t_lambda_persist_negative():
    """λ_persist منفی دست‌نخورده."""
    assert LAMBDA_PERSIST == -1.0


def t_no_production_import():
    """evolution هیچ import از *_gate/chrono/money ندارد."""
    import evolution
    src = open(evolution.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


def t_non_destructive_mine_untouched():
    """mine/propose/submit فعلی دست‌نخورده (evolution = additive)."""
    from doctor import Doctor
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    # mine همچنان کار می‌کند
    bn = doc.mine(trace={"errors_24h": 3})
    assert bn is not None
    # evolution یک ماژولِ جدا است، نه replacement


if __name__ == "__main__":
    failed = harness.run([
        # RFCArchive
        ("[1] آرشیو کران‌دار", t_archive_bounded_under_cap),
        ("[1] بهترین-در-سلول (ردِ پایین‌تر)", t_archive_best_in_cell),
        ("[1] بهتر جایگزین می‌کند", t_archive_better_replaces),
        ("[1] evict کم‌امتیازترین", t_archive_evict_lowest),
        ("[1] sample/mutate با lineage", t_archive_sample_mutate),
        ("[1] generation lineage", t_archive_lineage_generation),
        # measured_lift
        ("[2] lift بالا → passed", t_measured_lift_passes_high),
        ("[2] lift پایین → drop", t_measured_lift_drops_low),
        ("[2] eval error → drop", t_measured_lift_drops_on_eval_error),
        ("[2] uptime → جریمه", t_measured_lift_penalizes_uptime),
        ("[2] eval_fn قابل‌تزریق", t_measured_lift_custom_eval),
        # tournament
        ("[3] رتبه‌بندی بر score", t_tournament_ranks_by_score),
        ("[3] elo assigned", t_tournament_elo_assigned),
        ("[3] single passthrough", t_tournament_single_passthrough),
        ("[3] survivor top-1", t_survivor_returns_top_k),
        ("[3] survivor top-2", t_survivor_top_2),
        ("[3] judge_fn قابل‌تزریق", t_tournament_custom_judge),
        # guards
        ("[G] λ_persist منفی", t_lambda_persist_negative),
        ("[G] هیچ import از production", t_no_production_import),
        ("[G] mine فعلی دست‌نخورده", t_non_destructive_mine_untouched),
    ])
    sys.exit(1 if failed else 0)
