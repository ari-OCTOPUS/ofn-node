#!/usr/bin/env python3
"""obsidian_sync — به‌روزرسانیِ safe Obsidian notes.

قواعد:
  - محتوای دستی مالک را overwrite نکن
  - note‌های auto-generated با marker مشخص شوند
  - فقط بین <!-- OCTOPUS-AUTO-START --> ... <!-- OCTOPUS-AUTO-END --> update کن
  - اگر marker نیست، append امن با timestamp
  - secrets/PII redacted
"""
from __future__ import annotations
import sys
import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import intel_spine

START_MARKER = "<!-- OCTOPUS-AUTO-START -->"
END_MARKER = "<!-- OCTOPUS-AUTO-END -->"


def _now_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_update_note(note_path: Path, content: str, section_name: str = "auto") -> bool:
    """یک Obsidian note را safe update کن.

    اگر note موجود است و marker دارد: فقط بین marker‌ها replace.
    اگر note موجود است ولی marker ندارد: append.
    اگر note موجود نیست: بساز.
    """
    try:
        note_path = Path(note_path)
        note_path.parent.mkdir(parents=True, exist_ok=True)

        block = f"{START_MARKER}\n> auto-generated: {_now_str()}\n\n{content}\n\n{END_MARKER}"

        if note_path.exists():
            existing = note_path.read_text("utf-8")
            if START_MARKER in existing and END_MARKER in existing:
                # replace between markers
                import re
                pattern = re.compile(
                    re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
                    re.DOTALL)
                updated = pattern.sub(block, existing, count=1)
                note_path.write_text(updated, "utf-8")
                return True
            else:
                # append (no overwrite)
                append_text = f"\n\n{block}\n"
                note_path.write_text(existing + append_text, "utf-8")
                return True
        else:
            # create new
            header = f"---\ntype: octopus-auto\nsection: {section_name}\nupdated: {_now_str()}\n---\n\n"
            note_path.write_text(header + block + "\n", "utf-8")
            return True
    except Exception:
        return False


def sync_truth_note(vault_path: Path, truth_data: dict) -> bool:
    """CURRENT-TRUTH.md را به‌روز کن."""
    content = "## Current Truth\n\n"
    for k, v in truth_data.items():
        content += f"- **{k}:** {v}\n"
    return safe_update_note(
        Path(vault_path) / "Octopus" / "CURRENT-TRUTH.md",
        content, section_name="current-truth")


def sync_p0_note(vault_path: Path, p0_items: list[dict]) -> bool:
    """P0-Shortlist.md را به‌روز کن."""
    content = "## P0 Shortlist\n\n"
    for item in p0_items:
        content += f"- **{item.get('id', '?')}:** {item.get('title', '?')} — `{item.get('status', '?')}`\n"
    return safe_update_note(
        Path(vault_path) / "Octopus" / "Risks" / "P0-Shortlist.md",
        content, section_name="p0-shortlist")


def sync_memory_model_note(vault_path: Path) -> bool:
    """Memory-Model.md را به‌روز کن با intel_spine schema."""
    content = """## Memory Model (intel_spine)

### Layers
- L0: Raw Event Intake
- L1: Normalization + Correlation
- L2: Safety/Governance Gate (classification)
- L3: Working Memory (session-local)
- L4: Episodic Memory (events.jsonl, interactions.jsonl)
- L5: Semantic/Factual (facts.jsonl)
- L6: Beliefs (beliefs.jsonl)
- L7: Decisions (decisions.jsonl)
- L8: Proposals shadow (proposals.jsonl)

### Schemas

**Event:**
```json
{"event_id":"uuid","ts":"ISO-8601","source":"telegram|webapp|owner|agent","direction":"in|out","actor_ref":"hash","text_redacted":"<redacted:hash>","d_level":"D0-D6","safety_verdict":"allow|deny|hold"}
```

**Fact:**
```json
{"fact_id":"uuid","claim":"","evidence":["file:line"],"confidence":0.0,"status":"active|stale"}
```

### State
- Path: `_ops/state/intel_spine/*.jsonl`
- Flag: `OCTOPUS_INTERACTION_LOG=1` (default off)
- Append-only, redacted, no raw PII
"""
    return safe_update_note(
        Path(vault_path) / "Octopus" / "Memory" / "Memory-Model.md",
        content, section_name="memory-model")
