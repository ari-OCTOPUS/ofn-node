#!/usr/bin/env python3
"""
budget_gate.py — شمارندهٔ بودجهٔ مشترک (تک‌منبع) برای همهٔ مصرف‌کننده‌های LLM.
قرارداد: قبل از هر call → reserve(agent, est). اگر allow: بعد از call → settle(agent, est, actual)؛
اگر call شکست خورد → release(agent, est). رزرو زیرِ قفل persist می‌شود (ضدِ race).
تست‌شده در سندباکس: race/concurrency (۲۰ موازی → دقیقاً ۱۰ مجاز، سقف $2.00)، fail-closed، rollover.
مبنا: ARCHITECT_CHARTER §۵ + LEARNING-STATE (budget). status: propose (ساخته‌شده به verdict «همه‌چیو درست کن»).
"""
import json, pathlib, datetime, os, time

STATE = pathlib.Path(os.environ.get("BUDGET_STATE", r"F:\backup\_ops\budget\budget-state.json"))
LOCK  = pathlib.Path(str(STATE) + ".lock")
# ─── v2 (A1 · SoT-read): سقف‌ها از budgets.yaml خوانده می‌شوند؛ این ثابت‌ها فقط «کفِ fail-closed»اند.
# هرگز از این‌ها شل‌تر نمی‌شویم (strictest = min(yaml, hardcode))؛ yaml ناخوانا = همین‌ها.
# اعداد: verdict آری 2026-07-09 (روز 2 · ماه 200 · فاجعه 500 AUD). قبلاً ماه=30 (verdict 2026-07-07)؛
# با routingِ GLM+Fugu و سابسکرایبِ فلت، ۲۰۰ شد (disaster/kill دست‌نخورده).
CEIL_DAY_AUD_HARD, CEIL_MONTH_AUD_HARD, DISASTER_AUD_HARD = 2.0, 30.0, 500.0  # ماه→۳۰ (go-live 2026-07-10، رأی مالک «۳۰ بماند»؛ strictest=min(yaml30,hard30)=30)
AUD_DEFAULT = 1.5    # نرخِ USD→AUD پیش‌فرض (هم‌ارزِ opslib.fx_aud_per_usd؛ yaml.global.aud_per_usd override می‌کند)
BUDGETS_YAML = pathlib.Path(os.environ.get("BUDGETS_YAML", str(STATE.parent / "budgets.yaml")))
STALE_LOCK_S = 30    # قفلِ رهاشده بعد از این ثانیه‌ها steal می‌شود (ضدِ deadlock)

# ─── D3: SHADOW, alert-only drawdown guard (additive؛ صفر اثرِ پولی) ───────────────
# ماژولِ خواهر drawdown_guard.py. پشتِ HH_DRAWDOWN_ENFORCE (پیش‌فرض OFF → این مسیر
# اصلاً اجرا نمی‌شود → رفتارِ خرج byte-identical). ON → فقط observe + advisory alert؛
# هرگز block/halt/reserve/settle نمی‌کند. Enforcement (بلاک روی breach) کارِ owner-gatedِ
# آینده است و این‌جا ساخته نشده. importِ fail-soft — هر خطا = گاردِ خاموش، نه crash.
try:
    import sys as _sys
    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import drawdown_guard as _drawdown_guard   # sibling در همین scripts/
except Exception:
    _drawdown_guard = None

DRAWDOWN_ADVISORY_LOG = pathlib.Path(os.environ.get(
    "DRAWDOWN_ADVISORY_LOG", str(STATE.parent / "drawdown-advisory.jsonl")))


def _drawdown_shadow_observe(agent, d, c):
    """مشاهدهٔ shadow، money-neutral و fail-soft. مقدارِ برگشتی در هیچ تصمیمِ پولی
    استفاده نمی‌شود و state را تغییر نمی‌دهد. flag OFF (پیش‌فرض) → خروجِ زودهنگام،
    صفر I/O → byte-identical. هر خطا خاموش بلعیده می‌شود (گارد هرگز خرج را متأثر نمی‌کند)."""
    if _drawdown_guard is None:
        return
    if not _drawdown_guard.enforce_enabled():
        return   # HH_DRAWDOWN_ENFORCE خاموش (پیش‌فرض) → هیچ مشاهده‌ای، byte-identical
    try:
        window_spend_aud = float(d.get("spent_today_usd", 0.0)) * c["aud"]
        _drawdown_guard.observe(
            window_spend_aud, c["day_aud"], c,
            agent=agent,
            now_iso=datetime.datetime.now().isoformat(timespec="seconds"),
            log_path=str(DRAWDOWN_ADVISORY_LOG),
            enforce_flag_on=True)
    except Exception:
        pass   # fail-soft — گاردِ shadow هرگز مسیرِ پول را متأثر نمی‌کند


# ── A1 (۲۰۲۶-۰۸-۰۳): پنجرهٔ استثنای سقفِ ماهانه — در کد، نه در متن ──────────
# رأیِ مالک ۰۷-۳۰ (تمدیدشده ۰۸-۰۳): «سقفِ این پنجره US$200 است، نه AU$30.»
# تا امروز آن استثنا فقط در `_ops/GOALS-OCTOPUS.md` **نوشته** شده بود و هیچ کدی
# نمی‌خواندش: `_caps()` همان min(hard=30, yaml=30) را می‌داد و `reserve()` روی
# AU$30 هالت می‌کرد. یعنی پنجره از ۰۷-۳۰ تا امروز اثرِ واقعی نداشت. (چون
# spent_month=0 بود هرگز گاز نگرفت — پس چیزی از دست نرفت، ولی ادعا و رفتار یکی
# نبودند؛ و همین شکل از «متن به‌جای کد» جای دیگری ۳۱ ساعت قحطی ساخت.)
#
# خواهرش `goal_directed.max_circular_now()` از ۰۷-۳۰ همین قرارداد را دارد و
# خودش منقضی می‌شود؛ این تابع عمداً **همان الگو** است تا یکی یاد گرفتنش کافی باشد.
SPEND_CAP_USD_ENV, SPEND_CAP_UNTIL_ENV = "OCTOPUS_SPEND_CAP_USD", "OCTOPUS_SPEND_CAP_UNTIL"

# A2 (۲۰۲۶-۰۸-۰۳): اگر env نبود، رأیِ **tracked** ِ مالک پرش می‌کند —
# `_ops/OCTOPUS-flags.cmd` گیت‌ایگنور است، پس تنها ردِ ماندگارِ رأی همان فایل است.
# env همچنان برنده می‌ماند (رفتارِ امروز بایت‌به‌بایت همان). import ِ fail-soft:
# این مسیرِ پول است و نبودِ ماژول فقط یعنی برگشت به رفتارِ env-only.
try:
    import sys as _sys
    _OPS = pathlib.Path(__file__).resolve().parents[2] / "_ops"
    if str(_OPS) not in _sys.path:
        _sys.path.insert(0, str(_OPS))
    import owner_verdicts as _verdicts
except Exception:  # noqa: BLE001
    _verdicts = None


def _knob(env_name):
    """مقدارِ مؤثرِ یک knob: env، وگرنه رأیِ ثبت‌شده، وگرنه رشتهٔ خالی."""
    live = str(os.environ.get(env_name, "") or "").strip()
    if live or _verdicts is None:
        return live
    try:
        return _verdicts.get(env_name)
    except Exception:  # noqa: BLE001
        return ""


def spend_cap_now(base_aud, aud_per_usd, disaster_aud, today=None):
    """سقفِ ماهانهٔ مؤثر (AUD) + دلیلش. `today` **کاملاً** تزریق‌شدنی است؛ هیچ
    شاخه‌ای پشتِ سرِ صداکننده ساعتِ دیوار را نمی‌خواند (درسِ «ساعتِ نیمه‌تزریقی»).

    fail-closed به سمتِ **محافظه‌کار** — یعنی پایهٔ سخت‌گیر — روی: نبودِ env،
    **نبودِ تاریخِ انقضا** (استثنای بی‌تاریخ = قاعدهٔ نو، و رأیِ مالک تاریخ داشت)،
    مقدارِ ناخوانا/نامثبت، تاریخِ بدشکل، و پنجرهٔ گذشته. پس یک تایپو سقف را
    ابدی باز نمی‌کند. استثنا فقط **بالا** می‌برد و هرگز از خطِ فاجعه رد نمی‌شود.

    بدونِ کش خوانده می‌شود، پس در روزِ انقضا **بدونِ ری‌استارت** برمی‌گردد."""
    base = float(base_aud)
    shut = lambda why: {"value_aud": base, "reason": why, "window_open": False}  # noqa: E731
    raw = _knob(SPEND_CAP_USD_ENV)
    until = _knob(SPEND_CAP_UNTIL_ENV)
    if not raw:
        return shut("default")
    if not until:
        return shut("no-expiry-declared")
    try:
        usd = float(raw)
    except (TypeError, ValueError):
        return shut("bad-value")
    if not usd > 0:
        return shut("bad-value")
    try:
        end = datetime.date.fromisoformat(until)
        now = datetime.date.fromisoformat(today) if today else datetime.date.today()
    except (TypeError, ValueError):
        return shut("bad-date")
    if now > end:
        return {**shut(f"expired:{until}"), "expired": True}
    value = min(max(base, usd * float(aud_per_usd)), float(disaster_aud))
    return {"value_aud": value, "reason": f"owner-window:{until}", "window_open": True}


def _caps():
    """v2/A1: سقف‌ها را از budgets.yaml (تک‌منبع حقیقت) می‌خواند. fail-closed:
      • yaml ناخوانا/غایب/بی‌PyYAML → کفِ هاردکد (هرگز نامحدود، هرگز crash).
      • cap شل‌تر از هاردکد در yaml → هاردکد می‌ماند (strictest = min).
    فقط سقف‌ها SoT-read‌اند؛ نرخ ارز آینهٔ opslib است (yaml.aud_per_usd یا 1.5) تا دو لایه واگرا نشوند.
    بی‌کش — هر بار تازه می‌خواند تا ویرایش مالک روی yaml بدون ری‌استارت اعمال شود."""
    day, month, disaster, aud, src = (
        CEIL_DAY_AUD_HARD, CEIL_MONTH_AUD_HARD, DISASTER_AUD_HARD, AUD_DEFAULT, "hardcode-floor")
    spike = None   # D3 (shadow drawdown guard): raw owner-tunable threshold از budgets.yaml global.spike_pct؛
                   # None → drawdown_guard از کفِ placeholder استفاده می‌کند. صرفاً observe؛ هیچ اثرِ پولی ندارد.
    try:
        import yaml
        g = (yaml.safe_load(BUDGETS_YAML.read_text("utf-8")) or {}).get("global", {})
        if isinstance(g, dict):
            if g.get("cap_monthly")  is not None: month    = min(month,    float(g["cap_monthly"]))
            if g.get("cap_daily")    is not None: day      = min(day,      float(g["cap_daily"]))
            if g.get("cap_disaster") is not None: disaster = min(disaster, float(g["cap_disaster"]))
            if g.get("aud_per_usd")  is not None: aud      = float(g["aud_per_usd"])
            if g.get("spike_pct")    is not None:                      # D3: raw، بدون floor (single-source read)
                try: spike = float(g["spike_pct"])
                except (TypeError, ValueError): spike = None
            src = "budgets.yaml ∧ hardcode-floor"
    except Exception:
        pass  # fail-closed → کفِ هاردکد
    # A1: پنجرهٔ استثنای مالک — **بعد از** کفِ سخت‌گیر اعمال می‌شود چون عمداً
    # بالابرنده است. بسته/منقضی ⇒ `month` بایت‌به‌بایت همان قبلی می‌ماند.
    window = spend_cap_now(month, aud, disaster)
    if window["window_open"]:
        month = window["value_aud"]
        src += f" ∧ {window['reason']}"
    return {"day_aud": day, "month_aud": month, "disaster_aud": disaster, "aud": aud,
            "src": src, "spike_pct": spike,   # spike_pct صرفاً برای گاردِ shadow؛ در تصمیمِ پول استفاده نمی‌شود
            "month_window": window}           # قابلِ مشاهده در گزارش — پنجرهٔ باز هرگز پنهان نیست


def _load():
    if not STATE.exists():
        return {}
    return json.loads(STATE.read_text("utf-8"))


def _save(d):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")


def _lock():
    for _ in range(50):
        try:
            return os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            try:  # steal a stale lock left by a crashed holder
                if time.time() - os.path.getmtime(LOCK) > STALE_LOCK_S:
                    os.unlink(LOCK); continue
            except OSError:
                pass
            time.sleep(0.1)
    raise TimeoutError("budget busy")


def _unlock(fd):
    os.close(fd)
    try:
        os.unlink(LOCK)
    except OSError:
        pass


def _roll(d):
    t = datetime.date.today().isoformat(); m = t[:7]
    if d.get("date") != t:
        d["date"] = t; d["spent_today_usd"] = 0.0
    if d.get("month") != m:
        d["month"] = m; d["spent_month_aud"] = 0.0
    for k, v in (("spent_today_usd", 0.0), ("spent_month_aud", 0.0), ("halted", False)):
        d.setdefault(k, v)
    return d


def reserve(agent, est_usd):
    fd = _lock()
    try:
        try:
            d = _roll(_load())
        except Exception:
            return {"allow": False, "reason": "state-unreadable"}   # fail-closed (نه crash)
        c = _caps()                                # v2: سقف‌ها از SoT (با کفِ fail-closed)
        if d["halted"]:
            return {"allow": False, "reason": "halted"}
        if (d["spent_today_usd"] + est_usd) * c["aud"] > c["day_aud"]:
            return {"allow": False, "reason": "daily"}
        if d["spent_month_aud"] + est_usd * c["aud"] > c["month_aud"]:
            d["halted"] = True; _save(d); return {"allow": False, "reason": "monthly-halt"}
        d["spent_today_usd"] += est_usd            # ← رزرو واقعاً persist می‌شود
        d["spent_month_aud"] += est_usd * c["aud"]
        _save(d)
        _drawdown_shadow_observe(agent, d, c)      # D3 shadow — money-neutral، fail-soft، پس از persist
        return {"allow": True, "reserved": est_usd}
    finally:
        _unlock(fd)


def settle(agent, est_usd, actual_usd):
    """بعد از call: تخمین را با هزینهٔ واقعی جایگزین کن."""
    fd = _lock()
    try:
        c = _caps()                                # v2: نرخ/خطِ فاجعه از SoT (با کفِ fail-closed)
        d = _roll(_load()); delta = actual_usd - est_usd
        d["spent_today_usd"] = max(0.0, d["spent_today_usd"] + delta)
        d["spent_month_aud"] = max(0.0, d["spent_month_aud"] + delta * c["aud"])
        if d["spent_month_aud"] >= c["disaster_aud"]:
            d["halted"] = True                     # خطِ فاجعه (D-22) = halt کامل
        _save(d); return d
    finally:
        _unlock(fd)


def release(agent, est_usd):
    """اگر call شکست خورد → رزرو پس داده می‌شود (بدونِ نشتِ بودجه)."""
    return settle(agent, est_usd, 0.0)


if __name__ == "__main__":
    # CLI کوچک برای بازرسی: python -X utf8 budget_gate.py  → سقف‌های مؤثر (SoT) + وضعیتِ امروز
    try:
        print(json.dumps({"caps_effective": _caps(), "state": _roll(_load())},
                         ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
