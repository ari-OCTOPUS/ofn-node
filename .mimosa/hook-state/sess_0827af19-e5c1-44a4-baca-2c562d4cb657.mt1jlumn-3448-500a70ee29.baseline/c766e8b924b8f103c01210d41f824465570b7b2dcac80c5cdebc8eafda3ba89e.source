"""test_close_ipred_dead_import_20260816 — VOTE B قفل، نه سیم TCB.

SETTINGS_ANCHORS در verifier import می‌شود و در run() مصرف نمی‌شود.
ثبت در run_all نشده (WORKLOCK).
"""
import ast
from pathlib import Path

SRC = (
    Path(__file__).resolve().parents[2]
    / "4d_system"
    / "agents"
    / "verifier.py"
)


def test_settings_anchors_imported_and_unused_in_run():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "config.settings":
            for alias in node.names:
                if alias.name == "ANCHORS" and alias.asname == "SETTINGS_ANCHORS":
                    imported = True
    assert imported, "import SETTINGS_ANCHORS باید بماند (قفل مردگی، نه حذف)"

    run_fn = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "VerifierAgent":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "run":
                    run_fn = item
    assert run_fn is not None
    used = any(
        isinstance(n, ast.Name) and n.id == "SETTINGS_ANCHORS"
        for n in ast.walk(run_fn)
    )
    assert used is False, "سیم I_pred به run() بدون رأی VOTE B ممنوع است"
