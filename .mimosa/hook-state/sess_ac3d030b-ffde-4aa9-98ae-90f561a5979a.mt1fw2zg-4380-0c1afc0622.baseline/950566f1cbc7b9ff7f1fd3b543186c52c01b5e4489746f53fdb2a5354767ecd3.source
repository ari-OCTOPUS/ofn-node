"""test_route_scorer.py — امتیازدهِ ردهٔ مسیریابی (پیشنهاد، نه اجرا).

آموزه: کم‌عمق → local؛ عمیق/معماری/چندفایل → primary؛ متوسط → secondary؛
حساس → ترجیحِ محلی (redact-first). decision_record کلیدهای لازم را دارد.
مرزِ سخت: بدونِ پرچمِ CORTEX_ROUTE_SCORER هیچ نوشتنی روی دیسک نیست (سایه‌ی محض).
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("route-scorer")

import route_scorer   # noqa: E402
import opslib         # noqa: E402

_REQUIRED_SCORES = {"complexity", "risk", "privacy", "impact", "cost", "urgency"}
_REQUIRED_RECORD = {"task_id", "scores", "tier", "why", "est_cost", "fallback"}


def _clear_flag():
    os.environ.pop(route_scorer.FLAG, None)


def t_a_shallow_routes_local():
    """کم‌عمق/روتین → محلی."""
    for task in ("classify", "summarize", "triage a short note"):
        r = route_scorer.score_route(task, None)
        assert r["tier"] == "local", (task, r["tier"], r["scores"])


def t_b_deep_routes_primary():
    """عمیق/معماری/چندفایل → primary."""
    r = route_scorer.score_route(
        "orchestrate a deep architecture refactor",
        {"n_files": 12, "reversible": False})
    assert r["tier"] == "primary", (r["tier"], r["scores"])
    assert r["scores"]["complexity"] >= 0.8


def t_c_sensitive_prefers_local_with_redact_note():
    """حساس → ترجیحِ محلی + یادداشتِ redact-first در reasons."""
    r = route_scorer.score_route("summarize", {"sensitive": True})
    assert r["tier"] == "local", r["tier"]
    assert any("redact" in reason.lower() for reason in r["reasons"]), r["reasons"]
    # حتی کارِ عمیقِ حساس هم محلی می‌ماند (override قوی)
    r2 = route_scorer.score_route(
        "orchestrate a deep migration", {"sensitive": True, "n_files": 20})
    assert r2["tier"] == "local", r2["tier"]


def t_d_medium_routes_secondary():
    """عمقِ متوسط → secondary."""
    r = route_scorer.score_route(
        "research and synthesize a comparison", {"impact": "medium", "n_files": 3})
    assert r["tier"] == "secondary", (r["tier"], r["scores"])


def t_e_record_has_required_keys():
    """خروجی و decision_record هر دو شکلِ قراردادی را دارند."""
    r = route_scorer.score_route("plan a redesign", {"n_files": 6})
    assert set(r) >= {"tier", "scores", "reasons", "decision_record"}
    assert set(r["scores"]) == _REQUIRED_SCORES
    assert isinstance(r["reasons"], list) and r["reasons"]
    rec = r["decision_record"]
    assert _REQUIRED_RECORD <= set(rec), set(rec)
    assert rec["tier"] == r["tier"]
    assert rec["scores"] == r["scores"]
    assert isinstance(rec["est_cost"], (int, float))
    assert rec["fallback"] in ("local", "owner")
    for v in r["scores"].values():
        assert 0.0 <= v <= 1.0


def t_f_no_disk_write_without_flag():
    """پرچم خاموش = صفر نوشتن روی دیسک (سایه‌ی محض)."""
    _clear_flag()
    log = route_scorer.DECISIONS_LOG
    if log.exists():
        log.unlink()
    for _ in range(3):
        route_scorer.score_route("orchestrate a deep plan", {"n_files": 9})
    assert not log.exists(), "بدونِ پرچم نباید فایلِ تصمیم ساخته شود"


def t_g_flag_on_persists_record():
    """پرچم روشن = append روی STATE_DIR (فقط این‌جا). سپس دوباره خاموش."""
    log = route_scorer.DECISIONS_LOG
    if log.exists():
        log.unlink()
    os.environ[route_scorer.FLAG] = "1"
    try:
        route_scorer.score_route("classify", None)
        route_scorer.score_route("orchestrate deep architecture", {"n_files": 10})
    finally:
        _clear_flag()
    assert log.exists(), "با پرچمِ روشن باید نوشته شود"
    lines = [ln for ln in log.read_text("utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2, len(lines)
    # نوشتن فقط زیرِ STATE_DIR
    assert str(opslib.STATE_DIR) in str(log.resolve())
    # پرچمِ خاموش دوباره = دیگر رشد نمی‌کند
    route_scorer.score_route("summarize", None)
    lines2 = [ln for ln in log.read_text("utf-8").splitlines() if ln.strip()]
    assert len(lines2) == 2, len(lines2)


def t_h_fail_soft_never_crashes():
    """ورودیِ بدقواره → پیش‌فرضِ امنِ محلی، نه کرش."""
    for bad in (None, 123, {"weird": object()}):
        r = route_scorer.score_route(bad if isinstance(bad, (str, type(None))) else str(bad),
                                     bad if isinstance(bad, dict) else None)
        assert r["tier"] in ("local", "secondary", "primary")
        assert set(r["scores"]) == _REQUIRED_SCORES
    # ctx غیرِdict → نادیده، بی‌کرش
    r = route_scorer.score_route("classify", ["not", "a", "dict"])
    assert r["tier"] == "local"


def t_i_string_false_is_not_coerced_to_true():
    """باگِ ۲۰۲۶-۰۸-۰۷: `_flag_hint` قبلاً `bool(ctx[k])` خام می‌زد — `bool("false")`
    در پایتون True است، پس `{"reversible": "false"}` را به‌جای False به True
    می‌خواند و risk را به‌غلط پایین می‌آورد (دقیقاً برعکسِ intent)."""
    r_str = route_scorer.score_route("architect a change", {"reversible": "false"})
    r_bool = route_scorer.score_route("architect a change", {"reversible": False})
    assert r_str["scores"]["risk"] == r_bool["scores"]["risk"], (
        r_str["scores"]["risk"], r_bool["scores"]["risk"])
    # رشته‌های صادقانه هنوز درست کار کنند
    r_true_str = route_scorer.score_route("architect a change", {"reversible": "true"})
    r_true_bool = route_scorer.score_route("architect a change", {"reversible": True})
    assert r_true_str["scores"]["risk"] == r_true_bool["scores"]["risk"]


def t_j_coercion_fix_is_generic_across_all_keys():
    """پوششِ بقایای فیکسِ ۹۸b807۵: coercion-bug فقط رویِ reversible تست شده بود،
    ولی فیکس عمومی است (سطر ۱۰۳–۱۰۵، بدونِ استثنا). این تست همان تله را برایِ
    هر کلیدِ دیگری که `_flag_hint` می‌خواند سنجیده و قفل می‌کند که رشتهٔ "false"
    دیگر به‌عنوان True خوانده نمی‌شود. مرز: کلیدهای حساس (sensitive/private) مهم‌تر‌اند
    چون coerce‌شدنشان privacy-override را ساکت می‌کند (تلهٔ امنیتی، نه فقط عددی)."""
    # sensitive: "false" باید privacy را پایین بیاورد (نه override به local)
    s_str = route_scorer.score_route("summarize", {"sensitive": "false"})
    s_off = route_scorer.score_route("summarize", {})
    assert s_str["scores"]["privacy"] == s_off["scores"]["privacy"], (
        "sensitive='false' نباید privacy را بالا ببرد", s_str["scores"]["privacy"],
        s_off["scores"]["privacy"])
    assert s_str["tier"] != "local" or s_str["scores"]["privacy"] < 0.60, (
        "نباید privacy-override شلیک کند وقتی صریحاً false داده شده", s_str)
    # private: همان تله
    p_str = route_scorer.score_route("summarize", {"private": "false"})
    assert p_str["scores"]["privacy"] == s_off["scores"]["privacy"], (
        "private='false' نباید privacy را بالا ببرد", p_str["scores"]["privacy"])
    # high_correctness/critical: "false" نباید risk را بالا ببرد
    c_str = route_scorer.score_route("classify", {"critical": "false"})
    c_off = route_scorer.score_route("classify", {})
    assert c_str["scores"]["risk"] == c_off["scores"]["risk"], (
        "critical='false' نباید risk را بالا ببرد", c_str["scores"]["risk"],
        c_off["scores"]["risk"])
    # architecture: "false" نباید complexity را بالا ببرد
    a_str = route_scorer.score_route("classify", {"architecture": "false"})
    a_off = route_scorer.score_route("classify", {})
    assert a_str["scores"]["complexity"] == a_off["scores"]["complexity"], (
        "architecture='false' نباید complexity را بالا ببرد",
        a_str["scores"]["complexity"], a_off["scores"]["complexity"])
    # low_impact: "false" نباید impact را پایین بیاورد (یعنی نباید min 0.15 کند)
    l_str = route_scorer.score_route("classify", {"low_impact": "false"})
    l_off = route_scorer.score_route("classify", {})
    assert l_str["scores"]["impact"] == l_off["scores"]["impact"], (
        "low_impact='false' نباید impact را تغییر دهد",
        l_str["scores"]["impact"], l_off["scores"]["impact"])


def t_k_persistence_gate_parses_falsy_strings_as_off(monkeypatch=None):
    """باگِ ۲۰۲۶-۰۸-۰۷ (دوم): گیتِ persistence `if not os.environ.get(FLAG)` هر
    رشتهٔ ناخالی را truthy می‌خواند — پس `CORTEX_ROUTE_SCORER=0`/`=false`/`=no`
    همگی به‌عنوان «روشن» persistence را روشن نگه می‌داشتند. فیکس: همان parsingِ
    `_flag_hint`. این تست ثابت می‌کند مقادیرِ falsy-explicit persistence را خاموش
    نگه می‌دارند (صفر نوشتن روی دیسک) و فقط مقادیرِ truthy روشن می‌کنند."""
    import os as _os
    log_path = route_scorer.DECISIONS_LOG
    # نصبِ دکوریشنِ monkeypatch اگر pytest اجرا کند؛ در غیرِ اینصورت env دستی
    _saved = _os.environ.pop(route_scorer.FLAG, None)
    try:
        for falsy in ("0", "false", "FALSE", "no", "off", "none", ""):
            _os.environ[route_scorer.FLAG] = falsy
            before = log_path.exists() and sum(1 for _ in open(log_path, encoding="utf-8")) or 0
            route_scorer.score_route("orchestrate a deep architecture refactor",
                                     {"n_files": 3, "reversible": False})
            after = log_path.exists() and sum(1 for _ in open(log_path, encoding="utf-8")) or 0
            assert after == before, (
                f"FLAG='{falsy}' باید persistence را خاموش کند ولی {after-before} "
                f"ردیف نوشته شد (قبل={before}, بعد={after})")
        # فقط مقادیرِ truthy باید بنویسند
        for truthy in ("1", "true", "yes", "on"):
            _os.environ[route_scorer.FLAG] = truthy
            before = log_path.exists() and sum(1 for _ in open(log_path, encoding="utf-8")) or 0
            route_scorer.score_route("orchestrate a deep architecture refactor",
                                     {"n_files": 3, "reversible": False})
            after = log_path.exists() and sum(1 for _ in open(log_path, encoding="utf-8")) or 0
            assert after == before + 1, (
                f"FLAG='{truthy}' باید یک ردیف بنویسد ولی {after-before} نوشته شد "
                f"(قبل={before}, بعد={after})")
    finally:
        _os.environ.pop(route_scorer.FLAG, None)
        if _saved is not None:
            _os.environ[route_scorer.FLAG] = _saved


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_route_scorer: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)