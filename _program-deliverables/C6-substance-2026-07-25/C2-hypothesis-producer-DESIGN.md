# C2 — C6 has no hypothesis producer: activation buys exactly one experiment (and that one is a fabricated success)
# VERDICT: real-bug
# FILES: ['F:\\backup\\_ops\\c6_probes.py (NEW)', 'F:\\backup\\_ops\\c6_producer.py (NEW)', 'F:\\backup\\_ops\\c6_trigger.py (EDIT — 8 anchored edits)', 'F:\\backup\\_ops\\tests\\test_c6_hypothesis_producer.py (NEW)', 'F:\\backup\\_ops\\tests\\run_all.py (EDIT — register the new test)', 'F:\\backup\\_ops\\tests\\test_c6_trigger_propose_only.py (EDIT — extend the banned-primitive scan to the two new C6 files)']
# FLAG: OCTOPUS_WIRE_C6_PRODUCER (new, default OFF) — in addition to the existing OCTOPUS_WIRE_C6_RESEARCH + _ops/ACTIVATION-C6-RESEARCH.flag. Knobs: C6_QUEUE_MAX_PENDING (default 8), C6_QUEUE_MAX_ROWS (default 500), C6_RUNNING_STALE_H (default 48). With the producer flag OFF, behaviour is byte-identical to today. Arm all three together or C6 still buys one (fake) experiment.

## SUMMARY
Ship a probe-registry-backed hypothesis producer that only emits a queue row when an in-repo, read-only, $0 probe MEASURES a real mechanism-level defect right now (a count of primitive operations, never a wall-clock delta), deduped by a content-addressed id so each defect is proposed exactly once ever, bounded by max-pending/max-rows, and silent when nothing fires. Add a `mechanism_count` kind to _derive_fns so the row can actually name its probe (today a JSONL row cannot carry a bench_fn, so every row would run the same default bench). Fix _mark_hypothesis to match on id only, backfill ids at pop time, close rows on the two early-return paths, and reap stale RUNNING rows to ABANDONED (never a fabricated verdict). Suppress the fabricated seed hypothesis when the producer is armed.

## TESTS
HERMETIC TEST: F:\backup\_ops\tests\test_c6_hypothesis_producer.py (script-native, one process, $0, no network; ORG_ROOT/OPS_DIR pinned to a tempdir BEFORE opslib is imported; c6.QUEUE rebound to that tempdir; the real probe registry is only checked for shape, never executed, so nothing touches the live tree).

RUN: python -X utf8 "F:\backup\_ops\tests\test_c6_hypothesis_producer.py"  (exit 0 = PASS). Do NOT run run_all.py to validate this — it writes live state and rewrites the capability marker.

FAILS BEFORE THE PATCH — three independent ways:
1. `import c6_probes` / `import c6_producer` raise ModuleNotFoundError → non-zero exit. (Both modules are new.)
2. Assertion 7 is the substantive regression and fails even if the modules existed: with today's c6_trigger.py:265 (`if d.get("id") == hid or d.get("status") == "RUNNING":`), calling `_mark_hypothesis("B", "accepted", True)` on a two-row queue also closes unrelated row A, so `A.status` becomes "DONE" and `A.verdict` becomes "accepted" — the check `A.status == "RUNNING" and "verdict" not in A` fails with the message "over-marking: بستنِ B ردیفِ نامرتبطِ A را هم بست/verdict جعلی داد".
3. Assertions 8, 9, 10, 11 fail: id-backfill, the ABANDONED reaper, the `mechanism_count` branch of `_derive_fns` (today `_derive_fns` ignores `kind` entirely — line 199 assigns it and never reads it, so it returns the ms-based verifier and `_vf({}, {"measured_count": -1})` returns supported=True because `benchmark_gain_ms` defaults to 0.0 → gain>0.0 is False... it returns supported=False by accident but `_ef({})` calls `_default_bench` and returns `measured_ms`, not `measured_count`, so the `measured_count == -1` check fails), and the seed suppression.

PASSES AFTER — all 13 groups green, including the falsification-symmetry checks: measured>floor → supported, measured==floor → falsified, measured==-1 (probe error) → never supported.

COVERAGE MAP (what each group locks):
- 1,2,2.5 — refusal to fabricate: silent probe, "I don't know" probe (-1), and a probe that raises all produce zero rows.
- 3,4 — row schema is complete AND survives the real `research_contract.make_contract(_build_contract(row))`, which is the integration point that would otherwise kill the beat at c6_trigger.py:127.
- 5,5.5 — idempotency key holds across repeat runs and across a row already marked DONE (a defect already answered is never re-asked).
- 6 — max-pending bound (C6_QUEUE_MAX_PENDING=2 → third probe refused).
- 7 — the over-marking corruption regression (the core fix).
- 8 — id backfill closes the leak that id-only matching would otherwise open.
- 9 — stale RUNNING is reaped to ABANDONED with NO verdict key (honest, not fabricated).
- 10 — mechanism_count verifier semantics in all three directions.
- 11 — the fabricated seed is suppressed when the real producer is armed.
- 12 — flag-off is a pure no-op (today's behaviour byte-identical).
- 13 — every registered probe declares a falsification criterion (an unfalsifiable hypothesis is not research — research_contract.py:66-67).

NOT COVERED BY THE HERMETIC TEST (deliberate, and the owner should know): the two real probes' `measure()` bodies are never executed by the suite, because running them requires the live vault tree (`self_audit.run_audit` over real paths, and the real RFC directory). Suggested manual one-liner for the owner before arming, read-only and $0:
  python -X utf8 -c "import sys;sys.path.insert(0,r'F:\backup\_ops');import c6_probes as p;print({k:p.PROBES[k]['measure']() for k in p.PROBES})"
Expected today: self_audit_redundant_reads count>=6, rfc_duplicate_surplus count≈230.

## RISKS
- HONEST CEILING — the producer does NOT guarantee one experiment per day, and any design that did would be the fabrication machine this exercise exists to kill. v1 ships two probes, so arming C6 buys at most two real experiments, then the queue goes empty and the beat returns 'no-pending-hypothesis' — which is now the truth rather than a bug. The supported way to add work is to register another probe (a small, owner-reviewable diff), never to lower the bar for what counts as a hypothesis.
- THE FIX IS INCOMPLETE WITHOUT THE THIRD FLAG — the producer defaults OFF, so `OCTOPUS_WIRE_C6_RESEARCH=1` + ACTIVATION-C6-RESEARCH.flag alone still yields today's behaviour, including the fabricated seed experiment. Arm all three together (OCTOPUS_WIRE_C6_RESEARCH, ACTIVATION-C6-RESEARCH.flag, OCTOPUS_WIRE_C6_PRODUCER) or do not arm at all. Half-arming is worse than dark.
- PROBE 1 REBINDS TWO MODULE FUNCTIONS — `_measure_self_audit_redundant_reads` temporarily replaces `self_audit._read` and `self_audit._grep`, restoring them in `finally` under a module lock. The wrappers call through, so behaviour and results are unchanged, but if another thread called `self_audit.run_audit` in the same window the counts would be inflated (never corrupted). The lock makes concurrent probe runs safe; it cannot stop an unrelated caller. Acceptable because the count only needs to be > 0 to fire, and inflation cannot manufacture a defect that isn't there (the duplicate call sites are static).
- PROBE 2 IS I/O-HEAVY — it reads up to 1000 RFC files (~234 today) once per daily beat. $0 and read-only, but it is real disk work inside the daily tick. Mitigated by the early `pending >= max_pending` return, which skips ALL measurement on a busy day, and by the [:1000] cap.
- COUNT-SCALED `benchmark_gain` FEEDS `governance.utility()` — verified acceptable: PRE-0/governance.py utility() is `gain - risk - cost - debt - uncertainty` with all weights 1.0 and acceptance only requires U > 0, so a gain of 6 (ops) and a gain of 4.7 (ms) both pass identically. No threshold retuning is needed. But note the consequence: an accepted mechanism_count result writes a memory via learning_gate exactly as an accepted micro_benchmark does — the owner should read the first few RFC cards before trusting the admission path with a new units regime.
- SEMANTIC SHIFT IN `supported` — for mechanism_count, `supported=True` means 'the defect reproduced', not 'an improvement was achieved'. The RFC card therefore proposes a fix the owner must implement; C6 still writes no code (propose-only boundary untouched, merge_or_deploy still FORBIDDEN). If this reads as confusing on the card, `_summarize` should be extended to say so explicitly — I left `_summarize` almost untouched to keep the diff minimal, so the card currently leans on the hypothesis text to carry that meaning.
- ID-ONLY MATCHING CHANGES BEHAVIOUR FOR LEGACY ROWS — any pre-existing RUNNING row without a matching id will no longer be closed by a later run; it will be reaped to ABANDONED after C6_RUNNING_STALE_H. This is safe today because `_ops/state/c6/` does not exist (C6 has never run, so there are zero legacy rows), but it is the migration hazard if this patch is applied to a tree where C6 already ran.
- QUEUE IS APPEND-ONLY AND NEVER PRUNED (vault law: never delete). C6_QUEUE_MAX_ROWS=500 makes the producer stop and alert rather than grow unbounded, but the owner will eventually need to move the file to _Archive by hand. There is no automatic rotation, deliberately.
- THREE SOURCES WERE REJECTED, AND THAT REJECTION IS PART OF THE ANSWER — self_audit gaps, improve.py proposals, and doctor RFCs all look like hypothesis streams and are not. Wiring any of them into C6 would produce a daily 'experiment' with no measurable claim. The 230-of-234 duplicate RFC finding is the empirical proof of what happens when a prose stream is treated as a proposal stream; do not let a future session 'improve' the producer by adding them.
- SEPARATE PRE-EXISTING GREEN-LIE FOUND WHILE WORKING (not fixed here, flagged for an owner decision): the seed hypothesis at c6_trigger.py:282-295 is guaranteed to 'succeed'. `_default_bench` times one `read_bytes()` (sub-millisecond) and `gain = 5.0 - measured` is therefore always ~4.7 > 0 → supported → U ≈ 4.6 > 0 → verdict 'accepted', producing an admitted memory that records a finding never tested. My patch suppresses the seed only when the producer flag is on. Deleting `seed_default_hypothesis` outright (and its two call sites at organism.py:631 and brain_worker.py:277) is the cleaner fix but touches the live tick, so I left it as an owner call.

## CODE
=====================================================================
FILE 1 — NEW: F:\backup\_ops\c6_probes.py
=====================================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_probes.py — رجیستریِ پروبِ نقصِ *مکانیزمی* برای حلقهٔ C6.

هر پروب یک ادعای **شمارشی** می‌سازد، نه ادعای ساعتِ دیواری: «مسیرِ P روی
ورودیِ I تعداد N عملیاتِ اولیه انجام می‌دهد در حالی که کفِ لازم F است».
چرا شمارش و نه میلی‌ثانیه (درسی که این vault قبلاً پرداخت): بنچ‌مارکِ زیرمیلی‌ثانیه
از سه جهت دروغ می‌گوید (cache گرم/ترتیب، مکثِ GC، مقایسهٔ زیرمجموعه‌های جدا)؛
ادعای مکانیزمی سخت‌افزار-مستقل است و همان ورودی را متقارن می‌سنجد.

قراردادِ هر پروب — measure() -> {"count": int, "detail": str}:
  · فقط‌خواندنی، $0، بدونِ شبکه، قطعی (دو اجرای پشتِ‌هم همان عدد).
  · هر خطا → count = -1 یعنی «نمی‌دانم» — هرگز «سالم» و هرگز فرضیه.
  · فقط وقتی count > floor است نقص واقعی است → فقط آن‌وقت فرضیه زاده می‌شود.

afterlife: وقتی مالک نقص را رفع کند، همین پروب count<=floor می‌دهد و دیگر هرگز
فرضیه نمی‌سازد — پروب خودش را بازنشسته می‌کند.
"""
from __future__ import annotations

import sys
import threading
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

_LOCK = threading.Lock()   # پروبِ ۱ موقتاً توابعِ یک ماژول را می‌پیچد — تک‌سنجشی


def _measure_self_audit_redundant_reads() -> dict:
    """یک اجرای run_audit(write=False) چند بار *همان* مسیر را کامل می‌خواند؟

    count = مجموعِ فراخوانی‌های _read/_grep منهای تعدادِ مسیرهای متمایز
            = تعدادِ خواندنِ قابلِ‌حذف.
    روش: فقط دو تابعِ خودِ ماژول (self_audit._read/_grep) موقتاً پیچیده می‌شوند
+    (نه pathlib سراسری) و در finally برمی‌گردند. پیچه‌ها خودِ اصل را صدا می‌زنند
    پس رفتار عوض نمی‌شود. run_audit(write=False) فقط‌خواندنی است
    (تنها نوشتنِ آن ماژول پشتِ `if write:` در self_audit.py:432 است).
    """
    with _LOCK:
        try:
            import self_audit as _sa
        except Exception as e:  # noqa: BLE001
            return {"count": -1, "detail": f"import-error:{type(e).__name__}"}
        hits: Counter = Counter()
        _r0, _g0 = _sa._read, _sa._grep   # noqa: SLF001

        def _r(p):
            hits[str(p)] += 1
            return _r0(p)

        def _g(p, needle):
            hits[str(p)] += 1
            return _g0(p, needle)

        try:
            _sa._read, _sa._grep = _r, _g          # noqa: SLF001
            _sa.run_audit(write=False)
        except Exception as e:  # noqa: BLE001 — پروبِ خطادار = «نمی‌دانم»
            return {"count": -1, "detail": f"probe-error:{type(e).__name__}"}
        finally:
            _sa._read, _sa._grep = _r0, _g0        # noqa: SLF001
    dup = {p: n for p, n in hits.items() if n > 1}
    redundant = sum(n - 1 for n in dup.values())
    detail = "; ".join(f"{Path(p).name}\u00d7{n}"
                       for p, n in sorted(dup.items(), key=lambda kv: -kv[1])[:6])
    return {"count": redundant, "detail": detail or "no duplicate reads"}


def _measure_rfc_duplicate_surplus() -> dict:
    """چند فایلِ RFC دقیقاً همان «گلوگاه» را تکرار می‌کنند؟

    count = تعدادِ فایلِ مازاد (کل − گلوگاه‌های متمایز). فقط‌خواندنی، $0.
    چرا مهم است: رجیستریِ پر از تکرار، «دکتر N پیشنهاد داد» را به یک عددِ
    دروغ تبدیل می‌کند و صفِ توجهِ مالک را باد می‌کند.
    """
    try:
        d = opslib.GENOME_DIR / "knowledge" / "internal"
        if not d.is_dir():
            return {"count": -1, "detail": "rfc-dir-missing"}
        seen: Counter = Counter()
        n = 0
        for p in sorted(d.glob("RFC-*.md"))[:1000]:
            if p.name.endswith("-lesson.md"):
                continue
            try:
                lines = p.read_text("utf-8", errors="replace").splitlines()
            except OSError:
                continue
            body = ""
            for i, ln in enumerate(lines):
                if "bottleneck" in ln:
                    body = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    break
            n += 1
            seen[body[:160]] += 1
        if n == 0:
            return {"count": 0, "detail": "no RFC files"}
        top, topn = seen.most_common(1)[0]
        return {"count": n - len(seen),
                "detail": f"{n} RFC / {len(seen)} distinct bottleneck; "
                          f"most repeated \u00d7{topn}: {top[:60]}"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "detail": f"probe-error:{type(e).__name__}"}


PROBES = {
    "self_audit_redundant_reads": {
        "measure": _measure_self_audit_redundant_reads,
        "floor": 0,
        "unit": "redundant-file-reads",
        "subject": "_ops/cortex/self_audit.py::run_audit",
        "question": "Does one self-audit read the same file more than once?",
        "hypothesis": ("run_audit() reads at least one path more than once per run; a "
                       "per-run memo in _read/_grep would make each distinct path be read "
                       "exactly once while leaving the produced matrix byte-identical."),
        "expected_artifact": "counted redundant file reads per run_audit()",
        "falsification": ["measured redundant reads <= 0 (every path read exactly once)"],
        "fix_hint": ("یک dictِ memoی پر-اجرا در self_audit._read/_grep (کلید = مسیر) — "
                     "خروجیِ ماتریس باید بایت‌به‌بایت یکسان بماند."),
    },
    "rfc_duplicate_surplus": {
        "measure": _measure_rfc_duplicate_surplus,
        "floor": 5,
        "unit": "surplus-duplicate-RFC-files",
        "subject": "genome knowledge/internal RFC registry",
        "question": "How many RFC files restate a bottleneck the registry already holds?",
        "hypothesis": ("the RFC registry holds substantially more files than distinct "
                       "bottlenecks, i.e. the proposal path lacks a bottleneck-identity "
                       "dedup guard before writing a new RFC."),
        "expected_artifact": "counted surplus RFC files (total minus distinct bottlenecks)",
        "falsification": ["surplus duplicate RFC files <= floor (registry is already deduped)"],
        "fix_hint": ("پیش از ساختِ RFC، hashِ متنِ bottleneck را با RFCهای غیر-terminal "
                     "مقایسه کن — همان گاردی که analyze_organs/_mine_knob_rfcs دارند "
                     "ولی مسیرِ mine()→propose ندارد."),
    },
}


=====================================================================
FILE 2 — NEW: F:\backup\_ops\c6_producer.py
=====================================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_producer.py — تولیدکنندهٔ فرضیهٔ C6 (نیمهٔ غایبِ حلقهٔ خودبهبودی).

بدونِ این، فعال‌سازیِ C6 دقیقاً *یک* آزمایش می‌خرد: seed یک‌بار می‌کارد
(c6_trigger.py:280) و از روزِ دوم صف تا ابد خالی است.

قانونِ این ماژول (ضدِ green-lie):
  ۱. فرضیه فقط از پروبی می‌آید که **همین الان** یک نقصِ واقعی را می‌سنجد
     (count > floor). پروبِ خطادار (count = -1) = «نمی‌دانم» → هیچ فرضیه‌ای.
  ۲. هیچ متنِ آرزویی (گافِ چک‌لیست، پیشنهادِ نثری، RFC) به فرضیه ترجمه نمی‌شود.
  ۳. صفِ خالی صادق است؛ فرضیهٔ ساختگی دقیقاً همان دروغی است که C6 برای کشتنش هست.

idempotency: id = sha256(probe|subject) — هر نقص دقیقاً یک‌بار در عمر پیشنهاد می‌شود
(مقایسه با **همهٔ** ردیف‌ها، نه فقط PENDING — ردیفِ DONE یعنی جواب داده شده).
کران: C6_QUEUE_MAX_PENDING (پیش‌فرض ۸) و C6_QUEUE_MAX_ROWS (پیش‌فرض ۵۰۰).
append-only — هرگز ردیفی حذف/بازنویسی نمی‌شود (قانونِ vault).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

ENV_FLAG = "OCTOPUS_WIRE_C6_PRODUCER"
PRODUCER_VERSION = "c6-producer.v1"


def flag_on() -> bool:
    return str(os.environ.get(ENV_FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    try:
        return int(str(os.environ.get(name, default)).strip())
    except (TypeError, ValueError):
        return default


def default_queue() -> Path:
    return opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl"


def hypothesis_id(probe_key: str, subject: str) -> str:
    """کلیدِ idempotency — محتوا-محور، مستقل از زمان/عددِ سنجش‌شده."""
    return "c6h-" + hashlib.sha256(
        f"{probe_key}|{subject}".encode("utf-8")).hexdigest()[:16]


def _rows(queue: Path) -> list:
    if not queue.exists():
        return []
    out = []
    try:
        for ln in queue.read_text("utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    except OSError:
        return []
    return out


def _build_row(key: str, spec: dict, measured: dict) -> dict:
    """ردیفِ صف — همان شکلِ seed (c6_trigger.py:282-295) + payloadِ mechanism_count.
    هر کلیدِ لازمِ _build_contract/research_contract.validate این‌جا هست."""
    return {
        "id": hypothesis_id(key, str(spec.get("subject", ""))),
        "status": "PENDING",
        "kind": "mechanism_count",
        "question": str(spec["question"])[:500],
        "hypothesis": str(spec["hypothesis"])[:500],
        "stop_condition": "one offline re-count on the same code path (no wall-clock claim)",
        "verifier": "compare_frozen_baselines",
        "expected_artifact": str(spec["expected_artifact"])[:200],
        "falsification_criteria": [str(x) for x in spec["falsification"]],
        "tools": ["test_in_sandbox", "compare_frozen_baselines"],
        # —— payloadِ mechanism_count (مصرفِ _derive_fns) ——
        "probe": key,
        "subject": str(spec.get("subject", ""))[:200],
        "unit": str(spec.get("unit", "ops"))[:60],
        "floor": int(spec.get("floor", 0)),
        "baseline_count": int(measured.get("count", -1)),
        "baseline_detail": str(measured.get("detail", ""))[:300],
        "fix_hint": str(spec.get("fix_hint", ""))[:300],
        "source": "producer",
        "producer_version": PRODUCER_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def produce(*, queue=None, probes=None) -> dict:
    """پروب‌ها را بسنج و فقط برای نقصِ واقعیِ تازه یک ردیف append کن.

    خروجی: {produced, ids, reason, skipped}. هرگز raise نمی‌کند؛ هرگز ردیفی را
    حذف/بازنویسی نمی‌کند؛ هرگز وقتی پروبی نمی‌سوزد چیزی نمی‌سازد.
    """
    if not flag_on():
        return {"produced": 0, "ids": [], "reason": "flag-off", "skipped": {}}
    q = Path(queue) if queue is not None else default_queue()
    if probes is None:
        try:
            import c6_probes as _cp
            probes = _cp.PROBES
        except Exception as e:  # noqa: BLE001
            return {"produced": 0, "ids": [], "reason": f"probes-unavailable:{type(e).__name__}",
                    "skipped": {}}

    max_pending = _int_env("C6_QUEUE_MAX_PENDING", 8)
    max_rows = _int_env("C6_QUEUE_MAX_ROWS", 500)
    rows = _rows(q)
    known = {str(r.get("id")) for r in rows if r.get("id")}
    pending = sum(1 for r in rows if r.get("status") == "PENDING")
    skipped = {"dup": 0, "no-defect": 0, "unknown": 0}

    if len(rows) >= max_rows:
        opslib.alert([f"c6 queue at cap ({len(rows)}/{max_rows}) \u2014 "
                      f"تولیدکننده متوقف شد؛ صف append-only است و باید آرشیو شود."])
        return {"produced": 0, "ids": [], "reason": "queue-full", "skipped": skipped}
    if pending >= max_pending:
        # کران پیش از هر سنجش — روزِ پرکار صفر هزینهٔ پروب دارد.
        return {"produced": 0, "ids": [], "reason": "max-pending", "skipped": skipped}

    made = []
    for key in sorted(probes):                     # ترتیبِ قطعی = خروجیِ تکرارپذیر
        if pending >= max_pending:
            break
        spec = probes[key] or {}
        hid = hypothesis_id(key, str(spec.get("subject", "")))
        if hid in known:
            skipped["dup"] += 1
            continue                                # هر نقص دقیقاً یک‌بار، حتی اگر DONE باشد
        try:
            m = spec["measure"]()
            count = int(m.get("count", -1))
        except Exception as e:  # noqa: BLE001 — پروبِ معیوب هرگز به فرضیه ترجمه نمی‌شود
            opslib.alert([f"c6 probe {key} failed (non-fatal): {type(e).__name__}: {e}"])
            skipped["unknown"] += 1
            continue
        if count < 0:
            skipped["unknown"] += 1                 # «نمی‌دانم» ≠ «نقص دارم»
            continue
        if count <= int(spec.get("floor", 0)):
            skipped["no-defect"] += 1               # نقص واقعی نیست → سکوتِ صادقانه
            continue
        row = _build_row(key, spec, m)
        try:
            q.parent.mkdir(parents=True, exist_ok=True)
            with q.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
        except OSError as e:
            opslib.alert([f"c6 producer append failed: {type(e).__name__}: {e}"])
            break
        known.add(hid)
        made.append(hid)
        pending += 1

    reason = "produced" if made else (
        "all-known" if skipped["dup"] and not skipped["no-defect"] else "no-real-defect")
    return {"produced": len(made), "ids": made, "reason": reason, "skipped": skipped}


=====================================================================
FILE 3 — EDITS to F:\backup\_ops\c6_trigger.py  (8 anchored edits)
=====================================================================

--- EDIT 3.1 — imports (anchor = lines 24-28, exact text) ---
OLD:
import json
import os
import sys
import time
from pathlib import Path

NEW:
import calendar
import hashlib
import json
import os
import sys
import time
from pathlib import Path


--- EDIT 3.2 — stale-RUNNING reaper + id backfill in _pop_next_hypothesis
     (anchor = the whole function, lines 54-83) ---
OLD (replace entire block from `def _pop_next_hypothesis` through `    return found`):
def _pop_next_hypothesis() -> "dict | None":
    """اولین فرضیهٔ status=PENDING را برمی‌دارد و آن را می‌بندد (idempotent-safe)."""
    ... (existing body) ...
    return found

NEW:
RUNNING_STALE_H = 48.0   # پیش‌فرض؛ با C6_RUNNING_STALE_H قابلِ تغییر


def _stale_running(d: dict, now: float) -> bool:
    """ردیفِ RUNNINGی که بیش از C6_RUNNING_STALE_H مانده = beatِ مرده، نه نتیجه.
    taken_at به وقتِ UTC نوشته می‌شود → timegm (نه mktimeِ محلی)."""
    try:
        hours = float(os.environ.get("C6_RUNNING_STALE_H", RUNNING_STALE_H))
    except (TypeError, ValueError):
        hours = RUNNING_STALE_H
    try:
        t = calendar.timegm(time.strptime(str(d.get("taken_at", "")), "%Y-%m-%dT%H:%M:%SZ"))
    except (ValueError, TypeError):
        return False
    return (now - t) > hours * 3600.0


def _pop_next_hypothesis() -> "dict | None":
    """اولین فرضیهٔ status=PENDING را برمی‌دارد و آن را می‌بندد (idempotent-safe).

    C2 (2026-07-25) دو افزوده:
      · reaper: RUNNINGِ کهنه → ABANDONED. هرگز verdictِ جعلی — beat مرد، پس هیچ
        نتیجه‌ای وجود ندارد که ثبت شود. بدونِ این، هر مرگِ میانِ راه یک جایگاهِ
        صف را برای همیشه نشت می‌داد.
      · id backfill: _mark_hypothesis دیگر فقط بر id تطبیق می‌دهد؛ ردیفِ دستیِ بی‌id
        وگرنه هرگز بسته نمی‌شد.
    """
    if not QUEUE.exists():
        return None
    try:
        lines = QUEUE.read_text("utf-8").splitlines()
    except Exception:  # noqa: BLE001
        return None
    out, found, reaped = [], None, 0
    now = time.time()
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            out.append(ln)   # preserve malformed line
            continue
        if d.get("status") == "RUNNING" and _stale_running(d, now):
            d["status"] = "ABANDONED"
            d["reason"] = "stale-running-reaped"
            d["done_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            reaped += 1
        if found is None and d.get("status") == "PENDING":
            d["status"] = "RUNNING"
            d["taken_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if not d.get("id"):
                d["id"] = "c6h-anon-" + hashlib.sha256(
                    json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()[:12]
            found = d
        out.append(json.dumps(d, ensure_ascii=False))
    if found is not None or reaped:
        try:
            QUEUE.parent.mkdir(parents=True, exist_ok=True)
            QUEUE.write_text("\n".join(out) + "\n", encoding="utf-8")
        except Exception:  # noqa: BLE001
            return None
    return found


--- EDIT 3.3 — run the producer before popping (anchor = lines 116-118) ---
OLD:
        return {"ran": False, "reason": f"import-failed:{type(e).__name__}"}

    h = _pop_next_hypothesis()

NEW:
        return {"ran": False, "reason": f"import-failed:{type(e).__name__}"}

    # C2 (2026-07-25): تولیدکنندهٔ فرضیه — بدونِ آن، فعال‌سازی دقیقاً *یک* آزمایش
    # می‌خرد (seed یک‌بار، بعد صف تا ابد خالی). همان cadenceِ روزانه، همان دو گیت،
    # به‌علاوهٔ OCTOPUS_WIRE_C6_PRODUCER (پیش‌فرض خاموش). فقط از نقصِ سنجیده‌شده
    # ردیف می‌سازد؛ اگر چیزی نیافت هیچ نمی‌نویسد — صفِ خالی صادق است.
    try:
        import c6_producer as _c6p
        _c6p.produce(queue=QUEUE)
    except Exception as _pe:  # noqa: BLE001 — تولیدکننده هرگز beat را نمی‌کشد
        opslib.alert([f"c6 producer skipped (non-fatal): {type(_pe).__name__}: {_pe}"])

    h = _pop_next_hypothesis()


--- EDIT 3.4 — close the row on contract-invalid (anchor = lines 125-127) ---
OLD:
    except Exception as e:  # noqa: BLE001 — فرضیهٔ بد نباید daily tick را بکشد
        opslib.alert([f"c6 contract invalid (hypothesis closed): {type(e).__name__}: {e}"])
        return {"ran": False, "reason": f"contract-invalid:{type(e).__name__}"}

NEW:
    except Exception as e:  # noqa: BLE001 — فرضیهٔ بد نباید daily tick را بکشد
        opslib.alert([f"c6 contract invalid (hypothesis closed): {type(e).__name__}: {e}"])
        # پیش‌تر متنِ هشدار می‌گفت «closed» ولی ردیف تا ابد RUNNING می‌ماند.
        _mark_hypothesis(h.get("id"), f"contract-invalid:{type(e).__name__}", False)
        return {"ran": False, "reason": f"contract-invalid:{type(e).__name__}"}


--- EDIT 3.5 — close the row on run-failed (anchor = lines 150-152) ---
OLD:
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"c6 run_experiment failed: {type(e).__name__}: {e}"])
        return {"ran": False, "reason": f"run-failed:{type(e).__name__}"}

NEW:
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"c6 run_experiment failed: {type(e).__name__}: {e}"])
        _mark_hypothesis(h.get("id"), f"run-failed:{type(e).__name__}", False)
        return {"ran": False, "reason": f"run-failed:{type(e).__name__}"}


--- EDIT 3.6 — id is now guaranteed by the pop (anchor = line 193) ---
OLD:
    _mark_hypothesis(h.get("id") or contract.get("contract_id"), verdict, delivered)
NEW:
    # id از _pop_next_hypothesis تضمین شده (backfill)؛ fallback به contract_id حذف شد
    # چون هیچ‌وقت با idِ هیچ ردیفی تطبیق نمی‌خورد (نشتِ خاموشِ RUNNING).
    _mark_hypothesis(h.get("id"), verdict, delivered)


--- EDIT 3.7 — mechanism_count dispatch in _derive_fns (anchor = lines 197-199) ---
OLD:
def _derive_fns(h: dict, contract: dict):
    """experiment_fn + verifier_fn از نوعِ hypothesis. v1: فقط 'micro_benchmark'."""
    kind = str(h.get("kind", "micro_benchmark"))

NEW:
def _derive_fns(h: dict, contract: dict):
    """experiment_fn + verifier_fn از نوعِ hypothesis.

    · micro_benchmark — ادعای ساعتِ دیواری (نسخهٔ اول، دست‌نخورده).
    · mechanism_count — ادعای *شمارشی* از رجیستریِ c6_probes: «مسیرِ P روی همان
      ورودی N عملیات می‌کند و N > floor». متقارن (همان پروبی که baseline را در
      زمانِ تولید ساخت، دوباره سنجیده می‌شود)، سخت‌افزار-مستقل، $0، بدونِ شبکه.
      فرضیه وقتی falsify می‌شود که نقص دیگر بازتولید نشود (measured <= floor).
    """
    kind = str(h.get("kind", "micro_benchmark"))

    if kind == "mechanism_count":
        def experiment_fn(c, *, _h=h):
            try:
                import c6_probes as _p
                spec = _p.PROBES.get(str(_h.get("probe", "")))
                if spec is None:
                    return {"error": "unknown-probe", "measured_count": -1,
                            "floor": int(_h.get("floor", 0))}
                m = spec["measure"]()
                return {"measured_count": int(m.get("count", -1)),
                        "detail": str(m.get("detail", ""))[:300],
                        "baseline_count": int(_h.get("baseline_count", -1)),
                        "floor": int(_h.get("floor", 0)),
                        "unit": str(_h.get("unit", "ops")),
                        "subject": str(_h.get("subject", ""))}
            except Exception as e:  # noqa: BLE001
                return {"error": f"{type(e).__name__}: {e}", "measured_count": -1,
                        "floor": int(_h.get("floor", 0))}

        def verifier_fn(c, result):
            measured = int(result.get("measured_count", -1))
            floor = int(result.get("floor", 0))
            # پروبِ خطادار (−۱) = «نمی‌دانم»، نه تأیید → هرگز supported.
            supported = measured > floor
            return {"supported": supported,
                    "evidence": json.dumps(result, ensure_ascii=False)[:500],
                    # gain = تعدادِ عملیاتِ قابلِ‌حذف (شمارش)، نه میلی‌ثانیه.
                    "benchmark_gain": float(max(0, measured - floor)) if supported else 0.0,
                    "risk": 0.1}

        return experiment_fn, verifier_fn

    # (ادامه: بدنهٔ micro_benchmark کاملاً دست‌نخورده می‌ماند)


--- EDIT 3.8 — _mark_hypothesis: match on id ONLY (anchor = line 265) ---
OLD (line 249 signature + line 265 condition):
def _mark_hypothesis(hid: str, verdict: str, delivered: bool) -> None:
    """صف را با نتیجهٔ نهایی به‌روز کن."""
...
            if d.get("id") == hid or d.get("status") == "RUNNING":
                d["status"] = "DONE"

NEW:
def _mark_hypothesis(hid: str, verdict: str, delivered: bool) -> None:
    """صف را با نتیجهٔ نهایی به‌روز کن — **فقط ردیفِ هم‌شناسه**.

    باگِ برطرف‌شده (2026-07-25، خطِ ۲۶۵): شرطِ قبلی
    `d.get("id") == hid or d.get("status") == "RUNNING"` هر ردیفِ RUNNINGی را می‌بست،
    نه فقط ردیفِ همین اجرا. با صفِ تک‌ردیفی بی‌اثر بود؛ با صفِ واقعی یعنی
    فرضیه‌ای که هرگز آزمایش نشد، verdict/card_deliveredِ اجرای دیگری را بردارد
    — فسادِ داده و دقیقاً همان green-lieی که این حلقه برای کشتنش هست.
    ردیفِ RUNNINGِ جامانده به‌جای verdictِ جعلی، توسطِ reaperِ _pop_next_hypothesis
    به ABANDONED می‌رود.
    """
...
            if hid and d.get("id") == hid:
                d["status"] = "DONE"


--- EDIT 3.9 — the fabricated seed must not fire when the real producer is armed
     (anchor = lines 276-281) ---
OLD:
def seed_default_hypothesis() -> bool:
    """اگر صف خالی است، یک فرضیهٔ نمونهٔ بی‌خطر اضافه کن (با اولین بوت)."""
    try:
        QUEUE.parent.mkdir(parents=True, exist_ok=True)

NEW:
def seed_default_hypothesis() -> bool:
    """اگر صف خالی است، یک فرضیهٔ نمونهٔ بی‌خطر اضافه کن (با اولین بوت).

    C2 (2026-07-25): وقتی تولیدکنندهٔ واقعی مسلح است این تابع **هیچ نمی‌کارد**.
    دلیل: این seed یک فرضیهٔ ساختگی است — _default_bench فقط مدتِ یک read را
    می‌سنجد و آن را از baseline_msِ ثابتِ ۵.۰ کم می‌کند، پس روی هر دیسکِ سالم
    gain>0 و verdict «موفق» می‌شود بی‌آن‌که ادعای خودش (کش در مقابلِ re-parse)
    را آزموده باشد — همان green-lieی که C6 برای کشتنش هست.
    """
    if str(os.environ.get("OCTOPUS_WIRE_C6_PRODUCER", "")).strip().lower() \
            in ("1", "true", "yes", "on"):
        return False
    try:
        QUEUE.parent.mkdir(parents=True, exist_ok=True)


=====================================================================
FILE 4 — NEW: F:\backup\_ops\tests\test_c6_hypothesis_producer.py
=====================================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C2: تولیدکنندهٔ فرضیهٔ C6 + رفعِ over-markingِ _mark_hypothesis.

hermetic: ORG_ROOT پیش از importِ opslib به پوشهٔ موقت پین می‌شود و هیچ پروبِ
واقعی اجرا نمی‌شود (رجیستری با پروبِ ساختگی تزریق می‌شود) → $0، بدونِ شبکه،
بدونِ لمسِ درختِ زنده.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="c6-producer-")
os.environ["ORG_ROOT"] = _TMP                 # پیش از هر import
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "1"
os.environ["C6_QUEUE_MAX_PENDING"] = "2"
os.environ["C6_RUNNING_STALE_H"] = "48"

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes"),
           str(_OPS / "memory"), str(_OPS / "cortex"), str(_OPS.parent / "PRE-0")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import c6_probes            # noqa: E402
import c6_producer          # noqa: E402
import c6_trigger as c6     # noqa: E402
import research_contract    # noqa: E402

fails = []


def check(cond, label):
    if not cond:
        fails.append(label)


QUEUE = Path(_TMP) / "_ops" / "state" / "c6" / "hypothesis-queue.jsonl"
QUEUE.parent.mkdir(parents=True, exist_ok=True)
c6.QUEUE = QUEUE            # تولید و مصرف روی همان فایلِ موقت


def rows():
    if not QUEUE.exists():
        return []
    return [json.loads(x) for x in QUEUE.read_text("utf-8").splitlines() if x.strip()]


def fake(count):
    return {"measure": lambda: {"count": count, "detail": f"synthetic:{count}"},
            "floor": 0, "unit": "ops", "subject": f"test::subject{count}",
            "question": "Does the synthetic path do redundant work?",
            "hypothesis": "the synthetic path performs more primitive ops than its floor",
            "expected_artifact": "counted ops",
            "falsification": ["measured ops <= floor"],
            "fix_hint": "memoize"}


# ۱) صفر نقصِ واقعی → صفر ردیف (صفِ خالی صادق است)
r = c6_producer.produce(queue=QUEUE, probes={"quiet": fake(0)})
check(r["produced"] == 0 and not rows(), "پروبِ خاموش نباید فرضیه بسازد")

# ۲) پروبِ خطادار (−۱ = «نمی‌دانم») هرگز فرضیه نمی‌سازد
r = c6_producer.produce(queue=QUEUE, probes={"broken": fake(-1)})
check(r["produced"] == 0 and not rows(), "پروبِ خطادار نباید فرضیه بسازد")

# ۲.۵) پروبی که raise می‌کند هم فرضیه نمی‌سازد و beat را نمی‌کشد
_boom = dict(fake(9))
_boom["measure"] = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
r = c6_producer.produce(queue=QUEUE, probes={"boom": _boom})
check(r["produced"] == 0 and not rows(), "پروبِ raise‌کننده نباید فرضیه بسازد")

# ۳) نقصِ واقعی → دقیقاً یک ردیفِ PENDING با schemaِ درست
r = c6_producer.produce(queue=QUEUE, probes={"real": fake(6)})
rs = rows()
check(r["produced"] == 1 and len(rs) == 1, "نقصِ واقعی باید دقیقاً یک ردیف بسازد")
row = rs[0] if rs else {}
for k in ("id", "status", "kind", "question", "hypothesis", "stop_condition", "verifier",
          "expected_artifact", "falsification_criteria", "probe", "subject", "unit",
          "floor", "baseline_count", "fix_hint", "source", "producer_version", "created_at"):
    check(k in row, f"کلیدِ {k} در ردیفِ صف نیست")
check(row.get("status") == "PENDING" and row.get("kind") == "mechanism_count",
      "status/kind ردیف غلط است")
check(row.get("baseline_count") == 6, "baseline_count باید عددِ زمانِ تولید باشد")

# ۴) ردیف باید از قراردادِ واقعیِ C6 رد شود (وگرنه beat با contract-invalid می‌میرد)
try:
    research_contract.make_contract(c6._build_contract(row))
except Exception as e:  # noqa: BLE001
    fails.append(f"ردیفِ تولیدکننده از research_contract رد نشد: {type(e).__name__}: {e}")

# ۵) idempotency: همان پروب دوباره → هیچ ردیفِ تازه
c6_producer.produce(queue=QUEUE, probes={"real": fake(6)})
check(len(rows()) == 1, "کلیدِ idempotency کار نکرد — ردیفِ تکراری ساخته شد")

# ۵.۵) idempotency حتی بعد از DONE (نقصِ جواب‌داده‌شده دوباره پرسیده نمی‌شود)
_r = rows()[0]
_r["status"] = "DONE"
QUEUE.write_text(json.dumps(_r, ensure_ascii=False) + "\n", encoding="utf-8")
c6_producer.produce(queue=QUEUE, probes={"real": fake(6)})
check(len(rows()) == 1, "نقصِ DONE نباید دوباره پیشنهاد شود")

# ۶) کرانِ عمق: MAX_PENDING=2
QUEUE.write_text("", encoding="utf-8")
c6_producer.produce(queue=QUEUE, probes={"a": fake(3), "b": fake(4), "c": fake(5)})
check(sum(1 for x in rows() if x["status"] == "PENDING") == 2, "کرانِ max-pending رعایت نشد")

# ۷) رگرسیونِ over-marking — قلبِ این تست (روی کدِ امروز قرمز می‌شود).
_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
QUEUE.write_text(
    json.dumps({"id": "A", "status": "RUNNING", "kind": "mechanism_count",
                "taken_at": _now}, ensure_ascii=False) + "\n" +
    json.dumps({"id": "B", "status": "PENDING", "kind": "mechanism_count"},
               ensure_ascii=False) + "\n", encoding="utf-8")
b = c6._pop_next_hypothesis()
check(b is not None and b.get("id") == "B", "pop باید ردیفِ PENDING را بردارد")
c6._mark_hypothesis("B", "accepted", True)
_a = [x for x in rows() if x.get("id") == "A"]
_b = [x for x in rows() if x.get("id") == "B"]
check(bool(_a) and _a[0]["status"] == "RUNNING" and "verdict" not in _a[0],
      "over-marking: بستنِ B ردیفِ نامرتبطِ A را هم بست/verdictِ جعلی داد")
check(bool(_b) and _b[0]["status"] == "DONE" and _b[0]["verdict"] == "accepted",
      "ردیفِ خودی بسته نشد")

# ۸) ردیفِ بی‌id هنگامِ pop باید id بگیرد، وگرنه هرگز بسته نمی‌شود
QUEUE.write_text(json.dumps({"status": "PENDING", "kind": "micro_benchmark"},
                            ensure_ascii=False) + "\n", encoding="utf-8")
h = c6._pop_next_hypothesis()
check(bool(h and h.get("id")), "ردیفِ بی‌id هنگامِ pop شناسه نگرفت")
if h and h.get("id"):
    c6._mark_hypothesis(h["id"], "rejected", False)
    check(rows()[0]["status"] == "DONE", "ردیفِ بی‌id بسته نشد (نشتِ RUNNING)")

# ۹) reaper: RUNNINGِ کهنه → ABANDONED، هرگز verdictِ جعلی
_old = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 100 * 3600))
QUEUE.write_text(
    json.dumps({"id": "OLD", "status": "RUNNING", "taken_at": _old}, ensure_ascii=False)
    + "\n" + json.dumps({"id": "NEW", "status": "PENDING"}, ensure_ascii=False) + "\n",
    encoding="utf-8")
c6._pop_next_hypothesis()
_o = [x for x in rows() if x.get("id") == "OLD"]
check(bool(_o) and _o[0]["status"] == "ABANDONED" and "verdict" not in _o[0],
      "RUNNINGِ کهنه باید ABANDONED شود بدونِ verdict")

# ۱۰) verifierِ mechanism_count: خطای پروب هرگز supported نمی‌شود
_ef, _vf = c6._derive_fns({"kind": "mechanism_count", "probe": "nope",
                           "floor": 0, "baseline_count": 5}, {})
check(_vf({}, {"measured_count": -1, "floor": 0})["supported"] is False,
      "پروبِ خطادار نباید supported شود")
check(_vf({}, {"measured_count": 6, "floor": 0})["supported"] is True,
      "نقصِ بازتولیدشده باید supported شود")
check(_vf({}, {"measured_count": 0, "floor": 0})["supported"] is False,
      "نقصِ رفع‌شده باید falsify شود")
check(_ef({}).get("measured_count") == -1, "پروبِ ناشناخته باید −۱ بدهد، نه raise")

# ۱۱) با تولیدکنندهٔ مسلح، seedِ ساختگی نباید کاشته شود
QUEUE.unlink(missing_ok=True)
check(c6.seed_default_hypothesis() is False and not rows(),
      "با تولیدکنندهٔ مسلح، seedِ ساختگی نباید کاشته شود")

# ۱۲) flag خاموش → no-opِ محض (رفتارِ امروز دست‌نخورده)
os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "0"
check(c6_producer.produce(queue=QUEUE, probes={"real": fake(9)})["reason"] == "flag-off",
      "flag خاموش باید no-opِ محض باشد")
check(not rows(), "flag خاموش نباید چیزی بنویسد")
os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "1"

# ۱۳) رجیستریِ واقعی: قراردادِ هر پروب کامل است (بدونِ اجرای پروب)
check(len(c6_probes.PROBES) >= 1, "رجیستریِ پروب خالی است")
for _k, _s in c6_probes.PROBES.items():
    for _f in ("measure", "floor", "unit", "subject", "question", "hypothesis",
               "expected_artifact", "falsification", "fix_hint"):
        check(_f in _s, f"پروبِ {_k} فیلدِ {_f} را ندارد")
    check(callable(_s.get("measure")), f"پروبِ {_k}.measure قابلِ‌فراخوانی نیست")
    check(isinstance(_s.get("falsification"), list) and _s["falsification"],
          f"پروبِ {_k} معیارِ ابطال ندارد — فرضیهٔ ابطال‌ناپذیر پژوهش نیست")

print("FAIL" if fails else "PASS", "— test_c6_hypothesis_producer")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)


=====================================================================
FILE 5 — EDIT: F:\backup\_ops\tests\run_all.py  (register the test)
=====================================================================
Anchor (line 20 of the TESTS list):
OLD:
         # M3 (2026-07-24): reproduction=C6 lifecycle recorder + agent-gateway red-team
         "test_c6_state_machine.py", "test_agent_gateway_redteam.py",
NEW:
         # M3 (2026-07-24): reproduction=C6 lifecycle recorder + agent-gateway red-team
         "test_c6_state_machine.py", "test_agent_gateway_redteam.py",
         # C2 (2026-07-25): تولیدکنندهٔ فرضیهٔ C6 + رفعِ over-markingِ _mark_hypothesis
         "test_c6_hypothesis_producer.py",


=====================================================================
FILE 6 — EDIT: F:\backup\_ops\tests\test_c6_trigger_propose_only.py
         (extend the banned-primitive scan to the two new C6 modules)
=====================================================================
Anchor (lines 65-66):
OLD:
for rel in ("c6_trigger.py", "c6_state_machine.py",
            "outcomes/research_loop.py", "outcomes/research_contract.py"):
NEW:
for rel in ("c6_trigger.py", "c6_state_machine.py",
            "c6_probes.py", "c6_producer.py",
            "outcomes/research_loop.py", "outcomes/research_contract.py"):
