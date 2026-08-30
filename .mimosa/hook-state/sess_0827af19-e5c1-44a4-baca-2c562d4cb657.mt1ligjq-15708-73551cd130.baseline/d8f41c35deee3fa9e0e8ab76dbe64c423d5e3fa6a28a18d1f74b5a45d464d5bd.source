#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_producer.py — C2 · تولیدکنندهٔ صادقِ فرضیهٔ C6 (پشتِ OCTOPUS_WIRE_C6_PRODUCER).

هر فرضیه فقط از یک سنجهٔ واقعیِ read-only ساخته می‌شود و count>floor شرط تولید است.
صفِ خالی نتیجهٔ سالم است و «no-pending-hypothesis» به‌خودی‌خودی نیاز به ساختن فرضیهٔ
ساختگی نیست. dedupe محتوایی روی کل صف؛ سقف pending و سقف کل ردیف‌ها؛ خطا = alert + no-op.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import c6_probes  # noqa: E402

FLAG = "OCTOPUS_WIRE_C6_PRODUCER"
# ۲۰۲۶-۰۷-۲۸ — درِ دومِ همین صف: «ریشه‌اش را نمی‌دانم» از لایهٔ خودشناسی.
# جدا از FLAG چون منبعِ ردیف فرق می‌کند: `produce()` فقط از سنجهٔ عددی می‌سازد و
# count>floor شرطش است؛ این‌یکی از یک **اعلامِ صریحِ نادانی** می‌سازد و عمداً
# baseline_count=-1 می‌گذارد تا هیچ‌کس آن را با یک نقصِ سنجیده‌شده اشتباه نگیرد.
UNKNOWN_FLAG = "OCTOPUS_C6_UNKNOWN_ROOTCAUSE"
_UNKNOWN_MARKERS = ("نامعلوم", "نیاز به کاوش", "unknown", "needs probing",
                    "not known", "tbd")


def _cap(name: str, default: int) -> int:
    try:
        return int(str(os.environ.get(name, default)).strip() or default)
    except (TypeError, ValueError):
        return default


MAX_PENDING_ROWS = _cap("C6_QUEUE_MAX_PENDING", 10)
MAX_QUEUE_ROWS = _cap("C6_QUEUE_MAX_ROWS", 50)


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def unknown_flag_on() -> bool:
    return str(os.environ.get(UNKNOWN_FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _read_rows(queue: Path) -> list[dict]:
    rows = []
    try:
        if queue.exists():
            for ln in queue.read_text("utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                if isinstance(d, dict):
                    rows.append(d)
    except OSError:
        pass
    return rows


def _existing_id(rows: list[dict], probe: str, subject: str) -> str:
    return "c6-" + _sha(f"{probe}|{subject}")[:12]


def _already_present(rows: list[dict], hid: str, probe: str, subject: str) -> bool:
    for r in rows:
        if str(r.get("id") or "") == hid:
            return True
        if str(r.get("probe") or "") == probe and str(r.get("subject") or "") == subject:
            return True
    return False


def _mk_row(probe: str, measured: dict) -> dict:
    """ردیفِ کامل برای research_contract + mechanism_count (C2 schema)."""
    import time as _time
    spec = c6_probes.PROBES[probe]
    hid = _existing_id([], probe, str(spec.get("subject", "")))
    count = int(measured.get("count", -1)) if isinstance(measured, dict) else -1
    fals = spec.get("falsification") or [f"measured count <= floor ({spec.get('floor', 0)})"]
    if not isinstance(fals, list):
        fals = [str(fals)]
    kind = "romajan_claim" if str(probe).startswith("romajan_") else "mechanism_count"
    return {
        "id": hid,
        "status": "PENDING",
        "kind": kind,
        "probe": probe,
        "subject": str(spec.get("subject", ""))[:200],
        "question": str(spec.get("question", ""))[:500],
        "hypothesis": str(spec.get("hypothesis") or spec.get("question") or "")[:500],
        "stop_condition": "one offline re-count on the same code path (no wall-clock claim)",
        "verifier": "compare_frozen_baselines",
        "expected_artifact": str(spec.get("expected_artifact") or f"measured count for {probe}")[:200],
        "falsification_criteria": [str(x) for x in fals][:8],
        "tools": ["test_in_sandbox", "compare_frozen_baselines"],
        "unit": str(spec.get("unit", "ops"))[:60],
        "floor": int(spec.get("floor", 0) or 0),
        "baseline_count": count,
        "baseline_detail": str((measured or {}).get("detail", ""))[:300],
        "measured": measured if isinstance(measured, dict) else {"count": -1},
        "fix_hint": str(spec.get("fix_hint", ""))[:300],
        "source": "c6_producer",
        "producer_version": "c6-producer.v2",
        "honesty": "measured-only; no fabricated hypotheses",
        "created_at": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
    }


UNKNOWN_PROBE = "doctor_unknown_root_cause"


def _is_unknown(text) -> bool:
    t = str(text or "").strip().lower()
    if not t:
        return True          # ریشهٔ خالی هم «نمی‌دانم» است، فقط بی‌صداتر
    return any(m in t for m in _UNKNOWN_MARKERS)


def unknown_root_causes(record: dict) -> list:
    """(symptom, root_cause, severity) هایی که خودشناسی ریشه‌شان را نامعلوم اعلام کرده.

    فقط `pathology` خوانده می‌شود؛ `open_questions` عمداً این‌جا نمی‌آید — یک
    پرسشِ آزاد آزمونِ ابطال‌پذیر ندارد و صف را از ردیفِ غیرقابل‌آزمون پر می‌کند.
    مقصدِ آن‌ها مالک است (`initiative`)، نه آزمایشگاه."""
    u = record.get("understanding") if isinstance(record, dict) else None
    if not isinstance(u, dict):
        u = record if isinstance(record, dict) else {}
    out = []
    for p in (u.get("pathology") or []):
        if not isinstance(p, dict):
            continue
        sym = str(p.get("symptom") or "").strip()
        if not sym or not _is_unknown(p.get("root_cause")):
            continue
        out.append({"symptom": sym[:180],
                    "declared_root_cause": str(p.get("root_cause") or "")[:180],
                    "severity": str(p.get("severity") or "")[:20]})
    return out


def _mk_unknown_row(item: dict, record: dict) -> dict:
    """ردیفِ صف برای یک ریشهٔ نامعلوم — همان اسکیمای `_mk_row`، با kindِ جدا."""
    import time as _time
    sym = item["symptom"]
    subject = f"doctor root_cause unknown: {sym}"[:200]
    return {
        "id": _existing_id([], UNKNOWN_PROBE, subject),
        "status": "PENDING",
        "kind": "unknown_root_cause",
        "probe": UNKNOWN_PROBE,
        "subject": subject,
        "question": f"چرا «{sym}» رخ می‌دهد؟ خودشناسی ریشه را نامعلوم اعلام کرده.",
        "hypothesis": (
            "the symptom has one dominant, nameable source inside the organism's own "
            "frozen logs; a single offline count grouped by producing module either "
            "names it or refutes the claim of a dominant source."),
        "stop_condition": "one offline count over the frozen logs (no wall-clock claim)",
        "verifier": "compare_frozen_baselines",
        "expected_artifact": "occurrence count of the symptom grouped by producing module",
        "falsification_criteria": [
            "the symptom does not occur in the frozen logs (count == 0)",
            "occurrences spread over more than 3 modules with no dominant source",
        ],
        "tools": ["test_in_sandbox", "compare_frozen_baselines"],
        "unit": "occurrence",
        "floor": 0,
        # -1 عمدی است: هیچ اندازه‌گیری‌ای پشتِ این ردیف نیست. تنها چیزی که
        # می‌دانیم این است که **نمی‌دانیم** — و همان قابلِ صف‌شدن است.
        "baseline_count": -1,
        "baseline_detail": (f"declared unknown by doctor self-knowledge "
                            f"v{record.get('version')} (source={record.get('source')})")[:300],
        "measured": {"count": -1, "detail": "not measured — this row exists because the "
                                            "root cause was declared unknown"},
        "fix_hint": "",
        "source": "c6_producer:unknown_root_cause",
        "producer_version": "c6-unknown.v1",
        "honesty": "declared-unknown; no fabricated root cause, no fabricated count",
        "origin": {"symptom": sym,
                   "declared_root_cause": item.get("declared_root_cause"),
                   "severity": item.get("severity"),
                   "selfknow_version": record.get("version"),
                   "selfknow_focus": str(record.get("focus") or "")[:160]},
        "created_at": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
    }


def produce_from_unknown(queue=None, record: "dict | None" = None) -> dict:
    """یک ریشهٔ نامعلومِ اعلام‌شده → یک ردیفِ PENDINGِ قابل‌ابطال. هرگز raise نمی‌کند.

    مثلِ `produce()` حداکثر **یک** ردیف در هر فراخوان می‌نویسد (سقفِ صف و ریتمِ
    همان است)، و مثلِ آن dedupe محتوایی روی کلِ صف دارد: یک نشانه دو بار صف
    نمی‌شود، هرچند خودشناسی هر نیم‌ساعت دوباره اعلامش کند."""
    try:
        if not unknown_flag_on():
            return {"produced": False, "reason": "flag-off"}
        queue = Path(queue) if queue is not None else (
            opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl")
        if record is None:
            try:
                record = json.loads(
                    (opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json")
                    .read_text("utf-8"))
            except (OSError, ValueError):
                return {"produced": False, "reason": "no-self-knowledge"}
        items = unknown_root_causes(record if isinstance(record, dict) else {})
        if not items:
            return {"produced": False, "reason": "no-unknown-root-cause", "unknown": 0}
        rows = _read_rows(queue)
        pending = [r for r in rows if str(r.get("status") or "") == "PENDING"]
        if len(pending) >= MAX_PENDING_ROWS:
            return {"produced": False, "reason": "pending-cap", "unknown": len(items)}
        if len(rows) >= MAX_QUEUE_ROWS:
            return {"produced": False, "reason": "queue-cap", "unknown": len(items)}
        dup = 0
        for item in items:
            row = _mk_unknown_row(item, record if isinstance(record, dict) else {})
            if _already_present(rows, row["id"], UNKNOWN_PROBE, row["subject"]):
                dup += 1
                continue
            queue.parent.mkdir(parents=True, exist_ok=True)
            with open(queue, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            return {"produced": True, "id": row["id"], "probe": UNKNOWN_PROBE,
                    "unknown": len(items), "duplicates": dup}
        return {"produced": False, "reason": "all-already-queued",
                "unknown": len(items), "duplicates": dup}
    except Exception as e:  # noqa: BLE001
        try:
            opslib.alert([f"c6 unknown-root-cause producer failed (no-op): "
                          f"{type(e).__name__}: {e}"])
        except Exception:
            pass
        return {"produced": False, "reason": f"failsoft:{type(e).__name__}"}


def produce(queue: Path) -> dict:
    """سعی می‌کند حداکثر یک فرضیهٔ صادقِ جدید append کند؛ هرگز raise نمی‌کند."""
    try:
        if not flag_on():
            return {"produced": False, "reason": "flag-off"}
        queue = Path(queue)
        rows = _read_rows(queue)
        pending = [r for r in rows if str(r.get("status") or "") == "PENDING"]
        if len(pending) >= MAX_PENDING_ROWS:
            return {"produced": False, "reason": "pending-cap"}
        if len(rows) >= MAX_QUEUE_ROWS:
            return {"produced": False, "reason": "queue-cap"}

        new_rows = list(rows)
        # «نقصی نیست» و «نمی‌توانم ببینم» دو چیزِ کاملاً متفاوت‌اند و تا امروز هر دو
        # یک پیام می‌دادند. ۲۰۲۶-۰۷-۲۶: از ۶ پروب، ۵ تا count=-1 می‌دادند (دو تا
        # واقعاً خراب بودند) و خروجی همچنان «no-defect» بود — یعنی گزارشِ سلامت از
        # یک لایهٔ حسِ تقریباً کور. حالا کوری شمرده و برگردانده می‌شود.
        blind, seen = [], []
        for probe, spec in c6_probes.PROBES.items():
            measured = spec["measure"]()
            count = int(measured.get("count", -1)) if isinstance(measured, dict) else -1
            if count < 0:
                blind.append(probe)
                continue
            seen.append(probe)
            if count <= int(spec["floor"]):
                continue
            hid = _existing_id(new_rows, probe, spec["subject"])
            if _already_present(new_rows, hid, probe, spec["subject"]):
                continue
            row = _mk_row(probe, measured)
            queue.parent.mkdir(parents=True, exist_ok=True)
            with open(queue, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            return {"produced": True, "id": row["id"], "probe": probe,
                    "measured": len(seen), "blind": len(blind)}
        return {"produced": False,
                "reason": "no-defect" if seen else "all-probes-blind",
                "measured": len(seen), "blind": len(blind),
                "blind_probes": sorted(blind)[:12]}
    except Exception as e:  # noqa: BLE001
        try:
            opslib.alert([f"c6_producer failed (no-op): {type(e).__name__}: {e}"])
        except Exception:
            pass
        return {"produced": False, "reason": f"failsoft:{type(e).__name__}"}
