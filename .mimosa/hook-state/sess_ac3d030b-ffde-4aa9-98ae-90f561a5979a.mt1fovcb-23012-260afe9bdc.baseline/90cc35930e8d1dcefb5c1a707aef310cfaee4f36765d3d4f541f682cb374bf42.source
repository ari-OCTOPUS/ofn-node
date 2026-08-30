#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vault_scanner.py — Standalone read-only inventory scanner for F:\\backup.

WHAT IT DOES
  Walks the vault, tags every top-level entry by category, detects messiness
  and risk, and produces:
    1. vault-inventory.json   (structured registry)
    2. vault-report.md        (human-readable report)
    3. a Telegram summary     (green/yellow/red model)

SAFETY GUARANTEES — this script will NEVER:
  - delete a file or folder   (no os.remove / os.rmdir / shutil.rmtree)
  - move or rename anything    (no os.rename / shutil.move)
  - copy anything              (no shutil.copy)
  - open any vault file in write mode (no open(...,'w'/'a'/'wb') on vault paths)
  The ONLY writes are the two output files on the Desktop, and only when not
  running with --dry-run.

  This file does not import shutil at all. Verify yourself:
      grep -nE "shutil|os\\.remove|os\\.rename|os\\.rmdir|'w'|'a'|'wb'" vault_scanner.py
  (You will only find 'w' used for DESKTOP output files, never on vault paths.)

USAGE
  python vault_scanner.py                # full scan + write reports + send Telegram
  python vault_scanner.py --dry-run      # scan only, print, write/send NOTHING
  python vault_scanner.py --no-telegram  # scan + write reports, skip Telegram
  python vault_scanner.py --scope "03 - Projects"  # narrow to one subtree
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone
from collections import defaultdict

# --------------------------------------------------------------------------- #
#  HARDCODED CONSTANTS — edit here only
# --------------------------------------------------------------------------- #
ROOT       = r"F:\backup"
DESKTOP    = os.path.join(os.path.expanduser("~"), "Desktop")
ENV_FILE   = os.path.join(ROOT, ".env")
READ_ONLY  = True   # hard guard; assert-checked at runtime
MAX_DEPTH  = 3      # how deep to walk per subtree
CLUTTER_THRESHOLD      = 40   # loose files above this => "cluttered"
EMPTY_STUB_THRESHOLD   = 3    # entries below this => "empty stub"
ACTIVE_DAYS   = 7             # modified within => "active"
DORMANT_DAYS  = 90            # untouched beyond => "dormant"
TELEGRAM_MAX  = 4096          # Telegram message char cap

# Folders that are pure noise — never descend into them
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "site-packages", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
# File prefixes to skip (per-entry, not content)
SKIP_FILE_PREFIXES = (".DS_Store", "Thumbs.db")

# Keyword -> risk reason (HIGH risk). Lowercased matched against path+name.
HIGH_RISK_KEYWORDS = {
    "account":   "financial / accounting data",
    "tax":       "tax records",
    "crypto":    "crypto / trading data",
    "wallet":    "wallet / keys",
    "mining":    "mining operations",
    "onlyfans":  "personal monetization content",
    "اونلی فنز": "personal monetization content",
    ".env":      "secrets / credentials file",
    "secret":    "secrets",
    "token":     "tokens / credentials",
    "password":  "passwords",
    "private":   "private keys / data",
    "ledger":    "financial ledger",
}

# Folder-name (lowercased) -> category tag
CATEGORY_RULES = [
    ("00 - inbox",        "inbox"),
    ("01 - dashboard",    "dashboard"),
    ("02 - life os",      "life-os"),
    ("03 - projects",     "projects-root"),
    ("04 - architect",    "architect"),
    ("05 - agents",       "agents"),
    ("06 - architecture", "architecture"),
    ("07 - knowledge",    "knowledge"),
    ("08 - assets",       "assets"),
    ("09 - people",       "people"),
    ("10 - telegram",     "telegram-processing"),
    ("_ops",              "ops-organism"),
    ("_code",             "code-legacy"),
    ("_launchpad",        "launchpad"),
    ("_memory",           "memory"),
    ("_archive",          "archive"),
    ("_templates",        "templates"),
    ("_duplicates",       "duplicates"),
    ("chronos-fable-os",  "system-project"),
    ("survival-gateway",  "infrastructure"),
    (".obsidian",         "config"),
    (".claude",           "config"),
    (".zcode",            "config"),
]

# Project subfolder categories (under 03 - Projects)
PROJECT_KEYWORDS = {
    "accounting":  "finance",
    "crypto":      "crypto",
    "mining":      "mining",
    "lead":        "lead-gen",
    "نقاشی":       "lead-gen",
    "ziman":       "web-platform",
    "گالری":       "web-platform",
    "اونلی فنز":   "content-monetization",
    "onlyfans":    "content-monetization",
}


# --------------------------------------------------------------------------- #
#  SAFETY GUARD
# --------------------------------------------------------------------------- #
def assert_read_only():
    """Fail hard if someone disabled the READ_ONLY flag."""
    assert READ_ONLY, "READ_ONLY must be True. Refusing to run."
    # Forbidden modules — we never import shutil anywhere; assert it's absent
    # from sys.modules to catch accidental injection.
    if "shutil" in sys.modules:
        # shutil may be imported transitively by stdlib; that's fine as long
        # as WE never call its destructive functions. We just don't use it.
        pass


# --------------------------------------------------------------------------- #
#  HELPERS
# --------------------------------------------------------------------------- #
def safe_mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def safe_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def age_days(mtime, now):
    if mtime <= 0:
        return None
    return (now - mtime) / 86400.0


def activity_label(days):
    if days is None:
        return "unknown"
    if days <= ACTIVE_DAYS:
        return "active"
    if days >= DORMANT_DAYS:
        return "dormant"
    return "normal"


def ext_of(name):
    _, ext = os.path.splitext(name)
    return ext.lower().lstrip(".") or "(none)"


def category_for(rel_path, name):
    low = name.lower()
    # top-level rules
    for needle, cat in CATEGORY_RULES:
        if low == needle or low.startswith(needle):
            return cat
    # project subfolder detection
    parts = rel_path.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0].lower().startswith("03 - projects"):
        combined = low
        for kw, cat in PROJECT_KEYWORDS.items():
            if kw in combined:
                return cat
        return "project-other"
    return "other"


def risk_for(rel_path, name):
    """Return (tier, reason) or (None, None)."""
    hay = (rel_path + "/" + name).lower()
    for kw, reason in HIGH_RISK_KEYWORDS.items():
        if kw in hay:
            return ("high", reason)
    return (None, None)


def should_skip_dir(name):
    return name in SKIP_DIRS


# --------------------------------------------------------------------------- #
#  CORE SCAN
# --------------------------------------------------------------------------- #
def scan_subtree(root_abs, max_depth):
    """
    Walk one subtree up to max_depth, collecting stats.
    Returns (top_entries, all_dirs_seen) where top_entries is a list of dicts.
    """
    now = time.time()
    top_entries = []

    try:
        children = sorted(os.listdir(root_abs))
    except OSError as e:
        return [{"name": os.path.basename(root_abs), "error": str(e)}]

    for child in children:
        if child.startswith(SKIP_FILE_PREFIXES):
            continue
        child_path = os.path.join(root_abs, child)
        rel = os.path.relpath(child_path, ROOT)

        is_dir = os.path.isdir(child_path)
        cat = category_for(rel, child)
        risk_tier, risk_reason = risk_for(rel, child)

        mtime = safe_mtime(child_path)
        days = age_days(mtime, now)

        entry = {
            "name": child,
            "path": child_path,
            "rel": rel,
            "type": "dir" if is_dir else "file",
            "category": cat,
            "mtime": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
                      if mtime > 0 else None,
            "age_days": round(days, 1) if days is not None else None,
            "activity": activity_label(days),
            "risk_tier": risk_tier or "low",
            "risk_reason": risk_reason,
        }

        if is_dir:
            d = gather_dir(child_path, max_depth - 1, now)
            entry.update(d)
            entry["issues"] = detect_issues_dir(entry)
        else:
            entry["size_bytes"] = safe_size(child_path)
            entry["ext"] = ext_of(child)
            entry["issues"] = detect_issues_file(child, entry)

        top_entries.append(entry)

    return top_entries


def gather_dir(dir_abs, depth_remaining, now):
    """Recursively gather size, counts, file-type breakdown for a directory."""
    result = {
        "total_size_bytes": 0,
        "file_count": 0,
        "dir_count": 0,
        "loose_file_count": 0,   # files directly in THIS dir
        "ext_breakdown": defaultdict(int),
        "child_dirs": [],        # names of immediate subdirs
        "newest_mtime": 0.0,
        "max_depth_seen": 0,
    }
    if depth_remaining < 0:
        result["truncated"] = True
        return result

    try:
        entries = os.listdir(dir_abs)
    except OSError:
        result["access_error"] = True
        return result

    for name in entries:
        if name.startswith(SKIP_FILE_PREFIXES):
            continue
        p = os.path.join(dir_abs, name)
        if os.path.isdir(p):
            if should_skip_dir(name):
                continue
            result["dir_count"] += 1
            result["child_dirs"].append(name)
            sub = gather_dir(p, depth_remaining - 1, now)
            result["total_size_bytes"] += sub["total_size_bytes"]
            result["file_count"] += sub["file_count"]
            result["dir_count"] += sub["dir_count"]
            result["newest_mtime"] = max(result["newest_mtime"], sub["newest_mtime"])
            result["max_depth_seen"] = max(result["max_depth_seen"],
                                           (sub.get("max_depth_seen", 0) + 1))
        else:
            sz = safe_size(p)
            mt = safe_mtime(p)
            result["file_count"] += 1
            result["loose_file_count"] += 1
            result["total_size_bytes"] += sz
            result["newest_mtime"] = max(result["newest_mtime"], mt)
            result["ext_breakdown"][ext_of(name)] += 1

    result["ext_breakdown"] = dict(sorted(result["ext_breakdown"].items()))
    return result


def detect_issues_dir(entry):
    issues = []
    if entry.get("loose_file_count", 0) > CLUTTER_THRESHOLD:
        issues.append(f"cluttered ({entry['loose_file_count']} loose files)")
    total = entry.get("file_count", 0) + entry.get("dir_count", 0)
    if 0 < total < EMPTY_STUB_THRESHOLD:
        issues.append(f"empty stub ({total} items)")
    if entry.get("activity") == "dormant":
        issues.append("dormant (untouched >90d)")
    return issues


def detect_issues_file(name, entry):
    issues = []
    low = name.lower()
    if low.startswith("untitled"):
        issues.append("unnamed/generic (Untitled)")
    ext = entry.get("ext", "")
    if ext == "(none)":
        issues.append("no file extension")
    return issues


# --------------------------------------------------------------------------- #
#  ROOT-LEVEL CLUTTER + SPECIAL CHECKS
# --------------------------------------------------------------------------- #
def root_loose_files(top_entries):
    return [e for e in top_entries if e["type"] == "file"]


def stale_duplicate_check(top_entries):
    """Flag _code/ subfolders that mirror 03 - Projects/ names."""
    projects = {e["name"].lower() for e in top_entries
                if e.get("category") == "projects-root"}
    code_entry = next((e for e in top_entries if e.get("category") == "code-legacy"), None)
    if not code_entry:
        return []
    mirrored = []
    for child in code_entry.get("child_dirs", []):
        if child.lower() in projects:
            mirrored.append(child)
    return mirrored


def organism_health_peek(top_entries):
    """Read-only peek at _ops health from outside — governor alerts + state."""
    ops = next((e for e in top_entries if e.get("category") == "ops-organism"), None)
    if not ops:
        return None
    findings = {"governor_alert_errors": 0, "recent_errors": []}
    alerts_path = os.path.join(ops["path"], "governor", "governor-alerts.md")
    if os.path.isfile(alerts_path):
        try:
            with open(alerts_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            err_lines = [ln.strip() for ln in lines
                         if any(w in ln.lower() for w in
                                ("error", "fail", "traceback", "crash", "halt"))]
            findings["governor_alert_errors"] = len(err_lines)
            findings["recent_errors"] = err_lines[-5:]
        except OSError:
            pass
    return findings


# --------------------------------------------------------------------------- #
#  REPORT BUILDERS
# --------------------------------------------------------------------------- #
def human_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def build_inventory(top_entries, health, stale_dupes, root_loose):
    return {
        "schema": "vault-inventory/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": ROOT,
        "read_only": READ_ONLY,
        "summary": summarize(top_entries),
        "top_level": [
            {
                "name": e["name"],
                "category": e["category"],
                "type": e["type"],
                "purpose_guess": purpose_guess(e),
                "inputs": "filesystem (read-only)",
                "outputs": "vault content / state",
                "connections": guess_connections(e),
                "risk_tier": e.get("risk_tier", "low"),
                "risk_reason": e.get("risk_reason"),
                "activity": e.get("activity"),
                "file_count": e.get("file_count"),
                "dir_count": e.get("dir_count"),
                "size_human": human_size(e["total_size_bytes"]) if e.get("total_size_bytes") else None,
                "issues": e.get("issues", []),
            } for e in top_entries
        ],
        "root_loose_files": [e["name"] for e in root_loose],
        "stale_duplicate_mirrors": stale_dupes,
        "organism_health": health,
    }


def purpose_guess(e):
    cat = e["category"]
    table = {
        "inbox": "Holding pen for unsorted incoming notes/prompts",
        "dashboard": "Dashboards, control panels, handoff logs",
        "life-os": "Life OS / weekly review",
        "projects-root": "Container for all active projects",
        "finance": "Accounting / financial / tax data",
        "crypto": "Crypto trading portfolio data",
        "mining": "Mining hardware / operations",
        "lead-gen": "Lead generation (painting business)",
        "web-platform": "Ziman Gallery web platform",
        "content-monetization": "OnlyFans content / monetization",
        "project-other": "Project (unclassified)",
        "architect": "Architect system specs/proposals/audits",
        "agents": "Agent registry / definitions",
        "architecture": "Architecture maps, ADRs, specs",
        "knowledge": "Knowledge base / research notes",
        "assets": "Media / photos / mining assets",
        "people": "People index",
        "telegram-processing": "Telegram routing / processing",
        "ops-organism": "Octopus autonomous agent organism (Python)",
        "code-legacy": "Older code mirror of projects",
        "launchpad": "Live pipeline / launchpad for bots",
        "memory": "Persistent agent memory / heartbeats",
        "archive": "Archive / old logs",
        "templates": "Obsidian templates",
        "duplicates": "Duplicate detection results / broken git",
        "system-project": "CHRONOS-FABLE-OS sub-project",
        "infrastructure": "Docker / LiteLLM gateway",
        "config": "Tool config (.obsidian / .claude / .zcode)",
        "other": "Unclassified",
    }
    return table.get(cat, "Unclassified")


def guess_connections(e):
    cat = e["category"]
    if cat == "ops-organism":
        return "_memory/, _ops/state/, _ops/governor/, Telegram bot, LLM APIs"
    if cat == "memory":
        return "_ops/ (organism heartbeat)"
    if cat == "code-legacy":
        return "mirrors 03 - Projects/ (possible stale copy)"
    if cat == "launchpad":
        return "_ops/, 03 - Projects/"
    if cat in ("finance", "crypto", "mining", "content-monetization"):
        return "Telegram reporting, _ops/ budget organ"
    return "—"


def summarize(top_entries):
    total_files = sum(e.get("file_count", 0) for e in top_entries if e["type"] == "dir")
    total_size = sum(e.get("total_size_bytes", 0) for e in top_entries if e["type"] == "dir")
    high_risk = [e["name"] for e in top_entries if e.get("risk_tier") == "high"]
    cluttered = [e["name"] for e in top_entries
                 if e["type"] == "dir" and any("cluttered" in i for i in e.get("issues", []))]
    empty_stubs = [e["name"] for e in top_entries
                   if e["type"] == "dir" and any("empty stub" in i for i in e.get("issues", []))]
    dormant = [e["name"] for e in top_entries
               if e["type"] == "dir" and any("dormant" in i for i in e.get("issues", []))]
    active = [e["name"] for e in top_entries if e.get("activity") == "active"]
    return {
        "top_level_count": len(top_entries),
        "total_files_seen": total_files,
        "total_size_human": human_size(total_size),
        "high_risk_areas": high_risk,
        "cluttered_areas": cluttered,
        "empty_stubs": empty_stubs,
        "dormant_areas": dormant,
        "active_areas": active,
    }


def build_markdown_report(inv):
    s = inv["summary"]
    L = []
    L.append("# F:\\backup — Vault Inventory Report")
    L.append("")
    L.append(f"_Generated:_ {inv['generated_at']}  ")
    L.append(f"_Root:_ `{inv['root']}`  ")
    L.append(f"_Mode:_ **READ-ONLY** (no file was moved, renamed, deleted, or modified)")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- **Top-level entries:** {s['top_level_count']}")
    L.append(f"- **Total files seen:** {s['total_files_seen']}")
    L.append(f"- **Total size:** {s['total_size_human']}")
    L.append(f"- **Active areas (≤7d):** {', '.join(s['active_areas']) or '—'}")
    L.append(f"- **Dormant areas (>90d):** {', '.join(s['dormant_areas']) or '—'}")
    L.append("")
    L.append("## 🔴 High-Risk Areas")
    L.append("")
    if s["high_risk_areas"]:
        for e in inv["top_level"]:
            if e["risk_tier"] == "high":
                L.append(f"- **{e['name']}** — {e['risk_reason']}  ")
                L.append(f"  _Purpose:_ {e['purpose_guess']}  ")
                L.append(f"  _Action:_ 🟤 ASK OWNER before any change.")
    else:
        L.append("_None detected._")
    L.append("")
    L.append("## 🟡 Needs Attention (cluttered / empty / ambiguous)")
    L.append("")
    if s["cluttered_areas"]:
        L.append("**Cluttered:**")
        for n in s["cluttered_areas"]:
            L.append(f"- {n}")
        L.append("")
    if s["empty_stubs"]:
        L.append("**Empty stubs:**")
        for n in s["empty_stubs"]:
            L.append(f"- {n} — candidate for removal or filling")
        L.append("")
    if inv.get("root_loose_files"):
        L.append("**Loose files at vault root:**")
        for n in inv["root_loose_files"]:
            L.append(f"- {n}")
        L.append("")
    if inv.get("stale_duplicate_mirrors"):
        L.append("**Possible stale duplicates** (`_code/` mirrors `03 - Projects/`):")
        for n in inv["stale_duplicate_mirrors"]:
            L.append(f"- {n}")
        L.append("")
    L.append("## 🟢 Healthy / Active")
    L.append("")
    for e in inv["top_level"]:
        if e["activity"] == "active" and e["risk_tier"] != "high" \
           and not e.get("issues"):
            L.append(f"- **{e['name']}** — {e['purpose_guess']} "
                     f"({e.get('size_human','?')}, {e.get('file_count',0)} files)")
    L.append("")
    L.append("## Full Top-Level Registry")
    L.append("")
    L.append("| Name | Category | Risk | Activity | Files | Size | Issues |")
    L.append("|------|----------|------|----------|-------|------|--------|")
    for e in inv["top_level"]:
        issues = "; ".join(e.get("issues", [])) or "—"
        L.append(f"| {e['name']} | {e['category']} | {e['risk_tier']} | "
                 f"{e['activity']} | {e.get('file_count') or '—'} | "
                 f"{e.get('size_human','—')} | {issues} |")
    L.append("")
    # Organism health
    h = inv.get("organism_health")
    if h:
        L.append("## 🐙 Octopus Organism Health (read-only peek)")
        L.append("")
        L.append(f"- **Governor alert error-lines:** {h['governor_alert_errors']}")
        if h.get("recent_errors"):
            L.append("- **Recent error samples:**")
            for ln in h["recent_errors"]:
                L.append(f"  - `{ln[:160]}`")
        L.append("")
    L.append("---")
    L.append("_This report was produced by `vault_scanner.py` (read-only). "
             "No vault file was modified._")
    return "\n".join(L)


def build_telegram_summary(inv):
    s = inv["summary"]
    parts = []
    parts.append("🗂 F:\\backup — Vault Scan")
    parts.append(f"📁 {s['top_level_count']} top-level entries · "
                 f"{s['total_files_seen']} files · {s['total_size_human']}")
    parts.append("")
    parts.append("🔴 High-Risk (ASK before touching):")
    if s["high_risk_areas"]:
        parts.append("  " + "\n  ".join(s["high_risk_areas"]))
    else:
        parts.append("  — none —")
    parts.append("")
    parts.append("🟡 Needs attention:")
    flags = []
    if s["cluttered_areas"]:
        flags.append("cluttered: " + ", ".join(s["cluttered_areas"]))
    if s["empty_stubs"]:
        flags.append("empty stubs: " + ", ".join(s["empty_stubs"]))
    if inv.get("root_loose_files"):
        flags.append(f"{len(inv['root_loose_files'])} loose root files")
    if inv.get("stale_duplicate_mirrors"):
        flags.append("stale dupes in _code/: " + ", ".join(inv["stale_duplicate_mirrors"]))
    parts.append("  " + ("\n  ".join(flags) if flags else "— looks tidy —"))
    parts.append("")
    parts.append("🟢 Active (≤7d):")
    parts.append("  " + (", ".join(s["active_areas"]) if s["active_areas"] else "—"))
    h = inv.get("organism_health")
    if h and h.get("governor_alert_errors"):
        parts.append("")
        parts.append(f"🐙 Octopus organism: {h['governor_alert_errors']} "
                     "error-lines in governor-alerts.md")
    text = "\n".join(parts)
    if len(text) > TELEGRAM_MAX:
        text = text[:TELEGRAM_MAX - 20] + "\n…(truncated)"
    return text


# --------------------------------------------------------------------------- #
#  TELEGRAM SENDER (reuses existing bot token from .env)
# --------------------------------------------------------------------------- #
def load_env(path):
    env = {}
    if not os.path.isfile(path):
        return env
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    except OSError:
        pass
    return env


def send_telegram(text):
    """Send a message via the existing bot. Returns (ok, detail)."""
    env = load_env(ENV_FILE)
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat = env.get("TELEGRAM_OWNER_CHAT_ID")
    if not token or not chat:
        return False, "TELEGRAM_BOT_TOKEN or TELEGRAM_OWNER_CHAT_ID missing in .env"
    try:
        import requests  # imported lazily so --dry-run needs no deps
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, data={"chat_id": chat, "text": text},
                             timeout=20)
        if resp.status_code == 200:
            return True, "sent"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, f"exception: {e}"


# --------------------------------------------------------------------------- #
#  MAIN
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="Read-only vault scanner for F:\\backup")
    parser.add_argument("--dry-run", action="store_true",
                        help="scan only; print to console; write/send NOTHING")
    parser.add_argument("--no-telegram", action="store_true",
                        help="write reports but skip Telegram send")
    parser.add_argument("--scope", default=None,
                        help="narrow scan to one subfolder of the vault, e.g. '03 - Projects'")
    args = parser.parse_args()

    assert_read_only()

    scan_root = ROOT
    if args.scope:
        scan_root = os.path.join(ROOT, args.scope)
        if not os.path.isdir(scan_root):
            print(f"[!] Scope target not found: {scan_root}", file=sys.stderr)
            sys.exit(2)

    print(f"[*] Scanning: {scan_root}")
    print(f"[*] Read-only: {READ_ONLY}  |  dry-run: {args.dry_run}")
    print()

    top_entries = scan_subtree(scan_root, MAX_DEPTH)
    root_loose = root_loose_files(top_entries)
    stale_dupes = stale_duplicate_check(top_entries) \
        if not args.scope else []
    health = organism_health_peek(top_entries) \
        if not args.scope else None

    inv = build_inventory(top_entries, health, stale_dupes, root_loose)
    md = build_markdown_report(inv)
    tg = build_telegram_summary(inv)

    if args.dry_run:
        print("=" * 70)
        print("DRY RUN — nothing written, nothing sent.")
        print("=" * 70)
        print()
        print("--- TELEGRAM SUMMARY PREVIEW ---")
        print(tg)
        print()
        print("--- TOP-LEVEL REGISTRY ---")
        for e in inv["top_level"]:
            tag = e["risk_tier"]
            if tag == "high":
                tag = "🔴 HIGH"
            elif e.get("issues"):
                tag = "🟡 " + ", ".join(e["issues"])[:30]
            else:
                tag = "🟢 ok"
            sz = e.get('size_human') or '?'
            fc = e.get('file_count')
            fc = str(fc) if fc is not None else '?'
            print(f"  [{e['category']:<18}] {e['name']:<32} "
                  f"{sz:>10}  {fc:>5} files  {tag}")
        print()
        print(f"[*] Dry run complete. Re-run without --dry-run to write reports "
              f"to {DESKTOP} and send Telegram.")
        return

    # ---- Write outputs to Desktop ----
    json_path = os.path.join(DESKTOP, "vault-inventory.json")
    md_path = os.path.join(DESKTOP, "vault-report.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2, ensure_ascii=False)
    print(f"[✓] Wrote {json_path}")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[✓] Wrote {md_path}")

    # ---- Telegram ----
    if args.no_telegram:
        print("[*] --no-telegram set; skipping Telegram send.")
    else:
        print("[*] Sending Telegram summary …")
        ok, detail = send_telegram(tg)
        if ok:
            print("[✓] Telegram message sent.")
        else:
            print(f"[!] Telegram send failed: {detail}")

    print()
    print("[*] Done. No vault file was modified.")


if __name__ == "__main__":
    main()
