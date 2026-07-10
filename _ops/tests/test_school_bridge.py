#!/usr/bin/env python3
"""تست school_bridge — پلِ afferent→School (یادگیری از کلاس + حافظه). $0 آفلاین.
یادگیری awareness را بالا می‌برد · حافظه (persist) بین‌اجراها می‌ماند · رویدادِ PII-رد یاد نمی‌شود ·
insight فقط propose-only (co-activation→پیشنهادِ یال، هرگز اعمالِ خودکار) · isolation."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("school-bridge")
_AFF = (harness.REAL_VAULT / r"_ops\afferent")
if str(_AFF) not in sys.path:
    sys.path.insert(0, str(_AFF))
from school_bridge import SchoolBridge  # noqa: E402
from sensory_bus import Observation, classify  # noqa: E402


def _market_events(n=3):
    """AfferentEventهای واقعی از classify (market → topic_ids)."""
    return [classify(Observation(source="crypto", obs_type="market",
                                 label=f"crypto snapshot {i}", intensity=0.6)) for i in range(n)]


def _tmp_state():
    return Path(tempfile.mkdtemp(prefix="school-")) / "aw.json"


def t_learning_raises_awareness():
    sb = SchoolBridge(state_path=_tmp_state())
    before = sb.field.mean_awareness()
    rep = sb.learn_from(_market_events(4))
    assert rep["taught_signals"] > 0, rep
    assert sb.field.mean_awareness() > before, (before, sb.field.mean_awareness())
    # topicِ market (C02) باید awareness گرفته باشد
    assert sb.awareness_of("C02") > 0.0, rep


def t_memory_persists_across_runs():
    sp = _tmp_state()
    sb1 = SchoolBridge(state_path=sp)
    sb1.learn_from(_market_events(4))
    a1 = sb1.awareness_of("C02")
    assert a1 > 0.0
    sb2 = SchoolBridge(state_path=sp)          # نمونهٔ نو، از دیسک بارگذاری = «یادش مانده»
    assert abs(sb2.awareness_of("C02") - a1) < 1e-6, (a1, sb2.awareness_of("C02"))


def t_pii_rejected_event_not_learned():
    from sensory_bus import AfferentEvent
    sb = SchoolBridge(state_path=_tmp_state())
    before = sb.field.mean_awareness()
    # رویدادِ afferent=False (شبیهِ لیبلِ PII که sensory_bus رد کرده)
    ev = AfferentEvent(source="x", obs_type="market", topic_ids=["C02"],
                       ledger_event_type="OBSERVE", intensity=0.9, afferent=False)
    rep = sb.learn_from([ev])
    assert rep["taught_signals"] == 0 and sb.field.mean_awareness() == before, rep


def t_insights_propose_only():
    sb = SchoolBridge(state_path=_tmp_state())
    # چند مشاهدهٔ پرشدت → co-activation → پیشنهادِ یال (نه اعمال)
    strong = _market_events(6)
    for _ in range(4):
        sb.learn_from(strong, persist=False)
    rep = sb.learn_from(strong, persist=False)
    for ins in rep["insights"]:
        # co-activation فقط propose_new_edge=True است — هیچ‌جا خودکار اعمال نمی‌شود
        assert ins["kind"] in ("topic-ignited", "structural-shift", "co-activation")
        if ins["kind"] == "co-activation":
            assert ins["propose_new_edge"] is True


def t_isolation_no_production_import():
    src = (_AFF / "school_bridge.py").read_text("utf-8")
    imports = " ".join(ln.strip() for ln in src.splitlines()
                       if ln.strip().startswith(("import ", "from ")))
    for forbidden in ("organ_gate", "money_gate", "budget_gate", "chrono",
                      "opslib", "unified_bus", "organism", "wiring"):
        assert forbidden not in imports, (forbidden, imports)


if __name__ == "__main__":
    failed = harness.run([
        ("یادگیری awareness را بالا می‌برد", t_learning_raises_awareness),
        ("حافظه بین‌اجراها می‌ماند (persist)", t_memory_persists_across_runs),
        ("رویدادِ PII-رد یاد نمی‌شود", t_pii_rejected_event_not_learned),
        ("insight فقط propose-only", t_insights_propose_only),
        ("isolation: بدونِ import production", t_isolation_no_production_import),
    ])
    sys.exit(1 if failed else 0)
