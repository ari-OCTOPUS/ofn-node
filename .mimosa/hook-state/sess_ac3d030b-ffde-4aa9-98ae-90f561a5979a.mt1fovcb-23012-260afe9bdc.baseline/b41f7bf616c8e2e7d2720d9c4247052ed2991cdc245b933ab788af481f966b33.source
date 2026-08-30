"""Read-only vault scan CLI (Phase 2). Prints the channel map; writes NOTHING to
the vault. Restricted folders are excluded unless --include-restricted is passed.

    python scripts/scan_vault.py "D:/path/to/ObsidianVault"
    python scripts/scan_vault.py <vault> --include-restricted   # opt in explicitly
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nbb_cp.adapters.vault.scanner import VaultScanner  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    root = argv[0]
    include_restricted = "--include-restricted" in argv[1:]
    if not Path(root).is_dir():
        print(f"not a directory: {root}")
        return 2
    result = VaultScanner(root, include_restricted=include_restricted).scan()
    print(result.to_channel_map_md())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
