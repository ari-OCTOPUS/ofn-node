"""Turn the first real upload into the golden vector.

Run this only AFTER `check_rotation.py` says the photo came out the right way
up. The order is not a preference: a golden vector taken from a sideways
photo pins the bug in place for ever, and every future test then agrees with
it.

Why this reconstruction is exact rather than approximate:

    toDataURL output  ==  "data:image/jpeg;base64," + base64(those bytes)

and the file on disk is those bytes — `media.write_rendition` decodes the
payload and writes it unchanged. So base64-ing the stored rendition gives
back the identical string the browser produced. This is not a fixture we
invented; it is the producer's own output, recovered.

That matters because three times in one night the same failure appeared:
tests that generate their own input validate themselves. The real producer —
a canvas, on a real phone, with real EXIF — is the one source whose shape we
did not choose.

    python3 tools/capture_golden.py <draft-id>
"""

from __future__ import annotations

import base64
import os
import sys

MEDIA = os.path.expanduser("~/.local/share/ofn/photos/studio")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(HERE, "tests", "fixtures")

EDGES = (1600, 320)


def main(draft: str) -> int:
    folder = os.path.join(MEDIA, draft)
    if not os.path.isdir(folder):
        print(f"پیش‌نویسی به نام «{draft}» در {MEDIA} نیست.")
        print("موجود:", ", ".join(sorted(os.listdir(MEDIA))) or "(هیچ)")
        return 1

    os.makedirs(FIXTURES, exist_ok=True)
    written = 0
    for edge in EDGES:
        src = os.path.join(folder, f"0-{edge}.jpg")
        if not os.path.isfile(src):
            print(f"  {edge}: فایل نیست — {src}")
            continue
        with open(src, "rb") as fh:
            raw = fh.read()
        vector = "data:image/jpeg;base64," + base64.b64encode(raw).decode()
        out = os.path.join(FIXTURES, f"canvas-{edge}.txt")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(vector + "\n")
        print(f"  canvas-{edge}.txt  ←  {len(raw)} بایت  "
              f"({len(vector)} کاراکتر base64)")
        written += 1

    if written != len(EDGES):
        print("\nناقص. هر دو اندازه لازم است.")
        return 1
    print("\nحالا: python3 -m pytest tests/test_photos_golden.py -q")
    print("آن پنج تست دیگر skip نمی‌شوند.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
