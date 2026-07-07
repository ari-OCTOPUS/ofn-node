#!/usr/bin/env python3
# bridge_to_ledger.py -- PHASE 3 (verdict Ari): app proposals/ -> central brain.
# GARD-ha (agreed framework file/reason/risk/test):
#   - KHOROOJI KHAM-e model HARGEZ mostaghim vared-e EXPERIENCE-LEDGER-e canonical nemishavad.
#   - har proposal aval secret-scan mishavad; agar olgoo-ye secret did -> quarantine + skip.
#   - faghat "dars-e sanitize-shode-ye kotah" estekhraj va be STAGING neveshte mishavad:
#       00 - Inbox/build-proposals/_LEDGER-INBOX.md  (propose-only, montazer-e verdict Ari)
#   - enteghal-e nahayi az staging be EXPERIENCE-LEDGER-e canonical DASTI/taamoli ast (in script namikonad).
#   - agar file STOP bood -> foori khoorooj.
#
# Run:
#   python bridge_to_ledger.py --scan          # scan proposals, write sanitized digest to staging
#   python bridge_to_ledger.py --scan --one    # faghat avalin proposal (sample verdict)
#   python bridge_to_ledger.py --status
from __future__ import annotations
import argparse, re, datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
VAULT = APP_DIR.parent.parent.parent
PROPOSALS = APP_DIR / "proposals"
STAGING = VAULT / "00 - Inbox" / "build-proposals" / "_LEDGER-INBOX.md"
QUARANTINE = APP_DIR / "proposals_quarantine"
PROCESSED = APP_DIR / "bridge_processed.txt"   # esm-e proposal-haye pardazesh-shode (idempotent)
STOP_FILES = [VAULT / "STOP", APP_DIR / "STOP"]

# gard-e secret -- har khat ba in olgoo -> proposal quarantine mishavad, be staging nemiravad.
SECRET_PAT = re.compile(
    r"(sk-[A-Za-z0-9]{8}|pplx-[A-Za-z0-9]{8}|xox[bap]-|AKIA[0-9A-Z]{10}|"
    r"-----BEGIN|ghp_[A-Za-z0-9]{20}|api[_-]?key\s*[=:]\s*\S|"
    r"token\s*[=:]\s*\S|password\s*[=:]\s*\S|seed\s*[=:]\s*\S|"
    r"0x[a-fA-F0-9]{20,}|[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93,104})",
    re.IGNORECASE,
)


def stop_requested():
    return any(p.exists() for p in STOP_FILES)

def load_processed():
    if PROCESSED.exists():
        return set(PROCESSED.read_text(encoding="utf-8").split("\n"))
    return set()

def mark_processed(name):
    with PROCESSED.open("a", encoding="utf-8") as f:
        f.write(name + "\n")

def extract_lesson(text):
    """faghat dars-e kotah ra bar migardanad -- NE khorooji khaam-e model.
    dars = mohtava-ye zir-e '## Brain #1' ta section-e baadi, kotah-shode."""
    lines = text.splitlines()
    lesson = []
    topic = ""
    grab = False
    for ln in lines:
        if ln.startswith("- topic:"):
            topic = ln.split("topic:", 1)[1].strip()
        if ln.startswith("## Brain #1"):
            grab = True
            continue
        if grab:
            if ln.startswith("## "):   # section baadi
                break
            if ln.strip():
                lesson.append(ln.strip())
    # kotah: max 2 khat
    return topic, " ".join(lesson)[:280]

def scan(one=False):
    if stop_requested():
        print("STOP detected -- halting."); return
    if not PROPOSALS.exists():
        print("no proposals dir."); return
    STAGING.parent.mkdir(parents=True, exist_ok=True)
    QUARANTINE.mkdir(exist_ok=True)
    done = load_processed()
    files = sorted(PROPOSALS.glob("*.md"))
    new = [f for f in files if f.name not in done]
    if one:
        new = new[:1]
    if not new:
        print("no new proposals to bridge."); return

    # header-e staging agar nabood
    if not STAGING.exists():
        STAGING.write_text(
            "---\ntype: report\nstatus: inbox\ntags: [learning-engine, bridge, ledger-inbox]\n"
            "created: %s\nupdated: %s\n---\n\n"
            "# LEDGER-INBOX -- staging-e pol-e app -> maghz (PHASE 3, propose-only)\n\n"
            "> har radif dars-e sanitize-shode az proposals/ app-e mahalli ast. "
            "secret-scan pass shode. **enteghal be EXPERIENCE-LEDGER-e canonical = faghat verdict Ari (dasti).**\n\n"
            "| tarikh | topic | dars (sanitized) | manba | verdict Ari |\n"
            "|---|---|---|---|---|\n" % (
                datetime.date.today().isoformat(), datetime.date.today().isoformat()),
            encoding="utf-8")

    added = quarantined = 0
    rows = []
    for f in new:
        txt = f.read_text(encoding="utf-8", errors="replace")
        if SECRET_PAT.search(txt):
            # quarantine -- move (copy + mark; hazf nemikonim, faghat mark)
            (QUARANTINE / f.name).write_text(txt, encoding="utf-8")
            mark_processed(f.name)
            quarantined += 1
            print("QUARANTINE (secret pattern): " + f.name)
            continue
        topic, lesson = extract_lesson(txt)
        if not lesson:
            mark_processed(f.name)
            continue
        # double-check: lesson-e estekhraj-shode ham secret nadashte bashad
        if SECRET_PAT.search(lesson):
            (QUARANTINE / f.name).write_text(txt, encoding="utf-8")
            mark_processed(f.name); quarantined += 1
            print("QUARANTINE (secret in lesson): " + f.name); continue
        row = "| %s | %s | %s | %s | (pending) |" % (
            datetime.date.today().isoformat(), topic[:40], lesson.replace("|", "/"), f.name)
        rows.append(row)
        mark_processed(f.name)
        added += 1

    if rows:
        with STAGING.open("a", encoding="utf-8") as sf:
            sf.write("\n".join(rows) + "\n")
    print("bridged: %d sanitized rows -> staging | quarantined: %d" % (added, quarantined))
    print("staging: 00 - Inbox/build-proposals/_LEDGER-INBOX.md")
    print("NOTE: enteghal be EXPERIENCE-LEDGER-e canonical = verdict Ari (dasti).")

def status():
    done = load_processed()
    q = len(list(QUARANTINE.glob("*.md"))) if QUARANTINE.exists() else 0
    n = len(list(PROPOSALS.glob("*.md"))) if PROPOSALS.exists() else 0
    print("-- bridge status --")
    print("proposals total: %d | processed: %d | quarantined: %d" % (n, len(done) - 1 if done else 0, q))
    print("staging exists: %s" % STAGING.exists())

def main():
    ap = argparse.ArgumentParser(description="bridge_to_ledger -- phase3 propose-only")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--one", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.status:
        status(); return
    if a.scan:
        scan(one=a.one); return
    ap.print_help()

if __name__ == "__main__":
    main()
