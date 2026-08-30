#!/usr/bin/env python3
"""
live_state_guard.py — تریپ‌وایرِ نوشتن روی state ِ **زنده**.

مسئله‌ای که می‌بندد (اندازه‌گیری‌شدهٔ ۲۰۲۶-۰۸-۰۳): فیکسچرها داخلِ ظرف‌های زنده
می‌نویسند. `state/legs/lead-send-counter.json` امروز `sent=5` بود — یعنی نصفِ
سقفِ واقعیِ ارسالِ روزانه را تست سوزانده. `state/approval-log.jsonl` هر ۲۰ ردیفش
`action_id='test-001'` است. تا این بسته نشود **هیچ سنجهٔ پذیرشی معتبر نیست**،
چون هر نسبتی که از این ظرف‌ها حساب شود در جهتِ خوش‌بینانه غلط است.

چرا فقط `harness.setup()` کافی نبود: هارنس envها را ست می‌کند، ولی
`opslib.STATE_DIR` در **زمانِ import** بسته می‌شود. تستی که (مستقیم یا از راهِ یک
ماژولِ دیگر) قبل از `setup()` ماژولی را import کند، به درختِ زنده می‌افتد — بی‌صدا.
این گارد به‌جای ست‌کردنِ مسیر، **خودِ نوشتن** را می‌گیرد: مستقل از اینکه مسیر
چطور resolve شد.

قرارداد:
  · خواندنِ state ِ زنده **آزاد** است (خیلی تست‌ها عمداً واقعیت را می‌خوانند).
  · نوشتن/حذف/تغییرِ نام زیرِ `<REAL_VAULT>/_ops/state` استثنا می‌دهد.
  · state ِ خودِ worktree هرگز مسدود نیست (زیرِ آن مسیر نیست).
  · استثنای مجاز فقط **اعلام‌شده**: `with live_state_guard.allow_live_write("چرا")`.

مصرف:
    import live_state_guard; live_state_guard.arm()
یا خودکار برای هر تست (بی‌ویرایشِ فایلِ تست) از راهِ `_isolation_boot/sitecustomize.py`.
"""
from __future__ import annotations

import builtins
import contextlib
import io
import os
import sqlite3
import sys
from pathlib import Path

# ── دامنه ─────────────────────────────────────────────────────────────────────
# هم‌ریشهٔ `harness.REAL_VAULT` — درختِ زنده، نه worktree. لیترالِ F:\backup عیناً
# پیش‌فرضِ `opslib.ORG_ROOT` است؛ اگر یکی عوض شد آن یکی هم باید عوض شود.
REAL_VAULT_DEFAULT = r"F:\backup"


class LiveStateWriteError(RuntimeError):
    """تست خواست داخلِ state ِ زنده بنویسد. این باگِ تست است، نه باگِ گارد."""


_armed = False
_mode = "block"                 # block | report
_roots: tuple[str, ...] = ()
_violations: list[dict] = []
_allow_depth = 0
_allow_reasons: list[str] = []
_orig: dict = {}


def _norm(p) -> str | None:
    """resolve **قبل از** قضاوت — گاردِ زیررشته‌ای با یک `..` دور می‌خورد.
    ورودیِ غیرمسیری (fd ِ عددی) → None یعنی «قضاوت نکن»."""
    if isinstance(p, int):
        return None
    try:
        s = os.fspath(p)
    except TypeError:
        return None
    if not isinstance(s, str):
        try:
            s = s.decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            return None
    if not s:
        return None
    try:
        return os.path.normcase(os.path.abspath(s))
    except (OSError, ValueError):
        return None


def live_state_roots() -> tuple[str, ...]:
    vault = os.environ.get("REAL_VAULT") or REAL_VAULT_DEFAULT
    # agi2027_runtime هم اضافه شد (۲۰۲۶-۰۸-۰۳، VQ-WAL-RUNTIME-001): همان کلاسِ خطر —
    # مسیری که با `_HERE.parent` حساب می‌شود و اگر تستی هنوز از REAL_VAULT import کند
    # (دفاعِ لایه‌دومی، لایهٔ اول = knob ِ harness.setup) به کنترل‌پلینِ tracked ِ زنده می‌رسد.
    return tuple(os.path.normcase(os.path.abspath(os.path.join(vault, "_ops", sub)))
                 for sub in ("state", "agi2027_runtime"))


def _inside(path) -> str | None:
    """مسیرِ نرمال‌شده اگر زیرِ یکی از ریشه‌های زنده باشد، وگرنه None.
    مقایسه با جداکنندهٔ انتهایی تا `..._statex` با `..._state` اشتباه نشود."""
    n = _norm(path)
    if n is None:
        return None
    for r in _roots:
        if n == r or n.startswith(r + os.sep):
            return n
    return None


def _emit(rec: dict) -> None:
    """ثبتِ بیرونی — تستی که پروسهٔ فرزند می‌سازد هم دیده شود (فرزند env را ارث می‌برد).
    نوشتنِ لحظه‌ای نه atexit: تستی که `os._exit` بزند وگرنه بی‌ردّ می‌رود.
    از `open` ِ **اصلی** استفاده می‌کند تا در wrapper بازگشتی نیفتد."""
    p = os.environ.get("OCTOPUS_TEST_ISOLATION_LOG")
    if not p:
        return
    import json
    opener = _orig.get("builtins.open", (None, None, open))[2]
    try:
        with opener(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({**rec, "pid": os.getpid(),
                                "argv": " ".join(sys.argv[:3])}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _benign(op: str, path: str) -> bool:
    """آیا این عملیات **صفر بایت** عوض می‌کند؟

    سنجهٔ پذیرشِ برشِ ۰ «صفر بایتِ تغییر» است، نه «صفر تلاش». `mkdir(exist_ok=True)`
    روی پوشه‌ای که هست، و `unlink(missing_ok=True)` روی فایلی که نیست، هیچ‌چیز عوض
    نمی‌کنند. این‌ها **مسدود نمی‌شوند** ولی ثبت می‌شوند: نشانهٔ اینکه ماژول مسیرش را
    به درختِ زنده resolve کرده — یعنی نوشتنِ بعدی زنده می‌افتد. هشدار است، نه جهش.
    (درسِ `power.resume_leg`: `ok=true` یعنی «استثنا نداد»، نه «جهان عوض شد».)"""
    try:
        if op in ("os.mkdir", "os.makedirs"):
            return os.path.isdir(path)
        if op in ("os.remove", "os.unlink", "os.rmdir", "os.truncate"):
            return not os.path.exists(path)
    except OSError:
        return False
    return False


def _trip(op: str, path: str, detail: str = "") -> None:
    benign = _benign(op, path)
    rec = {"op": op, "path": path, "detail": detail, "benign": benign,
           "allowed": _allow_depth > 0,
           "reason": _allow_reasons[-1] if _allow_reasons else ""}
    _violations.append(rec)
    _emit(rec)
    if benign or _allow_depth > 0 or _mode == "report":
        return
    raise LiveStateWriteError(
        f"نوشتن روی state ِ زنده مسدود شد: {op} → {path}\n"
        f"  این تست ظرفِ واقعیِ ارگانیسم را عوض می‌کند. رفع: قبل از هر import ِ دیگری\n"
        f"  `import harness; ENV = harness.setup(\"<نام>\")` — یا اگر واقعاً لازم است،\n"
        f"  صریح اعلامش کن: `with live_state_guard.allow_live_write(\"چرا\"): ...`"
    )


# ── بردارهای نوشتن ────────────────────────────────────────────────────────────
_WRITE_FLAGS = (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC)


def _mode_writes(mode: str) -> bool:
    return any(ch in mode for ch in ("w", "a", "x", "+"))


def _wrap_open(orig):
    def guarded(file, mode="r", *a, **kw):
        if _armed and _mode_writes(str(mode)):
            hit = _inside(file)
            if hit:
                _trip("open", hit, f"mode={mode!r}")
        return orig(file, mode, *a, **kw)
    return guarded


def _wrap_os_open(orig):
    def guarded(path, flags, *a, **kw):
        if _armed and (flags & _WRITE_FLAGS):
            hit = _inside(path)
            if hit:
                _trip("os.open", hit, f"flags={flags:#o}")
        return orig(path, flags, *a, **kw)
    return guarded


def _wrap_two_path(orig, name):
    """os.replace / os.rename — هر دو سر مهم‌اند: مقصدِ زنده = نوشتن،
    مبدأِ زنده = برداشتنِ فایلِ زنده."""
    def guarded(src, dst, *a, **kw):
        if _armed:
            for label, p in (("src", src), ("dst", dst)):
                hit = _inside(p)
                if hit:
                    _trip(name, hit, label)
        return orig(src, dst, *a, **kw)
    return guarded


def _wrap_one_path(orig, name):
    def guarded(path, *a, **kw):
        if _armed:
            hit = _inside(path)
            if hit:
                _trip(name, hit)
        return orig(path, *a, **kw)
    return guarded


def _wrap_sqlite_connect(orig):
    def guarded(database, *a, **kw):
        if _armed:
            db = database
            ro = False
            if isinstance(db, str):
                if db == ":memory:" or db.startswith("file::memory:"):
                    return orig(database, *a, **kw)
                if kw.get("uri") and db.startswith("file:"):
                    # `mode=ro` یعنی اتصالِ فقط‌خواندنی — همان چیزی که پروبها لازم دارند.
                    q = db.split("?", 1)[1] if "?" in db else ""
                    ro = "mode=ro" in q
                    db = db.split("?", 1)[0][len("file:"):]
            hit = _inside(db)
            if hit and not ro:
                _trip("sqlite3.connect", hit, "اتصالِ نوشتنی")
        return orig(database, *a, **kw)
    return guarded


# نام → (ماژول، سازندهٔ wrapper). ترتیب اهمیتی ندارد؛ هر کدام مستقل جهش‌آزموده است.
_TARGETS = (
    ("builtins.open",     builtins, "open",     _wrap_open),
    ("io.open",           io,       "open",     _wrap_open),
    ("os.open",           os,       "open",     _wrap_os_open),
    ("os.replace",        os,       "replace",  lambda o: _wrap_two_path(o, "os.replace")),
    ("os.rename",         os,       "rename",   lambda o: _wrap_two_path(o, "os.rename")),
    ("os.remove",         os,       "remove",   lambda o: _wrap_one_path(o, "os.remove")),
    ("os.unlink",         os,       "unlink",   lambda o: _wrap_one_path(o, "os.unlink")),
    ("os.rmdir",          os,       "rmdir",    lambda o: _wrap_one_path(o, "os.rmdir")),
    ("os.mkdir",          os,       "mkdir",    lambda o: _wrap_one_path(o, "os.mkdir")),
    ("os.makedirs",       os,       "makedirs", lambda o: _wrap_one_path(o, "os.makedirs")),
    ("os.truncate",       os,       "truncate", lambda o: _wrap_one_path(o, "os.truncate")),
    ("sqlite3.connect",   sqlite3,  "connect",  _wrap_sqlite_connect),
)


def arm(mode: str = None) -> tuple[str, ...]:
    """مسلح‌کردن. idempotent — دوبار صدا زدن wrapper روی wrapper نمی‌گذارد."""
    global _armed, _mode, _roots
    if mode is None:
        env = (os.environ.get("OCTOPUS_TEST_LIVE_STATE_GUARD") or "").strip().lower()
        mode = "report" if env == "report" else "block"
    _mode = mode
    _roots = live_state_roots()
    if _armed:
        return _roots
    for name, mod, attr, wrap in _TARGETS:
        orig = getattr(mod, attr)
        _orig[name] = (mod, attr, orig)
        setattr(mod, attr, wrap(orig))
    _armed = True
    return _roots


def disarm() -> None:
    global _armed
    for _name, (mod, attr, orig) in _orig.items():
        setattr(mod, attr, orig)
    _orig.clear()
    _armed = False


@contextlib.contextmanager
def allow_live_write(reason: str):
    """استثنای **اعلام‌شده**. هر عبور در `violations()` با دلیلش ثبت می‌شود،
    پس «هیچ‌کس نمی‌نویسد» و «یکی با اجازه می‌نویسد» دو چیزِ متفاوت می‌مانند."""
    global _allow_depth
    if not reason or not str(reason).strip():
        raise ValueError("allow_live_write بی‌دلیل مجاز نیست")
    _allow_depth += 1
    _allow_reasons.append(str(reason))
    try:
        yield
    finally:
        _allow_depth -= 1
        _allow_reasons.pop()


def violations(include_allowed: bool = False, include_benign: bool = False) -> list[dict]:
    """پیش‌فرض: فقط جهش‌های واقعیِ مسدودشده. `include_benign=True` نشتیِ اشاره‌ای
    (مسیرِ زنده resolve شد ولی صفر بایت عوض می‌شد) را هم برمی‌گرداند."""
    return [v for v in _violations
            if (include_allowed or not v["allowed"])
            and (include_benign or not v.get("benign"))]


def reset() -> None:
    _violations.clear()


def is_armed() -> bool:
    return _armed


# ── تریپ‌وایرِ دوم: شبکهٔ بیرونی ──────────────────────────────────────────────
# چرا لازم شد: برای سنجشِ «سوییت کجا می‌نویسد» باید سوییت را دواند، ولی بعضی تست‌ها
# مسیرِ vendor ِ **پولی** را می‌زنند (ممیزیِ ۰۷-۲۷: تماسِ مستقیمِ client.complete که
# نه breaker می‌بیندش نه شمارندهٔ سهمیه). خرجِ پول گیتِ مالک دارد؛ پس خودِ ابزارِ
# اندازه‌گیری حق ندارد آن را ناخواسته تولید کند. loopback باز می‌ماند چون چند تست
# عمداً سرورِ محلی بالا می‌آورند.

class ExternalNetworkError(RuntimeError):
    """تست خواست به میزبانِ غیرِ loopback وصل شود."""


_net_armed = False
_net_hits: list[dict] = []
_LOOPBACK_NAMES = {"localhost", "localhost.localdomain", "ip6-localhost", ""}


def _is_loopback(addr) -> bool:
    host = addr[0] if isinstance(addr, (tuple, list)) and addr else addr
    if not isinstance(host, str):
        return False
    h = host.strip("[]").lower()
    if h in _LOOPBACK_NAMES or h == "::1":
        return True
    return h.startswith("127.")


def _check_addr(name: str, address) -> None:
    if not _net_armed or _is_loopback(address):
        return
    _net_hits.append({"op": name, "addr": str(address), "pid": os.getpid()})
    _emit({"op": f"net:{name}", "path": str(address), "detail": "خروجیِ غیرِ loopback",
           "benign": False, "allowed": False, "reason": ""})
    raise ExternalNetworkError(
        f"اتصالِ بیرونی مسدود شد: {name} → {address}\n"
        f"  اجرای اندازه‌گیری حق ندارد اثرِ بیرونی/هزینهٔ واقعی بسازد."
    )


# ⚠️ متد و تابع **جای آرگومانِ متفاوت** دارند و یک wrapper ِ مشترک برای هر دو غلط است:
# `sock.connect(addr)` آدرس را در arg ِ اول بعد از self دارد، ولی
# `create_connection(addr, timeout)` آن را در arg ِ اولِ خودش. نسخهٔ اولِ این گارد
# «اگر a تهی نبود a[0]» را برمی‌داشت، پس وقتی timeout **موضعی** پاس می‌شد عددِ timeout
# را آدرس می‌خواند: هم گزارش را بی‌معنا می‌کرد، هم یک اتصالِ loopback ِ مجاز را رد
# می‌کرد (`test_lead_boundary_http` که سرورِ محلی بالا می‌آورد قرمز شد؛ ۹ از ۱۰
# «تماسِ بیرونی» ِ گزارش‌شده مثبتِ کاذب بودند).
def _wrap_sock_method(orig, name):
    def guarded(self, address, *a, **kw):
        fam = getattr(self, "family", None)
        af_unix = getattr(_socket_mod, "AF_UNIX", None)
        if af_unix is not None and fam == af_unix:
            return orig(self, address, *a, **kw)      # سوکتِ محلیِ فایل‌محور
        _check_addr(name, address)
        return orig(self, address, *a, **kw)
    return guarded


def _wrap_create_connection(orig):
    def guarded(address, *a, **kw):
        _check_addr("create_connection", address)
        return orig(address, *a, **kw)
    return guarded


_socket_mod = None


def arm_network() -> None:
    """فقط loopback مجاز. صداکننده: runner ِ ایزوله — نه harness ِ عمومی."""
    global _net_armed, _socket_mod
    if _net_armed:
        return
    import socket
    _socket_mod = socket
    _orig["socket.connect"] = (socket.socket, "connect", socket.socket.connect)
    _orig["socket.connect_ex"] = (socket.socket, "connect_ex", socket.socket.connect_ex)
    _orig["socket.create_connection"] = (socket, "create_connection", socket.create_connection)
    socket.socket.connect = _wrap_sock_method(socket.socket.connect, "connect")
    socket.socket.connect_ex = _wrap_sock_method(socket.socket.connect_ex, "connect_ex")
    socket.create_connection = _wrap_create_connection(socket.create_connection)
    _net_armed = True


def network_hits() -> list[dict]:
    return list(_net_hits)


if __name__ == "__main__":                                    # پروبِ دستی
    roots = arm("report")
    print("ریشه‌های محافظت‌شده:", roots)
    probe = Path(roots[0]) / "legs" / "lead-send-counter.json"
    print("مسیرِ نمونه زیرِ ریشه؟", _inside(probe) is not None)
    print("state ِ همین worktree زیرِ ریشه؟",
          _inside(Path(__file__).resolve().parent.parent / "state") is not None)
    sys.exit(0)
