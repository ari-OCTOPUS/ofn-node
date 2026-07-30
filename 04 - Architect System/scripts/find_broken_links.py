# -*- coding: utf-8 -*-
"""یابنده wikilinkهای شکسته — dry-run: فقط گزارش، هیچ اصلاح خودکاری نمی‌کند.
اجرا:  python "04 - Architect System/scripts/find_broken_links.py"
        python "…/find_broken_links.py" --curated    # فقط لایهٔ دست‌چین (گیتِ باریکِ قبلی)

دامنهٔ منبعِ لینک (۲۰۲۶-۰۷-۳۰): **هر .mdِ درختِ زنده** — `in_link_scope`.
تا دیروز این اسکریپت `in_scope` ِ validate_frontmatter را قرض می‌گرفت و همان را برای
انتخابِ *منبع*ها به کار می‌برد؛ نتیجه: ۴۵ فایلِ ریشه، کلِ `_ops`/`_memory` و کلِ بستهٔ
OCTOPUS-DOCTOR هرگز برای لینکِ خروجی اسکن نمی‌شدند (۴۲۳ نوت دیده می‌شد از ۲۱۴۰).
یک شکستگیِ واقعی که هیچ‌وقت گزارش نشد: در `OCTOPUS-DOCTOR/70-نسخه‌ها/` لینکِ
`RESEARCH-PROMPTS-round3-architecture` که تنها هم‌نامش زیرِ `_Duplicates` است.
دامنهٔ فرانت‌متر عوض نشده: سندِ عملیاتی نوتِ دست‌چین نیست (§۱۱).

ایندکسِ مقصدها کلِ vault است (منهای _Archive/_Duplicates/_code و پوشه‌های نقطه‌دار)
تا لینک به بسته‌های داخلی شکسته شمرده نشود.
گزارش دو بلوک دارد: «لایهٔ دست‌چین» (قانونِ vault) و «لایهٔ عملیاتی/بستهٔ سند»
(بک‌لاگِ تازه-مرئی). هر دو در exit code حساب می‌شوند؛ `--curated` فقط بلوکِ اول.
"""
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
# پیش‌فرض: درختِ زنده. `VAULT_LINK_ROOT` فقط برای آزمونِ خودِ این اسکریپت روی
# fixture است (درسِ تکرارشده: اسکریپتی که ROOT ِ هاردکد دارد فقط روی والتِ زنده
# قابلِ آزمون است). هیچ رفتارِ پیش‌فرضی عوض نمی‌شود.
ROOT = Path(os.environ.get("VAULT_LINK_ROOT") or Path(__file__).resolve().parents[2]).resolve()
# مقصدهای نامعتبر: آرشیو/قرنطینه/کد — لینکِ زنده به این‌ها یعنی نوت باید آپدیت شود
EXCLUDE = ("_Archive", "_Duplicates", ".git", "_code", ".obsidian", ".claude")
# placeholder های عمدی که لینک نیستند + نقل‌قول‌های تاریخی داخل لاگ چت
IGNORE_TARGETS = {"...", "…", "wikilink", "Atlas/Home MOC"}

SYSTEM_FOLDERS = {"00 - Inbox", "01 - Dashboard", "02 - Life OS", "05 - Agents",
                  "06 - Architecture Maps", "09 - People", "10 - Telegram processing"}
OPS_BASENAMES = {"README.md", "REGISTRY.md", "RUNBOOK.md", "VERDICT_QUEUE.md"}
PROJECT_AREAS = ("03 - Projects", "04 - Architect System", "07 - Knowledge")

# ۲۰۲۶-۰۷-۳۰: با پهن‌شدنِ دامنهٔ منبع، مسیرهای حساسِ .agentignore هم زیرِ اسکن می‌آمدند.
# این‌ها نه خوانده می‌شوند نه مسیرشان در گزارش echo می‌شود (§۱۰ + .agentignore).
# به‌عنوان *مقصد* در ایندکس می‌مانند تا لینکِ سالم به آن‌ها شکسته شمرده نشود.
# ۲۰۲۶-۰۷-۳۰ (تصحیحِ امنیتی) — الگوها از خودِ `.agentignore` خوانده می‌شوند، نه
# هاردکد. فهرستِ هاردکدِ قبلی فقط ۴ پوشه + یک پسوند بود و globهای واقعیِ
# `.agentignore` (`*secret*`، `*key*`، `*wallet*`، `*seed*`، `*.pem`، `*MyHeritage*`،
# `*23andme*`، `armin_dna*`) را پوشش نمی‌داد ⇒ با پهن‌شدنِ دامنه، فایل‌هایی مثلِ
# یک `SECRETS.md` واقعاً **باز و خوانده** می‌شدند (نقضِ §۱۰).
# ⚠️ تطبیق **بی‌حساسیت به حروف** است: `SECRETS.md` با الگوی `*secret*` به‌صورتِ
# case-sensitive مطابقت نمی‌کند — همان درزی که این فایل را از فیلتر رد می‌کرد.
def _load_agentignore():
    """الگوهای `.agentignore` → (dir_names, globs, exact_paths). fail-soft:
    اگر فایل نبود، به فهرستِ کمینهٔ امن برمی‌گردد (هرگز به «همه مجاز»)."""
    dirs, globs, exact = set(), set(), set()
    try:
        for line in (ROOT / ".agentignore").read_text("utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            s = s.lstrip("/")
            if s.endswith("/"):
                dirs.add(s.rstrip("/").lower().split("/")[-1])
            elif "*" in s or "?" in s:
                globs.add(s.lower())
            else:
                exact.add(s.lower())
                if "/" not in s:
                    globs.add(s.lower())
    except OSError:
        pass
    dirs |= {"08 - partner (pii)", "secrets-export", "امواج مغزی", "neuro-hrv-nof1"}
    globs |= {"*-tokens.md", "*secret*", "*key*", "*wallet*", "*seed*", "*.pem",
              "owner-profile*"}      # OWNER-PROFILE: هم .json هم -LOG.md (PII، کامیتِ 21042e6)
    return dirs, globs, exact


SENSITIVE_DIRS, SENSITIVE_GLOBS, SENSITIVE_EXACT = _load_agentignore()


def _is_sensitive(parts) -> bool:
    """هر مسیری که `.agentignore` منع کرده — بی‌حساسیت به حروف، روی هر سگمنت."""
    import fnmatch
    low = [seg.lower() for seg in parts]
    if any(seg in SENSITIVE_DIRS for seg in low):
        return True
    rel = "/".join(low)
    if rel in SENSITIVE_EXACT:
        return True
    return any(fnmatch.fnmatch(seg, g) for seg in low for g in SENSITIVE_GLOBS)
# نقل‌قول‌های تاریخیِ داخلِ capture خامِ تلگرام لینکِ زنده نیستند
RAW_CAPTURE = ("10 - Telegram processing", "Raw")


def in_link_scope(p):
    """دامنهٔ *منبعِ* لینک: هر .mdِ درختِ زنده، منهای captureِ خامِ تلگرام و
    مسیرهای حساس. فیلترهای EXCLUDE/dot-dir جای دیگر (حلقهٔ اصلی) اعمال می‌شوند."""
    parts = p.relative_to(ROOT).parts
    if _is_sensitive(parts):
        return False
    for i, seg in enumerate(parts[:-1]):
        if seg == RAW_CAPTURE[0] and RAW_CAPTURE[1] in parts[i + 1:]:
            return False
    return True


def in_curated_scope(p):
    """لایهٔ دست‌چین (§۱۱) — همان دامنهٔ validate_frontmatter. حالا فقط
    *برچسبِ tier* در گزارش است، نه فیلترِ منبع."""
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
        if in_link_scope(p):            # هر .mdِ زنده منبعِ لینک است؛ ایندکس کامل می‌ماند
            md_files.append(p)
    else:
        basenames.add(norm(p.name))

pat = re.compile(r"\[\[([^\]\|#\^]+?)(?:[#\^][^\]\|]*)?(?:\|[^\]]*)?\]\]")

# 2026-07-29: نحوِ wikilink داخلِ بک‌تیک **لینک نیست** — ابسیدین آن را کد رندر
# می‌کند. تا امروز این validator روی متنِ خام می‌دوید، پس هر سندی که نحو را نقل
# می‌کرد (یا JSONای که [[ داشت، مثل {"inline_keyboard":[[{...}]]}) قرمزِ کاذب
# می‌گرفت. اول بلوکِ fenced، بعد code spanِ درون‌خطی حذف می‌شود.
_FENCED = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)
_INLINE = re.compile(r"`[^`\n]*`")


def strip_code(text: str) -> str:
    """متن بدونِ بلوکِ fenced و code spanِ درون‌خطی — همان چیزی که ابسیدین
    به‌عنوان لینک می‌بیند. ترتیب مهم است: اول fenced، بعد inline."""
    return _INLINE.sub("", _FENCED.sub("", text))


CURATED_ONLY = "--curated" in sys.argv


def resolve_target(target):
    """آیا این هدف در vault پیدا می‌شود؟
    ۲۰۲۶-۰۷-۳۰: پسوندِ صریحِ `.md` را می‌ریزد — ابسیدین `[[Foo.md]]` را دقیقاً مثل
    `[[Foo]]` حل می‌کند، ولی این validator تا امروز فقط stem را می‌شناخت و ۴ لینکِ
    سالم (اونلی فنز/SYNTH-05) را قرمزِ کاذب می‌گرفت."""
    t = norm(target)
    leaf = norm(target.split("/")[-1])
    for cand in (t, t[:-3] if t.endswith(".md") else t):
        if cand in relpaths or cand in basenames:
            return True
    return leaf in basenames or (leaf.endswith(".md") and leaf[:-3] in basenames)


curated, ops = [], []
for p in md_files:
    if CURATED_ONLY and not in_curated_scope(p):
        continue
    text = strip_code(p.read_text(encoding="utf-8", errors="replace"))
    for m in pat.finditer(text):
        target = m.group(1).strip().rstrip("\\")  # \| جدول‌ها
        if not target or target in IGNORE_TARGETS:
            continue
        if resolve_target(target):
            continue
        row = (p.relative_to(ROOT).as_posix(), target)
        (curated if in_curated_scope(p) else ops).append(row)

scanned = sum(1 for p in md_files if not CURATED_ONLY or in_curated_scope(p))
print(f"بررسی شد: {scanned} نوت" + ("  (--curated)" if CURATED_ONLY else ""))
if curated:
    print(f"لینک شکسته — لایهٔ دست‌چین (§۱۱): {len(curated)}")
    for f, t in curated:
        print(f"  ✗ [[{t}]]  در  {f}")
if ops:
    print(f"لینک شکسته — لایهٔ عملیاتی/بستهٔ سند: {len(ops)}")
    for f, t in ops:
        print(f"  ✗ [[{t}]]  در  {f}")
if curated or ops:
    sys.exit(1)
print("✓ لینک شکسته‌ای نیست")
