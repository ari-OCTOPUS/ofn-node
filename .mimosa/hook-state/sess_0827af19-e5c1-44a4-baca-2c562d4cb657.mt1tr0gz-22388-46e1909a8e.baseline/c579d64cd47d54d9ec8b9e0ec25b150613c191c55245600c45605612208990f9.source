# -*- coding: utf-8 -*-
"""تست clade_ledger — از سنتز شورا: parent + descendants_accepted + CMP."""
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

from organs.clade_ledger import CladeLedger  # noqa: E402


def test_propose_and_lineage():
    c = CladeLedger()
    root = c.propose(None, "new_module", "knowledge_afferent v1", "C2", "no events")
    child = c.propose(root.node_id, "patch", "schema v3", "C14", "quality enum fails")
    grand = c.propose(child.node_id, "flag", "hook default off", "C3", "no-op when off")
    assert c.lineage(grand.node_id) == [grand.node_id, child.node_id, root.node_id]
    assert root.parent_id is None


def test_apply_increments_descendants():
    c = CladeLedger()
    root = c.propose(None, "new_module", "root", "R", "f")
    c1 = c.propose(root.node_id, "patch", "child1", "R1", "f1")
    c2 = c.propose(root.node_id, "patch", "child2", "R2", "f2")
    c.apply(c1.node_id, effect_metric="ratio_margin", effect_value=0.05)
    assert c._nodes[root.node_id].descendants_accepted == 1
    assert c._nodes[c1.node_id].state == "APPLIED"


def test_reject_and_revert():
    c = CladeLedger()
    root = c.propose(None, "config", "root", "R", "f")
    r1 = c.propose(root.node_id, "patch", "rejected child", "R1", "f1")
    r2 = c.propose(root.node_id, "patch", "reverted child", "R2", "f2")
    c.reject(r1.node_id, "falsifier hit")
    c.apply(r2.node_id, effect_metric="x", effect_value=1.0)
    c.revert(r2.node_id, reverted_by="rollback_flag")
    assert c._nodes[r1.node_id].state == "REJECTED"
    assert c._nodes[r2.node_id].state == "REVERTED"


def test_cmp():
    c = CladeLedger()
    root = c.propose(None, "new_module", "root", "R", "f")
    for i in range(4):
        ch = c.propose(root.node_id, "patch", f"ch{i}", f"R{i}", f"f{i}")
        if i < 3:
            c.apply(ch.node_id)
        else:
            c.reject(ch.node_id)
    assert c.cmp(root.node_id) == 0.75  # 3/4 accepted


def test_idempotent_propose():
    c = CladeLedger()
    a = c.propose(None, "patch", "same", "R", "f")
    b = c.propose(None, "patch", "same", "R", "f")
    assert a.node_id == b.node_id  # same hash → same node


def test_stats():
    c = CladeLedger()
    r = c.propose(None, "new_module", "root", "R", "f")
    c.apply(r.node_id, effect_metric="m", effect_value=1.0)
    s = c.stats()
    assert s["total_nodes"] == 1 and s["roots"] == 1
    assert s["by_state"]["APPLIED"] == 1
