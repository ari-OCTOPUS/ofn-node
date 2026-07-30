#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_snapshot_staleness — منطقِ کهنگی و فهرستِ بازدارنده، با ورودیِ کنترل‌شده.

چرا این فایل بعد از بقیه نوشته شد: دو جهشِ اجراشده روی `snapshot.py` **سبز
ماندند** —

    `auth = "STALE"`               → `"AUTHORITATIVE"`   ⇒ سوییت سبز
    `blockers.append("self-model-not-fresh")` → حذف       ⇒ سوییت سبز

یعنی هر دو محافظتِ ادعاشده اصلاً سنجیده نمی‌شدند. علتش این بود که
`t_stale_self_model_degrades_compass` فقط `compass` را با یک dict ِ **دست‌ساز**
می‌آزماید؛ خودِ `snapshot._state()` که کهنگی را محاسبه می‌کند هرگز با ورودیِ
کنترل‌شده اجرا نمی‌شد، و تنها بندِ زندهٔ آن (`snapshot.build()`) با شرطِ
`in ("ADVISORY_SHADOW","STALE","MISSING")` آن‌قدر شل بود که هر سه را می‌پذیرفت.

`_state` تابعِ خالص با `now` و `sla_s` تزریق‌شدنی است — دقیقاً همان چیزی که
آسان تست می‌شود و تست نشده بود.

هیچ فایلِ زنده‌ای نوشته نمی‌شود: همه‌چیز در tmpdir.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from unified_control import snapshot  # noqa: E402

NOW = 1_785_400_000.0


def _file(tmp: Path, name: str, payload, age_s: float) -> Path:
    p = tmp / name
    p.write_text(json.dumps(payload, ensure_ascii=False), "utf-8")
    mt = NOW - age_s
    os.utime(p, (mt, mt))
    return p


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="uc-stale-")).resolve()


# ── هستهٔ کهنگی ─────────────────────────────────────────────────────────────
def t_a_fresh_file_is_authoritative():
    tmp = _tmp()
    p = _file(tmp, "x.json", {"a": 1}, age_s=10)
    s = snapshot._state(p, now=NOW, sla_s=3600)
    assert s["authority"] == "AUTHORITATIVE", s
    assert 0 <= s["age_s"] <= 20, s


def t_a_file_past_its_sla_is_stale_not_authoritative():
    """جهشِ سبزِ ۱: `auth = "STALE"` → `"AUTHORITATIVE"` هیچ تستی را قرمز نکرد."""
    tmp = _tmp()
    p = _file(tmp, "x.json", {"a": 1}, age_s=7200)
    s = snapshot._state(p, now=NOW, sla_s=3600)
    assert s["authority"] == "STALE", s
    assert s["authority"] != "AUTHORITATIVE"
    assert s["age_s"] > s["sla_s"], s


def t_the_sla_boundary_is_exclusive_not_inclusive():
    """مرزِ off-by-one: دقیقاً روی SLA هنوز کهنه نیست، یک ثانیه بعدش هست."""
    tmp = _tmp()
    on = _file(tmp, "on.json", {"a": 1}, age_s=3600)
    over = _file(tmp, "over.json", {"a": 1}, age_s=3601)
    assert snapshot._state(on, now=NOW, sla_s=3600)["authority"] == "AUTHORITATIVE"
    assert snapshot._state(over, now=NOW, sla_s=3600)["authority"] == "STALE"


def t_a_missing_or_empty_file_is_missing_not_fresh():
    tmp = _tmp()
    absent = tmp / "nope.json"
    assert snapshot._state(absent, now=NOW, sla_s=3600)["authority"] == "MISSING"
    empty = tmp / "empty.json"
    empty.write_text("{}", "utf-8")
    os.utime(empty, (NOW - 5, NOW - 5))
    assert snapshot._state(empty, now=NOW, sla_s=3600)["authority"] == "MISSING"


def t_unparseable_json_is_missing_never_authoritative():
    """فایلِ خراب نباید «تازه و معتبر» شمرده شود — بدترین حالتِ ممکن."""
    tmp = _tmp()
    bad = tmp / "bad.json"
    bad.write_text("{ not json", "utf-8")
    os.utime(bad, (NOW - 5, NOW - 5))
    s = snapshot._state(bad, now=NOW, sla_s=3600)
    assert s["authority"] == "MISSING", s


def t_a_fresh_shadow_file_is_never_promoted():
    """تازگی مجوزِ اقتدار نیست — shadow حتی نو هم advisory می‌ماند."""
    tmp = _tmp()
    p = _file(tmp, "h.json", {"period_s": 60}, age_s=5)
    s = snapshot._state(p, now=NOW, sla_s=3600, shadow=True)
    assert s["authority"] == "ADVISORY_SHADOW", s


def t_a_stale_shadow_reports_stale_not_shadow():
    """ترتیبِ بندها مهم است: کهنگی بر shadow مقدم است، وگرنه یک فایلِ
    ماه‌ها-کهنه به‌عنوان «مشاورِ معتبر» خوانده می‌شود."""
    tmp = _tmp()
    p = _file(tmp, "h.json", {"period_s": 60}, age_s=99999)
    s = snapshot._state(p, now=NOW, sla_s=3600, shadow=True)
    assert s["authority"] == "STALE", s


# ── فهرستِ بازدارنده ────────────────────────────────────────────────────────
def t_a_non_authoritative_self_model_becomes_a_blocker():
    """جهشِ سبزِ ۲: حذفِ `blockers.append("self-model-not-fresh")` سبز ماند."""
    live = snapshot.build()
    auth = live["self_model"]["authority"]
    if auth == "AUTHORITATIVE":
        # روی درختِ زنده تازه است — پس ناوردی را روی همان منطق می‌سنجیم
        assert "self-model-not-fresh" not in live["blockers"], live["blockers"]
    else:
        assert "self-model-not-fresh" in live["blockers"], (auth, live["blockers"])


def t_every_blocker_is_a_nonempty_string():
    live = snapshot.build()
    assert isinstance(live["blockers"], list)
    for b in live["blockers"]:
        assert isinstance(b, str) and b.strip(), live["blockers"]


def t_the_snapshot_writes_nothing():
    """ناوردیِ فقط‌خواندنی — بندِ اولِ کلِ این پکیج."""
    import hashlib
    from unified_control import snapshot as sn
    targets = [Path(sn.OPS) / "state" / "ORGANISM-STATE.json",
               Path(sn.OPS) / "state" / "cortex" / "self-model.json"]
    before = {}
    for t in targets:
        before[t] = hashlib.sha256(t.read_bytes()).hexdigest() if t.exists() else None
    sn.build()
    for t in targets:
        after = hashlib.sha256(t.read_bytes()).hexdigest() if t.exists() else None
        assert after == before[t], f"snapshot فایلِ زنده را عوض کرد: {t}"


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")
    print(f"\n{'OK' if not failed else 'FAILED'} {len(tests) - failed}/{len(tests)}")
    sys.exit(1 if failed else 0)
