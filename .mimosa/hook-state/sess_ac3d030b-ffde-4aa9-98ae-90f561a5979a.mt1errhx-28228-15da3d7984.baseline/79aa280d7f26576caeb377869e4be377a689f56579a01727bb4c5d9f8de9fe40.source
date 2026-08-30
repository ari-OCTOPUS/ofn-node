#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clade_ledger.py — از سنتز شورا (نوت ۷۲): درخت تکامل با parent + descendants_accepted.

هر تصمیم خودتغییری یک node در درخت است. CMP (Collective Mutation Performance)
بعداً محاسبه می‌شود؛ ثبت parent از روز اول الزامی است."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class CladeNode:
    node_id: str
    parent_id: str | None        # None = root
    change_type: str              # patch | new_module | flag | config | rollback
    description: str
    pre_reg_id: str              # کارت/پیش‌ثبت مرتبط
    falsifier: str               # شرط رد
    created_at: float
    state: str = "PROPOSED"      # PROPOSED | APPLIED | REJECTED | REVERTED
    descendants_accepted: int = 0  # CMP شمارش — بعداً محاسبه
    effect_metric: str = ""      # متریک اثر (مثلاً "ratio_margin")
    effect_value: float | None = None
    reverted_by: str | None = None


class CladeLedger:
    """append-only · idempotent · بدون حذف."""

    def __init__(self, path: Path | None = None):
        self.path = path
        self._nodes: dict[str, CladeNode] = {}
        if path and path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    d = json.loads(line)
                    self._nodes[d["node_id"]] = CladeNode(**d)

    def propose(self, parent_id: str | None, change_type: str,
                description: str, pre_reg_id: str, falsifier: str) -> CladeNode:
        nid = f"clade-{hashlib.sha256(f'{parent_id}|{change_type}|{description}'.encode()).hexdigest()[:12]}"
        if nid in self._nodes:
            return self._nodes[nid]  # idempotent
        node = CladeNode(
            node_id=nid, parent_id=parent_id, change_type=change_type,
            description=description, pre_reg_id=pre_reg_id,
            falsifier=falsifier, created_at=time.time())
        self._nodes[nid] = node
        self._save()
        return node

    def apply(self, node_id: str, effect_metric: str = "",
              effect_value: float | None = None) -> bool:
        n = self._nodes.get(node_id)
        if n and n.state == "PROPOSED":
            n.state = "APPLIED"
            n.effect_metric = effect_metric
            n.effect_value = effect_value
            self._save()
            # parent's descendants_accepted++
            if n.parent_id and n.parent_id in self._nodes:
                self._nodes[n.parent_id].descendants_accepted += 1
                self._save()
            return True
        return False

    def reject(self, node_id: str, reason: str = "") -> bool:
        n = self._nodes.get(node_id)
        if n and n.state == "PROPOSED":
            n.state = "REJECTED"
            self._save()
            return True
        return False

    def revert(self, node_id: str, reverted_by: str) -> bool:
        n = self._nodes.get(node_id)
        if n and n.state == "APPLIED":
            n.state = "REVERTED"
            n.reverted_by = reverted_by
            self._save()
            return True
        return False

    def lineage(self, node_id: str) -> list[str]:
        """زنجیرهٔ parent تا root."""
        chain = []
        current = self._nodes.get(node_id)
        while current:
            chain.append(current.node_id)
            current = self._nodes.get(current.parent_id) if current.parent_id else None
        return chain

    def cmp(self, node_id: str) -> float | None:
        """Collective Mutation Performance: نسبت فرزندان accepted به کل فرزندان."""
        n = self._nodes.get(node_id)
        if not n:
            return None
        children = [c for c in self._nodes.values() if c.parent_id == node_id]
        if not children:
            return None
        accepted = sum(1 for c in children if c.state in ("APPLIED",))
        return round(accepted / len(children), 4)

    def stats(self) -> dict:
        by_state: dict[str, int] = {}
        for n in self._nodes.values():
            by_state[n.state] = by_state.get(n.state, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "by_state": by_state,
            "total_accepted": by_state.get("APPLIED", 0),
            "total_reverted": by_state.get("REVERTED", 0),
            "roots": sum(1 for n in self._nodes.values() if n.parent_id is None),
            "max_depth": max((len(self.lineage(n.node_id)) for n in self._nodes.values()),
                            default=0),
        }

    def _save(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as f:
                for n in self._nodes.values():
                    f.write(json.dumps(asdict(n), ensure_ascii=False) + "\n")
