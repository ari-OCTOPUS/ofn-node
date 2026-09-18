#!/usr/bin/env python3
"""Runtime snapshot of board 138 with two-sided hashes (DC-03E1A pattern).

Purpose: the live runtime on 138 has diverged from canonical git. Before any
patch, PR or rollback decision, capture what is actually running — byte-exact,
with a hash computed on the node and re-computed locally — and record which
files exist in 138's own HEAD and which do not.

Byte-exactness matters: files are fetched base64-encoded and verified by sha256
on both sides. A text-mode fetch would silently rewrite line endings and the
hash would no longer describe the running code.

Secrets: these are live runtime files and may embed credentials. Contents are
never printed; a pattern scan records the KIND and COUNT of matches (never a
value) so the export can be reviewed before anything is committed or pushed.

Usage:
  python runtime_snapshot.py --board board138
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
EVIDENCE = LANE / "evidence"
SNAP_DIR = EVIDENCE / "runtime-snapshot-138"

REPO = "/home/ari/ofn"

# (repo-relative path, human label). Repo files get a git blob hash and an
# in-HEAD check; absolute-path files get stat + sha256 only.
TARGETS = [
    ("ofn/ziman_cycle/gates.py", "A1 ziman hold flip (claimed)"),
    ("ofn/agents/owner_notify.py", "R1 notify retry patch (claimed)"),
    ("ofn/agents/glass_runner.py", "telegram button intake patch (claimed)"),
    ("tools/w1_verdict_collector.py", "W1 verdict collector (untracked)"),
    ("state/revenue-drive/owner_ask.py", "owner card generator"),
    ("state/revenue-drive/owner_reply.py", "owner reply attribution"),
    ("state/revenue-drive/action_executor.py", "action executor"),
    ("state/revenue-drive/proposal_intake.py", "proposal intake"),
    ("state/revenue-drive/uwork_acceptance_test.py", "uwork acceptance test"),
    ("state/revenue-drive/patch_uwork_wire.py", "uwork wire patch script"),
    ("state/revenue-drive/funnel_reconcile.py", "funnel reconcile"),
    ("ofn/agents/owner_digest_emit.py", "owner digest emit (untracked)"),
    ("ofn/agents/owner_queue_notify_hook.py", "owner queue notify hook (untracked)"),
]

ABS_TARGETS = [
    ("/usr/local/bin/octopus-138-pulse.sh", "telemetry pulse (leaf key fix)"),
    ("/etc/systemd/system/octopus-w1-verdict.service", "W1 verdict unit"),
    ("/etc/systemd/system/octopus-w1-verdict.timer", "W1 verdict timer"),
]

SECRET_PATTERNS = [
    ("shopify_admin_token", re.compile(r"shpat_[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("telegram_bot_token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{12,}\b")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("assigned_password", re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']")),
    ("bearer_header", re.compile(r"(?i)authorization['\"]?\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._-]{20,}")),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ssh(cmd: str, timeout: int = 180) -> tuple[int, bytes]:
    key = str(Path.home() / ".ssh" / "id_ed25519")
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=8", "-i", key, "ari@192.168.0.138", cmd],
        capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL,
    )
    return proc.returncode, proc.stdout


def remote_meta(paths: list[str]) -> dict:
    """One round trip: stat + sha256 + git blob hash + in-HEAD check."""
    script = ["set +e", f'cd {REPO}']
    for p in paths:
        q = f"{REPO}/{p}"
        script.append(f'echo "--- {p}"')
        # Single-quoted awk only: a \" escape nested inside $( ) inside " "
        # is re-parsed into garbage and the substitution comes back empty.
        script.append(f'echo "size=$(stat -c %s {q} 2>/dev/null)"')
        script.append(f'echo "mtime=$(stat -c %y {q} 2>/dev/null)"')
        script.append(f'echo "sha256=$(sha256sum {q} 2>/dev/null | awk \'{{print $1}}\')"')
        script.append(f'echo "blob=$(git hash-object {q} 2>/dev/null)"')
        script.append(f'git cat-file -e HEAD:{p} 2>/dev/null && echo "in_head=YES" || echo "in_head=NO"')
        script.append(f'git diff --quiet HEAD -- {p} 2>/dev/null && echo "diff_head=CLEAN" || echo "diff_head=DIFFERS"')
    script.append("echo PROBE_END=1")
    rc, out = ssh("\n".join(script))
    text = out.decode(errors="replace").replace("\r", "")
    meta: dict[str, dict] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("--- "):
            current = line[4:].strip()
            meta[current] = {}
            continue
        if current is None or "=" not in line:
            continue
        k, _, v = line.partition("=")
        meta[current][k.strip()] = v.strip()
    return meta


def fetch_bytes(remote_path: str) -> bytes | None:
    rc, out = ssh(f"base64 -w0 {remote_path} 2>/dev/null")
    if rc != 0 or not out.strip():
        return None
    try:
        return base64.b64decode(out.strip())
    except Exception:
        return None


def scan_secrets(data: bytes) -> dict:
    text = data.decode("utf-8", errors="replace")
    findings = {}
    for name, pattern in SECRET_PATTERNS:
        hits = len(pattern.findall(text))
        if hits:
            findings[name] = hits
    return findings


def per_file_meta(rel: str) -> dict:
    """Fallback for a single file when the batched probe returns a partial block.

    The batched script demonstrably lost one file's hash lines (16 entries, one
    block with size/mtime but no sha256/blob). Rather than ship a manifest with
    a hole, re-measure that file on its own — the same commands work fine when
    issued per file.
    """
    q = f"{REPO}/{rel}"
    script = "; ".join([
        f'echo "size=$(stat -c %s {q} 2>/dev/null)"',
        f'echo "mtime=$(stat -c %y {q} 2>/dev/null)"',
        f'echo "sha256=$(sha256sum {q} 2>/dev/null | awk \'{{print $1}}\')"',
        f'echo "blob=$(git hash-object {q} 2>/dev/null)"',
        f'git cat-file -e HEAD:{rel} 2>/dev/null && echo "in_head=YES" || echo "in_head=NO"',
        f'git diff --quiet HEAD -- {rel} 2>/dev/null && echo "diff_head=CLEAN" || echo "diff_head=DIFFERS"',
    ])
    rc, out = ssh(f"cd {REPO} && {script}")
    meta = {}
    for line in out.decode(errors="replace").replace("\r", "").splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            meta[k.strip()] = v.strip()
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default="board138")
    args = ap.parse_args()

    SNAP_DIR.mkdir(parents=True, exist_ok=True)

    repo_paths = [p for p, _ in TARGETS]
    meta = remote_meta(repo_paths)

    entries = []
    for rel, label in TARGETS:
        m = meta.get(rel, {})
        if not m.get("sha256"):
            m = per_file_meta(rel) or m
        entry = {
            "path": rel,
            "abs": f"{REPO}/{rel}",
            "label": label,
            "size": m.get("size"),
            "mtime": m.get("mtime"),
            "sha256": m.get("sha256"),
            "git_blob": m.get("blob"),
            "in_head": m.get("in_head"),
            "diff_vs_head": m.get("diff_head"),
        }
        data = fetch_bytes(f"{REPO}/{rel}")
        if data is None:
            entry["fetch"] = "MISSING"
            entries.append(entry)
            continue
        local_sha = hashlib.sha256(data).hexdigest()
        entry["fetch"] = "OK"
        entry["sha256_verified"] = (local_sha == entry["sha256"])
        entry["sha256_local"] = local_sha
        entry["secrets_found"] = scan_secrets(data)
        slug = rel.replace("/", "__")
        (SNAP_DIR / slug).write_bytes(data)
        entries.append(entry)
        print(f"  [{entry['fetch']:>7}] {rel} sha_match={entry['sha256_verified']} "
              f"in_head={entry['in_head']} diff={entry['diff_vs_head']} "
              f"secrets={entry['secrets_found'] or 'none'}")

    abs_entries = []
    for path, label in ABS_TARGETS:
        rc, out = ssh(f'sha256sum {path} 2>/dev/null; stat -c "size=%s mtime=%y" {path} 2>/dev/null')
        text = out.decode(errors="replace")
        sha = re.search(r"\b([0-9a-f]{64})\b", text)
        size = re.search(r"size=(\d+)", text)
        entry = {
            "path": path, "label": label,
            "sha256": sha.group(1) if sha else None,
            "size": size.group(1) if size else None,
        }
        data = fetch_bytes(path)
        if data is None:
            entry["fetch"] = "MISSING"
        else:
            local_sha = hashlib.sha256(data).hexdigest()
            entry["fetch"] = "OK"
            entry["sha256_verified"] = (local_sha == entry["sha256"])
            entry["secrets_found"] = scan_secrets(data)
            (SNAP_DIR / path.strip("/").replace("/", "__")).write_bytes(data)
        abs_entries.append(entry)
        print(f"  [{entry['fetch']:>7}] {path} sha_match={entry.get('sha256_verified')} "
              f"secrets={entry.get('secrets_found') or 'none'}")

    # Preimages: whatever backups the day's patches left behind.
    rc, out = ssh(
        "ls -la /home/ari/ofn/ofn/ziman_cycle/*.pre-* /home/ari/ofn/ofn/agents/*.pre-* "
        "/home/ari/ofn/ofn/agents/*.bak-* /usr/local/bin/*.bak-* "
        "/home/ari/ofn/tools/*.pre-* /home/ari/ofn/tools/*.bak-* 2>/dev/null")
    preimages = [l for l in out.decode(errors="replace").splitlines() if l.strip()]

    manifest = {
        "schema": "runtime_snapshot.v1",
        "at_utc": utc_now(),
        "board": args.board,
        "repo_head_on_board": None,
        "files": entries,
        "system_files": abs_entries,
        "preimage_listing": preimages,
        "notes": (
            "sha256 computed on the node and re-computed locally after a base64 fetch; "
            "sha256_verified=True means the local copy is byte-identical to the running file. "
            "secrets_found reports pattern KIND and COUNT only - values are never captured."
        ),
    }

    rc, out = ssh(f"git -C {REPO} log -1 --format=%H")
    manifest["repo_head_on_board"] = out.decode().strip()

    (EVIDENCE / "RUNTIME-SNAPSHOT-MANIFEST.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    verified = sum(1 for e in entries + abs_entries if e.get("sha256_verified"))
    total = len(entries) + len(abs_entries)
    print(f"\nsnapshot -> {SNAP_DIR} ({verified}/{total} byte-verified)")
    print(f"manifest -> {EVIDENCE / 'RUNTIME-SNAPSHOT-MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
