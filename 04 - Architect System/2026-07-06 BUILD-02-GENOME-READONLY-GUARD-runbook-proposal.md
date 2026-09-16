---
type: runbook-proposal
status: proposal            # propose-only — runbookِ آماده. من چیزی نساختم/اجرا نکردم.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «قدم دو رو کامل کن» 2026-07-06"
depends_on: "[[2026-07-06 BUILD-01-OFFBOX-BACKUP-runbook-proposal]] · REPORT §۴ قدم۲ · تطبیق D4"
grounds: [RESEARCH-GENOME-RECONCILIATION D4 (DEEP-GAP شکاف ۸), DOCTOR-BLUEPRINT row-36/47 (FUSE), ARCHITECT_CHARTER immutable-to-agents]
tags: [build-02, genome, read-only, integrity-guard, evaluator-tampering, propose-only]
---

# BUILD-02 — read-only فنیِ ژنوم + گاردِ یکپارچگی (propose-only)

> **صادقانه از همین اول:** الان چیزی که می‌گیریم **تشخیص (detection)** است، نه **پیش‌گیریِ کاملِ OS-level**. پیش‌گیریِ per-identity به پروسهٔ مستقلِ حلقه نیاز دارد که در **فاز ۵** می‌آید. این قدم، شکافِ ۸ (evaluator-tampering) را با یک گاردِ **قطعی و zero-LLM** می‌بندد تا آن‌موقع. (این دقیقاً ریسکِ R3 گزارش است.)

---

## ۱. «ژنوم» چه فایل‌هایی‌اند (مجموعهٔ تحتِ‌حفاظت)
```
architect/ARCHITECT_CHARTER.md
learning-engine/LEARNING-CONTRACT.yaml
learning-engine/MUTATION-WHITELIST.md
learning-engine/ENGINE-PROMPT.md        # فقط §۰ invariants مهم است، ولی کلِ فایل قفل می‌شود
(آینده) learning-engine/EVOLUTIONARY-DOCTOR-RUBRIC.md   # وقتی فاز ۴ ساخته شد
```

## ۲. دو لایهٔ حفاظت (صادقانه دربارهٔ هرکدام)
| لایه | چه می‌کند | الان ممکن؟ |
|---|---|---|
| **A. گاردِ تشخیصی** (`genome_guard.py`) | هر تغییرِ ژنومِ بدونِ‌تأیید را CRITICAL می‌کند | ✅ **بله، همین حالا** |
| **B. read-only سبک** (Windows `attrib +R`) | ویرایشِ تصادفی را سخت می‌کند (نه یک مهاجمِ مصمم) | ✅ بله (با workflowِ §۶) |
| **C. پیش‌گیریِ per-identity** (ACL deny-write برای هویتِ حلقه) | حلقه از نظرِ فنی نتواند بنویسد | ⛔ **فاز ۵** (نیازمندِ پروسهٔ مستقل) |

## ۳. GENOME-LOCK — مبنای تأییدشده (تک‌منبعِ «چه چیزی مجاز است»)
یک فایلِ `learning-engine/GENOME-LOCK.json` که هَشِ **تأییدشدهٔ** هر فایلِ ژنوم را نگه می‌دارد. **فقط مالک** به‌روزش می‌کند = خودِ عملِ تأیید.
```json
{
  "updated": "2026-07-06",
  "owner_verdict": "قفلِ اولیهٔ ژنوم — آری",
  "files": {
    "architect/ARCHITECT_CHARTER.md":            {"sha256": "<هَش>", "verdict_ref": "charter LIFTED 2026-07-06"},
    "learning-engine/LEARNING-CONTRACT.yaml":     {"sha256": "<هَش>", "verdict_ref": "verdict #۵"},
    "learning-engine/MUTATION-WHITELIST.md":      {"sha256": "<هَش>", "verdict_ref": "verdict 2026-07-06"},
    "learning-engine/ENGINE-PROMPT.md":           {"sha256": "<هَش>", "verdict_ref": "draft-v1"}
  }
}
```
> منطق: اگر هَشِ فایل = هَشِ قفل → تأییدشده (چون مالک قفل را به‌روز کرده). اگر ≠ → تغییرِ بدونِ‌تأیید → CRITICAL. GENOME-LOCK خودش genome-tier و owner-only است.

## ۴. genome_guard.py (قطعی · zero-LLM · Windows-side)
```python
#!/usr/bin/env python3
# genome_guard.py — گاردِ یکپارچگیِ ژنوم (قطعی، بدونِ LLM، بدونِ نوشتن).
# Windows-side اجرا شود: بایت‌های اوراکل آن‌جاست → FP نوعِ FUSE stale-view رخ نمی‌دهد (row-36/47).
import hashlib, json, sys, pathlib, datetime, argparse, os

VAULT = pathlib.Path(os.environ.get("VAULT_ROOT", r"F:\backup\04 - Architect System"))  # قابلِ override برای تست/حمل
LOCK  = VAULT / "learning-engine" / "GENOME-LOCK.json"
GENOME = [
    "architect/ARCHITECT_CHARTER.md",
    "learning-engine/LEARNING-CONTRACT.yaml",
    "learning-engine/MUTATION-WHITELIST.md",
    "learning-engine/ENGINE-PROMPT.md",
]

def sha256(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def do_init(verdict):
    files = {rel: {"sha256": sha256(VAULT/rel), "verdict_ref": verdict} for rel in GENOME}
    LOCK.write_text(json.dumps(
        {"updated": datetime.date.today().isoformat(), "owner_verdict": verdict, "files": files},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"GENOME-LOCK نوشته شد ({len(files)} فایل). این کارِ فقط-مالک است.")

def do_check():
    if not LOCK.exists():
        print(json.dumps({"error": "no GENOME-LOCK — اول --init"})); sys.exit(2)
    try:
        lock = json.loads(LOCK.read_text(encoding="utf-8")).get("files", {})
    except Exception as e:                       # قفلِ خراب = مشکوک، نه سالم
        print(json.dumps({"error": f"lock-unreadable: {e}"})); sys.exit(2)
    findings = []
    for rel in GENOME:
        p = VAULT / rel
        if not p.exists():
            findings.append({"file": rel, "severity": "CRITICAL", "kind": "genome-missing"}); continue
        cur, rec = sha256(p), lock.get(rel)
        if rec is None:
            findings.append({"file": rel, "severity": "CRITICAL", "kind": "genome-unlocked"})
        elif cur != rec["sha256"]:
            findings.append({"file": rel, "severity": "CRITICAL", "kind": "genome-unapproved-change",
                             "expected": rec["sha256"][:12], "got": cur[:12]})
    out = {"generated": datetime.date.today().isoformat(),
           "genome_ok": not findings, "findings": findings}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if not findings else 1)   # exit=1 → GOVERNOR تشدید می‌کند

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", metavar="VERDICT", help="ثبتِ مبنای تأییدشده (فقط مالک)")
    a = ap.parse_args()
    do_init(a.init) if a.init else do_check()
```

## ۵. اتصال به دکتر و GOVERNOR
- GOVERNOR (فاز ۲ §۱.۲) هر تیک `genome_guard.py` را اجرا می‌کند؛ `exit=1` یا هر finding با kind=`genome-unapproved-change` → **تشدیدِ فوریِ تلگرام** + گیتِ نمره.
- `dashboard_doctor.py` می‌تواند خروجیِ JSON گارد را به `findings[]` خودش merge کند (هم‌قالب: severity/kind) — بدونِ شکستنِ سه مصرف‌کنندهٔ فعلی (backward-compatible).

## ۶. read-only سبک + workflowِ ویرایشِ مجازِ مالک
```powershell
# قفلِ سبک (ویرایشِ تصادفیِ ایجنت/اسکریپت را سخت می‌کند)
attrib +R "F:\backup\04 - Architect System\architect\ARCHITECT_CHARTER.md"
attrib +R "F:\backup\04 - Architect System\learning-engine\LEARNING-CONTRACT.yaml"
attrib +R "F:\backup\04 - Architect System\learning-engine\MUTATION-WHITELIST.md"
attrib +R "F:\backup\04 - Architect System\learning-engine\ENGINE-PROMPT.md"
```
**برای تغییرِ قانونیِ ژنوم (فقط مالک):** `attrib -R` → ویرایش → `python genome_guard.py --init "verdict: <چه‌چیز>"` (قفل را به‌روز کن) → `attrib +R`. سه مرحله = عمداً کند و آگاهانه (همان روحِ «کلید دوم» سبکِ D5).

## ۷. چرا Windows-side (نه سندباکس)
دکتر از mountِ FUSE گاهی نمای کهنه می‌دهد (DOCTOR-BLUEPRINT row-36/47؛ حتی snapshotِ خودسازگارِ کهنه دیده شد). هَش‌گرفتن باید روی **بایت‌های اوراکل = سمتِ Windows** باشد تا CRITICALِ کاذب رخ ندهد. پس گارد در Task Scheduler سمتِ Windows می‌نشیند (کنارِ BUILD-01).

## ۸. چه چیزی این فاز تغییر می‌دهد
**صفرِ عملیاتی از سمتِ من.** کد و lock این‌جا فقط برای مرورند. ساختِ `GENOME-LOCK.json` = عملِ فقط-مالک؛ گذاشتنِ `genome_guard.py` در `scripts/` = با یک «برو» propose می‌کنم.

## ۹. QA checklist
- [ ] `--init` یک‌بار با verdict اجرا شد؛ `GENOME-LOCK.json` ساخته شد و خودش `attrib +R` شد.
- [ ] تغییرِ آزمایشیِ یک بایت در whitelist → گارد `genome-unapproved-change` می‌دهد (تستِ مثبت).
- [ ] بعد از `--init` دوباره → `genome_ok=true` (تستِ منفی).
- [ ] اجرا از سمتِ Windows، نه سندباکس (بدونِ FP).

## ۱۰. باز مانده و گامِ بعد
- بازِ verdict نیست.
- **قدمِ ۳ نقشه:** GOVERNOR در **shadow** با NSSM (فقط نظارت/گزارش، بی‌اعمال) — که همین گارد را هم مصرف می‌کند.

## ۱۱. ردیفِ ledger پیشنهادی
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | REPORT §۴ قدم۲ + تطبیق D4 | genome_guard.py + GENOME-LOCK + read-only سبک | آماده‌ی اجرای مالک |

---

*propose-only. هیچ ژنوم/کد تغییر نکرد و چیزی نصب/اجرا نشد. ساختِ GENOME-LOCK = عملِ فقط-مالک.*
