# -*- coding: utf-8 -*-
"""تست آفلاین turn_engine — بدون شبکه، بدون تلگرام، بدون خرج.
ماشین حالت کامل + اثبات READ_BACK_USED + BLOCK بدون call + partial-turn."""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import turn_engine as te  # noqa: E402


class FakeStore(te.MemoryStore):
    pass


def _engine(tmp_path, responses=None):
    store = FakeStore(tmp_path / "mem.jsonl")
    calls = []

    def model_fn(prompt, key):
        calls.append(prompt)
        return (responses or (lambda p: "پاسخ تستی"))(prompt)

    def send_fn(text):
        return {"ok": True, "message_id": 42}

    evid = tmp_path / "evid"
    eng = te.TurnEngine(store=store, model_fn=model_fn, send_fn=send_fn,
                        live_b_ok=lambda: True, warmup_turns=0,
                        evid_dir=evid)
    return eng, calls


def _states(t):
    return [s["state"] for s in t.states]


def test_full_state_machine_happy_path(tmp_path):
    eng, calls = _engine(tmp_path)
    t = eng.run_turn(1, 101, "سلام، وضع چطوره؟", "2026-08-20T06:00:00+00:00", "h1")
    assert "TELEGRAM_SENT" in _states(t) and "MEMORY_COMMITTED" in _states(t)
    assert "CONSOLIDATED" in _states(t)
    assert t.gate_mode == "ADVISORY" and calls, "باید مدل صدا زده شود"
    assert t.memory_commit_id.startswith("mem-")


def test_cross_turn_read_back_used(tmp_path):
    eng, calls = _engine(
        tmp_path, responses=lambda p: f"پاسخ + استفاده از {p.split()[-1]}" if "mem-" in p else "پاسخ")
    t1 = eng.run_turn(1, 101, "یادت باشه دمای مخزن ۷۰ بود", "2026-08-20T06:00:00+00:00", "h1")
    t2 = eng.run_turn(2, 102, "دمای مخزن چقدر بود؟", "2026-08-20T06:05:00+00:00", "h1")
    v = eng.learning_verdict(t1, t2)
    assert v == "READ_BACK_USED", f"got {v}; retrieved={t2.retrieved_ids}"


def test_block_no_model_call(tmp_path):
    store = FakeStore(tmp_path / "mem.jsonl")
    store.append("episodic", "x", "t0", provenance="")  # provenance ناقص
    calls = []

    def model_fn(p, k):
        calls.append(p)
        return "نباید بیاید"

    eng = te.TurnEngine(store=store, model_fn=model_fn,
                        send_fn=lambda t: {"ok": True, "message_id": 1},
                        live_b_ok=lambda: True, warmup_turns=0,
                        evid_dir=tmp_path / "evid")
    t = eng.run_turn(3, 103, "هرچی", "2026-08-20T06:10:00+00:00", "h")
    assert t.gate_mode == "BLOCK" and not calls, "BLOCK نباید مدل صدا بزند"
    assert "MODEL_INTENT_RECORDED" not in _states(t)


def test_send_fail_partial_turn(tmp_path):
    eng, _ = _engine(tmp_path)
    eng.send_fn = lambda t: {"ok": False}
    t = eng.run_turn(4, 104, "تست partial", "2026-08-20T06:15:00+00:00", "h")
    assert "SEND_FAILED" in _states(t)
    ledger = (eng.evid_dir / "TURN-LEDGER.jsonl").read_text(encoding="utf-8")
    assert "TURN_PARTIAL_OUTPUT_NOT_LEARNED" in ledger
    live = te.EVID / "TURN-LEDGER.jsonl"
    # Isolation: this test must not append to the live closed-loop evidence pack.
    if live.exists():
        assert str(eng.evid_dir.resolve()) != str(te.EVID.resolve())


def test_hcwm_not_decorative(tmp_path):
    eng, _ = _engine(tmp_path)
    ab = eng.hc_wm_ablation([])
    assert ab["decorative"] is False  # uncertainties همیشه متفاوت است


def test_footer_format(tmp_path):
    eng, _ = _engine(tmp_path)
    sent = []
    eng.send_fn = lambda text: (sent.append(text), {"ok": True, "message_id": 9})[1]
    eng.run_turn(5, 105, "تست فوتر", "2026-08-20T06:20:00+00:00", "h")
    assert "[ADVISORY · turn=" in sent[0] and "gate=" in sent[0]


def test_evid_dir_is_isolated(tmp_path):
    eng, _ = _engine(tmp_path)
    eng.send_fn = lambda text: {"ok": False}
    eng.run_turn(9, 109, "iso", "2026-08-20T06:30:00+00:00", "h")
    assert (eng.evid_dir / "TURN-LEDGER.jsonl").exists()
    assert eng.evid_dir.resolve() != te.EVID.resolve()
    assert eng.evid_dir.resolve().is_relative_to(tmp_path.resolve())
