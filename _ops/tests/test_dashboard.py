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
    try:
        os.environ["OCTOPUS_PROFILE"] = "paper-full"
        # پاک‌کردنِ overrideهای صریح تا default اعمال شود
        for n, _, _ in dash.WIRE_FLAGS:
            os.environ.pop(n, None)
        eff = dash._effective_flags()
        assert eff["OCTOPUS_WIRE_DOCTOR"] is True
        assert eff["OCTOPUS_WIRE_NEURAL"] is True
        # barbell risky → در paper-full نیست
        assert eff["OCTOPUS_WIRE_BARBELL"] is False
    finally:
        if orig_prof is not None:
            os.environ["OCTOPUS_PROFILE"] = orig_prof
        else:
            os.environ.pop("OCTOPUS_PROFILE", None)


def test_effective_flags_bare():
    """bare باید همه را خاموش کند."""
    orig_prof = os.environ.pop("OCTOPUS_PROFILE", None)
    try:
        os.environ["OCTOPUS_PROFILE"] = "bare"
        for n, _, _ in dash.WIRE_FLAGS:
            os.environ.pop(n, None)
        eff = dash._effective_flags()
        assert all(not v for v in eff.values()), "bare باید همه را خاموش کند"
    finally:
        if orig_prof is not None:
            os.environ["OCTOPUS_PROFILE"] = orig_prof
        else:
            os.environ.pop("OCTOPUS_PROFILE", None)


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
    ])
    sys.exit(1 if failed else 0)
