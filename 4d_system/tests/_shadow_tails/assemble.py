#!/usr/bin/env python3
"""بازسازیِ درختِ کاملِ پروژه در محیطی که mount اندازه‌ی کهنه گزارش می‌دهد.

استفاده (داخل sandbox لینوکسی ایجنت):
    python3 tests/_shadow_tails/assemble.py <SRC> <DEST>
مثال:
    python3 tests/_shadow_tails/assemble.py /sessions/.../mnt/4d_system /tmp/w4d

روش: کپیِ نمای (احتمالاً بریده‌ی) mount + جایگزینیِ انتهای هر فایلِ مانیفست
از آخرین رخدادِ «لنگر» (خطِ اولِ فایلِ دُم). روی ویندوزِ مالک لازم نیست.
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

    # ۱) کپیِ انتخابی
    for f in src_p.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(src_p)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if f.suffix not in {".py", ".txt", ".json", ".md", ".tail", ".bat", ""}:
            continue
        out = dest_p / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, out)

    # ۲) مونتاژ دُم‌ها
    tails = dest_p / "tests" / "_shadow_tails"
    manifest = tails / "MANIFEST.txt"
    fixed, failed = [], []
    for line in manifest.read_text(encoding="utf-8").splitlines():
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

    print(f"assembled: {len(fixed)} | FAILED (لنگر پیدا نشد — دُم را از لنگرِ "
          f"قدیمی‌تری بازبنویس): {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
