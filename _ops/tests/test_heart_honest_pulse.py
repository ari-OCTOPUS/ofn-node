#!/usr/bin/env python3
"""test_heart_honest_pulse.py — T4 (2026-07-25): سنجه‌هایی که دروغِ خوش‌بینانه می‌گفتند.

گواه از state زنده (اسکن ۱۱:۱۲):
  الف) velocity-stream: ۵۲۷/۵۲۷ سطر confirmed=0 و effects=0؛ metronome_share=0.9644
      → «سرعت» ۹۶٪ ضربانِ خودِ قلب بود. فلگ OCTOPUS_HEART_HONEST_PULSE خاموش بود.
  ب) delta_self: S_informed=0.02342 > S_blind=0.02225 (مدلِ آگاه بدتر از کور)،
      raw=-0.02573 ولی 0.0 منتشر می‌شد با authoritative=true.

این تست ادعا می‌کند:
  ۱) سریِ فقط-ضربان (+کمی confirmed) → metronome_share>0.9 → با فلگ روشن:
     self_referential=True و authoritative=False؛ با فلگ خاموش: رفتارِ قبلی (بدون پرچم).
  ۲) S_informed>S_blind → با فلگ روشن: delta_self_live منفی منتشر می‌شود؛ با فلگ
     خاموش: clamp به 0.0 (بایت‌به‌بایتِ قدیم). و gate0 در مودِ honest با Δ≤0 بسته است.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
sys.path.insert(0, str(OPS / "heart"))
sys.path.insert(0, str(OPS / "budget"))

import opslib  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="oct-t4-honest-"))
opslib.ORG_ROOT = _TMP
opslib.STATE_DIR = _TMP / "state"
opslib.STATE_DIR.mkdir(parents=True, exist_ok=True)

import producers  # noqa: E402

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


def _sandbox_paths():
    producers.LEDGER_PATH = _TMP / "ledger.jsonl"
    producers.CONSOLIDATION_PATH = _TMP / "no-consolidation.json"
    producers.CHRONO_DB = _TMP / "chrono.db"
    producers.COGNITION_STREAM = _TMP / "no-cog.jsonl"
    producers.FUEL_STREAM = _TMP / "no-fuel.jsonl"
    producers.PULSE_DIR = _TMP / "state" / "pulse"
    producers.STREAM_PATH = producers.PULSE_DIR / "velocity-stream.jsonl"
    producers.SIGNALS_PATH = producers.PULSE_DIR / "heart-signals-latest.json"


def _make_ledger(n_confirmed: int):
    now = time.time()
    rows = [{"type": "MONEY_ATTRIBUTION", "payload": {"state": "CONFIRMED"},
             "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now - i * 60))}
            for i in range(n_confirmed)]
    producers.LEDGER_PATH.write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", "utf-8")


def _make_chrono(n_beats: int):
    con = sqlite3.connect(str(producers.CHRONO_DB))
    con.execute("CREATE TABLE heartbeat (beat_seq INTEGER PRIMARY KEY, wall_ts INTEGER NOT NULL)")
    now_ms = int(time.time() * 1000)
    con.executemany("INSERT INTO heartbeat(beat_seq, wall_ts) VALUES (?,?)",
                    [(i + 1, now_ms - i * 60_000) for i in range(n_beats)])
    con.commit()
    con.close()


# ═══ ۱) گاردِ self_referential ════════════════════════════════════════════════
_sandbox_paths()
_make_ledger(5)          # confirmed=5 → ۱۵ واحد
_make_chrono(2000)       # beats=2000 → ۲۰۰ واحد → share ≈ ۰.۹۳ > ۰.۹

os.environ.pop("OCTOPUS_HEART_HONEST_PULSE", None)
off = producers.velocity_meter(window_hours=24.0)
check(off.get("metronome_share") and off["metronome_share"] > 0.9,
      f"metronome_share واقعاً >0.9 است (={off.get('metronome_share')})")
check(off.get("authoritative") is True,
      "فلگ خاموش: authoritative طبق قاعدهٔ قدیم True (بایت‌به‌بایت)")
check(off.get("self_referential") is False,
      "فلگ خاموش: self_referential=False (رفتارِ قدیم)")

os.environ["OCTOPUS_HEART_HONEST_PULSE"] = "1"
on = producers.velocity_meter(window_hours=24.0)
check(on.get("self_referential") is True,
      "فلگ روشن: self_referential=True وقتی متروَنوم >0.9")
check(on.get("authoritative") is False,
      "فلگ روشن: authoritative=False — عددِ متروَنوم دیگر «معتبر» اعلام نمی‌شود")

# ═══ ۲) انتشارِ Δ منفی ════════════════════════════════════════════════════════
# سریِ ساختگی: نیمهٔ اول v با cov هم‌جهت (+)، نیمهٔ دوم ضد‌جهت — مدلِ informed روی
# holdout بدتر از blind می‌شود (S_informed > S_blind → raw < 0).
rows = []
for i in range(12):
    rows.append({"v": float(i), "cov": {"confirmed": float(i), "effects": 0.0, "hour": 1.0}})
for i in range(12, 24):
    rows.append({"v": float(23 - i), "cov": {"confirmed": float(i), "effects": 0.0, "hour": 1.0}})

d = producers.delta_self_estimator(min_samples=8, rows=rows)
check(d.get("delta_self_raw") is not None and d["delta_self_raw"] < 0,
      f"fixture واقعاً Δ منفی تولید می‌کند (raw={d.get('delta_self_raw')})")

os.environ["OCTOPUS_HEART_HONEST_PULSE"] = "1"
d_on = producers.delta_self_estimator(min_samples=8, rows=rows)
check(d_on.get("delta_self_live") is not None and d_on["delta_self_live"] < 0,
      "فلگ روشن: مقدارِ منفی منتشر می‌شود (نه صفرِ ساختگی)")

os.environ["OCTOPUS_HEART_HONEST_PULSE"] = "0"
d_off = producers.delta_self_estimator(min_samples=8, rows=rows)
check(d_off.get("delta_self_live") == 0.0,
      "فلگ خاموش: clamp به 0.0 (بایت‌به‌بایتِ رفتارِ قدیم)")

# ═══ ۳) gate0 در مودِ honest با Δ≤0 بسته است ═══════════════════════════════════
# بخش ۲ با estimator واقعی ثابت کرد fixture یک Δ منفی منتشر می‌کند. تکرار مکانیکی
# همان سری برای رسیدن به ۴۸ نمونه، مرز train/holdout را عوض می‌کند و دیگر همان آزمایش
# نیست؛ بنابراین اینجا خروجی واقعیِ بخش ۲ را به consumer تزریق می‌کنیم تا فقط wiring
# و تصمیم gate0 را، مستقل از شکل سری، ابطال کنیم.
os.environ["OCTOPUS_HEART_HONEST_PULSE"] = "1"
negative_authoritative = {**d_on, "authoritative": True,
                          "sample_size": max(48, int(d_on.get("sample_size", 0) or 0))}
_orig_delta_estimator = producers.delta_self_estimator
try:
    producers.delta_self_estimator = lambda *args, **kwargs: dict(negative_authoritative)
    out = producers.compute_all(write=False)
finally:
    producers.delta_self_estimator = _orig_delta_estimator
check(out["delta_self"].get("authoritative") is True,
      "خروجیِ منفیِ estimator برای آزمون consumer معتبر است (authoritative)")
check(out["delta_self"].get("delta_self_live") is not None
      and out["delta_self"]["delta_self_live"] < 0,
      "compute_all مقدارِ منفی را بدون clamp عبور می‌دهد")
check(out.get("gate0_live_producer") is False,
      "gate0 با Δ منفی بسته است — «خودشناسی منفی» دیگر گیت را باز نمی‌کند")

os.environ.pop("OCTOPUS_HEART_HONEST_PULSE", None)

print(f"\n{'PASS' if not fails else 'FAIL'} — test_heart_honest_pulse")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
