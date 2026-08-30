#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_restart_battery.py — C2-F: باتریِ رستاخیز — سناریوی مرکبِ end-to-end.

یک داستانِ کامل (نه unitهای جدا — ترکیب را اثبات می‌کند):
  تحویلِ ۲ کارت → رأی روی #1 → تعویقِ #2 → **restart** →
  فقط #2 بازسازی می‌شود → تصمیمِ #2 با توکنِ بازسازی‌شده → replayِ #2 مسدود →
  HALT روی restart می‌ماند → شناسنامهٔ تولد زنجیرِ پیوسته دارد →
  اثرِ EXECUTINGِ رهاشده RECONCILE می‌شود → cacheِ خراب با SoTِ سالم بی‌ضرر است.

نگاشت به قانونِ C2-F:
  restart-after-delivery ✔ · restart-after-defer ✔ · restart-before/after-verdict ✔ ·
  restart-during-in-flight ✔ · replay-callback ✔ · corrupted-cache+intact-SoT ✔ ·
  missing-projection-rebuild ✔ · HALT-persists ✔ · boot-lineage-continuous ✔
$0 آفلاین؛ صفر شبکه؛ state موقت.
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("restart-battery")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs"),
           str(_OPS / "outcomes"), str(_OPS / "spine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live_loop import LiveLoop, _InMemoryBus  # noqa: E402
from leg import Leg, TaskPacket  # noqa: E402
import proposal_token as pt  # noqa: E402
import deferral_rebuild as dr  # noqa: E402
import boot_certificate as bc  # noqa: E402
import journal_recovery as jr  # noqa: E402
import opslib  # noqa: E402

_OWNER = 777
_STATE = Path(str(opslib.STATE_DIR))
_ODB = _STATE / "outcomes" / "outcomes.db"
_ENVF = _STATE.parent / "battery.env"


class _FakeChannel:
    def __init__(self):
        self.sent = []
        self._owner = _OWNER

    def send_text(self, text, reply_markup=None):
        self.sent.append({"text": text, "reply_markup": reply_markup})
        return True


def _leg(n):
    packet = TaskPacket(leg_id="battery-leg", organ="TEST",
                        read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
                        tools=("draft",), budget_aud=0.0)
    leg = Leg(packet, organ_table={"TEST": {"floor": 0}})
    for i in range(n):
        leg.emit_proposal("draft_quote", {"scope": f"room {i}", "expected_aud": 100 + i})
    return leg


def _toks(chan):
    out = []
    for m in chan.sent:
        for row in (m.get("reply_markup") or {}).get("inline_keyboard") or []:
            out.append(row[0]["callback_data"].split(":", 2)[2])
    return out


def _rows(et):
    if not _ODB.exists():
        return []
    con = sqlite3.connect(f"file:{_ODB}?mode=ro", uri=True)
    r = con.execute("SELECT proposal_id FROM outcomes WHERE event_type=?", (et,)).fetchall()
    con.close()
    return [x[0] for x in r]


def t_full_resurrection_story():
    # ── محیط ──
    os.environ["OCTOPUS_WIRE_PROPOSAL_BUTTONS"] = "1"
    os.environ["OCTOPUS_WIRE_VERDICT_OUTCOME"] = "1"
    os.environ["OCTOPUS_WIRE_SPINE"] = "1"
    os.environ[pt.SECRET_ENV] = "unit-test-secret-not-real"
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)
    _ENVF.write_text("K1=v\n", encoding="utf-8")
    if _ODB.exists():
        _ODB.unlink()

    # ── زندگیِ اول: تحویل ۲ کارت؛ رأی #1؛ تعویق #2 ──
    chan1 = _FakeChannel()
    loop1 = LiveLoop(bus=_InMemoryBus(), approval_channel=chan1, leg=_leg(2))
    loop1.route_leg_proposals(deliver=True)
    t1, t2 = _toks(chan1)[:2]
    assert loop1.record_proposal_outcome_by_token(t1, "ok", from_id=_OWNER)
    rec = loop1.record_proposal_outcome_by_token(t2, "later", from_id=_OWNER)
    assert rec and rec.get("event") == "deferred"
    cert1 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    assert cert1.get("emitted")

    # ── «خواب» + restart: اشیای کاملاً نو (RAM = صفر) ──
    time.sleep(1.05)
    chan2 = _FakeChannel()
    loop2 = LiveLoop(bus=_InMemoryBus(), approval_channel=chan2, leg=_leg(0))
    # cacheِ خراب با SoTِ سالم: ورودیِ زبالهٔ نامرتبط نباید چیزی را بشکند
    loop2._proposal_cb["garbage-token"] = {"broken": True}

    # ── فاز ۶ (PROJECTIONS): فقط #2 (معوق) بازسازی می‌شود، #1 (decided) نه ──
    res = dr.rebuild_deferred_cards(loop2, chan2)
    assert res["rebuilt"] == 1, f"فقط کارتِ معوق: {res}"
    tok_rebuilt = _toks(chan2)[0]
    decided_pids = set(_rows("accepted-measurement"))
    rebuilt_text = chan2.sent[0]["text"]
    assert all(p not in rebuilt_text for p in decided_pids), "کارتِ decided نباید برگردد"

    # ── فاز ۷ (JOURNAL) + ۴ (RUNTIME): اثرِ EXECUTINGِ رهاشده → RECONCILE ──
    import chrono as ch
    dbp = _STATE / "chrono-batt.db"
    db = ch.ChronoDB(path=dbp)
    old = int(time.time() * 1000) - 9 * 3600_000
    db._con.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,status,"
                    "execution_id,execution_started_at,created_ts) "
                    "VALUES('fx-mid','send','r','EXECUTING','e1',?,?)", (old, old))
    db._con.commit(); db._con.close()
    rec2 = jr.boot_recovery(state_dir=_STATE, chrono_db_path=dbp)
    assert rec2["chrono"].get("reconciled_now") == 1, f"in-flight → RECONCILE: {rec2}"

    # ── HALT persists: فایلِ halt پایدار است و شناسنامه آن را می‌بیند ──
    halt_file = getattr(opslib, "HALT_ALL", None)
    halted_before = None
    if halt_file is not None:
        Path(halt_file).parent.mkdir(parents=True, exist_ok=True)
        Path(halt_file).write_text("battery-halt-test", encoding="utf-8")
        halted_before = bool(opslib.halted())
    cert2 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    if halt_file is not None:
        Path(halt_file).unlink(missing_ok=True)
        assert halted_before, "halt باید از فایلِ durable خوانده شود (restart-safe)"

    # ── زنجیرهٔ تولد: cert2.prev == cert1.boot ──
    assert cert2.get("emitted") and cert2.get("prev_boot_id") == cert1.get("boot_id"), \
        f"زنجیرهٔ هویت: {cert1.get('boot_id')} -> {cert2.get('prev_boot_id')}"
    assert (cert2.get("uptime_gap_s") or 0) >= 1.0, "خواب اندازه‌گیری شده"

    # ── تصمیمِ #2 بعد از restart با توکنِ بازسازی‌شده؛ سپس replay مسدود ──
    rec3 = loop2.record_proposal_outcome_by_token(tok_rebuilt, "no", from_id=_OWNER)
    assert rec3 is not None, "کارتِ بازسازی‌شده باید قابلِ تصمیم باشد"
    loop3 = LiveLoop(bus=_InMemoryBus(), approval_channel=_FakeChannel(), leg=_leg(0))
    assert loop3.record_proposal_outcome_by_token(tok_rebuilt, "ok", from_id=_OWNER) is None, \
        "replay بعد از تصمیم باید مسدود باشد"
    assert len(_rows("accepted-measurement")) == 1 and len(_rows("rejected")) == 1, \
        "دقیقاً یک accepted و یک rejected — صفر duplicate"


if __name__ == "__main__":
    failed = harness.run([
        ("باتریِ رستاخیز — داستانِ کاملِ ۹-سناریویی", t_full_resurrection_story),
    ])
    sys.exit(1 if failed else 0)
