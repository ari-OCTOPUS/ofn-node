"""Did the browser actually apply EXIF rotation?

Run this on the first real photo uploaded from a real phone, BEFORE the
golden vector is captured. The order matters: a golden vector taken from a
sideways photo pins the bug in place for ever, and every future test agrees
with it.

Reads the dimensions out of the JPEG's own SOF marker. No browser, no
Pillow, no library — the two numbers that matter are eight bytes into a
segment the format is required to have.

    portrait source + `imageOrientation: 'from-image'` applied  →  h > w
    portrait source + rotation silently skipped                 →  w > h

That is the whole test. A synthetic file cannot perform it, because a
synthetic file has no EXIF for the browser to honour or ignore.

    python3 tools/check_rotation.py
"""

from __future__ import annotations

import os
import struct
import sys

MEDIA = os.path.expanduser("~/.local/share/ofn/photos/studio")

# Start Of Frame markers. Baseline, extended, progressive, lossless — all
# carry height and width in the same place. Excluded: DHT/JPG/DAC, which sit
# in the same numeric range but are not frame headers.
_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def dimensions(path: str) -> tuple[int, int]:
    """(width, height) of a JPEG, from its frame header."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"{path} is not a JPEG")
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in _SOF:
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        (length,) = struct.unpack(">H", data[i + 2:i + 4])
        i += 2 + length
    raise ValueError(f"no frame header found in {path}")


def main() -> int:
    if not os.path.isdir(MEDIA):
        print(f"هیچ رسانه‌ای در {MEDIA} نیست — هنوز عکسی نیامده.")
        return 1

    found = 0
    for draft in sorted(os.listdir(MEDIA)):
        folder = os.path.join(MEDIA, draft)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".jpg"):
                continue
            path = os.path.join(folder, name)
            try:
                w, h = dimensions(path)
            except ValueError as exc:
                print(f"  {draft}/{name}: {exc}")
                continue
            found += 1
            shape = "عمودی" if h > w else ("مربع" if h == w else "افقی")
            print(f"  {draft}/{name}: {w}×{h}  → {shape}"
                  f"   ({os.path.getsize(path) // 1024} KB)")

    if not found:
        print("هیچ فایل JPEG پیدا نشد.")
        return 1
    print()
    print("اگر عکس منبع عمودی بوده و اینجا «افقی» نوشته، چرخش اعمال نشده.")
    print("در آن حالت بردار طلایی نگیرید — یک عکس کج، باگ را تثبیت می‌کند.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
