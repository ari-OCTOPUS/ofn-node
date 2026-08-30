"""VaultScanner — read-only markdown analysis on a fixture vault (no real vault)."""

import pytest

pytestmark = pytest.mark.l1

from nbb_cp.adapters.vault.scanner import VaultScanner


def _make_vault(tmp_path):
    def w(rel, text):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    w("03 - Projects/ziman.md",
      "---\ntype: project\nrisk_level: medium\n---\nGallery plan [[color-theory]] and [[armin]] #gallery\n")
    w("07 - Knowledge/color-theory.md", "---\ntype: knowledge\n---\nNotes on color.\n")
    w("07 - Knowledge/isolated.md", "---\ntype: knowledge\n---\nNo links here.\n")
    w("09 - People/armin.md", "---\ntype: person\nsensitivity: restricted\n---\nProfile of [[ziman]].\n")
    return tmp_path


def _add_crypto_note(root):
    p = root / "03 - Projects/Crypto - etoro/trade.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\ntype: project\n---\nSee [[color-theory]] #trade\n", encoding="utf-8")


class TestVaultScanner:
    def test_excludes_restricted_by_default(self, tmp_path):
        result = VaultScanner(_make_vault(tmp_path)).scan()
        titles = {n.title for n in result.notes}
        assert "armin" not in titles
        assert {"ziman", "color-theory", "isolated"} <= titles
        assert "09 - People" in result.excluded_folders

    def test_detects_orphan(self, tmp_path):
        result = VaultScanner(_make_vault(tmp_path)).scan()
        assert "isolated" in result.orphans
        assert "color-theory" not in result.orphans

    def test_infers_cross_folder_channel(self, tmp_path):
        result = VaultScanner(_make_vault(tmp_path)).scan()
        chans = {(c.from_folder, c.to_folder): c for c in result.channels}
        assert ("03 - Projects", "07 - Knowledge") in chans
        assert "ziman" in chans[("03 - Projects", "07 - Knowledge")].evidence
        assert ("03 - Projects", "09 - People") not in chans

    def test_include_restricted_surfaces_people_channel(self, tmp_path):
        result = VaultScanner(_make_vault(tmp_path), include_restricted=True).scan()
        chans = {(c.from_folder, c.to_folder): c for c in result.channels}
        assert ("03 - Projects", "09 - People") in chans
        assert chans[("03 - Projects", "09 - People")].risk_level == "high"

    def test_extracts_tags(self, tmp_path):
        result = VaultScanner(_make_vault(tmp_path)).scan()
        ziman = next(n for n in result.notes if n.title == "ziman")
        assert "gallery" in ziman.tags

    def test_scan_writes_nothing(self, tmp_path):
        root = _make_vault(tmp_path)
        before = {p.as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        VaultScanner(root).scan()
        after = {p.as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        assert before == after  # same files AND identical content

    def test_channel_map_renders_actual_data(self, tmp_path):
        result = VaultScanner(_make_vault(tmp_path)).scan()
        md = result.to_channel_map_md()
        assert "Inferred channels" in md and "Orphans" in md
        # Not just the headers: the real orphan, a real channel id, and its evidence appear.
        assert "isolated" in md
        assert result.channels[0].channel_id in md
        assert "ziman" in md

    def test_crypto_note_makes_channel_critical(self, tmp_path):
        # A crypto note collapses to folder '03 - Projects'; risk must still read
        # 'critical' from the full path, not 'medium' from the collapsed folder.
        root = _make_vault(tmp_path)
        _add_crypto_note(root)
        result = VaultScanner(root, include_restricted=True).scan()
        assert any(c.risk_level == "critical" for c in result.channels)

    def test_nested_restricted_excluded_by_default(self, tmp_path):
        root = _make_vault(tmp_path)
        _add_crypto_note(root)
        result = VaultScanner(root).scan()  # crypto subfolder excluded by default
        assert not any(n.path.startswith("03 - Projects/Crypto - etoro") for n in result.notes)

    def test_symlink_into_restricted_is_excluded(self, tmp_path):
        root = _make_vault(tmp_path)
        real = root / "03 - Projects/Crypto - etoro/secret.md"
        real.parent.mkdir(parents=True, exist_ok=True)
        real.write_text("---\ntype: project\n---\ntop secret\n", encoding="utf-8")
        link = root / "00 - Inbox/shortcut.md"
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(real)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks not permitted on this platform")
        result = VaultScanner(root).scan()  # default excludes crypto
        # The symlink resolves into the excluded folder, so it must NOT be scanned.
        assert not any(n.title in ("secret", "shortcut") for n in result.notes)
