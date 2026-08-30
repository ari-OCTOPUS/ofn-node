"""test_stuck_money — نقطهٔ کورِ ۱۳۴: کارتِ پولی که در نیمهٔ راه یخ می‌زند.

دو قیدِ متضاد که باید هم‌زمان برقرار باشند:
  · **دیده شود** — کارتی که در APPROVING بماند نباید ساکت گم شود.
  · **دست نخورد** — این ماژول حق ندارد هیچ گذارِ پولی را انجام دهد؛ جارویی که
    کارتِ کهنه را خودش ببندد، مجریِ خودکارِ پول است.

و یک قیدِ ظریف: رکوردِ بدونِ مهرِ زمان باید **مشکوک** شمرده شود، نه تازه. اگر
سنِ نامعلوم را صفر بگیریم، دقیقاً رکوردهایی که بیشترین احتمالِ خرابی را دارند از
رادار حذف می‌شوند.
"""
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("stuck-money")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import stuck_money as sm   # noqa: E402

NOW = 1_800_000_000.0
H = 3600.0


def _write(store: dict):
    p = sm._store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(store, ensure_ascii=False), "utf-8")


def _clear():
    try:
        sm._store_path().unlink()
    except OSError:
        pass


# ─── دیده‌شدن ──────────────────────────────────────────────────────────────
def t_an_old_approving_card_is_surfaced():
    _clear()
    _write({"money:e1": {"decision": "APPROVING", "ts": NOW - 5 * H}})
    rows = sm.scan(now=NOW)
    assert len(rows) == 1 and rows[0]["effect_id"] == "e1", rows
    assert rows[0]["age_h"] == 5.0, rows


def t_reconcile_required_counts_as_stuck_too():
    _clear()
    _write({"money:e1": {"decision": "RECONCILE_REQUIRED", "ts": NOW - 9 * H}})
    assert len(sm.scan(now=NOW)) == 1


def t_a_fresh_approving_card_is_not_noise():
    """چند دقیقه در APPROVING طبیعی است — آلارمِ زودرس یعنی آلارمِ نادیده."""
    _clear()
    _write({"money:e1": {"decision": "APPROVING", "ts": NOW - 60}})
    assert sm.scan(now=NOW) == []


def t_finished_states_are_never_flagged():
    _clear()
    _write({f"money:e{i}": {"decision": d, "ts": NOW - 99 * H}
            for i, d in enumerate(("APPROVED", "DENIED", "EXPIRED",
                                   "PENDING", "DEFERRED"))})
    assert sm.scan(now=NOW) == [], sm.scan(now=NOW)


def t_a_record_without_a_timestamp_is_suspect_not_fresh():
    """نبودِ شواهد دلیلِ بی‌گناهی نیست — به‌ویژه در مسیرِ پول."""
    _clear()
    _write({"money:e1": {"decision": "APPROVING"}})
    rows = sm.scan(now=NOW)
    assert len(rows) == 1 and rows[0]["age_h"] is None, rows
    assert "نامعلوم" in rows[0]["why"], rows


def t_the_oldest_and_the_unknown_come_first():
    _clear()
    _write({"money:new": {"decision": "APPROVING", "ts": NOW - 3 * H},
            "money:old": {"decision": "APPROVING", "ts": NOW - 40 * H},
            "money:none": {"decision": "APPROVING"}})
    order = [r["effect_id"] for r in sm.scan(now=NOW)]
    assert order[0] == "none", order       # سنِ نامعلوم بالاترین اولویت
    assert order[1] == "old", order


def t_non_money_records_are_ignored():
    _clear()
    _write({"task:t1": {"decision": "APPROVING", "ts": NOW - 99 * H},
            "money:e1": {"decision": "APPROVING", "ts": NOW - 99 * H}})
    assert [r["effect_id"] for r in sm.scan(now=NOW)] == ["e1"]


def t_iso_timestamps_are_understood():
    _clear()
    iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(NOW - 6 * H))
    _write({"money:e1": {"decision": "APPROVING", "updated": iso}})
    rows = sm.scan(now=NOW)
    assert len(rows) == 1 and 5.5 < (rows[0]["age_h"] or 0) < 6.5, rows


# ─── دست‌نزدن ──────────────────────────────────────────────────────────────
def t_the_scan_never_writes_anything():
    _clear()
    _write({"money:e1": {"decision": "APPROVING", "ts": NOW - 99 * H}})
    before = sm._store_path().read_bytes()
    sm.scan(now=NOW)
    sm.card(now=NOW)
    assert sm._store_path().read_bytes() == before, "اسکن فایل را عوض کرد"


def t_the_module_cannot_transition_a_money_state():
    import ast
    tree = ast.parse(Path(sm.__file__).read_text("utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("persist_money_decision", "_mutate_store", "_save_store",
              "write_text", "settle", "apply", "unlink"):
        assert d not in called, f"ماژولِ فقط‌ناظر عمل می‌کند: {d}"
    banned = {"subprocess", "urllib", "requests", "socket"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)


# ─── کارت ──────────────────────────────────────────────────────────────────
def t_the_card_is_quiet_when_nothing_is_stuck():
    _clear()
    body = sm.card(now=NOW)
    assert "هیچ پرداختی نیمه‌کاره نیست" in body


def t_the_card_says_why_it_refuses_to_finish_them():
    _clear()
    _write({"money:e1": {"decision": "APPROVING", "ts": NOW - 99 * H}})
    body = sm.card(now=NOW)
    assert "پول هرگز خودکار نیست" in body, body
    assert "نکنی:" in body


def t_a_missing_or_broken_store_is_not_a_crash():
    _clear()
    assert sm.scan(now=NOW) == []
    sm._store_path().parent.mkdir(parents=True, exist_ok=True)
    for junk in ("", "{", "[]", "null", "نه‌JSON"):
        sm._store_path().write_text(junk, "utf-8")
        assert sm.scan(now=NOW) == [], junk
        assert sm.card(now=NOW)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_stuck_money: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
