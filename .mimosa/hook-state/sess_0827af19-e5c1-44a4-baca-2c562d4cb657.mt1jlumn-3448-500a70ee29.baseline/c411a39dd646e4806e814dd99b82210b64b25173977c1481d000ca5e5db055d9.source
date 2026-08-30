#!/usr/bin/env python3
"""test_ziman_catalog_bridge.py — برنامهٔ ۸: پلِ read-only کاتالوگِ زیمان.

پوشش:
  * نبود/خرابیِ کاتالوگ → دقیقاً رفتارِ قدیمِ C1–C4 (fail-soft، بدون کرش)
  * کاتالوگِ واقعی (شکلِ ziman-catalog.json) → خانواده‌های F1..F4/OTHER +
    شمارشِ per-family + پرچم‌های perishable/alcohol_suspect/edible
  * resolution از opslib.ORG_ROOT (ایزوله‌پذیر با harness) + گاردِ allowlist (D2)
  * aliasِ کدهای قدیمیِ C1–C4 و propose-only ماندنِ همه‌چیز

pytest-style + قابلِ اجرای مستقیم (python test_ziman_catalog_bridge.py).
$0 آفلاین · stdlib-only · هیچ دستی به vault زنده.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_OPS = _TESTS.parent
_VAULT = _OPS.parent
# درختِ زیرِ تست = همین درخت (نظمِ worktree) — مگر صریحاً override شده باشد
os.environ.setdefault("REAL_VAULT", str(_VAULT))

import harness  # noqa: E402

ENV = harness.setup("ziman-catalog")   # ORG_ROOT → مینی-vault موقت (قبل از import opslib)

for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from leg import TaskPacket  # noqa: E402
from ziman_leg import (LEGACY_FAMILY_ALIAS, PRODUCT_FAMILIES,  # noqa: E402
                       ZIMAN_CATALOG_NOTE, ZimanLeg)


# ─── fixture: کپیِ شکلِ واقعیِ ziman-catalog.json (فیلدها عینِ فایلِ زمینی) ────
def _fixture_catalog() -> dict:
    return {
        "products": [
            {"product_id": "ZIM-F1-01", "family": "F1_floral",
             "photo_files": ["IMG_A.jpg"], "one_line": "silk rose box",
             "form": "cube box", "palette": "red", "edible": "none",
             "perishable": False,
             "medium": ["silk roses", "satin ribbon"],
             "occasion_fit": ["birthday"], "personalisation": "none"},
            {"product_id": "ZIM-F1-02", "family": "F1_floral",
             "photo_files": ["IMG_B.jpg"], "one_line": "silk carnation basket",
             "form": "basket", "palette": "purple", "edible": "none",
             "perishable": False,
             "medium": ["silk carnations", "wicker basket"],
             "occasion_fit": ["get well"], "personalisation": "none"},
            {"product_id": "ZIM-F4-01", "family": "F4_mixed_hamper",
             "photo_files": ["IMG_C.jpg"], "one_line": "black-gold hamper",
             "form": "hat-box", "palette": "black/gold", "edible": "chocolate",
             "perishable": True,
             "medium": ["Ferrero Rocher chocolates", "sparkling wine (alcohol)"],
             "occasion_fit": ["celebration"], "personalisation": "none"},
            {"product_id": "ZIM-F4-02", "family": "F4_mixed_hamper",
             "photo_files": ["IMG_D.jpg"], "one_line": "blue kids hamper",
             "form": "fabric box", "palette": "blue", "edible": "mixed",
             "perishable": True,
             # «jute twine bows» عمداً — نباید با \bwine\b به‌غلط الکل flag شود
             "medium": ["plush teddy bear", "jute twine bows"],
             "occasion_fit": ["new baby boy"], "personalisation": "none"},
            {"product_id": "ZIM-F3-01", "family": "F3_candy_basket",
             "photo_files": ["IMG_E.jpg"], "one_line": "marshmallow bouquet",
             "form": "glitter box", "palette": "pink", "edible": "candy",
             "perishable": False,
             "medium": ["marshmallow sticks"], "occasion_fit": ["birthday"],
             "personalisation": "none"},
            {"product_id": "ZIM-F2-01", "family": "F2_framed",
             "photo_files": ["IMG_F.jpg"], "one_line": "shadow-box frame",
             "form": "shadow-box", "palette": "terracotta", "edible": "none",
             "perishable": False,
             "medium": ["silk ranunculus", "light-wood shadow-box frame"],
             "occasion_fit": ["home decor"], "personalisation": "none"},
            {"product_id": "ZIM-OTHER-01", "family": "OTHER",
             "photo_files": ["IMG_G.jpg"], "one_line": "blank placeholder",
             "form": "blank image", "palette": "white", "edible": "none",
             "perishable": False, "medium": [], "occasion_fit": [],
             "personalisation": "none"},
        ],
        "stats": {"photo_count": 8, "distinct_product_count": 7,
                  "family_counts": [{"family": "F1_floral", "products": 2}]},
        "taxonomy_assessment": "fixture",
        "taxonomy_adjustments": [],
        "data_gaps": [],
    }


def _write_catalog(root: Path, data: dict | str | None = None) -> Path:
    p = root / ZIMAN_CATALOG_NOTE
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        p.write_text(data, encoding="utf-8")
    else:
        p.write_text(json.dumps(data if data is not None else _fixture_catalog(),
                                ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _leg(**kw) -> ZimanLeg:
    return ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30, **kw)


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="ziman-cat-"))


# ─── نبود کاتالوگ → دقیقاً رفتارِ قدیم ─────────────────────────────────────────
def test_missing_catalog_exact_legacy_behavior():
    leg = _leg(catalog_path=_tmp() / "does-not-exist.json")
    assert leg.product_families() == dict(PRODUCT_FAMILIES)
    s = leg.status_snapshot()
    assert s["product_families"] == list(PRODUCT_FAMILIES.keys())
    assert s["catalog"]["loaded"] is False
    assert s["catalog"]["evidence_class"] == "UNKNOWN"
    p = leg.inventory_report({"C1": 10, "XX": 1})
    fams = p.payload["families"]
    assert set(fams) == set(PRODUCT_FAMILIES)
    # در fallback هیچ کلیدِ نو داخلِ خانواده‌ها نیست — عینِ payload قدیم
    assert set(fams["C1"].keys()) == {"name", "count"}
    assert fams["C1"]["count"] == 10
    assert p.payload["unknown_keys_rejected"] == ["XX"]
    assert p.payload["next_step"] == "Owner classifies into C1–C4 then SKU cards"


def test_corrupt_or_misshapen_catalog_fail_soft():
    root = _tmp()
    bad = _write_catalog(root, "{{{ this is not json")
    leg = _leg(catalog_path=bad)
    assert leg.product_families() == dict(PRODUCT_FAMILIES)   # بدون کرش
    misshapen = _write_catalog(_tmp(), {"products": {}})       # شکلِ غلط
    leg2 = _leg(catalog_path=misshapen)
    assert leg2.product_families() == dict(PRODUCT_FAMILIES)
    assert leg2.status_snapshot()["catalog"]["loaded"] is False
    # حتی draft هم با کاتالوگِ خراب مسیرِ قدیم را می‌رود
    d = leg.draft_content(product_family="C4")
    assert d.payload["product_family"] == "C4"
    assert d.payload["family_source"] == "legacy_fallback"


# ─── کاتالوگِ واقعی → خانواده‌ها/شمارش/پرچم‌های زمینی ─────────────────────────
def test_catalog_families_counts_and_flags():
    leg = _leg(catalog_path=_write_catalog(_tmp()))
    fams = leg.product_families()
    assert list(fams) == ["F1_floral", "F4_mixed_hamper", "F2_framed",
                          "F3_candy_basket", "OTHER"]        # مرتب به count، بعد نام
    s = leg.status_snapshot()
    assert s["product_families"] == list(fams)
    cat = s["catalog"]
    assert cat["loaded"] is True
    assert cat["source"] == ZIMAN_CATALOG_NOTE
    assert cat["product_count"] == 7
    assert cat["family_counts"] == {"F1_floral": 2, "F4_mixed_hamper": 2,
                                    "F2_framed": 1, "F3_candy_basket": 1,
                                    "OTHER": 1}
    assert cat["perishable_products"] == 2         # فیلدِ صریحِ perishable
    assert cat["alcohol_suspect_products"] == 1    # فقط «sparkling wine (alcohol)» — نه twine
    assert cat["evidence_class"] == "GROUNDED"


def test_inventory_report_grounded_per_family():
    leg = _leg(catalog_path=_write_catalog(_tmp()))
    p = leg.inventory_report({"C1": 10, "XX": 1})
    fams = p.payload["families"]
    # aliasِ قدیمی: C1 → F1_floral (رد نمی‌شود)؛ XX همچنان رد
    assert "C1" not in p.payload["unknown_keys_rejected"]
    assert "XX" in p.payload["unknown_keys_rejected"]
    assert fams["F1_floral"]["count"] == 10                   # عددِ مالک (کلیدِ قدیمی)
    assert fams["F1_floral"]["catalog_count"] == 2            # شمارشِ زمینی (additive)
    assert fams["F4_mixed_hamper"]["catalog_count"] == 2
    assert fams["F4_mixed_hamper"]["perishable_count"] == 2
    assert fams["F4_mixed_hamper"]["alcohol_suspect_count"] == 1
    assert fams["F4_mixed_hamper"]["edible"] == {"chocolate": 1, "mixed": 1}
    assert fams["F2_framed"]["perishable_count"] == 0
    # کلیدهای قدیمیِ قرارداد دست‌نخورده (ADD, don't rename)
    assert p.payload["canonical_write"] is False
    assert p.payload["draft_only"] is True
    assert p.payload["capacity_public_claim_allowed"] is False
    assert "F1_floral" in p.payload["next_step"]
    assert p.payload["catalog"]["loaded"] is True


def test_org_root_resolution_and_removal():
    """resolution پیش‌فرض از opslib.ORG_ROOT در لحظهٔ فراخوان — نه مسیرِ hardcode.
    ORG_ROOT صریحاً pin می‌شود (در سشنِ مشترکِ pytest، opslib ممکن است قبل از
    harness.setup این ماژول import شده باشد و ریشهٔ دیگری cache کرده باشد)."""
    import opslib
    root = Path(ENV["root"])
    old_root = opslib.ORG_ROOT
    opslib.ORG_ROOT = root
    written = _write_catalog(root)
    try:
        leg = _leg()                              # بدون تزریق — باید از ORG_ROOT پیدا کند
        assert leg.status_snapshot()["catalog"]["loaded"] is True
        assert set(leg.product_families()) == {"F1_floral", "F4_mixed_hamper",
                                               "F2_framed", "F3_candy_basket",
                                               "OTHER"}
        written.unlink()
        leg2 = _leg()                             # حذف شد → رفتارِ قدیم، بدون کرش
        assert leg2.product_families() == dict(PRODUCT_FAMILIES)
    finally:
        opslib.ORG_ROOT = old_root
        if written.exists():
            written.unlink()


def test_draft_content_alias_and_derived_warnings():
    leg = _leg(catalog_path=_write_catalog(_tmp()))
    # C4 (کدِ قدیمی) → F4_mixed_hamper؛ هشدارِ فاسدشدنی از فیلدِ perishable مشتق می‌شود
    d = leg.draft_content(product_family="C4", occasion="تولد")
    assert d.payload["product_family"] == "F4_mixed_hamper"
    assert d.payload["requested_family"] == "C4"
    assert d.payload["family_source"] == "catalog"
    assert "فاسدشدنی" in d.payload["body"] and "محلی" in d.payload["body"]
    assert "الکل" in d.payload["body"]            # alcohol_suspect در F4
    assert d.payload["publish"] is False and d.payload["draft_only"] is True
    # خانوادهٔ غیرفاسدشدنی → بدون هشدار
    d2 = leg.draft_content(product_family="F1_floral")
    assert "فاسدشدنی" not in d2.payload["body"]
    assert "الکل" not in d2.payload["body"]
    # ناشناخته → پیش‌فرضِ قدیم (aliasِ C3 = F2_framed)
    d3 = leg.draft_content(product_family="ZZ")
    assert d3.payload["product_family"] == LEGACY_FAMILY_ALIAS["C3"]


def test_utf8_bom_catalog_loads():
    """فایلِ زمینیِ واقعی BOM دارد (خروجی PowerShell) — پل باید آن را بخواند، نه fallback."""
    root = _tmp()
    p = root / ZIMAN_CATALOG_NOTE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(_fixture_catalog(), ensure_ascii=False),
                 encoding="utf-8-sig")                        # با BOM، عینِ فایلِ واقعی
    leg = _leg(catalog_path=p)
    assert leg.status_snapshot()["catalog"]["loaded"] is True
    assert leg.status_snapshot()["catalog"]["product_count"] == 7


def test_allowlist_gate_blocks_catalog_read():
    """اگر کاتالوگ در read_allowlistِ packet نباشد → حتی با فایلِ موجود لود نمی‌شود (D2)."""
    pkt = TaskPacket(leg_id="ziman-gallery", organ="ZIMAN",
                     read_allowlist=("03 - Projects/Ziman Galerry/PROJECT.md",),
                     tools=("status_snapshot",), budget_aud=1.0)
    leg = ZimanLeg(packet=pkt, organ_table={"ZIMAN": {}}, capacity_ceiling=30,
                   catalog_path=_write_catalog(_tmp()))
    assert leg.product_families() == dict(PRODUCT_FAMILIES)
    assert leg.status_snapshot()["catalog"]["loaded"] is False


def test_bridge_stays_propose_only():
    leg = _leg(catalog_path=_write_catalog(_tmp()))
    assert leg.tick()["ok"] is True
    for forbidden in ("send", "publish", "pay"):
        assert not hasattr(leg, forbidden)
    s = leg.status_snapshot()
    assert s["autonomy"] == "propose-only"
    assert s["execution_state"] == "ZERO outward execution — drafts only"


if __name__ == "__main__":
    print("── test_ziman_catalog_bridge ──")
    _failed = harness.run([
        ("missing_catalog_exact_legacy_behavior", test_missing_catalog_exact_legacy_behavior),
        ("corrupt_or_misshapen_catalog_fail_soft", test_corrupt_or_misshapen_catalog_fail_soft),
        ("catalog_families_counts_and_flags", test_catalog_families_counts_and_flags),
        ("inventory_report_grounded_per_family", test_inventory_report_grounded_per_family),
        ("org_root_resolution_and_removal", test_org_root_resolution_and_removal),
        ("utf8_bom_catalog_loads", test_utf8_bom_catalog_loads),
        ("draft_content_alias_and_derived_warnings", test_draft_content_alias_and_derived_warnings),
        ("allowlist_gate_blocks_catalog_read", test_allowlist_gate_blocks_catalog_read),
        ("bridge_stays_propose_only", test_bridge_stays_propose_only),
    ])
    sys.exit(1 if _failed else 0)
