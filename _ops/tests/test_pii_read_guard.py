#!/usr/bin/env python3
"""تستِ standalone برای گاردِ read دادهٔ ویژهٔ PII/PHI (audit R-05 + R-15).

گاردِ کد در .claude/hooks/pii_read_guard.py است (خارج از _ops، ولی نسبت به ریشهٔ
repo مسیرِ ثابت دارد و در هر دو درختِ worktree/live در همان مسیر است). این تست
مستقیماً _decide() را لود می‌کند و اثبات می‌کند: هر segment/glob جدید deny می‌شود
و مسیرِ عادیِ vault allow می‌ماند. یک تستِ end-to-end هم main() را می‌سنجد که روی
تطبیق واقعاً JSONِ deny منتشر می‌کند (deny-by-default on match).

اجرا: python -X utf8 test_pii_read_guard.py    (بدونِ pytest، مثلِ بقیهٔ سوئیت)

نکتهٔ همگام‌سازی: .claude/ در .gitignore است؛ اگر این تست روی درختِ live قرمز شد،
یعنی integrator ویرایشِ hook را به live کپی نکرده — همان سیگنالِ fail-closedِ مطلوب.
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GUARD_PATH = os.path.join(ROOT, ".claude", "hooks", "pii_read_guard.py")

_spec = importlib.util.spec_from_file_location("pii_read_guard", GUARD_PATH)
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


class _C:
    failed = 0


def check(name, cond):
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


V = "F:/backup"          # ریشهٔ نمونهٔ vault (مسیرها absolute‌اند، مثلِ ورودیِ واقعیِ Read)
HY = V + "/07 - Knowledge/هیپنوتیزم  و خودآگاهی"   # پوشهٔ هیپنوتیزم (دو فاصله)

# ── DENY: هر segment/glob جدید ─────────────────────────────────────────────
check("partner PII dir denied (segment)",
      G._decide(V + "/08 - Partner (PII)/partner-notes.md") is True)
check("DNA/EEG data dir denied (segment)",
      G._decide(HY + "/Marathon/امواج مغزی/armin_dna.vcf") is True)
check("DNA report PDF denied (MyHeritage glob)",
      G._decide(HY + "/Marathon/GenomeInsight Report — MyHeritage_raw_dna_data.csv.pdf") is True)
check("HRV N-of-1 dir denied (segment)",
      G._decide(HY + "/فیوژن هیپنوتیزم/Neuro-HRV-Nof1/01-master-prompt.md") is True)
check("owner psychotherapeutic profile denied (segment+glob)",
      G._decide(V + "/_ops/state/OWNER-PROFILE.json") is True)

# ── DENY: جابه‌جایی/کپیِ فایلِ ژنتیکی هرجای vault (globِ نام‌فایل) ──────────
check("relocated genetic file denied (armin_dna* glob)",
      G._decide(V + "/00 - Inbox/armin_dna_summary.json") is True)
check("23andme export denied (*23andme* glob)",
      G._decide(V + "/00 - Inbox/armin_dna_23andme_format.txt") is True)
check("relocated profile denied anywhere (OWNER-PROFILE* glob)",
      G._decide(V + "/00 - Inbox/OWNER-PROFILE.json") is True)
# audit R-ACCT: bank statement moved out of /Statements/ for processing stays denied
check("relocated ANZ bank statement denied (*ANZ-BE* glob)",
      G._decide(V + "/00 - Inbox/ANZ-BE_stmt04_2024-03-20.pdf") is True)
check("in-place ANZ statement denied (/statements/ segment)",
      G._decide(V + "/03 - Projects/Accounting/Accounting/finance/"
                    "Statements/ANZ-BE-XXXXXXXXX/ANZ-BE_stmt04.pdf") is True)

# ── ALLOW: مسیرِ عادیِ vault ───────────────────────────────────────────────
check("normal dashboard note allowed",
      G._decide(V + "/01 - Dashboard/HANDOFF.md") is False)
check("normal knowledge note allowed",
      G._decide(V + "/07 - Knowledge/SHADOW-THEORY-5principles-v1.md") is False)
# رگرسیون: 'genome-system' یک استعارهٔ کد است نه DNA — نباید over-block شود
check("organism genome-system NOT over-blocked (no *genome* glob)",
      G._decide(V + "/07 - Knowledge/genome-system.md") is False)

# ── رگرسیون: لایه‌های موجود دست‌نخورده ─────────────────────────────────────
check("existing secret glob still denied (wallet)",
      G._decide(V + "/03 - Projects/Mining/monero wallet.txt") is True)
check("existing finance segment still denied (accounting/data)",
      G._decide(V + "/03 - Projects/Accounting/data/ledger.xlsx") is True)

# ── end-to-end: main() روی تطبیق JSONِ deny منتشر می‌کند (fail-closed) ──────
def _run_main(payload):
    old_in, old_out = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(json.dumps(payload))
    sys.stdout = io.StringIO()
    try:
        G.main()
        return sys.stdout.getvalue()
    finally:
        sys.stdin, sys.stdout = old_in, old_out


_out = _run_main({"tool_name": "Read",
                  "tool_input": {"file_path": V + "/_ops/state/OWNER-PROFILE.json"}})
try:
    _dec = json.loads(_out)["hookSpecificOutput"]["permissionDecision"]
except Exception:
    _dec = None
check("main() emits deny JSON on PII match", _dec == "deny")

_out2 = _run_main({"tool_name": "Read",
                   "tool_input": {"file_path": V + "/01 - Dashboard/HANDOFF.md"}})
check("main() stays silent on normal path (allowed)", _out2.strip() == "")

print("\n== %d failure(s) ==" % _C.failed)
sys.exit(1 if _C.failed else 0)
