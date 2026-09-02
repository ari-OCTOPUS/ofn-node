# Lane LB tests — read-only round.
# Directive scenario numbers (1–15) cited per test.
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ofn.doctor.round import DoctorRound, SourceNotFoundError, tree_hash  # noqa: E402


def _make_vault(root: Path):
    """A small healthy synthetic vault: pointers exempt, refs resolve, no junk."""
    (root / "01-TRUTH").mkdir(parents=True)
    (root / "01-TRUTH" / "CURRENT-TRUTH.md").write_text(
        "# CURRENT-TRUTH\nRedirect → 99-ARCHIVE\\mirror-cleanup-20260902\n", encoding="utf-8")
    (root / "07 - Knowledge").mkdir()
    (root / "07 - Knowledge" / "note.md").write_text("# ok\n", encoding="utf-8")
    (root / "01-TRUTH" / "STATE.md").write_text(
        "ref `07 - Knowledge/note.md` and [[07 - Knowledge/note.md]]\n", encoding="utf-8")


def test_01_healthy_vault_yields_no_source_findings(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    _make_vault(vault)
    result = DoctorRound().run(vault)
    source_findings = [f for f in result.findings if f.id != "CONTRACT-GAPS"]
    assert source_findings == []
    assert result.stats["read_only_proven"] is True


def test_02_missing_source_root_fails_closed(tmp_path):
    with pytest.raises(SourceNotFoundError):
        DoctorRound().run(tmp_path / "does-not-exist")


def test_03_malformed_file_is_a_finding_not_a_crash(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "01-TRUTH").mkdir()
    (vault / "01-TRUTH" / "CURRENT-TRUTH.md").write_bytes(b"\xff\xfe\x00binary")
    result = DoctorRound().run(vault)
    ids = [f.id for f in result.findings]
    assert any(i.startswith("MALFORMED-") for i in ids)
    assert all(f.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL") for f in result.findings)


def test_04_unreadable_file_is_a_finding_not_a_crash(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    _make_vault(vault)
    locked = vault / "01-TRUTH" / "STATE.md"

    real_read_bytes = Path.read_bytes

    def guarded(self, *a, **kw):
        if self == locked:
            raise PermissionError("denied")
        return real_read_bytes(self, *a, **kw)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    result = DoctorRound().run(vault)
    assert any(f.id.startswith("PERMDENIED-") for f in result.findings)
    assert result.stats["read_only_proven"] is True


def test_05_findings_have_stable_ids_no_duplicates(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    _make_vault(vault)
    (vault / "01-TRUTH" / "STATE.md").write_text(
        "see `missing/a.md` and `missing/a.md` again\n", encoding="utf-8")
    r1 = DoctorRound().run(vault)
    r2 = DoctorRound().run(vault)
    ids1 = [f.id for f in r1.findings]
    ids2 = [f.id for f in r2.findings]
    assert len(ids1) == len(set(ids1))            # no duplicates within a run
    assert ids1 == ids2                           # identical rerun → identical ids


def test_09_10_round_never_touches_source_tree(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    _make_vault(vault)
    (vault / "01-TRUTH" / "STATE.md").write_text("see `gone/x.md`\n", encoding="utf-8")
    (vault / "debug-x.log").write_text("junk", encoding="utf-8")
    skip = {".pytest_cache", "__pycache__"}
    before = tree_hash(vault, skip)
    result = DoctorRound().run(vault)
    after = tree_hash(vault, skip)
    assert before == after                         # scenario 9: nothing changed
    assert result.changed_sources == []            # scenario 10: hashes before==after
    assert result.manifest_after == result.manifest_before
    assert len(result.findings) >= 3               # deadref + junk + contract-gaps


def test_mirror_relapse_is_detected(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "02 - Life OS").mkdir(parents=True)
    (vault / "02 - Life OS" / "CURRENT-TRUTH.md").write_text(
        "# full content-bearing mirror\n" + ("x" * 2000), encoding="utf-8")
    result = DoctorRound().run(vault)
    mirrors = [f for f in result.findings if f.category == "mirror"]
    assert len(mirrors) == 1
    assert mirrors[0].severity == "HIGH"
    assert mirrors[0].evidence_sha256 == hashlib.sha256(
        (vault / "02 - Life OS" / "CURRENT-TRUTH.md").read_bytes()).hexdigest()


def test_canonical_and_machine_lineage_mirrors_are_exempt(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    for rel in ("06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md",
                "OCTOPUS/CURRENT-TRUTH.md"):
        p = vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("legitimate content " * 200, encoding="utf-8")
    result = DoctorRound().run(vault)
    assert [f for f in result.findings if f.category == "mirror"] == []
