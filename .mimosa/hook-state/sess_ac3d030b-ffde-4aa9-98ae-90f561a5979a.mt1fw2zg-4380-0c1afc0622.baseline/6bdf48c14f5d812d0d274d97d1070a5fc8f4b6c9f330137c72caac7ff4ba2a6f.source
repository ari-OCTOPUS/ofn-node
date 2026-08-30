# brain_context.py -- READ-ONLY context from the central vault brain.
# app moghe-e ejra dade-ye maghz-ha ra mikhanad (faghat khandan).
# HICH neveshtani be maghz-e markazi nist -- in fghat read + sanitize ast.
# gate: chon faghat read-only ast va chizi be ledger-e canonical ezafe nemishavad,
#        kharej az Security Gate ast (verdict Ari: "moghe-e ejra bekhanad, dargir nashavim").
from __future__ import annotations
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
VAULT = APP_DIR.parent.parent.parent          # .../backup

# manaba-e read-only (faghat khandan). agar naboodand, skip.
SOURCES = {
    "brain":   VAULT / "01 - Dashboard" / "Brain.md",
    "handoff": VAULT / "01 - Dashboard" / "HANDOFF.md",
    "ledger":  VAULT / "_memory" / "EXPERIENCE-LEDGER.md",
}
SYNTH_DIR = VAULT / "00 - Inbox" / "scout-digests"   # akharin synthesis

# gard-e secret: agar in olgooha dide shod, khat sanitize mishavad (echo nemishavad).
SECRET_PAT = re.compile(
    r"(sk-[A-Za-z0-9]|pplx-[A-Za-z0-9]|xox[bap]-|AKIA[0-9A-Z]|"
    r"-----BEGIN|api[_-]?key\s*[=:]|token\s*[=:]|password\s*[=:]|"
    r"seed\s*[=:]|0x[a-fA-F0-9]{20,}|[48][0-9AB][0-9A-Za-z]{93,104})",  # last = monero-ish
    re.IGNORECASE,
)

def _sanitize(text: str) -> list[str]:
    """faghat khatati ke secret nadarand + kotah. har khat-e mashkook -> [REDACTED]."""
    out = []
    for ln in text.splitlines():
        ln = ln.rstrip()
        if not ln:
            continue
        if SECRET_PAT.search(ln):
            out.append("[REDACTED -- secret pattern]")
        else:
            out.append(ln)
    return out

def _tail(path: Path, n_lines: int) -> list[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    return _sanitize("\n".join(lines[-n_lines:]))

def _latest_synth() -> tuple[str, list[str]]:
    if not SYNTH_DIR.exists():
        return ("", [])
    files = sorted(SYNTH_DIR.glob("*synthesis*.md")) + sorted(SYNTH_DIR.glob("*.md"))
    if not files:
        return ("", [])
    f = max(files, key=lambda p: p.stat().st_mtime)
    return (f.name, _tail(f, 25))

def read_brain(max_lines_each: int = 20) -> dict:
    """
    khorooji: dict-e amn (secret-filtered) baraye estefade dar tasmim-e app.
    hame read-only. agar file naboud, meghdar khali.
    """
    ctx = {}
    ctx["brain_tail"] = _tail(SOURCES["brain"], max_lines_each)
    ctx["ledger_tail"] = _tail(SOURCES["ledger"], max_lines_each)
    ctx["handoff_tail"] = _tail(SOURCES["handoff"], 12)
    sname, stail = _latest_synth()
    ctx["synthesis_name"] = sname
    ctx["synthesis_tail"] = stail
    ctx["available"] = {k: SOURCES[k].exists() for k in SOURCES}
    ctx["available"]["synthesis"] = bool(sname)
    return ctx

def summary_line(ctx: dict) -> str:
    """yek khat baraye chap dar log-e app."""
    a = ctx.get("available", {})
    have = [k for k, v in a.items() if v]
    return "brain-context: read %d src (%s) | synthesis: %s" % (
        len(have), ", ".join(have) or "none", ctx.get("synthesis_name") or "-")

def as_prompt_block(ctx: dict, max_chars: int = 1500) -> str:
    """block-e amn baraye dadan be model (think) -- DATA not instruction."""
    parts = []
    if ctx.get("brain_tail"):
        parts.append("## Brain (live pulse):\n" + "\n".join(ctx["brain_tail"]))
    if ctx.get("synthesis_tail"):
        parts.append("## Latest synthesis (%s):\n" % ctx.get("synthesis_name", "") + "\n".join(ctx["synthesis_tail"]))
    if ctx.get("ledger_tail"):
        parts.append("## Experience ledger (recent):\n" + "\n".join(ctx["ledger_tail"]))
    block = "\n\n".join(parts)
    return block[:max_chars]

if __name__ == "__main__":
    c = read_brain()
    print(summary_line(c))
    print("---")
    print(as_prompt_block(c)[:600])
