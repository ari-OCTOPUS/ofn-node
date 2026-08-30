"""test_dashboard.py — تست‌های داشبورد زندهٔ :8770.

نکات:
  - بدون import از organism.py (crash 独立性).
  - route-smoke، env-write، restart-logic، profile round-trip.
  - $0-assert: هیچ spend / capability-gate لمس نمی‌شود.
"""
import importlib
import json
import os
import sys
import tempfile
import threading
import time
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlencode

_HERE = Path(__file__).resolve().parent
_DASH = _HERE.parent / "dashboard"
sys.path.insert(0, str(_DASH))
sys.path.insert(0, str(_HERE))           # harness.py

# ماژولِ dashboard را لود کن (آدرسِ مطلق تا_shadow نشود)
import importlib.util
_spec = importlib.util.spec_from_file_location("dash_srv", _DASH / "server.py")
dash = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dash)


# ── ۱. هیچ import از organism ندارد ──────────────────────────────────────────────
def test_no_organism_import():
    """داشبورد نباید organism.py را import کند (crash 独立性)."""
    src = (_DASH / "server.py").read_text("utf-8")
    # فرض: نباید "import organism" یا "from organism" در سورس باشد
    assert "import organism" not in src.replace("import importlib", ""), \
        "dashboard نباید organism.py را import کند"
    assert "from organism" not in src, "dashboard نباید از organism.py import کند"


# ── ۲. route-smoke ───────────────────────────────────────────────────────────────
def _start_server(port: int):
    """سرور را روی یک پورتِ تست شروع کن. برمی‌گرداند: (conn, srv)."""
    from http.server import ThreadingHTTPServer
    srv = ThreadingHTTPServer(("127.0.0.1", port), dash._Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.3)
    return HTTPConnection("127.0.0.1", port), srv


def _stop(srv):
    srv.shutdown()
    srv.server_close()


def test_routes_smoke():
    """تمامِ routeهای GET باید ۲۰۰ برگردانند (یا ۴۰۴ برای مجهول)."""
    conn, srv = _start_server(18770)
    try:
        for path in ["/", "/capabilities", "/activity", "/channels", "/ideas", "/api/flags"]:
            conn.request("GET", path)
            r = conn.getresponse()
            body = r.read()
            assert r.status == 200, f"{path} → {r.status}"
            assert len(body) > 0, f"{path} بدنهٔ خالی"
        # مجهول → ۴۰۴
        conn.request("GET", "/nonexistent")
        r = conn.getresponse()
        assert r.status == 404
    finally:
        _stop(srv)


def test_organism_page_when_no_state():
    """اگر state نباشد، صفحهٔ ارگانیسم راهنما نشان می‌دهد."""
    conn, srv = _start_server(18771)
    try:
        conn.request("GET", "/")
        r = conn.getresponse()
        body = r.read().decode("utf-8")
        # یا state هست (رویِ دستگاهِ واقعی) یا نیست — هر دو معتبر، ولی صفحه باید رندر شود
        assert r.status == 200
        assert "ارگانیسم" in body or "RUN-ORGANISM" in body
    finally:
        _stop(srv)


# ── ۳. env-write ──────────────────────────────────────────────────────────────────
def test_write_env_creates_file():
    """POST /save باید OCTOPUS.env را atomic بسازد با محتوای درست."""
    with tempfile.TemporaryDirectory() as td:
        fake_env = Path(td) / "OCTOPUS.env"
        # monkey-patch مسیرِ ENV_FILE
        orig = dash.ENV_FILE
        dash.ENV_FILE = fake_env
        try:
            form = {
                "OCTOPUS_PROFILE": "bare",
                "OCTOPUS_WIRE_DOCTOR": "1",
                "OCTOPUS_WIRE_NEURAL": "0",
                "CHRONO_DOCTOR_EVERY_N_BEATS": "999",
            }
            msg = dash._write_env(form)
            assert "ذخیره شد" in msg
            assert fake_env.exists()
            content = fake_env.read_text("utf-8")
            assert "set OCTOPUS_PROFILE=bare" in content
            assert "set OCTOPUS_WIRE_DOCTOR=1" in content
            assert "set OCTOPUS_WIRE_NEURAL=0" in content
            assert "set CHRONO_DOCTOR_EVERY_N_BEATS=999" in content
        finally:
            dash.ENV_FILE = orig


def test_write_env_profile_roundtrip():
    """paper-full ← bare و bare ← paper-full درست ست می‌شوند."""
    with tempfile.TemporaryDirectory() as td:
        fake_env = Path(td) / "OCTOPUS.env"
        orig = dash.ENV_FILE
        dash.ENV_FILE = fake_env
        try:
            dash._write_env({"OCTOPUS_PROFILE": "paper-full"})
            c1 = fake_env.read_text("utf-8")
            assert "set OCTOPUS_PROFILE=paper-full" in c1
            dash._write_env({"OCTOPUS_PROFILE": "bare"})
            c2 = fake_env.read_text("utf-8")
            assert "set OCTOPUS_PROFILE=bare" in c2
            assert "paper-full" not in c2.split("OCTOPUS_PROFILE=")[1].split("\n")[0]
        finally:
            dash.ENV_FILE = orig


def test_write_env_rejects_bad_cadence():
    """cadence غیر‌عددی باید به default برگردد."""
    with tempfile.TemporaryDirectory() as td:
        fake_env = Path(td) / "OCTOPUS.env"
        orig = dash.ENV_FILE
        dash.ENV_FILE = fake_env
        try:
            dash._write_env({"CHRONO_DOCTOR_EVERY_N_BEATS": "not-a-number"})
            content = fake_env.read_text("utf-8")
            assert "set CHRONO_DOCTOR_EVERY_N_BEATS=1440" in content  # default
        finally:
            dash.ENV_FILE = orig


# ── ۴. restart-logic ─────────────────────────────────────────────────────────────
def test_do_restart_creates_both_files():
    """restart باید STOP-ORGANISM + RESTART-REQUESTED هر دو را بسازد."""
    with tempfile.TemporaryDirectory() as td:
        fake_stop = Path(td) / "STOP-ORGANISM"
        fake_restart = Path(td) / "RESTART-REQUESTED"
        o1, o2 = dash.STOP_ORGANISM, dash.RESTART_REQUESTED
        dash.STOP_ORGANISM = fake_stop
        dash.RESTART_REQUESTED = fake_restart
        try:
            msg = dash._do_restart()
            assert "STOP-ORGANISM" in msg or "RESTART" in msg
            assert fake_stop.exists(), "STOP-ORGANISM ساخته نشد"
            assert fake_restart.exists(), "RESTART-REQUESTED ساخته نشد"
        finally:
            dash.STOP_ORGANISM, dash.RESTART_REQUESTED = o1, o2


# ── ۵. $0 / no-spend assert ──────────────────────────────────────────────────────
def test_no_spend_paths():
    """سورسِ داشبورد نباید مسیرِ spend/capability-gate را لمس کند."""
    src = (_DASH / "server.py").read_text("utf-8")
    forbidden = ["capability_gate", "money_gate", "budget_gate", "ledger.append",
                 "ledger_note", "EffectorGate"]
    found = [f for f in forbidden if f in src]
    assert not found, f"داشبورد نباید این مسیرها را لمس کند: {found}"


def test_write_targets_only_control_files():
    """تنهایی writeهای مجاز: OCTOPUS.env + STOP-ORGANISM + RESTART-REQUESTED."""
    src = (_DASH / "server.py").read_text("utf-8")
    # write_text یا os.replace باید فقط برای control-fileها باشد (در _write_env و _do_restart)
    # هیچ write به ledger/state نباید باشد
    # ORGANISM-STATE فقط باید خوانده شود (_read_json)، نه نوشته
    for line in src.split("\n"):
        stripped = line.strip()
        if "ORGANISM-STATE" in stripped and "read" not in stripped.lower() \
                and "ORGANISM-STATE" not in stripped.split("=")[0]:
            # خطوطی مثل comment یا dict literal مجازند — فقط writeهای عملیاتی ممنوع
            if any(kw in stripped for kw in ["write_text", "open(", "json.dump", "os.replace"]):
                assert False, f"ORGANISM-STATE نباید نوشته شود: {stripped}"


# ── ۶. effective flags ────────────────────────────────────────────────────────────
def test_effective_flags_profile_default():
    """paper-full باید flagهای امن را روشن کند."""
    # بدون env override، profile default از os.environ
    orig_prof = os.environ.pop("OCTOPUS_PROFILE", None)
    orig_ov = dash._read_env_overrides
    try:
        # این تست منطقِ profile default را می‌سنجد، نه OCTOPUS-flags.cmd زنده را.
        # پاک‌کردن env کافی نبود: server دوباره فایل override را می‌خواند و مثلاً
        # BARBELL=1 زنده را روی paper-full اعمال می‌کرد (قرمزِ وابسته به محیط).
        dash._read_env_overrides = lambda: {}
        os.environ["OCTOPUS_PROFILE"] = "paper-full"
        for n, _, _ in dash.WIRE_FLAGS:
            os.environ.pop(n, None)
        eff = dash._effective_flags()
        assert eff["OCTOPUS_WIRE_DOCTOR"] is True
        assert eff["OCTOPUS_WIRE_NEURAL"] is True
        # barbell risky → در paper-full نیست
        assert eff["OCTOPUS_WIRE_BARBELL"] is False
    finally:
        dash._read_env_overrides = orig_ov
        if orig_prof is not None:
            os.environ["OCTOPUS_PROFILE"] = orig_prof
        else:
            os.environ.pop("OCTOPUS_PROFILE", None)


def test_effective_flags_bare():
    """bare + بدونِ env-override باید همه را خاموش کند (منطقِ profile).
    جلسه ۴۶: OCTOPUS-flags.cmdِ واقعی حالا برای go-live چند flag را force می‌کند (override
    بر profile مقدم است — precedence درست). این تست منطقِ profile را می‌سنجد، پس override-file
    را ایزوله می‌کند."""
    orig_prof = os.environ.pop("OCTOPUS_PROFILE", None)
    orig_ov = dash._read_env_overrides
    try:
        dash._read_env_overrides = lambda: {}   # ایزوله از OCTOPUS-flags.cmdِ واقعی
        os.environ["OCTOPUS_PROFILE"] = "bare"
        for n, _, _ in dash.WIRE_FLAGS:
            os.environ.pop(n, None)
        eff = dash._effective_flags()
        assert all(not v for v in eff.values()), "bare باید همه را خاموش کند"
    finally:
        dash._read_env_overrides = orig_ov
        if orig_prof is not None:
            os.environ["OCTOPUS_PROFILE"] = orig_prof
        else:
            os.environ.pop("OCTOPUS_PROFILE", None)


# ── ۸. /api/flags نباید کلیدِ unmanaged را نشان دهد (ممیزیِ وب‌اپ ۲۰۲۶-۰۸-۰۷) ─────
def test_safe_env_overrides_drops_unmanaged_keys():
    """`_read_env_overrides()` هر خطِ `set KEY=VALUE` را خام برمی‌گرداند — شاملِ
    کلیدهایِ ناشناخته که ممکن است هر مقداری (حتی چیزی شبیهِ secret) داشته باشند.
    `_safe_env_overrides()` باید فقط کلیدهایِ مدیریت‌شده را نگه دارد."""
    orig = dash._read_env_overrides
    try:
        fake_managed_name = dash.WIRE_FLAGS[0][0]
        dash._read_env_overrides = lambda: {
            fake_managed_name: "1",
            "OCTOPUS_PROFILE": "paper-full",
            "SOME_RANDOM_TOKEN": "<REDACTED-OPENAI-KEY>",
        }
        out = dash._safe_env_overrides()
        assert out == {fake_managed_name: "1", "OCTOPUS_PROFILE": "paper-full"}, out
        assert "SOME_RANDOM_TOKEN" not in out, "کلیدِ unmanaged باید بیرون بماند"
    finally:
        dash._read_env_overrides = orig


def test_api_flags_endpoint_never_leaks_unmanaged_key():
    """تستِ end-to-end واقعی: یک درخواستِ HTTP ِ واقعی به /api/flags، با یک
    ENV_FILE ِ ساختگی که یک خطِ unmanaged دارد — پاسخ نباید آن خط را داشته باشد."""
    orig_env_file = dash.ENV_FILE
    with tempfile.TemporaryDirectory() as d:
        fake_env = Path(d) / "OCTOPUS-flags.cmd"
        fake_env.write_text(
            "set OCTOPUS_PROFILE=paper-full\r\n"
            "set NOT_A_REAL_FLAG_JUST_A_TOKEN=sk-shaped-value-1234\r\n",
            "utf-8")
        dash.ENV_FILE = fake_env
        port = 18770
        conn, srv = _start_server(port)
        try:
            conn.request("GET", "/api/flags")
            r = conn.getresponse()
            body = r.read().decode("utf-8")
            assert r.status == 200
            assert "sk-shaped-value-1234" not in body, "مقدارِ unmanaged نباید در پاسخ باشد"
            assert "NOT_A_REAL_FLAG_JUST_A_TOKEN" not in body, "کلیدِ unmanaged نباید در پاسخ باشد"
            d2 = json.loads(body)
            assert d2["env_overrides"].get("OCTOPUS_PROFILE") == "paper-full"
        finally:
            conn.close()
            srv.shutdown()
            dash.ENV_FILE = orig_env_file


# ── ۷. self-test runner ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import harness
    failed = harness.run([
        ("هیچ import از organism", test_no_organism_import),
        ("route smoke", test_routes_smoke),
        ("organism page بدون state", test_organism_page_when_no_state),
        ("write env فایل‌سازی", test_write_env_creates_file),
        ("write env profile roundtrip", test_write_env_profile_roundtrip),
        ("write env cadence بد رد شود", test_write_env_rejects_bad_cadence),
        ("do restart هر دو فایل", test_do_restart_creates_both_files),
        ("no spend paths", test_no_spend_paths),
        ("write targets فقط control-files", test_write_targets_only_control_files),
        ("effective flags default", test_effective_flags_profile_default),
        ("effective flags bare", test_effective_flags_bare),
        ("safe_env_overrides کلیدِ unmanaged را حذف می‌کند", test_safe_env_overrides_drops_unmanaged_keys),
        ("/api/flags کلیدِ unmanaged نشت نمی‌دهد", test_api_flags_endpoint_never_leaks_unmanaged_key),
    ])
    sys.exit(1 if failed else 0)
