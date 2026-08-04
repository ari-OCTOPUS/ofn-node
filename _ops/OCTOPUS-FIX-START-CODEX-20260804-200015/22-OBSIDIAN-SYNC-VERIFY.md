# 22 — Obsidian sync verification

Read `_ops/intel_spine/obsidian_sync.py` in full (124 lines).

## Marker-based safe update, confirmed from source

`safe_update_note(note_path, content, section_name)`:
- If the note exists **and** contains both `<!-- OCTOPUS-AUTO-START -->` and
  `<!-- OCTOPUS-AUTO-END -->`: replaces **only** the text between those markers via a
  non-greedy regex (`re.DOTALL`, `count=1`) — everything outside the markers (i.e. any
  owner-hand-written content) is left byte-for-byte untouched.
- If the note exists but has **no** markers: appends the new auto-block at the end —
  **never overwrites** existing content.
- If the note doesn't exist: creates it fresh with a frontmatter header.
- Any exception → returns `False`, never raises, never partially writes (the write itself is
  a single `Path.write_text` call — either the whole new content lands or the exception is
  caught before any write happens).

This independently matches — and is required by — this very vault's own constitution
(`agent-prompts/_PROJECT_INSTRUCTIONS.md` §7: "به نوت انسانی فقط append یا انتقال؛ هرگز
بازنویسی مخرب" — never destructively rewrite a human note). Good cross-check: the code was
built compliant with the vault's own governance rules independent of this verification run.

## Test confirmation

`test_adapters_obsidian.py`, obsidian-specific checks (of 15/15 total pass): truth note
created/exists, memory note created/exists, **idempotent** (repeated calls produce exactly
one marker block, not a growing pile of duplicate blocks), updated content actually reflects
the new call, **manual content preserved + auto content appended** (the strongest test here
— it seeds a note with hand-written text first, then calls `safe_update_note`, then asserts
both the original hand-written string AND the new auto content are present), and no raw
`chat_id` value leaks into the note text.

## Status: PASS — marker-based update is real, tested, and independently confirmed from
source, not just from the test's own self-report.
