"""vault_witness — آداپتور فقط-خواندنِ والت (OCTOPUS-AUTONOMY-SPEC قدم ۵).

الت (Obsidian) را از بیرون گواهی می‌کند: SHA فایل‌ها، مقایسه با مانیفستِ
رسیدها، و حکم consistent / incomplete / inconsistent — **هیچ نوشتنی روی
والت از سمت کد**. این دقیقاً همان الگویی است که WAL را WITNESS_A کرد:
رسیدِ روی‌دیسک در برابر عددِ ادعاشده، با فرمانِ تکرارپذیر.

قواعد:
  · root صریح می‌خواهد (پیش‌فرض نداریم — التِ اشتباه گواهی نگیرد)
  · فایلِ ناخوانا = UNKNOWN، هرگز skip بی‌صدا
  · موردِ انتظارِ غایب = incomplete (نه inconsistent — غیبت ≠ تحریف)
  · بایت‌های متفاوت با مانیفست = inconsistent (درجهٔ اول)
  · هیچ مسیر نوشتن — تستِ source-scan قفلش می‌کند
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "octopus.vault-witness.v1"

SKIP_DIRS = {".git", ".obsidian", "__pycache__", "node_modules", ".tmp-test",
             ".tmp-test-run"}
MAX_FILES = 20000  # سقفِ صرف‌جویی — بیشتر از این = سنجش ناقص، صادق گزارش شود


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def walk_vault(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        out.append(rel)
        if len(out) >= MAX_FILES:
            break
    return out


def witness(
    root: Path,
    manifest: dict | None = None,
    expect: list[str] | None = None,
) -> dict:
    """مقایسهٔ درخت با مانیفست {relpath: sha256}.

    expect: فایل‌هایی که حضورشان انتظار می‌رود (غیبت = incomplete).
    """
    if manifest is None:
        manifest = {}
    if not root.is_dir():
        return {"schema": SCHEMA, "verdict": "incomplete",
                "detail": f"root is not a directory: {root}",
                "files": []}
    rels = walk_vault(root)
    truncated = len(rels) >= MAX_FILES
    files: list[dict] = []
    consistent = incomplete = inconsistent = unknown = 0
    for rel in rels:
        sha = sha256_file(root / rel)
        entry = {"path": str(rel)}
        if sha is None:
            entry["verdict"] = "unknown"
            unknown += 1
        else:
            entry["sha256"] = sha
            want = manifest.get(str(rel))
            if want is None:
                entry["verdict"] = "unmanifested"  # درخت دارد، مانیفست نه
                incomplete += 1
            elif want == sha:
                entry["verdict"] = "consistent"
                consistent += 1
            else:
                entry["verdict"] = "inconsistent"
                inconsistent += 1
        files.append(entry)
    for rel in (expect or []):
        if rel not in {str(r) for r in rels}:
            files.append({"path": rel, "verdict": "missing-expected"})
            incomplete += 1
    if inconsistent:
        verdict = "inconsistent"
    elif incomplete or unknown or truncated:
        verdict = "incomplete"
    else:
        verdict = "consistent"
    return {
        "schema": SCHEMA,
        "root": str(root),
        "verdict": verdict,
        "counts": {"consistent": consistent, "inconsistent": inconsistent,
                   "incomplete": incomplete, "unknown": unknown,
                   "truncated": truncated},
        "files": files,
    }


def load_manifest(path: Path) -> dict:
    """مانیفستِ رسیده: JSON سادهٔ {relpath: sha256}."""
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) < 1:
        print(json.dumps({"schema": SCHEMA, "error":
                          "usage: vault_witness.py ROOT [MANIFEST.json]",
                          "verdict": "incomplete"}, ensure_ascii=False))
        return 2
    root = Path(argv[0])
    manifest = load_manifest(Path(argv[1])) if len(argv) > 1 else {}
    print(json.dumps(witness(root, manifest), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
