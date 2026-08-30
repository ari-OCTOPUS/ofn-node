"""test_ease_claim_unwired_20260816 — قفل NEVER-WIRED برای claim_hypothesis.

API در 4d_system/memory/store.py زنده است؛ صفر caller تولیدی بیرون تست‌ها
(REST-NIGHT/PERPETUAL). این تست رفتار تولید را عوض نمی‌کند — فقط قفل می‌کند
که سیم تازهٔ خاموش بدون رأی وارد نشود.

ثبت در run_all.py نشده (WORKLOCK).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEF = (ROOT / "4d_system" / "memory" / "store.py").resolve()
SKIP_PARTS = {
    "tests",
    "__pycache__",
    "_Archive",
    "_Duplicates",
    "node_modules",
    ".venv",
    "venv",
    "_scratch-hardtest",
    "_portable-build",
}


def test_claim_hypothesis_defined_in_store():
    src = DEF.read_text(encoding="utf-8")
    assert "def claim_hypothesis(" in src


def test_claim_hypothesis_no_production_callers():
    hits: list[str] = []
    for base in (ROOT / "4d_system", ROOT / "_ops"):
        for path in base.rglob("*.py"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.resolve() == DEF:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "claim_hypothesis" in text:
                hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits
