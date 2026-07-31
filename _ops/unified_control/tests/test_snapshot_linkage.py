#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_snapshot_linkage — پیوندِ exact-row ِ سه دفترِ چرخهٔ هدف در snapshot.

چرا این تست وجود دارد (ممیزیِ ۰۷-۳۰/۰۷-۳۱): `snapshot.build` سه «آخرین ردیف»
از سه دفترِ مستقل (prereg/journal/verdicts) کنارِ هم می‌گذاشت. آن سه ردیف
می‌توانند مالِ سه چرخهٔ متفاوت باشند و `link_graph` آن‌وقت حکمِ چرخهٔ کهنه را
به‌عنوانِ حکمِ چرخهٔ جاری نمایش می‌داد — بازسازیِ اتصال از تصادف، نه از شناسه.
سنجهٔ این فایل رفتار است: ردیفِ ناهم‌چرخه هرگز برنمی‌گردد، حتی اگر آخرین
ردیفِ فایل باشد.

هیچ فایلِ زنده‌ای خوانده/نوشته نمی‌شود: STATE به tmpdir پین می‌شود.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from unified_control import snapshot  # noqa: E402


def _tc(tmp: Path) -> Path:
    d = tmp / "test_cycle"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _jsonl(p: Path, rows: list) -> None:
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", "utf-8")


def _pinned(rows_pre, rows_journal, rows_verdicts):
    """snapshot.build() با STATE ِ پین‌شده به tmpdir؛ خروجی: goal_cycle + blockers."""
    tmp = Path(tempfile.mkdtemp(prefix="uc-link-")).resolve()
    tc = _tc(tmp)
    if rows_pre is not None:
        _jsonl(tc / "prereg.jsonl", rows_pre)
    if rows_journal is not None:
        _jsonl(tc / "journal.jsonl", rows_journal)
    if rows_verdicts is not None:
        _jsonl(tc / "verdicts.jsonl", rows_verdicts)
    old = snapshot.STATE
    try:
        snapshot.STATE = tmp
        s = snapshot.build(now=1_785_400_000.0)
    finally:
        snapshot.STATE = old
    return s


PRE_C1 = {"prereg_id": "pre-c1", "cycle_id": "2026-07-30#1", "goal_key": "g1"}
PRE_C2 = {"prereg_id": "pre-c2", "cycle_id": "2026-07-31#0", "goal_key": "g1"}
J_C1 = {"prereg_id": "pre-c1", "cycle_id": "2026-07-30#1", "slot": 1}
J_C2 = {"prereg_id": "pre-c2", "cycle_id": "2026-07-31#0", "slot": 0}
V_C1 = {"prereg_id": "pre-c1", "cycle_id": "2026-07-30#1", "verdict": "FAIL",
        "goal_key": "g1", "schema": "cycle_verdict.v1"}


def t_a_stale_cycle_rows_never_masquerade_as_the_current_cycle():
    """رگ اصلی: آخرین prereg ِ c2 است؛ journal/verdict فقط برای c1 وجود دارد.
    کدِ قدیمی ([-1]) همین ردیف‌های c1 را به‌عنوانِ «جاری» برمی‌گرداند — قرمز."""
    s = _pinned([PRE_C1, PRE_C2], [J_C1], [V_C1])
    gc = s["goal_cycle"]
    assert gc["prereg"].get("prereg_id") == "pre-c2", gc["prereg"]
    assert gc["journal"] == {}, ("journal از چرخهٔ کهنه نشت کرد", gc["journal"])
    assert gc["verdict"] == {}, ("حکمِ چرخهٔ کهنه به نامِ چرخهٔ جاری", gc["verdict"])
    assert gc["link_basis"] == "prereg_id", gc


def t_b_matching_rows_are_found_by_id_not_by_position():
    """ردیفِ هم‌چرخه حتی اگر وسطِ فایل باشد پیدا می‌شود (کلید، نه جایگاه)."""
    s = _pinned([PRE_C1, PRE_C2], [J_C2, J_C1], [V_C1])
    gc = s["goal_cycle"]
    assert gc["journal"].get("prereg_id") == "pre-c2", gc["journal"]
    assert gc["verdict"] == {}, gc["verdict"]


def t_c_rows_without_prereg_id_fall_back_to_cycle_id():
    j_old_shape = {"cycle_id": "2026-07-31#0", "slot": 0}          # بدونِ prereg_id
    s = _pinned([PRE_C2], [j_old_shape], None)
    gc = s["goal_cycle"]
    assert gc["journal"] == j_old_shape, gc["journal"]
    assert gc["link_basis"] == "prereg_id", gc


def t_d_loop_health_blocker_counts_any_verdict_ever_not_this_cycle():
    """«no-independent-verdict-yet» سلامتِ حلقه است: با وجودِ هر حکمی در دفتر،
    نبودِ حکمِ چرخهٔ در-جریان بازدارنده نیست."""
    s = _pinned([PRE_C1, PRE_C2], [J_C1], [V_C1])
    assert "no-independent-verdict-yet" not in s["blockers"], s["blockers"]
    s2 = _pinned([PRE_C2], None, None)
    assert "no-independent-verdict-yet" in s2["blockers"], s2["blockers"]


def t_e_counts_still_cover_the_whole_ledgers():
    s = _pinned([PRE_C1, PRE_C2], [J_C1], [V_C1])
    c = s["goal_cycle"]["counts"]
    assert c == {"prereg": 2, "cycles": 1, "verdicts": 1}, c


def t_f_empty_ledgers_keep_the_old_contract():
    s = _pinned(None, None, None)
    gc = s["goal_cycle"]
    assert gc["prereg"] == {} and gc["journal"] == {} and gc["verdict"] == {}, gc
    assert gc["link_basis"] is None, gc
    assert "no-preregistered-goal" in s["blockers"], s["blockers"]


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
