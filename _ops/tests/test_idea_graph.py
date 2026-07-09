#!/usr/bin/env python3
"""تستِ رفتاریِ P-I: موتورِ ایده-گراف.

ایده-گراف محتوای واقعیِ vault را می‌خواند و گرافِ ارتباطِ ایده‌ها/پروژه‌ها را
می‌سازد (frontmatter + wikilinks)، سپس تحلیل می‌کند (هاب‌ها، خوشه‌ها، پل‌ها،
یال‌های پیشنهادی). propose-only مطلق.

این تست اثبات می‌کند:
  (الف) پارس: frontmatter + wikilink → nodes + edges واقعی.
  (ب) تحلیل: هاب‌ها، خوشه‌ها، پل‌ها، یال‌های پیشنهادی کار می‌کنند.
  (ج) resolve: wikilink با basename تطبیق می‌خورد (نه فقط مسیرِ کامل).
  (د) propose-only: هیچ effector؛ یال‌های پیشنهادی human-append هستند.
  (هـ) روی vaultِ واقعی: گراف معنی‌دار می‌سازد (_nodes/edges > 0).
  (و) flag خاموش → idea_beat no-op.
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("idea-graph")

_OPS = Path(r"F:\backup\_ops")
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import wiring  # noqa: E402
from idea_graph import IdeaGraph, _parse_frontmatter, _normalize_id, WIKILINK_RE  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


def _fake_vault():
    """یک vaultِ کوچکِ موقت با پروژه‌های وصل‌شده با wikilink + frontmatter."""
    root = Path(ENV["root"]) / "fake-vault"
    for sub in ("03 - Projects", "07 - Knowledge", "00 - Inbox"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    # پروژهٔ A با wikilink به B و tag مشترک
    (root / "03 - Projects" / "Alpha.md").write_text(
        "---\ntype: project\nstatus: active\ntags: [painting, sydney]\nproject: \"[[03 - Projects/Alpha]]\"\ncreated: 2026-07-01\n---\n# Alpha\n\nSee [[03 - Projects/Beta|Beta]] for synergy.\n", "utf-8")
    # پروژهٔ B با tag مشترک ولی بدونِ یال به A (پیشنهادِ یالِ نو)
    (root / "03 - Projects" / "Beta.md").write_text(
        "---\ntype: project\nstatus: idea\ntags: [painting, branding]\ncreated: 2026-07-02\n---\n# Beta\n\nRelated work.\n", "utf-8")
    # نوتِ دانش با sources (یالِ cites) و tag متفاوت
    (root / "07 - Knowledge" / "Theory.md").write_text(
        "---\ntype: knowledge\ntags: [theory]\nsources: [\"[[03 - Projects/Alpha]]\"]\n---\n# Theory\n\nBuilds on Alpha.\n", "utf-8")
    # نوتِ Inbox با basename-only link
    (root / "00 - Inbox" / "Idea.md").write_text(
        "---\ntype: log\nstatus: inbox\ntags: [painting]\n---\n# Idea\n\nLinks to [[Beta]].\n", "utf-8")
    return root


# ════════════════════════════════════════════════════════════════════════════════
# (الف) پارس: frontmatter + wikilink → nodes + edges
# ════════════════════════════════════════════════════════════════════════════════

def t_parse_frontmatter_basic():
    """frontmatter ساده پارس می‌شود."""
    meta, body = _parse_frontmatter("---\ntype: project\ntags: [a, b]\n---\n# Title\n")
    assert meta["type"] == "project"
    assert meta["tags"] == ["a", "b"]
    assert "# Title" in body


def t_parse_no_frontmatter():
    """بدونِ frontmatter → meta خالی، body کامل."""
    meta, body = _parse_frontmatter("# Just a title\nbody")
    assert meta == {}
    assert "Just a title" in body


def t_build_creates_nodes_and_edges():
    """build از fake vault → nodes + edges واقعی."""
    root = _fake_vault()
    g = IdeaGraph()
    report = g.build(root)
    assert report["n_nodes"] >= 4, f"باید ≥۴ node باشد، نه {report['n_nodes']}"
    assert report["n_edges"] >= 1, "باید ≥۱ edge باشد"
    # Alpha و Beta باید موجود باشند
    assert "03 - Projects/Alpha" in g.nodes
    assert "03 - Projects/Beta" in g.nodes


def t_wikilink_creates_reference_edge():
    """wikilink [[Beta]] در Alpha → یالِ references."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    refs = [e for e in g.edges if e.src == "03 - Projects/Alpha" and e.label == "references"]
    assert any(e.dst == "03 - Projects/Beta" for e in refs), \
        "Alpha باید به Beta با references وصل باشد"


def test_frontmatter_sources_creates_cite_edge():
    """frontmatter sources: [[Alpha]] → یالِ cites."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    cites = [e for e in g.edges if e.label == "cites"
             and e.src == "07 - Knowledge/Theory"
             and e.dst == "03 - Projects/Alpha"]
    assert len(cites) >= 1, "Theory باید Alpha را cites کند"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) resolve با basename
# ════════════════════════════════════════════════════════════════════════════════

def t_resolve_by_basename():
    """wikilink با basename (نه مسیرِ کامل) هم resolve می‌شود."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    # Idea.md با [[Beta]] لینک داده (basename-only)
    refs = [e for e in g.edges if e.src == "00 - Inbox/Idea" and e.dst == "03 - Projects/Beta"]
    assert len(refs) >= 1, "basename-only link باید resolve شود"


# ════════════════════════════════════════════════════════════════════════════════
# (ب) تحلیل: هاب‌ها، خوشه‌ها، پل‌ها، یال‌های پیشنهادی
# ════════════════════════════════════════════════════════════════════════════════

def t_hubs_returns_high_indegree():
    """هاب‌ها: Alpha باید in-degree ≥۱ داشته باشد (Theory از طریقِ cites به آن لینک می‌کند)."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    hubs = dict(g.hubs())
    assert hubs.get("03 - Projects/Alpha", 0) >= 1, \
        f"Alpha باید in-degree≥۱ داشته باشد (Theory cites): {hubs.get('03 - Projects/Alpha')}"
    # و هابِ اول باید در واقع دارای in-degree > 0 باشد (نه همگی صفر)
    assert hubs and hubs[list(hubs.keys())[0]] >= 1


def t_clusters_by_tags():
    """خوشهٔ painting باید Alpha و Beta و Idea را داشته باشد."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    clusters = g.clusters_by_tags()
    assert "painting" in clusters, "خوشهٔ painting باید موجود باشد"
    assert "03 - Projects/Alpha" in clusters["painting"]
    assert "03 - Projects/Beta" in clusters["painting"]


def t_bridges_detected():
    """نوت با ≥۲ tag → bridge. (اگر کسی ≥۲ tag متمایز دارد)."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    # این تست فقط بررسی می‌کند که bridges کار می‌کند (خروجی list است)
    assert isinstance(g.bridges(), list)


def t_proposed_edges_for_unlinked_shared_tag():
    """Alpha و Idea tag‌های مشترک (painting) دارند ولی شاید یال نباشد → پیشنهاد."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    proposed = g.proposed_edges()
    # اگر Alpha↔Idea یال نیست ولی tag مشترک دارند → در proposed
    assert isinstance(proposed, list)
    # حداقل یک پیشنهاد باید وجود داشته باشد (Alpha-Beta بدونِ یال، tag مشترک)
    assert len(proposed) >= 1, "باید حداقل یک یالِ پیشنهادی باشد"


def t_analyze_full_report():
    """analyze گزارشِ کامل با همهٔ فیلدها می‌دهد."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    a = g.analyze()
    for key in ("n_nodes", "n_edges", "n_broken_targets", "hubs",
                "n_clusters", "n_bridges", "n_proposed_edges",
                "proposed_edges_sample", "propose_only"):
        assert key in a, f"analyze باید {key} داشته باشد"
    assert a["propose_only"] is True


# ════════════════════════════════════════════════════════════════════════════════
# (د) propose-only — هیچ effector
# ════════════════════════════════════════════════════════════════════════════════

def t_no_effector_methods():
    """IdeaGraph نباید متدِ write/merge/settle داشته باشد."""
    for m in ("write", "merge", "settle", "send", "publish", "pay", "append"):
        assert not hasattr(IdeaGraph, m), f"IdeaGraph نباید {m} داشته باشد"


def t_proposed_edges_are_human_append():
    """یال‌های پیشنهادی باید propose_new_edge=True داشته باشند (human-gate)."""
    root = _fake_vault()
    g = IdeaGraph()
    g.build(root)
    for p in g.proposed_edges():
        assert p.get("propose_new_edge") is True


# ════════════════════════════════════════════════════════════════════════════════
# (هـ) vault واقعی
# ════════════════════════════════════════════════════════════════════════════════

def t_real_vault_builds_meaningful_graph():
    """روی vaultِ واقعی: گراف معنی‌دار می‌سازد (nodes/edges > 0)."""
    g = IdeaGraph()
    report = g.build(r"F:\backup")
    assert report["n_nodes"] > 100, f"vault واقعی باید ≥۱۰۰ node داشته باشد: {report['n_nodes']}"
    assert report["n_edges"] > 50, f"vault واقعی باید ≥۵۰ edge داشته باشد: {report['n_edges']}"


def t_real_vault_hubs_meaningful():
    """روی vaultِ واقعی: هاب‌ها عنوانِ معنی‌دار دارند."""
    g = IdeaGraph()
    g.build(r"F:\backup")
    hubs = g.hubs()
    assert len(hubs) > 0
    # هابِ اول باید in-degree > 0 داشته باشد
    assert hubs[0][1] > 0


# ════════════════════════════════════════════════════════════════════════════════
# (و) flag خاموش → idea_beat no-op
# ════════════════════════════════════════════════════════════════════════════════

def t_idea_beat_flag_off_noop():
    """flag خاموش → idea_beat None (no-op)."""
    os.environ.pop("OCTOPUS_WIRE_IDEAS", None)
    g = wiring.make_idea_graph()
    r = wiring.idea_beat(g, beat=1440)
    assert r is None


def t_idea_beat_flag_on_returns_analysis():
    """flag روشن + beat مضرب → تحلیل برمی‌گرداند."""
    os.environ["OCTOPUS_WIRE_IDEAS"] = "1"
    try:
        g = wiring.make_idea_graph()
        r = wiring.idea_beat(g, vault_root=str(_fake_vault()), beat=1440)
        assert r is not None
        assert "n_nodes" in r
    finally:
        os.environ.pop("OCTOPUS_WIRE_IDEAS", None)


def t_idea_beat_non_multiple_noop():
    """beat غیرِ مضربِ N → no-op."""
    os.environ["OCTOPUS_WIRE_IDEAS"] = "1"
    try:
        g = wiring.make_idea_graph()
        r = wiring.idea_beat(g, beat=100)  # ۱۰۰ مضربِ ۱۴۴۰ نیست
        assert r is None
    finally:
        os.environ.pop("OCTOPUS_WIRE_IDEAS", None)


# ════════════════════════════════════════════════════════════════════════════════
# structural — organism wiring
# ════════════════════════════════════════════════════════════════════════════════

def t_organism_calls_idea_beat():
    """tick باید idea_beat را صدا بزند."""
    assert "idea_beat" in ORGANISM_SRC


def t_organism_builds_idea_graph():
    """boot باید make_idea_graph را صدا بزند."""
    assert "make_idea_graph" in ORGANISM_SRC


def t_organism_applies_profile():
    """boot باید apply_profile را صدا بزند (P-W3)."""
    assert "apply_profile" in ORGANISM_SRC


def t_organism_forwards_doctor_result():
    """publish_tick_signals باید doctor_result را بگیرد (نه None همیشگی).
    (فراخوانی چندخطی است، پس کلِ فایل را بررسی می‌کنیم.)"""
    # نباید doctor_result=None همیشگی باشد (W7: باید doctor_result واقعی منتقل شود)
    assert "doctor_result=_doctor_result" in ORGANISM_SRC, \
        "publish_tick_signals باید doctor_result واقعی را منتقل کند (نه None)"
    # و نباید doctor_result=None در همان فراخوانی باشد
    publish_block_idx = ORGANISM_SRC.find("publish_tick_signals(")
    block = ORGANISM_SRC[publish_block_idx:publish_block_idx + 400]
    assert "doctor_result=None" not in block, \
        "W7: doctor_result نباید None باشد — باید _doctor_result منتقل شود"


if __name__ == "__main__":
    failed = harness.run([
        # (الف) پارس
        ("parse frontmatter", t_parse_frontmatter_basic),
        ("parse بدونِ frontmatter", t_parse_no_frontmatter),
        ("build → nodes + edges", t_build_creates_nodes_and_edges),
        ("wikilink → reference edge", t_wikilink_creates_reference_edge),
        ("frontmatter sources → cites", test_frontmatter_sources_creates_cite_edge),
        # (ج) resolve
        ("resolve با basename", t_resolve_by_basename),
        # (ب) تحلیل
        ("هاب‌ها (in-degree)", t_hubs_returns_high_indegree),
        ("خوشه‌ها by tags", t_clusters_by_tags),
        ("پل‌ها", t_bridges_detected),
        ("یال‌های پیشنهادی", t_proposed_edges_for_unlinked_shared_tag),
        ("analyze گزارشِ کامل", t_analyze_full_report),
        # (د) propose-only
        ("بدونِ متدِ effector", t_no_effector_methods),
        ("یال‌های پیشنهادی human-append", t_proposed_edges_are_human_append),
        # (هـ) vault واقعی
        ("vault واقعی: گراف معنی‌دار", t_real_vault_builds_meaningful_graph),
        ("vault واقعی: هاب‌ها", t_real_vault_hubs_meaningful),
        # (و) flag
        ("flag off → no-op", t_idea_beat_flag_off_noop),
        ("flag on → تحلیل", t_idea_beat_flag_on_returns_analysis),
        ("beat غیرِ مضربِ N → no-op", t_idea_beat_non_multiple_noop),
        # structural
        ("organism idea_beat", t_organism_calls_idea_beat),
        ("organism make_idea_graph", t_organism_builds_idea_graph),
        ("organism apply_profile", t_organism_applies_profile),
        ("organism doctor_result منتقل", t_organism_forwards_doctor_result),
    ])
    sys.exit(1 if failed else 0)
