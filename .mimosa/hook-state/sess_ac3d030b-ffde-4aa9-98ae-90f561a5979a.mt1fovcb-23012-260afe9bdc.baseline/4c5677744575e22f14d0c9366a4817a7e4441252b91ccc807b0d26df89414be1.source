#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_leg_activation — قالبِ «پای فعال‌شونده» (W4 لِین H، منشور §۵).

    manifest ِ قراردادی (۱۲ فیلد، آینهٔ validate_contract) · گذارهای
    DORMANT/READY/ACTIVE · نگهبانِ صفر-template · activate ِ propose-only
"""
import json
import re
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-leg-activation")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)
_CONTRACT = str(_OPS / "telegram_contract")
if _CONTRACT not in sys.path:
    sys.path.insert(0, _CONTRACT)

import leg_activation as la  # noqa: E402
import leg_tasks as lt  # noqa: E402
import validate_contract as vc  # noqa: E402

import os  # noqa: E402

NOW = 1_785_400_000.0
_MANIFEST_DIR = Path(ENV["root"]) / "manifests"
os.environ["OCTOPUS_LEG_MANIFEST_DIR"] = str(_MANIFEST_DIR)


def _write_manifest(leg="mining", mutate=None) -> Path:
    d = la.manifest_skeleton(leg, "ماینینگ")
    if mutate:
        mutate(d)
    p = la.manifest_path(leg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
    return p


def _clear(leg="mining"):
    try:
        la.manifest_path(leg).unlink()
    except OSError:
        pass
    try:
        lt._path(leg).unlink()
    except OSError:
        pass


# ── قراردادِ manifest ───────────────────────────────────────────────────────
def t_skeleton_passes_the_real_validate_contract():
    """اسکلت باید از خودِ validate_contract.validate_manifest پاس شود —
    نه فقط از آینهٔ محلی. (خواننده و نویسنده با هم — درسِ ۰۷-۳۱.)"""
    p = _write_manifest("mining")
    errors = []
    vc.validate_manifest(p, errors)
    assert errors == [], errors
    assert la.manifest_errors(json.loads(p.read_text("utf-8"))) == []


def t_required_field_list_matches_validate_contract_source():
    """گاردِ drift: لیستِ ۱۲ فیلدِ این ماژول باید بایت-به-بایت با literal ِ
    `required = {…}` در سورسِ validate_contract.py یکی باشد."""
    src = (_OPS / "telegram_contract" / "validate_contract.py").read_text("utf-8")
    m = re.search(r"required = \{(.*?)\}", src, re.S)
    assert m, "required literal در validate_contract پیدا نشد"
    fields = set(re.findall(r'"([a-z_]+)"', m.group(1)))
    assert fields == set(la.MANIFEST_REQUIRED), (
        f"drift: contract={sorted(fields)} module={sorted(la.MANIFEST_REQUIRED)}")
    assert len(la.MANIFEST_REQUIRED) == 12


def t_a_manifest_missing_version_fails_both_validators():
    """جهشِ قرمزکننده: حذفِ version باید هم validator ِ واقعی و هم آینه را
    قرمز کند — وگرنه آینه کور است."""
    p = _write_manifest("mining", mutate=lambda d: d.pop("version"))
    errors = []
    try:
        vc.validate_manifest(p, errors)
    except ValueError:
        errors.append("path-outside-root (still red)")
    assert errors, "validator ِ واقعی manifest ِ بی‌version را پذیرفت"
    assert la.manifest_errors(json.loads(p.read_text("utf-8"))), \
        "آینهٔ محلی manifest ِ بی‌version را پذیرفت"


def t_registration_is_never_authorization():
    d = la.manifest_skeleton("crypto", "کریپتو")
    assert d["registration_is_authorization"] is False
    d2 = dict(d)
    d2["registration_is_authorization"] = True
    assert la.manifest_errors(d2), "manifest ِ خود-مجوزده رد نشد"


def t_group_manifest_always_carries_leg_key():
    d = la.manifest_skeleton("studio_pf", "استودیو")
    assert d["surface"] == "legs_forum_group" and d["leg_key"] == "studio_pf"
    d.pop("leg_key")
    assert la.manifest_errors(d), "manifest ِ گروهی بدونِ leg_key رد نشد"


# ── گذارهای وضعیت ──────────────────────────────────────────────────────────
def t_no_manifest_or_no_topic_means_dormant():
    _clear("mining")
    cfg = {"topics": {"mining": 42}}
    assert la.activation_status("mining", cfg, now=NOW) == la.DORMANT
    _write_manifest("mining")
    assert la.activation_status("mining", {"topics": {}}, now=NOW) == la.DORMANT


def t_manifest_plus_topic_without_activity_is_ready():
    _clear("mining")
    _write_manifest("mining")
    cfg = {"topics": {"mining": 42}}
    assert la.activation_status("mining", cfg, now=NOW) == la.READY


def t_recent_leg_activity_makes_it_active_and_stale_activity_does_not():
    _clear("mining")
    _write_manifest("mining")
    cfg = {"topics": {"mining": 42}}
    lt.add("mining", "بررسیِ نرخِ هش", now=NOW - 86400)          # دیروز
    assert la.activation_status("mining", cfg, now=NOW) == la.ACTIVE
    _clear("mining")
    _write_manifest("mining")
    lt.add("mining", "کارِ کهنه", now=NOW - 15 * 86400)          # ۱۵ روز پیش
    assert la.activation_status("mining", cfg, now=NOW) == la.READY


def t_a_broken_manifest_on_disk_is_not_ready():
    _clear("mining")
    _write_manifest("mining", mutate=lambda d: d.pop("owner_phrases"))
    cfg = {"topics": {"mining": 42}}
    assert la.activation_status("mining", cfg, now=NOW) == la.DORMANT


# ── نگهبانِ صفر-template ───────────────────────────────────────────────────
def t_the_guard_rejects_boilerplate_and_empty_text():
    for filler in ("", "   ",
                   "گزارش خودکار: هیچ فعالیتی ثبت نشده",
                   "هیچ فعالیتی ثبت نشده است.",
                   "این یک پیام آزمایشی است",
                   "status of {{leg_name}}",
                   "TODO: fill this in",
                   "Lorem ipsum dolor sit amet"):
        assert la.zero_template_guard(filler), filler


def t_the_guard_passes_real_event_text():
    for real in ("مشتری از بروکر تماس گرفت — سفارشِ ۳ تابلو، تحویل جمعه",
                 "قیمتِ بیت‌کوین از آستانهٔ هشدارِ مالک گذشت: ۱۲۳٬۴۵۰",
                 "ریگ ۲ از ساعتِ ۰۳:۱۰ خاموش است؛ برق قطع شده بود"):
        assert not la.zero_template_guard(real), real


def t_the_blocklist_is_parametrizable():
    assert la.zero_template_guard("گزارشِ نوبتیِ پا", blocklist=("گزارشِ نوبتی",))
    assert not la.zero_template_guard("گزارش خودکار", blocklist=("چیزِ دیگر",))


# ── activate: propose-only ─────────────────────────────────────────────────
def t_activate_returns_a_plan_and_never_calls_create_topic():
    _clear("crypto")
    calls = []
    plan = la.activate("crypto", cfg={"topics": {}},
                       create_topic_fn=lambda *a, **k: calls.append(a),
                       title="کریپتو", now=NOW)
    assert calls == [], "activate در این موج تاپیک ساخت — ممنوع"
    assert plan["propose_only"] is True
    steps = {s["step"]: s for s in plan["steps"]}
    assert set(steps) == {"manifest", "topic", "first_real_event"}
    assert steps["manifest"]["needed"] and steps["topic"]["needed"]
    assert steps["first_real_event"]["needed"] is True
    assert la.manifest_errors(plan["manifest_skeleton"]) == []


def t_activate_marks_existing_pieces_as_not_needed():
    _clear("mining")
    _write_manifest("mining")
    plan = la.activate("mining", cfg={"topics": {"mining": 42}},
                       create_topic_fn=None, now=NOW)
    steps = {s["step"]: s for s in plan["steps"]}
    assert not steps["manifest"]["needed"] and not steps["topic"]["needed"]
    assert plan["current_status"] == la.READY


# ── مرزها ──────────────────────────────────────────────────────────────────
def t_the_module_has_no_external_effectors():
    import ast
    tree = ast.parse(Path(la.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for bad in ("send", "send_text", "post", "sendMessage", "urlopen",
                "create_topic"):
        assert bad not in called, f"leg_activation اثرِ بیرونی دارد: {bad}"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(la.manifest_path("mining")).lower().startswith(live)
    assert not str(lt._path("mining")).lower().startswith(live)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_leg_activation: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
