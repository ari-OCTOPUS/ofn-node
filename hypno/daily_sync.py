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


def sync_lab_results_to_rag(store: Store, results: list[dict]) -> int:
    """Turn each lab result into a RAG chunk, like daily notes.

    A lab result is a daily verdict, a decision decomposition, or a quiz
    outcome. Each becomes a short factual note the brain can recall later:
    "نتیجهٔ آزمایش ۲۰۲۶-۰۸-۰۷: حکم زرد، سهم بدن ۶۱٪".
    """
    import json
    added = 0
    for r in results:
        rid = r.get("id")
        source_url = f"local://lab-result/{rid}"
        if store.has_research_source(source_url):
            continue
        kind = r.get("kind", "")
        payload = r.get("payload") or {}
        day = ""
        # lab results have a created_at epoch; format it
        import time as _t
        ca = r.get("created_at") or 0
        if ca:
            day = _t.strftime("%Y-%m-%d", _t.gmtime(ca))
        # human-readable summary of the payload
        if kind == "daily":
            body = (f"آزمایش روزانه {day}: بدن {payload.get('b')}, "
                    f"خود {payload.get('c')}, ابرموجود {payload.get('x')} → "
                    f"حکم {payload.get('verdict', 'نامشخص')}.")
        elif kind == "decision":
            body = (f"تجزیهٔ تصمیم {day}: سهم بدن {payload.get('body_share')}, "
                    f"سهم خود {payload.get('self_share')}, "
                    f"سهم ابرموجود {payload.get('super_share')} → "
                    f"{payload.get('dominant', 'نامشخص')}.")
        elif kind == "quiz":
            body = (f"کوییز {day}: سناریو را {payload.get('verdict')} حدس زدم "
                    f"({'درست' if payload.get('correct') else 'غلط'}).")
        else:
            body = f"نتیجهٔ آزمایشگاه {day}."
        if len(body) < 40:
            body = body + f" — نتیجهٔ آزمایشگاه شخصی {day}."
        store.add_research(
            title=f"آزمایش {day}",
            text=body,
            source_url=source_url,
            source_type="lab_result",
            tags="math_models self_love_training خواب بدن تصمیم",
        )
        added += 1
    if added:
        store.rebuild_fts()
    return added


def main() -> None:
    cfg = load()
    db_path = os.path.join(cfg.state_dir, "hypno.sqlite")
    store = Store(db_path)

    # Notes from the last 36h — a little wider than 24h so a delayed run (the
    # timer has RandomizedDelaySec) still catches yesterday's notes.
    notes = store.recent_daily_notes(days=1.5)
    print(f"found {len(notes)} recent note(s)")
    added = sync_notes_to_rag(store, notes)
    print(f"synced {added} new note chunk(s) to RAG")

    # Lab results from the last 36h too.
    lab = store.recent_lab_results(days=1.5)
    print(f"found {len(lab)} recent lab result(s)")
    lab_added = sync_lab_results_to_rag(store, lab)
    print(f"synced {lab_added} new lab chunk(s) to RAG")

    reply = feed_brain(cfg, store, notes)
    if reply:
        print(f"brain reply: {reply[:120]}")


if __name__ == "__main__":
    main()
