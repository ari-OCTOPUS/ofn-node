"""baseline — a CONTENT manifest for the files a receipt actually read.

Why this exists (found 2026-09-17, a real hole in the first PRE receipt): the receipt
pinned `git rev-parse HEAD` as its "runtime identity", but the doctor reads files from
the **working tree**. Re-checking showed that of the 11 distinct files in the halt-site
scan, **4 were not in a clean tracked state** — one tracked-but-modified
(`ofn/agents/release_pipeline.py`, itself one of the five oracle consumers) and three
**never tracked at all** (`ofn/agents/followup_worker.py`, `ofn/kernel/stale_class.py`,
`ops/ign1_telegram_ignite.py`). A baseline pinned to a commit does not describe those
files, so a POST compared against it would not be reproducible from the commit alone.

The fix is content-level, not commit-level: record a sha256 for every file the analysis
read, and define the POST rule as *"every manifest digest identical except the files the
change intended to touch"*. That is strictly more precise than HEAD pinning and it
detects a concurrent lane's edit automatically.

Deliberately NO `subprocess`: the safety rules forbid it, and running git (hooks,
aliases, config) is exactly the kind of surface this tool must not have. `tracked`
status is therefore *not* claimed — the manifest is content-based, which is the sound
comparison anyway.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

MANIFEST_SCHEMA = "octopus.halt-doctor.source-manifest.v1"

# Records the rule so a POST reader cannot reinterpret it.
MANIFEST_RULE = (
    "POST is comparable iff every digest here is identical except the files the change "
    "intended to touch. A file outside that set changing means a concurrent writer moved "
    "the baseline and PRE must be re-run."
)


def sha256_file(path: Path) -> str | None:
    """Content digest, or None if the file cannot be read. Never raises."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def source_manifest(repo: Path, files) -> dict:
    """{relative_path: sha256|null} for every file the analysis depends on."""
    out: dict[str, str | None] = {}
    for rel in sorted(set(files)):
        out[rel] = sha256_file(Path(repo) / rel)
    return {
        "schema": MANIFEST_SCHEMA,
        "rule": MANIFEST_RULE,
        "tracked_status_claimed": False,
        "tracked_status_reason": (
            "determining tracked/untracked requires running git, which the safety rules "
            "forbid (no subprocess). The manifest is content-based by design."
        ),
        "file_count": len(out),
        "files": out,
    }


def compare(previous: dict, current: dict, expected_changed) -> dict:
    """Compare two manifests. `expected_changed` = the files the change intended.

    Returns a dict with the three sets that matter, and `comparable` / `verdict`.
    """
    prev_files = (previous or {}).get("files", {}) or {}
    cur_files = (current or {}).get("files", {}) or {}
    expected = set(expected_changed or ())

    added = sorted(set(cur_files) - set(prev_files))
    removed = sorted(set(prev_files) - set(cur_files))
    changed = sorted(p for p in set(prev_files) & set(cur_files)
                     if prev_files[p] != cur_files[p])

    unexpected_changed = [p for p in changed if p not in expected]
    intended = [p for p in changed if p in expected]
    expected_not_changed = sorted(expected - set(changed))

    comparable = not added and not removed and not unexpected_changed
    if not comparable:
        verdict = "BASELINE_MOVED"
    elif expected_not_changed:
        verdict = "CHANGE_INCOMPLETE"
    else:
        verdict = "COMPARABLE"

    return {
        "verdict": verdict,
        "comparable": comparable,
        "intended_changes": intended,
        "unexpected_changes": unexpected_changed,
        "files_added": added,
        "files_removed": removed,
        "expected_but_unchanged": expected_not_changed,
        "note": ("BASELINE_MOVED means a file outside the intended set changed - re-run "
                 "PRE before drawing any conclusion"
                 if verdict == "BASELINE_MOVED" else
                 "CHANGE_INCOMPLETE means an intended file did not change"
                 if verdict == "CHANGE_INCOMPLETE" else
                 "every digest matches except the intended files"),
    }
