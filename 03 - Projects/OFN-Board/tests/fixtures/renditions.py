"""Shared test fixture: canvas renditions (finding 89).

The same two-rendition payload was defined in test_studio_api.py and
test_product_photos.py, and a third test imported from another test module.
One definition, one place: anything that simulates a browser canvas send
imports from here.

The bytes are a minimal JPEG header plus filler — enough for the media
layer to accept and process, not a real image (golden canvas fixtures are
a separate, human-captured task, finding 88).
"""

from __future__ import annotations

import base64

IMG = base64.b64encode(b"\xff\xd8\xff" + b"x" * 200).decode()
RENDITIONS = {"1600": "data:image/jpeg;base64," + IMG,
              "320": "data:image/jpeg;base64," + IMG}
