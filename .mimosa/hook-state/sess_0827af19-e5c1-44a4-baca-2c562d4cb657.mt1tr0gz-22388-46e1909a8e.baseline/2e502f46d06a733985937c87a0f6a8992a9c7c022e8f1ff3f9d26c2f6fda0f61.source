#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dashboard_doctor.py — ماژول عیب‌یابی/تکمیل داشبورد (خروجی: JSON روی stdout).

چک‌های قطعی، صفر LLM، صفر نوشتن. ایجنت خروجی را تفسیر می‌کند و پیشنهاد تکمیل می‌دهد
(propose-only در اجرای زمان‌بندی؛ اعمال فقط در جلسهٔ تعاملی با verdict مالک).

خروجی دو نمره دارد (Option B، 2026-07-05): raw_score = تشخیص خام دست‌نخورده؛
effective_score = پس از لایهٔ suppression (verdict-gated) + انتقال چک‌های حساس‌به‌محیط
به needs_source_verify. هر تعدیل ledger_ref دارد → قابل‌ممیزی، بدون پنهان‌کردنِ سیگنال.

اجرا از ریشهٔ vault:  python3 "04 - Architect System/scripts/dashboard_doctor.py"
"""
import json, os, re, sys, datetime

ROOT = os.getcwd()
SKIP_DIRS = {"_Archive", "_Duplicates", "09 - People", ".obsidian", ".claude",
             ".git", "node_modules", "__pycache__", "_code", "_superseded",
             "secrets-export", "photos", "content", "research-results"}
KIT = ["PROJECT.md", "INDEX.md", "DecisionLog.md", "OpenQuestions.md"]
PROJECTS_DIR = os.path.join(ROOT, "03 - Projects")
DASHBOARD = os.path.join(ROOT, "01 - Dashboard", "SYSTEM-DASHBOARD.html")
# نام‌های استانداردِ عمداً تکراری (کیت + عمومی) — در چک تکرار نادیده گرفته می‌شوند
DUP_WHITELIST = {"PROJECT", "INDEX", "DecisionLog", "OpenQuestions", "README",
                 "TODO", "ROADMAP", "HANDOFF", "BLUEPRINT", "DEPLOY", "GLOSSARY"}
SECRET_PAT = re.compile(r"sk-ant-|sk-[A-Za-z0-9]{20,}|api[_-]?key\s*[:=]\s*\S|BEGIN [A-Z ]*KEY|xox[bap]-")
STALE_DAYS = 14
TODAY = datetime.date.today()

# ── لایهٔ verdict-gated (Option B، 2026-07-05) ──────────────────────────────
# تشخیص خام (بالا) دست‌نخورده می‌ماند؛ suppression/verify فقط لایهٔ گزارش‌اند.
# هر قاعده ledger_ref دارد تا افزودن هر تعدیل = یک verdict قابل‌ردیابی در EXPERIENCE-LEDGER.
SUPPRESS_RULES = [
    # تکرارِ by-design: pointerهای عمدیِ «MOVED - » (secret منتقل‌شده به secrets-export).
    {"id": "moved-pointer", "check": "dup-basename", "path_re": re.compile(r"(^|/)MOVED - "),
     "ledger_ref": "2026-07-04·row-26",
     "reason": "pointer عمدیِ secretِ منتقل‌شده — تکرار نامِ by-design، نه ابهام واقعی"},
]
# چک‌های حساس‌به‌محیط: سندباکس mount گاهی نمای کهنه/ناقص از فایل‌های تازه‌ویرایش‌شده می‌دهد
# (utf8 چه دُم‌بریده چه وسط‌فایل، و index-drift به‌خاطر INDEXِ کهنه). اوراکل = Windows-side.
# پنهان نمی‌شوند؛ به needs_source_verify منتقل و از گیت CRITICAL خارج می‌شوند تا نمره را کاذب نکوبند.
VERIFY_RULES = {
    "utf8-corrupt": ("utf8-suspect", "2026-07-04·row-27",
                     "سندباکس mount کهنه؛ قبل از CRITICAL از سمت ویندوز verify شود"),
    "index-drift": ("index-drift-suspect", "2026-07-04·row-26",
                    "INDEX ممکن است در mount کهنه باشد؛ از سمت ویندوز verify شود"),
}
VERIFY_W = 1  # وزن سبک: نه صفر (پنهان نیست) نه سنگین (قطعی‌شده نیست)

findings = []
def add(sev, check, path, msg, fix=""):
    findings.append({"severity": sev, "check": check, "path": path.replace(ROOT + os.sep, ""),
                     "msg": msg, "proposed_fix": fix})

def walk_md():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.endswith("-venv")]
        for fn in fns:
            if fn.endswith(".md"):
                yield os.path.join(dp, fn)

def fm_field(text, key):
    m = re.search(rf"^{key}:\s*(.+)$", text[:600], re.M)
    return m.group(1).strip().strip('"') if m else None

# ۱+۲ — کیت هر پروژه + INDEX drift
if os.path.isdir(PROJECTS_DIR):
    for proj in sorted(os.listdir(PROJECTS_DIR)):
        pdir = os.path.join(PROJECTS_DIR, proj)
        if not os.path.isdir(pdir):
            continue
        for k in KIT:
            if not os.path.isfile(os.path.join(pdir, k)):
                add("HIGH", "kit-missing", pdir, f"فایل کیت «{k}» وجود ندارد",
                    f"ساخت {k} طبق قالب LIVING-BRAIN-BLUEPRINT (با verdict)")
        idx = os.path.join(pdir, "INDEX.md")
        if os.path.isfile(idx):
            itext = open(idx, encoding="utf-8", errors="replace").read()
            for fn in os.listdir(pdir):
                if fn.endswith(".md") and fn != "INDEX.md":
                    base = fn[:-3]
                    if base not in itext:
                        add("MEDIUM", "index-drift", os.path.join(pdir, fn),
                            "نوت در INDEX پروژه فهرست نشده",
                            f"افزودن wikilink «{base}» به INDEX (با verdict)")

# ۳+۵ — UTF-8 خراب + کهنگی PROJECT.md + نبود project: binding در کیت
def _stable_read_verdict(path):
    """شاهدِ اضافه برای فایلِ undecodable — از doctor.stable_read (D-1، بلوپرینت §4).
    فقط در شاخهٔ خطا صدا زده می‌شود (vault سالم = صفر اثر). lazy-import چون doctor
    در import خودش opslib را می‌آورد (stdout→utf8) — فقط وقتی واقعاً corruption هست.
    نمره/label دست‌نخورده می‌ماند (VERIFY_RULES سر جایش) — این فقط evidence است؛
    swap کامل طبق GROUNDING-PLAN منتظر گیتِ F2 است."""
    try:
        _ops = os.path.join(ROOT, "_ops")
        if _ops not in sys.path:
            sys.path.insert(0, _ops)
            sys.path.insert(0, os.path.join(_ops, "budget"))
            sys.path.insert(0, os.path.join(_ops, "doctor"))
        from doctor import stable_read as _sr   # flat module _ops/doctor/doctor.py
        _txt, verdict, _ev = _sr(path)
        return verdict
    except Exception:
        return "unavailable"

for f in walk_md():
    try:
        text = open(f, encoding="utf-8").read()
    except UnicodeDecodeError as e:
        _v = _stable_read_verdict(f)
        add("CRITICAL", "utf8-corrupt", f,
            f"بایت خراب UTF-8: {e.reason} @ {e.start} · stable_read={_v}",
            "باز و ذخیره در Obsidian یا تعمیر دستی بایت"
            + ("" if _v in ("corrupt", "unavailable") else f" — stable_read می‌گوید {_v}: اول نمای منبع را verify کن"))
        continue
    base = os.path.basename(f)
    if base == "PROJECT.md":
        upd = fm_field(text, "updated")
        if upd:
            try:
                d = datetime.date.fromisoformat(upd)
                if (TODAY - d).days > STALE_DAYS:
                    add("MEDIUM", "stale-project", f,
                        f"updated={upd} (بیش از {STALE_DAYS} روز)", "بازبینی Active Context")
            except ValueError:
                add("LOW", "bad-date", f, f"updated نامعتبر: {upd}", "اصلاح فرمت YYYY-MM-DD")
    if base in ("INDEX.md", "DecisionLog.md", "OpenQuestions.md") and \
       os.path.dirname(os.path.dirname(f)) == PROJECTS_DIR and "project:" not in text[:400]:
        add("LOW", "kit-unbound", f, "فرانت‌متر کلید project: ندارد", "افزودن project: binding")

# ۴ — basename تکراری (خارج از whitelist)
seen = {}
for f in walk_md():
    b = os.path.basename(f)[:-3]
    seen.setdefault(b, []).append(f)
for b, paths in seen.items():
    if len(paths) > 1 and b not in DUP_WHITELIST:
        add("MEDIUM", "dup-basename", paths[1],
            f"wikilink بدون‌مسیر «[[{b}]]» مبهم است ({len(paths)} فایل)",
            "rename با verdict یا همیشه لینک مسیردار")

# ۶+۷ — سلامت خود ارتیفکت: hash، مقصد لینک‌های obsidian://، الگوی secret
if os.path.isfile(DASHBOARD):
    html_text = open(DASHBOARD, encoding="utf-8", errors="replace").read()
    if "model-hash:" not in html_text:
        add("HIGH", "html-no-hash", DASHBOARD, "کامنت model-hash نیست — idempotency شکسته",
            "بازساخت با پرامپت داشبورد")
    if SECRET_PAT.search(html_text):
        add("CRITICAL", "html-secret", DASHBOARD, "الگوی شبیه secret در HTML!",
            "توقف انتشار + پاک‌سازی فوری")
    for m in re.finditer(r'obsidian://open\?vault=backup&file=([^"\']+)', html_text):
        import urllib.parse
        rel = urllib.parse.unquote(m.group(1))
        if not (os.path.isfile(os.path.join(ROOT, rel + ".md")) or
                os.path.isfile(os.path.join(ROOT, rel))):
            add("HIGH", "html-dead-target", DASHBOARD, f"مقصد لینک وجود ندارد: {rel}",
                "اصلاح مسیر در رندر بعدی")
else:
    add("HIGH", "html-missing", DASHBOARD, "فایل داشبورد وجود ندارد", "اجرای پرامپت داشبورد")

sev_w = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 3, "LOW": 1}

def _match_suppress(f):
    for r in SUPPRESS_RULES:
        if f["check"] == r["check"] and r["path_re"].search(f["path"]):
            return r
    return None

# لایهٔ گزارش: تفکیک خام به suppressed / needs_source_verify / effective (بدون حذف).
suppressed, needs_verify, effective = [], [], []
for f in findings:
    r = _match_suppress(f)
    if r:
        suppressed.append({**f, "suppressed_by": r["id"], "ledger_ref": r["ledger_ref"],
                           "suppress_reason": r["reason"]})
        continue
    if f["check"] in VERIFY_RULES:
        lbl, ref, reason = VERIFY_RULES[f["check"]]
        needs_verify.append({**f, "check": lbl, "raw_check": f["check"],
                             "needs_source_verify": True, "ledger_ref": ref, "note": reason})
        continue
    effective.append(f)

def _score(items, extra=0):
    return max(0, 100 - sum(sev_w[f["severity"]] for f in items) - extra)

raw_score = _score(findings)
effective_score = _score(effective, extra=VERIFY_W * len(needs_verify))
order = list(sev_w)
out = {"generated": TODAY.isoformat(),
       "detection_env": "sandbox-mount (اوراکلِ نهایی = Windows-side)",
       "raw_score": raw_score, "effective_score": effective_score,
       "counts_raw": {s: sum(1 for f in findings if f["severity"] == s) for s in sev_w},
       "counts_effective": {s: sum(1 for f in effective if f["severity"] == s) for s in sev_w},
       "suppressed": suppressed,
       "needs_source_verify": needs_verify,
       "findings": sorted(effective, key=lambda f: order.index(f["severity"]))}
print(json.dumps(out, ensure_ascii=False, indent=1))
sys.exit(0 if effective_score >= 70 else 1)
