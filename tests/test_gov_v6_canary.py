"""GOV-V6 canary status lock — the doc may only claim PROVEN with receipts.

Until the live three-observation ritual (no-approval red, author red, valid
reviewer green) is recorded in docs/octopus-os/08-GOV-V6-CANARY.md, the
status line must stay ASSERTED_NOT_PROVEN. Flipping the marker without the
receipt lines turns this test red — a status claim without evidence cannot
land (same class as F-09/F-13)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "octopus-os" / "08-GOV-V6-CANARY.md"


def test_canary_doc_exists_and_honest() -> None:
    src = DOC.read_text(encoding="utf-8")
    m = re.search(r"GOV_V6_BEHAVIOR\s*=\s*(\S+)", src)
    assert m, "status line missing"
    status = m.group(1)
    if status == "ASSERTED_NOT_PROVEN":
        return
    assert status.startswith("PROVEN"), f"unknown status {status!r}"
    # claiming PROVEN requires receipt pointers in the same line
    assert re.search(r"GOV_V6_BEHAVIOR\s*=\s*PROVEN\s*\(receipts?:", src), \
        "PROVEN without receipt links is exactly the drift this locks out"
