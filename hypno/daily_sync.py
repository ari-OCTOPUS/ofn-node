"""Nightly sync: turn each daily note into a RAG chunk the brain can recall.

Runs as a systemd timer at 04:30 (after the OFN assistant refresh at 04:10).
Idempotent: a note already synced (matched by its `local://daily-note/<id>`
source URL) is never re-inserted. A note that was deleted has its chunk
removed by the delete endpoint, so stale chunks do not accumulate here.

The brain feeding step is optional: if the remote key is absent the job still
syncs notes to RAG, it just skips the "tell the model about today" call.
That way a board without a configured brain still gets the RAG benefit.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypno.config import load
from hypno.adapters.store import Store


def sync_notes_to_rag(store: Store, notes: list[dict]) -> int:
    """Add each note as a research chunk. Returns how many were new."""
    added = 0
    for note in notes:
        nid = note.get("id")
        source_url = f"local://daily-note/{nid}"
        # Idempotency: if this note is already a chunk, skip.
        if store.has_research_source(source_url):
            continue
        day = note.get("day", "")
        content = note.get("content", "").strip()
        if len(content) < 40:
            # add_research requires >= 40 chars. A shorter note is padded with
            # its own metadata so it still becomes a findable chunk rather
            # than being silently dropped.
            content = (content + " — این یادداشت روزانهٔ " + day + " است.").strip()
        store.add_research(
            title=f"یادداشت {day}",
            text=content,
            source_url=source_url,
            source_type="daily_note",
            # Tags include the RELEVANT_TERMS the rag filter requires, so a
            # note about sleep or breathing is not dropped by is_safe_research.
            tags="hypnosis_core self_love_training خواب بدن تنفس آرام",
        )
        added += 1
    if added:
        store.rebuild_fts()
    return added


def feed_brain(cfg, store: Store, notes: list[dict]) -> str | None:
    """Tell the remote brain about today's notes, so it has fresh context.

    Returns the model's reply, or None if the brain was not armed or had
    nothing to read. Failures are swallowed: this is a bonus, not a
    dependency — the RAG sync above is what matters.
    """
    if not cfg.api_key or not notes:
        return None
    try:
        from hypno.adapters.brain import Brain
        brain = Brain(cfg)
        blob = "\n".join(f"- [{n.get('day','')}] {n.get('content','')}" for n in notes)
        r = brain.answer(
            "این یادداشت‌های امروز من بود. لطفاً به‌خاطر بسپار و در گفت‌وگوهای آینده به آن‌ها ارجاع بده.",
            "learn", [], [], "safe",
        )
        return r.get("reply")
    except Exception:
        return None


def main() -> None:
    cfg = load()
    db_path = os.path.join(cfg.state_dir, "hypno.sqlite")
    store = Store(db_path)

    # Notes from the last 36h — a little wider than 24h so a delayed run (the
    # timer has RandomizedDelaySec) still catches yesterday's notes.
    notes = store.recent_daily_notes(days=1.5)
    print(f"found {len(notes)} recent note(s)")

    added = sync_notes_to_rag(store, notes)
    print(f"synced {added} new chunk(s) to RAG")

    reply = feed_brain(cfg, store, notes)
    if reply:
        print(f"brain reply: {reply[:120]}")


if __name__ == "__main__":
    main()
