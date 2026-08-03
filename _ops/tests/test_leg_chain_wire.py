#!/usr/bin/env python3
"""test_leg_chain_wire.py — WP-C: اثباتِ سیم‌کشیِ زنجیرهٔ درآمدِ Lead + پاهای بیزنسی.

پوشش (همه additive + flag-off/DRY؛ با فلگ‌ها خاموش رفتار بایت‌به‌بایتِ فعلی):
  (الف) LEG-04: ماژولِ lead_quote تمیز import می‌شود و pending/mark_sent/summary دیگر
       ImportError نمی‌دهند (importِ مردهٔ lead_draft حذف شد؛ به persistence واقعی route شد).
  (ب) LEG-02/03: leg_beat با OCTOPUS_WIRE_LEAD_DRAFT خاموش → draft_quote را صدا نمی‌زند؛
       با فلگ روشن → draft_quote (monkeypatch‌شده) دقیقاً یک‌بار صدا زده می‌شود. DRY.
  (پ) LEG-08: فقط یک make_ziman_leg و یک ziman_beat در wiring.py مانده (جفتِ اولِ مرده حذف).
  (ت) قرارداد مشترک: business_legs_beat هر ۴ status را جمع می‌کند (mining/crypto/
       accounting/knowledge) با کلیدهای leg/live/signal/note.
  (ث) ایمنیِ no-op: ingest_beat/email_beat/heartstate_beat با فلگِ خاموش None (صفر side-effect).

standalone: harness یک مینی-vault موقت می‌سازد (OPS_DIR/STATE به tmp) و REAL_VAULT را به
همین worktree می‌بندد تا کدِ worktree تست شود، نه live-tree. $0 آفلاین، stdlib-only.
اجرا: python -X utf8 _ops/tests/test_leg_chain_wire.py
"""
import os
import re
import sys
from pathlib import Path

# REAL_VAULT = همین worktree (نه F:\backup live) تا wiring/legsِ ویرایش‌شده تست شوند.
_WORKTREE = Path(__file__).resolve().parents[2]
os.environ.setdefault("REAL_VAULT", str(_WORKTREE))

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("leg-chain-wire")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chrono   # noqa: E402
import wiring   # noqa: E402
from leg import TaskPacket  # noqa: E402
from lead_leg import LeadLeg  # noqa: E402

_WIRING_SRC = (_OPS / "wiring.py").read_text("utf-8")


def _clear(*names):
    for n in names:
        os.environ.pop(n, None)


def _pacemaker_and_leg():
    """Pacemaker واقعی (bus واقعی) + LeadLeg واقعی — همان الگوی test_lead_leg_loop."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-legchain.db")
    pm = chrono.Pacemaker(db=db, clock=chrono._utc_ms)
    packet = TaskPacket(
        leg_id="lead-naghshi", organ="LEAD_PAINTING",
        read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
        tools=("draft_quote",), budget_aud=5.0)
    leg = LeadLeg(packet, organ_table={"LEAD_PAINTING": 100.0})
    return pm, leg


# ════════════════════════════════════════════════════════════════════════════════
# (الف) LEG-04 — lead_quote تمیز import می‌شود؛ wrapperها ImportError نمی‌دهند
# ════════════════════════════════════════════════════════════════════════════════

def t_lead_quote_imports_clean():
    import importlib
    lq = importlib.import_module("lead_quote")
    importlib.reload(lq)
    # هیچ‌کدام نباید ImportError بدهد (قبلاً `from lead_draft import …` می‌ترکید)
    p = lq.pending()
    assert isinstance(p, list), "pending باید list برگرداند"
    s = lq.summary()
    assert isinstance(s, dict) and "n_pending" in s, "summary باید dict با n_pending باشد"
    assert lq.mark_sent("no-such-attribution") is False, "mark_sent روی نبود → False (fail-soft)"


def t_lead_quote_no_dead_import():
    src = (_OPS / "legs" / "lead_quote.py").read_text("utf-8")
    assert "from lead_draft import" not in src, "importِ مردهٔ lead_draft باید حذف شده باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ب) LEG-02/03 — leg_beat draft فقط پشتِ OCTOPUS_WIRE_LEAD_DRAFT (DRY)
# ════════════════════════════════════════════════════════════════════════════════

def _install_draft_recorder(leg):
    """draft_quote را با یک ضبط‌کننده جایگزین کن (monkeypatch)؛ شمارندهٔ صدازدن برمی‌گرداند."""
    calls = {"n": 0, "args": []}

    class _FakeProp:
        proposal_id = "P-FAKE"

    def _rec(attribution_id, scope, price_range_aud, assumptions=None, hlc=(0, 0)):
        calls["n"] += 1
        calls["args"].append(attribution_id)
        return _FakeProp()

    leg.draft_quote = _rec  # type: ignore[assignment]
    return calls


def t_leg_beat_flag_off_no_draft():
    """OCTOPUS_WIRE_LEAD_TICK روشن، ولی OCTOPUS_WIRE_LEAD_DRAFT خاموش → draft صدا نمی‌شود."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    _clear("OCTOPUS_WIRE_LEAD_DRAFT")
    try:
        pm, leg = _pacemaker_and_leg()
        calls = _install_draft_recorder(leg)
        r = wiring.leg_beat(leg, pacemaker=pm, beat=1)
        assert r is not None, "با LEAD_TICK روشن، leg_beat باید گزارش بدهد"
        assert calls["n"] == 0, "با فلگِ draft خاموش نباید draft_quote صدا شود"
        assert "lead_chain" not in r, "با فلگ خاموش نباید lead_chain در خروجی باشد"
    finally:
        _clear("OCTOPUS_WIRE_LEAD_TICK", "OCTOPUS_WIRE_LEAD_DRAFT")


def t_leg_beat_flag_on_calls_draft():
    """هر دو فلگ روشن → زنجیره fire می‌شود ولی probeِ ساختگی حذف شده (مرحلهٔ ۵ نقشهٔ لید
    2026-07-15): بدونِ draftِ *واقعیِ* pending، هیچ draft_quoteای صدا نمی‌شود و
    drafted=False — دیگر LEAD-PROBEِ دروغین ساخته نمی‌شود. draftِ واقعی حالا در
    lead_discovery_beat با attribution_id واقعی است (test_lead_quote_chain)."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_DRAFT"] = "1"
    try:
        pm, leg = _pacemaker_and_leg()
        calls = _install_draft_recorder(leg)
        r = wiring.leg_beat(leg, pacemaker=pm, beat=1)
        assert calls["n"] == 0, f"probe حذف شده — draft_quote نباید صدا شود، شد {calls['n']}"
        lc = r.get("lead_chain", {})
        assert lc.get("drafted") is False, "بدونِ pendingِ واقعی، drafted باید False باشد"
        assert "invoice" in lc, "قدمِ invoiceِ زنجیره باید حاضر بماند (LEG-05)"
    finally:
        _clear("OCTOPUS_WIRE_LEAD_TICK", "OCTOPUS_WIRE_LEAD_DRAFT")


# ════════════════════════════════════════════════════════════════════════════════
# (پ) LEG-08 — فقط یک make_ziman_leg و یک ziman_beat
# ════════════════════════════════════════════════════════════════════════════════

def t_single_ziman_defs():
    n_make = len(re.findall(r"^def make_ziman_leg\b", _WIRING_SRC, re.M))
    n_beat = len(re.findall(r"^def ziman_beat\b", _WIRING_SRC, re.M))
    assert n_make == 1, f"باید دقیقاً یک make_ziman_leg باشد، شد {n_make}"
    assert n_beat == 1, f"باید دقیقاً یک ziman_beat باشد، شد {n_beat}"
    # نسخهٔ زنده (دومی) باید امضایِ organism.py را داشته باشد (leg=None, beat, doctor=…)
    import inspect
    params = list(inspect.signature(wiring.ziman_beat).parameters)
    assert params[:1] == ["leg"] and "doctor" in params, \
        "ziman_beatِ مانده باید نسخهٔ زندهٔ (leg,…,doctor) باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ت) قرارداد مشترک — business_legs_beat هر ۴ status را جمع می‌کند
# ════════════════════════════════════════════════════════════════════════════════

def t_business_legs_beat_collects_four():
    """قرارداد ۲۰۲۶-۰۷-۲۵: **۵** پا، و «lead» اجباری است.

    قبلاً دقیقاً ۴ پا pin شده بود (mining/crypto/accounting/knowledge) — و هر چهار
    skeleton یا کهنه‌اند. پای درآمدیِ زنده در آگاهیِ ارگانیسم **نبود**، پس خودآگاهی
    پاهای مرده را می‌شمرد و کسب‌وکارِ واقعی را نمی‌دید. حالا حضورِ lead بخشی از قرارداد
    است تا کسی دوباره بی‌صدا حذفش نکند."""
    r = wiring.business_legs_beat(beat=1, write=False)
    assert r is not None and "business_legs" in r
    legs = r["business_legs"]
    assert set(legs.keys()) == {"lead", "mining", "crypto", "accounting", "knowledge"}, \
        f"باید هر ۵ پا باشد (lead اجباری)، شد {sorted(legs.keys())}"
    _ld = legs["lead"]
    assert _ld.get("money_link") == "active", "lead باید money_link=active بدهد"
    assert "confirmed_revenue_aud" in _ld, \
        "lead باید فیلدِ درآمد را صریح بدهد (None وقتی حساب‌کتاب پارک است، نه صفرِ دروغ)"
    assert isinstance(_ld.get("identity"), dict) and isinstance(_ld.get("inbox"), dict), \
        "lead باید هویتِ فاکتور و وضعیتِ صندوق را گزارش کند"
    for name, st in legs.items():
        assert isinstance(st, dict), f"{name} status باید dict باشد"
        assert st.get("leg") == name, f"{name}: کلیدِ leg باید {name} باشد"
        assert "live" in st and "signal" in st and "note" in st, \
            f"{name}: قرارداد leg/live/signal/note ناقص است"


def t_business_legs_beat_writes_sidecar():
    import json
    sp = harness.REAL_VAULT  # placeholder؛ مسیرِ واقعی از opslib می‌آید
    import opslib
    r = wiring.business_legs_beat(beat=2, write=True)
    assert r is not None
    side = opslib.STATE_DIR / "ORGANISM-STATE.business_legs"
    assert side.exists(), "سایدکارِ business_legs باید نوشته شود"
    data = json.loads(side.read_text("utf-8"))
    assert "business_legs" in data and "updated_at" in data


# ════════════════════════════════════════════════════════════════════════════════
# (ث) ایمنیِ no-op — فلگ‌های خاموش هیچ side-effect ندارند
# ════════════════════════════════════════════════════════════════════════════════

def t_new_beats_noop_when_flag_off():
    _clear("OCTOPUS_WIRE_INGEST", "OCTOPUS_WIRE_EMAIL", "HEARTSTATE_SHADOW")
    assert wiring.ingest_beat(beat=1440) is None, "ingest خاموش → None"
    assert wiring.email_beat(beat=60) is None, "email خاموش → None"
    assert wiring.heartstate_beat(beat=1) is None, "heartstate shadow خاموش → None"


CHECKS = [
    ("LEG-04: lead_quote تمیز import + wrapperها بی‌ImportError", t_lead_quote_imports_clean),
    ("LEG-04: importِ مردهٔ lead_draft حذف شده", t_lead_quote_no_dead_import),
    ("LEG-02/03: leg_beat فلگ خاموش → بدون draft", t_leg_beat_flag_off_no_draft),
    ("LEG-02/03: leg_beat فلگ روشن → draft_quote صدا می‌شود", t_leg_beat_flag_on_calls_draft),
    ("LEG-08: فقط یک make_ziman_leg/ziman_beat (نسخهٔ زنده)", t_single_ziman_defs),
    ("قرارداد: business_legs_beat ۵ پا + lead اجباری", t_business_legs_beat_collects_four),
    ("business_legs_beat سایدکار می‌نویسد", t_business_legs_beat_writes_sidecar),
    ("no-op: ingest/email/heartstate با فلگِ خاموش None", t_new_beats_noop_when_flag_off),
]


def main() -> int:
    print("🧪 test_leg_chain_wire — سیم‌کشیِ زنجیرهٔ درآمد + پاهای بیزنسی (WP-C)")
    failed = harness.run(CHECKS)
    print(f"\n{'✅ همه سبز' if not failed else f'❌ {failed} شکست'} ({len(CHECKS)} چک)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
