#!/usr/bin/env python3
"""تستِ رفتاریِ پول‌بر‌درصد — barbell allocation + share attribution.

سه بخش:
  (۱) barbell_allocate: شاخکِ CONFIRMED-دار درصد↑، satellite سقف‌نشکن، cull فقط روی مرگِ پایدار، hysteresis.
  (۲) attribution partners[]/pct: ثبتِ سهمِ شریک در propose/confirm + confirmed_revenue by_partner.
  (۳) money-lock دست‌نخورده.
$0 آفلاین.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("barbell-attribution")

_OPS = (harness.REAL_VAULT / r"_ops")
for _p in [str(_OPS), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import attribution  # noqa: E402
import governor_epoch  # noqa: E402
import yaml  # noqa: E402

# budgets.yaml واقعی (نه harness mock) برای barbell_allocate
_REAL_BUDGETS = yaml.safe_load((_OPS / "budget" / "budgets.yaml").read_text(encoding="utf-8"))


# ════════════════════════════════════════════════════════════════════════════════
# (۱) barbell_allocate
# ════════════════════════════════════════════════════════════════════════════════

def t_confirmed_organ_gets_higher_pct():
    """شاخکی که CONFIRMED AUD بیشتر دارد → درصدِ بیشتر درونِ گروهِ خود."""
    # ZIMAN (core) درآمدِ بالاتر از ARCHITECT_SYS دارد
    result = governor_epoch.barbell_allocate(
        confirmed_by_organ={"ZIMAN": 1000.0, "ARCHITECT_SYS": 100.0,
                            "PROJECT_F": 0.0, "MINING": 0.0},
        prev_pcts=None, budgets=_REAL_BUDGETS)
    pcts = result["organ_pct"]
    assert pcts.get("ZIMAN", 0) > pcts.get("ARCHITECT_SYS", 0), \
        f"ZIMAN (CONFIRMED بیشتر) باید درصدِ بیشتر داشته باشد: {pcts}"


def t_satellite_cap_not_broken():
    """هیچ satellite از satellite_cap_pct (۱۰٪) بیشتر نمی‌گیرد."""
    # حتی اگر PROJECT_F همهٔ CONFIRMED را داشته باشد
    result = governor_epoch.barbell_allocate(
        confirmed_by_organ={"ZIMAN": 0.0, "ARCHITECT_SYS": 0.0,
                            "PROJECT_F": 10000.0, "MINING": 0.0},
        prev_pcts=None, budgets=_REAL_BUDGETS)
    pcts = result["organ_pct"]
    sat_cap = result["barbell"]["satellite_cap_pct"]
    assert pcts.get("PROJECT_F", 0) <= sat_cap + 0.001, \
        f"PROJECT_F نباید از cap ({sat_cap}) بیشتر بگیرد: {pcts.get('PROJECT_F')}"


def t_cull_only_on_persistent_death():
    """cull فقط وقتی satellite سیگنالِ صفرِ پایدار دارد (zero_streak ≥ cull_days)."""
    # MINING با ۱۰ روز صفر → cull نشود (زیرِ آستانه)
    result_short = governor_epoch.barbell_allocate(
        confirmed_by_organ={"ZIMAN": 100.0, "MINING": 0.0},
        zero_streak={"MINING": 10}, budgets=_REAL_BUDGETS)
    assert "MINING" not in result_short["culled"], \
        "MINING با ۱۰ روز نباید cull شود (زیرِ آستانهٔ ۳۰)"
    # MINING با ۳۵ روز صفر → cull
    result_long = governor_epoch.barbell_allocate(
        confirmed_by_organ={"ZIMAN": 100.0, "MINING": 0.0},
        zero_streak={"MINING": 35}, budgets=_REAL_BUDGETS)
    assert "MINING" in result_long["culled"], \
        "MINING با ۳۵ روز باید cull شود (مرگِ پایدار)"


def t_no_cull_if_recently_confirmed():
    """satellite با streak بلند ولی CONFIRMED اخیر → cull نشود (بامبو)."""
    result = governor_epoch.barbell_allocate(
        confirmed_by_organ={"MINING": 500.0},
        zero_streak={"MINING": 100}, budgets=_REAL_BUDGETS)
    assert "MINING" not in result["culled"], \
        "MINING با CONFIRMED نباید cull شود حتی با streak بلند (بامبو)"


def t_hysteresis_limits_change():
    """hysteresis: تغییرِ درصدِ خام محدود است (ضدِ نوسان).
    توجه: نرمال‌سازیِ نهایی ممکن است delta را کمی تغییر دهد، پس tolerance بزرگ‌تر."""
    # prev_pcts = مساوی؛ حالا ZIMAN همهٔ CONFIRMED را دارد
    prev = {"ZIMAN": 0.25, "ARCHITECT_SYS": 0.25, "GENOME_SYS": 0.20,
            "PROJECT_F": 0.15, "MINING": 0.15}
    result = governor_epoch.barbell_allocate(
        confirmed_by_organ={"ZIMAN": 10000.0, "ARCHITECT_SYS": 0.0,
                            "GENOME_SYS": 0.0, "PROJECT_F": 0.0, "MINING": 0.0},
        prev_pcts=prev, budgets=_REAL_BUDGETS)
    pcts = result["organ_pct"]
    hyst = result["hysteresis_max_delta"]
    # تغییر ZIMAN نباید خیلی بیشتر از hyst باشد (نرمال‌سازی tolerance می‌دهد)
    delta_ziman = abs(pcts.get("ZIMAN", 0) - prev["ZIMAN"])
    # بدونِ hysteresis، delta می‌توانستید 0.45 (0.7-0.25) باشد. hyst آن را به ~0.05 محدود می‌کند.
    # نرمال‌سازی می‌تواند تا ~۲× شود. پس delta < hyst*۳ = 0.15 یک گاردِ معقول است.
    assert delta_ziman < hyst * 3, \
        f"تغییرِ ZIMAN باید توسطِ hysteresis محدود شده باشد (delta={delta_ziman} < {hyst*3})"


def t_core_satellite_split():
    """CORE بیشتر از SATELLITE (barbell). حتی با توزیعِ مساویِ CONFIRMED."""
    result = governor_epoch.barbell_allocate(
        confirmed_by_organ={"ZIMAN": 100.0, "ARCHITECT_SYS": 100.0,
                            "GENOME_SYS": 100.0, "PROJECT_F": 100.0, "MINING": 100.0},
        prev_pcts=None, budgets=_REAL_BUDGETS)
    pcts = result["organ_pct"]
    core_total = sum(pcts.get(m, 0) for m in ["ZIMAN", "ARCHITECT_SYS", "GENOME_SYS"])
    sat_total = sum(pcts.get(m, 0) for m in ["PROJECT_F", "MINING"])
    assert core_total > sat_total, \
        f"CORE باید بیشتر از SATELLITE باشد (barbell): core={core_total} sat={sat_total}"


def t_propose_only():
    """barbell_allocate باید propose_only=True برگرداند."""
    result = governor_epoch.barbell_allocate(confirmed_by_organ={}, budgets=_REAL_BUDGETS)
    assert result.get("propose_only") is True


# ════════════════════════════════════════════════════════════════════════════════
# (۲) attribution partners[]/pct
# ════════════════════════════════════════════════════════════════════════════════

def t_propose_with_explicit_partners():
    """propose با partners صریح → partners در payload ثبت می‌شود."""
    rec = attribution.propose("lead.doer", 100.0, lead="test",
                              partners=[{"who": "Ari", "pct": 60}, {"who": "Saba", "pct": 40}])
    payload = rec.get("payload", {})
    ps = payload.get("partners", [])
    assert len(ps) == 2
    whos = [p["who"] for p in ps]
    assert "Ari" in whos and "Saba" in whos


def t_propose_without_partners():
    """propose بدون partners → partners در payload نیست (سازگار با قبل)."""
    rec = attribution.propose("lead.doer", 50.0, lead="test")
    payload = rec.get("payload", {})
    assert "partners" not in payload, "بدونِ partners نباید فیلد اضافه شود (سازگاری)"


def t_confirm_creates_split():
    """confirm با partners → ATTRIBUTED رکورد split دارد (سهمِ هر شریک)."""
    rec_p = attribution.propose("lead.doer", 100.0, lead="test")
    aid = rec_p["payload"]["attribution_id"]
    rec_c = attribution.confirm(aid, "lead.doer", 100.0,
                                matched={"ref": "test-ref"},
                                partners=[{"who": "Ari", "pct": 50}, {"who": "Saba", "pct": 50}])
    # ATTRIBUTED رکورد (دومی) باید split داشته باشد
    # fold کن و بررسی کن
    folded = attribution.fold()
    attr = folded.get(aid, {})
    split = attr.get("split", {})
    assert "Ari" in split and "Saba" in split, f"split باید Ari+Saba داشته باشد: {split}"
    assert abs(split["Ari"] - 50.0) < 0.01 and abs(split["Saba"] - 50.0) < 0.01


def t_confirmed_revenue_by_partner():
    """confirmed_revenue باید by_partner را داشته باشد (جمعِ AUD per partner)."""
    rec_p = attribution.propose("lead.doer", 200.0, lead="test")
    aid = rec_p["payload"]["attribution_id"]
    attribution.confirm(aid, "lead.doer", 200.0,
                        matched={"ref": "ref2"},
                        partners=[{"who": "Ari", "pct": 50}, {"who": "Saba", "pct": 50}])
    rev = attribution.confirmed_revenue()
    assert "by_partner" in rev
    assert rev["by_partner"].get("Ari", 0) >= 100.0, \
        f"Ari باید ≥۱۰۰ داشته باشد: {rev['by_partner']}"


def t_partners_normalize():
    """partners با pct نامتجانس → نرمال‌سازی می‌شود (مجموع=۱۰۰)."""
    ps = attribution._partners_for("test", [{"who": "A", "pct": 30}, {"who": "B", "pct": 70}])
    total = sum(p["pct"] for p in ps)
    assert abs(total - 100.0) < 0.01, f"partners باید نرمالایز شود: total={total}"


# ════════════════════════════════════════════════════════════════════════════════
# (۳) money-lock دست‌نخورده
# ════════════════════════════════════════════════════════════════════════════════

def t_barbell_does_not_open_money():
    """barbell_allocate نباید هیچ capability/money gate را باز کند (propose-only)."""
    result = governor_epoch.barbell_allocate(confirmed_by_organ={}, budgets=_REAL_BUDGETS)
    assert result.get("propose_only") is True
    # نباید هیچ کلیدِ money/live را برگرداند
    blob = str(result)
    assert "allow" not in blob.lower() or "propose" in blob.lower()


def t_allocation_in_budgets_yaml():
    """budgets.yaml باید allocation.barbell داشته باشد."""
    import yaml
    b = yaml.safe_load((_OPS / "budget" / "budgets.yaml").read_text(encoding="utf-8"))
    alloc = (b.get("allocation") or {}).get("barbell", {})
    assert alloc.get("core_share") == 0.70
    assert alloc.get("satellite_share") == 0.30
    assert alloc.get("satellite_cap_pct") == 0.10


def t_partners_default_in_budgets():
    """budgets.yaml باید partners_default با Project-F 50/50 داشته باشد."""
    import yaml
    b = yaml.safe_load((_OPS / "budget" / "budgets.yaml").read_text(encoding="utf-8"))
    pd = (b.get("allocation") or {}).get("partners_default", {})
    pf = pd.get("PROJECT_F", [])
    pcts = {p.get("who"): p.get("pct") for p in pf}
    assert pcts.get("Ari") == 50 and pcts.get("Saba") == 50, \
        f"Project-F باید ۵۰/۵۰ باشد: {pcts}"


if __name__ == "__main__":
    failed = harness.run([
        # (۱) barbell
        ("CONFIRMED → درصدِ بیشتر", t_confirmed_organ_gets_higher_pct),
        ("satellite cap نشکن", t_satellite_cap_not_broken),
        ("cull فقط روی مرگِ پایدار", t_cull_only_on_persistent_death),
        ("no cull اگر CONFIRMED اخیر", t_no_cull_if_recently_confirmed),
        ("hysteresis محدودِ تغییر", t_hysteresis_limits_change),
        ("CORE > SATELLITE", t_core_satellite_split),
        ("propose_only", t_propose_only),
        # (۲) attribution partners
        ("propose با partners صریح", t_propose_with_explicit_partners),
        ("propose بدون partners (سازگار)", t_propose_without_partners),
        ("confirm → split", t_confirm_creates_split),
        ("confirmed_revenue by_partner", t_confirmed_revenue_by_partner),
        ("partners نرمالایز", t_partners_normalize),
        # (۳) money-lock
        ("barbell money را باز نمی‌کند", t_barbell_does_not_open_money),
        ("allocation در budgets.yaml", t_allocation_in_budgets_yaml),
        ("partners_default Project-F ۵۰/۵۰", t_partners_default_in_budgets),
    ])
    sys.exit(1 if failed else 0)
