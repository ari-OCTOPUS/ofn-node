#!/usr/bin/env python3
"""تست P-Chrono-4 · فلشِ میرا روی ledger ژنوم (v0.4.5 گسترشِ langar).
اثبات: age_tick فقط با is_human=1 حرکت می‌کند و دقیقاً +1 (TINV-3) · appendهای
غیرانسانی فلش را نمی‌برند · زنجیرهٔ hash پس از گسترش verify می‌شود · دستکاری/برگشتِ
age = شکستِ زنجیره (مرگِ منطقی) · رکوردهای legacy (بدونِ فیلدِ age) هنوز verify
می‌شوند · پلِ موجودِ opslib.ledger_note رگرسیون ندارد. $0 آفلاین."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("langar")
import opslib  # noqa: E402
import chrono  # noqa: E402

sys.path.insert(0, str(ENV["genome"] / "ledger"))
from ledger import Ledger, GENESIS, _canonical  # noqa: E402


def _fresh(name: str) -> Ledger:
    return Ledger(ENV["genome"] / "ledger" / f"{name}.jsonl")


def t_age_moves_only_on_human():
    lg = _fresh("age")
    for i in range(3):
        rec = lg.append("NOTE", {"subtype": "obs", "i": i}, actor="agent")
        assert rec["age_tick"] == 0 and rec["is_human"] == 0, rec
    assert lg.last_age_tick() == 0
    h1 = lg.append("APPROVAL", {"verdict": "yes"}, actor="human", is_human=True)
    assert h1["age_tick"] == 1 and h1["is_human"] == 1
    lg.append("NOTE", {"subtype": "obs"}, actor="agent")
    assert lg.last_age_tick() == 1                     # غیرانسانی فلش را نبرد
    h2 = lg.append("APPROVAL", {"verdict": "again"}, actor="human", is_human=True)
    assert h2["age_tick"] == 2                          # دقیقاً +1
    ok, msg = lg.verify()
    assert ok, msg


def t_on_human_judgment_helper():
    lg = _fresh("judg")
    entry = chrono.on_human_judgment({"verdict": "approve"}, ledger=lg)
    assert entry["type"] == "APPROVAL" and entry["age_tick"] == 1
    assert chrono.last_age_tick(lg) == 1


def t_tamper_breaks_chain():
    lg = _fresh("tamper")
    lg.append("NOTE", {"subtype": "a"}, actor="agent")
    lg.append("APPROVAL", {"v": 1}, actor="human", is_human=True)
    lines = lg.path.read_text("utf-8").splitlines()
    rec = json.loads(lines[0])
    rec["payload"] = {"subtype": "EVIL"}               # ویرایشِ خاموشِ تاریخ
    lines[0] = json.dumps(rec, ensure_ascii=False)
    lg.path.write_text("\n".join(lines) + "\n", "utf-8")
    ok, msg = lg.verify()
    assert not ok and "tamper" in msg, msg


def t_age_reversal_is_logical_death():
    lg = _fresh("reversal")
    lg.append("APPROVAL", {"v": 1}, actor="human", is_human=True)   # age=1
    lg.append("APPROVAL", {"v": 2}, actor="human", is_human=True)   # age=2
    # مهاجم رکوردی با hash صحیح ولی age برگشته می‌سازد → verify باید بمیرد
    body = {"id": "x" * 32, "ts": "2026-07-08T00:00:00+00:00", "type": "NOTE",
            "actor": "attacker", "payload": {}, "meta": {},
            "prev": lg.last_hash(), "age_tick": 0, "is_human": 0}
    rec = {**body, "hash": hashlib.sha256(_canonical(body)).hexdigest()}
    with open(lg.path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    ok, msg = lg.verify()
    assert not ok and ("reversal" in msg or "arrow" in msg or "TINV-3" in msg), msg
    # و حالتِ دوم: append غیرانسانی که age را جلو ببرد هم مرگِ منطقی است
    lg2 = _fresh("sneak")
    lg2.append("NOTE", {}, actor="agent")
    body2 = {"id": "y" * 32, "ts": "2026-07-08T00:00:00+00:00", "type": "NOTE",
             "actor": "attacker", "payload": {}, "meta": {},
             "prev": lg2.last_hash(), "age_tick": 5, "is_human": 0}
    rec2 = {**body2, "hash": hashlib.sha256(_canonical(body2)).hexdigest()}
    with open(lg2.path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec2, ensure_ascii=False) + "\n")
    ok2, msg2 = lg2.verify()
    assert not ok2 and "TINV-3" in msg2, msg2


def t_legacy_records_still_verify():
    lg = _fresh("legacy")
    # رکوردِ قدیمی (پیش از v0.4.5): بدونِ age_tick/is_human — عیناً شکلِ کهنه
    body = {"id": "z" * 32, "ts": "2026-07-01T00:00:00+00:00", "type": "NOTE",
            "actor": "system", "payload": {"subtype": "old"}, "meta": {},
            "prev": GENESIS}
    rec = {**body, "hash": hashlib.sha256(_canonical(body)).hexdigest()}
    with open(lg.path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    lg2 = Ledger(lg.path)                              # tail از دیسک
    ok, msg = lg2.verify()
    assert ok, msg                                     # زنجیرهٔ مخلوط سالم است
    assert lg2.last_age_tick() == 0
    new = lg2.append("NOTE", {"subtype": "new"}, actor="agent")
    assert new["prev"] == rec["hash"] and new["age_tick"] == 0
    h = lg2.append("APPROVAL", {"v": 1}, actor="human", is_human=True)
    assert h["age_tick"] == 1
    ok, msg = lg2.verify()
    assert ok, msg


def t_ledger_note_bridge_regression():
    rec = opslib.ledger_note("CHRONO_TEST", {"x": 1}, actor="test")
    assert rec is not None and rec["type"] == "NOTE" and rec["is_human"] == 0
    assert rec["payload"]["subtype"] == "CHRONO_TEST"
    ok, msg = opslib.genome_ledger().verify()
    assert ok, msg


def t_heartbeat_advances_age():
    # v0.4.6 (verdict آری heart-driven): beat=True هم مثل human فلش را +۱ می‌برد
    lg = _fresh("beat")
    lg.append("NOTE", {"subtype": "obs"}, actor="agent")               # age 0
    b1 = lg.append("HEARTBEAT", {"beat": 1}, actor="pacemaker", beat=True)
    assert b1["age_tick"] == 1 and b1["beat"] == 1, b1                 # ضربان فلش را برد
    lg.append("NOTE", {"subtype": "obs"}, actor="agent")              # age 1 (بی‌حرکت)
    h = lg.append("APPROVAL", {"v": 1}, actor="human", is_human=True)
    assert h["age_tick"] == 2, h                                       # human هم +1
    b2 = lg.append("HEARTBEAT", {"beat": 2}, actor="pacemaker", beat=True)
    assert b2["age_tick"] == 3, b2
    ok, msg = lg.verify()
    assert ok, msg


def t_heart_rule_versioned_verify():
    # رکوردِ legacy (بدونِ age_rule) + رکوردهای heart در یک زنجیره → سالم verify
    lg = _fresh("ver")
    body = {"id": "L" * 32, "ts": "2026-07-01T00:00:00+00:00", "type": "NOTE",
            "actor": "system", "payload": {}, "meta": {}, "prev": GENESIS}
    rec = {**body, "hash": hashlib.sha256(_canonical(body)).hexdigest()}
    with open(lg.path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    lg2 = Ledger(lg.path)                                              # tail از دیسک
    b = lg2.append("HEARTBEAT", {}, actor="pacemaker", beat=True)     # heart رویِ legacy
    assert b["age_tick"] == 1 and b["prev"] == rec["hash"], b
    ok, msg = lg2.verify()
    assert ok, msg                                                    # زنجیرهٔ مخلوط سالم


def t_heart_beat_jump_is_logical_death():
    # مهاجم رکوردِ heart با beat=1 ولی جهشِ +2 → verify باید بمیرد (دقیقاً +1)
    lg = _fresh("beatjump")
    r0 = lg.append("APPROVAL", {}, actor="human", is_human=True)      # heart age 1
    body = {"id": "J" * 32, "ts": "2026-07-08T00:00:00+00:00", "type": "HEARTBEAT",
            "actor": "attacker", "payload": {}, "meta": {}, "prev": r0["hash"],
            "age_tick": 3, "is_human": 0, "age_rule": "heart", "beat": 1}
    rec = {**body, "hash": hashlib.sha256(_canonical(body)).hexdigest()}
    with open(lg.path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    ok, msg = lg.verify()
    assert not ok and "exactly 1" in msg, msg


if __name__ == "__main__":
    failed = harness.run([
        ("TINV-3: فلش فقط با is_human=1 و دقیقاً +1", t_age_moves_only_on_human),
        ("on_human_judgment → APPROVAL انسانی + release", t_on_human_judgment_helper),
        ("دستکاریِ تاریخ = شکستِ زنجیره", t_tamper_breaks_chain),
        ("برگشتِ age / پیریِ خودسرانه = مرگِ منطقی", t_age_reversal_is_logical_death),
        ("رکوردهای legacy (بدونِ age) verify می‌شوند", t_legacy_records_still_verify),
        ("رگرسیونِ پلِ ledger_note (NOTE+subtype)", t_ledger_note_bridge_regression),
        ("v0.4.6: heartbeat (beat=1) فلش را +۱ می‌برد + human هم", t_heartbeat_advances_age),
        ("v0.4.6: verify نسخه‌بندی‌شده (legacy TINV-3 + heart)", t_heart_rule_versioned_verify),
        ("v0.4.6: جهشِ beat (+۲) = مرگِ منطقی (دقیقاً +۱)", t_heart_beat_jump_is_logical_death),
    ])
    sys.exit(1 if failed else 0)
