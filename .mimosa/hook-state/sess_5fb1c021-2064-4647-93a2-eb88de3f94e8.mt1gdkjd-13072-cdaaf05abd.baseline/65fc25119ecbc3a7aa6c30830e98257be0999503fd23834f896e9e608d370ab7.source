"""test_close_experiments_retired_20260816 — Deep-Seams VOTE 1 close-honest.

بسته retired است (STATUS.md)؛ صفر caller تولیدی بیرون پوشه. حذف ممنوع.
ثبت در run_all نشده (WORKLOCK).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "_ops" / "hypothesis_engine" / "experiments"
SKIP = {"tests", "__pycache__", "_Archive", "_Duplicates", "node_modules", ".venv", "venv"}


def test_status_retired_file_exists():
    text = (PKG / "STATUS.md").read_text(encoding="utf-8")
    assert "status: retired" in text
    assert "حذف ممنوع" in text


def test_no_production_callers_outside_package():
    hits: list[str] = []
    for base in (ROOT / "4d_system", ROOT / "_ops"):
        for path in base.rglob("*.py"):
            if any(part in SKIP for part in path.parts):
                continue
            try:
                if path.resolve().is_relative_to(PKG.resolve()):
                    continue
            except ValueError:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "hypothesis_engine.experiments" in text or "hypothesis_engine/experiments" in text:
                hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits
