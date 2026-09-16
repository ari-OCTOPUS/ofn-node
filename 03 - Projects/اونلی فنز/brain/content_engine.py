#!/usr/bin/env python3
"""content_engine.py — #2: از داده → ایده → اسکریپت. $0، صفر LLM/PII."""
from __future__ import annotations
import json, random, math
from dataclasses import dataclass, field
from pathlib import Path

SHOT_TYPES = ["solo_static", "walking", "closeup_detail", "prop_interaction",
              "seasonal_visual", "asmr_motion", "angle_variety"]
PLATFORM_HINTS = {"reddit": "SFW teaser", "x": "aesthetic pin", "of": "feed set",
                  "ppv": "exclusive bundle", "shorts": "15s vertical"}
SEASONAL_TAGS = {"summer": ["sandals","beach","bright_pedi","sunglasses"],
                 "autumn": ["boots","cozy_socks","warm_tones","leaves"],
                 "winter": ["fuzzy_socks","indoor_cozy","spa_pedi","blanket"],
                 "spring": ["floral","fresh_pedi","sandals_return","pastel"]}


@dataclass
class ContentIdea:
    id: str; title: str; tags: list[str]; shot_type: str
    platform_hint: str; est_effort_min: int = 5


@dataclass
class ScriptScene:
    scene_num: int; shot_type: str; angle: str; duration_s: int; note: str = ""


@dataclass
class BatchPlan:
    ideas: list[ContentIdea]; total_time_min: int; sessions: int


@dataclass
class ReuseMatrix:
    idea_id: str; targets: dict  # {platform: content_type}


class ContentEngine:
    """از tag_performance + ترند → ایده → اسکریپت. بدون LLM."""

    def __init__(self, config_path=None):
        self._config_path = Path(config_path) if config_path else (
            Path(__file__).resolve().parents[1] / "studio" / "config.json")
        try: self._config = json.loads(self._config_path.read_text(encoding="utf-8"))
        except: self._config = {}
        self._rng = random.Random(42)

    def generate_ideas(self, tag_performance: dict | None = None,
                       season: str = "summer", count: int = 10) -> list[ContentIdea]:
        perf = tag_performance or {}
        seasonal = SEASONAL_TAGS.get(season, SEASONAL_TAGS["summer"])
        config_trends = [t.get("tag","") for t in self._config.get("trends",[])]
        all_tags = list(set(list(perf.keys()) + seasonal + config_trends + ["cozy","asmr"]))
        ideas = []
        for i in range(count):
            tag = self._rng.choice(all_tags) if all_tags else "cozy"
            shot = self._rng.choice(SHOT_TYPES)
            platform = self._rng.choice(list(PLATFORM_HINTS.keys()))
            title = f"{tag.replace('_',' ')} — {shot.replace('_',' ')}"
            ideas.append(ContentIdea(
                id=f"IDEA-{i+1:03d}", title=title,
                tags=[tag, shot, season], shot_type=shot,
                platform_hint=platform, est_effort_min=self._rng.randint(3,10)))
        return ideas

    def script_from_idea(self, idea: ContentIdea) -> list[ScriptScene]:
        """اسکریپتِ ساده: ۳ صحنه."""
        angles = ["top_down","side_45","closeup","floor_level","over_shoulder"]
        scenes = []
        for s in range(1,4):
            scenes.append(ScriptScene(
                scene_num=s, shot_type=idea.shot_type,
                angle=self._rng.choice(angles), duration_s=self._rng.randint(5,20),
                note=f"scene {s} — {idea.tags[0]}"))
        return scenes

    def batch_plan(self, ideas: list[ContentIdea], max_session_min: int = 90) -> BatchPlan:
        total = sum(i.est_effort_min for i in ideas)
        sessions = max(1, math.ceil(total / max_session_min))
        return BatchPlan(ideas=ideas, total_time_min=total, sessions=sessions)

    def reuse_matrix(self, idea: ContentIdea) -> ReuseMatrix:
        return ReuseMatrix(idea_id=idea.id, targets={
            "reddit": "SFW teaser frame", "x": "aesthetic pin",
            "of": "feed set (2-3)", "ppv": "exclusive bundle", "shorts": "15s clip"})

    def ab_pairs(self, ideas: list[ContentIdea]) -> list[tuple[ContentIdea, ContentIdea]]:
        pairs = []
        for i in range(0, len(ideas)-1, 2):
            pairs.append((ideas[i], ideas[i+1]))
        return pairs

    def ideas_html(self, ideas: list[ContentIdea]) -> str:
        lines = ["💡 <b>ایده‌های محتوا</b>","──────────"]
        for idea in ideas[:10]:
            lines.append(f"📌 {idea.id}: {idea.title} ({idea.platform_hint})")
        return "\n".join(lines)
