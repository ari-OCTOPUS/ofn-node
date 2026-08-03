#!/usr/bin/env python3
"""تستِ متابولیسمِ دادهٔ $0 پاها (2026-07-16): leg_cultivate + wiring.legs_cultivation_beat.

اثبات می‌کند:
  (الف) flag خاموش → None و صندوق‌ها بایت‌به‌بایت دست‌نخورده (رفتارِ امروز).
  (ب) flag روشن → صندوقِ ≥۲ پا (mining/crypto) هضم می‌شود؛ انتقال-نه-حذف + سایدکارِ
      نتیجه؛ سایدکارِ ORGANISM-STATE.legs_cultivation + گزارشِ دکتر نوشته می‌شوند.
  (ج) dedup: همان محتوا دوباره → duplicate، هیچ digestِ دوم (idempotent).
  (د) پیوندِ مغزِ B: digest → sensory_bus.ingest → school_bridge.learn_from(persist=True).
  (هـ) kill-switch (STOP) → None حتی با flag روشن.
  (و) cadence: beat غیرِ مضربِ N → None.
  (ز) دکتر گزارش را می‌بیند: پای گرسنه → کاندیدِ گلوگاهِ legs-starved (فقط اگر گزارش
      تازه باشد؛ کهنه → None)؛ بحران (error-rate) همچنان مقدم است.
  (ح) ساختاری: organism.py واقعاً beat را صدا می‌زند + کلیدِ merge + flag خارج از
      PAPER_FULL_FLAGS.
$0 آفلاین؛ state ایزوله (OPS_DIR موقتِ harness)؛ صفر نوشتن روی درختِ زنده.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("legs-cultivation")

_OPS = harness.SELF_OPS
for _p in [str(_OPS), str(_OPS / "legs"), str(_OPS / "doctor"), str(_OPS / "afferent")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import wiring          # noqa: E402
import leg_cultivate   # noqa: E402
from doctor import Doctor  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")
WIRING_SRC = (_OPS / "wiring.py").read_text("utf-8")

MINING_A = {"kind": "decision-batch", "label": "coordinator digest", "n_decisions": 3}
MINING_B = {"kind": "fleet-note", "label": "orange-pi uptime report", "n_nodes": 5}
CRYPTO_A = {"kind": "market-snapshot", "label": "btc-daily", "day": "2026-07-16"}


def _drop(leg: str, name: str, item: dict) -> Path:
    box = opslib.STATE_DIR / "legs" / f"{leg}-inbox"
    box.mkdir(parents=True, exist_ok=True)
    p = box / f"{name}.json"
    p.write_text(json.dumps(item, ensure_ascii=False), "utf-8")
    return p


def t_a_flag_off_is_noop():
    """flag خاموش → None؛ فایلِ صندوق دست‌نخورده."""
    os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)
    p = _drop("mining", "untouched", MINING_A)
    assert wiring.legs_cultivation_beat(beat=0) is None
    assert p.exists(), "flag خاموش نباید صندوق را لمس کند"
    p.unlink()   # پاکسازیِ fixtureِ تستی (state موقت، نه vault)


def t_b_digests_two_legs():
    """flag روشن: ۲ آیتمِ mining + ۱ آیتمِ crypto هضم؛ انتقال + سایدکار + گزارش."""
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    try:
        _drop("mining", "a-batch", MINING_A)
        _drop("mining", "b-fleet", MINING_B)
        _drop("crypto", "a-snap", CRYPTO_A)
        wiring._EPOCH_STATE.clear()   # epoch-gate: beat=60 = پنجرهٔ ۱ (شلیک)
        r = wiring.legs_cultivation_beat(beat=60)
        assert r is not None and r["propose_only"] is True, r
        assert r["legs"]["mining"]["digested"] == 2, r["legs"]["mining"]
        assert r["legs"]["crypto"]["digested"] == 1, r["legs"]["crypto"]
        assert r["digested_total"] == 3, r
        # همهٔ پاهای قرارداد حضور دارند (digestِ عمومی برای هر ۵ پا)
        assert set(r["legs"]) == set(leg_cultivate.CULTIVATED_LEGS), set(r["legs"])
        # فایل‌ها منتقل شدند (نه حذف) + سایدکارِ نتیجه
        box = opslib.STATE_DIR / "legs" / "mining-inbox"
        assert not list(box.glob("*.json")), "صندوقِ mining باید خالی شده باشد"
        allj = list((box / "processed").glob("*.json"))
        sides = [p for p in allj if p.name.endswith(".result.json")]
        moved = [p for p in allj if not p.name.endswith(".result.json")
                 and p.name != "_seen.json"]
        assert len(moved) == 2, moved
        assert len(sides) == 2, sides
        side = json.loads(sides[0].read_text("utf-8"))
        assert side.get("digested") is True and "processed_at" in side, side
        # سایدکارِ وضعیتِ ارگانیسم (اتمیک، الگوی business_legs)
        sp = opslib.STATE_DIR / "ORGANISM-STATE.legs_cultivation"
        d = json.loads(sp.read_text("utf-8"))
        assert d["digested_total"] == 3 and "updated_at" in d, d
        # گزارشِ فشردهٔ دکتر
        rep = json.loads(leg_cultivate.report_path().read_text("utf-8"))
        assert rep["schema"] == "cultivation-report.v1", rep
        assert rep["legs"]["mining"]["digested"] == 2, rep["legs"]["mining"]
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)


def t_c_dedup_idempotent():
    """همان محتوایِ mining دوباره → duplicate؛ هیچ digestِ دوم (پایپ‌لاین idempotent)."""
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    try:
        _drop("mining", "a-batch-again", MINING_A)
        wiring._EPOCH_STATE.clear()
        r = wiring.legs_cultivation_beat(beat=60)
        m = r["legs"]["mining"]
        assert m["duplicates"] == 1 and m["digested"] == 0, m
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)


class FakeBridge:
    """ضبط‌کنندهٔ learn_from — قراردادِ SchoolBridge بدونِ curriculum واقعی."""
    def __init__(self):
        self.calls = []

    def learn_from(self, events, persist=False):
        evs = list(events)
        self.calls.append({"events": evs, "persist": persist})
        return {"taught_signals": len(evs), "mean_before": 0.0, "mean_after": 0.1,
                "ignited": [], "insights": []}


def t_d_school_link_absorbs_digest():
    """پیوندِ مغزِ B: یک digestِ واقعی → یک AfferentEventِ afferent=True →
    school_bridge.learn_from با persist=True (جذب در حافظهٔ School)."""
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    try:
        from sensory_bus import SensoryBus
        _drop("knowledge", "a-note", {"kind": "knowledge-drop",
                                      "label": "hypnosis MOC updated"})
        bus, bridge = SensoryBus(), FakeBridge()
        wiring._EPOCH_STATE.clear()
        r = wiring.legs_cultivation_beat(beat=60, sensory_bus=bus, school_bridge=bridge)
        assert r["legs"]["knowledge"]["digested"] == 1, r["legs"]["knowledge"]
        assert len(bridge.calls) == 1, bridge.calls
        call = bridge.calls[0]
        assert call["persist"] is True, "یادگیری باید persist=True باشد (حافظهٔ ماندگار)"
        assert len(call["events"]) == 1, call["events"]   # یک event به‌ازای هر digest
        ev = call["events"][0]
        assert getattr(ev, "afferent", False) is True and ev.source == "legs.knowledge", ev
        assert r["school"] == {"taught_signals": 1}, r["school"]
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)


def t_e_killswitch_wins():
    """STOP مقدم بر flag — حتی روشن هم None."""
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    try:
        opslib.STOP_ORGANISM.write_text("test", "utf-8")
        try:
            assert wiring.legs_cultivation_beat(beat=0) is None
        finally:
            opslib.STOP_ORGANISM.unlink()
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)


def t_f_cadence():
    """beat غیرِ مضربِ N → None؛ مضربِ N → اجرا."""
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    try:
        wiring._EPOCH_STATE.clear()
        assert wiring.legs_cultivation_beat(beat=7) is None       # epoch 0 (beat<60)
        assert wiring.legs_cultivation_beat(beat=120) is not None  # پنجرهٔ epoch ۲
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)


def t_g_doctor_sees_report():
    """دکتر گزارشِ تازه را می‌بیند: پای گرسنه (هرگز خوراک نگرفته) → کاندیدِ گلوگاهِ
    legs-starved با severity=medium؛ بحرانِ واقعی (error-rate) همچنان مقدم؛
    گزارشِ کهنه → نادیده (None)."""
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    try:
        # صندوق‌ها خالی؛ accounting/ziman هرگز خوراک نگرفته‌اند → starved در گزارش
        wiring._EPOCH_STATE.clear()
        r = wiring.legs_cultivation_beat(beat=60)
        assert "accounting" in r["starved_legs"], r["starved_legs"]
        doc = Doctor(state_dir=str(opslib.STATE_DIR),
                     knowledge_dir=str(ENV["ops"] / "knowledge-internal-test"))
        # trace خالی ({}) گاردِ قدیمیِ mine را فعال می‌کند (early None) — trace بی‌گلوگاه
        bn = doc.mine(trace={"errors_24h": 0, "frozen": False})
        assert bn is not None, "دکتر باید پای گرسنه را از گزارشِ تازه ببیند"
        assert bn["evidence"]["key"] == "legs-starved", bn
        assert bn["severity"] == "medium", bn
        # بحرانِ واقعی مقدم است — تغذیه هرگز error/freeze را کنار نمی‌زند
        bn2 = doc.mine(trace={"errors_24h": 5})
        assert bn2["evidence"]["key"] == "error-rate-high", bn2
        # گزارشِ کهنه (mtime قدیمی) → سیگنالِ نامعتبر → None
        old = time.time() - 3 * 86400
        os.utime(leg_cultivate.report_path(), (old, old))
        assert doc.mine(trace={"errors_24h": 0, "frozen": False}) is None, \
            "گزارشِ کهنه نباید RFC بسازد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)


def t_h_structurally_wired_and_out_of_profile():
    """organism.py این beat را صدا می‌زند؛ flag عمداً خارج از PAPER_FULL_FLAGS."""
    assert "legs_cultivation_beat(" in ORGANISM_SRC, "organism باید beat را صدا بزند"
    assert '"legs_cultivation"' in ORGANISM_SRC, "کلیدِ merge در ORGANISM-STATE"
    assert "OCTOPUS_WIRE_LEG_CULTIVATE" not in str(wiring.PAPER_FULL_FLAGS), \
        "flag نباید در پروفایلِ paper-full باشد (فعال‌سازی فقط با رأی مالک)"
    assert 'flag("OCTOPUS_WIRE_LEG_CULTIVATE")' in WIRING_SRC


if __name__ == "__main__":
    for f in (t_a_flag_off_is_noop, t_b_digests_two_legs, t_c_dedup_idempotent,
              t_d_school_link_absorbs_digest, t_e_killswitch_wins, t_f_cadence,
              t_g_doctor_sees_report, t_h_structurally_wired_and_out_of_profile):
        f()
        print("ok", f.__name__)
    print("PASS test_legs_cultivation")
