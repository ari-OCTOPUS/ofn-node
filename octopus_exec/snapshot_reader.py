"""Explicit bounded local inputs. No recursive discovery and no command execution."""
import hashlib
from pathlib import Path
from shadow_homeostasis.canonical import strict_json

MAX_FILE = 1024 * 1024
MAX_FILES = 32


def no_reparse(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("reparse/symlink rejected: " + str(part))
    return path


def safe_path(root, relative):
    root = no_reparse(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or rel.drive or ".." in rel.parts or ":" in str(relative):
        raise ValueError("path escape rejected")
    target = no_reparse(root / rel)
    if not target.resolve().is_relative_to(root):
        raise ValueError("path escape rejected")
    return target


def read_json(path, max_bytes=MAX_FILE):
    path = no_reparse(path)
    with path.open("rb") as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("input byte budget exceeded")
    return strict_json(raw), hashlib.sha256(raw).hexdigest()


def load_inputs(root):
    manifest, manifest_hash = read_json(safe_path(root, "manifest.json"))
    if manifest.get("schema") != "octopus-input-manifest.v1":
        raise ValueError("input manifest schema")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
        raise ValueError("explicit bounded input list required")
    paths, cases, identities = set(), [], set()
    for entry in entries:
        path = safe_path(root, entry["path"])
        if str(path).lower() in paths:
            raise ValueError("duplicate input path")
        paths.add(str(path).lower())
        payload, byte_hash = read_json(path)
        if byte_hash != entry["sha256"]:
            raise ValueError("input hash mismatch: " + entry["path"])
        if not isinstance(payload, list) or len(payload) > 32:
            raise ValueError("bounded case array required")
        for case in payload:
            if not isinstance(case.get("case_id"), str):
                raise ValueError("case identity required")
            identity = case["case_id"].casefold()
            if identity in identities:
                raise ValueError("duplicate case identity")
            identities.add(identity)
            cases.append(case)
    if len(cases) > 128:
        raise ValueError("case count budget exceeded")
    return manifest, manifest_hash, sorted(cases, key=lambda c: c["case_id"])
