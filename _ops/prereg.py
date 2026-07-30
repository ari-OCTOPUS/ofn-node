#!/usr/bin/env python3
"""prereg — پیش‌ثبتِ نیتِ چرخه، **قبل** از اجرا، append-only و fail-closed.

چرا فایلِ جدا و چرا قبل از اجرا (منشور §۴.۳ + الزامِ CROSS-SESSION-BRIEF:184):
target ای که بعد از دیدنِ نتیجه نوشته شود قابلِ جابه‌جایی است — همان
`alter_acceptance_criteria` که `PRE-0/governance.py` ممنوع کرده. پس target
این‌جا، روی دیسک، با mtime ِ قبل از اجرا منجمد می‌شود و `cycle_evaluator`
(ارزیابِ مستقل) فقط همین را می‌خواند — نه ادعای اجراکننده را.

قواعد:
  • **fail-closed:** ثبتِ ناموفق = چرخه اجرا نمی‌شود (صداکننده موظف است).
  • **append-only:** هیچ ردیفی ویرایش/حذف نمی‌شود؛ تصحیح = ردیفِ جدید.
  • **idempotent per cycle:** برای یک cycle_id فقط یک پیش‌ثبت؛ تکرار همان را
    برمی‌گرداند (دوبار-شلیک در یک اسلات ساختاراً بی‌اثر).
  • scope/forbidden صریح ثبت می‌شوند تا breach قابلِ‌ممیزی باشد.

$0 · stdlib · بدونِ فلگ (کتابخانه است؛ صداکننده‌اش flag-gated است).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "prereg.v1"
LEDGER = opslib.STATE_DIR / "test_cycle" / "prereg.jsonl"

# محدودهٔ مجاز و ممنوعِ پیش‌فرضِ هر چرخهٔ v1 — صریح، تا breach سنجش‌پذیر باشد.
_SCOPE = ("measure-only", "state/test_cycle/**")
_FORBIDDEN = ("external-send", "spend", "merge", "deploy", "restart",
              "flag-arm", "secret-read", "delete")

_REQUIRED = ("goal", "goal_key", "method", "metric_path", "metric_key",
             "baseline", "target", "deadline_cycles", "direction")

# میدان‌هایی که «همان هدف» را تعریف می‌کنند. اگر هرکدام با پیش‌ثبتِ موجودِ همان
# چرخه فرق کند، این دیگر همان چرخه نیست و idempotency دروغ است.
_IDENTITY = ("goal_key", "method_index", "metric_path", "metric_key",
             "baseline", "target")


def _from_proposal(p: dict, key: str):
    """مقدارِ میدانِ هویتی از پیشنهاد — با همان پیش‌فرض‌هایی که `register` می‌نویسد."""
    if key == "method_index":
        return p.get("method_index", 0)
    return p.get(key)


def _norm(v):
    """مقایسهٔ مقاومِ نوع: `0` و `0.0` یک عددند؛ dict ِ target ترتیب‌ناپذیر است."""
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, (int, float)):
        return ("num", float(v))
    if isinstance(v, dict):
        return ("dict", tuple(sorted((str(k), _norm(x)) for k, x in v.items())))
    return ("str", str(v))


def rows() -> list:
    """همهٔ ردیف‌های پیش‌ثبت (fail-soft؛ ردیفِ خراب رد می‌شود)."""
    out: list = []
    try:
        if not LEDGER.exists():
            return out
        with open(LEDGER, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("schema") == SCHEMA:
                    out.append(d)
    except OSError:
        pass
    return out


def for_cycle(cycle_id: str) -> "dict | None":
    for r in rows():
        if r.get("cycle_id") == cycle_id:
            return r
    return None


def register(proposal: dict, *, cycle: str, now: "float | None" = None) -> dict:  # noqa: ARG001
    """نیت را پیش‌ثبت کن. شکست در اعتبار یا نوشتن = ok=False (صداکننده نباید اجرا کند).

    اعتبار این‌جا **دوباره** چک می‌شود — به مولد اعتماد نمی‌کنیم؛ اگر روزی مولدِ
    دیگری (مغز) کاندیدا بدهد، همین گیت جلوی هدفِ بی‌ترازو را می‌گیرد."""
    if not isinstance(proposal, dict):
        return {"ok": False, "reason": "bad-proposal"}
    missing = [k for k in _REQUIRED if proposal.get(k) in (None, "")]
    if missing:
        return {"ok": False, "reason": "invalid-proposal",
                "missing": missing}
    t = proposal.get("target")
    if not (isinstance(t, dict) and t.get("op") in (">", ">=")
            and isinstance(t.get("value"), (int, float))
            and not isinstance(t.get("value"), bool)):
        return {"ok": False, "reason": "bad-target"}
    existing = for_cycle(str(cycle))
    if existing is not None:
        # ⚠️ idempotent فقط وقتی که **همان** هدف باشد. نسخهٔ اول هر پیشنهادی را
        # با `ok=True` می‌پذیرفت و ردیفِ قدیمی را برمی‌گرداند — سناریوی خطر:
        #   ۱) هدفِ A برای این چرخه پیش‌ثبت می‌شود
        #   ۲) اجرا قبل از `_mark_done` شکست می‌خورد ⇒ اسلات هنوز due است
        #   ۳) تیکِ بعد (مثلاً بعد از رسیدنِ حکمِ FAIL) مولد هدفِ B می‌دهد
        #   ۴) register(B) با ok=True ردیفِ A را برمی‌گرداند
        #   ۵) چرخه B را **اجرا** می‌کند ولی ارزیاب بعداً A را می‌سنجد
        # یعنی هدفِ اجراشده با هدفِ منجمدشده فرق می‌کرد — و کلِ ادعای
        # «target قبل از اجرا قفل شد» بی‌معنا می‌شد. حالا هویت تطبیق می‌شود.
        drift = [k for k in _IDENTITY
                 if _norm(existing.get(k)) != _norm(_from_proposal(proposal, k))]
        if drift:
            return {"ok": False, "reason": "cycle-prereg-mismatch",
                    "drift": drift, "prereg_id": existing.get("prereg_id"),
                    "frozen": {k: existing.get(k) for k in drift}}
        return {"ok": True, "idempotent": True, "prereg_id": existing.get("prereg_id"),
                "row": existing}
    prereg_id = f"{cycle}:{proposal.get('goal_key')}"
    rec = {
        "schema": SCHEMA, "ts": opslib.now_iso(), "prereg_id": prereg_id,
        "cycle_id": str(cycle),
        "goal": str(proposal.get("goal"))[:400],
        "goal_key": str(proposal.get("goal_key")),
        "goal_source": str(proposal.get("goal_source") or "self")[:40],
        "direction": str(proposal.get("direction"))[:300],
        "method": str(proposal.get("method"))[:400],
        "method_index": proposal.get("method_index", 0),
        "hypothesis": str(proposal.get("why") or "")[:400],
        "metric_path": str(proposal.get("metric_path")),
        "metric_key": str(proposal.get("metric_key")),
        "baseline": proposal.get("baseline"),
        "target": {"op": t["op"], "value": t["value"]},
        "deadline_cycles": int(proposal.get("deadline_cycles", 2)),
        "allowed_scope": list(_SCOPE),
        "forbidden_actions": list(_FORBIDDEN),
        "expected_evidence": "جفتِ قبل/بعدِ عددیِ همین سنجه روی دیسک + حکمِ ارزیابِ مستقل",
        "rollback": "append-only؛ ابطال فقط با ردیفِ حکمِ VOID از ارزیاب/مالک",
        "stop_condition": "STOP-ORGANISM / HALT-ALL / فلگِ خاموش — هر سه چرخه را می‌ایستانند",
        "required_owner_gate": "هیچ (measure-only)؛ هر اقدامِ فراتر از سنجش = کارتِ رأی",
    }
    try:
        opslib.append_jsonl(LEDGER, rec)
    except (OSError, ValueError):
        return {"ok": False, "reason": "write-failed"}
    return {"ok": True, "prereg_id": prereg_id, "row": rec}


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"rows": len(rows()), "ledger": str(LEDGER)},
                     ensure_ascii=False, indent=1))
