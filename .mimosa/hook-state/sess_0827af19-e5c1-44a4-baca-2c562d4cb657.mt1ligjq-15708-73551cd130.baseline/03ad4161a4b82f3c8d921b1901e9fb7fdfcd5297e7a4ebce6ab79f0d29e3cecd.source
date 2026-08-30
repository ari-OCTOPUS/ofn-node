#!/usr/bin/env python3
"""test_agentignore_settings_parity.py — دو فهرستِ ممنوعه نباید واگرا شوند.

یافتهٔ ممیزیِ ۲۰۲۶-۰۸-۰۳: این ریپو **دو** فهرستِ مسیرِ ممنوع دارد که دستی
هم‌گام نگه داشته می‌شوند و هیچ‌چیز هم‌گامی‌شان را نمی‌سنجد:

  · `.agentignore`        — سرورِ MCP مستقیم پارسش می‌کند (`server.py::_denied`)
  · `.claude/settings.json` `permissions.deny` — هارنس اجرایش می‌کند

نتیجهٔ واگرایی (اندازه‌گیری‌شده): سه مسیر — `secrets-export/`، `*-tokens.md`،
`TELEGRAM-SYSTEM-MAP/E-state-config-tokens.md` — در `.agentignore` بودند و در
`settings.json` **نبودند**. یعنی سطحِ MCP می‌بستشان و ابزارهای بومیِ Claude Code
نه. و کامنتِ خودِ `.agentignore` می‌گوید آن سخت‌سازی **چون یک ایجنت یکی‌شان را
خواند** اضافه شده — پس رفع اعمال شد و نیمه‌کاره ماند.

چرا تست و نه یادآوری: «دو فایل را هم‌گام نگه دار» یک قاعدهٔ نثری است، و قاعدهٔ
نثری در این ریپو می‌پوسد. تنها چیزی که واگرایی را می‌گیرد چیزی است که قرمز شود.

⚠️ این تست **فقط جهتِ ایمن** را اجبار می‌کند: هر چیزی که `.agentignore` ممنوع
کرده باید در `settings.json` هم پوشش داشته باشد. عکسش آزاد است — `settings.json`
عمداً چیزهای بیشتری می‌بندد (`rm`، `.git/`، مسیرهای مالی) که ربطی به
`.agentignore` ندارند.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("agentignore-parity")

#: ریشهٔ **واقعیِ** vault — این دو فایل حاکمیتی‌اند و نسخهٔ زندهٔ آن‌ها موضوعِ
#: تست است، نه یک کپیِ فیکسچری. (خواندن است، نه نوشتن؛ گاردِ state دست‌نخورده.)
ROOT = harness.REAL_VAULT
AGENTIGNORE = ROOT / ".agentignore"
SETTINGS = ROOT / ".claude" / "settings.json"


def _entries():
    out = []
    for ln in AGENTIGNORE.read_text("utf-8", errors="replace").splitlines():
        e = ln.strip()
        if e and not e.startswith("#"):
            out.append(e)
    return out


def _deny():
    d = json.loads(SETTINGS.read_text("utf-8", errors="replace"))
    return (d.get("permissions") or {}).get("deny") or []


def t_a_both_files_exist_and_parse():
    assert AGENTIGNORE.exists(), AGENTIGNORE
    assert SETTINGS.exists(), SETTINGS
    assert _entries(), ".agentignore خالی است"
    assert _deny(), "settings.json هیچ deny ای ندارد"


def t_b_every_agentignore_path_has_a_settings_counterpart():
    """قلبِ رگرسیون. اگر مسیری فقط در یکی باشد، یک سطح می‌بندد و دیگری نه."""
    blob = "\n".join(_deny())
    missing = []
    for e in _entries():
        core = e.rstrip("/").lstrip("*")
        if core and core not in blob:
            missing.append(e)
    assert not missing, (
        "این مسیرها در .agentignore ممنوع‌اند ولی settings.json پوششی ندارد — "
        "سطحِ MCP می‌بندد، ابزارهای بومی نه", missing)


def t_c_the_three_measured_gaps_stay_closed():
    """گاردِ نقطه‌ای برای همان سه موردی که ۰۸-۰۳ واقعاً باز بودند."""
    blob = "\n".join(_deny())
    for needle in ("secrets-export", "-tokens.md", "E-state-config-tokens.md"):
        assert needle in blob, (needle, "دوباره از settings.json افتاد")


def t_d_the_constitution_is_write_protected():
    """منشور §۰ می‌گوید «این فایل برای ایجنت‌ها فقط‌خواندنی است» — تا ۰۸-۰۴ آن
    جمله صفر اجرا داشت. یک ایجنت که قواعد را ویرایش کند، هر ایجنتِ بعدی را از
    یک متنِ دستکاری‌شده تغذیه می‌کند (ConstraintRot با لایهٔ ماندگاری)."""
    blob = "\n".join(_deny())
    for needle in ("agent-prompts", "CLAUDE.md"):
        assert needle in blob, (needle, "منشور در برابرِ نوشتن محافظت‌نشده است")


def t_e_delete_verbs_stay_denied_on_both_shells():
    """§۰.۱ «هرگز حذف نکن» — هر دو پوستهٔ این ماشین."""
    blob = "\n".join(_deny())
    for needle in ("Bash(rm ", "Remove-Item"):
        assert needle in blob, needle


def t_f_the_files_are_read_not_written_by_this_test():
    """این تست حاکمیت را می‌سنجد؛ خودش هرگز عوضش نمی‌کند.

    با AST نه زیررشته: نسخهٔ اول `"write_text" not in src` بود و **خودش را
    گرفت**، چون همان نام داخلِ فهرستِ ممنوعه‌اش بود. زیررشته فرقِ «کدی که
    می‌نویسد» و «متنی که دربارهٔ نوشتن حرف می‌زند» را نمی‌فهمد — و این دقیقاً
    همان کلاسِ مثبتِ کاذبی است که یک گارد را بی‌اعتبار می‌کند."""
    import ast
    banned = {"write_text", "write_bytes", "mkdir", "unlink", "replace"}
    tree = ast.parse(Path(__file__).read_text("utf-8"))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr in banned:
                hits.append(fn.attr)
            if isinstance(fn, ast.Name) and fn.id == "open":
                for kw in node.keywords:
                    if kw.arg == "mode":
                        hits.append("open(mode=)")
            if len(node.args) > 1 and isinstance(fn, ast.Name) and fn.id == "open":
                hits.append("open(positional-mode)")
    assert not hits, ("این تست نباید بنویسد", hits)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e!r}")
    print(f"\ntest_agentignore_settings_parity: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
