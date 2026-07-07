"""خواندنِ read-only از vault برای دادنِ زمینه به تولیدکنندهٔ محتوا.
این ماژول هیچ‌چیز نمی‌نویسد — فقط می‌خواند."""
from pathlib import Path


def read_vault_context(vault_dir, notes) -> str:
    vault_dir = Path(vault_dir)
    parts = []
    for n in notes or []:
        p = vault_dir / n
        try:
            if p.exists() and p.is_file():
                parts.append(f"### {n}\n{p.read_text(encoding='utf-8').strip()}")
        except Exception:  # noqa: BLE001
            continue
    return "\n\n".join(parts).strip()
