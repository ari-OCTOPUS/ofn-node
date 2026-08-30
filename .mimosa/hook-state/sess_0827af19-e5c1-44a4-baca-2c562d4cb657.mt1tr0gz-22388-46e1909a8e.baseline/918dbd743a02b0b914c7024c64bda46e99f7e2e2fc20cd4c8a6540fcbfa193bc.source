"""تست‌های steering.py + self_model.py (گامِ ۱ / P0) — خالص، fail-soft، بدونِ عددِ جعلی."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ziman")))

import steering  # noqa: E402
import self_model  # noqa: E402

_SAMPLE = """# GOALS-ZIMAN
> این بلاک‌کوت نباید بولت حساب شود
- این خط هم قبل از سرفصل است و نادیده می‌رود

## DIRECTIVES — تمرکز
- بازارِ گرم اول
- اولین فروشِ واقعی

## PRIORITIES
- شادوباکس (F2)
- همپر (F4)

## GUARDRAILS
- بدونِ تأییدِ من هیچ انتشار
<!-- کامنت -->
"""


# ── steering ────────────────────────────────────────────────────────────────

def test_parse_goals_sections_and_bullets():
    g = steering.parse_goals(_SAMPLE)
    assert g["directives"] == ["بازارِ گرم اول", "اولین فروشِ واقعی"]
    assert g["priorities"] == ["شادوباکس (F2)", "همپر (F4)"]
    assert g["guardrails"] == ["بدونِ تأییدِ من هیچ انتشار"]


def test_parse_ignores_blockquote_and_pre_header_and_comments():
    g = steering.parse_goals(_SAMPLE)
    joined = " ".join(g["directives"] + g["priorities"] + g["guardrails"])
    assert "بلاک‌کوت" not in joined
    assert "قبل از سرفصل" not in joined
    assert "کامنت" not in joined


def test_load_steering_failsoft_when_no_file(tmp_path):
    s = steering.load_steering(goals_path=tmp_path / "nope.md", base_dir=tmp_path)
    assert s["directives"] == [] and s["paused"] is False
    assert s["goals_found"] is False


def test_steering_state_only_known_keys(tmp_path):
    import json
    sdir = tmp_path / "state" / "ziman"
    sdir.mkdir(parents=True)
    (sdir / "steering.json").write_text(
        json.dumps({"focus": "F2", "paused": True, "evil": "x"}), encoding="utf-8")
    st = steering.load_steering_state(base_dir=tmp_path)
    assert st["focus"] == "F2" and st["paused"] is True
    assert "evil" not in st


def test_finds_real_goals_file():
    # اگر در repo باشد باید پیدا و پارس شود (وگرنه در چک‌اوتِ دیگر رد)
    p = steering.find_goals()
    if p is None:
        return
    g = steering.parse_goals(p.read_text(encoding="utf-8"))
    assert g["directives"], "GOALS-ZIMAN.md باید DIRECTIVES داشته باشد"


# ── self_model (خالص) ────────────────────────────────────────────────────────

_CFG = {"business": {"name": "Ziman Gift", "location": "Sydney"},
        "capacity": {"units_per_week_ceiling": 30, "current_inventory": 20}}
_CAT = {"total": 35, "by_family": {"F1": 18, "F2": 2, "F3": 4, "F4": 11},
        "priced": 0, "perishable": 10, "local_only": 11, "alcohol_facet": 7}
_STEER = {"directives": ["بازارِ گرم اول"], "priorities": ["F2"], "guardrails": [],
          "focus": None, "paused": False}


def test_build_self_model_shape():
    m = self_model.build_self_model(catalog=_CAT, cfg=_CFG, steering=_STEER)
    assert m["schema"] == "ziman_self.v1"
    for k in ("identity", "objective", "standing", "gap_vector", "truth_tiers"):
        assert k in m
    assert m["propose_only"] is True and m["outward_execution"] is False


def test_authorities_all_false_and_no_fabricated_price():
    m = self_model.build_self_model(catalog=_CAT, cfg=_CFG, steering=_STEER)
    assert m["identity"]["authorities"] == {"price": False, "delivery_promise": False, "publish": False}
    assert m["standing"]["catalog"]["priced"] == 0            # هیچ قیمتِ جعلی


def test_capacity_is_conflict_and_failclosed():
    m = self_model.build_self_model(catalog=_CAT, cfg=_CFG, steering=_STEER)
    cap = m["standing"]["capacity"]
    assert cap["raw_yaml"] == 30 and cap["evidence"] == "CONFLICT"
    assert cap["effective_ceiling"] == 6                      # fail-closed تا revalidation


def test_real_sales_default_zero_and_progress():
    m = self_model.build_self_model(catalog=_CAT, cfg=_CFG, steering=_STEER)
    assert m["objective"]["real_sales"] == 0
    assert m["objective"]["validation_progress_pct"] == 0.0
    m2 = self_model.build_self_model(catalog=_CAT, cfg=_CFG, steering=_STEER, real_sales=5)
    assert m2["objective"]["validation_progress_pct"] == 50.0


def test_gap_vector_drives_first_sales():
    m = self_model.build_self_model(catalog=_CAT, cfg=_CFG, steering=_STEER)
    goals = {g["goal"]: g for g in m["gap_vector"]}
    assert goals["first_real_sales"]["gap"] == 10             # 10 - 0
    assert goals["priced_products"]["truth_tier"] == "CONFLICT"


def test_directives_flow_from_steering():
    m = self_model.build_self_model(catalog=_CAT, cfg=_CFG, steering=_STEER)
    assert m["objective"]["directives"] == ["بازارِ گرم اول"]


def test_build_failsoft_on_empty_inputs():
    m = self_model.build_self_model(catalog={}, cfg={}, steering={})
    assert m["schema"] == "ziman_self.v1"
    assert m["standing"]["catalog"]["total"] == 0


# ── self_model (زنده روی منابعِ واقعی) ────────────────────────────────────────

def test_load_self_model_real_sources():
    m = self_model.load_self_model()
    # کاتالوگِ واقعی باید بیاید (اگر repo کامل باشد)
    assert m["schema"] == "ziman_self.v1"
    assert m["propose_only"] is True
    if m["standing"]["catalog"]["total"]:
        assert m["standing"]["catalog"]["total"] >= 35
        assert m["standing"]["catalog"]["priced"] == 0
