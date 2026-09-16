#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_c6_hypothesis_producer.py — C2: تولیدکنندهٔ صادقِ فرضیه + صفِ id-safe.

این تست hermetic است: ORG_ROOT/OPS_DIR پیش از import به temp پین می‌شوند؛ هیچ probe
واقعی اجرا نمی‌شود. پوشش: producer flag-off، no-defect، defect-row، idempotent،
mark فقط same-id، stale reaper، seed suppression، mechanism_count سه‌خروجی،
inconclusive و gain bounded.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="c6-producer-")
os.environ["ORG_ROOT"] = _TMP
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ.pop("OCTOPUS_WIRE_C6_RESEARCH", None)
os.environ.pop("OCTOPUS_WIRE_C6_PRODUCER", None)

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes"),
           str(_OPS / "memory"), str(_OPS.parent / "PRE-0")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import c6_trigger as c6  # noqa: E402
import c6_probes as probes  # noqa: E402
import c6_producer as cp  # noqa: E402

fails = []


def check(cond, label):
    if not cond:
        fails.append(label)


def _reset_queue():
    c6.QUEUE.parent.mkdir(parents=True, exist_ok=True)
    if c6.QUEUE.exists():
        c6.QUEUE.unlink()


def _fake_measure(count):
    return lambda: {"count": count, "unit": "read", "detail": f"fake-{count}"}


# 1) flag خاموش = هیچ فرضیه
_reset_queue()
r = cp.produce(c6.QUEUE)
check(r == {"produced": False, "reason": "flag-off"}, "producer باید flag-off no-op باشد")
check(not c6.QUEUE.exists() or not c6.QUEUE.read_text("utf-8").strip(),
      "با flag-off نباید ردیفی ساخته شود")

# 2) defect نباشد = هیچ ردیف
os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "1"
old_probes = dict(probes.PROBES)
probes.PROBES.clear()
probes.PROBES["p_ok"] = {"measure": _fake_measure(1), "subject": "s1", "question": "q1", "floor": 3}
_reset_queue()
r = cp.produce(c6.QUEUE)
# 2026-07-26: خروجی عمداً دو کلیدِ تازه گرفت — `measured` و `blind`. تا آن روز
# «نقصی نیست» و «هیچ پروبی نمی‌توانست بسنجد» یک پیامِ یکسان می‌دادند، و همان
# باعث شد لایهٔ حسِ تقریباً کور، سلامت گزارش شود. pin روی شکلِ دقیق باز شد ولی
# سخت‌گیری نه: هر سه فیلدِ معنادار جداگانه assert می‌شوند.
check(r.get("produced") is False and r.get("reason") == "no-defect"
      and r.get("measured") == 1 and r.get("blind") == 0,
      f"count<=floor نباید ردیف بسازد و باید صادقانه گزارش شود: {r}")
check(not c6.QUEUE.exists() or not c6.QUEUE.read_text("utf-8").strip(),
      "no-defect نباید ردیفی بسازد")

# 3) defect واقعی = یک ردیف PENDING با id
probes.PROBES["p_bad"] = {"measure": _fake_measure(9), "subject": "s2", "question": "q2", "floor": 3}
_reset_queue()
r = cp.produce(c6.QUEUE)
check(r.get("produced") is True and r.get("probe") == "p_bad", f"producer باید ردیف بسازد: {r}")
rows = [json.loads(x) for x in c6.QUEUE.read_text("utf-8").splitlines() if x.strip()]
check(len(rows) == 1 and rows[0]["status"] == "PENDING" and rows[0]["id"],
      "ردیف باید PENDING و id دار باشد")
check(rows[0]["kind"] == "mechanism_count", "kind باید mechanism_count باشد")

# 4) idempotent: دوباره produce ردیف تکراری نسازد
r2 = cp.produce(c6.QUEUE)
check(r2.get("produced") is False and r2.get("reason") in ("no-defect", "pending-cap"),
      f"produce دوم نباید duplicate بسازد: {r2}")
rows2 = [json.loads(x) for x in c6.QUEUE.read_text("utf-8").splitlines() if x.strip()]
check(len(rows2) == 1, "صف نباید بیش از یک ردیف داشته باشد")

# 5) seed با producer روشن نباید seed بسازد
_reset_queue()
check(c6.seed_default_hypothesis() is False, "producer روشن ⇒ seed خاموش")

# 6) queue pop: stale RUNNING => ABANDONED، malformed حفظ، id backfill
_reset_queue()
old = (time.time() - 72 * 3600)
stale_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(old))
lines = [
    "{bad-json",
    json.dumps({"id": "r-stale", "status": "RUNNING", "taken_at": stale_ts}),
    json.dumps({"status": "PENDING", "probe": "px", "subject": "sx"}),
]
c6.QUEUE.write_text("\n".join(lines) + "\n", encoding="utf-8")
h = c6._pop_next_hypothesis()
out_lines = c6.QUEUE.read_text("utf-8").splitlines()
check(any(x == "{bad-json" for x in out_lines), "خط malformed باید حفظ شود")
objs = [json.loads(x) for x in out_lines if not x.startswith("{bad")]
st = next(x for x in objs if x.get("id") == "r-stale")
check(st["status"] == "ABANDONED" and "verdict" not in st,
      "stale RUNNING باید بدون verdict به ABANDONED برود")
run = next(x for x in objs if x.get("status") == "RUNNING")
check(run.get("id", "").startswith("c6-") and h.get("id") == run.get("id"),
      "PENDING بی‌id باید id محتوامحور بگیرد")

# 7) mark فقط same-id؛ RUNNING دیگر دست‌نخورده
_reset_queue()
c6.QUEUE.write_text("\n".join([
    json.dumps({"id": "target", "status": "RUNNING"}),
    json.dumps({"id": "other", "status": "RUNNING"}),
]) + "\n", encoding="utf-8")
c6._mark_hypothesis("target", "accepted", True)
objs = [json.loads(x) for x in c6.QUEUE.read_text("utf-8").splitlines()]
check(next(x for x in objs if x["id"] == "target")["status"] == "DONE",
      "target باید بسته شود")
check(next(x for x in objs if x["id"] == "other")["status"] == "RUNNING",
      "RUNNING نامرتبط نباید بسته شود")

# 8) mechanism_count: سه‌خروجی + supported/falsified/inconclusive + gain bounded
for cnt, supported, inconc in [(9, True, False), (2, False, False), (-1, False, True)]:
    probes.PROBES.clear()
    probes.PROBES["px"] = {"measure": _fake_measure(cnt), "subject": "sx", "question": "qx", "floor": 3}
    ef, vf, box = c6._derive_fns({"kind": "mechanism_count", "probe": "px", "floor": 3}, {})
    out = ef({})
    acc = vf({}, out)
    check(isinstance(ef({}).get("count"), int), "experiment_fn باید dict با count بدهد")
    check(box.get("bench", {}).get("schema") == "c6-mechanism-count.v1",
          "box باید bench را ثبت کند")
    check(acc["supported"] is supported, f"supported برای count={cnt} باید {supported} باشد")
    check(bool((box.get("accept") or {}).get("inconclusive")) is inconc,
          f"inconclusive برای count={cnt} باید {inconc} باشد")
    gain = (box.get("accept") or {}).get("benchmark_gain", 0.0)
    check(0.0 <= gain <= 1.0, f"gain باید bounded باشد: {gain}")

# 9) propose-only: mechanism_count نباید بهبودِ اعمال‌شده ادعا کند
summary = c6._summarize({"kind": "mechanism_count", "question": "q"},
                        {"verdict": "accepted", "reason": "ok"}, box)
check("بازتولیدِ نقص" in summary, "خلاصه باید mechanism count را reproduction بداند")
check("اعمال‌شده" not in summary, "خلاصه نباید بهبودِ اعمال‌شده ادعا کند")

# 10) نباید ابتدایی خطرناک در ماژول‌های C2 باشد
for rel in ("c6_probes.py", "c6_producer.py"):
    src = (_OPS / rel).read_text("utf-8")
    check("subprocess" not in src and "urlopen(" not in src and "requests." not in src,
          f"{rel} نباید primitive خطرناک داشته باشد")

probes.PROBES.clear()
probes.PROBES.update(old_probes)
os.environ.pop("OCTOPUS_WIRE_C6_PRODUCER", None)

print("FAIL" if fails else "PASS", "— test_c6_hypothesis_producer")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
