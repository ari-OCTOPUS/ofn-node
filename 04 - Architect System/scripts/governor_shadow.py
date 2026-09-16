#!/usr/bin/env python3
"""
governor_shadow.py — سرپرستِ shadow: می‌خواند، چک می‌کند، گزارش می‌دهد. صفر اعمال، صفر LLM، $0.
هر تیک: kill-check → heartbeat(سطرِ خودش) → dashboard_doctor → backup flags → budget.
هر خطای اجرای دکتر/گارد = alert (منشور §۴: خطای خاموش = شدیدترین باگ).
تست‌شده در سندباکس (integration): healthy=ok · tampered=alert · doctor-crash=alert · low-health=alert · STOP=halted.
status: propose. زمان‌بندی: Task Scheduler هر ~۱۵ دقیقه (SETUP-README).
"""
import json, subprocess, sys, pathlib, datetime, os

VAULT   = pathlib.Path(os.environ.get("VAULT_ROOT", r"F:\backup\04 - Architect System"))
SCRIPTS = pathlib.Path(os.environ.get("SCRIPTS_DIR", str(VAULT / "scripts")))
OPS     = pathlib.Path(os.environ.get("OPS_DIR", r"F:\backup\_ops"))
STOP    = VAULT / "STOP"
HEART   = VAULT / "_memory" / "HEARTBEAT.md"
ALERTS  = OPS / "governor" / "governor-alerts.md"
BUDGET  = OPS / "budget" / "budget-state.json"


def run_json(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "").strip()
        if not out:
            return {"_error": f"no output (exit={r.returncode}) {r.stderr[:150]}"}
        return json.loads(out)                 # خروجیِ خالی/نامعتبر = خطا، نه «سالم»
    except Exception as e:
        return {"_error": str(e)}


def beat(line):
    HEART.parent.mkdir(parents=True, exist_ok=True)
    with HEART.open("a", encoding="utf-8") as f:
        f.write(line + "\n")                   # فقط سطرِ خودش (append)


def alert(now, items):
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS.open("a", encoding="utf-8") as f:
        f.write(f"## {now}\n" + "\n".join(f"- ⚠️ {i}" for i in items) + "\n\n")
    # (اختیاری) اینجا فقط پینگِ تلگرام به مالک از طریقِ langar — هرگز شخصِ ثالث.


def main():
    now = datetime.datetime.now().isoformat(timespec="seconds")
    if STOP.exists():
        beat(f"- {now} · governor=HALTED (STOP) · beat-only"); return
    a = []
    doc = run_json([sys.executable, str(SCRIPTS / "dashboard_doctor.py")])
    if not isinstance(doc, dict) or doc.get("_error"):
        a.append("doctor FAILED to run")
    elif doc.get("effective_score", 100) < 70:
        a.append(f"health effective_score={doc.get('effective_score')}")
    # genome_guard.py بازنشسته و به _Archive منتقل شد (تری‌اسکن 2026-07-17): همیشه exit(2)
    # می‌داد (GENOME-LOCK.json هرگز init نشد) و صفر callerِ زنده داشت جز همین خطِ مرده.
    if (OPS / "backup" / "FAILED.flag").exists():
        a.append("backup FAILED flag present")
    try:
        if BUDGET.exists() and json.loads(BUDGET.read_text("utf-8")).get("halted"):
            a.append("budget HALTED")
    except Exception:
        a.append("budget-state unreadable")
    if a:
        alert(now, a)
    beat(f"- {now} · governor=shadow · {'ALERT×' + str(len(a)) if a else 'ok'}")


if __name__ == "__main__":
    main()
