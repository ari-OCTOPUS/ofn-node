#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_capability_manifest_registry — قابلیتِ نو خودش را معرفی می‌کند، بی‌import.

شکافی که می‌بندد: `SCAN_DIRS` فهرستِ **ثابتِ** پوشه بود و کشف به داشتنِ
`card()` بی‌آرگومان گره خورده بود. یعنی هر namespace نو (`world_discovery`،
`action_bridge`، `integrations/**`) ساختاراً نامرئی می‌ماند تا کسی یادش بیفتد
نامش را اضافه کند — همان الگوی «قابلیت هست، کسی نمی‌بیندش» که این پروژه بارها
خورده.

⚠️ **ثبت مجوز نیست.** مهم‌ترین بندِ این فایل همین است: حضورِ manifest یعنی
«قابلیت وجود دارد و مالک می‌تواند ببیندش» — نه اینکه اجرایش مجاز است. یک
manifest که خودش را مجوز اعلام کند **رد می‌شود**، نه اینکه فیلدش نادیده گرفته شود.
"""
import json
import sys
from pathlib import Path

import harness

ENV = harness.setup("cap-manifest")

import capability_registry as cr  # noqa: E402

_OPS = Path(cr.__file__).resolve().parent


def _valid(**over):
    d = {"schema": cr.MANIFEST_SCHEMA, "capability_id": "probe_cap",
         "title": "🧪 قابلیتِ آزمایشی", "version": "0.1.0",
         "owner_phrases": ["آزمایش"], "read_handler": "x:y",
         "action_contract": "a→b", "risk_class": "read",
         "owner_gate": "هیچ", "surface": "owner_outer_dm",
         "runtime_status_probe": "TEST", "tests": []}
    d.update(over)
    return d


def _write(tmpdir, payload):
    p = Path(tmpdir) / cr.MANIFEST_NAME
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False), "utf-8")
    return p


# ── کشفِ واقعی روی درختِ همین worktree ──────────────────────────────────────
def t_the_new_namespaces_are_discovered():
    """قلبِ شکاف: سه namespace ای که `SCAN_DIRS` نمی‌دید."""
    ids = {m["key"] for m in cr.discover_manifests(refresh=True)}
    for expected in ("action_bridge", "world_discovery_action", "self_goal_cycle"):
        assert expected in ids, f"{expected} کشف نشد — ids={sorted(ids)}"


def t_every_manifest_carries_risk_and_surface():
    for m in cr.discover_manifests(refresh=True):
        assert m["risk_class"] in ("read", "low", "medium", "high", "forbidden"), m
        assert m["surface"] in ("owner_outer_dm", "owner_inner_dm",
                                "legs_forum_group"), m
        assert str(m["version"]).strip(), m


def t_registration_is_never_authorization():
    """صریح در هر ردیف — تا هیچ مصرف‌کننده‌ای «دیده شد» را «مجاز است» نخواند."""
    for m in cr.discover_manifests(refresh=True):
        assert m["registration_is_authorization"] is False, m


def t_a_manifest_claiming_authorization_is_rejected():
    """manifest ای که خودش را مجوز اعلام کند رد می‌شود — نه اینکه فیلدش
    نادیده گرفته شود. تفاوت مهم است: نادیده‌گرفتن یعنی ردیف می‌ماند و ادعایش
    فقط بی‌اثر است؛ رد یعنی اصلاً واردِ فهرست نمی‌شود."""
    import tempfile
    d = tempfile.mkdtemp(prefix="cap-auth-")
    p = _write(d, _valid(registration_is_authorization=True))
    assert cr._read_manifest(p) is None, "manifest ِ خود-مجوزده پذیرفته شد"


def t_a_malformed_manifest_is_skipped_not_partially_accepted():
    import tempfile
    d = tempfile.mkdtemp(prefix="cap-bad-")
    for bad in ({"schema": "wrong.v9"}, _valid(capability_id=""),
                _valid(title="  "), _valid(risk_class=""), _valid(surface=""),
                _valid(version="")):
        p = _write(d, bad)
        assert cr._read_manifest(p) is None, bad


def t_unreadable_json_does_not_crash_discovery():
    import tempfile
    d = tempfile.mkdtemp(prefix="cap-broken-")
    p = Path(d) / cr.MANIFEST_NAME
    p.write_text("{ not json at all", "utf-8")
    assert cr._read_manifest(p) is None
    assert isinstance(cr.discover_manifests(refresh=True), list)


def t_a_valid_manifest_round_trips():
    import tempfile
    d = tempfile.mkdtemp(prefix="cap-ok-")
    p = _write(d, _valid())
    got = cr._read_manifest(p)
    assert got is not None and got["capability_id"] == "probe_cap", got


# ── فهرستِ واحد ─────────────────────────────────────────────────────────────
def t_the_catalog_merges_both_sources_without_losing_either():
    cat = cr.catalog(refresh=True)
    sources = {r.get("source") for r in cat}
    assert "manifest" in sources and "scan" in sources, sources
    assert len(cat) >= len(cr.discover(refresh=True)), "کاتالوگ ردیف گم کرد"
    keys = [r["key"] for r in cat]
    assert len(keys) == len(set(keys)), "کلیدِ تکراری در کاتالوگ"


def t_manifest_wins_over_scan_for_the_same_key():
    """اعلامِ صریحِ پکیج بر حدسِ اسکنر مقدم است."""
    cat = cr.catalog(refresh=True)
    row = next((r for r in cat if r["key"] == "action_bridge"), None)
    assert row is not None and row["source"] == "manifest", row


def t_discovery_imports_nothing():
    """صفر import — یک پکیجِ خراب نباید رجیستری را بکشد.

    سنجه: ماژول‌های پکیج‌های نو نباید بعد از کشف در `sys.modules` باشند."""
    for m in list(sys.modules):
        if m.startswith(("action_bridge", "world_discovery")):
            del sys.modules[m]
    cr.discover_manifests(refresh=True)
    leaked = [m for m in sys.modules
              if m.startswith(("action_bridge.", "world_discovery."))]
    assert not leaked, f"import نشت کرد: {leaked}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_capability_manifest_registry: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
