#!/usr/bin/env python3
"""GAP-LEDGER generator — ops/gap_sources.yaml -> ops/GAP-LEDGER.jsonl

قانون طلایی NOW.md: خروجی ماشین‌تولید است و هرگز دستی ویرایش نمی‌شود.
تنها فایل دست‌نویس مجاز، ops/gap_sources.yaml است.

stdlib + pyyaml فقط. هیچ کلاینت LLM (رفلکس بی-LLM روی ۱۳۸).

usage:
    python tools/gap_ledger.py --emit          # تولید JSONL + رندر md
    python tools/gap_ledger.py --check         # فقط اعتبارسنجی، exit 1 اگر نامعتبر
    python tools/gap_ledger.py --verify-chain  # تأیید زنجیرهٔ هش از نقطهٔ صفر
    python tools/gap_ledger.py --summary       # شمارش‌ها
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "ops" / "gap_sources.yaml"
LEDGER = ROOT / "ops" / "GAP-LEDGER.jsonl"
RENDER = ROOT / "ops" / "GAP-LEDGER.md"

ZERO = "0" * 64

# کلاس‌های مجاز برای خودکدنویسی (CODE_CLASS_A)
SELF_CODING_CLASSES = {"A1", "A2", "A3", "A4", "A5"}
# کلاس‌هایی که هرگز خودنوشت نمی‌شوند
BLOCKED_CLASSES = {"D", "Z"}
ALL_CLASSES = SELF_CODING_CLASSES | BLOCKED_CLASSES

F1_STATUS = {"LIVE", "PRESENT_UNWIRED", "STALE", "NOT_FOUND", "UNKNOWN", "BROKEN", "BLOCKED"}
GOV_STATUS = {"OPEN", "BLOCKED", "PARKED", "OWNER_DECISION", "BROKEN"}
GAP_STATE = {"OPEN", "PROPOSED", "CLOSED", "REVERTED"}

REQUIRED = [
    "id", "title", "category", "node", "f1_status", "gov_status",
    "class", "verify", "expect", "baseline_action", "rollback", "source",
]

# مسیرهایی که هرگز نباید توسط patch خودنوشت لمس شوند (CODE_CLASS_Z)
FORBIDDEN_PATHS = [
    "money_gate", "allowlist", "data/gates.json", "secrets", "keys",
    "policy", "GOV-V6", "executor", "MAY_AUTHORIZE",
]


def load() -> dict:
    with SOURCE.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate(doc: dict) -> list[str]:
    """هر شکاف باید verify و expect اجراپذیر داشته باشد. نقض = halt نه retry."""
    errors: list[str] = []
    gaps = doc.get("gaps") or []
    seen: set[str] = set()

    if not gaps:
        errors.append("no gaps found in source")

    for i, g in enumerate(gaps):
        tag = g.get("id", f"<index {i}>")

        for field in REQUIRED:
            val = g.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"{tag}: missing required field '{field}'")

        gid = g.get("id")
        if gid in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(gid)

        cls = g.get("class")
        if cls not in ALL_CLASSES:
            errors.append(f"{tag}: class '{cls}' not in {sorted(ALL_CLASSES)}")

        if g.get("f1_status") not in F1_STATUS:
            errors.append(f"{tag}: f1_status '{g.get('f1_status')}' invalid")

        if g.get("gov_status") not in GOV_STATUS:
            errors.append(f"{tag}: gov_status '{g.get('gov_status')}' invalid")

        state = g.get("state", "OPEN")
        if state not in GAP_STATE:
            errors.append(f"{tag}: state '{state}' not in {sorted(GAP_STATE)}")
        # شکافِ PROPOSED باید PR خود را نام ببرد — وگرنه ردیابی نمی‌شود
        if state == "PROPOSED" and not g.get("pr"):
            errors.append(f"{tag}: state=PROPOSED requires a 'pr' reference")
        # محدودیتِ دو تلاش، بعد OWNER_DECISION
        if int(g.get("attempts", 0)) > 2:
            errors.append(f"{tag}: attempts>2 must escalate to OWNER_DECISION")

        # قانون کلیدی: معیار بسته‌شدن باید اجراپذیر باشد، نه توصیفی
        verify = str(g.get("verify") or "")
        if verify and not any(
            tok in verify
            for tok in ("python", "pytest", "rg ", "git ", "ssh ", "curl", "stat ", "jq", "test ", "nats", "huggingface")
        ):
            errors.append(f"{tag}: verify does not look like an executable command")

        # شکاف خودکدنویسی‌پذیر باید rollback تک-commit داشته باشد
        if cls in SELF_CODING_CLASSES:
            rb = str(g.get("rollback") or "")
            if "revert" not in rb and "بدون تغییر" not in rb:
                errors.append(f"{tag}: class {cls} needs a single-commit revert rollback")

    return errors


def chain(doc: dict) -> list[dict]:
    """زنجیرهٔ هش SHA-256 فقط-افزودنی، یک سریالایزر واحد، تأیید از نقطهٔ صفر."""
    rows: list[dict] = []
    prev = ZERO
    for seq, g in enumerate(doc["gaps"]):
        rec = {
            "seq": seq,
            "prev_hash": prev,
            "id": g["id"],
            "title": g["title"],
            "category": g["category"],
            "node": str(g["node"]),
            "f1_status": g["f1_status"],
            "gov_status": g["gov_status"],
            "class": g["class"],
            "self_codable": g["class"] in SELF_CODING_CLASSES,
            "verify": g["verify"],
            "expect": str(g["expect"]),
            "verify_status": "UNVALIDATED",   # بدون رسید = UNKNOWN
            "baseline_action": g["baseline_action"],
            "measured_delta": None,           # پر می‌شود پس از اجرای واقعی
            "rollback": g["rollback"],
            "source": g["source"],
            "blocked_by": g.get("blocked_by"),
            "risk": g.get("risk"),
            "attempts": int(g.get("attempts", 0)),
            # OPEN → PROPOSED (PR باز) → CLOSED (verify روی برد سبز) | REVERTED
            "state": g.get("state", "OPEN"),
            "pr": g.get("pr"),
            "canary": bool(g.get("canary", False)),
        }
        payload = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        rec["hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        prev = rec["hash"]
        rows.append(rec)
    return rows


def verify_chain() -> int:
    if not LEDGER.exists():
        print("FAIL: ledger missing", file=sys.stderr)
        return 1
    prev = ZERO
    n = 0
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["prev_hash"] != prev:
            print(f"FAIL: chain break at seq {rec['seq']}", file=sys.stderr)
            return 1
        got = rec.pop("hash")
        payload = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if hashlib.sha256(payload.encode("utf-8")).hexdigest() != got:
            print(f"FAIL: hash mismatch at seq {rec['seq']}", file=sys.stderr)
            return 1
        prev = got
        n += 1
    print(json.dumps({"status": "OK", "records": n, "head": prev}, ensure_ascii=False))
    return 0


def summarise(rows: list[dict]) -> dict:
    def count(key: str) -> dict:
        out: dict[str, int] = {}
        for r in rows:
            out[r[key]] = out.get(r[key], 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    codable = [r for r in rows if r["self_codable"]]
    ready = [r for r in codable if not r["blocked_by"]]
    canaries = [r["id"] for r in ready if r["canary"]]
    return {
        "total": len(rows),
        "self_codable": len(codable),
        "self_codable_unblocked": len(ready),
        "owner_or_design_only": len(rows) - len(codable),
        "by_class": count("class"),
        "by_f1_status": count("f1_status"),
        "by_gov_status": count("gov_status"),
        "by_category": count("category"),
        "canary_targets": canaries,
    }


def _dist(d: dict) -> str:
    """توزیع را خوانا رندر کن، نه repr پایتون."""
    return " · ".join(f"{k} {v}" for k, v in d.items())


def render(rows: list[dict], summary: dict) -> str:
    lines = [
        "# GAP-LEDGER — ماشین‌تولید، دستی ویرایش نکن",
        "",
        f"generated from `ops/gap_sources.yaml` by `tools/gap_ledger.py` · records: {summary['total']}",
        "",
        "> هر `verify` هنوز `UNVALIDATED` است — هیچ‌کدام روی نود واقعی اجرا نشده.",
        "> طبق قانون آهنین: بدون رسید = UNKNOWN، هرگز LIVE.",
        "",
        "## خلاصه",
        "",
        f"- کل شکاف‌ها: **{summary['total']}**",
        f"- خودکدنویسی‌پذیر (CLASS_A): **{summary['self_codable']}** — از این تعداد **{summary['self_codable_unblocked']}** بدون blocker",
        f"- فقط مالک یا طراحی (CLASS_Z/D): **{summary['owner_or_design_only']}**",
        "",
        "| محور | توزیع |",
        "|------|-------|",
        f"| class | {_dist(summary['by_class'])} |",
        f"| f1_status | {_dist(summary['by_f1_status'])} |",
        f"| gov_status | {_dist(summary['by_gov_status'])} |",
        f"| category | {_dist(summary['by_category'])} |",
        "",
        f"**اهداف canary (سه هدف اول حلقه):** {', '.join(summary['canary_targets']) or '—'}",
        "",
        "## شکاف‌های خودکدنویسی‌پذیر و بی‌blocker (صف حلقه)",
        "",
        "| id | عنوان | class | verify → expect |",
        "|----|-------|-------|-----------------|",
    ]
    for r in rows:
        if r["self_codable"] and not r["blocked_by"]:
            v = r["verify"].replace("|", "\\|")
            e = r["expect"].replace("|", "\\|")
            mark = " 🐙" if r["canary"] else ""
            lines.append(f"| {r['id']}{mark} | {r['title']} | {r['class']} | `{v}` → `{e}` |")

    lines += [
        "",
        "## شکاف‌های owner-only یا نیازمند طراحی",
        "",
        "| id | عنوان | class | blocked_by |",
        "|----|-------|-------|------------|",
    ]
    for r in rows:
        if not r["self_codable"]:
            lines.append(f"| {r['id']} | {r['title']} | {r['class']} | {r['blocked_by'] or '—'} |")

    lines += [
        "",
        "## شکاف‌های خودکدنویسی‌پذیر ولی مسدود",
        "",
        "| id | عنوان | class | blocked_by |",
        "|----|-------|-------|------------|",
    ]
    for r in rows:
        if r["self_codable"] and r["blocked_by"]:
            lines.append(f"| {r['id']} | {r['title']} | {r['class']} | {r['blocked_by']} |")

    lines += ["", "---", "", "بودجهٔ حلقه: حداکثر ۳ PR خودنوشت در ۲۴ ساعت · هر PR ≤۱۵۰ خط ·",
              "هیچ کلاس شکافی >۶۰٪ یک پنجره · هر شکاف حداکثر ۲ تلاش، بعد OWNER_DECISION.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--verify-chain", action="store_true")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()

    if args.verify_chain:
        return verify_chain()

    doc = load()
    errors = validate(doc)
    if errors:
        for e in errors:
            print(f"INVALID: {e}", file=sys.stderr)
        # نقض invariant = halt نه retry
        return 1

    rows = chain(doc)
    summary = summarise(rows)

    if args.check:
        print(json.dumps({"status": "VALID", "gaps": len(rows)}, ensure_ascii=False))
        return 0

    if args.summary:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if args.emit:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        RENDER.write_text(render(rows, summary), encoding="utf-8")
        print(json.dumps(
            {"emitted": str(LEDGER.name), "rendered": str(RENDER.name), **summary},
            ensure_ascii=False, indent=2))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
