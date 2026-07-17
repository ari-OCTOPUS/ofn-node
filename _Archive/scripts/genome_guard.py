#!/usr/bin/env python3
"""
genome_guard.py — گاردِ یکپارچگیِ ژنوم (قطعی، بدونِ LLM، بدونِ نوشتن).
هر تغییرِ فایل‌های ژنوم که با GENOME-LOCK (مبنای تأییدشدهٔ مالک) نخواند = CRITICAL.
Windows-side اجرا شود (بایتِ اوراکل آن‌جاست → FP نوعِ FUSE stale-view رخ نمی‌دهد؛ درسِ row-36/47).
تست‌شده در سندباکس: init / ok / tamper(exit=1) / restore.
مبنا: تطبیق D4 (DEEP-GAP شکاف ۸). status: propose.
  استفاده:  python genome_guard.py --init "verdict: <چه‌چیز>"   (فقط مالک — مبنا را ثبت می‌کند)
            python genome_guard.py                              (چک؛ exit 0=ok, 1=مغایرت, 2=خطا)
"""
import hashlib, json, sys, pathlib, datetime, argparse, os

VAULT = pathlib.Path(os.environ.get("VAULT_ROOT", r"F:\backup\04 - Architect System"))  # قابلِ override
LOCK  = VAULT / "learning-engine" / "GENOME-LOCK.json"
GENOME = [
    "architect/ARCHITECT_CHARTER.md",
    "learning-engine/LEARNING-CONTRACT.yaml",
    "learning-engine/MUTATION-WHITELIST.md",
    "learning-engine/ENGINE-PROMPT.md",
    # (آینده) "learning-engine/EVOLUTIONARY-DOCTOR-RUBRIC.md",
]


def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def do_init(verdict):
    files = {rel: {"sha256": sha256(VAULT / rel), "verdict_ref": verdict} for rel in GENOME}
    LOCK.parent.mkdir(parents=True, exist_ok=True)
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
                             "got": cur[:12]})
    print(json.dumps({"generated": datetime.date.today().isoformat(),
                      "genome_ok": not findings, "findings": findings}, ensure_ascii=False))
    sys.exit(0 if not findings else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", metavar="VERDICT", help="ثبتِ مبنای تأییدشده (فقط مالک)")
    a = ap.parse_args()
    do_init(a.init) if a.init else do_check()
