#!/usr/bin/env python3
"""control_plane.snapshot() — جمع‌کنندهٔ واحدِ حالتِ زندهٔ کلِ سیستم.

علتِ معماری: اختاپوس ۷ لایه دارد و اصلش این است که «هر لایه باید لایهٔ زیرِ خودش را
بخواند، وگرنه فقط دفتر پر می‌کند.» ولی هیچ جمع‌کنندهٔ واحدی نبود — هیچ تابعی که کلِ
حالت را در یک JSON برگرداند. نتیجه: مالک نمی‌توانست وضعیت را ببیند، وب‌اپ داده نداشت،
و هر کارتِ تلگرامی منبعِ خودش را جدا می‌خواند. این تابع آن شکافِ «نمی‌شه دید» را
می‌بندد و پایهٔ وب‌اپ و هر dashboardی می‌شود.

قرارداد (سخت):
  · کاملاً **read-only.** هیچ writeای، هیچ side-effectای، صفر LLM call ($0).
  · **fail-soft کامل:** هر بخشی که خطا دهد → `{"status":"unknown","reason":"..."}`،
    نه crash. snapshot هرگز نباید fail کند (خروجیِ خودش بازتابِ سلامتیِ سیستم است).
  · **نمایِ ثابت:** کلیدهای خروجی پایدارند (نه پویا)؛ هر مقدار JSON-serializable.
  · **cache سبک:** TTL ۵ ثانیه (چون وب‌اپ ممکن است هر چند ثانیه poll کند). فقط در
    همان پروسه — نه بینِ پروسه‌ها (هر پروسه از snapshot_cache خودش استفاده می‌کند).
  · pشتِ فلگ **نیست** — فقط خواندن است، $0، هیچ‌خطری. owner-auth در لایهٔ endpoint
    (کارِ بعد)، نه اینجا.

منابعِ داده (reader-map): همهٔ state از `_ops/state/*.json` خوانده می‌شود. این فایل
عمداً miniapp_state را import نمی‌کند (دو دلیل: (۱) آن ماژول پر از منطقِ وب‌اپ و
side-effect است؛ (۲) snapshot باید پایه‌ای‌تر و قابل‌تست‌تر بماند). در عوض، هر بخش
مستقیم از فایلِ نام‌بردهٔ خودش می‌خواند — reader-map زیر همانی است.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# ریشهٔ repo: این فایل در `_ops/control_plane/` می‌نشیند، پس repo = دو سطح بالاتر.
# ORG_ROOT قراردادِ سراسریِ ریپوست (همان ریشهٔ vault)؛ _ops = ORG_ROOT/_ops.
_REPO = Path(os.environ.get("ORG_ROOT", str(_HERE.parent.parent))).resolve()
_OPS = _REPO / "_ops"
if not _OPS.exists():           # fallback: محاسبه از مسیرِ فایل (پدرِ پدرِ پدر)
    _OPS = _HERE.parent.parent
_STATE = _OPS / "state"

# خروجی‌های مغزِ 4D (consolidation/self-model) — خواندن، نه ساختِ پوشه.
_BRAIN_4D = _REPO / "4d_system" / "outputs" / "self_evolved"
_4D_DAEMON = _REPO / "4d_system" / "outputs" / "daemon_state.json"
_NEURAL = _OPS / "neural"

# ─── cache (در-پروسه، TTL ۵s) ──────────────────────────────────────────────────
_CACHE_TTL_S = 5.0
_cache: "dict | None" = None
_cache_ts: float = 0.0


def cache_clear() -> None:
    """باطل‌کردنِ cache (تست‌ها و endpointِ no-cache از این استفاده می‌کنند)."""
    global _cache, _cache_ts
    _cache = None
    _cache_ts = 0.0


def _section(name: str, fn) -> dict:
    """هر بخش در قرنطینهٔ خودش — یک بخشِ خراب هرگز کلِ snapshot را نمی‌کشد.
    الگویِ هم‌خانوادهٔ miniapp_state._section."""
    try:
        out = fn()
        if isinstance(out, dict):
            return out
        return {"status": "unknown", "reason": f"{name}_returned_non_dict"}
    except Exception as exc:  # noqa: BLE001 — fail-soft: snapshot هرگز crash نمی‌کند
        return {"status": "unknown",
                "reason": f"{name}_read_failed: {type(exc).__name__}: {str(exc)[:160]}"}


def _read_json(path: Path) -> "dict | list | None":
    """JSON-safe read. هر خطا → None (نه crash). path نباید پوشه بسازد."""
    try:
        if path.exists():
            return json.loads(path.read_text("utf-8", errors="replace"))
    except Exception:  # noqa: BLE001
        return None
    return None


# ─── بخش‌ها ─────────────────────────────────────────────────────────────────────
def _organism() -> dict:
    """بخش ۱: ارگانیسم — beat/frozen/halted/started/epoch/legs."""
    d = _read_json(_STATE / "ORGANISM-STATE.json") or {}
    if not isinstance(d, dict):
        return {"status": "unknown", "reason": "ORGANISM-STATE not a dict"}
    # legs: دو منبعِ ممکن (ziman واحد، یا business_legs لیست). هر دو را خواندنِ بدونِ
    # فرض می‌کنیم؛ live/dead از کلیدِ `live` یا `money_link` استخراج می‌شود.
    legs: dict = {}
    biz = d.get("business_legs")
    if isinstance(biz, dict):
        bl = biz.get("business_legs") if isinstance(biz.get("business_legs"), dict) else biz
        if isinstance(bl, dict):
            for lid, info in bl.items():
                if isinstance(info, dict):
                    legs[str(lid)] = {"live": bool(info.get("live")),
                                      "money_link": info.get("money_link"),
                                      "note": info.get("note")}
    ziman = d.get("ziman")
    if isinstance(ziman, dict) and ziman.get("leg_id"):
        legs[str(ziman.get("leg_id"))] = {"live": True,
                                          "money_link": ziman.get("money_link")}
    return {
        "beat": d.get("beat"),
        "started": d.get("started"),
        "epoch_mode": d.get("epoch_mode"),
        "frozen": bool(d.get("frozen")),
        "halted": d.get("halted"),
        "month": d.get("month"),
        "today": d.get("today"),
        "germline_lag_h": d.get("germline_lag_h"),
        "germline_alert": d.get("germline_alert"),
        "legs": legs,
        "n_legs": len(legs),
    }


def _budget() -> dict:
    """بخش ۲: بودجه — spent/ caps / fugu_quota / halt reason."""
    out: dict = {"spent_today_usd": None, "spent_month_aud": None,
                 "fugu_quota": {}, "monthly_cap": None, "halt_reason": None}
    # telemetry منبعِ صادقانهٔ بودجه‌ست (reconcile از سه منبع). organ-state هم مکمل.
    tl = _read_json(_STATE / "telemetry-latest.json") or {}
    if isinstance(tl, dict):
        out["spent_today_usd"] = (tl.get("brain") or {}).get("today")
        og = tl.get("organ_gate") or {}
        out["spent_month_aud"] = (og.get("month") or {}).get("aud") if isinstance(og, dict) else None
        out["sources"] = list((tl.get("sources") or {}).keys())
        out["fx_aud_per_usd"] = tl.get("fx_aud_per_usd")
    # fugu quota
    fq = _read_json(_STATE / "fugu-quota.json") or {}
    if isinstance(fq, dict):
        cap = int(os.environ.get("FUGU_DAILY_CALL_CAP", "60") or 60)
        used = int(fq.get("used_total") or 0)
        out["fugu_quota"] = {"day": fq.get("day"), "used": used, "cap": cap,
                             "remaining": max(0, cap - used),
                             "consecutive_failures": fq.get("consecutive_failures")}
    # budget-state (ممکن است نباشد — امروز بازسازی شد)
    bs = _read_json(_STATE / "budget" / "budget-state.json") or {}
    if isinstance(bs, dict):
        out.setdefault("spent_today_usd", bs.get("spent_today_usd"))
        out.setdefault("spent_month_aud", bs.get("spent_month_aud"))
        out["halted"] = bool(bs.get("halted"))
    # monthly cap از budgets.yaml (اگر خواندنی باشد)
    try:
        bp = _OPS / "budget" / "budgets.yaml"
        if bp.exists():
            txt = bp.read_text("utf-8", errors="replace")
            # فقط یک نگاهِ سبک — parse کاملِ YAML برای snapshot گران است و وابستگی می‌خواهد
            for line in txt.splitlines():
                ls = line.strip()
                if ls.startswith("cap_monthly") and ":" in ls:
                    out["monthly_cap"] = ls.split(":", 1)[1].strip()
                    break
    except Exception:  # noqa: BLE001
        pass
    return out


def _brain() -> dict:
    """بخش ۳: مغز — local_llm reachable / keys / paid_gate / last paid-call."""
    out: dict = {"local_llm": {}, "keys_present": {}, "paid_gate": {},
                 "last_paid_call": None}
    # local llm: daemon_state.json از مغزِ 4D
    ds = _read_json(_4D_DAEMON) or {}
    if isinstance(ds, dict) and ds:
        out["local_llm"] = {"reachable": True, "ticks": ds.get("total_ticks"),
                            "errors": ds.get("errors_this_run"),
                            "last_tick": ds.get("last_tick_at"),
                            "generation": ds.get("generation")}
    else:
        out["local_llm"] = {"reachable": False,
                            "reason": "4d_system/outputs/daemon_state.json absent/unreadable"}
    # keys_present + paid_gate از model_router. ⚠️ VQ-SNAPSHOT-SIDEFX-001 (۲۰۲۶-۰۸-۰۸):
    # keys_present() درونِ خود env_loader.load_env() را صدا می‌زند که os.environ را با
    # مقادیرِ واقعیِ .env (FUGU_API_KEY، GLM_API_KEY، SAKANA_API_KEY، …) MUTATE می‌کند.
    # این نقضِ قراردادِ «snapshot فقط‌خواندنی، هیچ side-effectای» بود. نسخهٔ نخستِ فیکس
    # یک فهرستِ hardcoded از نامِ secretها داشت — ولی دیپ‌اسکن نشان داد که load_env
    # **۹ کلیدِ دیگر** هم اضافه می‌کند (POCKETSMITH/SAKANA/ZAI/TG_CENTER/GMAIL/…) که
    # در آن فهرست نبودند. فیکسِ صحیح: عکسِ کاملِ os.environ قبل، و بعد از snapshot
    # هر کلیدی که اضافه شده را پس بگیر (بدونِ حدسِ نام — full diff، نه allowlist).
    try:
        import sys as _sys
        if str(_OPS / "cortex") not in _sys.path:
            _sys.path.insert(0, str(_OPS / "cortex"))
        if str(_OPS / "budget") not in _sys.path:
            _sys.path.insert(0, str(_OPS / "budget"))
        _env_before = dict(os.environ)          # عکسِ کامل (نه allowlist)
        from model_router import keys_present, paid_gate  # noqa: WPS433 — lazy
        out["keys_present"] = keys_present()
        # بازگردانِ هر کلیدی که snapshot اضافه کرد (full diff، نه guess)
        for _k in list(os.environ):
            if _k not in _env_before:
                os.environ.pop(_k, None)
        # هر مقداری که عوض شده بود را هم بازگردان (load_env idempotent‌ است ولی احتیاط)
        for _k, _v in _env_before.items():
            if os.environ.get(_k) != _v:
                os.environ[_k] = _v
        ok, why = paid_gate()
        out["paid_gate"] = {"open": bool(ok), "reason": why}
    except Exception as exc:  # noqa: BLE001
        out["keys_present"] = {"status": "unknown", "reason": f"{type(exc).__name__}"}
        out["paid_gate"] = {"status": "unknown", "reason": f"{type(exc).__name__}"}
    # last paid-call از paid-calls.jsonl (اگر هست) — آخرین ردیف
    try:
        pcp = Path(os.environ.get("OCTOPUS_OPS_RUNTIME_DIR", str(_STATE))) / "paid-calls.jsonl"
        if not pcp.exists():
            pcp = _STATE / "paid-calls.jsonl"
        if pcp.exists():
            last = None
            with pcp.open("r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            last = json.loads(line)
                        except Exception:  # noqa: BLE001
                            continue
            if isinstance(last, dict):
                out["last_paid_call"] = {"ts": last.get("ts"), "ok": last.get("ok"),
                                         "tier": last.get("tier"),
                                         "role": last.get("role")}
    except Exception:  # noqa: BLE001
        pass
    return out


def _flags() -> dict:
    """بخش ۴: فلگ‌ها — فقط شمارش (n_armed/n_partial/n_dark/n_total).
    dark = خوانده‌شده در کد ولی در flags-loaded نیست (از flags-loaded-*.json)."""
    procs = ("center", "cortex", "live", "organism", "miniapp-gateway")
    # از flags-loaded-organism به‌عنوانِ مرجع (همان ۲۴۴ اسم) استفاده می‌کنیم؛ اگر نبود
    # اولین موجود. همهٔ پروسه‌ها معمولاً یکسان‌اند (همان flags.cmd).
    ref = None
    for pr in procs:
        d = _read_json(_STATE / f"flags-loaded-{pr}.json") or {}
        if isinstance(d, dict) and d.get("flags"):
            ref = d
            break
    if not isinstance(ref, dict) or not ref.get("flags"):
        return {"status": "unknown", "reason": "no flags-loaded-*.json found"}
    flags = ref.get("flags") or {}
    n_total = len(flags)
    # armed = مقدارش ۱ (یا true/yes)؛ partial = ۰ یا چیزِ دیگر؛ dark = در این مرجع نیست
    n_armed = sum(1 for v in flags.values() if str(v).strip().lower() in ("1", "true", "yes"))
    n_partial = n_total - n_armed
    return {"n_armed": n_armed, "n_partial": n_partial,
            "n_dark": 0, "n_total": n_total,
            "source_pid": ref.get("pid"),
            "source": ref.get("source") or "flags-loaded",
            "note": "n_dark در یک گذرِ مجزای AST محاسبه می‌شود (test_phantom_guards)"}


def _approvals() -> dict:
    """بخش ۵: approvals — count of pending + oldest_pending_age."""
    out: dict = {"pending": 0, "oldest_pending_age_s": None}
    # unified-approval-queue.json منبعِ مرجع است
    uq = _read_json(_STATE / "unified-approval-queue.json") or {}
    if isinstance(uq, dict):
        counts = uq.get("counts") or {}
        if isinstance(counts, dict):
            out["pending"] = int(counts.get("pending") or counts.get("open") or 0)
        items = uq.get("items") or []
        if isinstance(items, list):
            out["total_items"] = len(items)
            # oldest pending: کمینهٔ ts در میانِ itemsِ pending
            now = time.time()
            oldest = None
            for it in items:
                if isinstance(it, dict) and it.get("status") in ("pending", "open", None, ""):
                    ts = it.get("ts") or it.get("created") or it.get("created_at")
                    try:
                        age = now - float(ts)
                        if oldest is None or age < oldest:
                            oldest = age
                    except (TypeError, ValueError):
                        continue
            if oldest is not None:
                out["oldest_pending_age_s"] = round(oldest, 1)
    elif isinstance(uq, list):
        out["pending"] = len(uq)
    return out


def _memory() -> dict:
    """بخش ۶: حافظه — bcm/hebbian/consolidation/self_model/smallest_fix."""
    out: dict = {"bcm": {}, "hebbian": {}, "consolidation": {},
                 "self_model": {}, "smallest_fix": None}
    # BCM: bcm-weights.json (step/beta/keys)
    bcm = _read_json(_STATE / "bcm-weights.json") or {}
    if isinstance(bcm, dict):
        out["bcm"] = {"step": bcm.get("step"), "beta": bcm.get("beta"),
                      "n_keys": len(bcm.get("keys") or {})}
    # Hebbian: _ops/neural/hebbian.json (یک list از associations)
    hb = _read_json(_NEURAL / "hebbian.json")
    if isinstance(hb, list):
        out["hebbian"] = {"n_associations": len(hb)}
    elif isinstance(hb, dict):
        out["hebbian"] = {"n_associations": len(hb.get("associations") or hb.get("pairs") or hb)}
    # Consolidation: _ops/neural/consolidation.json (list از cycles)
    co = _read_json(_NEURAL / "consolidation.json")
    if isinstance(co, list):
        out["consolidation"] = {"n_cycles": len(co)}
    elif isinstance(co, dict):
        out["consolidation"] = {"n_cycles": co.get("n_cycles"),
                                "n_insights": co.get("n_insights") or co.get("insights")}
    # Self-model: _ops/state/cortex/self-model.json
    sm = _read_json(_STATE / "cortex" / "self-model.json") or {}
    if isinstance(sm, dict) and sm:
        out["self_model"] = {"ts": sm.get("ts"), "schema": sm.get("schema"),
                             "n_modules": sm.get("n_modules"),
                             "self_awareness_pct": sm.get("self_awareness_pct"),
                             "version": sm.get("version")}
    else:
        out["self_model"] = {"status": "unknown", "reason": "self-model.json absent"}
    # smallest_fix: _ops/neural/smallest-fix.json (اگر هست)
    sf = _read_json(_NEURAL / "smallest-fix.json")
    if isinstance(sf, dict) and sf:
        out["smallest_fix"] = sf
    return out


def _health() -> dict:
    """بخش ۷: سلامتی — orphan_modules / dead_symbols / dark_gates.
    منبع: reach_probe خروجی می‌دهد ولی آخرین اجرا را از state می‌خوانیم (نه اجرای زنده)."""
    out: dict = {"n_orphan_modules": None, "n_dead_symbols": None,
                 "n_dark_gates": None, "reachable": False}
    # reach_probe آخرین خروجی‌اش را در state نمی‌نویسد؛ یک نگاهِ سبک به orphan_scan
    # آخرین گزارش اگر هست. اگر نبود، unknown صادقانه‌تر از یک عددِ ساختگی است.
    cand = _read_json(_STATE / "orphan-scan-latest.json")
    if isinstance(cand, dict):
        out.update({"n_orphan_modules": cand.get("n_orphans") or cand.get("n_orphan_modules"),
                    "n_dead_symbols": cand.get("n_dead_symbols"),
                    "reachable": True, "source": "orphan-scan-latest.json"})
    if not out["reachable"]:
        out["reason"] = "no orphan/reach-probe state file; run reach_probe for live data"
    return out


def _pid_alive(pid) -> "bool | None":
    """آیا pid هنوز زنده‌ست؟ cross-platform best-effort.

    ⚠️ روی ویندوز `os.kill(pid, 0)` **غلط** است: WinError 87 می‌دهد (signal 0 یک مفهومِ
    POSIX است، ویندوز آن را پشتیبانی نمی‌کند) که ما به‌اشتباه «غیرِزنده» تفسیر می‌کردیم.
    راهِ درست روی ویندوز: `OpenProcess` با `PROCESS_QUERY_LIMITED_INFORMATION` —
    handle≠0 یعنی پروسه موجود. روی POSIX، `os.kill(pid,0)` استاندارد است."""
    if not pid:
        return None
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if h:
                kernel32.CloseHandle(h)
                return True
            return False
        except Exception:  # noqa: BLE001 — fallback اگر ctypes نباشد
            return None
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def _processes() -> dict:
    """بخش ۸: پروسه‌ها — هر ۵ پروسه (pid/boot_ts/alive).
    alive = pid هنوز در جدولِ پروسه‌هاست (تلاشِ سبک، cross-platform best-effort)."""
    procs = ("center", "cortex", "live", "organism", "miniapp-gateway")
    out: dict = {"processes": {}, "n_alive": 0}
    for pr in procs:
        d = _read_json(_STATE / f"flags-loaded-{pr}.json") or {}
        if not isinstance(d, dict) or not d:
            out["processes"][pr] = {"status": "unknown", "reason": "no flags-loaded file"}
            continue
        pid = d.get("pid")
        alive = _pid_alive(pid)
        out["processes"][pr] = {"pid": pid, "alive": alive,
                                "source_mtime": d.get("source_mtime"),
                                "n_flags": len(d.get("flags") or {})}
        if alive:
            out["n_alive"] += 1
    return out


# ─── جمع‌کنندهٔ اصلی ────────────────────────────────────────────────────────────
_SECTIONS = (                        # ترتیب ثابت (قراردادِ API)
    ("organism", _organism),
    ("budget", _budget),
    ("brain", _brain),
    ("flags", _flags),
    ("approvals", _approvals),
    ("memory", _memory),
    ("health", _health),
    ("processes", _processes),
)


def snapshot(use_cache: bool = True) -> dict:
    """همهٔ حالتِ زندهٔ سیستم در یک dict. read-only، $0، fail-soft، cache TTL 5s.

    خروجی همیشه شاملِ هر ۸ بخش است (نمایِ ثابت). هر بخش یا دادهٔ معتبر دارد یا
    `status: unknown` با reason. snapshot هرگز exception پرتاب نمی‌کند."""
    global _cache, _cache_ts
    if use_cache and _cache is not None and (time.time() - _cache_ts) < _CACHE_TTL_S:
        return _cache
    out: dict = {"schema": "control-plane.snapshot.v1",
                 "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "epoch": time.time(),
                 "sections": [name for name, _ in _SECTIONS]}
    for name, fn in _SECTIONS:
        out[name] = _section(name, fn)
    if use_cache:
        _cache = out
        _cache_ts = time.time()
    return out


if __name__ == "__main__":           # CLI: python -X utf8 control_plane.py
    print(json.dumps(snapshot(use_cache=False), ensure_ascii=False, indent=2))
