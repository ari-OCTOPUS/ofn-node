#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutate_obsidian_budget_guard.py — دندانِ گاردِ ایندکس را روی کپی می‌سنجد.

هم‌الگوی `mutate_live_state_guard.py`. تفاوتِ باربر با نسخهٔ اولِ این
جهش‌آزمایی: **هیچ‌وقت `.obsidian/app.json` ِ زنده نوشته نمی‌شود.**

۲۰۲۶-۰۸-۰۴ — بارِ اول برای اثباتِ همین پنج جهش، شش نوبت روی فایلِ زندهٔ
پیکربندیِ ابسیدین نوشتم و هر بار برگرداندم. بایت‌به‌بایت هم برگشت (`diff -q`
سبز) ولی الگو همانی است که حافظهٔ خودِ این ریپو منع می‌کند: اگر وسطِ آن شش
نوبت ابسیدین باز می‌بود، یا جلسهٔ موازیِ دیگری همان فایل را می‌خواند — و در
همین ساعت‌ها واقعاً یک ممیزیِ موازی داشت همان فایل را می‌خواند — پیکربندیِ
مالک قربانیِ اثباتِ من می‌شد.

اجرا:  python mutate_obsidian_budget_guard.py
خروجی: ۰ اگر هر جهش تستِ **هدفِ خودش** را قرمز کند، وگرنه ۱.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

harness.setup("mutate-obsidian-budget")

LIVE = harness.REAL_VAULT / ".obsidian" / "app.json"
GUARD = _HERE / "test_obsidian_index_budget.py"


def _mutations(cfg):
    """هر جهش: (نام، تابعِ تغییردهنده، نامِ تستی که **باید** قرمز شود)."""
    def revert_ext(d):
        d["userIgnoreFilters"] = [
            "/\\.(pyc|pyo|log|db|zip)$/" if x.startswith("/\\.(") else x
            for x in d["userIgnoreFilters"]]

    def filter_md(d):
        d["userIgnoreFilters"].append("/\\.(md)$/")

    def drop_duplicates(d):
        d["userIgnoreFilters"] = [x for x in d["userIgnoreFilters"]
                                  if "_Duplicates" not in x]

    def broken_regex(d):
        d["userIgnoreFilters"].append("/\\.(unclosed$/")

    def empty(d):
        d["userIgnoreFilters"] = []

    return [
        ("ext-filter reverted to the pre-08-04 five", revert_ext,
         "t_b_every_unrenderable_extension_stays_filtered"),
        ("someone filters .md too (over-filtering)", filter_md,
         "t_c_content_extensions_are_never_filtered"),
        ("_Duplicates falls out of the exclusions", drop_duplicates,
         "t_d_the_two_move_targets_stay_excluded"),
        ("a malformed regex is added", broken_regex,
         "t_e_every_regex_filter_actually_compiles"),
        ("the whole filter list is emptied", empty,
         "t_a_the_config_is_readable_and_not_empty"),
    ]


def main():
    base = json.loads(LIVE.read_text("utf-8", errors="replace"))
    before = LIVE.read_bytes()

    # سلامتِ پایه: گارد باید روی نسخهٔ دست‌نخورده **سبز** باشد. بدونِ این،
    # یک «قرمز» می‌تواند صرفاً یعنی گارد از اول خراب بوده.
    with tempfile.TemporaryDirectory() as td:
        clean = Path(td) / "app.json"
        clean.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, str(GUARD), str(clean)],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print("BASELINE IS ALREADY RED — جهش بی‌معنی است:")
            print(r.stdout)
            return 1
    print("baseline: guard green on the unmutated copy\n")

    failures = []
    for name, apply_mut, target in _mutations(base):
        d = json.loads(json.dumps(base))     # deep copy
        apply_mut(d)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "app.json"
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
            r = subprocess.run([sys.executable, str(GUARD), str(p)],
                               capture_output=True, text=True, encoding="utf-8")
        out = r.stdout or ""
        killed_by_target = f"FAIL {target}" in out
        if killed_by_target:
            print(f"  KILLED   {name}\n           -> {target}")
        else:
            reds = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL")]
            print(f"  SURVIVED {name}\n           expected red: {target}\n"
                  f"           actually red: {reds or 'nothing'}")
            failures.append(name)

    # ⚠️ ناوردیِ اصلیِ این اسکریپت: فایلِ زنده حتی یک بایت هم عوض نشده باشد.
    after = LIVE.read_bytes()
    if after != before:
        print("\n❌ فایلِ زندهٔ app.json تغییر کرد — این اسکریپت هرگز نباید بنویسد")
        return 1
    print(f"\nlive .obsidian/app.json untouched: {len(before)} bytes, byte-identical")
    print(f"\n{'✅' if not failures else '❌'} mutations: "
          f"{len(_mutations(base)) - len(failures)}/{len(_mutations(base))} killed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
