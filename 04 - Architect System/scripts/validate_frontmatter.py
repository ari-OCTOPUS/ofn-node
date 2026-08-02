# -*- coding: utf-8 -*-
"""اعتبارسنج فرانت‌متر — طبق 06 - Architecture Maps/Property Schema.md
dry-run است: فقط گزارش می‌دهد، چیزی را تغییر نمی‌دهد. خروج غیرصفر = خطا موجود.
اجرا:  python "04 - Architect System/scripts/validate_frontmatter.py"
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SCHEMA_MD = ROOT / "06 - Architecture Maps" / "Property Schema.md"
TYPES_JSON = ROOT / ".obsidian" / "types.json"
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

CORE_KEYS = {"type", "status", "tags", "updated"}  # created روی نوت‌های قدیمی اختیاری است

# ── A3 (۲۰۲۶-۰۸-۰۳): schema تک‌منبعِ حقیقت است، نه این فایل ──────────────────
# تا امروز این سه فهرست این‌جا هاردکد بودند و بی‌صدا از Property Schema جدا
# می‌افتادند: افزودنِ دو کلیدِ ویس به schema، validator را همچنان قرمز نگه داشت
# تا **سومین** جا هم دستی ویرایش شد. حالا از بلوکِ ماشین‌خوانِ §۲.۳ خوانده می‌شوند.
# فهرستِ زیر فقط **پشتیبان** است: اگر schema ناخوانا بود، کار می‌کند ولی
# با ⚠️ ِ صریح اعلام می‌کند که ممکن است کهنه باشد — سکوت بدترین حالت است.
_FALLBACK_KEY_TYPES = {
    "type": "text", "project": "text", "status": "text", "tags": "multitext",
    "created": "date", "updated": "date", "kind": "text", "owner": "text",
    "start": "date", "source": "text", "sources": "multitext",
    "created_by": "text", "org": "text", "role": "text", "telegram": "text",
    "related": "multitext", "model": "text", "trigger": "text", "code": "text",
    "version": "text", "aliases": "multitext", "risk_level": "text",
    "autonomy_level": "text", "epistemic_status": "text", "parent": "text",
    "aligns_to": "text", "extends": "text", "supersedes": "text",
    "superseded_by": "text", "canon_rank": "text", "depends-on": "multitext",
    "closes": "multitext", "target": "text", "audits": "text", "result": "text",
    "language": "text", "salience": "number", "message_id": "number",
    "chat_id": "number", "file_id": "text", "duration": "number",
    "transcribed_by": "text", "transcript_secs": "number",
}
_FALLBACK_TYPES = {"project", "knowledge", "log", "telegram-log", "person", "agent",
                   "moc", "reference", "handoff", "dashboard", "instructions",
                   "report", "research", "prompt",
                   "architecture", "design", "proposal", "runbook", "tasks"}
_FALLBACK_STATUSES = {"idea", "active", "paused", "done", "archived",
                      "inbox", "draft", "ready", "superseded"}

_BEGIN, _END = "<!-- SCHEMA-MACHINE:BEGIN", "<!-- SCHEMA-MACHINE:END"


def parse_schema_block(text):
    """بلوکِ §۲.۳ → (keys{name: type}, types, statuses). ناقص/غایب ⇒ None.
    عمداً سخت‌گیر است: نیمه‌پارس‌شده بدتر از پارس‌نشده است، چون سکوت می‌سازد."""
    lo = text.find(_BEGIN)
    hi = text.find(_END, lo + 1) if lo >= 0 else -1
    if lo < 0 or hi < 0:
        return None
    body = text[text.find("\n", lo) + 1:hi]
    keys, types, statuses, in_keys = {}, set(), set(), False
    for raw in body.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("```") or stripped.startswith("#"):
            continue
        m = re.match(r"^(types|statuses):\s*\[(.*)\]$", stripped)
        if m:
            vals = {v.strip() for v in m.group(2).split(",") if v.strip()}
            (types if m.group(1) == "types" else statuses).update(vals)
            in_keys = False
            continue
        if stripped == "keys:":
            in_keys = True
            continue
        m = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_-]*):\s*(\S+)$", line)
        if m and in_keys:
            keys[m.group(1)] = m.group(2)
            continue
    if not keys or not types or not statuses:
        return None
    return keys, types, statuses


def load_schema():
    """(key_types, TYPES, STATUSES, source). source='fallback' ⇒ باید اعلام شود."""
    try:
        parsed = parse_schema_block(SCHEMA_MD.read_text(encoding="utf-8"))
    except OSError:
        parsed = None
    if parsed:
        return parsed[0], parsed[1], parsed[2], "schema"
    return dict(_FALLBACK_KEY_TYPES), set(_FALLBACK_TYPES), set(_FALLBACK_STATUSES), "fallback"


SCHEMA_KEY_TYPES, TYPES, STATUSES, SCHEMA_SOURCE = load_schema()
KNOWN_KEYS = CORE_KEYS | set(SCHEMA_KEY_TYPES)


def types_json_drift():
    """کلیدهای schema در برابر `.obsidian/types.json` — رانش را **نام‌به‌نام** بگو.
    این دومین جایی است که کلید باید بنشیند؛ نگفتنش یعنی همان تلهٔ سه‌جایی."""
    try:
        declared = set(json.loads(TYPES_JSON.read_text(encoding="utf-8")).get("types", {}))
    except (OSError, ValueError):
        return ["`.obsidian/types.json` خوانده نشد — رانشِ کلیدها بررسی نشد"]
    out = []
    missing = sorted(set(SCHEMA_KEY_TYPES) - declared)
    extra = sorted(declared - set(SCHEMA_KEY_TYPES))
    if missing:
        out.append(f"در schema هست ولی در types.json نیست: {', '.join(missing)}")
    if extra:
        out.append(f"در types.json هست ولی در schema نیست: {', '.join(extra)}")
    return out

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

def check_note(rel, fm, *, known_keys=None, types=None, statuses=None):
    """خطاهای یک نوت. سه فهرست **تزریق‌شدنی‌اند** تا تست بتواند schema ِ ساختگی
    بدهد و ثابت کند پذیرشِ کلید واقعاً از schema می‌آید نه از فهرستِ پشتیبان."""
    known_keys = KNOWN_KEYS if known_keys is None else known_keys
    types = TYPES if types is None else types
    statuses = STATUSES if statuses is None else statuses
    if fm is None:
        return [f"{rel}: فرانت‌متر ندارد"]
    out = []
    missing = CORE_KEYS - set(fm)
    if missing and fm.get("type") != "handoff":
        out.append(f"{rel}: کلید(های) هسته غایب: {', '.join(sorted(missing))}")
    t = fm.get("type", "")
    if t and t not in types:
        out.append(f"{rel}: type نامعتبر: '{t}'")
    s = fm.get("status", "")
    if s and s not in statuses:
        out.append(f"{rel}: status نامعتبر: '{s}' (مجاز: {'/'.join(sorted(statuses))})")
    for k in ("updated", "created", "start"):
        v = fm.get(k, "")
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            out.append(f"{rel}: {k} باید YYYY-MM-DD باشد: '{v}'")
    tags = fm.get("tags", "")
    if "tags" in fm and not tags.startswith("["):
        out.append(f"{rel}: tags باید لیست باشد: '{tags}'")
    unknown = set(fm) - known_keys
    if unknown:
        out.append(f"{rel}: کلید(های) خارج از schema: {', '.join(sorted(unknown))} — اول Property Schema را آپدیت کن")
    return out


def scan():
    errors, count = [], 0
    for p in ROOT.rglob("*.md"):
        # فیلتر روی مسیر نسبی — مسیر مطلق ROOT ممکن است خودش ".claude" داشته باشد (worktree) و همه‌چیز را خالی exclude کند
        # پوشه‌های نقطه‌دار (worktreeهای جامانده مثل .wt-*، .zcode) هرگز نوت نیستند
        parts = p.relative_to(ROOT).parts
        if any(x in parts for x in EXCLUDE) or any(x.startswith(".") for x in parts) or not in_scope(p):
            continue
        rel = p.relative_to(ROOT).as_posix()
        count += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        errors.extend(check_note(rel, parse_frontmatter(text)))
    return errors, count


def main():
    """۰ = سالم. اسکن زیرِ __main__ است تا این فایل **import‌شدنی** بماند —
    وگرنه تستِ پذیرش نمی‌تواند بدونِ جاروی کلِ والت منطقش را بسنجد."""
    errors, count = scan()
    print(f"بررسی شد: {count} نوت")
    print(f"منبعِ schema: {SCHEMA_SOURCE}  ({len(KNOWN_KEYS)} کلید · {len(TYPES)} type · {len(STATUSES)} status)")
    if SCHEMA_SOURCE == "fallback":
        print("  ⚠️ بلوکِ ماشین‌خوانِ §۲.۳ ِ Property Schema خوانده/پارس نشد — فهرستِ")
        print("     پشتیبانِ هاردکد به کار رفت و **ممکن است کهنه باشد**. اول آن بلوک را درست کن.")

    drift = types_json_drift() if SCHEMA_SOURCE == "schema" else []
    if drift:
        print(f"رانشِ schema ↔ types.json: {len(drift)}")
        for d in drift:
            print("  ✗", d)

    if errors:
        print(f"خطا: {len(errors)}")
        for e in errors:
            print("  ✗", e)
    if errors or drift:
        return 1
    print("✓ همه نوت‌ها معتبرند")
    return 0


if __name__ == "__main__":
    sys.exit(main())
