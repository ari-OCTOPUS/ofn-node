# -*- coding: utf-8 -*-
"""اعتبارسنج فرانت‌متر — طبق 06 - Architecture Maps/Property Schema.md
dry-run است: فقط گزارش می‌دهد، چیزی را تغییر نمی‌دهد. خروج غیرصفر = خطا موجود.
اجرا:  python "04 - Architect System/scripts/validate_frontmatter.py"
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
EXCLUDE = ("_Archive", "_Duplicates", ".git", "_code", ".obsidian", ".claude", "_Templates",
           ".pytest_cache", "node_modules",
           # ۲۰۲۶-۰۷-۲۹: والتِ دکترِ اختاپوس بستهٔ سندِ داخلی است (§۱۱ — قراردادِ خودش)
           "OCTOPUS-DOCTOR")

# دامنه: فقط «لایه دست‌چین» vault. بسته‌های سند داخلی پروژه‌ها (brushline، کاریابی،
# زیرپوشه‌های عمیق Mining/فیوژن، ساختار داخلی architect) قرارداد خودشان را دارند و چک نمی‌شوند.
SYSTEM_FOLDERS = {"00 - Inbox", "01 - Dashboard", "02 - Life OS", "05 - Agents",
                  "06 - Architecture Maps", "09 - People", "10 - Telegram processing"}
# ۲۰۲۶-۰۷-۲۹: سندهای عملیاتیِ استاندارد (§۱۱) قراردادِ خودشان را دارند — نوتِ vault نیستند
OPS_BASENAMES = {"README.md", "REGISTRY.md", "RUNBOOK.md", "VERDICT_QUEUE.md"}
PROJECT_AREAS = ("03 - Projects", "04 - Architect System", "07 - Knowledge")

def in_scope(p):
    rel = p.relative_to(ROOT)
    parts = rel.parts
    if p.name == "CLAUDE.md":          # فایل config است، نه نوت
        return False
    if p.name in OPS_BASENAMES:         # سندِ عملیاتی (§۱۱)
        return False
    if len(parts) == 1:                 # ریشه = لایهٔ سندِ عملیاتی/staging، نه نوت (۲۰۲۶-۰۷-۲۹)
        return False
    if parts[0] in SYSTEM_FOLDERS:      # پوشه‌های سیستمی: کامل
        return True
    if p.name == "PROJECT.md":          # شناسنامه‌های سطحِ پروژه؛ زیرپکیج‌های عمیق‌تر
        return parts[0] in PROJECT_AREAS and len(parts) <= 3  # (مثل attach-proposal) قراردادِ خودشان
    if parts[0] in ("03 - Projects", "07 - Knowledge") and len(parts) <= 3:
        # نوت‌های سطح‌بالا؛ زیرپوشه‌های «_» بستهٔ داخلی‌اند (_audit، _OCTOPUS-PMO)
        return not (len(parts) == 3 and parts[1].startswith("_"))
    return False

TYPES = {"project", "knowledge", "log", "telegram-log", "person", "agent",
         "moc", "reference", "handoff", "dashboard", "instructions",
         "report", "research", "prompt",
         "architecture", "design", "proposal", "runbook", "tasks"}  # گسترش 2026-07-04 (دو مرحله) با تأیید مالک — هماهنگ با Property Schema
STATUSES = {"idea", "active", "paused", "done", "archived",
            "inbox", "draft", "ready", "superseded"}  # گسترش 2026-07-04 با تأیید مالک
CORE_KEYS = {"type", "status", "tags", "updated"}  # created روی نوت‌های قدیمی اختیاری است
KNOWN_KEYS = CORE_KEYS | {"project", "created", "kind", "owner", "start", "source", "sources",
                          "created_by", "org", "role", "telegram", "related", "model",
                          "trigger", "code", "version", "aliases", "tags",
                          "risk_level", "autonomy_level", "epistemic_status",
                          # کلیدهای رابطه/عملیاتی — گسترش 2026-07-04 (§۲.۱ Property Schema)
                          "parent", "aligns_to", "extends", "supersedes", "superseded_by",
                          "canon_rank", "depends-on", "closes", "target",
                          "audits", "result", "language", "salience",
                          # کلیدهای capture ماشینی تلگرام — ۲۰۲۶-۰۷-۳۱، رأی capture (§۲.۲ Property Schema)
                          "message_id", "chat_id", "file_id", "duration",
                          # کلیدهای transcribe ویس — ۲۰۲۶-۰۸-۰۳، رأی مالک (§۲.۲ Property Schema)
                          "transcribed_by", "transcript_secs"}

def parse_frontmatter(text):
    if not text.startswith("---"):
        return None
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm

errors = []
count = 0
for p in ROOT.rglob("*.md"):
    # فیلتر روی مسیر نسبی — مسیر مطلق ROOT ممکن است خودش ".claude" داشته باشد (worktree) و همه‌چیز را خالی exclude کند
    # پوشه‌های نقطه‌دار (worktreeهای جامانده مثل .wt-*، .zcode) هرگز نوت نیستند
    parts = p.relative_to(ROOT).parts
    if any(x in parts for x in EXCLUDE) or any(x.startswith(".") for x in parts) or not in_scope(p):
        continue
    rel = p.relative_to(ROOT).as_posix()
    count += 1
    text = p.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{rel}: فرانت‌متر ندارد")
        continue
    missing = CORE_KEYS - set(fm)
    if missing and fm.get("type") != "handoff":
        errors.append(f"{rel}: کلید(های) هسته غایب: {', '.join(sorted(missing))}")
    t = fm.get("type", "")
    if t and t not in TYPES:
        errors.append(f"{rel}: type نامعتبر: '{t}'")
    s = fm.get("status", "")
    if s and s not in STATUSES:
        errors.append(f"{rel}: status نامعتبر: '{s}' (مجاز: {'/'.join(sorted(STATUSES))})")
    for k in ("updated", "created", "start"):
        v = fm.get(k, "")
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            errors.append(f"{rel}: {k} باید YYYY-MM-DD باشد: '{v}'")
    tags = fm.get("tags", "")
    if "tags" in fm and not tags.startswith("["):
        errors.append(f"{rel}: tags باید لیست باشد: '{tags}'")
    unknown = set(fm) - KNOWN_KEYS
    if unknown:
        errors.append(f"{rel}: کلید(های) خارج از schema: {', '.join(sorted(unknown))} — اول Property Schema را آپدیت کن")

print(f"بررسی شد: {count} نوت")
if errors:
    print(f"خطا: {len(errors)}")
    for e in errors:
        print("  ✗", e)
    sys.exit(1)
print("✓ همه نوت‌ها معتبرند")
