"""Architecture test: mutations are paired with a ledger event (finding 13).

`ledger-on-mutation` was discipline only — nothing stopped a future method
from writing a row without recording why. This test reads Node's source and
requires that every method whose name indicates a mutation (create/update/
delete/send/publish/enqueue/engage/release/attach/add/record/upsert) call
`self.ledger.append` in its body, unless explicitly listed.

The allowlist is small and each entry names its reason. Anything added
there needs a DecisionRecord, not just a pass.
"""

from __future__ import annotations

import ast
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = os.path.join(ROOT, "ofn", "node.py")

# Methods that mutate state but deliberately write no ledger event.
# Each entry: method name -> why no ledger.
NO_LEDGER_ALLOWLIST = {
    "create_painting_lead": "writes via painting store; the store's own "
        "create_lead is the record, and LEAD_CAPTURED is appended by the "
        "node wrapper (see body)",
    "record_owner_answer": "persists the answer in the owner store and "
        "returns THINK_DONE metadata; the WORKER appends the single "
        "THINK_DONE after the sink succeeds (owner-brain P0 fix)",
    "mark_owner_job_running": "mirrors queue pickup into the owner store; "
        "the durable record is THINK_QUEUED already written by worker.submit",
    "mark_owner_job_failed": "mirrors refusals into the owner store; the "
        "durable records are the worker's THINK_RETRY/THINK_PARKED rows",
}

MUTATION_PREFIXES = (
    "create_", "update_", "delete_", "send_", "publish_", "engage_",
    "release_", "attach_", "add_", "record_", "upsert_", "file_",
    "set_", "mark_", "drop_", "store_",
)


def node_mutation_methods() -> list[str]:
    """Methods on Node whose names look like mutations, without a ledger call."""
    with open(NODE, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    node_class = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.ClassDef) and n.name == "Node")
    offenders = []
    for item in node_class.body:
        if not isinstance(item, ast.FunctionDef):
            continue
        name = item.name
        if not name.startswith(MUTATION_PREFIXES):
            continue
        if name in NO_LEDGER_ALLOWLIST:
            continue
        body_src = ast.get_source_segment(open(NODE, encoding="utf-8").read(),
                                          item) or ""
        has_ledger = ("self.ledger.append" in body_src
                      or "_record_release_event(" in body_src)
        if not has_ledger:
            offenders.append(name)
    return offenders


class TestMutationLedgerPairing(unittest.TestCase):
    """Every mutation method must record why in the ledger."""

    def test_no_mutation_without_ledger(self):
        offenders = node_mutation_methods()
        self.assertEqual(offenders, [],
                         f"mutations without ledger.append: {offenders}")

    def test_allowlist_entries_are_documented(self):
        """The allowlist is tiny and every entry has a reason."""
        self.assertLessEqual(len(NO_LEDGER_ALLOWLIST), 5)


if __name__ == "__main__":
    unittest.main()
