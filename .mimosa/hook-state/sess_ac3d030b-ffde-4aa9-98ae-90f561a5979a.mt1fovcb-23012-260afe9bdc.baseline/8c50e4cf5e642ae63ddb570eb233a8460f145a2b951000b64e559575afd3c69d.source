#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pii_guard_covers_every_read_tool.py — درِ پشتیِ خروجِ داده بسته بماند.

یافتهٔ ممیزیِ ۲۰۲۶-۰۸-۰۳: `.claude/hooks/pii_read_guard.py` تنها اجرایِ
ماشینیِ لایهٔ secret/PII ِ `.agentignore` بود، و روی `tool_name != "Read"`
بی‌قیدوشرط `return` می‌کرد. یعنی هر سه مسیرِ زیر همان محتوا را می‌آوردند و
گارد اصلاً صدا زده نمی‌شد:

    Bash("cat <فایل>")   ·   Grep(output_mode="content")   ·   Glob

شعاعِ انفجارِ Bash از خودِ Read بیشتر بود، چون هر مسیری را می‌پذیرد.

⚠️ چرا موردهای **منفی** این‌جا مهم‌تر از مثبت‌ها هستند: این هوک روی **هر**
فراخوانیِ Bash می‌دود. گاردی که کارِ روزمره را بلاک کند، اولین کاری که با آن
می‌کنند خاموش‌کردنش است. پس نیمی از این فایل اثبات می‌کند که فرمان‌های واقعیِ
همین جلسه هنوز رد می‌شوند — از جمله فرمان‌هایی که کلمهٔ «secret» یا «key» در
متنشان هست ولی به هیچ فایلِ حساسی دست نمی‌زنند.

⚠️ `.claude/` در gitignore است، پس خودِ هوک تاریخچهٔ گیت ندارد. این فایلِ
tracked نگهبانش است: اگر هوک بازتولید شود و دوباره فقط `Read` را ببیند،
این تست قرمز می‌شود.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("pii-guard-tools")

HOOK = harness.REAL_VAULT / ".claude" / "hooks" / "pii_read_guard.py"
SETTINGS = harness.REAL_VAULT / ".claude" / "settings.json"


def _load():
    spec = importlib.util.spec_from_file_location("pii_read_guard", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ask(tool, **ti):
    """هوک را همان‌طور که harness صدایش می‌زند اجرا کن: JSON روی stdin.
    خروجیِ خالی = «نظری ندارم» = مجاز. خروجیِ deny = بلاک."""
    payload = json.dumps({"tool_name": tool, "tool_input": ti})
    r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "").strip()
    if not out:
        return False
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


# ── مثبت: این‌ها باید بلاک شوند ───────────────────────────────────────────────
BLOCK_BASH = [
    'cat "F:/backup/03 - Projects/Accounting/data/ledger.xlsx"',
    "cat _ops/state/owner-profile.json",
    "type .env",
    'rg -A5 "balance" "03 - Projects/Crypto - etoro/data/"',
    'head -50 "F:/backup/08 - Partner (PII)/notes.md"',
    "python -c \"print(open('secrets.env').read())\"",
    'cat "data/حساب کتاب/1404.md"',
]

# ── منفی: این‌ها باید رد شوند (فرمان‌های واقعیِ همین جلسه) ─────────────────────
ALLOW_BASH = [
    "git add _ops/tests/test_phantom_guards.py",
    "git log --oneline -5",
    'grep -rn "secret" _ops/ --include=*.py',
    'rg "OCTOPUS_AGENT_OWNER_SECRET" _ops/budget/opslib.py',
    'grep -c "api_key" _ops/cortex/model_router.py',
    "python _ops/tests/run_all.py",
    "cp _ops/OCTOPUS-flags.cmd /tmp/flags.bak",
    "cat .claude/settings.json",
    "ls -la _ops/state/",
    "git diff --stat HEAD~1",
    # این سه واقعاً مثبتِ کاذب **بودند** و حین ساخت رفع شدند. این‌جا قفل
    # می‌شوند تا هر شل‌کردنِ بعدیِ `_looks_like_path` دوباره برشان نگرداند:
    'grep -rn "flag_drift.is_secret_name" _ops/',   # ارجاعِ نقطه‌دارِ پایتون
    'echo "---.env check (presence only)---"',      # متنِ echo، نه مسیر
    'python -c "print(m.SECRET_GLOBS + m.PII_GLOBS)"',
]

#: نامِ برهنه‌ای که روی دیسک نیست ولی هدفِ واقعی است — باریک‌کردنِ اولِ من این
#: را هم کشته بود و تست گرفتش. مرزِ بینِ این و «---.env» تمامِ ظرافتِ کار است.
BLOCK_BARE_NAME = "python -c \"print(open('secrets.env').read())\""


def t_a_the_hook_and_its_matcher_both_exist():
    assert HOOK.exists(), HOOK
    d = json.loads(SETTINGS.read_text("utf-8", errors="replace"))
    entries = (d.get("hooks") or {}).get("PreToolUse") or []
    matchers = [e.get("matcher", "") for e in entries
                if any("pii_read_guard" in h.get("command", "")
                       for h in (e.get("hooks") or []))]
    assert matchers, "هوکِ PII در settings.json سیم‌کشی نشده"
    joined = "|".join(matchers)
    for tool in ("Read", "Bash", "Grep", "Glob"):
        assert tool in joined, (
            f"«{tool}» در matcher نیست — هوک برای آن ابزار اصلاً صدا زده "
            f"نمی‌شود، پس منطقِ داخلش بی‌ربط است. matcher فعلی: {joined}")


def t_b_read_is_still_blocked_as_before():
    """رگرسیونِ رفتارِ قدیمی — گسترش نباید چیزی را باز کرده باشد."""
    m = _load()
    for fp in ("_ops/state/owner-profile.json",
               "F:/backup/03 - Projects/Accounting/data/x.xlsx",
               "wallet-seed.txt", "id_rsa.pem"):
        assert m._decide(fp), fp


def t_c_bash_cat_no_longer_walks_around_the_guard():
    """قلبِ رفع. تا ۰۸-۰۴ هر کدام از این‌ها بی‌صدا محتوا را می‌آورد."""
    m = _load()
    for cmd in BLOCK_BASH:
        assert m._decide_command(cmd), f"هنوز رد می‌شود: {cmd}"
    assert m._decide_command(BLOCK_BARE_NAME), (
        "نامِ برهنه‌ای که روی دیسک نیست هم باید گرفته شود — وگرنه هر مسیرِ "
        f"نسبی به cwd ِ دیگر از گارد رد می‌شود: {BLOCK_BARE_NAME}")


def t_d_everyday_commands_are_not_blocked():
    """گاردِ ضدِ گرگ‌گرگ. اگر این قرمز شود، هوک باید **باریک‌تر** شود، نه
    اینکه این تست شل شود — گاردی که کارِ روزمره را می‌بندد خاموش می‌شود."""
    m = _load()
    noisy = [c for c in ALLOW_BASH if m._decide_command(c)]
    assert not noisy, ("مثبتِ کاذب — این فرمان‌ها به هیچ فایلِ حساسی دست "
                       "نمی‌زنند ولی بلاک شدند", noisy)


def t_e_grep_and_glob_scopes_are_checked():
    m = _load()
    assert m._target({"tool_name": "Grep",
                      "tool_input": {"path": "03 - Projects/Accounting/data"}})[1]
    assert m._decide("03 - Projects/Accounting/data/")
    assert m._target({"tool_name": "Glob", "tool_input": {"path": "x"}})[0] == "path"
    # ابزارِ ناشناخته هرگز بلاک نمی‌شود (FAIL-OPEN دست‌نخورده)
    assert m._target({"tool_name": "WebFetch", "tool_input": {"url": "x"}}) == (None, None)


def t_f_end_to_end_through_the_real_process():
    """نه فقط تابع — خودِ فایل، با همان قراردادِ stdin/stdout ِ harness.
    یک تابعِ درست با یک `main()` ِ خراب همچنان یک گاردِ مرده است."""
    assert _ask("Bash", command="cat _ops/state/owner-profile.json") is True
    assert _ask("Bash", command="git status") is False
    assert _ask("Read", file_path="id_rsa.pem") is True
    assert _ask("Grep", path="03 - Projects/Accounting/data") is True
    assert _ask("Grep", path="_ops/tests") is False


def t_g_the_guard_still_fails_open_on_garbage():
    """FAIL-OPEN مقدس است: باگِ این فایل نباید کلِ vault را قفل کند."""
    r = subprocess.run([sys.executable, str(HOOK)], input="{not json",
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and not (r.stdout or "").strip(), (r.returncode, r.stdout)
    assert _ask("Bash", command="") is False
    assert _ask("Bash") is False


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_pii_guard_covers_every_read_tool: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
