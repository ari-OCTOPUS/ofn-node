#!/usr/bin/env python3
"""test_langar_route_parity — دو درزِ اندازه‌گیری‌شدهٔ ۲۰۲۶-۰۸-۰۱، هر دو دوطرفه.

WS-4/B — «۹ handlerِ واقعی در langar هیچ ردیفی در LANGAR_CMDS ندارند»
────────────────────────────────────────────────────────────────────
`langar_bot.LangarBot.handle` ۴۱ فرمانِ واقعی دارد؛ جدولِ `langar_bridge`
سی ردیف داشت. با prefix-matching، **۹ فرمانِ زنده** به هیچ ردیفی نمی‌خوردند:

    /agreement /agreement_for_creator /agreement_signed
    /code /code_queue /code_status /inbox /reset /studio

مالک تایپ می‌کرد و **سکوت** می‌گرفت، در حالی که handler همان لحظه زنده بود.

این فایل نُه رشته را چک نمی‌کند — **قاعده** را چک می‌کند، در هر دو جهت:
  · handlerِ بی‌ردیف  → سکوتِ خاموش (بیماریِ امروز).
  · ردیفِ بی‌handler  → `dispatch` فرمان را از مسیرهای دیگرِ رباتِ واحد
    می‌دزدد و langar «دستور ناشناخته» می‌گوید. جوابِ غلطِ مطمئن، بدتر از سکوت.
  · اعلامِ کهنه در `LANGAR_ROUTE_EXCLUDED` هم قرمز می‌شود — اعلامی که دیگر
    handler ندارد به‌اندازهٔ شکافِ ندیده بد است.

WS-4/A — «`/lead` یک نام است و دو معنی»
───────────────────────────────────────
باتِ بیرونی `/lead a | 120 | interior | …` → متراژ. باتِ درونی
`/lead a | 5000 | lead.doer` → AUD. مثالِ خودِ راهنمای باتِ درونی اگر در گروه
تایپ شود، **کوتِ ۵۰۰۰ متری** می‌شود؛ بدونِ خطا. `t_c_*` همان رفتارِ پیش-از-فیکس
را بازسازی می‌کند و نشان می‌دهد قرمز است.

مرزها: صفر شبکه، صفر پروسه، صفر نوشتن در درختِ زنده. فقط پارس و توابعِ خالص.
هیچ‌جا نامِ لید/شخص خوانده یا چاپ نمی‌شود — ورودی‌ها ساختگی‌اند.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("langar-route-parity")           # اول از همه — وگرنه ایزوله نیست

import os  # noqa: E402

_OPS = _HERE.parent
sys.path.insert(0, str(_OPS / "legs"))
sys.path.insert(0, str(_OPS / "telegram_center"))

import langar_bridge as lb  # noqa: E402
import chat_room as cr  # noqa: E402

# ریشهٔ واقعیِ vault فقط برای **خواندنِ سورس** (الگوی test_leg_parity). هیچ نوشتنی.
REAL_VAULT = Path(os.environ.get("REAL_VAULT", r"F:\backup"))


def _langar_bot_path():
    """مسیرِ langar_bot.py بدونِ hardcodeِ نامِ پوشهٔ ونچر (قرارداد: صفر echo هویت).

    اول env، بعد glob روی `03 - Projects/*/langar/`. نبود → None و تست‌های
    وابسته **صریحاً SKIP** گزارش می‌شوند، نه سبز. «نبودِ خطا ≠ سبز».
    """
    envp = (os.environ.get("OCTOPUS_LANGAR_DIR") or "").strip()
    if envp and (Path(envp) / "langar_bot.py").is_file():
        return Path(envp) / "langar_bot.py"
    try:
        hits = sorted((REAL_VAULT / "03 - Projects").glob("*/langar/langar_bot.py"))
    except OSError:
        hits = []
    return hits[0] if hits else None


_SRC_CACHE = {}


def _src() -> str:
    if "s" not in _SRC_CACHE:
        p = _langar_bot_path()
        _SRC_CACHE["s"] = (p.read_text("utf-8", errors="replace")
                           if p is not None else "")
    return _SRC_CACHE["s"]


# ── مجموعهٔ ایستایِ پیش-از-فیکس، برای اثباتِ دندان ──────────────────────────
# این دقیقاً همان تاپلی است که تا ۲۰۲۶-۰۸-۰۱ در `dispatch` بود.
PRE_FIX_ROUTES = (
    "/pf_", "/dm_", "/fan_", "/vault_", "/saba", "/drafts", "/brief", "/think",
    "/spine", "/upgrade", "/gates", "/verdicts", "/rules", "/kpi", "/kpi_record",
    "/report", "/guards", "/report_warning", "/clear_warning", "/clear_full_stop",
    "/report_karma", "/set_karma", "/octopus", "/octopus_status", "/octopus_tick",
    "/kill", "/revive", "/status", "/start", "/help",
)


# ═══ B · استخراج ═══════════════════════════════════════════════════════════
def t_a1_ast_extractor_reads_all_three_condition_shapes():
    """استخراج‌گر باید هر سه شکلِ شرطِ `handle` را بگیرد. اگر یکی را از دست
    بدهد، بقیهٔ تست‌ها روی مجموعهٔ ناقص سبز می‌شوند — یعنی گاردِ کور."""
    fake = (
        "class B:\n"
        "    def handle(self, chat_id, text):\n"
        "        cmd = text\n"
        "        if cmd == '/alpha':\n"
        "            return 1\n"
        "        if cmd in ('/beta', '/gamma'):\n"
        "            return 2\n"
        "        if cmd.startswith('/delta_'):\n"
        "            return 3\n"
        "        if cmd == 'no-slash':\n"
        "            return 4\n"
        "        return None\n")
    got = lb.derive_langar_commands(fake)
    assert got == frozenset({"/alpha", "/beta", "/gamma", "/delta_"}), got


def t_a2_broken_source_is_empty_not_a_crash():
    """پارس‌نشدن → مجموعهٔ خالی (fail-soft). «نمی‌دانم» نباید ادعای «هیچ» شود؛
    `effective_routes` روی خالی به فهرستِ ایستا سقوط می‌کند."""
    assert lb.derive_langar_commands("def broken(:\n") == frozenset()
    assert lb.derive_langar_commands("") == frozenset()
    assert lb.derive_langar_commands("def other(): pass") == frozenset()


def t_a3_real_handler_has_more_commands_than_the_static_table():
    """لنگرِ واقعیت: استخراج روی سورسِ زنده باید عددی معنادار بدهد."""
    src = _src()
    if not src:
        print("      ⏭ SKIP — langar_bot.py پیدا نشد (نه سبز، نه قرمز)")
        return
    hands = lb.derive_langar_commands(src)
    assert len(hands) >= 40, f"استخراج ناقص است: {len(hands)} فرمان"
    assert "/pf_" in hands and "/studio" in hands, sorted(hands)[:5]


# ═══ B · گاردِ دوطرفه ═══════════════════════════════════════════════════════
def t_b1_teeth_pre_fix_table_silently_drops_nine_live_handlers():
    """🦷 دندان — رفتارِ پیش-از-فیکس بازسازی شده و **قرمز** است.

    با جدولِ ایستایِ ۳۰ردیفی، دقیقاً ۹ فرمانِ زنده به `dispatch` نمی‌رسیدند.
    اگر روزی این عدد صفر شود، این تست خودش می‌گوید ادعا کهنه شده."""
    src = _src()
    if not src:
        print("      ⏭ SKIP — langar_bot.py پیدا نشد")
        return
    cov = lb.route_coverage(routes=PRE_FIX_ROUTES, source=src)
    silent = set(cov["handler_without_route"]) | set(lb.LANGAR_ROUTE_EXCLUDED)
    assert len(silent) == 9, f"انتظار ۹ سکوت، دیده شد {len(silent)}: {sorted(silent)}"
    assert silent == {"/agreement", "/agreement_for_creator", "/agreement_signed",
                      "/code", "/code_queue", "/code_status",
                      "/inbox", "/reset", "/studio"}, sorted(silent)


def t_b2_no_live_handler_routes_into_silence():
    """جهتِ یکم — handlerِ زنده باید ردیف داشته باشد، مگر با دلیلِ اعلام‌شده."""
    src = _src()
    if not src:
        print("      ⏭ SKIP — langar_bot.py پیدا نشد")
        return
    os.environ[lb.ROUTE_DERIVE_FLAG] = "1"
    try:
        cov = lb.route_coverage(routes=lb.effective_routes(source=src), source=src)
    finally:
        os.environ.pop(lb.ROUTE_DERIVE_FLAG, None)
    assert not cov["handler_without_route"], (
        "handlerِ زنده که تایپش سکوت می‌دهد: " + str(cov["handler_without_route"]))


def t_b3_no_route_points_at_a_ghost_handler():
    """جهتِ دوم — ردیفی که handler ندارد یعنی `dispatch` فرمان را از مسیرهای
    دیگرِ رباتِ واحد می‌دزدد و langar «دستور ناشناخته» می‌گوید."""
    src = _src()
    if not src:
        print("      ⏭ SKIP — langar_bot.py پیدا نشد")
        return
    os.environ[lb.ROUTE_DERIVE_FLAG] = "1"
    try:
        cov = lb.route_coverage(routes=lb.effective_routes(source=src), source=src)
    finally:
        os.environ.pop(lb.ROUTE_DERIVE_FLAG, None)
    assert not cov["route_without_handler"], (
        "ردیفِ بی‌handler: " + str(cov["route_without_handler"]))


def t_b4_a_ghost_route_is_actually_caught():
    """🦷 دندان برای جهتِ دوم: اگر کسی یک ردیفِ خیالی append کند، قرمز شود.
    بدونِ این، `t_b3` می‌توانست همیشه-سبز باشد و کسی نفهمد."""
    src = _src()
    if not src:
        print("      ⏭ SKIP — langar_bot.py پیدا نشد")
        return
    cov = lb.route_coverage(routes=PRE_FIX_ROUTES + ("/ghost_route_xyz",), source=src)
    assert cov["route_without_handler"] == ["/ghost_route_xyz"], cov["route_without_handler"]


def t_b5_stale_exclusion_declaration_goes_red():
    """اعلامِ کهنه به‌اندازهٔ شکافِ ندیده بد است — و امروز کهنه نیست."""
    src = _src()
    if not src:
        print("      ⏭ SKIP — langar_bot.py پیدا نشد")
        return
    cov = lb.route_coverage(routes=lb.LANGAR_CMDS, source=src)
    assert not cov["excluded_not_a_handler"], (
        "اعلامِ کهنه در LANGAR_ROUTE_EXCLUDED: " + str(cov["excluded_not_a_handler"]))
    assert all(str(v).strip() for v in lb.LANGAR_ROUTE_EXCLUDED.values()), \
        "هر ردیفِ excluded باید دلیل داشته باشد"


# ═══ B · پاریتهٔ فلگ ════════════════════════════════════════════════════════
def t_b6_flag_off_is_byte_identical_to_today():
    """فلگ خاموش → **همان شیءِ** LANGAR_CMDS. نه کپی، نه ابرمجموعه.

    ⚠️ نسخهٔ اولِ این تست فقط `effective_routes()` بی‌آرگومان را می‌سنجید و
    جهشِ «شرطِ فلگ را بردار» را زنده رد کرد: زیرِ harness مسیرِ langar پیدا
    نمی‌شود، پس مشتق خالی می‌ماند و مسیرِ روشن هم اتفاقاً همان ایستا را
    می‌دهد. یعنی پایه از قبل همان نتیجه را می‌داد — گاردِ کور. حالا سورسِ
    **واقعی** تزریق می‌شود تا دو شاخه واقعاً از هم فرق کنند."""
    os.environ.pop(lb.ROUTE_DERIVE_FLAG, None)
    assert lb.effective_routes() is lb.LANGAR_CMDS
    assert lb.LANGAR_CMDS == PRE_FIX_ROUTES, "تاپلِ ایستا نباید عوض شده باشد"
    # و مسیریابیِ خاموش هنوز همان چیزی را رد می‌کند که امروز رد می‌کرد.
    assert not lb._routed("/studio", lb.effective_routes())
    assert lb._routed("/pf_status", lb.effective_routes())
    src = _src()
    if not src:
        print("      ⏭ SKIP(نیمه) — سورسِ واقعی نبود؛ شاخهٔ تزریقی سنجیده نشد")
        return
    # با سورسِ واقعی، شاخهٔ روشن قطعاً ابرمجموعه است. پس اگر خاموش هم همان را
    # بدهد، فلگ اثری ندارد و parity دروغ است.
    assert lb.effective_routes(source=src) is lb.LANGAR_CMDS, \
        "فلگ خاموش ولی جدول عوض شد — parity شکست"


def t_b7_flag_on_widens_and_never_narrows():
    """فلگ روشن → ابرمجموعهٔ ایستا. هیچ ردیفِ امروزی حذف نمی‌شود."""
    src = _src()
    if not src:
        print("      ⏭ SKIP — langar_bot.py پیدا نشد")
        return
    os.environ[lb.ROUTE_DERIVE_FLAG] = "1"
    try:
        eff = set(lb.effective_routes(source=src))
    finally:
        os.environ.pop(lb.ROUTE_DERIVE_FLAG, None)
    assert set(lb.LANGAR_CMDS) <= eff, sorted(set(lb.LANGAR_CMDS) - eff)
    assert "/studio" in eff and "/reset" in eff and "/inbox" in eff
    assert "/code" not in eff, "تصادمِ نام باید مسدود بماند تا رأیِ مالک"


def t_b8_empty_derivation_falls_back_to_the_static_table():
    """اگر سورس ناخوانا شد، فلگِ روشن نباید جدول را **کوچک** کند."""
    os.environ[lb.ROUTE_DERIVE_FLAG] = "1"
    try:
        assert lb.effective_routes(source="def broken(:\n") == lb.LANGAR_CMDS
    finally:
        os.environ.pop(lb.ROUTE_DERIVE_FLAG, None)


# ═══ A · `/lead` — یک نام، دو معنی ══════════════════════════════════════════
def t_c1_teeth_pre_fix_reads_aud_as_square_metres():
    """🦷 دندان — رفتارِ پیش-از-فیکس: مثالِ **خودِ راهنمای باتِ درونی** به پارسرِ
    کوت داده می‌شود و بی‌صدا ۵۰۰۰ متر می‌شود. بدونِ خطا. بدونِ هشدار."""
    import quote_cmd as qc
    p = qc.parse("/lead بازسازی آشپزخانه | 5000 | lead.doer")
    assert p.get("ok") is True, p
    assert p["fields"]["size_m2"] == 5000.0, p["fields"]
    assert p["fields"].get("area_type") == "lead.doer", p["fields"]
    # یعنی: پارسر «پا» را «نوعِ سطح» خواند و AUD را متر. هیچ‌کس نپرسید.


def t_c2_register_grammar_is_recognised():
    for t in ("/lead بازسازی آشپزخانه | 5000 | lead.doer",
              "/lead x | ۵۰۰۰ | ziman.doer",
              "/lead y | 1200.5 | crypto.doer"):
        r = cr.lead_intent(t)
        assert r["intent"] == "register", (t, r)


def t_c3_quote_grammar_is_never_stolen():
    """مهم‌تر از گرفتنِ گرامرِ ثبت: **نگرفتنِ** گرامرِ کوت. یک مثبتِ کاذب این‌جا
    یعنی تنها راهِ کوت‌گرفتن در تلگرام بسته می‌شود."""
    for t in ("/lead آشپزخانه ۳خوابه | 120 | interior | standard | residential",
              "/lead نما | 80 | exterior",
              "/lead اتاق | 40 | داخلی",
              "/lead اتاق | 40",
              "/lead اتاق",
              "/lead",
              "/lead a | 5000 | lead.doer | extra | more",   # ۵ فیلد = کوت
              "/lead a | ناعدد | lead.doer"):
        r = cr.lead_intent(t)
        assert r["intent"] != "register", (t, r)
    # و مثبتِ صریح: `area_type` باید **شناخته** شود، نه صرفاً «ثبت نیست».
    # نسخهٔ اولِ این تست فقط `!= register` را می‌سنجید و جهشِ «شاخهٔ کوت را
    # حذف کن» زنده ماند — چون چکِ «پا» هم اتفاقاً همان ورودی را رد می‌کرد.
    for t in ("/lead آشپزخانه | 120 | interior | standard | residential",
              "/lead نما | 80 | exterior",
              "/lead اتاق | 40 | داخلی",
              "/lead اتاق | 40 | بیرونی"):
        r = cr.lead_intent(t)
        assert r["intent"] == "quote" and r["why"] == "area-type", (t, r)


def t_c4_guard_is_off_by_default_and_speaks_only_when_armed():
    """فلگ خاموش → `None` برای **هر** ورودی = رفتارِ امروز بایت‌به‌بایت."""
    os.environ.pop(cr.LEAD_FLAG, None)
    for t in ("/lead بازسازی | 5000 | lead.doer",
              "/lead آشپزخانه | 120 | interior"):
        assert cr.lead_guard(t) is None, t
    os.environ[cr.LEAD_FLAG] = "1"
    try:
        card = cr.lead_guard("/lead بازسازی | 5000 | lead.doer")
        assert card and "lead.doer" in card and "متراژ" in card, card
        assert cr.lead_guard("/lead آشپزخانه | 120 | interior") is None
    finally:
        os.environ.pop(cr.LEAD_FLAG, None)


def t_c5_center_actually_calls_the_guard():
    """گاردی که صداکننده ندارد مرده است — و این‌جا دو بار در ۲۴ ساعت رخ داده.
    AST ِ `center.py:_quote_cmd` باید `chat_room.lead_guard` را صدا بزند."""
    import ast
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8", errors="replace")
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_quote_cmd"), None)
    assert fn is not None, "_quote_cmd در center.py پیدا نشد"
    calls = [n.func.attr for n in ast.walk(fn)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    assert "lead_guard" in calls, f"_quote_cmd گارد را صدا نمی‌زند: {calls}"


# ═══ صداکنندهٔ تولیدی ═══════════════════════════════════════════════════════
def t_d_added_symbols_have_production_callers():
    """هر چیزی که اضافه شد باید بیرون از `_ops/tests` صداکننده داشته باشد.
    شمارش با AST روی سورسِ تولیدی — نه grep، که کامنت را هم می‌شمارد."""
    import ast
    prod = {
        "effective_routes": _OPS / "legs" / "langar_bridge.py",
        "lead_guard": _OPS / "telegram_center" / "center.py",
    }
    for name, path in prod.items():
        tree = ast.parse(path.read_text("utf-8", errors="replace"))
        n = sum(1 for x in ast.walk(tree)
                if isinstance(x, ast.Call)
                and ((isinstance(x.func, ast.Name) and x.func.id == name)
                     or (isinstance(x.func, ast.Attribute) and x.func.attr == name)))
        assert n >= 1, f"{name} صفر صداکنندهٔ تولیدی دارد — مرده است"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_langar_route_parity: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
