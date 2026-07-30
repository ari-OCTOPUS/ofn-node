"""test_surface_policy — چهار جوابِ مالک، تبدیل‌شده به ناوردی.

رأیِ ۲۰۲۶-۰۷-۲۸: «گروه = پاها · یک چتِ خصوصی برای خودآگاهی · بقیه جای دیگر»،
«فقط وقتی واقعاً به من نیاز داری»، «یک چیز در هر پیام، یک دکمه».

دادهٔ پشتِ این تصمیم (۱۷۶ ارسال، ۲۶–۲۸ جولای): ۶۲٪ در General، ۲۳٪ در ⚙️سیستم،
۱۱٪ در 🧠دانش، و **هر ۷ تاپیکِ بیزنسی فقط یک پیام** — کارتِ ساخته‌شدنشان. یعنی
گروه لولهٔ سروصدای سیستم بود و اتاق‌های کار خالی.

سه مرزی که این تست محافظت می‌کند:
  ۱) **ایمنی هرگز نگه داشته نمی‌شود.** سکوت روی cortisol/alert یعنی مرگِ خاموش.
  ۲) **نگه‌داشتن ≠ دورانداختن.** هرچه فرستاده نشد باید ثبت شده باشد، وگرنه
     بعداً نمی‌شود سنجید که سکوت درست بوده.
  ۳) **فلگ خاموش = بایت‌به‌بایت مثل قبل.** این ماژول روی مسیرِ زندهٔ ارسال
     می‌نشیند؛ اگر خاموشی‌اش کامل نباشد، یک no-op می‌تواند پیام‌ها را ببلعد.
"""
import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("surface-policy")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import surface_policy as sp   # noqa: E402


def _on(v=True):
    if v:
        os.environ[sp.FLAG] = "1"
    else:
        os.environ.pop(sp.FLAG, None)


# ─── ۰: خاموشی باید کامل باشد ─────────────────────────────────────────────
def t_flag_off_routes_nothing_at_all():
    """این ماژول روی مسیرِ زندهٔ ارسال است — خاموشی نصفه یعنی پیامِ بلعیده‌شده."""
    _on(False)
    for s in ("lead", "brain", "heart", "cortisol", "", None, "ناشناخته"):
        assert sp.route(s) == (None, None), s


def t_flag_off_never_holds():
    _on(False)
    for s in ("heart", "doctor", "summary"):
        dest, _ = sp.route(s)
        assert dest != sp.HOLD, s


# ─── ۱: گروه = پاها ───────────────────────────────────────────────────────
def t_every_leg_goes_to_its_own_room():
    _on()
    try:
        for stream, key in sp.LEG_TOPIC.items():
            dest, k = sp.route(stream)
            assert dest == sp.GROUP and k == key, (stream, dest, k)
    finally:
        _on(False)


def t_the_leg_rooms_exist_in_the_centre_config_contract():
    """اتاقی که در configِ مرکز نباشد، پیام را به جایی می‌فرستد که وجود ندارد.

    ⚠️ نسخهٔ اول این چک سورسِ `approval_channel.py` را می‌گشت و روی `studio_pf`
    قرمز شد — ولی آن کلید **آن‌جا نیست و نباید باشد**: قرارداد `center-config.json`
    است. تست فرضِ غلطِ خودش را به‌عنوان عیبِ کد گزارش کرده بود.
    """
    import json
    cfg_p = harness.REAL_VAULT / "_ops" / "state" / "telegram" / "center-config.json"
    if not cfg_p.exists():
        return                      # بدونِ config چیزی برای سنجیدن نیست
    topics = (json.loads(cfg_p.read_text("utf-8")).get("topics") or {})
    missing = [k for k in sp.LEG_TOPIC.values() if k not in topics]
    assert not missing, f"اتاقِ این پاها در configِ مرکز نیست: {missing}"


# ─── ۲: چتِ خصوصی = خودآگاهی ──────────────────────────────────────────────
def t_self_awareness_streams_go_to_the_private_chat():
    _on()
    try:
        for s in sp.SELF_STREAMS:
            dest, k = sp.route(s)
            assert dest == sp.DM and k == "self", (s, dest, k)
    finally:
        _on(False)


def t_a_stream_is_never_both_a_leg_and_a_self_stream():
    """اگر یک نام در هر دو باشد، مقصدش به ترتیبِ کد بستگی دارد نه به معنا."""
    assert not (set(sp.LEG_TOPIC) & sp.SELF_STREAMS)
    assert not (set(sp.LEG_TOPIC) & sp.SAFETY_STREAMS)
    assert not (sp.SELF_STREAMS & sp.SAFETY_STREAMS)


# ─── ۳: ایمنی هرگز ساکت نمی‌شود ───────────────────────────────────────────
def t_safety_is_never_held():
    """مهم‌ترین مرز: سکوت روی هشدار یعنی مرگِ خاموش."""
    _on()
    try:
        for s in sp.SAFETY_STREAMS:
            dest, k = sp.route(s)
            assert dest == sp.DM and k == "safety", (s, dest, k)
    finally:
        _on(False)


def t_needs_owner_still_carries_its_reason_label():
    """`needs_owner` از ۰۷-۳۰ فقط برچسب را عوض می‌کند — مقصد در هر دو DM است.
    برچسب مهم است: «تصمیمِ مالک» و «محیطی» نباید در لاگ یکی به نظر برسند."""
    _on()
    try:
        assert sp.route("doctor", needs_owner=True) == (sp.DM, "needs-owner")
        assert sp.route("doctor") == (sp.DM, "ambient")
    finally:
        _on(False)


# ─── ۴: تحویل، نه سکوت (رأیِ مالک ۲۰۲۶-۰۷-۳۰) ─────────────────────────────
def t_ambient_streams_are_delivered_to_the_dm_not_held():
    """⚠️ این بند تا ۰۷-۳۰ **وارونه** بود و عمداً بازنویسی شد — نه برای سبزکردن،
    بلکه چون خودِ مالک رأی را عوض کرد: «ناگفته‌ها به DM اختاپوس بیایند.»

    تاریخچه: رأیِ ۰۷-۲۸ («فقط وقتی واقعاً به من نیاز داری») fallback را HOLD
    کرد و از همان لحظه ~۱۷۰ پیامِ doctor/heart/needs بی‌صدا در
    held-stream.jsonl ماند — ثبت‌شده ولی نادیده. مالک وقتی شمارش را در پالسِ
    ساعتیِ لنگر دید، تحویل را انتخاب کرد. اگر روزی این بند دوباره وارونه شود،
    باید یک رأیِ سومِ ثبت‌شده پشتش باشد، نه یک ویرایشِ بی‌صدا."""
    _on()
    try:
        for s in ("heart", "doctor", "needs", "summary", "center", "چیزِ‌ناشناخته"):
            dest, key = sp.route(s)
            assert dest == sp.DM, (s, dest, "محیطی باید تحویل شود، نه HOLD")
            assert key == "ambient", (s, key)
        # و هیچ مسیری در route دیگر HOLD تولید نمی‌کند — سازوکارِ hold فقط
        # آرشیو/فراخوانِ صریح است.
        for s in ("", None, "x" * 80):
            assert sp.route(s)[0] != sp.HOLD, s
    finally:
        _on(False)


def t_what_was_not_sent_is_still_recorded():
    """سکوت نباید فراموشی باشد — وگرنه بعداً نمی‌شود سنجید که درست بوده."""
    before = len(sp.held_since(500))
    assert sp.hold("doctor", "متنِ آزمایشی") is True
    rows = sp.held_since(500)
    assert len(rows) == before + 1
    assert rows[-1]["stream"] == "doctor" and "آزمایشی" in rows[-1]["text"]


def t_the_hold_log_stays_inside_the_isolated_tree():
    """گاردِ نشتی — همان تلهٔ money-fsm که امروز صبح درختِ زنده را آلوده کرد."""
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(sp._held_path()).lower().startswith(live), sp._held_path()


def t_a_broken_hold_never_raises():
    """ثبت‌نشدن نباید ارسال را بکشد."""
    real = sp._held_path
    sp._held_path = lambda: Path("/\x00نامعتبر/x.jsonl")
    try:
        assert sp.hold("x", "y") is False
    finally:
        sp._held_path = real


# ─── ۵: یک چیز، یک دکمه ───────────────────────────────────────────────────
def t_one_thing_carries_at_most_one_button():
    """هر دکمهٔ اضافه یک تصمیمِ اضافه است."""
    r = sp.one_thing("سرخط", "زمینه", "بزن")
    assert r["ok"] and r["n_buttons"] == 1 and len(r["buttons"]) == 1


def t_one_thing_keeps_context_to_a_single_line():
    r = sp.one_thing("سرخط", "خطِ اول\nخطِ دوم\nخطِ سوم", "بزن")
    assert r["text"].count("\n") == 1, r["text"]


def t_one_thing_without_an_action_has_zero_buttons():
    r = sp.one_thing("فقط خبر")
    assert r["ok"] and r["n_buttons"] == 0 and r["buttons"] == []


def t_an_empty_headline_produces_nothing():
    for bad in ("", "   ", None):
        assert sp.one_thing(bad)["ok"] is False


# ─── ۶: سیم ───────────────────────────────────────────────────────────────
def t_the_send_path_consults_the_policy_before_routing():
    """AST نه گرپ: مشورت باید **قبل از** `_stream_route` باشد وگرنه بی‌اثر است."""
    src = (_OPS / "budget" / "approval_channel.py").read_text("utf-8")
    i = src.index("import surface_policy")
    j = src.index("_stream_route(stream)", i)
    assert j > i, "سیاست بعد از مسیریابی مشورت می‌شود"
    assert "_sp.hold(stream, text)" in src[i:j], "نگه‌داشته ثبت نمی‌شود"


def t_the_send_path_honours_all_three_destinations_not_just_hold():
    """⚠️ این چک از یک نقصِ واقعیِ همان روز آمد.

    نسخهٔ اولِ سیم‌کشی **فقط** شاخهٔ HOLD را می‌خواند و برای DM/GROUP مسیرِ
    قدیمی تصمیم می‌گرفت. سه دقیقه بعد از ری‌استارت اندازه‌گیریِ زنده نشانش داد:
    `needs` درست نگه داشته شد، ولی `discovery` — که باید به چتِ خصوصی می‌رفت —
    به تاپیکِ گروه رفت. سیاست جوابِ درست را می‌داد و **کسی نمی‌خواندش**.

    درس: «سیاست وصل شد» را با **هر سه** مقصد بسنج، نه با یکی. یک شاخهٔ
    سیم‌شده از سه‌تا، از بیرون شبیهِ «وصل است» به نظر می‌رسد.
    """
    src = (_OPS / "budget" / "approval_channel.py").read_text("utf-8")
    i = src.index("import surface_policy")
    j = src.index("r_chat, r_topic = _stream_route(stream)", i)
    seg = src[i:j + 60]
    assert '== "dm"' in seg, "شاخهٔ DM سیم نشده — به گروه می‌رود"
    assert '== "group"' in seg, "شاخهٔ GROUP سیم نشده"
    assert "_topic_by_key" in seg, "کلیدِ اتاق به chat/topic ترجمه نمی‌شود"


def t_a_missing_room_falls_back_instead_of_vanishing():
    """اتاقِ نبود نباید پیام را ببلعد — گم‌شدن بدتر از جای اشتباه است."""
    import approval_channel as ac
    assert ac._topic_by_key(None) == (None, None)
    assert ac._topic_by_key("اتاقی-که-وجود-ندارد") == (None, None)


def t_the_send_path_cannot_be_killed_by_the_policy():
    """سیاست هرگز نباید ارسال را بشکند — باید داخلِ try باشد."""
    tree = ast.parse((_OPS / "budget" / "approval_channel.py").read_text("utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Try) and "surface_policy" in ast.dump(n):
            assert n.handlers, "try بدونِ except"
            return
    raise AssertionError("مشورتِ سیاست داخلِ try نیست")


def t_the_policy_module_sends_nothing_itself():
    """این ماژول فقط مقصد را می‌گوید. اگر خودش بفرستد، همهٔ گیت‌ها دور می‌خورند."""
    tree = ast.parse(Path(sp.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http", "smtplib"}), imported
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("send", "send_text", "post", "sendMessage"):
        assert d not in called, f"سیاست خودش می‌فرستد: {d}"


def t_the_policy_is_reachable_from_every_process_not_just_the_centre():
    """سیاست باید از **هر چهار پروسه** پیدا شود، نه فقط از مرکز.

    ۲۰۲۶-۰۷-۲۸، ممیزیِ متخاصم: `import surface_policy` لختِ داخلِ مسیرِ ارسالِ
    `approval_channel` فقط وقتی کار می‌کرد که پروسه از `_ops/telegram_center`
    اجرا شده باشد (آن‌جا sys.path[0] است). از `organism` و `cortex` و `live`
    غایب بود، به `except` می‌افتاد، و مسیرِ قدیمی تصمیم می‌گرفت — بی هیچ خطا،
    چون fallback درست بود. رأیِ سطحِ مالک از یک پروسه اعمال می‌شد و از سه تای
    دیگر بی‌صدا رد.

    این تست **زیرپروسهٔ واقعی** با cwdِ هر چهار پروسه بالا می‌آورد. گاردِ متنی
    (grepِ `sys.path.insert` کنارِ import) دقیقاً همان چیزی است که این باگ ازش
    رد شد: کد آن‌جا بود، اثرش نبود.
    """
    import subprocess
    ops = Path(__file__).resolve().parent.parent
    code = ("import sys;"
            f"sys.path.insert(0, r'{ops}');"
            f"sys.path.insert(0, r'{ops / 'budget'}');"
            "import approval_channel as ac;"
            "print('OK' if ac.load_surface_policy() is not None else 'MISSING')")
    for sub in ("", "cortex", "live", "budget", "telegram_center"):
        cwd = ops / sub if sub else ops
        if not cwd.is_dir():
            continue
        out = subprocess.run([sys.executable, "-X", "utf8", "-c", code],
                             cwd=str(cwd), capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
        assert "OK" in (out.stdout or ""), (
            f"سیاست از پروسه‌ای با cwd={cwd.name or '_ops'} پیدا نشد: "
            f"{(out.stdout or '')[-200:]} {(out.stderr or '')[-300:]}")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_surface_policy: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
