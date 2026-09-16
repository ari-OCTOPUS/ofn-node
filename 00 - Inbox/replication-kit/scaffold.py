#!/usr/bin/env python3
"""scaffold.py — بازسازی اسکلت vault agent-first از روی seed/

Usage:
    python scaffold.py <target-dir> [--git-init] [--force]

Safety:
    - مقصد باید خالی باشد (یا --force برای مقصدی که فقط فایل مخفی دارد).
    - هرگز چیزی حذف یا overwrite نمی‌کند — اگر فایلی از قبل باشد، خطا می‌دهد.
    - هیچ secret ای در seed نیست و این اسکریپت هم چیزی از محیط نمی‌خواند.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
SEED = KIT_DIR / "seed"


def fail(msg: str) -> None:
    print(f"[scaffold] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Recreate the agent-first vault skeleton")
    ap.add_argument("target", help="مسیر vault جدید (باید خالی باشد)")
    ap.add_argument("--git-init", action="store_true", help="git init + اولین commit")
    ap.add_argument("--force", action="store_true", help="اجازه به مقصدی که فقط dotfile دارد")
    args = ap.parse_args()

    if not SEED.is_dir():
        fail(f"seed/ کنار اسکریپت پیدا نشد: {SEED}")

    target = Path(args.target).expanduser().resolve()
    if target == SEED or SEED in target.parents:
        fail("مقصد نمی‌تواند داخل خود kit باشد")

    if target.exists():
        visible = [p for p in target.iterdir() if not p.name.startswith(".")]
        if any(target.iterdir()) and not args.force:
            fail(f"مقصد خالی نیست: {target} (برای مقصد با dotfile از --force استفاده کن)")
        if visible:
            fail(f"مقصد فایل قابل‌مشاهده دارد: {visible[:3]} — scaffold هرگز overwrite نمی‌کند")
    target.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    copied = 0
    for src in sorted(SEED.rglob("*")):
        rel = src.relative_to(SEED)
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        if dst.exists():
            fail(f"از قبل وجود دارد (overwrite ممنوع): {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix == ".md":
            txt = src.read_text(encoding="utf-8")
            txt = txt.replace("created: 2026-01-01", f"created: {today}")
            txt = txt.replace("updated: 2026-01-01", f"updated: {today}")
            dst.write_text(txt, encoding="utf-8")
        else:
            shutil.copy2(src, dst)
        copied += 1
    print(f"[scaffold] {copied} فایل در {target} ساخته شد.")

    if args.git_init:
        try:
            subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True)
            (target / ".gitignore").write_text(
                ".obsidian/workspace*\n*.env*\n*secret*\n*wallet*\n*seed*\n*key*\n*.pem\nsecrets-export/\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "-A"], cwd=target, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "agent-checkpoint: vault scaffold from replication-kit"],
                cwd=target, check=True, capture_output=True,
            )
            print("[scaffold] git init + اولین commit انجام شد.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[scaffold] WARN: git init ناموفق ({e}) — دستی انجام بده.")

    print(
        "\nقدم‌های بعدی (فاز ۱ — human-only):\n"
        "  1. جدول پروژه‌ها را در _PROJECT_INSTRUCTIONS.md پر کن.\n"
        "  2. ROTATION_CHECKLIST.md را با سرویس‌های واقعی پر کن (§Security Gate).\n"
        "  3. برای هر پروژه: پوشه در '03 - Projects' + PROJECT.md از _Templates/project.md.\n"
        "  4. validate: python '04 - Architect System/scripts/validate_frontmatter.py'\n"
        "             python '04 - Architect System/scripts/find_broken_links.py'\n"
        "  نقشه کامل: BLUEPRINT.md §۱۰"
    )


if __name__ == "__main__":
    main()
