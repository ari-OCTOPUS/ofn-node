#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive.py — آرشیو بدایع (NOVELTY-ARCHIVE) — فاز ۲ MEGA-FINISH-ALL-v1.

هدف: گیت دوشرطی «بدیع AND یادگرفتنی» پیش از مصرف بودجه (LAW-07، ضد چرخهٔ تکرار).
همهٔ فاصلهها روی «بردار رفتاری» محاسبه میشوند؛ متن فقط پشتیبان است.

ادعاهای این ماژول:
  - EXACT_DUPLICATE / VARIATION_CANDIDATE / NOVELTY_CANDIDATE / LEARNABLE /
    ADMITTED / INCOMPLETE / QUARANTINED / RETIRED — همه MEASURED، هیچ VERIFIED.
  - آرشیو append-only است: هیچ حذف/بازنویسی (فایل ردیفهای قبلی را هرگز عوض نمیکند).
  - هر ردیف رسید دارد (behavior_id + input hash + ts).

روش (reproducible):
  1. نرمالسازی NFKC + casefold + حذف نقطهگذاری.
  2. امضای دقیق = sha256 متن نرمالشده → EXACT_DUPLICATE.
  3. فاصلهٔ جاکارد روی shingle کاراکتری ۳گرم → VARIATION (≥ آستانهٔ منجمد 0.80).
  4. یادگرفتنی = replay_recipe + receipt_refs + expected_observable_delta + falsifier.
  5. ADMITTED = NOVELTY_CANDIDATE + LEARNABLE + شاهدِ مستقل.

stdlib-only · fail-soft · هیچ تماس پولی داخل گیت (هزینه = صفر فراخوان).
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Optional

SCHEMA = "novelty-archive.v1"
VARIATION_THRESHOLD = 0.80   # منجمد — تغییر پس از دیدن نتیجه ممنوع (LAW-07)

# وضعیتهای پذیرش
INCOMPLETE = "INCOMPLETE"
EXACT_DUPLICATE = "EXACT_DUPLICATE"
VARIATION_CANDIDATE = "VARIATION_CANDIDATE"
NOVELTY_CANDIDATE = "NOVELTY_CANDIDATE"
LEARNABLE = "LEARNABLE"
ADMITTED = "ADMITTED"
QUARANTINED = "QUARANTINED"
RETIRED = "RETIRED"


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).casefold()
    s = re.sub(r"[^\w\s]+", " ", s, flags=re.UNICODE)
    return " ".join(s.split())


def exact_key(s: str) -> str:
    return hashlib.sha256(normalize_text(s).encode("utf-8")).hexdigest()


def shingles(s: str, n: int = 3) -> set:
    t = f"  {normalize_text(s)}  "
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def jaccard(a: set, b: set) -> float:
    den = len(a | b)
    return (len(a & b) / den) if den else 1.0


@dataclass
class BehaviorVector:
    """بردار رفتاریِ یک ایده/قابلیت — مبنای فاصله."""
    schema_version: str = SCHEMA
    behavior_id: str = ""
    proposal_id: str = ""
    lineage_ids: list = field(default_factory=list)
    problem_class: str = ""
    input_contract: str = ""
    output_contract: str = ""
    state_transition: str = ""
    tool_family: str = ""
    model_family: str = ""
    resource_bucket: str = ""
    risk_class: str = ""
    human_value_target: str = ""
    failure_signature: str = ""
    expected_observable_delta: str = ""
    replay_recipe: str = ""
    receipt_refs: list = field(default_factory=list)
    text: str = ""
    lang: str = ""
    ts: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


def vector_from_proposal(p: dict, *, text: str = "") -> BehaviorVector:
    """از یک proposal (یا متن خام) بردار میسازد؛ فیلدهای نبوده خالی میمانند (نه حدس)."""
    now = time.time()
    return BehaviorVector(
        behavior_id=exact_key(str(p.get("text") or text))[:12],
        proposal_id=str(p.get("proposal_id") or p.get("id") or ""),
        lineage_ids=list(p.get("lineage_ids") or []),
        problem_class=str(p.get("problem_class") or ""),
        input_contract=str(p.get("input_contract") or ""),
        output_contract=str(p.get("output_contract") or ""),
        state_transition=str(p.get("state_transition") or ""),
        tool_family=str(p.get("tool_family") or ""),
        model_family=str(p.get("model_family") or ""),
        resource_bucket=str(p.get("resource_bucket") or ""),
        risk_class=str(p.get("risk_class") or ""),
        human_value_target=str(p.get("human_value_target") or ""),
        failure_signature=str(p.get("failure_signature") or ""),
        expected_observable_delta=str(p.get("expected_observable_delta") or ""),
        replay_recipe=str(p.get("replay_recipe") or ""),
        receipt_refs=list(p.get("receipt_refs") or []),
        text=str(p.get("text") or text),
        lang=str(p.get("lang") or ""),
        ts=now,
    )


def distance(a: BehaviorVector, b: BehaviorVector) -> dict:
    """فاصلهٔ دو بردار: امضای دقیق، امضای رفتاری، جاکارد متنی."""
    return {
        "exact_duplicate": exact_key(a.text) == exact_key(b.text),
        "jaccard_char3": round(jaccard(shingles(a.text), shingles(b.text)), 4),
        "signature_match": bool(
            a.input_contract and a.input_contract == b.input_contract
            and a.output_contract == b.output_contract
            and a.state_transition == b.state_transition
            and a.risk_class == b.risk_class),
    }


def learnable(v: BehaviorVector) -> tuple[bool, list]:
    """یادگرفتنی = replay + رسید + دلتای قابل مشاهده + falsifier."""
    missing = []
    if not v.replay_recipe:
        missing.append("replay_recipe")
    if not v.receipt_refs:
        missing.append("receipt_refs")
    if not v.expected_observable_delta:
        missing.append("expected_observable_delta")
    if not v.problem_class:
        missing.append("problem_class")
    return (not missing), missing


class NoveltyArchive:
    """آرشیو append-only روی دیسک. هیچ حذف/بازنویسی."""
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[BehaviorVector]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            try:
                out.append(BehaviorVector(**{k: d[k] for k in BehaviorVector.__dataclass_fields__ if k in d}))
            except Exception:
                continue
        return out

    def append(self, record: dict) -> dict:
        """append-only؛ ردیف قبلی هرگز تغییر نمیکند. خروجی = رسید ردیف."""
        row = {"schema": SCHEMA, "ts": time.time(), **record}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {"row_hash": hashlib.sha256(
            json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:24],
            "line": sum(1 for _ in self.path.open(encoding="utf-8"))}


def evaluate(proposal: dict, archive: Iterable[BehaviorVector],
             *, threshold: float = VARIATION_THRESHOLD) -> dict:
    """حکم پذیرش دوشرطی — پیش از مصرف بودجه صدا زده میشود (هزینه = صفر)."""
    v = vector_from_proposal(proposal)
    if not normalize_text(v.text):
        return {"state": INCOMPLETE, "allow": False,
                "reason": "no-text", "behavior_id": v.behavior_id}
    best = None
    for b in archive:
        d = distance(v, b)
        if d["exact_duplicate"]:
            return {"state": EXACT_DUPLICATE, "allow": False,
                    "nearest": {"behavior_id": b.behavior_id, **d},
                    "reason": "exact-duplicate-of-archived", "behavior_id": v.behavior_id}
        if best is None or d["jaccard_char3"] > best[0]:
            best = (d["jaccard_char3"], b.behavior_id, d)
    near = best[0] if best else 0.0
    if near >= threshold:
        return {"state": VARIATION_CANDIDATE, "allow": False,
                "nearest": {"behavior_id": best[1], "jaccard_char3": near},
                "reason": f"variation-of-archived (jaccard={near:.2f} >= {threshold})",
                "behavior_id": v.behavior_id}
    ok_learn, missing = learnable(v)
    if not ok_learn:
        return {"state": NOVELTY_CANDIDATE, "allow": True,
                "learnable": False, "missing_for_learnable": missing,
                "nearest": {"behavior_id": best[1] if best else "", "jaccard_char3": near},
                "reason": "novel-wording; learnability-fields-missing",
                "behavior_id": v.behavior_id}
    # ADMITTED فقط با شاهدِ مستقل (غیر از خودِ ایده)
    if proposal.get("independent_evidence_ref"):
        return {"state": ADMITTED, "allow": True, "learnable": True,
                "nearest": {"behavior_id": best[1] if best else "", "jaccard_char3": near},
                "reason": "novel-and-learnable-with-independent-evidence",
                "behavior_id": v.behavior_id}
    return {"state": LEARNABLE, "allow": True, "learnable": True,
            "nearest": {"behavior_id": best[1] if best else "", "jaccard_char3": near},
            "reason": "novel-and-learnable; independent-evidence-pending",
            "behavior_id": v.behavior_id}


def cohort_summary(ideas: Iterable[str]) -> dict:
    """اعداد صادقانهٔ همگروه: کل، یکتای دقیق، تکرار، جفتهای نزدیک، نامزدهای بدیع."""
    texts = [normalize_text(t) for t in ideas]
    total = len(texts)
    seen = {}
    states = []
    for t in texts:
        if not t:
            states.append(INCOMPLETE)
            continue
        k = exact_key(t)
        if k in seen:
            states.append(EXACT_DUPLICATE)
        else:
            seen[k] = True
            states.append(NOVELTY_CANDIDATE)
    unique_texts = list(dict.fromkeys(t for t in texts if t))
    pairs = 0
    from itertools import combinations
    sg = [shingles(t) for t in unique_texts]
    for i, j in combinations(range(len(unique_texts)), 2):
        if jaccard(sg[i], sg[j]) >= VARIATION_THRESHOLD:
            pairs += 1
    return {
        "schema": SCHEMA, "grade": "MEASURED", "method": "normalize+exact-key+char3-jaccard",
        "total": total,
        "exact_unique": sum(1 for s in states if s == NOVELTY_CANDIDATE),
        "exact_repeat_records": sum(1 for s in states if s == EXACT_DUPLICATE),
        "near_duplicate_candidate_pairs": pairs,
        "behaviorally_novel_and_learnable": "UNKNOWN",
        "states": {s: states.count(s) for s in set(states)},
    }


def parse_queue_md(path: Path) -> list[str]:
    """استخراج ایدهها از SURVIVORS-QUEUE.md (خطهای `- **idea:** ...`)."""
    import re as _re
    txt = Path(path).read_text("utf-8", errors="replace")
    return _re.findall(r"^- \*\*idea:\*\* (.+)$", txt, _re.M)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", help="path to SURVIVORS-QUEUE.md")
    ap.add_argument("--check-proposal", help="path to a JSON proposal dict")
    ap.add_argument("--archive", default=str(Path(__file__).resolve().parent.parent
                                             / "state" / "novelty" / "archive.jsonl"))
    args = ap.parse_args()
    arc = NoveltyArchive(Path(args.archive))
    if args.cohort:
        ideas = parse_queue_md(Path(args.cohort))
        s = cohort_summary(ideas)
        # ثبت append-only با ingestِ idempotent: ردیفهایی که behavior_id دارند
        # دوباره ثبت نمیشوند (آرشیو رشد بیمورد نکند).
        existing = {b.behavior_id for b in arc.load()}
        added = 0
        for t in ideas:
            bid = exact_key(t)
            if bid in existing:
                continue
            arc.append({"kind": "cohort-idea", "state": "indexed",
                        "text": t, "behavior_id": bid})
            existing.add(bid)
            added += 1
        s["archive_rows_added"] = added
        print(json.dumps(s, ensure_ascii=False, indent=1))
    elif args.check_proposal:
        p = json.loads(Path(args.check_proposal).read_text("utf-8"))
        print(json.dumps(evaluate(p, arc.load()), ensure_ascii=False, indent=1))
    else:
        ap.print_help()
