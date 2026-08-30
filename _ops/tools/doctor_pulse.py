#!/usr/bin/env python3
"""Read-only doctor pulse — contracts in OCTOPUS-DOCTOR/90-_meta/state."""
import json
from pathlib import Path

ROOT = Path("F:/backup/OCTOPUS-DOCTOR/90-_meta/state")
STATES = ("proposed", "running", "awaiting-merge", "merged", "rejected", "failed")


def read_json(name):
    path = ROOT / name
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def read_jsonl(name):
    path = ROOT / name
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def mission_counts(missions):
    counts = {state: 0 for state in STATES}
    for mission in missions:
        counts[mission["state"]] += 1
    return counts


def pending_count(outbox, inbox):
    out_keys = {(item["mission_id"], item["gate"]) for item in outbox}
    in_keys = {(item["mission_id"], item["gate"]) for item in inbox}
    return len(out_keys - in_keys)


def main():
    missions = read_json("missions.json")
    outbox = read_jsonl("tg-outbox.jsonl")
    inbox = read_jsonl("tg-inbox.jsonl")
    result = {
        "missions_by_state": None if missions is None else mission_counts(missions),
        "pending_cards": None if outbox is None or inbox is None else pending_count(outbox, inbox),
        "quota": read_json("fugu-quota.json"),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
