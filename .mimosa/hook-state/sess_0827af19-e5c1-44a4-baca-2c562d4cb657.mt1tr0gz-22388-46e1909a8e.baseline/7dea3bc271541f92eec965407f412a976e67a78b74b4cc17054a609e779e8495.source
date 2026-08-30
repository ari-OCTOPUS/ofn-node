#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prediction_writer.py — Q3 (OWNER-QUEUE-RESOLUTION §Q3, 2026-08-19): حلقهٔ
observe→predict→outcome→belief-update برای خودِ دیمن 4d.

غیر-TCB. به ledger ضدفتلشِ Core (_ops/state/predictions.db) فقط INSERT
می‌زند (تریگرهای ABORT در سطح DB هر UPDATE/DELETE را می‌بندند — همان
قرارداد prediction-ledger.v1). باورها در 4d_system/outputs/prediction-beliefs.json
نگهداری و append می‌شوند. هر خطا fail-soft است: لوپ دیمن هرگز نمی‌میرد."""
from __future__ import annotations
import hashlib, json, logging, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("brain.prediction_writer")

LEDGER = Path(__file__).resolve().parents[2] / "_ops/state/predictions.db"
BELIEFS = Path(__file__).resolve().parents[1] / "outputs/prediction-beliefs.json"
SCHEMA_V = "prediction-ledger.v1"
TRACE = "daemon4d-autoloop"
MIN_MI_DELTA = 1e-4   # آستانهٔ «بهبود MI» برای hit


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_beliefs() -> dict:
    try:
        return json.loads(BELIEFS.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"sources": {}}


def _save_beliefs(b: dict) -> None:
    try:
        BELIEFS.parent.mkdir(parents=True, exist_ok=True)
        BELIEFS.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        logger.warning("beliefs save failed: %s", e)


def _pending_prediction(cur, source_label: str):
    row = cur.execute(
        "SELECT p.prediction_id, p.content FROM predictions p "
        "JOIN outcomes o ON o.prediction_id = p.prediction_id "
        "WHERE p.source=? AND p.content LIKE ? ORDER BY p.created_at DESC LIMIT 1",
        (f"{TRACE}:{source_label}", "%MI%")).fetchone()
    return row  # آخرین prediction همین source که outcome دارد → الگوی جدید روی تازه‌ترین


def predict(source_label: str, mi_now: float) -> str | None:
    """پیش‌ثبتِ پیش‌بینی دربارهٔ MI بعدیِ همین source (پیش از مشاهدهٔ بعدی)."""
    try:
        b = _load_beliefs()
        st = b["sources"].setdefault(source_label, {"alpha": 1.0, "beta": 1.0, "n": 0})
        mean = st["alpha"] / (st["alpha"] + st["beta"])
        theta = round(mi_now * (0.5 + 0.5 * mean), 6)   # باورِ خوش‌بین‌تر → آستانهٔ بالاتر
        content = f"next MI of [{source_label}] >= {theta} (belief mean {mean:.3f}, n={st['n']})"
        pid = f"daemon4d-{int(time.time()*1000)}-{hashlib.sha1(source_label.encode()).hexdigest()[:6]}"
        con = sqlite3.connect(str(LEDGER), timeout=10)
        con.execute(
            "INSERT INTO predictions(prediction_id, created_at, content, content_sha, "
            "trace_id, source, model, confidence, eval_window, schema_version) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pid, _now(), content,
             hashlib.sha256(content.encode()).hexdigest(),
             TRACE, f"{TRACE}:{source_label}", "local-analysis+beta-belief",
             round(0.5 + 0.25 * mean, 3), "next-occurrence", SCHEMA_V))
        con.commit(); con.close()
        b["sources"][source_label]["last_theta"] = theta
        b["sources"][source_label]["last_pid"] = pid
        _save_beliefs(b)
        logger.info("prediction registered: %s | %s", pid, content)
        return pid
    except Exception as e:  # noqa: BLE001
        logger.warning("predict failed (fail-soft): %s", e)
        return None


def resolve(source_label: str, mi_observed: float) -> dict | None:
    """پیوندِ outcome به تازه‌ترین predictionِ بازِ همین source + به‌روزرسانی باور."""
    try:
        b = _load_beliefs()
        st = b["sources"].get(source_label) or {}
        pid = st.get("last_pid")
        if not pid:
            return None
        con = sqlite3.connect(str(LEDGER), timeout=10)
        row = con.execute("SELECT content FROM predictions WHERE prediction_id=?", (pid,)).fetchone()
        done = con.execute("SELECT COUNT(*) FROM outcomes WHERE prediction_id=?", (pid,)).fetchone()[0]
        if not row or done:
            con.close(); return None
        import re
        m = re.search(r">=\s*([0-9.]+)", row[0] or "")
        theta = float(m.group(1)) if m else 0.0
        hit = mi_observed >= theta
        con.execute("INSERT INTO outcomes(prediction_id, outcome_at, outcome, outcome_sha) "
                    "VALUES (?,?,?,?)",
                    (pid, _now(),
                     f"{'hit' if hit else 'miss'}: MI={mi_observed:.6f} vs theta={theta}",
                     hashlib.sha256(f"{pid}:{mi_observed}".encode()).hexdigest()))
        con.commit(); con.close()
        st["alpha"] = st.get("alpha", 1.0) + (1 if hit else 0)
        st["beta"] = st.get("beta", 1.0) + (0 if hit else 1)
        st["n"] = st.get("n", 0) + 1
        st.pop("last_pid", None)
        b["sources"][source_label] = st
        _save_beliefs(b)
        logger.info("outcome attached: %s -> %s (belief a/b=%s/%s)",
                    pid, "hit" if hit else "miss", st["alpha"], st["beta"])
        return {"prediction_id": pid, "hit": hit, "theta": theta, "belief": st}
    except Exception as e:  # noqa: BLE001
        logger.warning("resolve failed (fail-soft): %s", e)
        return None


def cycle(source_label: str, mi_now: float) -> dict | None:
    """یک چرخهٔ کامل روی رخدادِ این source: resolve قبلی → predict جدید."""
    r = resolve(source_label, mi_now)
    pid = predict(source_label, mi_now)
    return {"resolved": r, "new_prediction": pid}
