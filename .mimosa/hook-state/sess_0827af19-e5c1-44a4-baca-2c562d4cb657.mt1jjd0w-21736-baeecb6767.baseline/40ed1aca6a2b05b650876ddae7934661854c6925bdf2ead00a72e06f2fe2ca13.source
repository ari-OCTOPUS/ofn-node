#!/usr/bin/env python3
"""گیتِ ماشین‌خوانِ تست — `test-report.json`.

مسئله‌ای که این ماژول حل می‌کند
────────────────────────────────
`run_all.py` وضعیت را به‌صورتِ **نثر** و یک لیستِ نامِ فایل گزارش می‌دهد
(`failed = [...]`, `sys.exit(1)`). برای انسان عالی است. برای یک ارگانیسمی که
قرار است کدِ خودش را merge کند فاجعه است: هیچ عددِ صحیحی وجود ندارد که بشود
گیت را رویش بست، و «هیچ خطایی ندیدم» به‌سادگی با «پاس شد» اشتباه می‌شود.
این دقیقاً قانونِ §۱۴ است: **نبودِ خطا برابرِ پاس نیست.**

طراحی — چرا `run_all.py` را دست نمی‌زنم
──────────────────────────────────────
یک نشستِ همزمان همین حالا `run_all.py` را ویرایش می‌کند (mtimeِ ۲۸ جولای ~۰۱:۲۳).
پس به‌جای ویرایش، فهرستِ تست‌ها را با **AST** از همان فایل می‌خوانم — بدونِ
import و بدونِ هیچ اثرِ جانبی. نتیجه: تنها یک منبعِ حقیقت برای «چه چیزی تست
می‌شود» باقی می‌ماند و این ماژول هرگز نمی‌تواند از آن رانش کند (§۴).

خروجی: `_ops/state/test-report.json`
    {"schema":"test-report.v1","ts":…,"passed":N,"failed":M,"errors":K,
     "skipped":S,"files_ok":…,"files_failed":[…],"unparsed":[…],
     "granularity":"test"|"mixed"|"file","duration_s":…,
     "expected_red":[…],"gate":"green"|"red"|"unknown"}

`gate` هرگز «green» نمی‌شود مگر همه‌چیز پارس شده باشد و شکستی جز
`expected_red` نمانده باشد. ابهام = `unknown` = قرمز برای هر مصرف‌کننده.

اجرا:
    python _ops/tests/gate_report.py --dry-run   # فقط بگو چه چیزی اجرا می‌شود
    python _ops/tests/gate_report.py             # اجرا + نوشتنِ JSON
    python _ops/tests/gate_report.py --only test_leg.py
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "test-report.v1"

# قرمزِ عمدی و مستند (VQ-GUARD-001). این فهرست **تنها** جایی است که یک شکست
# مجاز است، و هر عضوش باید یک شناسهٔ رأیِ باز داشته باشد.
EXPECTED_RED = {"test_paid_router_dark_config.py": "VQ-GUARD-001"}

_RE_PYTEST = re.compile(
    r"(?:(\d+)\s+failed)?[,\s]*(?:(\d+)\s+passed)?[,\s]*(?:(\d+)\s+skipped)?"
    r"[,\s]*(?:(\d+)\s+error(?:s)?)?", re.I)
_RE_UNITTEST_RAN = re.compile(r"^Ran\s+(\d+)\s+tests?", re.M)
_RE_UNITTEST_FAIL = re.compile(
    r"^FAILED\s*\((?:.*?failures=(\d+))?(?:.*?errors=(\d+))?(?:.*?skipped=(\d+))?",
    re.M)


def read_test_lists(run_all_path):
    """فهرستِ تست‌ها را با AST از run_all.py بیرون می‌کشد. بدونِ import.

    فقط لیترال‌ها خوانده می‌شوند؛ `EXTRA_TESTS` که با `Path(...)` ساخته شده
    عمداً نادیده گرفته می‌شود و در `skipped_dynamic` گزارش می‌گردد — چون
    ادعای «همه را اجرا کردم» بدونِ آن دروغ است.
    """
    src = Path(run_all_path).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    tests, pytest_tests, dynamic = [], set(), []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not isinstance(tgt, ast.Name):
                continue
            name = tgt.id
            if name not in ("TESTS", "PYTEST_TESTS", "EXTRA_TESTS"):
                continue
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                dynamic.append(name)
                continue
            if name == "TESTS":
                tests = [str(v) for v in value]
            elif name == "PYTEST_TESTS":
                pytest_tests = {str(v) for v in value}
            else:
                dynamic.append(name)
    return tests, pytest_tests, dynamic


def parse_counts(stdout: str, stderr: str, returncode: int) -> dict:
    """تبدیلِ خروجیِ یک فایلِ تست به عدد. تابعِ خالص — قلبِ قابلِ تستِ این ماژول.

    سه سطحِ دقت، و هر کدام صادقانه برچسب می‌خورد:
      · `test` — pytest یا unittest شمارش داد
      · `file` — هیچ عددی پیدا نشد، فقط exit code داریم
    """
    blob = f"{stdout or ''}\n{stderr or ''}"

    # ── pytest ──────────────────────────────────────────────────────────
    tail = [l for l in blob.splitlines() if re.search(r"\b(passed|failed|error)\b", l, re.I)]
    for line in reversed(tail):
        m = _RE_PYTEST.search(line)
        if not m or not any(m.groups()):
            continue
        failed, passed, skipped, errors = (int(g) if g else 0 for g in m.groups())
        if passed or failed or errors or skipped:
            return {"passed": passed, "failed": failed, "errors": errors,
                    "skipped": skipped, "granularity": "test", "source": "pytest"}

    # ── unittest ────────────────────────────────────────────────────────
    ran = _RE_UNITTEST_RAN.search(blob)
    if ran:
        total = int(ran.group(1))
        f = _RE_UNITTEST_FAIL.search(blob)
        failures = int(f.group(1) or 0) if f else 0
        errors = int(f.group(2) or 0) if f else 0
        skipped = int(f.group(3) or 0) if f else 0
        bad = failures + errors
        if not f and returncode != 0:
            # «Ran N» دیدیم ولی نه OK نه FAILED، و exit قرمز است → نمی‌دانیم.
            return {"passed": 0, "failed": 1, "errors": 0, "skipped": 0,
                    "granularity": "file", "source": "unittest-ambiguous"}
        return {"passed": max(0, total - bad - skipped), "failed": failures,
                "errors": errors, "skipped": skipped,
                "granularity": "test", "source": "unittest"}

    # ── هیچ عددی نبود ───────────────────────────────────────────────────
    ok = returncode == 0
    return {"passed": 1 if ok else 0, "failed": 0 if ok else 1,
            "errors": 0, "skipped": 0, "granularity": "file",
            "source": "exitcode"}


def run_one(path: Path, use_pytest: bool, timeout=300) -> dict:
    cmd = ([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(path)]
           if use_pytest else [sys.executable, "-X", "utf8", str(path)])
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(path.parent), timeout=timeout,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        counts = parse_counts(r.stdout, r.stderr, r.returncode)
        counts["returncode"] = r.returncode
    except subprocess.TimeoutExpired:
        counts = {"passed": 0, "failed": 1, "errors": 0, "skipped": 0,
                  "granularity": "file", "source": "timeout", "returncode": None}
    except Exception as exc:  # noqa: BLE001
        counts = {"passed": 0, "failed": 1, "errors": 0, "skipped": 0,
                  "granularity": "file", "source": f"launch-error:{type(exc).__name__}",
                  "returncode": None}
    counts["file"] = path.name
    counts["duration_s"] = round(time.time() - t0, 2)
    return counts


def build_report(results, dynamic_skipped, duration_s) -> dict:
    passed = sum(r["passed"] for r in results)
    failed = sum(r["failed"] for r in results)
    errors = sum(r["errors"] for r in results)
    skipped = sum(r["skipped"] for r in results)
    files_failed = [r["file"] for r in results
                    if r["failed"] or r["errors"] or (r.get("returncode") not in (0, None))]
    unexpected = [f for f in files_failed if f not in EXPECTED_RED]
    unparsed = [r["file"] for r in results if r["granularity"] == "file"]

    grans = {r["granularity"] for r in results}
    granularity = ("test" if grans == {"test"}
                   else "file" if grans == {"file"} else "mixed")

    if dynamic_skipped:
        gate = "unknown"           # فهرستی هست که نتوانستیم بخوانیم → ادعا نمی‌کنیم
    elif unexpected:
        gate = "red"
    elif granularity == "file":
        gate = "unknown"           # هیچ عددی نداریم → سبز اعلام نمی‌کنیم (§۱۴)
    else:
        gate = "green"

    return {
        "schema": SCHEMA,
        "ts": time.time(),
        "passed": passed, "failed": failed, "errors": errors, "skipped": skipped,
        "files_total": len(results),
        "files_failed": files_failed,
        "files_unexpected_red": unexpected,
        "expected_red": EXPECTED_RED,
        "unparsed": unparsed,
        "granularity": granularity,
        "dynamic_lists_skipped": dynamic_skipped,
        "duration_s": round(duration_s, 2),
        "gate": gate,
        "per_file": results,
    }


def render(rep: dict) -> str:
    icon = {"green": "✅", "red": "❌", "unknown": "🚩"}.get(rep["gate"], "🚩")
    lines = [
        f"{icon} گیت: {rep['gate']}  |  پاس {rep['passed']}  شکست {rep['failed']}  "
        f"خطا {rep['errors']}  رد‌شده {rep['skipped']}",
        f"   فایل‌ها: {rep['files_total']}  |  دقت: {rep['granularity']}  |  "
        f"{rep['duration_s']}s",
    ]
    if rep["files_unexpected_red"]:
        lines.append("   ❌ قرمزِ غیرمنتظره: " + ", ".join(rep["files_unexpected_red"]))
    if rep["unparsed"]:
        lines.append(f"   🚩 {len(rep['unparsed'])} فایل عددی نداد (فقط exit code) — "
                     "این‌ها نمی‌توانند گیت را سبز کنند.")
    if rep["dynamic_lists_skipped"]:
        lines.append("   🚩 فهرستِ پویا خوانده نشد: "
                     + ", ".join(rep["dynamic_lists_skipped"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    here = Path(__file__).resolve().parent
    run_all = here / "run_all.py"
    out = here.parent / "state" / "test-report.json"

    tests, pytest_tests, dynamic = read_test_lists(run_all)
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        if i + 1 < len(argv):
            only = argv[i + 1]
            tests = [t for t in tests if t == only]

    if "--dry-run" in argv:
        print(f"{len(tests)} فایل اجرا می‌شود ({len(pytest_tests)} تای‌شان با pytest)."
              + (f"\nفهرستِ پویای خوانده‌نشده: {dynamic}" if dynamic else ""))
        for t in tests[:10]:
            print(f"  · {t}{'  [pytest]' if t in pytest_tests else ''}")
        if len(tests) > 10:
            print(f"  … و {len(tests) - 10} تای دیگر")
        return 0

    t0 = time.time()
    results = []
    for t in tests:
        p = here / t
        if not p.exists():
            results.append({"file": t, "passed": 0, "failed": 1, "errors": 0,
                            "skipped": 0, "granularity": "file",
                            "source": "missing-file", "returncode": None,
                            "duration_s": 0.0})
            continue
        results.append(run_one(p, t in pytest_tests))
        print(f"  {results[-1]['file']}: {results[-1]['passed']}✓ "
              f"{results[-1]['failed']}✗ ({results[-1]['source']})")

    rep = build_report(results, dynamic, time.time() - t0)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + render(rep))
    print(f"→ {out}")
    return 0 if rep["gate"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
