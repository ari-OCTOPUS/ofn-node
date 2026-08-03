#!/usr/bin/env python3
"""token_meter.py — سنجهٔ مصرفِ توکن روی پنجرهٔ **غلتان**، و سهمِ درصدیِ مالک.

مسئله‌ای که می‌بندد (ممیزیِ ۲۰۲۶-۰۸-۰۳، بندهای (a) و (d)):

    هیچ متری در کلِ ریپو توکن را به‌عنوانِ **بودجه** نمی‌شمارد.
      · `fugu_quota` درخواست می‌شمارد (attempt-counted) — نه توکن.
      · `subscription: "max"` باعث می‌شود `client.est_worst_case` و
        `client.complete` هر دو صفر بدهند، پس `organ_gate`/`budget_gate` صفر
        جمع می‌زنند. شاهدِ زنده: بعد از ۳۹۵ فراخوانِ primary،
        `organ-state.json` روی `spent_month_musd: 0` است. سقفِ AUD ساختاراً
        دست‌نیافتنی است.
      · تنها جایی که توکنِ واقعی **و** مهرِ زمانی دارد `paid-calls.jsonl` است،
        و **صفر خوانندهٔ تجمیعی** دارد.
      · و هر پنجرهٔ مصرف در ریپو تقویمی است (`date.today()`)، در حالی که سهمیهٔ
        فروشنده غلتان است — پس حتی اگر عددی بود، پنجره‌اش غلط بود.

این ماژول فقط **می‌خواند**. صفر نوشتن، صفر شبکه، stdlib خالص.

مرزِ صداقتِ این ماژول (مهم‌تر از خودِ اعداد)
──────────────────────────────────────────
۱. **ظرفیت را نمی‌سنجد، اعلام می‌کند.** ظرفیتِ واقعیِ پلن قابلِ مشاهده نیست مگر
   با خوردن به سقف. پس `CAPACITY_ENV` یک **تخمینِ اعلام‌شده** است و خروجی همیشه
   `capacity_verified: False` را حمل می‌کند تا هیچ مصرف‌کننده‌ای آن را با
   واقعیت اشتباه نگیرد.
۲. **مصرفِ نامرئی تخمین است، نه مشاهده.** فروشنده توکنِ استدلالِ داخلی را
   برنمی‌گرداند. ضریب (`MULTIPLIER_ENV`) از تحقیقِ مالک می‌آید، و خروجی هم
   `visible` ِ خام و هم `effective` ِ ضریب‌خورده را جدا می‌دهد — تا اگر ضریب
   غلط بود، عددِ خام دست‌نخورده بماند. شاهدِ غیرمستقیمِ درون‌داده:
   `tokens_out=1200` با `chars_out=93`.
۳. **رأیِ مالک درصد است نه عددِ مطلق** (`owner-verdicts.yaml::fugu_weekly_share`):
   «اگر مصرفِ واقعی نشان داد تخمینم غلط بوده، ۴۰٪ روی ظرفیتِ *واقعی* اعمال
   می‌شود». پس این ماژول همیشه از درصد × ظرفیتِ **جاری** حساب می‌کند؛ عوض‌کردنِ
   تخمینِ ظرفیت خودبه‌خود بودجه را اصلاح می‌کند.

مصرف:
    python _ops/token_meter.py            # خلاصهٔ انسانی
    python _ops/token_meter.py --json     # ماشین‌خوان
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCHEMA = "token-meter.v1"

#: تنها منبعِ توکنِ واقعی در کلِ ریپو. append-only، هر ردیف یک `ts`.
LOG_REL = "state/paid-calls.jsonl"

#: پنجرهٔ غلتان — سهمیهٔ فروشنده غلتان است، نه تقویمی.
WINDOW_H = 24 * 7

#: ضریبِ مصرفِ نامرئی. تحقیقِ مالک ۰۸-۰۳: ~۶۰٪ نامرئی ⇒ ×۲.۶ روی مرئی.
MULTIPLIER_ENV = "OCTOPUS_FUGU_INVISIBLE_MULT"
DEFAULT_MULTIPLIER = 2.6

#: تخمینِ ظرفیتِ هفتگی (توکن). اعلام‌شده، نه سنجیده — بند ۱ بالا.
CAPACITY_ENV = "OCTOPUS_FUGU_WEEKLY_CAPACITY"
DEFAULT_CAPACITY = 180_000_000

#: سهمِ مالک از ظرفیت. رأیِ tracked در owner-verdicts.yaml.
SHARE_ENV = "OCTOPUS_FUGU_WEEKLY_SHARE_PCT"
DEFAULT_SHARE_PCT = 40.0

#: نگاشتِ task → پا. `task` از ۲۰۲۶-۰۸-۰۴ در paid-calls.jsonl ثبت می‌شود؛
#: ردیف‌های قدیمی‌تر آن را ندارند و صادقانه `unattributed` می‌شوند.
LEG_BY_TASK = {
    "ziman": "ziman",
    "draft": "ziman",
    "lead": "lead",
    "classify": "lead",
    "triage": "lead",
    "studio": "studio",
    "research": "studio",
    "synthesize": "studio",
}
LEG_SHARE_PCT = {"ziman": 40.0, "lead": 40.0, "studio": 20.0}


def _f(env: str, default: float) -> float:
    try:
        v = str(os.environ.get(env, "") or "").strip()
        return float(v) if v else float(default)
    except (TypeError, ValueError):
        return float(default)


def multiplier() -> float:
    return max(1.0, _f(MULTIPLIER_ENV, DEFAULT_MULTIPLIER))


def capacity() -> float:
    return max(0.0, _f(CAPACITY_ENV, DEFAULT_CAPACITY))


def share_pct() -> float:
    """درصدِ مالک — اول env، بعد رأیِ tracked، بعد پیش‌فرض."""
    raw = str(os.environ.get(SHARE_ENV, "") or "").strip()
    if raw:
        try:
            return max(0.0, min(100.0, float(raw)))
        except ValueError:
            pass
    try:
        import owner_verdicts as _ov          # noqa: PLC0415
        spec = (_ov.load() or {}).get("fugu_weekly_share") or {}
        return max(0.0, min(100.0, float(spec.get("value"))))
    except Exception:  # noqa: BLE001 — نبودِ رأی = پیش‌فرض، نه استثنا
        return DEFAULT_SHARE_PCT


def log_path(state_dir=None) -> Path:
    if state_dir is not None:
        return Path(state_dir) / "paid-calls.jsonl"
    try:
        import opslib                          # noqa: PLC0415
        return Path(opslib.STATE_DIR) / "paid-calls.jsonl"
    except Exception:  # noqa: BLE001
        return _HERE / LOG_REL


def _parse_ts(raw) -> "datetime | None":
    """`opslib.now_iso()` **محلی** می‌نویسد و بی‌منطقه است. خواندنش به‌عنوانِ UTC
    همان باگِ ثبت‌شدهٔ «UTC در نویسنده، محلی در خواننده» است که یک‌بار ده ساعت
    از هر روز را کور کرد. پس بی‌منطقه = محلی، و بعد به UTC تبدیل می‌شود."""
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt.astimezone(timezone.utc)


def read_window(window_h: float = WINDOW_H, now=None, state_dir=None) -> dict:
    """مصرفِ پنجرهٔ غلتان. هرگز استثنا — منبعِ ناخوانا ⇒ `readable: False`.

    تفکیکِ عمدی: `readable=False` (نمی‌دانیم) با `calls=0` (می‌دانیم هیچ) یکی
    نیست. یک ذخیرهٔ غایب نباید شبیهِ «مصرفِ صفر» رندر شود.
    """
    p = log_path(state_dir)
    out = {"schema": SCHEMA, "readable": False, "calls": 0, "failed": 0,
           "visible_in": 0, "visible_out": 0, "visible_total": 0,
           "by_leg": {}, "unattributed_calls": 0, "window_h": float(window_h),
           "oldest_ts": None, "newest_ts": None, "path": str(p)}
    if not p.exists():
        return out
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.astimezone(timezone.utc)
    cutoff = now_dt - timedelta(hours=float(window_h))
    try:
        raw = p.read_text("utf-8", errors="replace")
    except OSError:
        return out
    out["readable"] = True
    by_leg: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue                      # یک ردیفِ پاره کلِ متر را نمی‌کُشد
        ts = _parse_ts(r.get("ts"))
        if ts is None or ts < cutoff:
            continue
        if out["oldest_ts"] is None or ts < out["oldest_ts"]:
            out["oldest_ts"] = ts
        if out["newest_ts"] is None or ts > out["newest_ts"]:
            out["newest_ts"] = ts
        out["calls"] += 1
        if not r.get("ok", True):
            out["failed"] += 1
            continue                      # شکست توکن نسوزانده
        ti = int(r.get("tokens_in") or 0)
        to = int(r.get("tokens_out") or 0)
        out["visible_in"] += ti
        out["visible_out"] += to
        leg = LEG_BY_TASK.get(str(r.get("task") or "").strip().lower())
        if leg is None:
            out["unattributed_calls"] += 1
            leg = "unattributed"
        b = by_leg.setdefault(leg, {"calls": 0, "visible": 0})
        b["calls"] += 1
        b["visible"] += ti + to
    out["visible_total"] = out["visible_in"] + out["visible_out"]
    out["by_leg"] = by_leg
    for k in ("oldest_ts", "newest_ts"):
        if out[k] is not None:
            out[k] = out[k].isoformat()
    return out


def status(window_h: float = WINDOW_H, now=None, state_dir=None) -> dict:
    """وضعِ کامل: مصرف، بودجه، سرِ باقی‌مانده — با هر تخمین صریحاً برچسب‌خورده."""
    w = read_window(window_h, now=now, state_dir=state_dir)
    mult, cap, pct = multiplier(), capacity(), share_pct()
    effective = int(round(w["visible_total"] * mult))
    budget = int(round(cap * pct / 100.0))
    used_pct = (100.0 * effective / budget) if budget > 0 else None
    legs = {}
    for leg, lp in LEG_SHARE_PCT.items():
        lb = int(round(budget * lp / 100.0))
        lv = int((w["by_leg"].get(leg) or {}).get("visible") or 0)
        le = int(round(lv * mult))
        legs[leg] = {"budget_tokens": lb, "effective_tokens": le,
                     "used_pct": (100.0 * le / lb) if lb > 0 else None,
                     "calls": int((w["by_leg"].get(leg) or {}).get("calls") or 0)}
    return {
        "schema": SCHEMA,
        "readable": w["readable"],
        "window_h": w["window_h"],
        "calls": w["calls"], "failed": w["failed"],
        "visible_tokens": w["visible_total"],
        "effective_tokens": effective,
        "multiplier": mult,
        "capacity_tokens": int(cap),
        "share_pct": pct,
        "budget_tokens": budget,
        "used_pct": used_pct,
        "remaining_tokens": max(0, budget - effective),
        "by_leg": legs,
        "unattributed_calls": w["unattributed_calls"],
        # ── برچسب‌های صداقت: هیچ‌کدام از این‌ها مشاهده نیستند ──────────────
        "capacity_verified": False,
        "multiplier_verified": False,
        "attribution_complete": w["unattributed_calls"] == 0 and w["calls"] > 0,
        "note": ("ظرفیت و ضریب هر دو تخمینِ اعلام‌شده‌اند، نه سنجیده. "
                 "سهم درصدی است، پس اصلاحِ تخمینِ ظرفیت خودبه‌خود بودجه را "
                 "اصلاح می‌کند (رأیِ مالک ۰۸-۰۴)."),
        "oldest_ts": w["oldest_ts"], "newest_ts": w["newest_ts"],
    }


def _human(s: dict) -> str:
    if not s["readable"]:
        return "متر: ذخیرهٔ paid-calls خوانده نشد — «نمی‌دانم»، نه «صفر»."
    lines = [
        f"پنجره: {s['window_h']:.0f} ساعتِ غلتان · {s['calls']} فراخوان "
        f"({s['failed']} شکست)",
        f"توکنِ مرئی: {s['visible_tokens']:,}",
        f"مؤثر (×{s['multiplier']}): {s['effective_tokens']:,}  ← تخمین",
        f"بودجه: {s['share_pct']:.0f}٪ از {s['capacity_tokens']:,} = "
        f"{s['budget_tokens']:,}  ← ظرفیت تخمین است",
    ]
    if s["used_pct"] is not None:
        lines.append(f"مصرف‌شده: {s['used_pct']:.1f}٪ · باقی: "
                     f"{s['remaining_tokens']:,}")
    for leg, d in sorted(s["by_leg"].items()):
        up = f"{d['used_pct']:.1f}٪" if d["used_pct"] is not None else "—"
        lines.append(f"  {leg:<8} {d['effective_tokens']:>12,} / "
                     f"{d['budget_tokens']:>12,}  ({up}، {d['calls']} فراخوان)")
    if s["unattributed_calls"]:
        lines.append(f"⚠️ {s['unattributed_calls']} فراخوانِ بی‌انتساب — ردیف‌های "
                     f"پیش از ۰۸-۰۴ فیلدِ task ندارند")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    s = status()
    if "--json" in argv:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print(_human(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
