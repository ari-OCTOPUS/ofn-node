# -*- coding: utf-8 -*-
"""یابنده wikilinkهای شکسته — dry-run: فقط گزارش، هیچ اصلاح خودکاری نمی‌کند.
اجرا:  python "04 - Architect System/scripts/find_broken_links.py"
"""
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
EXCLUDE = ("_Archive", "_Duplicates", ".git", "_code", ".obsidian", ".claude")
# placeholder های عمدی که لینک نیستند + نقل‌قول‌های تاریخی داخل لاگ چت
IGNORE_TARGETS = {"...", "…", "wikilink", "Atlas/Home MOC"}

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
    if any(x in p.relative_to(ROOT).parts for x in EXCLUDE) or not safe_is_file(p):
        continue
    rel = p.relative_to(ROOT).as_posix()
    relpaths.add(norm(rel))
    if p.suffix.lower() == ".md":
        md_files.append(p)
        relpaths.add(norm(rel[:-3]))
        basenames.add(norm(p.stem))
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
