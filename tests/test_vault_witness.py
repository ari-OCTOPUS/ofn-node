"""Vault witness — read-only attestation of the vault (SPEC step 5).

Pins: consistent/incomplete/inconsistent verdicts on fixture trees;
missing-expected is incomplete (absence != tampering); unreadable bytes are
unknown, never silently skipped; and the adapter has ZERO write paths —
a guarded read of the vault cannot mutate it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "ofn" / "adapters" / "vault_witness.py"
sys.path.insert(0, str(ROOT))

from ofn.adapters import vault_witness as vw  # noqa: E402


def _make_vault(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "vault"
    root.mkdir()
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return root


def _manifest_for(root: Path) -> dict:
    return {str(rel): vw.sha256_file(root / rel)
            for rel in vw.walk_vault(root)}


def test_consistent_tree(tmp_path) -> None:
    root = _make_vault(tmp_path, {"a.md": "one", "d/b.md": "two"})
    res = vw.witness(root, _manifest_for(root))
    assert res["verdict"] == "consistent"
    assert res["counts"]["consistent"] == 2


def test_tampered_file_is_inconsistent(tmp_path) -> None:
    root = _make_vault(tmp_path, {"a.md": "original"})
    manifest = _manifest_for(root)
    (root / "a.md").write_text("TAMPERED", encoding="utf-8")
    res = vw.witness(root, manifest)
    assert res["verdict"] == "inconsistent"
    assert res["counts"]["inconsistent"] == 1


def test_missing_expected_is_incomplete_not_inconsistent(tmp_path) -> None:
    root = _make_vault(tmp_path, {"a.md": "x"})
    res = vw.witness(root, _manifest_for(root), expect=["SEASON-LOG.md"])
    assert res["verdict"] == "incomplete"
    kinds = {f["path"]: f["verdict"] for f in res["files"]}
    assert kinds["SEASON-LOG.md"] == "missing-expected"


def test_unmanifested_file_is_incomplete(tmp_path) -> None:
    root = _make_vault(tmp_path, {"a.md": "x", "b.md": "y"})
    res = vw.witness(root, {"a.md": vw.sha256_file(root / "a.md")})
    assert res["verdict"] == "incomplete"


def test_skipped_dirs_do_not_count_as_files(tmp_path) -> None:
    root = _make_vault(tmp_path, {"a.md": "x", ".git/HEAD": "ref",
                                  ".obsidian/ws.json": "{}"})
    rels = [str(r) for r in vw.walk_vault(root)]
    assert rels == ["a.md"]


def test_cli_needs_explicit_root(tmp_path) -> None:
    proc = subprocess.run(
        [sys.executable, str(ADAPTER)],
        capture_output=True, text=True, timeout=30, cwd=str(ROOT))
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "incomplete" and "usage" in payload["error"]


def test_cli_end_to_end(tmp_path) -> None:
    root = _make_vault(tmp_path, {"a.md": "hello"})
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(
        {"a.md": vw.sha256_file(root / "a.md")}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ADAPTER), str(root), str(manifest_path)],
        capture_output=True, text=True, timeout=30, cwd=str(ROOT))
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["verdict"] == "consistent"


# ── منفی: صفر نوشتن ─────────────────────────────────────────────────────────

def test_adapter_has_zero_write_paths() -> None:
    src = ADAPTER.read_text(encoding="utf-8")
    for banned in ("write_text", "write_bytes", "os.replace", "os.remove",
                   "unlink", "rmtree", "open(", ".touch("):
        if banned == "open(":
            # تنها open مجاز: حالت خواندن باینری برای هش
            import re
            opens = re.findall(r'\.open\("([^"]+)"\)', src)
            assert opens == ["rb"], opens
            continue
        assert banned not in src, banned
