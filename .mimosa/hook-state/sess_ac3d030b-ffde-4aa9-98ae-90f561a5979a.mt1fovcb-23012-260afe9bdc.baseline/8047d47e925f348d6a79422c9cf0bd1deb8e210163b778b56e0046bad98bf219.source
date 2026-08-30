# -*- coding: utf-8 -*-
"""Evidence-contract linter (S1 enforcement).

Resolves [REPO] path:line against real files, flags [UNVERIFIED] near TIER-1,
and optionally HEAD-checks [DOC]/[PAPER] URLs.

Usage:
  python -m octopus_v3.verify_evidence --root F:\\backup FILE [FILE ...]
  python -m octopus_v3.verify_evidence --root F:\\backup --net FILE
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

TAG_RE = re.compile(r"\[(REPO|SPEC|DOC|PAPER|INFER|UNKNOWN|UNVERIFIED|VERIFIED|CORRECTED|CHANGED)\]")
REPO_TICK_RE = re.compile(r"\[REPO\][^\n]{0,240}?`([^`]+)`")
TIER1_RE = re.compile(r"TIER-1")
WINDOW = 240


def _split_loc(spec: str) -> tuple[str, int | None]:
    m = re.search(r":(\d+)$", spec.strip())
    if m:
        return spec.strip()[: m.start()], int(m.group(1))
    return spec.strip(), None


def _line_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return -1


def lint_text(text: str, *, root: Path, source: str) -> list[str]:
    errors: list[str] = []
    for m in REPO_TICK_RE.finditer(text):
        rel, line = _split_loc(m.group(1))
        if not rel:
            continue
        target = (root / rel).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{source}: [REPO] path escapes root: {rel}")
            continue
        if not target.exists():
            errors.append(f"{source}: [REPO] missing file: {rel}")
            continue
        if line is not None:
            n = _line_count(target)
            if n >= 0 and line > n:
                errors.append(f"{source}: [REPO] {rel}:{line} > {n} lines")
    for um in re.finditer(r"\[UNVERIFIED\]", text):
        lo = max(0, um.start() - WINDOW)
        hi = min(len(text), um.end() + WINDOW)
        if TIER1_RE.search(text[lo:hi]):
            errors.append(f"{source}: [UNVERIFIED] sits near TIER-1 — cannot drive a TIER-1 verdict")
    return errors


def check_urls(text: str, source: str, timeout: float = 8.0) -> list[str]:
    errors: list[str] = []
    for m in re.finditer(r"\[(?:DOC|PAPER)\][^\n]{0,300}?(https?://[^\s\)\]]+)", text):
        url = m.group(1).rstrip(".,;")
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "octopus-v3-evidence/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if getattr(resp, "status", 200) >= 400:
                    errors.append(f"{source}: [DOC] HTTP {resp.status} {url}")
        except urllib.error.HTTPError as exc:
            if exc.code in (405, 403):
                # HEAD rejected — try GET range-less is too heavy; record as warn not fail
                continue
            errors.append(f"{source}: [DOC] HTTP {exc.code} {url}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"{source}: [DOC] unreachable {url} ({exc})")
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="OCTOPUS v3 evidence contract linter")
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--root", type=Path, default=Path(r"F:\backup"))
    p.add_argument("--net", action="store_true", help="HEAD-check [DOC]/[PAPER] URLs")
    args = p.parse_args(argv)
    root = args.root.resolve()
    all_err: list[str] = []
    for f in args.files:
        text = f.read_text(encoding="utf-8", errors="replace")
        all_err.extend(lint_text(text, root=root, source=str(f)))
        if args.net:
            all_err.extend(check_urls(text, str(f)))
    if all_err:
        sys.stderr.write("\n".join(all_err) + "\n")
        return 1
    print("verify_evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
