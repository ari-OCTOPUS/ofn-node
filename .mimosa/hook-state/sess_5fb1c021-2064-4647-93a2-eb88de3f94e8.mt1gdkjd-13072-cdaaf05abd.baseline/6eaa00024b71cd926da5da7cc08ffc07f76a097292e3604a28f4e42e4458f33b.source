#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_manifest_truth — MANIFEST_INVALID باید دیده شود، نه بی‌صدا حذف (SGC-14 §۱۲).

نسخهٔ قبلیِ `_read_manifest` نامعتبر را بی‌صدا None می‌کرد ⇒ «خراب اعلام شده»
و «اصلاً اعلام نشده» یک شکل می‌شدند. حالا دلیل ثبت و در card/report دیده
می‌شود؛ و ردیفِ نامعتبر همچنان هرگز واردِ فهرستِ معتبرها نمی‌شود
(جهشِ §۱۷.۲-۱۵: «manifest invalid → LIVE» باید قرمز بماند).
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import harness

ENV = harness.setup("manifest-truth")

import capability_registry as cr  # noqa: E402

VALID = {
    "schema": "octopus.capability-manifest.v1",
    "capability_id": "demo_ok", "title": "دمو", "version": "0.1.0",
    "risk_class": "read", "surface": "owner_outer_dm",
    "registration_is_authorization": False,
}


def _tmp_tree(entries: dict) -> Path:
    root = Path(tempfile.mkdtemp(prefix="cr-manifest-"))
    for rel, payload in entries.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(payload if isinstance(payload, str)
                     else json.dumps(payload, ensure_ascii=False), "utf-8")
    return root


def _with_here(root: Path):
    class _Ctx:
        def __enter__(self):
            self._old = cr._HERE
            cr._HERE = root
            return self

        def __exit__(self, *exc):
            cr._HERE = self._old
            cr.discover_manifests(refresh=True)   # کشِ واقعی را برگردان
    return _Ctx()


def t_invalid_manifests_are_reported_never_listed():
    root = _tmp_tree({
        "capability-manifest.json": VALID,
        "doctor/capability-manifest.json": {**VALID, "capability_id": "", "title": ""},
        "cortex/capability-manifest.json": {**VALID, "capability_id": "sneaky",
                                            "registration_is_authorization": True},
    })
    with _with_here(root):
        rows = cr.discover_manifests(refresh=True)
        keys = {r["key"] for r in rows}
        assert keys == {"demo_ok"}, keys
        rep = cr.manifest_report()
        assert rep["invalid_count"] == 2, rep
        reasons = {r["reason"] for r in rep["invalid"]}
        assert any(x.startswith("missing:") for x in reasons), reasons
        assert "claims-authorization" in reasons, reasons


def t_unreadable_manifest_is_reported_not_swallowed():
    root = _tmp_tree({"capability-manifest.json": "{not json"})
    with _with_here(root):
        assert cr.discover_manifests(refresh=True) == []
        rep = cr.manifest_report()
        assert rep["invalid_count"] == 1 and \
            rep["invalid"][0]["reason"].startswith("unreadable:"), rep


def t_card_surfaces_invalid_count_to_the_owner():
    root = _tmp_tree({
        "capability-manifest.json": {**VALID},
        "legs/capability-manifest.json": {**VALID, "capability_id": "bad", "version": ""},
    })
    with _with_here(root):
        cr.discover_manifests(refresh=True)
        cr._cache = None
        body = cr.card()
        assert "manifest نامعتبر" in body, body[:200]
        cr._cache = None


def t_real_tree_manifests_are_all_valid_and_include_world_discovery():
    rows = cr.discover_manifests(refresh=True)
    keys = {r["key"] for r in rows}
    assert "world_discovery" in keys, keys
    rep = cr.manifest_report()
    assert rep["invalid_count"] == 0, rep
    wd = next(r for r in rows if r["key"] == "world_discovery")
    assert wd["registration_is_authorization"] is False
    assert wd["risk_class"] == "read", wd


CHECKS = [(f.__name__, f) for f in (
    t_invalid_manifests_are_reported_never_listed,
    t_unreadable_manifest_is_reported_not_swallowed,
    t_card_surfaces_invalid_count_to_the_owner,
    t_real_tree_manifests_are_all_valid_and_include_world_discovery,
)]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    total = len(CHECKS)
    print(("✅" if not failed else "❌") + f" test_manifest_truth: {total - failed}/{total}")
    raise SystemExit(1 if failed else 0)
