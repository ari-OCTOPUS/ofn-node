#!/usr/bin/env python3
"""consolidate.py — تثبیتِ حافظه: اپیزودیک → سِمانتیک (sleep-time compute).

الهام: Generative Agents (Park و همکاران ۲۰۲۳) — «salience» (تازگی × اهمیت × ربط) و
«reflection»: عاملِ خوابیده لاگِ رویدادهای خام (اپیزودیک) را می‌روبد، برجسته‌ترها را به
نوت‌های سِمانتیکِ **کران‌دار** تقطیر می‌کند، و رویدادهای خامِ پردازش‌شده را **آرشیو** می‌کند
(هرگز حذف — قاعدهٔ vault §۱؛ فقط انتقال/حفظ). این کارِ محاسباتیِ زمانِ خواب است: بارِ
پنجرهٔ زندهٔ رویداد را سبک نگه می‌دارد و پیش از آنکه پنجرهٔ رولینگ (۵۰۰ خطِ events.py)
خطوطِ کهنه را از دیدِ خواننده بیندازد، آن‌ها را در آرشیو ماندگار می‌کند.

مرزها (هم‌راستا با بقیهٔ لایهٔ متابولیسم):
  * FLAG-OFF/SHADOW: تا `CORTEX_CONSOLIDATE=1` نباشد **no-op مطلق** — صفر خواندن، صفر نوشتن.
  * FAIL-SOFT: هر خطا → پیش‌فرضِ امن ({n_in:0,...})، هرگز caller را نمی‌شکند.
  * فقط زیرِ STATE_DIR می‌نویسد (semantic_memory.jsonl / events.archive.jsonl / cursor).
  * append-only: events.jsonl (لاگِ زنده) هرگز بازنویسی نمی‌شود؛ آرشیو یک کپیِ ماندگار است
    (پس «چیزی حذف نمی‌شود» دوچندان برقرار است: هم اصل در جای خود می‌ماند، هم در آرشیو).
  * CONTAINMENT: آرشیو = کپیِ verbatim (حفظِ اصل، §۱)؛ اما نوتِ سِمانتیک = سنتزِ رو-به-انسان
    و همیشه scrub می‌شود (هیچ هویتِ Project-F در لایهٔ مشتق‌شده echo نمی‌شود).

$0 · stdlib + opslib · بی‌محتوا در لایهٔ سِمانتیک.

API:  consolidate_once() -> {"n_in", "n_semantic", "archived", ...}
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
EVENTS_LOG = STATE / "events.jsonl"                 # همان مسیرِ events.py (تک‌منبع)
ARCHIVE    = STATE / "events.archive.jsonl"         # کپیِ ماندگارِ خام (هرگز حذف)
SEMANTIC   = STATE / "semantic_memory.jsonl"        # لایهٔ سِمانتیکِ مشتق‌شده (scrub-شده)
CURSOR     = STATE / "cortex" / "consolidate-cursor.json"

# ── knobها (همه env-override، همه $0) ────────────────────────────────────────────
TAIL_LINES   = int(os.environ.get("CORTEX_CONSOLIDATE_TAIL", "500"))      # پنجرهٔ tail
HALFLIFE_H   = float(os.environ.get("CORTEX_CONSOLIDATE_HALFLIFE_H", "24"))  # نیمه‌عمرِ تازگی
MAX_SEMANTIC = int(os.environ.get("CORTEX_CONSOLIDATE_MAX", "20"))        # سقفِ نوت/دور (کران)
SALIENCE_MIN = float(os.environ.get("CORTEX_CONSOLIDATE_MIN_SAL", "0.05"))  # کفِ برجستگی
SELF_AGENT   = "memory-consolidate"                # رویدادهای خودِ این ماژول consolidate نمی‌شوند

# اهمیتِ پایه بر پایهٔ نوعِ رویداد (شهودِ Generative Agents: خرابی/incident > روتین) ─
_IMPORTANCE = {
    "incident.opened":    1.00,
    "task.failed":        0.90,
    "approval.required":  0.85,
    "task.blocked":       0.80,
    "handoff.created":    0.60,
    "incident.contained": 0.55,
    "task.completed":     0.30,
    "task.started":       0.20,
    "system.heartbeat":   0.05,
}
_IMPORTANCE_DEFAULT = 0.40

# containment (parity با events._scrub_str / registry_scan.scrub) ────────────────
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")


def enabled() -> bool:
    """FLAG-OFF: تا مالک این env-flag را روشن نکند، ماژول کاملاً no-op است."""
    return os.environ.get("CORTEX_CONSOLIDATE", "0") == "1"


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _scrub(s: str, cap: int = 180) -> str:
    """هر رشتهٔ حاوی هویتِ ممنوع → کاملاً redact. فقط برای لایهٔ سِمانتیکِ مشتق‌شده."""
    v = str(s or "")[:cap]
    low = v.lower()
    if any(b in low or b in v for b in _BANNED_ECHO):
        return "(redacted:containment)"
    return v


# ── مؤلفه‌های برجستگی (salience) — هرکدام در [0,1] ────────────────────────────────
def _recency(ev: dict, now: float) -> float:
    """فروپاشیِ نمایی با نیمه‌عمر: رویدادِ تازه‌تر = وزنِ بیشتر. ts گم/۰ → عملاً کهنه."""
    try:
        ts = float(ev.get("ts", 0) or 0)
    except (TypeError, ValueError):
        ts = 0.0
    if ts <= 0:
        return 0.0
    age_h = max(0.0, (now - ts) / 3600.0)
    hl = HALFLIFE_H if HALFLIFE_H > 0 else 24.0
    return _clamp(0.5 ** (age_h / hl))


def _importance(ev: dict) -> float:
    """اهمیتِ ذاتیِ رویداد: نوعِ رویداد + تشدید با وضعیتِ خطا/نیازِ تأیید."""
    imp = _IMPORTANCE.get(str(ev.get("event_name", "")), _IMPORTANCE_DEFAULT)
    if str(ev.get("approval_state", "")) == "required":
        imp = max(imp, 0.85)                       # منتظرِ تأییدِ انسان = ذاتاً مهم
    if str(ev.get("status", "")).lower() in ("failed", "alert", "error"):
        imp = min(1.0, imp + 0.10)
    return _clamp(imp)


def _relevance(ev: dict) -> float:
    """ربط (پروکسیِ بی‌query): کنش‌پذیری + پیوستگی. اکشنِ بعدی/trace = مرتبط‌تر با «الان»."""
    rel = 0.5
    if str(ev.get("next_action", "")).strip():
        rel += 0.3                                 # اکشن‌پذیر = مرتبط با موقعیتِ جاری
    if str(ev.get("trace_id", "")).strip() or str(ev.get("correlation_id", "")).strip():
        rel += 0.2                                 # به یک زنجیره متصل است
    return _clamp(rel)


def _salience(ev: dict, now: float | None = None) -> float:
    """برجستگیِ کلی = تازگی × اهمیت × ربط (Generative Agents). خروجی در [0,1]."""
    n = time.time() if now is None else now
    return _recency(ev, n) * _importance(ev) * _relevance(ev)


# ── tail کردنِ لاگِ رویداد (خواندنِ خام؛ نگه‌داشتنِ خطِ خام برای آرشیوِ verbatim) ──
def _tail_events(limit: int) -> list[tuple[str, dict]]:
    """آخرین `limit` رویداد به‌صورتِ (خطِ خام، dictِ parse‌شده). خطوطِ خراب skip (fail-soft)."""
    out: list[tuple[str, dict]] = []
    try:
        if not EVENTS_LOG.exists():
            return out
        lines = EVENTS_LOG.read_text("utf-8").splitlines()
    except OSError:
        return out
    for raw in lines[-max(1, limit):]:
        raw = raw.rstrip("\n")
        if not raw.strip():
            continue
        try:
            out.append((raw, json.loads(raw)))
        except ValueError:
            continue                               # خطِ خراب = نادیده، نه crash
    return out


def _read_cursor() -> float:
    try:
        if CURSOR.exists():
            return float(json.loads(CURSOR.read_text("utf-8")).get("last_ts", 0) or 0)
    except (OSError, ValueError, TypeError):
        pass
    return 0.0


def _write_cursor(last_ts: float, stats: dict) -> None:
    try:
        CURSOR.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(CURSOR) as lj:
            lj.write({"ts": opslib.now_iso(), "schema": "consolidate-cursor.v1",
                      "last_ts": float(last_ts), **stats})
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"consolidate cursor write failed: {e}"])


def _make_note(ev: dict, sal: float, now: float) -> dict:
    """یک نوتِ سِمانتیک (reflection) از یک رویدادِ برجسته — content-free و scrub-شده.

    ۲۰۲۶-۰۸-۰۸ (up-1f41a4499b): memory poisoning guard. قانونِ اساسی §۷ می‌گوید
    نوتِ created_by:agent باید sources≥2 داشته باشد. این تابع حالا فیلد `sources`
    (شمارشِ منابعِ مستقل) و `poisoning_risk` را اضافه می‌کند. یک منبعِ مستقل =
    رویداد با trace_id معتبر، یا approval_state=approved، یا owner Correlation.
    بدونِ منبعِ مستقل = poisoning_risk بالاتر."""
    trace_id = str(ev.get("trace_id", "") or "")
    approval = str(ev.get("approval_state", "") or "")
    corr = str(ev.get("correlation_id", "") or "")
    # شمارشِ منابعِ مستقل (هرکدام یک شاهدِ جداگانه)
    sources_count = 0
    if trace_id and trace_id != "0" * len(trace_id):
        sources_count += 1
    if approval in ("approved", "denied", "rejected"):
        sources_count += 1
    if corr and corr.startswith("oct-"):
        sources_count += 1
    # poisoning_risk: نوتِ agent-made بدونِ منبعِ مستقل
    agent_id = str(ev.get("agent_id", "") or "")
    is_agent = agent_id and agent_id != SELF_AGENT and "self-heal" not in agent_id
    poisoning_risk = "high" if (is_agent and sources_count == 0) else (
                     "medium" if (is_agent and sources_count == 1) else "low")
    note = {
        "ts": opslib.now_iso(), "schema": "semantic-memory.v1", "kind": "reflection",
        "source_ts": ev.get("timestamp", ""),
        "source_agent": _scrub(ev.get("agent_id", ""), 40),
        "source_event": str(ev.get("event_name", ""))[:40],
        "trace_id": trace_id[:40],
        "salience": round(sal, 4),
        "recency": round(_recency(ev, now), 4),
        "importance": round(_importance(ev), 4),
        "relevance": round(_relevance(ev), 4),
        "gist": _scrub(ev.get("summary", ""), 180),
        "next_action": _scrub(ev.get("next_action", ""), 120),
        # ۲۰۲۶-۰۸-۰۸: memory poisoning guard (up-1f41a4499b)
        "sources_count": sources_count,
        "poisoning_risk": poisoning_risk,
    }
    # اگر poisoning_risk بالاست، هشدار بده (ولی نوت را حذف نکن — §۱: هرگز حذف)
    if poisoning_risk == "high":
        try:
            opslib.alert([f"memory-poisoning-risk: نوتِ agent-made بدونِ منبعِ مستقل "
                          f"(agent={_scrub(agent_id, 30)}, event={ev.get('event_name','')})"])
        except Exception:  # noqa: BLE001
            pass
    return note


def consolidate_once(now: float | None = None) -> dict:
    """یک دورِ تثبیت: tail → امتیازدهیِ برجستگی → نوتِ سِمانتیکِ کران‌دار + آرشیوِ خام.

    خروجی: {n_in, n_semantic, archived, flag, ...}. FLAG-OFF → همه صفر و صفر نوشتن.
    هرگز crash نمی‌کند (fail-soft)."""
    base = {"n_in": 0, "n_semantic": 0, "archived": 0, "flag": False,
            "ts": opslib.now_iso()}
    if not enabled():
        return base                                # no-op مطلق: صفر خواندن/نوشتن
    base["flag"] = True
    try:
        now = time.time() if now is None else now
        last_ts = _read_cursor()
        tail = _tail_events(TAIL_LINES)
        if not tail:
            return base
        max_ts = last_ts
        new: list[tuple[str, dict]] = []           # (خطِ خام، dict) رویدادهای نو (بعد از cursor)
        for raw, ev in tail:
            try:
                ts = float(ev.get("ts", 0) or 0)
            except (TypeError, ValueError):
                ts = 0.0
            if ts > max_ts:
                max_ts = ts
            if ts <= last_ts:
                continue                           # قبلاً پردازش شده (idempotent)
            if str(ev.get("agent_id", "")) == SELF_AGENT:
                continue                           # رویدادهای خودِ consolidate را consolidate نکن
            new.append((raw, ev))
        if not new:
            # چیزی نو نبود؛ cursor را جلو ببر تا رویدادهای self هم دوباره دیده نشوند
            if max_ts > last_ts:
                _write_cursor(max_ts, {"n_in": 0, "n_semantic": 0, "archived": 0})
            return base

        n_in = len(new)

        # (۱) آرشیوِ خامِ verbatim — حفظِ کاملِ اصل (هرگز حذف، §۱) ─────────────────
        archived = 0
        try:
            ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
            with open(ARCHIVE, "a", encoding="utf-8") as fh:
                for raw, _ev in new:
                    fh.write(raw + "\n")
                    archived += 1
        except OSError as e:
            opslib.alert([f"consolidate archive write failed: {e}"])

        # (۲) نوتِ سِمانتیکِ کران‌دار — فقط برجسته‌ترها، top-K (Generative Agents) ───
        scored = [(_salience(ev, now), ev) for _raw, ev in new]
        scored = [(s, ev) for (s, ev) in scored if s >= SALIENCE_MIN]
        scored.sort(key=lambda t: t[0], reverse=True)   # نزولی: برجسته‌ترین اول
        selected = scored[:max(0, MAX_SEMANTIC)]        # کرانِ خروجی
        n_semantic = 0
        for sal, ev in selected:
            try:
                opslib.append_jsonl(SEMANTIC, _make_note(ev, sal, now))
                n_semantic += 1
            except Exception as e:  # noqa: BLE001
                opslib.alert([f"consolidate semantic write failed: {e}"])
                break

        # (۳) cursor را جلو ببر (idempotency) ─────────────────────────────────────
        _write_cursor(max_ts, {"n_in": n_in, "n_semantic": n_semantic, "archived": archived})

        result = {"n_in": n_in, "n_semantic": n_semantic, "archived": archived,
                  "flag": True, "ts": opslib.now_iso()}

        # رویدادِ داشبورد (best-effort؛ اثری روی نتیجه ندارد) ──────────────────────
        if n_in > 0:
            try:
                sys.path.insert(0, str(_OPS))
                import events  # noqa: E402
                events.emit("task.completed", SELF_AGENT,
                            summary=f"تثبیتِ حافظه: {n_in} رویداد → {n_semantic} نوتِ سِمانتیک، "
                                    f"{archived} آرشیو",
                            next_action="")
            except Exception:  # noqa: BLE001
                pass
        return result
    except Exception as e:  # noqa: BLE001 — fail-soft مطلق: caller هرگز نمی‌شکند
        opslib.alert([f"consolidate_once failed: {e}"])
        return base


def recent_semantic(n: int = 10) -> list[dict]:
    """جدیدترین نوت‌های سِمانتیک برای داشبورد/بازیابی (جدید→قدیم). fail-soft."""
    try:
        if not SEMANTIC.exists():
            return []
        out = []
        for ln in SEMANTIC.read_text("utf-8").splitlines()[-max(1, n * 3):]:
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out[-n:][::-1]
    except OSError:
        return []


def summary() -> dict:
    """خلاصهٔ سبک برای خوراکِ داشبورد (بدونِ اجرای دور)."""
    cur = {}
    try:
        if CURSOR.exists():
            cur = json.loads(CURSOR.read_text("utf-8"))
    except (OSError, ValueError):
        cur = {}
    recent = recent_semantic(5)
    return {"schema": "consolidate-summary.v1", "flag": enabled(),
            "last_run": cur.get("ts", ""), "last_n_in": cur.get("n_in", 0),
            "last_n_semantic": cur.get("n_semantic", 0),
            "recent_semantic": [{"gist": r.get("gist", ""), "salience": r.get("salience", 0),
                                 "event": r.get("source_event", "")} for r in recent]}


if __name__ == "__main__":
    print(json.dumps(consolidate_once(), ensure_ascii=False, indent=2))