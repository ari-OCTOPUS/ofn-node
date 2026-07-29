# -*- coding: utf-8 -*-
"""یابنده wikilinkهای شکسته — dry-run: فقط گزارش، هیچ اصلاح خودکاری نمی‌کند.
اجرا:  python "04 - Architect System/scripts/find_broken_links.py"
دامنهٔ چک (۲۰۲۶-۰۷-۲۹، §۱۱): فقط لینک‌های «لایه دست‌چین» — همان scope ِ
validate_frontmatter. ایندکسِ مقصدها ولی کلِ vault است (منهای _Archive/_Duplicates/
_code و پوشه‌های نقطه‌دار) تا لینک به بسته‌های داخلی مثل OCTOPUS-DOCTOR شکسته شمرده نشود.
"""
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
# مقصدهای نامعتبر: آرشیو/قرنطینه/کد — لینکِ زنده به این‌ها یعنی نوت باید آپدیت شود
EXCLUDE = ("_Archive", "_Duplicates", ".git", "_code", ".obsidian", ".claude")
# placeholder های عمدی که لینک نیستند + نقل‌قول‌های تاریخی داخل لاگ چت
IGNORE_TARGETS = {"...", "…", "wikilink", "Atlas/Home MOC"}

SYSTEM_FOLDERS = {"00 - Inbox", "01 - Dashboard", "02 - Life OS", "05 - Agents",
                  "06 - Architecture Maps", "09 - People", "10 - Telegram processing"}
OPS_BASENAMES = {"README.md", "REGISTRY.md", "RUNBOOK.md", "VERDICT_QUEUE.md"}
PROJECT_AREAS = ("03 - Projects", "04 - Architect System", "07 - Knowledge")

def in_scope(p):
    """همان دامنهٔ validate_frontmatter — لایهٔ دست‌چین (§۱۱)."""
    parts = p.relative_to(ROOT).parts
    if p.name == "CLAUDE.md" or p.name in OPS_BASENAMES:
        return False
    if len(parts) == 1:
        return False
    if parts[0] in SYSTEM_FOLDERS:
        return True
    if p.name == "PROJECT.md":
        return parts[0] in PROJECT_AREAS and len(parts) <= 3
    if parts[0] in ("03 - Projects", "07 - Knowledge") and len(parts) <= 3:
        return not (len(parts) == 3 and parts[1].startswith("_"))
    return False

def norm(s):
    return unicodedata.normalize("NFC", s).lower()

def safe_is_file(p):
    try:
        return p.is_file()
    except OSError:
        return False

md_files, basenames, relpaths = [], set(), set()
for p in ROOT.rglob("*"):
    # فیلتر روی مسیر نسبی — مسیر مطلق ROOT ممکن است خودش ".claude" داشته باشد (worktree) و همه‌چیز را خالی exclude کند
    # پوشه‌های نقطه‌دار (worktreeهای جامانده مثل .wt-*، .zcode) نه چک می‌شوند نه مقصدند
    parts = p.relative_to(ROOT).parts
    if any(x in parts for x in EXCLUDE) or any(x.startswith(".") for x in parts) or not safe_is_file(p):
        continue
    rel = p.relative_to(ROOT).as_posix()
    relpaths.add(norm(rel))
    if p.suffix.lower() == ".md":
        relpaths.add(norm(rel[:-3]))
        basenames.add(norm(p.stem))
        if in_scope(p):                 # فقط لایهٔ دست‌چین چک می‌شود؛ ایندکس کامل می‌ماند
            md_files.append(p)
    else:
        basenames.add(norm(p.name))

pat = re.compile(r"\[\[([^\]\|#\^]+?)(?:[#\^][^\]\|]*)?(?:\|[^\]]*)?\]\]")
broken = []
for p in md_files:
    text = p.read_text(encoding="utf-8", errors="replace")
    for m in pat.finditer(text):
        target = m.group(1).strip().rstrip("\\")  # \| جدول‌ها
        if not target or target in IGNORE_TARGETS:
            continue
        t = norm(target)
        if t in relpaths or t in basenames or norm(target.split("/")[-1]) in basenames:
            continue
        broken.append((p.relative_to(ROOT).as_posix(), target))

print(f"بررسی شد: {len(md_files)} نوت")
if broken:
    print(f"لینک شکسته: {len(broken)}")
    for f, t in broken:
        print(f"  ✗ [[{t}]]  در  {f}")
    sys.exit(1)
print("✓ لینک شکسته‌ای نیست")
