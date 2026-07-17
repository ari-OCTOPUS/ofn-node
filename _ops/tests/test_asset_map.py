#!/usr/bin/env python3
"""test_asset_map.py — ASSET-OVERSIGHT (2026-07-16): aggregatorِ نظارتِ داراییِ کل.

اثبات می‌کند:
  * wiring.asset_map_beat با فلگِ خاموش → None (رفتارِ امروز، بایت‌به‌بایت).
  * asset_map_status ≥۳ پا را از fixtureها جمع می‌کند (assets/categories/as_of).
  * یک پای خراب (callable که raise می‌کند) → نقشه هنوز برمی‌گردد (fail-soft) و آن پا
    unavailable علامت می‌خورد (بقیهٔ پاها سالم).
  * برای یک fixtureِ کهنه (age_days > آستانه) پیشنهادِ refresh در proposals هست.
  * خروجی هرگز مبلغ/PII را leak نمی‌کند — کلیدهای غیرمجازِ منبع (amount_aud/note/مسیر)
    در نقشه ظاهر نمی‌شوند و sentinelِ مبلغ در کلِ json نیست.
  * با فلگِ روشن، asset_map_beat واقعاً نقشه می‌سازد + سایدکارِ اتمیک می‌نویسد.

اجرا: REAL_VAULT=worktree PYTHONIOENCODING=utf-8 python -X utf8 test_asset_map.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness  # noqa: E402
ENV = harness.setup("asset_map")

import opslib      # noqa: E402
import asset_map   # noqa: E402
import wiring      # noqa: E402

_SAFE_KEYS = {"leg", "category", "live", "age_days", "signal"}
_AMOUNT_SENTINEL = "987654.21"   # «مبلغِ» جعلی که هرگز نباید leak شود
_PII_SENTINEL = "C:/bank/secret-statement.xlsx"


def _fixture_sources() -> dict:
    """۵ پای ساختگی: ۳ سالم، ۱ کهنه، ۱ خراب — هر منبع کلیدهای اضافیِ خطرناک هم دارد
    تا اثباتِ whitelist ممکن شود."""
    def crypto():
        return {"leg": "crypto", "live": True, "signal": "buy=3 sell=2 hold=5",
                "age_days": 1.2, "note": _PII_SENTINEL, "amount_aud": _AMOUNT_SENTINEL}

    def accounting():
        # کهنه: age_days > ASSET_STALE_DAYS → باید پیشنهادِ refresh بسازد
        return {"leg": "accounting", "live": False, "signal": "workbooks=6",
                "age_days": 90.0, "note": "منبعِ مالی", "amount_aud": _AMOUNT_SENTINEL}

    def ziman():
        return {"leg": "ziman", "live": True, "signal": "families=4 drafts=2",
                "age_days": None}

    def revenue():
        return {"leg": "revenue", "live": False,
                "signal": "claimed=0 confirmed=0 coverage=None", "age_days": None}

    def broken():
        raise RuntimeError("leg exploded")

    return {
        "crypto":     ("digital-assets",  crypto),
        "accounting": ("financial-books", accounting),
        "ziman":      ("inventory",       ziman),
        "revenue":    ("revenue",         revenue),
        "mining":     ("mining-hardware", broken),
    }


def test_flag_off_beat_returns_none() -> None:
    """فلگِ خاموش → asset_map_beat باید None بدهد (not wired)."""
    import os
    os.environ.pop("OCTOPUS_WIRE_ASSET_MAP", None)
    assert wiring.asset_map_beat(beat=240) is None


def test_aggregates_at_least_three_legs() -> None:
    """نقشه از fixtureها ≥۳ پا جمع می‌کند؛ categories و as_of حاضرند."""
    m = asset_map.asset_map_status(sources=_fixture_sources())
    assert isinstance(m, dict)
    assert len(m["assets"]) >= 3, m["assets"]
    assert m["categories"] >= 3, m["categories"]
    assert isinstance(m.get("as_of"), str) and m["as_of"], "as_of لازم است"
    assert m.get("propose_only") is True


def test_broken_leg_is_failsoft() -> None:
    """یک پای raise-کننده نباید نقشه را بکشد؛ آن پا unavailable، بقیه سالم."""
    m = asset_map.asset_map_status(sources=_fixture_sources())
    assert "mining" in m["unavailable"], m["unavailable"]
    mining = next(a for a in m["assets"] if a["leg"] == "mining")
    assert mining["live"] is False and "unavailable" in mining["signal"], mining
    # پاهای سالم دست‌نخورده‌اند
    crypto = next(a for a in m["assets"] if a["leg"] == "crypto")
    assert crypto["live"] is True and "buy=3" in crypto["signal"], crypto


def test_stale_fixture_yields_refresh_proposal() -> None:
    """fixtureِ کهنه (accounting 90d) → پیشنهادِ refresh در proposals + stale_count≥۱."""
    m = asset_map.asset_map_status(sources=_fixture_sources())
    assert m["stale_count"] >= 1, m["stale_count"]
    joined = " | ".join(m["proposals"])
    assert "accounting" in joined and "refresh" in joined, joined
    # پیشنهادِ صداقتِ net-worth همیشه هست
    assert any("net-worth" in p for p in m["proposals"]), m["proposals"]


def test_never_leaks_amount_or_pii() -> None:
    """کلیدهای غیرمجازِ منبع (amount_aud/note/مسیر) در نقشه نیستند و sentinelِ مبلغ/PII
    در کلِ json ظاهر نمی‌شود."""
    m = asset_map.asset_map_status(sources=_fixture_sources())
    for a in m["assets"]:
        extra = set(a.keys()) - _SAFE_KEYS
        assert not extra, f"کلیدِ غیرمجاز در asset: {extra}"
    dump = json.dumps(m, ensure_ascii=False)
    assert _AMOUNT_SENTINEL not in dump, "مبلغ leak شد!"
    assert _PII_SENTINEL not in dump, "PII/مسیر leak شد!"
    assert "amount_aud" not in dump, "کلیدِ مبلغ leak شد!"


def test_flag_on_beat_builds_map_and_sidecar() -> None:
    """با فلگِ روشن، asset_map_beat نقشهٔ واقعی (پاهای worktree) می‌سازد + سایدکار می‌نویسد.
    beat=0 تا گاردِ cadence رد نشود."""
    import os
    os.environ["OCTOPUS_WIRE_ASSET_MAP"] = "1"
    try:
        r = wiring.asset_map_beat(beat=0)
        assert isinstance(r, dict), r
        assert "assets" in r and "proposals" in r and "as_of" in r
        # هیچ مبلغی حتی در نقشهٔ واقعی نباید باشد
        assert _AMOUNT_SENTINEL not in json.dumps(r, ensure_ascii=False)
        sp = opslib.STATE_DIR / "ORGANISM-STATE.asset_map"
        assert sp.exists(), "سایدکارِ ORGANISM-STATE.asset_map نوشته نشد"
        side = json.loads(sp.read_text("utf-8"))
        assert side.get("propose_only") is True
    finally:
        os.environ.pop("OCTOPUS_WIRE_ASSET_MAP", None)


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_asset_map: {len(_tests)}/{len(_tests)} سبز")
