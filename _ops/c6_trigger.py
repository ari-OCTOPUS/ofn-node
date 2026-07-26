#!/usr/bin/env python3
"""c6_trigger.py — runtime trigger برای حلقهٔ self-improvement C6 (مرحلهٔ ۴).

تولید مثل = خودبهبودیِ کد. این trigger روزی یک‌بار (از daily tick) صدا زده می‌شود،
یک فرضیه از `_ops/state/c6/hypothesis-queue.jsonl` برمی‌دارد، آن را به‌صورتِ یک
آزمایشِ sandbox اجرا می‌کند، و نتیجه را به‌عنوانِ RFC card (propose-only) به مالک
می‌دهد. **هیچِ auto-apply/merge/deploy** (governance مرزِ نهایی).

گیت‌ها (همگی لازم):
  - OCTOPUS_WIRE_C6_RESEARCH (env، پیش‌فرض خاموش)
  - ACTIVATION-C6-RESEARCH.flag (فایلِ مالک — فقط خودش می‌سازد)
  - organ_gate ARCHITECT_SYS (از داخلِ run_experiment اگر پولی باشد)
  - governance: فقط test_in_sandbox مجاز است.
سقف: ۱ آزمایش/روز (daily tick)، AU$0.50، ۵۰k token، ۱۲۰s.

صدا زدن:
  from c6_trigger import c6_research_beat
  c6_research_beat(state_dir=..., channel=..., beat=N)

fail-soft: هر خطا → alert + ادامه (هرگز daily tick را نمی‌کشد).
"""
from __future__ import annotations

import calendar
import gc
import hashlib
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "outcomes"), str(_HERE / "memory"), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

ENV_FLAG = "OCTOPUS_WIRE_C6_RESEARCH"
ACT_FLAG = opslib.OPS / "ACTIVATION-C6-RESEARCH.flag"
QUEUE = opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl"
LEDGER = opslib.STATE_DIR / "c6" / "research-ledger.jsonl"
# سقفِ روزانهٔ محافظه‌کارانه (نیمی از ARCHITECT_SYS floor، با headroom).
DAILY_BUDGET = {"cost_aud": 0.50, "time_s": 120, "tokens": 50000, "max_experiments": 1}

# ── C1 (2026-07-25): پارامترهای بنچ‌مارکِ صادق ────────────────────────────────
# نسخهٔ قبل یک readِ تکی را با time.time می‌سنجید و با baseline_ms=5.0 که **خودِ فرضیه**
# اعلام کرده بود مقایسه می‌کرد → gain ≈ ۴.۹ms هر روز، supported=True بی‌قید، و کارتِ
# «accepted» بدونِ ذره‌ای محتوا. درسِ پرداخت‌شدهٔ این vault: میکروبنچ در سه جهت دروغ
# می‌گوید — cacheِ گرم/ترتیب، مکثِ GC، و مقایسهٔ دو زیرمجموعهٔ جدا. پس اینجا: هر دو بازو
# روی **همان فایل** و در **همان پروسه**، جفت‌شده، با ترتیبِ دورانی، gc خاموش،
# median کنارِ mean، و ادعای اصلیِ **مکانیزمی** (شمارشِ parse) نه ساعتِ دیواری.
BENCH_PAIRS = 24      # مضربِ ۳ → هر بازو دقیقاً برابر در هر موقعیتِ سه‌تایی می‌نشیند
BENCH_INNER = 12      # «tick»های داخلِ هر اندازه‌گیری
BENCH_WARMUP = 2      # اجرایِ گرم‌کنندهٔ بی‌زمان، **یکسان** برای هر دو بازو
SIGN_ALPHA = 0.01     # سقفِ pِ آزمونِ علامتِ دقیق (یک‌طرفه، توزیع‌آزاد)
IQR_FACTOR = 1.5      # اثر ≥ ۱.۵×IQRِ همان اختلاف‌های جفتی (ثابتِ حصارِ Tukey)
NOISE_FACTOR = 3.0    # و ≥ ۳× کفِ نویزِ **اندازه‌گیری‌شده** از کنترلِ A/A
MAX_ATTEMPTS = 3      # تلاشِ دوبارهٔ فرضیهٔ «نامعلوم» (نه ابطال‌شده)
C6_RUNNING_STALE_H = float(os.environ.get("OCTOPUS_C6_RUNNING_STALE_H", "48"))

# معیارهای ابطال — دیگر تزئینی نیستند: دقیقاً همین‌ها در _accept_bench اجرا می‌شوند.
_FALSIFICATION = [
    "candidate performs the same number of parse operations per run as baseline "
    "(no mechanism delta) — hardware-independent, checked first",
    "paired sign test p > 0.01 (improvement indistinguishable from a coin flip)",
    "median paired delta < 1.5 x IQR of the same paired deltas",
    "median paired delta < 3 x measured A/A noise floor (same run, same machine)",
    "candidate output differs from baseline output (wrong is not fast)",
]


def flag_on() -> bool:
    """هر دو گیت لازم: env flag + فایلِ فعال‌سازیِ مالک."""
    if not str(os.environ.get(ENV_FLAG, "")).strip().lower() in ("1", "true", "yes", "on"):
        return False
    if not ACT_FLAG.exists():
        return False
    return True


def _queue_row_id(row: dict) -> str:
    try:
        hid = str(row.get("id") or "").strip()
        if hid:
            return hid
        probe = str(row.get("probe") or "")
        subject = str(row.get("subject") or row.get("hypothesis") or "")
        return "c6-" + hashlib.sha256(f"{probe}|{subject}".encode("utf-8")).hexdigest()[:12]
    except Exception:  # noqa: BLE001
        return ""


def _iso_epoch_utc(ts: str) -> float:
    """ISO timestamp را به UTC epoch تبدیل می‌کند (ledger/queue UTC هستند، ساعت محلی سیدنی نیست)."""
    try:
        import datetime as _dt
        t = _dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if t.tzinfo is not None:
            t = t.astimezone(_dt.timezone.utc).replace(tzinfo=None)
        return float(calendar.timegm(t.timetuple()))
    except Exception:  # noqa: BLE001
        return 0.0


def _pop_next_hypothesis() -> "dict | None":
    """اولین فرضیهٔ status=PENDING را می‌گیرد و idempotent-safe می‌کند؛ RUNNINGهای stale را
    بدون verdict به ABANDONED می‌برد و برای ردیف‌های قدیمیِ بی‌id، id محتوامحور backfill می‌کند."""
    if not QUEUE.exists():
        return None
    try:
        lines = QUEUE.read_text("utf-8").splitlines()
    except Exception:  # noqa: BLE001
        return None
    now = time.time()
    out, found, stale_changed = [], None, False
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            out.append(ln)   # preserve malformed line
            continue
        if d.get("status") == "RUNNING":
            age_h = (now - _iso_epoch_utc(d.get("taken_at") or d.get("claimed_at"))) / 3600.0
            if age_h >= C6_RUNNING_STALE_H:
                d["status"] = "ABANDONED"
                d["abandoned_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                d["abandoned_reason"] = "stale-running"
                stale_changed = True
        if found is None and d.get("status") == "PENDING":
            d["id"] = _queue_row_id(d)
            d["status"] = "RUNNING"
            d["taken_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            found = dict(d)
        out.append(json.dumps(d, ensure_ascii=False))
    if found is not None or stale_changed:
        try:
            QUEUE.parent.mkdir(parents=True, exist_ok=True)
            QUEUE.write_text("\n".join(out) + "\n", encoding="utf-8")
        except Exception:  # noqa: BLE001
            return None
    return found


def _build_contract(h: dict) -> dict:
    """یک spec ساده از hypothesis می‌سازد (caller بعداً make_contract می‌زند)."""
    return {
        "question": str(h.get("question", "Can we improve a self-process?"))[:500],
        "hypothesis": str(h.get("hypothesis", ""))[:500],
        # attempt داخلِ stop_condition می‌آید تا هر تلاشِ نو contract_idِ نو بگیرد؛ وگرنه
        # گاردِ idempotencyِ research_loop (find_completed) اجرای دوباره را کوتاه می‌کند و
        # یک روزِ پرنویز فرضیه را برای همیشه می‌کُشد.
        "stop_condition": (str(h.get("stop_condition", "one paired A/B bench run"))
                           + f" | attempt {int(h.get('attempt', 1) or 1)}")[:300],
        "verifier": str(h.get("verifier", "compare_frozen_baselines"))[:200],
        "expected_artifact": str(h.get(
            "expected_artifact",
            "paired A/B bench record: measured baseline median, paired delta "
            "median+mean+IQR, A/A noise floor, sign-test p, parse-op counters"))[:200],
        "falsification_criteria": h.get("falsification_criteria", list(_FALSIFICATION)),
        "budget": DAILY_BUDGET,
        "tools": h.get("tools", ["test_in_sandbox", "compare_frozen_baselines"]),
        "created_at_hint": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def c6_research_beat(*, state_dir: str, channel=None, beat: int = 0) -> dict:
    """روزانه: یک فرضیه → آزمایش → RFC card. پشتِ دو گیت. fail-soft. صفر auto-apply."""
    if not flag_on():
        return {"ran": False, "reason": "flag-off"}
    try:
        import research_contract as _rc
        import research_loop as _rl
        import memory_store as _msx
        import gate as _gx
        import decision_receipt as _drx
        import outcome_store as _osx
        import learning_gate as _lg
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"c6_research_beat import failed: {type(e).__name__}: {e}"])
        return {"ran": False, "reason": f"import-failed:{type(e).__name__}"}

    try:
        import c6_producer as _cp
        _cp.produce(QUEUE)
    except Exception as _pe:  # noqa: BLE001 — producer نباید beat را بکشد
        opslib.alert([f"c6 producer failed (fail-soft): {type(_pe).__name__}: {_pe}"])

    # کارتِ بدهکار قبل از هر چیز: این باید **بالاتر** از early-returnِ زیر باشد،
    # چون دقیقاً همان early-return بود که کارتِ ۲۵ جولای را برای همیشه دفن کرد.
    _redeliv = redeliver_undelivered_cards(channel)

    h = _pop_next_hypothesis()
    if h is None:
        return {"ran": False, "reason": "no-pending-hypothesis",
                "redelivered": _redeliv.get("sent", 0)}

    spec = _build_contract(h)
    try:
        contract = _rc.make_contract(spec)
    except Exception as e:  # noqa: BLE001 — فرضیهٔ بد نباید daily tick را بکشد
        opslib.alert([f"c6 contract invalid (hypothesis closed): {type(e).__name__}: {e}"])
        _mark_hypothesis(str(h.get("id") or ""), "contract-invalid", False)
        return {"ran": False, "reason": f"contract-invalid:{type(e).__name__}"}

    # experiment_fn + verifier_fn: از hypothesis.kind مشتق می‌شوند.
    experiment_fn, verifier_fn, bench_box = _derive_fns(h, contract)

    sd = Path(state_dir)
    # storesِ واقعی (production learning stack — همان مسیرِ verdict).
    try:
        mdir = sd / "memory"; mdir.mkdir(parents=True, exist_ok=True)
        rdir = sd / "receipts"; rdir.mkdir(parents=True, exist_ok=True)
        odir = sd / "outcomes"; odir.mkdir(parents=True, exist_ok=True)
        _mem = _msx.MemoryStore(path=mdir / "memory.db")
        _rcp = _drx.DecisionReceiptStore(rdir / "receipts.db")
        _outc = _osx.OutcomeStore(path=odir / "outcomes.db")
        _gate = _gx.MemoryGate(_mem)
        budget = _rl.Budget(contract["budget"])
        ledger = _rl.ResearchLedger(LEDGER)
        result = _rl.run_experiment(
            contract=contract, experiment_fn=experiment_fn, verifier_fn=verifier_fn,
            budget=budget, ledger=ledger,
            receipt_store=_rcp, memory_gate=_gate, outcome_store=_outc,
            state_dir=str(sd), held_out_eval=_lg.fast_ledger_eval,
            cost_aud=0.0, tokens=0)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"c6 run_experiment failed: {type(e).__name__}: {e}"])
        _mark_hypothesis(str(h.get("id") or ""), "run-failed", False)
        return {"ran": False, "reason": f"run-failed:{type(e).__name__}"}

    verdict = result.get("verdict", "?")
    # M3: record the unified reproduction lifecycle (fail-soft; derives, holds no
    # authority). ADMITTED needs the memory gate; TRANSPLANTED (generational birth) is
    # an owner tap ONLY — never emitted here (merge_or_deploy stays FORBIDDEN).
    try:
        import c6_state_machine as _sm
        _cid = contract.get("contract_id", f"c6-{beat}")
        _sm.transition(state_dir=str(sd), contract_id=_cid, to_state="RUNNING",
                       result=result, receipt_store=_rcp)
        _final = _sm.derive(result)
        if _final in ("REJECTED", "QUARANTINED", "TERMINATED", "VERIFIED_NOT_ADMITTED"):
            _sm.transition(state_dir=str(sd), contract_id=_cid, to_state=_final,
                           result=result, receipt_store=_rcp)
        elif _final in ("ADMITTED", "PENDING_ADMISSION"):
            _sm.transition(state_dir=str(sd), contract_id=_cid, to_state="VERIFIED",
                           result=result, receipt_store=_rcp)
            _sm.transition(state_dir=str(sd), contract_id=_cid,
                           to_state="PENDING_ADMISSION", result=result, receipt_store=_rcp)
    except Exception as _e:  # noqa: BLE001 — recorder never kills the beat
        opslib.alert([f"c6 state-machine record skipped: {type(_e).__name__}: {_e}"])
    # نتیجه → RFC card به مالک (فقط اگر چیز ارزشمندی برای گفتن باشد).
    summary = _summarize(h, result, bench_box)
    delivered = False
    # اگر کانال داده نشد (organism آن را پاس نمی‌دهد)، lazy از wiring بساز.
    _chan = channel
    if _chan is None:
        try:
            import wiring as _wiring
            _chan = _wiring.make_telegram_channel()
        except Exception:  # noqa: BLE001
            _chan = None
    if _chan is not None and hasattr(_chan, "rfc_card"):
        try:
            cid = contract.get("contract_id", f"c6-{beat}")[:60]
            # `f"c6-{cid}"` با cid تا ۶۰ کاراکتر، callback را به ۹۸ بایت می‌بُرد
            # (سقف ۶۴) → تلگرام ۴۰۰ می‌داد و کارت بی‌صدا گم می‌شد. 2026-07-26.
            delivered = _chan.rfc_card(rfc_id=_short_rfc_id("c6", cid),
                                       summary=summary[:800])
        except Exception as e:  # noqa: BLE001 — کارت نباید beat را بکشد
            opslib.alert([f"c6 rfc_card delivery failed: {type(e).__name__}: {e}"])
    # بستنِ hypothesis با نتیجه
    # «نامعلوم» (خطای بنچ / آلودگیِ outlier) ≠ «ابطال‌شده»: فقط تا سقفِ MAX_ATTEMPTS
    # دوباره صف می‌شود، بعد بسته. ابطالِ واقعی هرگز requeue نمی‌شود.
    _acc = (bench_box or {}).get("accept") or {}
    _requeue = bool(_acc.get("inconclusive")) and verdict == "rejected"
    _mark_hypothesis(h.get("id") or contract.get("contract_id"), verdict, delivered,
                     requeue=_requeue)
    return {"ran": True, "verdict": verdict, "delivered": delivered,
            "inconclusive": bool(_acc.get("inconclusive")), "summary": summary}


def _derive_fns(h: dict, contract: dict):
    """experiment_fn + verifier_fn + boxِ اندازه‌گیری. C1 را حفظ می‌کند و C2 را می‌افزاید.
    kind='mechanism_count' یک probe شمارشیِ read-only است: نقص بازتولید شد/نشد را می‌سنجد؛
    آن را «بهبودِ انجام‌شده» نمی‌داند و count<0 را unsupported+inconclusive می‌کند."""
    kind = str(h.get("kind", "micro_benchmark"))
    box: dict = {}

    # romajan_claim is mechanism_count with an explicit lab provenance label
    if kind in ("mechanism_count", "romajan_claim"):
        probe = str(h.get("probe") or "")
        floor = int(h.get("floor", 0) or 0)

        def _measure() -> dict:
            try:
                import c6_probes as _cp
                fn = (_cp.PROBES.get(probe) or {}).get("measure")
                if not callable(fn):
                    return {"count": -1, "unit": "count", "detail": "unknown-probe"}
                rec = fn()
                if not isinstance(rec, dict):
                    return {"count": -1, "unit": "count", "detail": "bad-probe-result"}
                return rec
            except Exception as e:  # noqa: BLE001
                return {"count": -1, "unit": "count",
                        "detail": f"probe-error:{type(e).__name__}"}

        def experiment_fn(c, *, _h=h):
            rec = _measure()
            count = int(rec.get("count", -1)) if isinstance(rec, dict) else -1
            gain = 0.0
            if count > floor:
                gain = max(0.0, min(1.0, (count - floor) / max(count, 1)))
            out = {"schema": "c6-mechanism-count.v1", "probe": probe,
                   "count": count, "unit": rec.get("unit", "count"),
                   "floor": floor, "detail": rec.get("detail", ""),
                   "gain": gain, "same_output": True}
            box["bench"] = out
            return out

        def verifier_fn(c, result):
            count = int((result or {}).get("count", -1)) if isinstance(result, dict) else -1
            gain = float((result or {}).get("gain", 0.0)) if isinstance(result, dict) else 0.0
            if count < 0:
                acc = {"supported": False, "benchmark_gain": 0.0,
                       "inconclusive": True, "reasons": ["E-MEASURE: probe failed"],
                       "criteria": {"measured_count": count, "floor": floor,
                                    "relative_gain": 0.0}}
            elif count > floor:
                acc = {"supported": True, "benchmark_gain": gain,
                       "inconclusive": False, "reasons": [],
                       "criteria": {"measured_count": count, "floor": floor,
                                    "relative_gain": round(gain, 4)}}
            else:
                acc = {"supported": False, "benchmark_gain": 0.0,
                       "inconclusive": False,
                       "reasons": ["F-MEASURE: defect not reproduced"],
                       "criteria": {"measured_count": count, "floor": floor,
                                    "relative_gain": 0.0}}
            box["accept"] = acc
            ev = {"supported": acc["supported"], "gain": round(acc["benchmark_gain"], 4),
                  "inconclusive": acc["inconclusive"], "why": acc["reasons"],
                  "m": acc["criteria"]}
            return {"supported": bool(acc["supported"]),
                    "evidence": json.dumps(ev, ensure_ascii=False)[:500],
                    "benchmark_gain": float(acc["benchmark_gain"]),
                    "risk": 0.1}

        return experiment_fn, verifier_fn, box

    def experiment_fn(c, *, _h=h):
        try:
            rec = _paired_bench(_h)
        except Exception as e:  # noqa: BLE001 — بنچِ خراب هرگز daily tick را نمی‌کشد
            rec = {"schema": "c6-paired-bench.v1",
                   "error": f"{type(e).__name__}: {e}",
                   "parse_calls_saved_per_run": 0.0}
        rec["kind"] = kind
        box["bench"] = rec
        return rec

    def verifier_fn(c, result):
        acc = _accept_bench(result)
        box["accept"] = acc
        # ترتیبِ کلیدها عمدی است: مهم‌ها اول، چون evidence در ledger برش می‌خورد.
        ev = {"supported": acc["supported"], "gain": round(acc["benchmark_gain"], 4),
              "inconclusive": acc["inconclusive"], "why": acc["reasons"],
              "m": acc["criteria"]}
        return {"supported": bool(acc["supported"]),
                "evidence": json.dumps(ev, ensure_ascii=False)[:500],
                "benchmark_gain": float(acc["benchmark_gain"]),
                "risk": 0.1}

    return experiment_fn, verifier_fn, box


# ── بنچ‌مارکِ جفت‌شده (C1) ────────────────────────────────────────────────────

def _bench_payload_path(h: dict) -> "Path | None":
    """payloadِ بنچ همیشه **داخلِ** STATE_DIR است (fail-closed)؛ پیش‌فرض ORGANISM-STATE.json."""
    try:
        base = Path(opslib.STATE_DIR).resolve()
        p = (base / str(h.get("bench_path") or "ORGANISM-STATE.json")).resolve()
        p.relative_to(base)              # هر مسیرِ بیرون از state → ValueError → None
        return p if (p.is_file() and p.stat().st_size > 0) else None
    except Exception:  # noqa: BLE001
        return None


def _new_ops() -> dict:
    return {"read_calls": 0, "parse_calls": 0, "stat_calls": 0, "bytes_read": 0, "runs": 0}


def _per(o: dict, key: str) -> float:
    return (float(o.get(key, 0)) / o["runs"]) if o.get("runs") else 0.0


def _arm_reparse(path, n: int, ops: dict):
    """بازوی پایه (baseline، همان چیزی که امروز هر tick می‌کند): read + parseِ دوباره."""
    obj = None
    for _ in range(n):
        raw = path.read_bytes()
        ops["read_calls"] += 1
        ops["bytes_read"] += len(raw)
        obj = json.loads(raw.decode("utf-8"))
        ops["parse_calls"] += 1
    return obj


def _arm_cached(path, n: int, ops: dict):
    """بازوی نامزد: یک parse، بعد فقط stat (mtime_ns+size) برای اعتبارسنجیِ cache.
    cache در هر اندازه‌گیری از نو ساخته می‌شود → هزینهٔ missِ اول **داخلِ** همین بازو
    حساب می‌شود (محافظه‌کارانه به نفعِ baseline)."""
    sig = obj = None
    for _ in range(n):
        st = path.stat()
        ops["stat_calls"] += 1
        cur = (st.st_mtime_ns, st.st_size)
        if cur != sig:
            raw = path.read_bytes()
            ops["read_calls"] += 1
            ops["bytes_read"] += len(raw)
            obj = json.loads(raw.decode("utf-8"))
            ops["parse_calls"] += 1
            sig = cur
    return obj


def _sign_test_p(wins: int, n: int) -> float:
    """pِ دقیقِ یک‌طرفهٔ آزمونِ علامت: زیرِ فرضِ صفر، علامتِ هر جفت یک شیر-یا-خط است.
    توزیع‌آزاد — به نرمال‌بودنِ زمان‌ها (که هرگز نیست) تکیه نمی‌کند."""
    if n <= 0:
        return 1.0
    w = max(0, min(int(wins), int(n)))
    return sum(math.comb(int(n), k) for k in range(w, int(n) + 1)) / float(1 << int(n))


def _iqr(vals) -> float:
    if len(vals) < 2:
        return 0.0
    q = statistics.quantiles(sorted(vals), n=4, method="inclusive")
    return float(q[2] - q[0])


def _paired_bench(h: dict) -> dict:
    """بنچِ جفت‌شدهٔ A/B + کنترلِ A/A، روی **همان ورودی** و در **همان اجرا**.

    طرح: در هر جفت سه اندازه‌گیری (A، B، A′) با ترتیبِ **دورانی** انجام می‌شود، پس هر
    برچسب دقیقاً به‌اندازهٔ برابر در هر موقعیت می‌نشیند → اثرِ ترتیب/گرم‌شدن/drift خنثی.
    A′ همان بازوی A است: توزیعِ |A′−A| کفِ نویزِ «اختلافِ بدونِ علت» را **اندازه می‌گیرد**
    (به‌جای حدس زدنش). gc پیش از ناحیهٔ زمان‌دار خاموش و در finally برمی‌گردد.
    ساعت: perf_counter_ns (monotonic، غیرقابلِ تنظیم) — نه time.time که adjustable است.
    baseline **اندازه‌گیری** می‌شود؛ هر baseline_msِ اعلامیِ فرضیه فقط به‌عنوانِ شاهدِ
    تخلف ثبت و **مصرف نمی‌شود**."""
    arms = h.get("_arms")   # تزریقِ in-process (فقط تست) — JSONL هرگز callable ندارد
    if arms is not None:
        if not (isinstance(arms, (list, tuple)) and len(arms) == 2
                and all(callable(x) for x in arms)):
            return {"schema": "c6-paired-bench.v1", "error": "bad-_arms",
                    "parse_calls_saved_per_run": 0.0}
        arm_a, arm_b = arms
    else:
        arm_a, arm_b = _arm_reparse, _arm_cached

    path = _bench_payload_path(h)
    if path is None:
        return {"schema": "c6-paired-bench.v1", "error": "no-payload",
                "parse_calls_saved_per_run": 0.0}

    n_pairs = max(6, min(int(h.get("bench_pairs", BENCH_PAIRS)), 120))
    n_pairs -= n_pairs % 3                       # مضربِ ۳ = توازنِ دقیقِ موقعیت‌ها
    inner = max(2, min(int(h.get("bench_inner", BENCH_INNER)), 200))

    ops = {"a": _new_ops(), "b": _new_ops(), "a2": _new_ops()}
    fns = {"a": arm_a, "b": arm_b, "a2": arm_a}   # a2 = همان بازوی A → کنترلِ A/A
    out: dict = {}
    ta, tb, taa = [], [], []

    warm = _new_ops()
    for _ in range(max(0, BENCH_WARMUP)):        # گرم‌کردنِ **برابر** برای هر دو بازو
        arm_a(path, inner, warm)
        arm_b(path, inner, warm)

    labels = ("a", "b", "a2")
    gc_was = gc.isenabled()
    gc.collect()
    gc.disable()
    try:
        for i in range(n_pairs):
            k = i % 3
            order = labels[k:] + labels[:k]      # چرخشِ موقعیت‌ها
            t = {}
            for lab in order:
                o = ops[lab]
                t0 = time.perf_counter_ns()
                res = fns[lab](path, inner, o)
                t1 = time.perf_counter_ns()
                o["runs"] += 1
                t[lab] = (t1 - t0) / 1e6
                out[lab] = res
            ta.append(t["a"])
            tb.append(t["b"])
            taa.append(abs(t["a2"] - t["a"]))
    finally:
        if gc_was:
            gc.enable()

    d = [x - y for x, y in zip(ta, tb)]           # اختلافِ **جفتی**، نه دو زیرمجموعهٔ جدا
    pa, pb = _per(ops["a"], "parse_calls"), _per(ops["b"], "parse_calls")
    wins = sum(1 for x in d if x > 0.0)          # مساوی = بُرد نیست (محافظه‌کارانه)
    return {
        "schema": "c6-paired-bench.v1",
        "design": ("paired A/B on identical input, same process, rotating order, "
                   "A/A control, gc disabled, perf_counter_ns"),
        "payload_bytes": path.stat().st_size,
        "n_pairs": n_pairs, "inner_ticks": inner,
        "gc_disabled_during_timing": True,
        "clock": "perf_counter_ns",
        # ── baselineِ **اندازه‌گیری‌شده** (هیچ عددِ هاردکدی در مقایسه دخالت ندارد) ──
        "baseline_median_ms": statistics.median(ta),
        "baseline_mean_ms": statistics.fmean(ta),
        "candidate_median_ms": statistics.median(tb),
        "candidate_mean_ms": statistics.fmean(tb),
        "delta_median_ms": statistics.median(d),
        "delta_mean_ms": statistics.fmean(d),
        "delta_iqr_ms": _iqr(d),
        "wins": wins, "n": len(d), "sign_test_p": _sign_test_p(wins, len(d)),
        "noise_floor_ms": statistics.median(taa),   # A/A = «اختلاف بدونِ علت»
        # ── ادعای مکانیزمی (مستقل از سخت‌افزار) ──
        "parse_calls_per_run_a": pa, "parse_calls_per_run_b": pb,
        "parse_calls_saved_per_run": pa - pb,
        "bytes_read_per_run_a": _per(ops["a"], "bytes_read"),
        "bytes_read_per_run_b": _per(ops["b"], "bytes_read"),
        "stat_calls_per_run_b": _per(ops["b"], "stat_calls"),
        "same_output": bool(out.get("a") == out.get("b")),
        # شاهدِ تخلف: اگر فرضیه baseline اعلام کرده بود، ثبت شد ولی **مصرف نشد**.
        "declared_baseline_ms_ignored": h.get("baseline_ms"),
    }


def _accept_bench(rec: dict) -> dict:
    """معیارِ پذیرش. **هر هفت شرط لازم است** و هرکدام مستقلاً می‌کُشد:
      F-OUTPUT  خروجیِ دو بازو یکسان باشد (سریعِ غلط، سریع نیست)
      F-MECH    (ادعای اصلی، مستقل از سخت‌افزار) نامزد در هر اجرا parseِ کمتر بزند.
                فرضِ صفر (دو بازوی یکسان) دقیقاً همین‌جا می‌میرد — بدونِ هیچ وابستگی
                به شانسِ ساعت. این تنها ادعایی است که روی هر ماشینی همان می‌ماند.
      F-SIGN    pِ آزمونِ علامتِ دقیق ≤ ۰.۰۱ → حداکثر ۱٪ از اجراهای فرضِ صفر شانسی رد شوند
      F-ZERO    میانهٔ اختلافِ جفتی > ۰
      F-IQR     اثر ≥ ۱.۵×IQRِ **همان** اختلاف‌ها (حصارِ Tukey): زیرِ فرضِ صفر میانه ≈ ۰
                ولی IQR > ۰ است، پس نسبت ≈ ۰؛ ۱.۵ یعنی اثر بر کلِ پراکندگیِ میانیِ
                همان اندازه‌گیری غلبه دارد. هیچ آستانهٔ ثابتِ میلی‌ثانیه‌ای در کار نیست.
      F-NOISE   اثر ≥ ۳× کفِ نویزِ کنترلِ A/A. این شرط حالتِ منحطِ IQR=0 (کوانتیزاسیونِ
                ساعت) را می‌بندد و «۳σ»ی robust است که با میانهٔ قدرمطلق‌ها سنجیده شده.
      E-SKEW    mean≈median (وگرنه نتیجه outlier-محور است → **نامعلوم**، نه پذیرفته)
    tagهای E-* = کیفیتِ اندازه‌گیری (inconclusive → تلاشِ دوباره)؛ F-* = ابطالِ واقعی.
    benchmark_gain **بی‌بعد** است (نسبتِ بهبود ۰..۱) تا با risk/cost در governance.utility
    هم‌مقیاس باشد — میلی‌ثانیهٔ خام آن‌جا معنا ندارد و همان بود که U را باد می‌کرد."""
    rec = rec or {}
    reasons = []

    def _f(x) -> float:
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0

    if rec.get("error"):
        # خطای اندازه‌گیری = کیفیتِ داده، نه ابطالِ فرضیه. اگر ادامه دهیم، دلایلِ F-*
        # هم ساخته می‌شوند در حالی که صرفاً پیامدِ نبودِ داده‌اند — و «نامعلوم» را به
        # «ابطال» تبدیل می‌کنند، یعنی فرضیه برای همیشه بسته می‌شود بدونِ آنکه یک‌بار
        # واقعاً سنجیده شده باشد. (این باگ را تستِ خودِ همین پچ گرفت.)
        return {"supported": False, "benchmark_gain": 0.0, "inconclusive": True,
                "reasons": [f"E-BENCH: {rec.get('error')}"],
                "criteria": {"parse_calls_saved_per_run":
                             _f(rec.get("parse_calls_saved_per_run")),
                             "sign_test_p": None, "delta_median_ms": None,
                             "delta_mean_ms": None, "delta_iqr_ms": None,
                             "noise_floor_ms": None, "baseline_median_ms": None,
                             "n": rec.get("n"), "wins": rec.get("wins"),
                             "relative_gain": 0.0}}
    if not rec.get("same_output", False):
        reasons.append("F-OUTPUT: candidate output != baseline output")
    saved = _f(rec.get("parse_calls_saved_per_run"))
    if saved <= 0.0:
        reasons.append("F-MECH: candidate performs no fewer parse ops per run")
    p = _f(rec.get("sign_test_p")) if rec.get("sign_test_p") is not None else 1.0
    if p > SIGN_ALPHA:
        reasons.append(f"F-SIGN: sign-test p={p:.4g} > {SIGN_ALPHA}")
    med, mean = _f(rec.get("delta_median_ms")), _f(rec.get("delta_mean_ms"))
    iqr, noise = _f(rec.get("delta_iqr_ms")), _f(rec.get("noise_floor_ms"))
    base = _f(rec.get("baseline_median_ms"))
    if med <= 0.0:
        reasons.append("F-ZERO: median paired delta <= 0")
    if med < IQR_FACTOR * iqr:
        reasons.append(f"F-IQR: effect {med:.4g}ms < {IQR_FACTOR}x IQR {iqr:.4g}ms")
    if med < NOISE_FACTOR * noise:
        reasons.append(f"F-NOISE: effect {med:.4g}ms < {NOISE_FACTOR}x A/A noise {noise:.4g}ms")
    if abs(mean - med) > max(0.5 * abs(med), IQR_FACTOR * iqr, noise):
        reasons.append(f"E-SKEW: mean {mean:.4g}ms vs median {med:.4g}ms — outlier-driven")

    supported = not reasons
    gain = max(0.0, min(1.0, med / base)) if (supported and base > 0.0) else 0.0
    inconclusive = bool(reasons) and all(
        str(r).split(":", 1)[0] in ("E-BENCH", "E-SKEW") for r in reasons)
    return {"supported": supported, "benchmark_gain": gain,
            "inconclusive": inconclusive, "reasons": reasons[:6],
            "criteria": {"parse_calls_saved_per_run": saved, "sign_test_p": p,
                         "delta_median_ms": med, "delta_mean_ms": mean,
                         "delta_iqr_ms": iqr, "noise_floor_ms": noise,
                         "baseline_median_ms": base, "n": rec.get("n"),
                         "wins": rec.get("wins"), "relative_gain": round(gain, 4)}}


def _summarize(h: dict, result: dict, box: dict = None) -> str:
    """کارتِ مالک باید **عدد** داشته باشد، نه فقط verdict (باگِ C1: «accepted» بی‌محتوا)."""
    v = result.get("verdict", "?")
    q = str(h.get("question", "?"))[:90]
    reason = str(result.get("reason", ""))[:110]
    mid = result.get("memory_id", "")
    lines = [f"C6 آزمایشِ خودبهبودی — verdict: {v}", f"پرسش: {q}", f"دلیل: {reason}"]
    try:
        acc = (box or {}).get("accept") or {}
        cr = acc.get("criteria") or {}

        def _n(k, d=0.0):
            try:
                return float(cr.get(k, d))
            except (TypeError, ValueError):
                return d

        if cr and str(h.get("kind", "micro_benchmark")) == "mechanism_count":
            mc = _n("measured_count", -1.0)
            lines.append(
                f"سنجهٔ شمارشیِ read-only: measured={int(mc)} · floor={int(_n('floor'))} · "
                f"gain={_n('relative_gain'):.2f}")
            lines.append("این سنجه فقط بازتولیدِ نقص را اندازه می‌گیرد.")
        elif cr:
            lines.append(
                "اندازه‌گیریِ جفت‌شده (همان ورودی، gc خاموش): "
                f"baselineِ اندازه‌گیری‌شده {_n('baseline_median_ms'):.3f}ms · "
                f"دلتا median {_n('delta_median_ms'):.3f} / mean {_n('delta_mean_ms'):.3f}ms · "
                f"IQR {_n('delta_iqr_ms'):.3f}ms · کفِ نویزِ A/A {_n('noise_floor_ms'):.3f}ms · "
                f"علامت {cr.get('wins')}/{cr.get('n')} (p={_n('sign_test_p', 1.0):.3g})")
            lines.append(
                f"مکانیزم (مستقل از سخت‌افزار): {_n('parse_calls_saved_per_run'):.1f} "
                f"parseِ کمتر در هر اجرا · بهبودِ نسبی {100 * _n('relative_gain'):.1f}%")
        if acc.get("reasons"):
            tail = "؛ ".join(str(x) for x in acc["reasons"])[:180]
            lines.append(("نامعلوم (کیفیتِ اندازه‌گیری): " if acc.get("inconclusive")
                          else "ردِ معیار: ") + tail)
    except Exception:  # noqa: BLE001 — خلاصه هرگز beat را نمی‌کشد
        pass
    if mid:
        lines.append(f"خاطره: {mid}")
    lines.append("این یک proposal است؛ اعمال فقط با رأیِ شما.")
    return "\n".join(lines)


REDELIVER_FLAG = "OCTOPUS_C6_REDELIVER"
REDELIVER_CAP = 3          # سقفِ هر tick — صفِ عقب‌افتاده نباید به storm تبدیل شود

# سقفِ callback_data در تلگرام ۶۴ بایت است. کارتِ RFC می‌سازد:
#     rfc:<verb>:<rfc_id>:<token>   →  10 + len(rfc_id) + 1 + 24
# پس rfc_id عملاً ≤ ۲۹ بایت. با `contract_id[:60]`ِ قبلی این ۹۸ بایت می‌شد و
# تلگرام کلِ پیام را ۴۰۰ می‌کرد — `send_text` استثنا را می‌بلعید و False می‌داد،
# بی‌هیچ ردی در هیچ لاگ. یعنی مسیرِ کارتِ C6 ساختاراً قادر به تحویل نبود.
RFC_ID_MAX = 29


def _short_rfc_id(prefix: str, raw: str) -> str:
    """شناسهٔ کوتاه و پایدار که در سقفِ ۶۴ بایتِ callback جا شود.

    پایدار (hash، نه شمارنده) تا بازفرستِ همان ردیف همان id را بدهد و گاردِ
    ضدِ کارتِ تکراریِ `rfc_card` واقعاً کار کند."""
    p = str(prefix or "c6")[:8]
    h = hashlib.sha1(str(raw or "").encode("utf-8")).hexdigest()[:12]
    return f"{p}-{h}"[:RFC_ID_MAX]


def _redeliver_summary(row: dict) -> str:
    """خلاصهٔ کارتِ بازفرست — فقط از چیزی که ردیف واقعاً نگه داشته.

    `_summarize` به خروجیِ خامِ بنچ نیاز دارد و آن در صف ذخیره نمی‌شود، پس
    بازسازیِ کلمه‌به‌کلمهٔ کارتِ اصلی ممکن نیست. به‌جای ساختنِ متنی که *انگار*
    تازه است، تاریخِ واقعی را می‌گوید — وگرنه مالک یک نتیجهٔ کهنه را نو می‌خوانَد."""
    done = str(row.get("done_at") or row.get("taken_at") or "")[:10]
    verdict = str(row.get("verdict") or "?")
    q = str(row.get("question") or row.get("hypothesis") or "").strip()
    return (f"نتیجهٔ آزمایشی که در {done} تمام شد و کارتش آن روز به دستت نرسید.\n"
            f"پرسش: {q[:420]}\n"
            f"حکم: {verdict}")


def _mark_card_delivered(hid: str) -> bool:
    """فقط همین یک فیلد را true کن. الگوی read-modify-write مثل `_mark_hypothesis`
    (صف append-only نیست — خودِ همین ماژول بازنویسی‌اش می‌کند)."""
    if not QUEUE.exists() or not hid:
        return False
    try:
        out, hit = [], False
        for ln in QUEUE.read_text("utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                out.append(ln)
                continue
            if d.get("id") == hid:
                d["card_delivered"] = True
                d["card_delivered_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                hit = True
            out.append(json.dumps(d, ensure_ascii=False))
        if hit:
            QUEUE.write_text("\n".join(out) + "\n", encoding="utf-8")
        return hit
    except Exception:  # noqa: BLE001
        return False


def pending_cards() -> list:
    """ردیف‌هایی که آزمایششان تمام شده ولی کارتشان هرگز نرسید. read-only."""
    if not QUEUE.exists():
        return []
    rows = []
    try:
        for ln in QUEUE.read_text("utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if str(d.get("status") or "") == "DONE" and not d.get("card_delivered"):
                rows.append(d)
    except Exception:  # noqa: BLE001
        return []
    return rows


def redeliver_undelivered_cards(channel=None, limit: int = REDELIVER_CAP) -> dict:
    """کارتی که محاسبه شد ولی هرگز نرسید را دوباره بفرست.

    چرا لازم شد (۲۰۲۶-۰۷-۲۶): مسیرِ تحویل از قبل وجود داشت و در `c6_research_beat`
    صدا زده می‌شد — ولی **فقط وقتی یک فرضیهٔ PENDING باشد**. صف که خالی شد، beat
    روی `no-pending-hypothesis` زودتر برمی‌گردد و ردیفِ `card_delivered:false`
    برای همیشه آن‌جا می‌مانَد. یعنی اختاپوس یک آزمایشِ واقعی کرد، حکم داد، و
    نتیجه‌اش را هرگز به مالک نگفت — و هیچ‌جا خطایی هم ثبت نشد.
    (شکستِ اصلیِ ۲۵ جولای نبودِ `OCTOPUS_CB_SECRET` بود؛ حالا هست، پس بازفرست
    واقعاً جواب می‌دهد — نه اینکه دوباره بی‌صدا False بگیرد.)

    پیش‌فرض خاموش. هر خطا → گزارشِ شمرده، هرگز استثنا به بیرون."""
    if str(os.environ.get(REDELIVER_FLAG, "") or "").strip().lower() not in (
            "1", "true", "yes", "on"):
        return {"ran": False, "reason": "flag-off"}
    rows = pending_cards()
    if not rows:
        return {"ran": True, "pending": 0, "sent": 0}
    _chan = channel
    if _chan is None:
        try:
            import wiring as _wiring
            _chan = _wiring.make_telegram_channel()
        except Exception:  # noqa: BLE001
            _chan = None
    if _chan is None or not hasattr(_chan, "rfc_card"):
        return {"ran": False, "pending": len(rows), "sent": 0, "reason": "no-channel"}
    sent = failed = 0
    for row in rows[:max(0, int(limit))]:
        hid = str(row.get("id") or "")
        try:
            ok = bool(_chan.rfc_card(rfc_id=_short_rfc_id("c6re", hid),
                                     summary=_redeliver_summary(row)[:800]))
        except Exception as e:  # noqa: BLE001 — تحویل نباید beat را بکشد
            opslib.alert([f"c6 redeliver failed: {type(e).__name__}: {e}"])
            ok = False
        if ok and _mark_card_delivered(hid):
            sent += 1
        else:
            failed += 1
    return {"ran": True, "pending": len(rows), "sent": sent, "failed": failed}


def _mark_hypothesis(hid: str, verdict: str, delivered: bool, requeue: bool = False) -> None:
    """صف را با نتیجهٔ نهایی به‌روز کن. requeue=True یعنی نتیجه **نامعلوم** بود (خطای بنچ
    یا آلودگیِ outlier)، نه ابطال‌شده → ردیف با attemptِ +۱ دوباره PENDING می‌شود، تا
    سقفِ MAX_ATTEMPTS. attempt واردِ stop_condition می‌شود پس contract_idِ فردا فرق دارد
    و گاردِ find_completedِ research_loop آن را کوتاه نمی‌کند."""
    if not QUEUE.exists() or not hid:
        return
    try:
        lines = QUEUE.read_text("utf-8").splitlines()
        out = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                out.append(ln)
                continue
            if hid and d.get("id") == hid:
                _att = int(d.get("attempt", 1) or 1)
                _now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                if requeue and _att < MAX_ATTEMPTS:
                    d["status"] = "PENDING"
                    d["attempt"] = _att + 1
                    d["last_verdict"] = f"{verdict}:inconclusive"
                    d["touched_at"] = _now
                else:
                    d["status"] = "DONE"
                    d["verdict"] = (f"{verdict}:inconclusive-exhausted" if requeue else verdict)
                    d["card_delivered"] = bool(delivered)
                    d["done_at"] = _now
                    _thesis_writeback(d)
                    _romajan_seen_writeback(d)
            out.append(json.dumps(d, ensure_ascii=False))
        QUEUE.write_text("\n".join(out) + "\n", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _thesis_writeback(row: dict) -> None:
    """مسیرِ رویا (رأیِ مالک 2026-07-25): حکمِ همین ضربانِ خودکار → دفترِ تز.

    فقط ردیف‌هایی که probeشان در `thesis_queue.PROBE_TO_ROW` است اثر دارند؛ بقیه no-op.
    وضعیت را فقط در انتقال‌های منطقاً اجباری عوض می‌کند — وگرنه صرفاً شاهد ثبت می‌شود
    (که برای شرطِ مرگِ ۹۰ روزهٔ تخصیصِ ۲۵٪ کافی است). flag-gated، fail-soft."""
    try:
        _out = str(Path(__file__).resolve().parent / "outcomes")
        if _out not in sys.path:
            sys.path.insert(0, _out)
        import thesis_queue as _tq  # noqa: WPS433
        _tq.record_from_c6(row)
    except Exception:  # noqa: BLE001 — دفترِ تز هرگز صف را نمی‌شکند
        pass


def _romajan_seen_writeback(row: dict) -> None:
    """پس از DONE شدنِ فرضیهٔ romajan_*: id را به seen-set بنویس تا دوباره پیشنهاد نشود.

    هر verdict ترمینال (accepted/rejected/…) کافی است — re-propose ممنوع است.
    این FACT شدنِ claim نیست؛ فقط «دیگر از این id فرضیه نساز». fail-soft."""
    try:
        probe = str(row.get("probe") or "")
        if not probe.startswith("romajan_"):
            return
        import c6_probes as _cp  # noqa: WPS433
        ids = []
        # prefer explicit claim ids carried on the row
        for k in ("claim_ids", "romajan_ids", "new_ids"):
            v = row.get(k)
            if isinstance(v, list):
                ids.extend(str(x) for x in v if str(x).strip())
        # fallback: parse from baseline_detail / measured.detail "new=..."
        if not ids:
            detail = str(row.get("baseline_detail") or "")
            m = row.get("measured") if isinstance(row.get("measured"), dict) else {}
            detail = detail or str(m.get("detail") or "")
            # if producer stored a single subject-hash id, still mark probe|subject
            sid = str(row.get("id") or "").strip()
            if sid:
                ids.append(sid)
        if ids:
            _cp.mark_romajan_seen(ids)
    except Exception:  # noqa: BLE001
        pass


def seed_default_hypothesis() -> bool:
    """اگر صف خالی است، یک فرضیهٔ نمونهٔ بی‌خطر اضافه کن (با اولین بوت).
    وقتی producer روشن است، seed صریحاً خاموش می‌شود تا فرضیهٔ صنعتی تولید نشود."""
    try:
        try:
            import c6_producer as _cp
            if _cp.flag_on():
                return False
        except Exception:
            pass
        QUEUE.parent.mkdir(parents=True, exist_ok=True)
        if QUEUE.exists() and QUEUE.read_text("utf-8").strip():
            return False
        h = {
            "id": "seed-state-read-cache-bench",
            "status": "PENDING",
            "kind": "micro_benchmark",
            "attempt": 1,
            "question": ("Does a stat-validated cache of the parsed ORGANISM-STATE do "
                         "strictly less work per tick than re-parsing it?"),
            "hypothesis": ("A stat-validated cached read performs fewer JSON parse "
                           "operations per tick than a re-parse of the identical input, "
                           "without changing the parsed result."),
            "stop_condition": "one paired A/B bench run in a single offline process",
            "verifier": "compare_frozen_baselines",
            "expected_artifact": ("paired A/B bench record: measured baseline median, "
                                  "paired delta median+mean+IQR, A/A noise floor, "
                                  "sign-test p, parse-op counters"),
            "falsification_criteria": list(_FALSIFICATION),
            # **هیچ baselineِ اعلامی** — baseline در همان اجرا اندازه‌گیری می‌شود (C1).
            "bench_label": "state-read-cache-vs-reparse",
            "bench_pairs": BENCH_PAIRS,
            "bench_inner": BENCH_INNER,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with QUEUE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False
