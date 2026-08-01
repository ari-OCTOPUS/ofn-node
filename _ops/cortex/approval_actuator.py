#!/usr/bin/env python3
"""approval_actuator.py — «اکچوایتورِ تصمیم‌های تأییدشده» (رفعِ گاف #۱ دبل‌چک).

بیماریِ ثبت‌شده (دبل‌چک G1/A2-1/G1b): مالک ✅ می‌زند، center روی
`state/telegram/approvals/<id>.json` می‌نویسد، ولی هیچ actuatorی مصرفش نمی‌کند (جز
code_autonomy فقط برای `code-*`). نتیجه: تصمیمِ تأییدشده از جعبهٔ راهنمایی می‌افتد
ولی هیچ اکشنی نمی‌شود → «حل‌شدنِ کاذبِ نامرئی».

این ماژول = seamِ اکچوایشن + صداقتِ نمایشی:
  • رجیستریِ handler (prefixِ id → تابع)؛ خالی به‌طورِ پیش‌فرض — هیچ اکشنی خودکار نیست.
  • هر approvalِ `ok`ِ تازه که handler ندارد → «acknowledged» علامت می‌خورد و در
    شمارشِ «تأییدشده ولی بی‌اکشن» می‌آید (دیگر بی‌صدا گم نمی‌شود).
  • خروجی = یک رویدادِ **system.heartbeat** (نه decision) → با guidance هیچ حلقه‌ای
    نمی‌سازد (guidance فقط approval.required/task.blocked/fear/needs را برمی‌دارد).
  • idempotent: markerِ actuated/acknowledged در state → هر id فقط یک‌بار پردازش.

مرزِ سخت: هرگز پول، هرگز اکشنِ بیرونی، هرگز خودکار. handlerها را فقط کدِ صریحِ owner-gated
ثبت می‌کند؛ خودِ این ماژول هیچ handlerِ پیش‌فرضی ندارد. پشتِ OCTOPUS_WIRE_ACTUATOR
در حلقهٔ ارگانیسم (پیش‌فرض خاموش، خارج از paper-full — چون approvalها شاملِ پول‌اند).

$0 · stdlib + opslib · fail-soft · content-free (scrub containment).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
APPROVALS = STATE / "telegram" / "approvals"
MARKS = STATE / "cortex" / "actuation-marks.json"     # {did: {status, ts}}
OUT = STATE / "cortex" / "actuation-latest.json"

# رأیِ نهایی که «اکشن می‌خواهد» = ok (no = ردشده، later = معطل — هیچ‌کدام اکچوایت نمی‌شوند)
_ACTIONABLE = "ok"
RECENT_DAYS = 7.0     # approvalهای کهنه‌تر نادیده (backlogِ باستانی سروصدا نکند)

# containment (parity با registry_scan.scrub) — هیچ رشتهٔ ممنوع echo نمی‌شود
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")

# رجیستریِ handler: prefixِ id → تابعِ fn(approval_rec)->dict. خالی = هیچ اکشنِ خودکار.
# فقط کدِ صریح (owner-gated) اینجا ثبت می‌کند؛ این ماژول هیچ پیش‌فرضی نمی‌گذارد.
HANDLERS: dict = {}


def register(prefix: str, fn) -> None:
    """یک handler برای idهایی که با prefix شروع می‌شوند ثبت کن (مثلاً 'lead-')."""
    if prefix and callable(fn):
        HANDLERS[str(prefix)] = fn


def _scrub(s: object, cap: int = 160) -> str:
    v = str(s if s is not None else "")[:cap]
    low = v.lower()
    return "(redacted:containment)" if any(b in low or b in v for b in _BANNED_ECHO) else v


def _read_json(p: Path) -> dict:
    try:
        d = json.loads(p.read_text("utf-8")) if p.exists() else {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_json(p: Path, data: dict) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(p) as lj:
            lj.write(data)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"approval_actuator persist failed: {type(e).__name__}: {e}"])


def _age_days(ts_iso) -> float:
    """سنِ یک approval بر حسبِ روز. ناخوانا → 0 (fail-open: تازه فرض کن تا دیده شود).

    ۲۰۲۶-۰۸-۰۱ — مرکز هر دو شکل را می‌نویسد: `...T09:11:02` (بی‌منطقه) و
    `...T09:28:48+1000` (با منطقه). کسرِ awareِ منطقه‌دار از naive در پایتون
    TypeError است و همین‌جا بلعیده می‌شد → **هر** رکوردِ منطقه‌دار سنِ ۰ می‌گرفت،
    یعنی پنجرهٔ RECENT_DAYS برای بیشترِ رکوردهای واقعی مرده بود (۳۲ از ۴۳ فایلِ
    زندهٔ امروز منطقه‌دارند — شمارشِ راستی‌آزمایی‌شده). درست: aware را به وقتِ
    محلی ببر و tzinfo را بردار.
    """
    try:
        import datetime as _dt
        t = _dt.datetime.fromisoformat(str(ts_iso))
        if t.tzinfo is not None:
            t = t.astimezone().replace(tzinfo=None)
        return max(0.0, (_dt.datetime.now() - t).total_seconds() / 86400.0)
    except Exception:  # noqa: BLE001
        return 0.0


def _approvals() -> list:
    """(did, rec) هر فایلِ approvalِ ok/no/later. fail-soft: پوشهٔ غایب → []."""
    out = []
    try:
        for p in sorted(APPROVALS.glob("*.json")):
            if p.name == "approvals.jsonl":
                continue
            rec = _read_json(p)
            did = str(rec.get("id") or p.stem)
            if did:
                out.append((did, rec))
    except OSError:
        pass
    return out


def _handler_for(did: str):
    """handlerِ منطبق با بلندترین prefix (خاص‌ترین برنده)، وگرنه None."""
    best = None
    for pref, fn in HANDLERS.items():
        if did.startswith(pref) and (best is None or len(pref) > len(best[0])):
            best = (pref, fn)
    return best[1] if best else None


def scan() -> dict:
    """فقط‌خواندنی: دسته‌بندیِ approvalهای فعلی — بدونِ نوشتن، بدونِ اکشن."""
    marks = _read_json(MARKS)
    actuated, acknowledged, rejected, later = [], [], [], []
    for did, rec in _approvals():
        verdict = str(rec.get("verdict") or "")
        if verdict == "no":
            rejected.append(did)
        elif verdict == "later":
            later.append(did)
        elif verdict == _ACTIONABLE:
            if _age_days(rec.get("ts")) > RECENT_DAYS:
                continue                      # کهنهٔ باستانی → در شمارشِ «بی‌اکشن» نیاید
            st = (marks.get(did) or {}).get("status")
            if st == "actuated":
                actuated.append(did)
            elif _handler_for(did) is not None:
                actuated.append(did)          # handler دارد (در run اجرا می‌شود)
            else:
                acknowledged.append(did)      # ok ولی بی‌اکشن — دستی پیگیری
    return {"actuated": actuated, "acknowledged": acknowledged,
            "rejected": rejected, "later": later,
            "n_unactuated": len(acknowledged)}


def run(dry_run: bool = False) -> dict:
    """اکچوایتور را بچرخان. برای هر approvalِ ok که هنوز پردازش نشده:
      • handler دارد → صدایش بزن (اگر dry_run نه) → markِ actuated.
      • handler ندارد → markِ acknowledged (یک‌بار) → در شمارشِ «بی‌اکشن».
    خروجیِ visibility = یک system.heartbeat (نه decision → بی‌حلقه با guidance).
    propose-only مطلق: هیچ پولی، هیچ اکشنِ بیرونی/خودکار. idempotent (marker)."""
    marks = _read_json(MARKS)
    new_ack, new_act, errors = [], [], 0
    for did, rec in _approvals():
        if str(rec.get("verdict") or "") != _ACTIONABLE:
            continue
        if did in marks:                       # قبلاً پردازش‌شده → idempotent
            continue
        if _age_days(rec.get("ts")) > RECENT_DAYS:
            continue                            # کهنهٔ باستانی → نادیده (بی‌سروصدا)
        fn = _handler_for(did)
        if fn is not None:
            status = "actuated"
            if not dry_run:
                try:
                    fn(dict(rec))               # handlerِ owner-gated؛ خودش مسئولِ گیت‌هاست
                except Exception:  # noqa: BLE001 — یک handler خراب بقیه را نمی‌کشد
                    errors += 1
                    status = "handler-error"
            marks[did] = {"status": status, "ts": opslib.now_iso()}
            if status == "actuated":
                new_act.append(did)
        else:
            marks[did] = {"status": "acknowledged", "ts": opslib.now_iso()}
            new_ack.append(did)

    if not dry_run and (new_ack or new_act):
        _write_json(MARKS, marks)

    s = scan()
    digest = {"ts": opslib.now_iso(), "schema": "actuation.v1",
              "n_unactuated": s["n_unactuated"], "n_actuated": len(s["actuated"]),
              "handlers": sorted(HANDLERS.keys()),
              "new_acknowledged": len(new_ack), "new_actuated": len(new_act),
              "errors": errors}
    if not dry_run:
        _write_json(OUT, digest)
        # صداقتِ نمایشی: فقط وقتی چیزِ نوی بی‌اکشن پیدا شد یک heartbeat بزن (بی‌اسپم،
        # بی‌حلقه — heartbeat در guidance به decision تبدیل نمی‌شود).
        if new_ack:
            try:
                if str(_HERE.parent) not in sys.path:
                    sys.path.insert(0, str(_HERE.parent))
                import events
                events.emit("system.heartbeat", "approval-actuator",
                            summary=_scrub(f"🔧 {len(new_ack)} تصمیمِ تأییدشده بدونِ اکشن — "
                                           f"جمعاً {s['n_unactuated']} منتظرِ پیگیریِ دستی"),
                            next_action="دستی انجام بده یا handler ثبت کن",
                            status="warn")
            except Exception:  # noqa: BLE001
                pass
    return digest


def summary() -> dict:
    """یک‌خطِ داشبورد: «🔧 اکچوایتور: N تصمیمِ تأییدشده بی‌اکشن»."""
    d = _read_json(OUT)
    n = int(d.get("n_unactuated") or 0)
    line = (f"🔧 اکچوایتور: {n} تصمیمِ تأییدشده بی‌اکشن (دستی)" if n
            else "🔧 اکچوایتور: هر تصمیمِ تأییدشده اکشن گرفت — 🟢")
    return {"n_unactuated": n, "n_actuated": int(d.get("n_actuated") or 0),
            "handlers": d.get("handlers") or [], "line": line}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
