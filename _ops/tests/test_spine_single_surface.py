#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_spine_single_surface.py — C4: سطحِ تولیدِ واحدِ spine + قراردادِ envelope + parity.

پوشش:
  1. قراردادِ envelope: هر رویدادی که spine_adapters تولید می‌کند full-envelope دارد
     (event_id, idempotency_key, event_type, domain, occurred_at, recorded_at, producer,
      correlation_id, trust, schema_version) و trust/event_type معتبرند.
  2. provenance هرگز null: publish با producer=None → ردیف producer='unknown'.
  3. PARITY: مسیرِ dual_write خام (flag=0) و emit_event (flag=1) برای همان ورودی
     ردیفِ **بایت‌به‌بایت یکسان** (همان event_id + همان همهٔ ستون‌ها) تولید می‌کنند.
  4. emit_event: flag خاموش → صفر I/O؛ idempotent (replay = published=False).
  5. validate_row رویدادِ ناقص/بی‌trust را رد می‌کند.
$0 آفلاین؛ صفر شبکه؛ spine در sandbox.
"""
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("spine-single-surface")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "spine"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import event_spine as es  # noqa: E402
import spine_adapters as sa  # noqa: E402
import opslib  # noqa: E402

_COLS = ("event_id", "idempotency_key", "event_type", "domain", "occurred_at", "recorded_at",
         "producer", "producer_sequence", "correlation_id", "mission_id", "subject",
         "trust", "schema_version", "payload_json")


def _fresh_spine(tag):
    os.environ["OCTOPUS_WIRE_SPINE"] = "1"
    p = Path(str(opslib.STATE_DIR)) / f"spine-{tag}.db"
    if p.exists():
        p.unlink()
    p.parent.mkdir(parents=True, exist_ok=True)
    return es.EventSpine(path=p), p


def _row(db_path, event_id):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.execute(f"SELECT {','.join(_COLS)} FROM events WHERE event_id=?", (event_id,))
    r = cur.fetchone()
    con.close()
    return dict(zip(_COLS, r)) if r else None


# ── ۱: قراردادِ envelope کامل ───────────────────────────────────────────────────
def t_full_envelope_contract():
    sp, p = _fresh_spine("contract")
    res = sa.emit_event(spine=sp, event_type="outcome-recorded", domain="proposal",
                        correlation_id="c-1", subject="s-1", producer="unit",
                        trust="OWNER_CONFIRMED", payload={"n": 3})
    sp.close()
    assert res.get("published"), res
    row = _row(p, res["event_id"])
    ok, missing = sa.validate_row(row)
    assert ok, f"envelope ناقص: {missing}"
    assert row["schema_version"] == es.SCHEMA_VERSION and row["trust"] == "OWNER_CONFIRMED"


# ── ۲: provenance هرگز null ─────────────────────────────────────────────────────
def t_provenance_never_null():
    sp, p = _fresh_spine("prov")
    eid = sp.publish({"event_type": "outcome-recorded", "domain": "d", "correlation_id": "c",
                      "subject": "s"})   # producer عمداً غایب
    sp.close()
    row = _row(p, eid)
    assert row["producer"] == "unknown", f"producer باید default شود: {row['producer']}"


# ── ۳: PARITY — dual_write خام == emit_event ────────────────────────────────────
def t_parity_direct_vs_adapter():
    payload = {"leg_id": "unknown", "measurement_only": True}
    kw = dict(event_type="accepted-measurement", domain="proposal",
              correlation_id="prop_P1", mission_id="M1", subject="P1",
              producer="owner_verdict", trust="OWNER_CONFIRMED")
    # مسیرِ خام
    spA, pA = _fresh_spine("direct")
    es.dual_write(spA, {**kw, "payload": payload})
    spA.close()
    # مسیرِ adapter
    spB, pB = _fresh_spine("adapter")
    sa.emit_event(spine=spB, payload=payload, **kw)
    spB.close()
    conA = sqlite3.connect(f"file:{pA}?mode=ro", uri=True)
    rowA = conA.execute(f"SELECT {','.join(_COLS)} FROM events").fetchone(); conA.close()
    conB = sqlite3.connect(f"file:{pB}?mode=ro", uri=True)
    rowB = conB.execute(f"SELECT {','.join(_COLS)} FROM events").fetchone(); conB.close()
    dA, dB = dict(zip(_COLS, rowA)), dict(zip(_COLS, rowB))
    # occurred_at/recorded_at هر دو مسیر به _utc_now_iso() default می‌شوند → فقط لحظهٔ فراخوان
    # فرق دارد (نه منطق). پس این دو ستونِ wall-clock را کنار می‌گذاریم؛ بقیه باید یکسان باشند —
    # مهم‌ترین: event_id و idempotency_key (dedup/replay بایت‌به‌بایت).
    _WALL = {"occurred_at", "recorded_at"}
    for c in _COLS:
        if c in _WALL:
            continue
        assert dA[c] == dB[c], f"PARITY شکست در {c}: {dA[c]!r} != {dB[c]!r}"
    assert dA["event_id"] == dB["event_id"], "event_id باید یکسان باشد (idempotency یکسان)"
    assert dA["idempotency_key"] == dB["idempotency_key"], "idempotency_key یکسان"


# ── ۴: flag خاموش + idempotent ──────────────────────────────────────────────────
def t_flag_off_and_idempotent():
    os.environ["OCTOPUS_WIRE_SPINE"] = "0"
    assert sa.emit_event(event_type="outcome-recorded", domain="d",
                         correlation_id="c").get("reason") == "flag-off"
    sp, p = _fresh_spine("idem")
    r1 = sa.emit_event(spine=sp, event_type="outcome-recorded", domain="d",
                       correlation_id="c-idem", subject="s", producer="u")
    r2 = sa.emit_event(spine=sp, event_type="outcome-recorded", domain="d",
                       correlation_id="c-idem", subject="s", producer="u")
    sp.close()
    assert r1.get("published") and not r2.get("published"), f"replay باید suppress شود: {r1} {r2}"


# ── ۵: validate_row رویدادِ بد را رد می‌کند ────────────────────────────────────
def t_validate_rejects_bad():
    ok, missing = sa.validate_row({"event_type": "outcome-recorded", "domain": "d"})
    assert not ok and "correlation_id" in missing
    ok2, m2 = sa.validate_row({"event_id": "e", "idempotency_key": "i", "event_type": "BOGUS",
                               "domain": "d", "occurred_at": "t", "recorded_at": "t",
                               "producer": "p", "correlation_id": "c", "trust": "OWNER_CONFIRMED",
                               "schema_version": 1})
    assert not ok2 and "invalid:event_type" in m2


if __name__ == "__main__":
    failed = harness.run([
        ("[۱] قراردادِ envelope کامل", t_full_envelope_contract),
        ("[۲] provenance هرگز null", t_provenance_never_null),
        ("[۳] PARITY: dual_write == emit_event", t_parity_direct_vs_adapter),
        ("[۴] flag خاموش + idempotent", t_flag_off_and_idempotent),
        ("[۵] validate_row رویدادِ بد را رد می‌کند", t_validate_rejects_bad),
    ])
    sys.exit(1 if failed else 0)
