# -*- coding: utf-8 -*-
"""تست‌های تولید صفحات ماشینی Obsidian — گیت ماشینی فاز ۹ (قطعیبودن)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "obsidian_sync"))

import obsidian_sync.gen_pages as g  # noqa: E402


def test_pages_generate_deterministically(tmp_path):
    orig = g.PAGES_DIR
    g.PAGES_DIR = tmp_path
    try:
        a = g.generate()
        b = g.generate()
        assert a == b
        names = list(a["pages"])
        assert set(names) == {"NOVELTY-ARCHIVE", "ECONOMY", "DOCTOR-REPORT",
                              "LAB-NOTEBOOK", "MUTATION-LEDGER", "RIGHTS-AND-LAWS",
                              "WEEKLY-CAPABILITY"}
        for name in names:
            body = (tmp_path / f"{name}.md").read_text("utf-8")
            assert body.startswith(f"# {name}")
            assert "machine-generated" in body
        assert (tmp_path / "MANIFEST.json").exists()
    finally:
        g.PAGES_DIR = orig


def test_second_run_identical_bytes(tmp_path):
    orig = g.PAGES_DIR
    g.PAGES_DIR = tmp_path
    try:
        g.generate()
        first = {p.name: p.read_bytes() for p in tmp_path.glob("*.md")}
        g.generate()
        second = {p.name: p.read_bytes() for p in tmp_path.glob("*.md")}
        assert first == second
    finally:
        g.PAGES_DIR = orig


def test_rights_page_only_ratified_sources():
    body = g._rights_laws_page()
    assert "PRE-0/CONSTITUTION.md" in body
    assert "DUAL-BRAIN-CONSTITUTION.md" in body
    assert "SELF-IMPROVEMENT-BOUNDARY.md" in body
    # قوانینِ پیشنهادیِ بدون رأی (LAW-01..20) نباید ادعا شوند
    assert "LAW-01" not in body
    assert "هیچ قانونی از سندِ بدونِ رأی مالک وارد نشده" in body


def test_mutation_page_lists_birth_and_gates():
    body = g._mutation_page()
    assert "b0dea5128a34aa95" in body
    assert "PROMOTE" in body
    assert "phase" in body.lower() or "P1" in body
