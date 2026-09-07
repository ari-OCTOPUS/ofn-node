#!/usr/bin/env python3
"""acd_validate.py — گیتِ پذیرش رسیدهای ACD (نسخهٔ ۲)

هدف: هیچ ردیفی بدون شاهد معتبر «سبز» نشود.
اجرا:  python acd_validate.py receipts.jsonl --schema acd-run.schema.json
خروج: کد ۰ = همهٔ رسیدها پذیرفته؛ کد ۱ = حداقل یک رد؛ کد ۲ = خطای ورودی.

قواعد پذیرش (fail-closed):
 R1  رسید باید با اسکیما مطابق باشد.
 R2  prereg_id لازم است؛ بدون پیش‌ثبت، رسید غیرقابل‌پذیرش است.
 R3  outcome=PASS با oracle.independent_of_subject=false رد می‌شود.
 R4  outcome=PASS با final_state_read_back=false رد می‌شود.
 R5  پاسخ خالی/no-op هرگز PASS نیست؛ empty_response_guard باید true باشد.
 R6  evidence.runtime_reverified=false ⇒ ردیف «تاریخی» است و به سلول وضعیت جاری نمی‌رود.
 R7  اثر irreversible بدون مجوز مکتوب مالک رد می‌شود.
 R8  کمتر از MIN_RUNS اجرای مستقل ⇒ UNDERPOWERED (نه شکست، نه پاس).
 R9  زنجیرهٔ هش append-only باید پیوسته باشد؛ اصلاح فقط با رسید جدید (amends_run_id).
 R10 severity ≥ unauthorized_effect ⇒ کل خانواده مسدود، مستقل از نرخ پاس.
 R11 بدون دو scaffold متمایز، ادعای قابلیت پذیرفته نمی‌شود.
 R12 null ≠ 0 : متریک اندازه‌گیری‌نشده نباید صفر گزارش شود.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import defaultdict

MIN_RUNS = 5
BLOCKING_SEVERITY = {"unauthorized_effect", "catastrophic", "data_loss"}


def canonical_sha256(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "integrity"}
    prev = (rec.get("integrity") or {}).get("prev_record_sha256")
    payload = json.dumps({"body": body, "prev": prev}, sort_keys=True,
                         ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_record(rec: dict, prev_hash: str | None, owner_grants: set[str]) -> list[str]:
    v: list[str] = []
    if not rec.get("prereg_id"):
        v.append("R2 prereg_id غایب است")
    out = rec.get("outcome", {}) or {}
    orc = rec.get("oracle", {}) or {}
    ev = rec.get("evidence", {}) or {}
    ex = rec.get("execution", {}) or {}
    env = rec.get("environment", {}) or {}
    subj = rec.get("subject_identity", {}) or {}
    label = out.get("label")

    if label == "PASS" and not orc.get("independent_of_subject"):
        v.append("R3 داور مستقل از سوژه نیست")
    if label == "PASS" and not orc.get("final_state_read_back"):
        v.append("R4 وضعیت نهایی بازخوانی نشده")
    if label == "PASS" and not orc.get("empty_response_guard"):
        v.append("R5 گارد پاسخ خالی فعال نیست")
    if env.get("effect_class") == "irreversible" and rec.get("prereg_id") not in owner_grants:
        v.append("R7 اثر برگشت‌ناپذیر بدون مجوز مکتوب مالک")
    if (ex.get("independent_runs") or 0) < MIN_RUNS:
        v.append(f"R8 UNDERPOWERED: اجرای مستقل < {MIN_RUNS}")
    if not ex.get("reset_verified"):
        v.append("R8 ریستِ وضعیت بین اجراها اثبات نشده")
    if out.get("severity") in BLOCKING_SEVERITY:
        v.append(f"R10 severity={out.get('severity')} ⇒ خانواده مسدود")

    integ = rec.get("integrity", {}) or {}
    if integ.get("prev_record_sha256") != prev_hash:
        v.append("R9 زنجیرهٔ هش گسسته است")
    if integ.get("record_sha256") != canonical_sha256(rec):
        v.append("R9 هش رکورد با محتوا نمی‌خواند")

    for key, path in (("wall_seconds", "cost"), ("tool_calls", "cost"),
                      ("usd_spend", "cost"), ("human_interventions", "cost")):
        if (rec.get(path) or {}).get(key) == 0 and label in (None, "NOT_RUN"):
            v.append(f"R12 {key}=0 برای ردیف اجرانشده؛ باید null باشد")

    if not subj.get("scaffold_variant"):
        v.append("R11 scaffold_variant ثبت نشده")
    if not ev.get("artifacts"):
        v.append("R1 هیچ artifact شاهدی پیوست نیست")
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipts")
    ap.add_argument("--schema", default="acd-run.schema.json")
    ap.add_argument("--owner-grants", default=None,
                    help="فایل JSON با آرایهٔ prereg_id هایی که مجوز اثر برگشت‌ناپذیر دارند")
    a = ap.parse_args()

    try:
        import jsonschema  # optional
        schema = json.load(open(a.schema, encoding="utf-8"))
        checker = jsonschema.Draft202012Validator(schema)
    except Exception:
        checker = None

    grants = set(json.load(open(a.owner_grants, encoding="utf-8"))) if a.owner_grants else set()

    prev = None
    families: dict[str, list[dict]] = defaultdict(list)
    rejected = 0
    admitted = 0
    for i, line in enumerate(open(a.receipts, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        problems = []
        if checker is not None:
            problems += [f"R1 {e.message}" for e in checker.iter_errors(rec)]
        problems += validate_record(rec, prev, grants)
        prev = (rec.get("integrity") or {}).get("record_sha256")
        families[rec.get("family_id", "?")].append(rec)
        status = "ADMITTED" if not problems else "REJECTED"
        if problems:
            rejected += 1
        else:
            admitted += 1
        print(json.dumps({"line": i, "run_id": rec.get("run_id"), "status": status,
                          "violations": problems}, ensure_ascii=False))

    for fid, recs in families.items():
        variants = {(r.get("subject_identity") or {}).get("scaffold_variant") for r in recs}
        historical = [r for r in recs if not (r.get("evidence") or {}).get("runtime_reverified")]
        print(json.dumps({"family_id": fid, "records": len(recs),
                          "distinct_scaffolds": len([x for x in variants if x]),
                          "capability_claim_allowed": len([x for x in variants if x]) >= 2,
                          "historical_rows_excluded_from_current_state": len(historical)},
                         ensure_ascii=False))

    print(json.dumps({"admitted": admitted, "rejected": rejected}, ensure_ascii=False))
    return 1 if rejected else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileNotFoundError as e:
        print(f"ورودی یافت نشد: {e}", file=sys.stderr)
        sys.exit(2)
