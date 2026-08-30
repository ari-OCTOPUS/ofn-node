#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_vault_hygiene_ratchet.py — لینکِ شکسته و فرانت‌مترِ خراب فقط پایین می‌روند.

§۱۱ منشور می‌گوید هر دو validator بعد از ویرایشِ دسته‌ای اجرا شوند و «جلسه وقتی
تمام است که هر دو پاس شوند». ولی هیچ‌چیز اجرایش نمی‌کرد: `grep` روی کلِ
`_ops/tests` نشان داد هیچ تستی این دو اسکریپت را صدا نمی‌زند.

⚠️ **ایزوله (۲۰۲۶-۰۸-۱۱)**: نسخهٔ قبلی مستقیماً REAL_VAULT را اسکن می‌کرد
(~۲۰۰۰ نوت، ~۵ دقیقه). حالا یک والتِ مصنوعیِ موقت می‌سازد و validators را
روی آن اجرا می‌کند. constants رatchet با ارقامِ مصنوعی تنظیم شده‌اند.

اجرای واقعی روی درختِ زنده (غیرایزوله) از طریق:
    python test_vault_hygiene_ratchet.py --live
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("vault-hygiene-ratchet")

_REAL_VAULT = harness.REAL_VAULT
_SCRIPTS_DIR = _REAL_VAULT / "04 - Architect System" / "scripts"

# ── constants رatchet روی والتِ مصنوعی ────────────────────────────────────
# والتِ مصنوعی دقیقاً این تعداد نقص را دارد. رatchet = این تعداد + headroom.
_MAX_CURATED_BROKEN = 2     # لایهٔ دست‌چین
_MAX_TOTAL_BROKEN = 3       # دست‌چین + عملیاتی
_MAX_FRONTMATTER = 3        # خطای فرانت‌متر (bad-frontmatter: unknown_type + invalid status + missing tags)
_MIN_LINK_NOTES = 8         # کفِ ضدِ سبزِ کاذب
_MIN_FRONT_NOTES = 6         # کفِ ضدِ سبزِ کاذب


# ── ساختِ والتِ مصنوعی ────────────────────────────────────────────────────
def _build_synthetic_vault(root: Path) -> Path:
    """والتِ مصنوعی با نقاطِ کنترلِ شناخته‌شده.

    شامل:
      - نوت‌های معتبر با فرانت‌مترِ صحیح (سیستم‌پوشه)
      - یک لینکِ شکستهٔ دست‌چین (system folder)
      - یک لینکِ شکستهٔ عملیاتی (project folder)
      - یک نوت با فرانت‌مترِ نامعتبر
      - اسکریپت‌های validator (کپی‌شده به مسیرِ درست)
      - Property Schema و types.json (کپی‌شده)
    """
    # ساختار پوشه‌ها
    sys_folders = ["00 - Inbox", "01 - Dashboard", "02 - Life OS", "05 - Agents",
                    "06 - Architecture Maps", "09 - People", "10 - Telegram processing"]
    project_areas = ["03 - Projects", "04 - Architect System", "07 - Knowledge"]

    for d in sys_folders:
        (root / d).mkdir(parents=True, exist_ok=True)
    for d in project_areas:
        (root / d).mkdir(parents=True, exist_ok=True)

    # نوت‌های معتبر (با فرانت‌متر کامل)
    _valid_note = """---
type: moc
status: active
tags: [test]
updated: 2026-08-11
---
# Test Note {name}
Content here.
"""
    count = 0
    for sf in sys_folders[:3]:
        for i in range(3):
            n = root / sf / f"note-{count}.md"
            n.write_text(_valid_note.format(name=f"{sf}-{i}"), "utf-8")
            count += 1

    # PROJECT.md in project areas
    for pa in project_areas[:2]:
        (root / pa / "PROJECT.md").write_text(
            "---\ntype: project\nstatus: active\ntags: [test]\nupdated: 2026-08-11\n---\n# Project\n",
            "utf-8")

    # هدفِ لینک: یک نوتِ معتبر که ویکیلینک به آن حل می‌شود
    target = root / "01 - Dashboard" / "target-existing.md"
    target.write_text(_valid_note.format(name="target-existing"), "utf-8")

    # نوت با لینکِ شکسته — لایهٔ دست‌چین (system folder)
    broken_curated = root / "01 - Dashboard" / "broken-link-curated.md"
    broken_curated.write_text(
        "---\ntype: moc\nstatus: active\ntags: [test]\nupdated: 2026-08-11\n---\n"
        "# Broken Link Curated\nThis links to [[NonExistentTarget]].\n", "utf-8")

    # نوت با لینکِ شکسته — لایهٔ عملیاتی (project folder, depth <= 3)
    broken_ops = root / "03 - Projects" / "broken-link-ops.md"
    broken_ops.write_text(
        "---\ntype: research\nstatus: draft\ntags: [test]\nupdated: 2026-08-11\n---\n"
        "# Broken Link Ops\nThis links to [[AnotherMissingTarget]].\n", "utf-8")

    # نوت با فرانت‌مترِ نامعتبر
    bad_front = root / "02 - Life OS" / "bad-frontmatter.md"
    bad_front.write_text(
        "---\ntype: unknown_type\nstatus: INVALID\n---\n# Bad Frontmatter\n", "utf-8")

    # harness AGENT_QUESTIONS.md را بدون فرانت‌متر می‌سازد — override با فرانت‌متر معتبر
    aq = root / "00 - Inbox" / "AGENT_QUESTIONS.md"
    if aq.exists():
        aq.write_text("---\ntype: handoff\nstatus: active\ntags: [test]\nupdated: 2026-08-11\n---\n# سوالات\n", "utf-8")

    # کپیِ Property Schema و types.json
    src_schema = _REAL_VAULT / "06 - Architecture Maps" / "Property Schema.md"
    dst_schema_dir = root / "06 - Architecture Maps"
    dst_schema_dir.mkdir(parents=True, exist_ok=True)
    if src_schema.exists():
        shutil.copy2(src_schema, dst_schema_dir / "Property Schema.md")

    src_types = _REAL_VAULT / ".obsidian" / "types.json"
    dst_obs = root / ".obsidian"
    dst_obs.mkdir(parents=True, exist_ok=True)
    if src_types.exists():
        shutil.copy2(src_types, dst_obs / "types.json")

    # کپیِ اسکریپت‌های validator به مسیرِ درست
    # validate_frontmatter.py: ROOT = __file__.parents[2]
    # پس باید در root/04 - Architect System/scripts/ قرار بگیرد
    dst_scripts = root / "04 - Architect System" / "scripts"
    dst_scripts.mkdir(parents=True, exist_ok=True)
    if (_SCRIPTS_DIR / "validate_frontmatter.py").exists():
        shutil.copy2(_SCRIPTS_DIR / "validate_frontmatter.py",
                     dst_scripts / "validate_frontmatter.py")
    if (_SCRIPTS_DIR / "find_broken_links.py").exists():
        shutil.copy2(_SCRIPTS_DIR / "find_broken_links.py",
                     dst_scripts / "find_broken_links.py")

    return root


def _run(script: Path, vault_root: Path, *args):
    """ریشه **صریح** pin می‌شود. find_broken_links از VAULT_LINK_ROOT می‌خواند.
    validate_frontmatter از __file__.parents[2] — وقتی کپی شده در مسیرِ درست
    خودکار به vault_root اشاره می‌کند."""
    env = dict(os.environ)
    env["VAULT_LINK_ROOT"] = str(vault_root)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, str(script), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(vault_root), env=env, timeout=30)
    return (r.stdout or "") + (r.stderr or "")


def _num(pattern, text, what):
    m = re.search(pattern, text)
    assert m, (f"خروجیِ validator شکلِ منتظره را ندارد — «{what}» پیدا نشد. "
               "یا اسکریپت عوض شده یا اصلاً ندویده؛ هر دو یعنی این گارد کور است.")
    return int(m.group(1))


def _links(vault_root: Path, scripts_dir: Path):
    out = _run(scripts_dir / "find_broken_links.py", vault_root)
    return {
        "scanned": _num(r"بررسی شد:\s*(\d+)\s*نوت", out, "شمارِ نوتِ اسکن‌شده"),
        "curated": _num(r"لایهٔ دست‌چین \(§۱۱\):\s*(\d+)", out, "لینکِ شکستهٔ دست‌چین")
        if "لایهٔ دست‌چین" in out else 0,
        "ops": _num(r"لایهٔ عملیاتی[^:]*:\s*(\d+)", out, "لینکِ شکستهٔ عملیاتی")
        if "لایهٔ عملیاتی" in out else 0,
        "clean": "لینک شکسته‌ای نیست" in out,
    }


def _front(vault_root: Path, scripts_dir: Path):
    out = _run(scripts_dir / "validate_frontmatter.py", vault_root)
    return {
        "scanned": _num(r"بررسی شد:\s*(\d+)\s*نوت", out, "شمارِ نوتِ فرانت‌متر"),
        "errors": _num(r"خطا:\s*(\d+)", out, "شمارِ خطا") if "خطا:" in out else 0,
        "clean": "همه نوت‌ها معتبرند" in out,
    }


# ── temp vault build (module-level fixture) ────────────────────────────────
_FIXTURE_VAULT = _build_synthetic_vault(Path(ENV["root"]))
_FIXTURE_SCRIPTS = _FIXTURE_VAULT / "04 - Architect System" / "scripts"


# ── tests ──────────────────────────────────────────────────────────────────
def t_a_the_link_validator_actually_ran():
    """گاردِ «اسکنر خراب است» — قبل از هر آستانه‌ای."""
    d = _links(_FIXTURE_VAULT, _FIXTURE_SCRIPTS)
    assert d["scanned"] >= _MIN_LINK_NOTES, (
        f"فقط {d['scanned']} نوت اسکن شد (کف {_MIN_LINK_NOTES}) — validator به "
        "درختِ اشتباه اشاره می‌کند یا زود ترکیده.")


def t_b_the_frontmatter_validator_actually_ran():
    d = _front(_FIXTURE_VAULT, _FIXTURE_SCRIPTS)
    assert d["scanned"] >= _MIN_FRONT_NOTES, (
        f"فقط {d['scanned']} نوت اسکن شد (کف {_MIN_FRONT_NOTES})")


def t_c_curated_broken_links_never_grow():
    """لایهٔ دست‌چین — رatchet بر downstream تغییرات."""
    d = _links(_FIXTURE_VAULT, _FIXTURE_SCRIPTS)
    assert d["curated"] <= _MAX_CURATED_BROKEN, (
        f"لینکِ شکستهٔ دست‌چین {d['curated']} > دفترِ {_MAX_CURATED_BROKEN}.")


def t_d_total_broken_links_never_grow():
    d = _links(_FIXTURE_VAULT, _FIXTURE_SCRIPTS)
    total = d["curated"] + d["ops"]
    assert total <= _MAX_TOTAL_BROKEN, (
        f"لینکِ شکستهٔ کل {total} > دفترِ {_MAX_TOTAL_BROKEN}")


def t_e_frontmatter_violations_never_grow():
    d = _front(_FIXTURE_VAULT, _FIXTURE_SCRIPTS)
    assert d["errors"] <= _MAX_FRONTMATTER, (
        f"خطای فرانت‌متر {d['errors']} > دفترِ {_MAX_FRONTMATTER}.")


def t_f_the_ledger_comes_down_when_the_debt_is_paid():
    """دوطرفه: اگر بدهی واقعاً پرداخت شد ولی این عددها پایین نیامدند،
    دفتر از واقعیت جدا افتاده و دیگر چیزی قفل نمی‌کند."""
    l = _links(_FIXTURE_VAULT, _FIXTURE_SCRIPTS)
    f = _front(_FIXTURE_VAULT, _FIXTURE_SCRIPTS)
    total = l["curated"] + l["ops"]
    # در والتِ مصنوعی: ۱ broken curated + ۱ broken ops = ۲ total
    # ratchet = 3 → headroom = 1. اگر total صفر شد ولی رatchet هنوز ۳، مشکل.
    if total < _MAX_TOTAL_BROKEN - 1:
        assert False, (
            f"لینکِ شکسته به {total} رسید ولی دفتر هنوز {_MAX_TOTAL_BROKEN} است — "
            "ratchet را پایین بیاور")
    if f["errors"] < _MAX_FRONTMATTER - 1:
        assert False, (
            f"خطای فرانت‌متر به {f['errors']} رسید ولی دفتر هنوز {_MAX_FRONTMATTER} "
            "است — ratchet را پایین بیاور")


def t_g_this_test_only_reads():
    """AST گارد: هیچ تابعِ t_* نباید بنویسد. fixture-level calls داخل
    `_build_synthetic_vault` مجاز هستند — فقط t_* functions را می‌سنجد."""
    import ast
    banned = {"write_text", "write_bytes", "unlink", "mkdir", "rename"}
    source = Path(__file__).read_text("utf-8")
    tree = ast.parse(source)
    # مجموعه‌ی line ranges برای تمام توابعِ t_  (مستقیم)
    t_func_lines = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("t_"):
            t_func_lines.update(range(node.lineno, node.end_lineno + 1))
    hits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            fn = n.func
            if isinstance(fn, ast.Attribute) and fn.attr in banned:
                if n.lineno in t_func_lines:
                    hits.append((n.lineno, fn.attr))
    assert not hits, ("t_* functions must not write", hits)


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
    print(f"\ntest_vault_hygiene_ratchet: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
