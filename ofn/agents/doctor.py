"""doctor — دکترِ سلامتِ بورد (OCTOPUS-AUTONOMY-SPEC-2026-09-03 §1).

تشخیص، نه درمان. این ماژول با «ofn/doctor» (لِین LB — دکترِ والت، اسکنِ
سند/مرجع با ReceiptLog) فرق دارد: آنجا بیمار والت است، اینجا بیمار خودِ
بورد — یونیت‌ها، نبض، پرچم‌ها، سقف‌ها، اثرهای بیرونی، هم‌ترازی repo/بورد
و میزبان. هیچ مسیر ترمیمی وجود ندارد: نه restart، نه نوشتن پرچم، نه
ارسال، نه حذف. تنها نوشتنِ مجاز، خودِ گزارش در STATE_DIR است.

چهار حالت، بی‌هیچ پنجمی و بی‌هیچ پیش‌فرضی:
  HEALTHY   پروب شد، سالم است
  UNHEALTHY پروب شد، خراب است
  UNPROBED  وجود دارد ولی پروب نشد — خطرناک‌ترین حالت (F-12)
  UNKNOWN   پروب شد، پاسخ قابل‌تفسیر نبود (fail-closed، هرگز حدس)

قاعدهٔ نانوشتنی: UNPROBED هرگز در تجمیع به HEALTHY تبدیل نمی‌شود؛
«۶ از ۶ پروب‌شدهٔ سالم» با «همه‌چیز سالم» یکی نیست. هر اندازه‌گیری
measured_at و فرمانِ تکرارپذیر دارد (قاعدهٔ F-09: ادعا بدون اندازه‌گیری
ننوشته شود) — همین است که WAL را تا WITNESS_B برد.
"""

from __future__ import annotations

import enum
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SCHEMA = "octopus.doctor.v1"
REPORT_PATH = opslib.STATE_DIR / "doctor" / "report.json"
PULSE_MAX_AGE_S = 2 * 3600  # دو تیکِ تایمرِ ساعتی (مقصد: نبض قدیمی = UNHEALTHY)
# سقفِ تازگیِ آخرین اجرای یک oneshot. محافزه‌کارانه (یک تیکِ روزانه
# + حاشیه) تا تایمرهای روزانه هشدارِ کاذب ندهند. سخت‌کردنِ این سقف بر پایهٔ
# دورهٔ خودِ تایمر، کارِ مجزا است (خارج از دامنهٔ این اصلاح).
ONESHOT_MAX_AGE_S = 26 * 3600

# دسته‌بندی پرچم‌ها: کدام بارِ واقعی دارد و کدام فقط ابراز نیت است
# (config.py:78-81 — OFN_WIRE_OUTBOUND را هیچ کد production نمی‌خواند).
INTENT_ONLY_FLAGS = frozenset({
    "OFN_WIRE_OUTBOUND",
})
LOAD_BEARING_FLAGS = frozenset({
    "OCTOPUS_WIRE_LEAD_OUTBOUND",
    "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL",
    "OFN_WIRE_EMAIL",
    "OFN_WIRE_PUBLISH",
    "OFN_KEEP_GATES_OPEN",
    "OFN_EXTRA_CLOSED_GATES",
})


class Verdict(str, enum.Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNPROBED = "unprobed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Measurement:
    name: str
    value: object | None
    verdict: Verdict
    source: str          # «systemctl show» · «sqlite3 <db>» · «cat <path>» …
    measured_at: str     # الزامی — opslib.now_iso()
    command: str         # تکرارپذیر توسط انسان
    sha256: str | None = None
    detail: str | None = None
    family: str = "misc"

    def as_dict(self) -> dict:
        d = {
            "name": self.name,
            "value": self.value,
            "verdict": self.verdict.value,
            "source": self.source,
            "measured_at": self.measured_at,
            "command": self.command,
            "sha256": self.sha256,
            "detail": self.detail,
            "family": self.family,
        }
        return d


def _sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
    except OSError:
        return None


def _oneshot_last_run_age_s(
    props: Mapping[str, str], now_monotonic: float
) -> float | None:
    """سنِ آخرین اجرای یک یونیت oneshot بر پایهٔ CLOCK_MONOTONIC.

    systemd مقدار را به میکروّانیه از زمان بوت می‌دهد؛ صفر یعنی هنوز خارج نشده.
    هر ناتوانی در خواندن یا تفسیر → None، تا فراخوان fail-closed بماند
    (قاعدهٔ «UNKNOWN، هرگز حدس»). پس اگر این property روی نسخهٔ systemd
    میزبان وجود نداشته باشد، رفتار به همین امروز (UNKNOWN) برمی‌گردد
    و هرگز به HEALTHYِ کاذب نمی‌رسد.
    """
    raw = props.get("ExecMainExitTimestampMonotonic", "").strip()
    if not raw:
        return None
    try:
        exited_us = int(raw)
    except ValueError:
        return None
    if exited_us <= 0:
        return None
    age = now_monotonic - (exited_us / 1_000_000)
    return age if age >= 0 else None


def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    """اجرای فقط-خواندنی و fail-soft. خروجی هرگز پروسه را نمی‌کشد."""
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            errors="replace")
        return p.returncode, (p.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return -1, ""


# ── خانوادهٔ ۱ — یونیت‌های systemd: همهٔ octopus-*، نه فقط MEMBER_UNITS ──────

def probe_units(
    runner: Callable[[list[str]], tuple[int, str]] = _run,
    now_iso: str | None = None,
    now_monotonic: float | None = None,
) -> list[Measurement]:
    ts = now_iso or opslib.now_iso()
    mono = time.monotonic() if now_monotonic is None else now_monotonic
    out: list[Measurement] = []
    if shutil.which("systemctl") is None:
        out.append(Measurement(
            "units.discovery", None, Verdict.UNPROBED, "systemctl which",
            ts, "command -v systemctl",
            detail="systemctl unavailable — unit scope cannot be enumerated"))
        return out
    rc, listing = runner(["systemctl", "list-units", "octopus-*", "--all",
                          "--no-legend", "--plain"])
    if rc != 0 or not listing.strip():
        out.append(Measurement(
            "units.discovery", None, Verdict.UNPROBED, "systemctl list-units",
            ts, "systemctl list-units 'octopus-*' --all --no-legend --plain",
            detail=f"rc={rc} — not booted with systemd or no units visible"))
        return out
    units = [ln.split()[0] for ln in listing.splitlines() if ln.strip()]
    for unit in units:
        rc_u, body = runner(
            ["systemctl", "show", unit, "--property=ActiveState",
             "--property=Result", "--property=UnitFileState",
             "--property=Type",
             "--property=ExecMainExitTimestampMonotonic"])
        if rc_u != 0:
            out.append(Measurement(
                f"unit.{unit}", None, Verdict.UNPROBED, "systemctl show", ts,
                f"systemctl show {unit} --property=ActiveState,Result",
                detail=f"show rc={rc_u}"))
            continue
        props = dict(
            (k, v) for k, _, v in
            (ln.partition("=") for ln in body.splitlines() if "=" in ln))
        active = props.get("ActiveState", "")
        result = props.get("Result", "")
        file_state = props.get("UnitFileState", "")
        svc_type = props.get("Type", "")
        cmd = (f"systemctl show {unit} --property=ActiveState,Result,"
               f"UnitFileState,Type,ExecMainExitTimestampMonotonic")
        age: float | None = None
        if result == "exit-code" or active == "failed":
            v, detail = Verdict.UNHEALTHY, f"Result={result} ActiveState={active}"
        elif active == "active":
            v, detail = Verdict.HEALTHY, f"ActiveState=active ({file_state})"
        elif file_state == "disabled":
            # خاموشِ عمدی: خودش خرابی نیست، ولی «سالم» هم نیست تا رأی/رسیدش دیده شود
            v, detail = Verdict.UNKNOWN, "disabled — deliberate? check ruling receipt"
        elif (svc_type == "oneshot" and result == "success"
              and active in ("inactive", "dead")):
            # oneshotِ بینِ دو اجرا: inactive+success حالتِ طبیعیِ اوست، نه ابهام.
            # سنجهٔ درست، تازگیِ آخرین اجراست نه ActiveState — وگرنه هر oneshotِ
            # سالم بین دو شلیک، UNKNOWNِ کاذب می‌شود و دکتر بی‌اعتبار می‌ماند.
            age = _oneshot_last_run_age_s(props, mono)
            if age is None:
                v, detail = Verdict.UNKNOWN, (
                    "oneshot: last-run age unavailable — "
                    "ExecMainExitTimestampMonotonic missing or unparseable")
            elif age <= ONESHOT_MAX_AGE_S:
                v, detail = Verdict.HEALTHY, (
                    f"oneshot between runs — last exit {int(age)}s ago, "
                    f"Result=success ({file_state})")
            else:
                v, detail = Verdict.UNHEALTHY, (
                    f"oneshot last exit {int(age)}s ago > {ONESHOT_MAX_AGE_S}s — "
                    "timer likely not firing")
        else:
            v, detail = Verdict.UNKNOWN, f"ActiveState={active} Result={result}"
        out.append(Measurement(
            f"unit.{unit}", {"active": active, "result": result,
                             "file_state": file_state, "type": svc_type,
                             "last_run_age_s": None if age is None else int(age)},
            v, "systemctl show", ts, cmd, detail=detail, family="units"))
    return out


# ── خانوادهٔ ۲ — تازگی نبض (آخرین رسید events.jsonl) ────────────────────────

def probe_pulse(
    events_path: Path | None = None,
    now: float | None = None,
    now_iso: str | None = None,
) -> list[Measurement]:
    ts = now_iso or opslib.now_iso()
    p = events_path or (opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl")
    if not p.exists():
        return [Measurement(
            "pulse.events", None, Verdict.UNPROBED, "file", ts, f"cat {p}",
            detail="events.jsonl absent — pulse age cannot be measured")]
    try:
        last_line = p.read_text(encoding="utf-8", errors="replace") \
            .rstrip("\n").splitlines()[-1]
        occurred = json.loads(last_line).get("occurred_at", "")
        age = (now if now is not None else time.time()) - _parse_iso(occurred)
        verdict = (Verdict.HEALTHY if age <= PULSE_MAX_AGE_S
                   else Verdict.UNHEALTHY)
        return [Measurement(
            "pulse.events", {"last": occurred, "age_s": round(age, 1)},
            verdict, "file", ts, f"tail -1 {p}",
            detail="stale beyond two timer ticks" if verdict ==
            Verdict.UNHEALTHY else None, family="pulse")]
    except (OSError, ValueError, IndexError):
        return [Measurement(
            "pulse.events", None, Verdict.UNKNOWN, "file", ts, f"tail -1 {p}",
            detail="unreadable/corrupt last receipt — fail closed",
            family="pulse")]


def _parse_iso(s: str) -> float:
    import datetime as _dt
    return _dt.datetime.fromisoformat(
        s.replace("Z", "+00:00")).timestamp()


# ── خانوادهٔ ۳ — پرچم‌ها: مقدار + SHA + بارِ واقعی در برابر intent-only ──────

def probe_flags(
    managed_flags: Path | None = None,
    node_env: Path | None = None,
    now_iso: str | None = None,
) -> list[Measurement]:
    ts = now_iso or opslib.now_iso()
    out: list[Measurement] = []
    mf = managed_flags or (Path.home() / "ofn/ofn/agi2027_runtime/"
                           "managed_flags.json")
    if not mf.exists():
        out.append(Measurement(
            "flags.managed", None, Verdict.UNKNOWN, "file", ts, f"cat {mf}",
            detail="managed_flags.json missing — unknown, never assumed",
            family="flags"))
    else:
        sha = _sha256_file(mf)
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            out.append(Measurement(
                "flags.managed", data, Verdict.HEALTHY, "file", ts,
                f"sha256sum {mf} && cat {mf}", sha256=sha, family="flags"))
        except (OSError, ValueError):
            out.append(Measurement(
                "flags.managed", None, Verdict.UNKNOWN, "file", ts,
                f"sha256sum {mf} && cat {mf}", sha256=sha,
                detail="corrupt JSON — banner-grade unknown", family="flags"))
    ne = node_env or (Path.home() / ".config/ofn/node.env")
    if not ne.exists():
        out.append(Measurement(
            "flags.node_env", None, Verdict.UNPROBED, "file", ts, f"cat {ne}",
            detail="node.env absent on this host", family="flags"))
        return out
    try:
        values: dict[str, str] = {}
        for ln in ne.read_text(encoding="utf-8", errors="replace").splitlines():
            k, _, v = ln.partition("=")
            if k.strip() in (INTENT_ONLY_FLAGS | LOAD_BEARING_FLAGS):
                values[k.strip()] = v.strip()
        payload = {k: {
            "value": v,
            "class": ("intent-only — gates nothing, never read as safety"
                      if k in INTENT_ONLY_FLAGS else "load-bearing"),
        } for k, v in sorted(values.items())}
        out.append(Measurement(
            "flags.node_env", payload, Verdict.HEALTHY, "file", ts,
            "grep -E '^(OFN_WIRE_OUTBOUND|OCTOPUS_WIRE_LEAD_OUTBOUND"
            "|OFN_WIRE_EMAIL|OFN_WIRE_PUBLISH|OFN_KEEP_GATES_OPEN"
            "|OFN_EXTRA_CLOSED_GATES)' " + str(ne), family="flags"))
    except OSError:
        out.append(Measurement(
            "flags.node_env", None, Verdict.UNKNOWN, "file", ts, f"cat {ne}",
            detail="unreadable", family="flags"))
    return out


# ── خانوادهٔ ۴ — سقف‌ها و شمارنده‌ها: هر دو سقف، مقدار زنده، هرگز هاردکد ──

def probe_caps(
    counter_path: Path | None = None,
    now_iso: str | None = None,
) -> list[Measurement]:
    ts = now_iso or opslib.now_iso()
    out: list[Measurement] = []
    try:
        import outbound_worker
        cap = outbound_worker._lead_daily_send_cap()
        out.append(Measurement(
            "caps.lead_daily_send", cap, Verdict.HEALTHY, "env+code", ts,
            "echo $OCTOPUS_LEAD_DAILY_SEND_CAP (default 10; <=0 = unlimited)",
            detail="owner rulings 2026-07-31 / 2026-08-12", family="caps"))
        sends = outbound_worker.sends_today()
        out.append(Measurement(
            "caps.sends_today", sends, Verdict.HEALTHY, "file+code", ts,
            f"cat {outbound_worker._counter_path()}", family="caps"))
    except Exception as e:  # noqa: BLE001
        out.append(Measurement(
            "caps.lead", None, Verdict.UNKNOWN, "import", ts,
            "python3 -c 'import outbound_worker'", detail=f"err:{type(e).__name__}",
            family="caps"))
    cp = counter_path or (opslib.STATE_DIR / "legs" / "lead-send-counter.json")
    if cp.exists():
        try:
            out.append(Measurement(
                "caps.counter_file", json.loads(cp.read_text(encoding="utf-8")),
                Verdict.HEALTHY, "file", ts, f"cat {cp}", family="caps"))
        except (OSError, ValueError):
            out.append(Measurement(
                "caps.counter_file", None, Verdict.UNKNOWN, "file", ts,
                f"cat {cp}", detail="corrupt counter — worker fails closed",
                family="caps"))
    else:
        out.append(Measurement(
            "caps.counter_file", None, Verdict.UNPROBED, "file", ts,
            f"cat {cp}", detail="no sends recorded yet", family="caps"))
    try:
        repo_root = _HERE.parents[1]
        sys.path.insert(0, str(repo_root))
        from ofn.config import (D27_DAILY_SEND_CAP, D27_DAILY_SPEND_CAP_AUD,
                                D27_PER_BOARD_BUDGET_DEFAULT)
        out.append(Measurement(
            "caps.d27_frame", {"send_per_day": D27_DAILY_SEND_CAP,
                               "spend_aud_per_day": D27_DAILY_SPEND_CAP_AUD,
                               "per_board_budget": D27_PER_BOARD_BUDGET_DEFAULT},
            Verdict.HEALTHY, "code constants", ts,
            "grep D27_ <repo>/ofn/config.py",
            detail="framework caps — separate from the lead transport cap",
            family="caps"))
    except Exception as e:  # noqa: BLE001
        out.append(Measurement(
            "caps.d27_frame", None, Verdict.UNKNOWN, "import", ts,
            "grep D27_ <repo>/ofn/config.py", detail=f"err:{type(e).__name__}",
            family="caps"))
    return out


# ── خانوادهٔ ۵ — اثرهای بیرونی: شمار، آخرین، تفکیک روز، دلتا ────────────────

def probe_outbound_effects(
    db_path: Path | None = None,
    previous_report: Path | None = None,
    now_iso: str | None = None,
) -> list[Measurement]:
    ts = now_iso or opslib.now_iso()
    db = db_path or (Path.home() / "ofn/ofn/agi2027_runtime/"
                     "outbound-effects.sqlite3")
    if not db.exists():
        return [Measurement(
            "effects.outbound", None, Verdict.UNPROBED, "sqlite3", ts,
            f"sqlite3 {db} 'SELECT state,COUNT(*) FROM outbound_effects GROUP BY state'",
            detail="db absent on this host", family="effects")]
    cmd = (f"sqlite3 {db} "
           "'SELECT state,COUNT(*) FROM outbound_effects GROUP BY state'")
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = c.execute(
            "SELECT state, COUNT(*) FROM outbound_effects GROUP BY state"
        ).fetchall()
        last = c.execute(
            "SELECT effect_id, updated_at FROM outbound_effects "
            "ORDER BY updated_at DESC LIMIT 1").fetchone()
        c.close()
        counts = {s: n for s, n in rows}
        prev_sent = None
        pr = previous_report or REPORT_PATH
        if pr.exists():
            try:
                prev_sent = json.loads(
                    pr.read_text(encoding="utf-8")).get(
                    "effects_prev_sent")
            except (OSError, ValueError):
                prev_sent = None
        sent = counts.get("sent", 0)
        delta = (sent - prev_sent) if isinstance(prev_sent, int) else None
        return [Measurement(
            "effects.outbound",
            {"counts": counts, "last_effect": (last or [None, None])[0],
             "prev_sent": prev_sent, "delta_since_last_report": delta},
            Verdict.HEALTHY, "sqlite3", ts, cmd,
            detail="unexpected new send = first-class event"
            if (delta or 0) > 0 else None, family="effects")]
    except sqlite3.Error as e:
        return [Measurement(
            "effects.outbound", None, Verdict.UNKNOWN, "sqlite3", ts, cmd,
            detail=f"err:{type(e).__name__}", family="effects")]


# ── خانوادهٔ ۶ — هم‌ترازی repo/بورد (بدون شبکه) ─────────────────────────────

def probe_repo_alignment(
    git_dir: Path | None = None,
    now_iso: str | None = None,
) -> list[Measurement]:
    ts = now_iso or opslib.now_iso()
    g = git_dir or (Path.home() / "ofn")
    if not (g / ".git").exists():
        return [Measurement(
            "align.repo", None, Verdict.UNPROBED, "git", ts,
            f"git -C {g} rev-parse HEAD", detail="no checkout on this host",
            family="align")]
    head_rc, head = _run(["git", "-C", str(g), "rev-parse", "HEAD"])
    main_rc, mainref = _run(
        ["git", "-C", str(g), "rev-parse", "origin/main"])
    if head_rc != 0 or main_rc != 0:
        return [Measurement(
            "align.repo", None, Verdict.UNKNOWN, "git", ts,
            f"git -C {g} rev-parse HEAD origin/main",
            detail="refs unreadable", family="align")]
    if head.strip() == mainref.strip():
        return [Measurement(
            "align.repo", {"head": head.strip()[:8],
                           "origin_main": mainref.strip()[:8], "behind": 0},
            Verdict.HEALTHY, "git", ts,
            f"git -C {g} rev-parse HEAD origin/main", family="align")]
    behind_rc, behind = _run(
        ["git", "-C", str(g), "rev-list", "--count",
         f"HEAD..{mainref.strip()}"])
    n = behind.strip() if behind_rc == 0 else "?"
    return [Measurement(
        "align.repo", {"head": head.strip()[:8],
                       "origin_main": mainref.strip()[:8], "behind": n},
        Verdict.UNHEALTHY, "git", ts,
        f"git -C {g} rev-list --count HEAD..origin/main",
        detail=f"board {n} commits behind origin/main — cockpit renders the "
               "past", family="align")]


# ── خانوادهٔ ۷ — میزبان: دیسک/حافظه/journal/smart ───────────────────────────

def probe_host(now_iso: str | None = None) -> list[Measurement]:
    ts = now_iso or opslib.now_iso()
    out: list[Measurement] = []
    try:
        st = os.statvfs("/")
        pct = int(100 * st.f_bavail / st.f_blocks)
        out.append(Measurement(
            "host.disk_free_pct", pct,
            Verdict.HEALTHY if pct >= 15 else Verdict.UNHEALTHY,
            "statvfs", ts, "df -h /",
            detail=None if pct >= 15 else "disk below 15%", family="host"))
    except (OSError, AttributeError):
        out.append(Measurement(
            "host.disk_free_pct", None, Verdict.UNKNOWN, "statvfs", ts,
            "df -h /", detail="statvfs unavailable (non-POSIX?)",
            family="host"))
    uptime_path = Path("/proc/uptime")
    if uptime_path.exists():
        try:
            up = int(float(uptime_path.read_text().split()[0]))
            out.append(Measurement(
                "host.uptime_s", up, Verdict.HEALTHY, "/proc/uptime", ts,
                "cat /proc/uptime", family="host"))
        except (OSError, ValueError):
            out.append(Measurement(
                "host.uptime_s", None, Verdict.UNKNOWN, "/proc/uptime", ts,
                "cat /proc/uptime", family="host"))
    else:
        out.append(Measurement(
            "host.uptime_s", None, Verdict.UNPROBED, "/proc/uptime", ts,
            "cat /proc/uptime", detail="no /proc on this host",
            family="host"))
    if shutil.which("journalctl") is None:
        out.append(Measurement(
            "host.journal_readable", None, Verdict.UNPROBED, "journalctl",
            ts, "journalctl -n 1", detail="journalctl unavailable",
            family="host"))
    else:
        rc, _ = _run(["journalctl", "-n", "1", "--no-pager"])
        out.append(Measurement(
            "host.journal_readable", rc == 0,
            Verdict.HEALTHY if rc == 0 else Verdict.UNPROBED, "journalctl",
            ts, "journalctl -n 1",
            detail=None if rc == 0 else
            "tracebacks unreadable for this user — an UNPROBED of its own",
            family="host"))
    return out


# ── تجمیع ────────────────────────────────────────────────────────────────────

def build_report(
    families: list[list[Measurement]] | None = None,
    extra: dict | None = None,
) -> dict:
    if families is None:
        families = [
            probe_units(), probe_pulse(), probe_flags(),
            probe_caps(), probe_outbound_effects(), probe_repo_alignment(),
            probe_host(),
        ]
    ms = [m for f in families for m in f]
    healthy = sum(1 for m in ms if m.verdict is Verdict.HEALTHY)
    unhealthy = sum(1 for m in ms if m.verdict is Verdict.UNHEALTHY)
    unprobed_names = [m.name for m in ms if m.verdict is Verdict.UNPROBED]
    unknown_names = [m.name for m in ms if m.verdict is Verdict.UNKNOWN]
    if unhealthy:
        verdict = "degraded"
    elif unprobed_names or unknown_names:
        verdict = "incomplete"
    else:
        verdict = "healthy"
    probed_total = healthy + unhealthy
    scope = len(ms)
    banner = (f"{probed_total}/{scope} measurements probed-clean — "
              f"{len(unprobed_names)} UNPROBED, {len(unknown_names)} UNKNOWN. "
              "NOT a clean bill of health."
              if verdict != "healthy" else
              f"{probed_total}/{scope} measurements probed and healthy.")
    report: dict = {
        "schema": SCHEMA,
        "generated_at": opslib.now_iso(),
        "verdict": verdict,
        "banner": banner,
        "probed": {"healthy": healthy, "unhealthy": unhealthy},
        "unprobed": {"count": len(unprobed_names), "names": unprobed_names},
        "unknown": {"count": len(unknown_names), "names": unknown_names},
        "measurements": [m.as_dict() for m in ms],
    }
    if extra:
        report.update(extra)
    return report


def write_report(report: dict, path: Path | None = None) -> tuple[Path, str]:
    """نوشتنِ اتمیکِ تنها خروجی مجازِ این ماژول (tmp + replace + sha)."""
    p = path or REPORT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    body = json.dumps(report, ensure_ascii=False, indent=2)
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, p)
    return p, hashlib.sha256(body.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    report = build_report()
    # دلتای ارسال برای گزارش بعدی را همان‌جا می‌گذاریم (خوانده‌شده در خانوادهٔ ۵)
    try:
        effects = [m for m in report["measurements"]
                   if m.get("name") == "effects.outbound"]
        if effects and isinstance(effects[0].get("value"), dict):
            prev = effects[0]["value"].get("counts", {}).get("sent")
            if isinstance(prev, int):
                report["effects_prev_sent"] = prev
    except (KeyError, AttributeError):
        pass
    print(json.dumps(report, ensure_ascii=False))
    if argv and argv[0] and argv[0] != "-":
        try:
            write_report(report, Path(argv[0]))
        except OSError:
            print(json.dumps({"report_write": "failed-soft"},
                             ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
