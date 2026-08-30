#!/usr/bin/env python3
"""acct_memory.py — حافظهٔ ضدِ فراموشیِ حسابدار (2026-07-16، الگوی شرکت‌های ۲۰۲۷).

مسئله (اسکنِ ارگانیسم): دانشِ مالک فرّار بود — suggestionها با /sync گم می‌شدند،
fine-categories.json یتیم بود، و هیچ قاعده‌ای از تأییدها یاد گرفته نمی‌شد (attributor استاتیک).

طرح (الگوی Ramp/Vic.ai — قاعدهٔ vendor با provenance، نه «هوشِ» مبهم):
  * **قاعدهٔ merchant** از تراکنش‌های *تأییدشدهٔ مالک* استخراج می‌شود — کلید = tokenِ
    نرمالِ merchant؛ مقدار = {owner, ptype, category?, sample_count, exception_count,
    last_seen, version}. قاعده فقط وقتی «فعال» است که sample_count ≥ MIN و
    exception_rate ≤ MAX — یک تأییدِ تکی هرگز قاعده نمی‌سازد (ضدِ تکثیرِ اشتباه).
  * **بازتولیدپذیر (ضدِ فراموشیِ ساختاری):** قواعد همیشه قابلِ بازساخت از txn-storeاند
    (منبعِ ماندگار)؛ فایلِ حافظه فقط کش است — sync/crash هیچ دانشی را نمی‌کشد.
  * **دفترچهٔ تصمیم‌ها (append-only):** هر rebuild یک خطِ خلاصه در decisions.jsonl —
    ردِ زمانیِ یادگیری برای audit.
  * **دیتاستِ طلایی + سنجهٔ drift (روش ۹):** export_golden از تأییدها؛ evaluate قواعد را
    روی همان می‌سنجد — دقتِ پایین = هشدار، نه سکوت.
  * **propose-only مطلق:** خروجیِ این حافظه فقط «پیشنهادِ حدس» برای کارتِ /review است؛
    هرگز auto-confirm، هرگز ثبت.

فایل‌ها (gitignored، در personal/): acct-memory.json (کشِ قواعد) · acct-decisions.jsonl.
$0 · stdlib · fail-soft خواندن، atomic نوشتن.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

MIN_SAMPLES = 3            # قاعده با کمتر از این هرگز فعال نمی‌شود (ضدِ تک‌نمونه)
MAX_EXCEPTION_RATE = 0.2   # اگر مالک ۲۰٪+ خلافِ قاعده تأیید کرد، قاعده غیرفعال
_SCHEMA = "acct-memory.v1"

# tokenهای بی‌ارزش که merchant نیستند (کلمه‌های عمومیِ بانکی)
_STOP = {"payment", "from", "to", "transfer", "direct", "debit", "credit", "card",
         "visa", "eftpos", "pty", "ltd", "the", "and", "aus", "au", "nsw", "purchase",
         "online", "banking", "bpay", "osko", "ref", "reference"}


def _memory_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "acct-memory.json"


def _decisions_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "acct-decisions.jsonl"


def _store_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "txn-store.json"


def merchant_key(desc: object) -> str:
    """tokenِ نرمالِ merchant از desc — قطعی، بدونِ عدد/نویز. '' یعنی قابلِ‌کلید نیست."""
    s = re.sub(r"[\d#*]+", " ", str(desc or "").lower())
    words = [w for w in re.split(r"[^a-z؀-ۿ]+", s) if len(w) >= 3 and w not in _STOP]
    return " ".join(words[:3])


def _load_txns(path: Path | None = None) -> list[dict]:
    p = path or _store_path()
    try:
        doc = json.loads(p.read_text("utf-8")) if p.exists() else None
    except (OSError, ValueError):
        return []
    if isinstance(doc, dict):
        t = doc.get("txns") or []
        return t if isinstance(t, list) else []
    return doc if isinstance(doc, list) else []


def rebuild(store_path: Path | None = None, memory_path: Path | None = None) -> dict:
    """قواعد را از تأییدهای مالک بازبساز (idempotent، بازتولیدپذیر). فقط confirmedها
    نمونه‌اند؛ برچسبِ اکثریت قاعده می‌شود و اقلیت exception شمرده می‌شود."""
    txns = _load_txns(store_path)
    buckets: dict = {}
    confirmed = 0
    for t in txns:
        if not isinstance(t, dict) or t.get("review") != "confirmed":
            continue
        key = merchant_key(t.get("desc"))
        if not key:
            continue
        confirmed += 1
        lbl = (str(t.get("owner", "")), str(t.get("ptype", "")))
        b = buckets.setdefault(key, {})
        b[lbl] = b.get(lbl, 0) + 1
    rules: dict = {}
    for key, votes in buckets.items():
        total = sum(votes.values())
        (owner, ptype), top = max(votes.items(), key=lambda kv: kv[1])
        exceptions = total - top
        rate = exceptions / total if total else 1.0
        rules[key] = {"owner": owner, "ptype": ptype,
                      "sample_count": total, "exception_count": exceptions,
                      "active": total >= MIN_SAMPLES and rate <= MAX_EXCEPTION_RATE,
                      "last_rebuilt": opslib.now_iso()}
    doc = {"_schema": _SCHEMA, "version": opslib.now_iso(),
           "confirmed_seen": confirmed, "rules": rules}
    mp = memory_path or _memory_path()
    try:
        mp.parent.mkdir(parents=True, exist_ok=True)
        tmp = mp.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, mp)
    except (OSError, TypeError, ValueError):
        return {"ok": False, "error": "نوشتنِ حافظه شکست", "rules": len(rules)}
    active = sum(1 for r in rules.values() if r["active"])
    try:
        opslib.append_jsonl(_decisions_path() if memory_path is None
                            else mp.parent / "acct-decisions.jsonl",
                            {"ts": opslib.now_iso(), "action": "rebuild",
                             "confirmed": confirmed, "rules": len(rules), "active": active})
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "rules": len(rules), "active": active, "confirmed_seen": confirmed}


def _load_rules(memory_path: Path | None = None) -> dict:
    p = memory_path or _memory_path()
    try:
        d = json.loads(p.read_text("utf-8")) if p.exists() else {}
        return d.get("rules", {}) if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def suggest(desc: object, memory_path: Path | None = None) -> dict | None:
    """پیشنهادِ حافظه برای یک desc — فقط قاعدهٔ *فعال*. None = حافظه نظری ندارد.
    خروجی: {owner, ptype, basis, sample_count} — **پیشنهاد است، نه حکم** (مالک تأیید می‌کند)."""
    key = merchant_key(desc)
    if not key:
        return None
    rules = _load_rules(memory_path)
    words = key.split()
    # fallbackِ پیشوندی: descهای یک merchant پسوندهای متغیر دارند (شعبه/تاریخ) —
    # کلیدِ کامل، بعد دو-کلمه، بعد تک‌کلمه. اولین قاعدهٔ *فعال* برنده.
    for k in (" ".join(words[:3]), " ".join(words[:2]), words[0]):
        r = rules.get(k)
        if isinstance(r, dict) and r.get("active"):
            return {"owner": r["owner"], "ptype": r["ptype"],
                    "basis": f"memory:{r['sample_count']}نمونه",
                    "sample_count": r["sample_count"]}
    return None


def export_golden(store_path: Path | None = None, limit: int = 500) -> list[dict]:
    """دیتاستِ طلایی از تأییدهای مالک (روش ۹) — descِ scrub‌شده + برچسبِ درست.
    برای evaluate/درفت؛ بدونِ مبلغ (سنجشِ دسته‌بندی به مبلغ نیاز ندارد → کمینهٔ PII)."""
    out = []
    for t in _load_txns(store_path):
        if not isinstance(t, dict) or t.get("review") != "confirmed":
            continue
        key = merchant_key(t.get("desc"))
        if not key:
            continue
        out.append({"merchant_key": key, "owner": str(t.get("owner", "")),
                    "ptype": str(t.get("ptype", ""))})
        if len(out) >= limit:
            break
    return out


def evaluate(store_path: Path | None = None, memory_path: Path | None = None) -> dict:
    """قواعدِ فعال را روی دیتاستِ طلایی بسنج (leave-in، سنجهٔ drift — نه اثباتِ تعمیم).
    خروجی: coverage (چند درصدِ طلایی قاعدهٔ فعال دارد) و accuracy (چند درصدشان درست)."""
    golden = export_golden(store_path)
    if not golden:
        return {"ok": False, "note": "طلایی خالی — هنوز تأییدی نیست", "n": 0}
    rules = _load_rules(memory_path)
    covered = correct = 0
    for g in golden:
        r = rules.get(g["merchant_key"])
        if not isinstance(r, dict) or not r.get("active"):
            continue
        covered += 1
        if r["owner"] == g["owner"] and r["ptype"] == g["ptype"]:
            correct += 1
    n = len(golden)
    return {"ok": True, "n": n, "covered": covered,
            "coverage_pct": round(100 * covered / n, 1),
            "accuracy_pct": round(100 * correct / covered, 1) if covered else None,
            "drift_alarm": bool(covered and (correct / covered) < 0.9)}


if __name__ == "__main__":
    print(json.dumps({"rebuild": rebuild(), "eval": evaluate()}, ensure_ascii=False, indent=1))
