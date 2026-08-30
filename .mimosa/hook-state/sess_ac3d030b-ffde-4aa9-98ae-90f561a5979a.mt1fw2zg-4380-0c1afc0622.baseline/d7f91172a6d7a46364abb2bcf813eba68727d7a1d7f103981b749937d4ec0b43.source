"""test_close_hf_expected_absent_20260816 — ERRORHUNT ۴ قفل.

HF_TOKEN در درخت 4d/_ops اجباری نیست؛ غیبت آگاهانه است. مقدار نساز.
ثبت در run_all نشده (WORKLOCK).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP = {"tests", "__pycache__", "_Archive", "_Duplicates", "node_modules"}


def test_hf_token_not_required_in_ops_or_4d():
    hits: list[str] = []
    for base in (ROOT / "4d_system", ROOT / "_ops"):
        for path in base.rglob("*.py"):
            if any(part in SKIP for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "HF_TOKEN" in text:
                hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits
