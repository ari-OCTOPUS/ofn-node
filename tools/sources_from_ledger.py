#!/usr/bin/env python3
"""بازسازی بی‌اتلاف gap_sources.yaml از GAP-LEDGER.jsonl کانونی.

چرا این کار می‌کند:
    tools/gap_ledger.py :: chain() هر فیلدِ منبع را عیناً داخل رکورد کپی می‌کند
    (id, title, category, node, f1_status, gov_status, class, verify, expect,
     baseline_action, rollback, source, blocked_by, risk, attempts, state, pr, canary).
    فیلدهای مشتق‌شده فقط این‌ها هستند: seq, prev_hash, hash, self_codable,
    verify_status, measured_delta — که همه از منبع حذف می‌شوند.
    پس نگاشت jsonl → yaml برگشت‌پذیر و بی‌اتلاف است.

چرا GAP-LEDGER.md برگشت‌پذیر نیست:
    md فقط id, title, class, verify, expect, blocked_by را رندر می‌کند.
    هشت فیلد اجباری دیگر (category, node, f1_status, gov_status,
    baseline_action, rollback, source) در آن وجود ندارند — به همین دلیل
    هر بازسازی از md با --check کانونی INVALID می‌شود، و درست هم همین است.

usage:
    python sources_from_ledger.py ops/GAP-LEDGER.jsonl > ops/gap_sources.yaml
    python sources_from_ledger.py ops/GAP-LEDGER.jsonl --verify ops/gap_sources.yaml

بعد از تولید، چرخهٔ اثبات:
    python tools/gap_ledger.py --check          # باید VALID بدهد
    python tools/gap_ledger.py --emit           # jsonl + md را بازتولید کند
    python tools/gap_ledger.py --verify-chain   # زنجیره از نقطهٔ صفر
    diff <(git show HEAD:ops/GAP-LEDGER.jsonl) ops/GAP-LEDGER.jsonl   # باید خالی باشد
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# فیلدهایی که generator می‌سازد و هرگز در منبع نیستند
DERIVED = {
    "seq", "prev_hash", "hash", "self_codable",
    "verify_status", "measured_delta",
}

# ترتیب فیلدها در yaml — همان ترتیب REQUIRED ابزار کانونی، بعد اختیاری‌ها
FIELD_ORDER = [
    "id", "title", "category", "node", "f1_status", "gov_status",
    "class", "verify", "expect", "baseline_action", "rollback", "source",
    "blocked_by", "risk", "attempts", "state", "pr", "canary",
]

# اختیاری‌هایی که اگر مقدار پیش‌فرض دارند حذف می‌شوند تا yaml تمیز بماند
OPTIONAL_DEFAULTS = {"attempts": 0, "state": "OPEN", "pr": None, "canary": False}


def load_rows(path: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            sys.exit(f"FAIL: line {i + 1} is not valid JSON — {exc}")
    if not rows:
        sys.exit("FAIL: ledger has no records")
    return rows


def q(val) -> str:
    """نقل‌قول امن برای yaml — فارسی و فرمان‌های shell را سالم نگه می‌دارد."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    # فرمان‌های verify پر از | و ' و " هستند — تک‌نقل با escape دوگانه امن‌ترین است
    needs_quote = (
        s == ""
        or s[0] in "&*?|-<>=!%@`{}[]#,\"'"
        or ": " in s
        or s.strip() != s
        or s.lower() in {"null", "true", "false", "yes", "no", "on", "off", "~"}
        or "|" in s
        or "#" in s
    )
    if needs_quote:
        return "'" + s.replace("'", "''") + "'"
    return s


def to_yaml(rows: list[dict], meta: dict | None = None) -> str:
    out: list[str] = [
        "# gap_sources.yaml — منبع curated شکاف‌های اختاپوس",
        "# بازسازی‌شدهٔ بی‌اتلاف از GAP-LEDGER.jsonl کانونی توسط sources_from_ledger.py",
        "# این تنها فایل دست‌نویس مجاز است. GAP-LEDGER.jsonl از این تولید می‌شود.",
        "",
        "meta:",
    ]
    m = meta or {}
    out.append(f"  created: {q(m.get('created', '2026-09-03'))}")
    out.append(f"  round: {m.get('round', 19)}")
    out.append(
        "  source_of_truth: "
        + q(m.get("source_of_truth", "reconstructed losslessly from canonical GAP-LEDGER.jsonl"))
    )
    out.append("")
    out.append("gaps:")
    out.append("")

    for r in rows:
        first = True
        for key in FIELD_ORDER:
            if key not in r:
                continue
            val = r[key]
            if key in OPTIONAL_DEFAULTS and val == OPTIONAL_DEFAULTS[key]:
                continue
            prefix = "- " if first else "  "
            out.append(f"{prefix}{key}: {q(val)}")
            first = False
        # فیلدهای ناشناخته را دور نریز — صراحت بر تمیزی مقدم است
        for key in sorted(set(r) - set(FIELD_ORDER) - DERIVED):
            out.append(f"  {key}: {q(r[key])}")
        out.append("")
    return "\n".join(out)


def verify_roundtrip(rows: list[dict], yaml_path: Path) -> int:
    """اثبات بی‌اتلاف بودن: هر فیلد غیرمشتق منبع باید با لجر یکی باشد."""
    try:
        import yaml as pyyaml
    except ImportError:
        sys.exit("FAIL: pyyaml لازم است برای --verify")

    doc = pyyaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    gaps = doc.get("gaps") or []
    if len(gaps) != len(rows):
        print(f"FAIL: row count {len(gaps)} != ledger {len(rows)}", file=sys.stderr)
        return 1

    bad = 0
    for src, led in zip(gaps, rows):
        if src.get("id") != led.get("id"):
            print(f"FAIL: id order drift {src.get('id')} vs {led.get('id')}", file=sys.stderr)
            bad += 1
            continue
        for key, want in led.items():
            if key in DERIVED:
                continue
            got = src.get(key, OPTIONAL_DEFAULTS.get(key))
            if key == "expect":
                got, want = str(got), str(want)
            if key == "node":
                got, want = str(got), str(want)
            if got != want:
                print(f"FAIL: {led['id']}.{key}: yaml={got!r} ledger={want!r}", file=sys.stderr)
                bad += 1

    if bad:
        print(f"FAIL: {bad} field mismatches", file=sys.stderr)
        return 1
    print(json.dumps(
        {"status": "LOSSLESS", "rows": len(rows),
         "fields_checked": sorted(set(rows[0]) - DERIVED)},
        ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger", type=Path, help="مسیر GAP-LEDGER.jsonl کانونی")
    ap.add_argument("--verify", type=Path, metavar="YAML",
                    help="بررسی بی‌اتلاف بودن yaml موجود در برابر لجر")
    args = ap.parse_args()

    if not args.ledger.exists():
        sys.exit(f"FAIL: ledger not found: {args.ledger}")

    rows = load_rows(args.ledger)

    if args.verify:
        if not args.verify.exists():
            sys.exit(f"FAIL: yaml not found: {args.verify}")
        return verify_roundtrip(rows, args.verify)

    sys.stdout.write(to_yaml(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
