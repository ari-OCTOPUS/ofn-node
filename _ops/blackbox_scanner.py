#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""blackbox_scanner.py — اسکنِ خودکارِ F:\ برای جعبه‌های سیاه (read-only، $0).

هدف: کشفِ دایرکتوری‌هایی با الگوی جعبه‌سیاه — بی‌گیت، بزرگ، یا با اسمِ خاص.
هیچ فایلِ ممنوعه‌ای را باز/هش/لیست نمی‌کند.

الگوهای کشف:
  - نام: "Black Box"، "OLD *"، "backup-*"، "octopus-*"، "this"، "zz"
  - ساختار: دایرکتوریِ بدون .git با حجمِ بالا و فایلِ کم

پشتِ OCTOPUS_WIRE_BLACKBOX_MAP. خروجی: JSON report در state/.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_BLACKBOX_MAP"
ROOTS = [
    Path("F:\\"),
    Path("F:\\backup"),
]

_FORBIDDEN = (
    "partner", "pii", "identity", ".env", "secret", "credential",
    "wallet", "seed", "id_rsa", ".pem", ".key", "owner-profile",
)

# الگوهای اسم — case-insensitive match
_BLACKBOX_PATTERNS = [
    ("nbb", "NBB / Black Box"), ("black box", "Black Box"), ("old ", "OLD archive"),
    ("backup-", "backup snapshot"), ("octopus-", "Octopus phase"),
    ("this", "odd name"), ("zz", "odd name"), ("claude-export", "Claude export"),
    ("tmp", "temp"), ("4d", "4D system"), (".worktree", "worktree"),
]


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _forbidden(p: str) -> bool:
    s = str(p).lower().replace("\\", "/")
    return any(x in s for x in _FORBIDDEN)


def _classify(name: str, is_dir: bool) -> str | None:
    low = name.lower()
    for pat, label in _BLACKBOX_PATTERNS:
        if pat in low:
            return label
    return None


def _sample_dir(p: Path, max_files: int = 10, max_depth: int = 1) -> dict:
    """نمونه‌برداریِ امن از دایرکتوری. بدون recursion عمیق."""
    try:
        items = list(p.iterdir())[:100]
    except (OSError, PermissionError):
        return {"error": "unreadable"}
    files = []
    dirs = []
    total_size = 0
    for item in items:
        try:
            if item.is_file():
                sz = item.stat().st_size
                total_size += sz
                name_low = item.name.lower()
                ext = item.suffix.lower()
                if not _forbidden(str(item)):
                    files.append({"name": item.name, "size": sz, "ext": ext})
            elif item.is_dir():
                if not _forbidden(str(item)):
                    dirs.append(item.name)
        except OSError:
            continue
    files.sort(key=lambda x: x["size"], reverse=True)
    # ext distribution
    ext_dist: dict[str, int] = {}
    for f in files:
        ext = f["ext"] or "(none)"
        ext_dist[ext] = ext_dist.get(ext, 0) + 1
    top_exts = sorted(ext_dist.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "file_count": len(files),
        "dir_count": len(dirs),
        "total_bytes": total_size,
        "top_files": files[:max_files],
        "top_exts": [{"ext": e, "n": n} for e, n in top_exts],
        "has_git": ".git" in dirs,
        "sampled": len(items) >= 100,
    }


def scan() -> dict:
    """اسکن rootهای F:\\. فقط دایرکتوری‌های سطح اول. fail-soft."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    findings = []
    for root in ROOTS:
        if not root.exists():
            continue
        try:
            for entry in sorted(root.iterdir()):
                if not entry.is_dir():
                    continue
                name = entry.name
                label = _classify(name, True)
                if label is None:
                    continue
                if _forbidden(name):
                    findings.append({
                        "path": str(entry),
                        "label": label,
                        "status": "forbidden",
                        "sample": "not-scanned",
                    })
                    continue
                sample = _sample_dir(entry)
                findings.append({
                    "path": str(entry),
                    "name": name,
                    "label": label,
                    "sample": sample,
                })
        except (OSError, PermissionError):
            continue

    report = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n": len(findings),
        "findings": findings,
    }
    # save
    out = opslib.STATE_DIR / "blackbox-scan-latest.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(out)
    except OSError:
        pass
    return report


def card() -> str:
    rep = scan()
    if not rep.get("ok", True) is True and "reason" in rep:
        return f"🔍 scanner: {rep.get('reason')}"
    lines = [f"🔍 F:\\ scan — {rep['n']} dirs — {rep['ts']}"]
    for f in rep.get("findings") or []:
        s = f.get("sample") or {}
        if isinstance(s, str):
            lines.append(f"  ⚪ {f['name']} [{f['label']}] — {s}")
            continue
        sz = s.get("total_bytes", 0)
        sz_str = f"{sz/1e6:.1f}MB" if sz > 1e6 else f"{sz/1e3:.0f}KB" if sz > 1e3 else f"{sz}B"
        git = "·git" if s.get("has_git") else "·NOGIT"
        lines.append(
            f"  {'🔴' if s.get('has_git') else '🟡'} {f['name']}: "
            f"{s.get('file_count', 0)}f/{sz_str}{git} [{f['label']}]"
        )
    if not rep.get("findings"):
        lines.append("  (no matches)")
    return "\n".join(lines)


if __name__ == "__main__":
    print(card())
