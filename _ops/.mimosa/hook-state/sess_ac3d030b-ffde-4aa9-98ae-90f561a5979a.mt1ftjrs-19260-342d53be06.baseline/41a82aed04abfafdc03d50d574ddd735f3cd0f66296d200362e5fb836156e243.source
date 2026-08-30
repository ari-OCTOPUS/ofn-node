#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_boot_certificate.py — C2-E: شناسنامهٔ تولد (`system.booted` → spine).

پوشش:
  1. اولین بوت: emit با prev_boot_id=None + payload کامل (halt/flags_hash/checksums)
  2. بوتِ دوم: prev_boot_id == boot_idِ اول — زنجیرهٔ تولد پیوسته است
  3. flags_hash فقط ساختار: هیچ **مقداری** از .env در payload/hash-input نیست؛
     تغییرِ مقدارِ .env هش را عوض نمی‌کند ولی تغییرِ نامِ کلید عوض می‌کند
  4. flag خاموش → skip، صفر I/O (spine.db ساخته نمی‌شود)
  5. uptime_gap_s از آخرین رویدادِ spine محاسبه می‌شود
  6. خطاها fail-soft (state_dir خراب → dict، هرگز raise)
$0 آفلاین؛ صفر شبکه؛ state موقت؛ secret واقعی خوانده نمی‌شود (فایلِ env مصنوعی).
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("boot-cert")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "spine"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import boot_certificate as bc  # noqa: E402
import opslib  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))
_SPINE = _STATE / "spine" / "spine.db"
_ENVF = _STATE.parent / "test.env"          # فایلِ envِ مصنوعیِ تست — نه .env واقعی


def _wipe():
    if _SPINE.exists():
        _SPINE.unlink()
    os.environ["OCTOPUS_WIRE_SPINE"] = "1"
    _ENVF.write_text("KEY_A=value-a\nKEY_B=value-b\n# comment\n", encoding="utf-8")


def _events():
    if not _SPINE.exists():
        return []
    con = sqlite3.connect(f"file:{_SPINE}?mode=ro", uri=True)
    rows = con.execute("SELECT event_type, domain, producer, trust, payload_json "
                       "FROM events ORDER BY rowid").fetchall()
    con.close()
    return rows


# ── ۱: اولین بوت ────────────────────────────────────────────────────────────────
def t_first_boot_emits_full_cert():
    _wipe()
    r = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    assert r.get("emitted"), f"باید emit شود: {r}"
    assert r.get("prev_boot_id") is None, "تولدِ اول prev ندارد"
    evs = _events()
    booted = [e for e in evs if e[0] == "system.booted"]
    assert len(booted) == 1 and booted[0][1] == "system" and booted[0][2] == "organism-boot"
    p = json.loads(booted[0][4])
    for k in ("boot_id", "halt_state", "flags_hash", "state_checksums", "booted_at"):
        assert k in p, f"payload باید {k} داشته باشد: {list(p)}"
    assert p["halt_state"] in ("armed", "clear", "unknown")


# ── ۲: زنجیرهٔ تولد ─────────────────────────────────────────────────────────────
def t_birth_chain_links():
    _wipe()
    r1 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    r2 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    assert r2.get("prev_boot_id") == r1.get("boot_id"), \
        f"زنجیره باید پیوسته باشد: {r1.get('boot_id')} -> {r2.get('prev_boot_id')}"
    r3 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    assert r3.get("prev_boot_id") == r2.get("boot_id")


# ── ۳: flags_hash ساختار است نه secret ─────────────────────────────────────────
def t_flags_hash_structure_not_values():
    _wipe()
    r1 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    # تغییرِ «مقدار» → هش نباید عوض شود (مقدار هرگز خوانده نمی‌شود)
    _ENVF.write_text("KEY_A=CHANGED-VALUE\nKEY_B=value-b\n", encoding="utf-8")
    r2 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    # تغییرِ «نام کلید» → هش باید عوض شود (ساختار عوض شده)
    _ENVF.write_text("KEY_A=value-a\nKEY_RENAMED=value-b\n", encoding="utf-8")
    r3 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    evs = [json.loads(e[4]) for e in _events() if e[0] == "system.booted"]
    h1, h2, h3 = (evs[0]["flags_hash"], evs[1]["flags_hash"], evs[2]["flags_hash"])
    assert h1 == h2, "تغییرِ مقدارِ env نباید هش را عوض کند (مقدار خوانده نمی‌شود)"
    assert h1 != h3, "تغییرِ نامِ کلید باید هش را عوض کند (ساختار)"
    payload_text = json.dumps(evs)
    assert "value-a" not in payload_text and "CHANGED-VALUE" not in payload_text, \
        "هیچ مقداری از env نباید در payload باشد"


# ── ۴: flag خاموش → صفر I/O ────────────────────────────────────────────────────
def t_flag_off_zero_io():
    _wipe()
    if _SPINE.exists():
        _SPINE.unlink()
    os.environ["OCTOPUS_WIRE_SPINE"] = "0"
    r = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    assert r == {"emitted": False, "reason": "flag-off"}
    assert not _SPINE.exists(), "flag خاموش نباید spine.db بسازد"


# ── ۵: uptime_gap_s از spine ────────────────────────────────────────────────────
def t_uptime_gap_from_spine():
    _wipe()
    bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    time.sleep(1.1)
    r2 = bc.emit_birth_certificate(state_dir=_STATE, env_file=_ENVF)
    gap = r2.get("uptime_gap_s")
    assert gap is not None and gap >= 1.0, f"خواب باید اندازه‌گیری شود: {gap}"


# ── ۶: fail-soft ───────────────────────────────────────────────────────────────
def t_fail_soft():
    os.environ["OCTOPUS_WIRE_SPINE"] = "1"
    r = bc.emit_birth_certificate(state_dir=Path("Z:/definitely/not/a/dir"))
    assert isinstance(r, dict) and not r.get("emitted"), f"هرگز raise: {r}"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱] اولین بوت: شناسنامهٔ کامل", t_first_boot_emits_full_cert),
        ("[۲] زنجیرهٔ تولد پیوسته", t_birth_chain_links),
        ("[۳] flags_hash: ساختار نه secret", t_flags_hash_structure_not_values),
        ("[۴] flag خاموش → صفر I/O", t_flag_off_zero_io),
        ("[۵] uptime_gap از spine", t_uptime_gap_from_spine),
        ("[۶] fail-soft", t_fail_soft),
    ])
    sys.exit(1 if failed else 0)
