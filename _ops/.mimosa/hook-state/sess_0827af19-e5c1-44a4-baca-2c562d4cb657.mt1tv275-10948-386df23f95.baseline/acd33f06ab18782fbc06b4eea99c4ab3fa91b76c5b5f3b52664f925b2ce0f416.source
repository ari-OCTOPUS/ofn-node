"""test_latent_poller_guard — گامِ ۶ ِ UNIFICATION-DESIGN-2026-08-03 (C14).

خطرِ سنجیده‌شده: `4d_system/` از ۲۰۲۶-۰۷-۱۸ بازنشسته است و هیچ پروسه/تسکی آن
را اجرا نمی‌کند، ولی `4d_system/brain/telegram_bot.py` روی `getUpdates`
long-poll می‌کند و توکنش را از **همان نامِ env ِ مرکزِ زنده** می‌گیرد. اگر روزی
بالا بیاید، دو پولر روی یک توکن ⇒ `409 Conflict` ⇒ فشارِ دکمهٔ مالک را هرکدام
که برنده شد می‌بلعد. خطر «نهفته» است، نه فعال — و باید نهفته بماند.

دو ناوردی اینجا سنجیده می‌شود:
  ۱) گارد پیش‌فرض **رد** می‌کند: خروجِ ناصفر، پیامی که ۴۰۹ و DEPRECATED.md را
     نام ببرد، و **صفر فراخوانیِ شبکه** (با requests ِ جعلی اثبات می‌شود).
  ۲) پروبِ `latent_second_poller` امروز LATENT می‌گوید نه ACTIVE — و اگر گارد
     برداشته شود یا opt-in مسلح شود، عدد **حرکت می‌کند** (تاشدگیِ یک‌طرفه کور است).

اجرا:  PYTHONIOENCODING=utf-8 python -X utf8 test_latent_poller_guard.py
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True     # نه pycِ کهنه در درختِ زنده، نه جهشِ خوانده‌نشده

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("latent-poller")

_OPS = harness.SELF_OPS
_REPO = _OPS.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import c6_probes as cp   # noqa: E402

BOT = _REPO / "4d_system" / "brain" / "telegram_bot.py"
LIVE_STATE = _REPO / "_ops" / "state"


# ─── ابزارِ فیکسچر ─────────────────────────────────────────────────────────

def _fixture(slug: str) -> Path:
    """ریشهٔ موقت. هر مسیرِ تست اینجاست — هرگز زیرِ درختِ زنده."""
    d = Path(tempfile.mkdtemp(prefix=f"latent-poller-{slug}-")).resolve()
    assert not str(d).lower().startswith(str(_REPO).lower()), \
        f"فیکسچر زیرِ درختِ زنده ساخته شد: {d}"
    return d


_DRIVER = '''\
import importlib.util, json, sys, types
from pathlib import Path
sys.dont_write_bytecode = True
rec = Path(sys.argv[2])
fake = types.ModuleType("requests")
def _net(*a, **k):
    rec.write_text(json.dumps({"network": True}), "utf-8")
    raise SystemExit(9)          # سنتینل: اولین تماسِ شبکه، بدونِ هیچ شبکهٔ واقعی
fake.post = _net
fake.get = _net
sys.modules["requests"] = fake
spec = importlib.util.spec_from_file_location("tb4d_under_test", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.run_bot()
sys.stdout.write("REACHED_END_OF_RUN_BOT\\n")
'''


def _run_bot_sandboxed(opt_in: str | None) -> tuple[int, str, Path]:
    """`run_bot()` را در یک پروسهٔ جدا با envِ **شسته** اجرا می‌کند.

    محیط فقط شاملِ چیزهای لازمِ ویندوز + دو مقدارِ **جعلی** است، پس «رد» را
    نمی‌شود با «تنظیم‌نشده» اشتباه گرفت. هیچ .env خوانده نمی‌شود؛ ماژول فقط
    از os.getenv می‌خواند."""
    fx = _fixture("sandbox")
    rec = fx / "network-calls.json"
    drv = fx / "driver.py"
    drv.write_text(_DRIVER, "utf-8")
    env = {
        "SystemRoot": os.environ.get("SystemRoot", r"C:\Windows"),
        "PATH": os.environ.get("PATH", ""),
        "TEMP": str(fx), "TMP": str(fx),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        # توکن/چتِ **ساختگی**: «رد» باید از گارد بیاید نه از is_configured().
        "TELEGRAM_BOT_TOKEN": "0000000000:FAKE-NOT-A-REAL-TOKEN",
        "TELEGRAM_CHAT_ID": "424242",
    }
    if opt_in is not None:
        env["OCTOPUS_4D_TELEGRAM_BOT_OPT_IN"] = opt_in
    p = subprocess.run([sys.executable, str(drv), str(BOT), str(rec)],
                       cwd=str(fx), env=env, capture_output=True, timeout=120)
    out = (p.stdout or b"").decode("utf-8", "replace") + \
          (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out, rec


def _mod_ast():
    import ast
    return ast.parse(BOT.read_text("utf-8"))


def _func(tree, name):
    import ast
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _first_stmt(fn):
    """اولین دستورِ اجرایی — docstring رد می‌شود."""
    import ast
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return body[0] if body else None


# ─── ۱: گارد پیش‌فرض رد می‌کند ─────────────────────────────────────────────

def t_guard_refuses_by_default_with_nonzero_exit():
    """پیش‌فرض = رد. سنجه exit code است، نه یک فلگ یا یک لاگ."""
    rc, out, _ = _run_bot_sandboxed(opt_in=None)
    assert rc != 0, f"گارد اجازه داد: exit={rc} out={out[:400]!r}"
    assert "REACHED_END_OF_RUN_BOT" not in out, f"run_bot تا انتها رفت: {out[:400]!r}"
    assert rc == 3, f"کدِ خروجِ ردِ گارد ۳ نیست: {rc} out={out[:400]!r}"


def t_refusal_makes_zero_network_calls():
    """«صفر getUpdates» با requests ِ جعلی اثبات می‌شود، نه با اعتماد.

    اگر گارد بعد از اولین تماس بنشیند، فایلِ ضبط ساخته می‌شود و این قرمز است."""
    rc, out, rec = _run_bot_sandboxed(opt_in=None)
    assert not rec.exists(), \
        f"شبکه لمس شد با وجودِ رد (exit={rc}): {rec.read_text('utf-8')[:200]}"


def t_refusal_names_the_409_risk_and_the_deprecation_doc():
    """پیامِ رد باید بگوید **چرا** و **کجا را بخوان** — وگرنه فقط یک کرشِ مبهم است."""
    rc, out, _ = _run_bot_sandboxed(opt_in=None)
    for needle in ("409", "DEPRECATED.md", "OCTOPUS_4D_TELEGRAM_BOT_OPT_IN",
                   "TELEGRAM_BOT_TOKEN"):
        assert needle in out, f"پیامِ رد «{needle}» را نام نمی‌برد: {out[:500]!r}"


def t_guard_allows_when_the_opt_in_is_set():
    """رأیِ مالک باید واقعاً در را باز کند — وگرنه گارد یک حذفِ پنهان است.

    مسیرِ اجازه بدونِ هیچ شبکهٔ واقعی اثبات می‌شود: requests ِ جعلی اولین تماس
    را ضبط می‌کند و با کدِ سنتینلِ ۹ خارج می‌شود. exit=9 ⇒ گارد رد نکرد و
    مسیر تا چوک‌پوینتِ شبکه رفت."""
    rc, out, rec = _run_bot_sandboxed(opt_in="1")
    assert "REFUSED" not in out, f"با opt-in هم رد کرد: {out[:400]!r}"
    assert rec.exists(), f"به چوک‌پوینتِ شبکه نرسید (exit={rc}) out={out[:400]!r}"
    assert json.loads(rec.read_text("utf-8")).get("network") is True, rec.read_text("utf-8")
    assert rc == 9, f"سنتینلِ شبکهٔ جعلی برنگشت: exit={rc} out={out[:400]!r}"


def t_opt_in_is_fail_closed_on_every_other_value():
    """هر چیزی جز رأیِ صریح = خاموش. غیاب، تهی، «0»، «off» — همه رد.

    `opt_in_enabled` از **سورسِ خودِ ماژول** (نه یک رونوشت) بیرون کشیده و
    اجرا می‌شود؛ فقط انتساب‌های سطحِ بالا و همان تابع، تا importِ کاملِ ماژول
    (و pycِ کنارِ درختِ زنده) لازم نشود."""
    import ast
    src = BOT.read_text("utf-8")
    tree = ast.parse(src)
    ns: dict = {}
    pieces = []
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.Assign)):
            pieces.append(ast.get_source_segment(src, n))
        elif isinstance(n, ast.FunctionDef) and n.name == "opt_in_enabled":
            pieces.append(ast.get_source_segment(src, n))
    exec(compile("\n".join(p for p in pieces if p), str(BOT), "exec"), ns)
    enabled = ns.get("opt_in_enabled")
    assert callable(enabled), "opt_in_enabled در سورس پیدا نشد"
    for off in ({}, {"OCTOPUS_4D_TELEGRAM_BOT_OPT_IN": ""},
                {"OCTOPUS_4D_TELEGRAM_BOT_OPT_IN": "0"},
                {"OCTOPUS_4D_TELEGRAM_BOT_OPT_IN": "off"},
                {"OCTOPUS_4D_TELEGRAM_BOT_OPT_IN": "maybe"}):
        assert enabled(off) is False, f"مقدارِ {off} نباید در را باز کند"
    for on in ("1", "true", "TRUE", " yes ", "on"):
        assert enabled({"OCTOPUS_4D_TELEGRAM_BOT_OPT_IN": on}) is True, \
            f"رأیِ صریح «{on}» رد شد"


def t_guard_runs_before_any_token_read_or_network():
    """گارد باید **اولین** دستورِ هر نقطهٔ ورود باشد.

    «قبل از شبکه» یعنی ساختاراً اول، نه اینکه امیدوار باشیم کسی وسطش چیزی
    اضافه نکند. سه نقطهٔ ورود: run_bot (اسکریپت)، poll_once (long-poll)،
    _api (چوک‌پوینتِ شبکه — تنها جایی که requests import می‌شود)."""
    import ast
    tree = _mod_ast()
    for name in ("run_bot", "poll_once", "_api"):
        fn = _func(tree, name)
        assert fn is not None, f"نقطهٔ ورود {name} پیدا نشد"
        st = _first_stmt(fn)
        assert isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) \
            and getattr(st.value.func, "id", None) == "require_opt_in", \
            f"{name} اولین کارش require_opt_in() نیست: {ast.dump(st)[:160] if st else None}"


def t_module_is_preserved_not_deleted():
    """قاعدهٔ vault: هرگز حذف نکن. گارد نباید به بهانهٔ امنیت ماژول را تهی کند."""
    assert BOT.exists(), "ماژولِ بازنشسته حذف شده"
    src = BOT.read_text("utf-8")
    for sym in ("def route_command", "def route_callback", "def build_status_text",
                "def poll_once", "def run_bot"):
        assert sym in src, f"نمادِ موجود گم شد: {sym}"


# ─── ۲: پروبِ latent_second_poller ─────────────────────────────────────────

def _mk_probe_repo(guard: bool, ignition: bool, armed: bool) -> tuple[Path, Path]:
    """درختِ ساختگی: یک پولرِ زنده + یک پولرِ بازنشسته، هر دو روی نامِ توکنِ مشترک."""
    fx = _fixture("probe")
    live = fx / "_ops" / "budget"
    live.mkdir(parents=True)
    (live / "live_poller.py").write_text(
        "import os\n"
        "def _env_str(n, d=''):\n    return os.environ.get(n, d)\n"
        "class C:\n"
        "    def __init__(self):\n        self._t = _env_str('TELEGRAM_BOT_TOKEN')\n"
        "    def poll(self):\n"
        "        return self._get(self._build_url('getUpdates', {}))\n"
        "    def beat(self):\n        return 'live-poll.json'\n", "utf-8")
    dep = fx / "4d_system" / "brain"
    dep.mkdir(parents=True)
    body = ["import os", "OPT = 'OCTOPUS_FIXTURE_OPT_IN'",
            "def _token():\n    return os.getenv('TELEGRAM_BOT_TOKEN', '')",
            "def poll_once(o):\n    return _api('getUpdates', offset=o)",
            "def _api(m, **k):\n    return None"]
    if guard:
        body.append("def require_opt_in(env=None):\n"
                    "    if os.environ.get(OPT):\n        return\n"
                    "    raise SystemExit(3)")
    (dep / "deprecated_poller.py").write_text("\n".join(body) + "\n", "utf-8")
    if ignition:
        sc = fx / "4d_system" / "scripts"
        sc.mkdir(parents=True, exist_ok=True)
        (sc / "start_x.bat").write_text(
            "@echo off\r\npython -m brain.deprecated_poller\r\n", "utf-8")
    sd = fx / "state"
    (sd / "pulse").mkdir(parents=True)
    (sd / "pulse" / "live-poll.json").write_text(
        json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "batch": 0}), "utf-8")
    if armed:
        (sd / "flags-loaded-fixture.json").write_text(
            json.dumps({"schema": "flags-loaded.v1",
                        "flags": {"OCTOPUS_FIXTURE_OPT_IN": "1"}}), "utf-8")
    return fx, sd


def t_probe_fixture_reports_latent_not_active():
    """پولرِ بازنشسته با گارد = LATENT؛ پولرِ زنده با نبضِ تازه = ACTIVE.
    reachable باید ۱ باشد، نه ۲ — و نه ۰."""
    fx, sd = _mk_probe_repo(guard=True, ignition=True, armed=False)
    r = cp._probe_latent_second_poller(repo_root=fx, state_dir=sd)
    d = r["detail"]
    assert "candidates=2" in d, f"دو نامزد شمرده نشد: {d}"
    assert r["count"] == 1, f"reachable باید ۱ باشد نه {r['count']}: {d}"
    assert "deprecated_poller.py=LATENT" in d, f"بازنشسته LATENT نشد: {d}"
    assert "live_poller.py=ACTIVE" in d, f"پولرِ زنده ACTIVE نشد: {d}"


def t_probe_moves_when_the_guard_is_removed():
    """تاشدگیِ یک‌طرفه کور است: بدونِ گارد و با مسیرِ روشن‌شدن باید ۲ بدهد."""
    fx, sd = _mk_probe_repo(guard=False, ignition=True, armed=False)
    r = cp._probe_latent_second_poller(repo_root=fx, state_dir=sd)
    assert r["count"] == 2, f"بدونِ گارد باید ۲ قابلِ‌رسیدن باشد: {r}"
    assert "deprecated_poller.py=UNKNOWN" in r["detail"], r["detail"]


def t_probe_does_not_trust_a_guard_whose_opt_in_is_armed():
    """گاردِ مسلح‌شده دیگر گارد نیست. «فلگ اعلام شد» ≠ «اثر دارد»."""
    fx, sd = _mk_probe_repo(guard=True, ignition=True, armed=True)
    r = cp._probe_latent_second_poller(repo_root=fx, state_dir=sd)
    assert r["count"] == 2, f"با opt-in ِ مسلح باید قابلِ‌رسیدن شمرده شود: {r}"


def t_probe_says_unknown_never_zero_when_it_scanned_nothing():
    """نبودِ داده حکم نیست: درختِ خالی باید -1 بدهد، نه یک صفرِ تمیزِ آرامش‌بخش."""
    fx = _fixture("empty")
    (fx / "state").mkdir()
    r = cp._probe_latent_second_poller(repo_root=fx, state_dir=fx / "state")
    assert r["count"] == -1, f"درختِ خالی صفر گزارش کرد: {r}"
    assert "UNKNOWN" in r["detail"], r["detail"]


def t_probe_on_the_live_tree_is_latent_not_active():
    """سنجهٔ پذیرشِ طرح روی درختِ واقعی (فقط‌خواندنی): ۲ نامزد، ≤۱ قابلِ رسیدن،
    و ماژولِ 4D هرگز ACTIVE نیست."""
    r = cp._probe_latent_second_poller(repo_root=_REPO, state_dir=LIVE_STATE)
    d = r["detail"]
    assert "candidates=2" in d, f"روی درختِ زنده دو نامزد شمرده نشد: {d}"
    assert r["count"] <= 1, f"دو پولرِ قابلِ رسیدن روی یک توکن — ۴۰۹ در راه است: {d}"
    assert "4d_system/brain/telegram_bot.py=LATENT" in d, f"4D نهفته نیست: {d}"
    assert "4d_system/brain/telegram_bot.py=ACTIVE" not in d, d


def t_probe_is_registered_with_a_floor_that_fires_on_two():
    """پروبی که ثبت نشود، پروب نیست."""
    spec = cp.PROBES.get("latent_second_poller")
    assert spec, "latent_second_poller در PROBES ثبت نشده"
    assert spec["measure"] is cp._probe_latent_second_poller
    assert spec["floor"] == 1, f"floor باید ۱ باشد تا ۲ شلیک کند: {spec['floor']}"
    assert "reads" not in spec, \
        "اعلانِ reads ِ ساختگی باعث می‌شود predicate_never_matches بی‌صدا skip کند"


def t_probe_never_writes_and_never_executes():
    """پروب فقط مشاهده می‌کند. یک خواننده که بنویسد یا اجرا کند، خواننده نیست."""
    import ast
    tree = ast.parse((_OPS / "c6_probes.py").read_text("utf-8"))
    mine = [n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and (n.name.startswith("_poller_") or n.name == "_probe_latent_second_poller")]
    assert len(mine) >= 5, f"توابعِ پروب پیدا نشدند: {[n.name for n in mine]}"
    banned = {"write_text", "write_bytes", "mkdir", "unlink", "rmtree", "touch",
              "rename", "makedirs", "remove", "run", "Popen", "urlopen", "system"}
    bad = []
    for fn in mine:
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                nm = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                if nm in banned:
                    bad.append(f"{fn.name}:{nm}")
            elif isinstance(n, ast.Import):
                bad += [f"{fn.name}:import {a.name}" for a in n.names
                        if a.name.split(".")[0] in ("subprocess", "socket", "requests",
                                                    "urllib", "shutil")]
    assert not bad, f"پروب می‌نویسد/اجرا می‌کند: {sorted(bad)}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_latent_poller_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
