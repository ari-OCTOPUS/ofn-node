# -*- coding: utf-8 -*-
# TARGET (owner wires in worktree): F:\backup\_ops\doctor\rules_store.py
"""
rules_store — انبارِ «قوانینِ رفتاری» (behavioral RULES) — stdlib فقط، inert تا import.

چرا (Why): حلقهٔ یادگیریِ اختاپوس (G1/P3) شواهد و پیشنهاد و ledger دارد، ولی «حافظهٔ
درس‌های ماندگار» ندارد. یک RULE = تقطیرِ یک review ِ پذیرفته‌شده به یک قانونِ کوتاه، تا
**همان کلاسِ خطا دوبار تکرار نشود** (معیارِ rule_recurrence = 0).

این چیست و چه چیزی نیست:
  * یک ledgerِ append-only با hash-chain (همان الگوی chord/ledger.py و epistemics)
    که فقط RULEها و «رخدادِ تکرار» را نگه می‌دارد.
  * NOT یک policy-engine و NOT رقیبِ chord/repair_policy (که داورِ ریسک است) و NOT
    رقیبِ genome. این فقط «حافظهٔ درس» است؛ هیچ verdictی صادر نمی‌کند و هیچ اجرایی ندارد.

قواعدِ ساختاری (safety by construction):
  * تغییرناپذیر: حذف نداریم؛ retire = یک رکوردِ tombstone روی همان زنجیره.
  * fail-closed: RULE ِ بی‌منبع/بی‌check رد می‌شود.
  * dedup بر اساسِ error_class: هر کلاسِ خطا فقط یک RULE ِ active دارد (ضدِ تورم).
  * مسیر relative به خودِ پکیج resolve می‌شود (نه CWD/env — تلهٔ ORG_ROOT vault).
    override فقط برای تست: env RULES_STORE_DIR.
  * هرگز روی ledgerِ مالی/genome/state ارگانیسم نمی‌نویسد — فقط state/rules-ledger.jsonl خودش.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

_LEDGER_NAME = "rules-ledger.jsonl"
STATUS = ("active", "retired")
SEVERITY = ("low", "medium", "high", "critical")

# انواعِ رکوردِ روی زنجیره
KIND_RULE = "rule"
KIND_RETIRE = "retire"
KIND_OCCURRENCE = "occurrence"   # رخدادِ دوبارهٔ یک کلاسِ خطا (سنجهٔ recurrence)


# ── helpers ──────────────────────────────────────────────────────────
def _sha256_of(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _now_ts() -> float:
    return time.time()


def new_rule_id() -> str:
    return f"RULE-{time.strftime('%Y%m%d', time.gmtime())}-{uuid.uuid4().hex[:6]}"


def _norm_class(error_class: str) -> str:
    """کلاسِ خطا را نرمال می‌کند تا dedup/شمارش پایدار باشد."""
    return " ".join((error_class or "").strip().lower().split())


def state_dir() -> Path:
    env = os.environ.get("RULES_STORE_DIR", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "state"


def ledger_path() -> Path:
    return state_dir() / _LEDGER_NAME


# ── data model ───────────────────────────────────────────────────────
@dataclass
class Rule:
    """یک قانونِ رفتاریِ ماندگار. کوتاه، قابلِ‌بررسی، با منبع."""
    error_class: str                 # کلاسِ خطا (مثلاً "budget/KeyError price_out")
    never_again: str                 # درسِ یک‌خطی (چه کاری دیگر نکن/بکن)
    check: str                       # چطور runner/checklist این را می‌گیرد
    source_trace: str                # trace_id/آدرسِ شاهد — خالی ممنوع (provenance)
    severity: str = "medium"
    added_by: str = "owner"          # accept انسانی منبعِ قانون است
    status: str = "active"
    rule_id: str = field(default_factory=new_rule_id)
    added_ts: float = field(default_factory=_now_ts)

    def validate(self) -> List[str]:
        errs: List[str] = []
        if not _norm_class(self.error_class):
            errs.append("error_class-empty")
        if not (self.never_again or "").strip():
            errs.append("never_again-empty")
        if not (self.check or "").strip():
            errs.append("check-empty (چطور گرفته می‌شود؟)")
        if not (self.source_trace or "").strip():
            errs.append("source_trace-empty (provenance اجباری)")
        if self.severity not in SEVERITY:
            errs.append(f"severity-invalid:{self.severity}")
        if self.status not in STATUS:
            errs.append(f"status-invalid:{self.status}")
        return errs

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── low-level chain I/O (mirror chord/ledger pattern) ────────────────
def _read_all() -> List[Dict[str, Any]]:
    p = ledger_path()
    if not p.exists() or p.stat().st_size == 0:
        return []
    out: List[Dict[str, Any]] = []
    for ln in p.read_text("utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:  # noqa: BLE001 — خطِ خراب را می‌شماریم نه اینکه بترکیم
            out.append({"_corrupt": True, "raw": ln[:200]})
    return out


def _last(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return records[-1] if records else None


def _append(kind: str, body: Dict[str, Any], dedup_key: str = "") -> Dict[str, Any]:
    p = ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    records = _read_all()
    last = _last(records)
    if dedup_key and last and last.get("dedup_key") == dedup_key:
        return {"ok": True, "skipped": "dedup", "path": str(p)}
    rec = {"kind": kind, **body,
           "prev_sha256": (last or {}).get("sha256", ""),
           "dedup_key": dedup_key,
           "chain_ts": _now_ts()}
    rec["sha256"] = _sha256_of({k: v for k, v in rec.items() if k != "sha256"})
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    return {"ok": True, "sha256": rec["sha256"], "path": str(p)}


# ── public API ───────────────────────────────────────────────────────
def add_rule(rule: Rule) -> Dict[str, Any]:
    """یک RULE ِ جدید ثبت می‌کند. fail-closed. dedup بر اساسِ error_class ِ active.
    خروجی: {ok, rule_id?, errors?, skipped?}."""
    errs = rule.validate()
    if errs:
        return {"ok": False, "errors": errs}
    cls = _norm_class(rule.error_class)
    if any(_norm_class(r.get("error_class", "")) == cls for r in list_active()):
        return {"ok": True, "skipped": "active-rule-exists-for-class", "error_class": cls}
    res = _append(KIND_RULE, rule.to_dict(), dedup_key=f"rule:{cls}")
    res["rule_id"] = rule.rule_id
    return res


def list_active() -> List[Dict[str, Any]]:
    """RULEهای فعال (با درنظرگرفتنِ retireها). آخرین وضعیتِ هر rule_id ملاک است."""
    retired = set()
    rules: Dict[str, Dict[str, Any]] = {}
    for rec in _read_all():
        if rec.get("_corrupt"):
            continue
        if rec.get("kind") == KIND_RULE:
            rules[rec.get("rule_id", "")] = rec
        elif rec.get("kind") == KIND_RETIRE:
            retired.add(rec.get("rule_id", ""))
    return [r for rid, r in rules.items() if rid and rid not in retired]


def get(rule_id: str) -> Optional[Dict[str, Any]]:
    for rec in _read_all():
        if rec.get("kind") == KIND_RULE and rec.get("rule_id") == rule_id:
            return rec
    return None


def retire(rule_id: str, reason: str, by: str = "owner") -> Dict[str, Any]:
    """بازنشستگیِ یک RULE — بدونِ حذف؛ فقط tombstone روی زنجیره."""
    if not get(rule_id):
        return {"ok": False, "errors": [f"unknown-rule:{rule_id}"]}
    if not (reason or "").strip():
        return {"ok": False, "errors": ["reason-empty"]}
    return _append(KIND_RETIRE, {"rule_id": rule_id, "reason": reason.strip(), "by": by})


def record_occurrence(error_class: str, source_trace: str) -> Dict[str, Any]:
    """یک رخدادِ دوبارهٔ کلاسِ خطا را ثبت می‌کند. اگر RULE ِ active برای این کلاس
    باشد، یعنی «قانون نتوانست جلویش را بگیرد» → recurrence (زنگِ خطرِ harness)."""
    cls = _norm_class(error_class)
    if not cls:
        return {"ok": False, "errors": ["error_class-empty"]}
    covered = any(_norm_class(r.get("error_class", "")) == cls for r in list_active())
    res = _append(KIND_OCCURRENCE, {"error_class": cls, "source_trace": source_trace,
                                    "covered_by_active_rule": covered})
    res["recurrence"] = covered
    return res


def recurrence_count(error_class: str) -> int:
    """چند بار این کلاسِ خطا **پس از** داشتنِ یک RULE ِ active دوباره رخ داده."""
    cls = _norm_class(error_class)
    return sum(1 for rec in _read_all()
               if rec.get("kind") == KIND_OCCURRENCE
               and _norm_class(rec.get("error_class", "")) == cls
               and rec.get("covered_by_active_rule"))


def metrics() -> Dict[str, Any]:
    """سنجه‌های خلاصه برای صفحهٔ یادگیری/تلگرام."""
    recs = _read_all()
    active = list_active()
    recurrences = [r for r in recs if r.get("kind") == KIND_OCCURRENCE and r.get("covered_by_active_rule")]
    return {
        "active_rules": len(active),
        "total_events": len(recs),
        "recurrences": len(recurrences),      # هدف: 0
        "chain": verify_chain(),
    }


def verify_chain(limit: int = 500) -> Dict[str, Any]:
    """راستی‌آزماییِ hash-chain روی nتای آخر."""
    recs = _read_all()[-limit:]
    if not recs:
        return {"ok": True, "checked": 0, "note": "empty"}
    bad, prev = 0, None
    for rec in recs:
        if rec.get("_corrupt"):
            bad += 1
            continue
        expect = _sha256_of({k: v for k, v in rec.items() if k != "sha256"})
        if rec.get("sha256") != expect:
            bad += 1
        elif prev is not None and rec.get("prev_sha256") != prev:
            bad += 1
        prev = rec.get("sha256")
    return {"ok": bad == 0, "checked": len(recs), "bad": bad}


if __name__ == "__main__":
    import tempfile
    os.environ["RULES_STORE_DIR"] = tempfile.mkdtemp(prefix="rules_smoke_")
    r = Rule(error_class="budget/KeyError price_out",
             never_again="هرگز organ_gate را بدونِ قفلِ price_out صدا نزن",
             check="test_budget_locks::test_price_out_locked باید سبز باشد",
             source_trace="RUN-smoke-001", severity="high")
    assert add_rule(r)["ok"], add_rule(r)
    assert add_rule(r).get("skipped"), "dedup باید فعال باشد"
    assert len(list_active()) == 1
    record_occurrence("budget/KeyError price_out", "RUN-smoke-002")
    assert recurrence_count("budget/KeyError price_out") == 1
    assert retire(r.rule_id, "کلاس ادغام شد")["ok"]
    assert len(list_active()) == 0
    assert verify_chain()["ok"]
    print("rules_store smoke ok:", metrics())
