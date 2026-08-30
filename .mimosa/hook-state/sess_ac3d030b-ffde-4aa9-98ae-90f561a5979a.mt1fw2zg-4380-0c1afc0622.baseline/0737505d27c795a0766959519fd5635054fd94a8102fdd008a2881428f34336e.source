#!/usr/bin/env python3
"""نسخه‌ی ۴ — مونتاژِ دُم‌ها (MANIFEST3) + جایگزینیِ کاملِ فایل‌های fresh/.

    python3 tests/_shadow_tails/assemble4.py <SRC> <DEST>

fresh/: هر فایل زیر tests/_shadow_tails/fresh/<relpath> عیناً روی
<DEST>/<relpath> کپی می‌شود — برای فایل‌هایی که بازنویسی‌شان در نمای mount
بریده دیده می‌شود و دُم‌گذاری به‌صرفه نیست (مثل خودِ تست‌ها).
"""
import sys
import shutil
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", ".obsidian", "outputs", ".git",
                ".claude", ".agents", ".streamlit"}


def main(src: str, dest: str) -> int:
    src_p, dest_p = Path(src), Path(dest)
    if dest_p.exists():
        shutil.rmtree(dest_p)

    for f in src_p.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(src_p)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if f.suffix not in {".py", ".txt", ".json", ".md", ".tail",
                            ".tail2", ".bat", ""}:
            continue
        out = dest_p / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, out)

    tails = dest_p / "tests" / "_shadow_tails"
    fixed, failed = [], []
    for line in (tails / "MANIFEST3.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rel, tailname = line.split("|")
        target = dest_p / rel
        tail = (tails / tailname).read_bytes()
        anchor = tail.split(b"\n", 1)[0]
        data = target.read_bytes()
        idx = data.rfind(anchor)
        if idx < 0:
            failed.append(rel)
            continue
        target.write_bytes(data[:idx] + tail)
        fixed.append(rel)

    fresh = tails / "fresh"
    n_fresh = 0
    if fresh.exists():
        for f in fresh.rglob("*"):
            if f.is_file():
                rel = f.relative_to(fresh)
                out = dest_p / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, out)
                n_fresh += 1

    print(f"assembled: {len(fixed)} | fresh: {n_fresh} | FAILED: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
