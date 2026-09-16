#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vault.py — حافظهٔ دکتر: خواندن و نوشتنِ والتِ Obsidian.

والت **منبعِ حقیقتِ انسان‌خوان** است. هر نوت یک واحدِ حافظه با frontmatter است.
هیچ چیزی در والت بدونِ `type` و `tags` نوشته نمی‌شود — بدونِ metadata، debug ناممکن است
(چک‌لیستِ حافظهٔ محلی، §«metadata برای هر memory item»).

لایه‌بندیِ حافظه (نگاشت به پوشه‌ها):
    semantic   → 10-قوانین · 20-معادلات · 30-مغناطیس · 40-اندام‌ها
    episodic   → 50-اسکن‌ها · 60-یافته‌ها
    procedural → 70-نسخه‌ها
    open       → 80-پرسش‌های-باز
stdlib-only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

LAYER = {
    "10-قوانین": "semantic", "20-معادلات": "semantic",
    "30-مغناطیس": "semantic", "40-اندام‌ها": "semantic",
    "50-اسکن‌ها": "episodic", "60-یافته‌ها": "episodic",
    "70-نسخه‌ها": "procedural", "80-پرسش‌های-باز": "open",
    "00-INDEX": "index", "90-_meta": "meta",
}
_LINK = re.compile(r"\[\[([^\]|#]+)")


@dataclass
class Note:
    path: Path
    rel: str
    layer: str
    fm: dict
    body: str
    links: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        m = re.search(r"^#\s+(.+)$", self.body, re.MULTILINE)
        return m.group(1).strip() if m else self.path.stem

    @property
    def status(self) -> str:
        return str(self.fm.get("status", ""))

    def excerpt(self, n: int = 1400) -> str:
        t = re.sub(r"\n{3,}", "\n\n", self.body).strip()
        return t if len(t) <= n else t[:n] + " …"


def _parse_fm(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm, body = {}, text[end + 4:]
    key = None
    for line in text[4:end].splitlines():
        if line.strip().startswith("- ") and key:
            fm.setdefault(key, [])
            if isinstance(fm[key], list):
                fm[key].append(line.strip()[2:].strip().strip('"'))
        elif ":" in line:
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip().strip('"')
            if v.startswith("[") and v.endswith("]"):
                fm[key] = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
            else:
                fm[key] = v if v else []
    return fm, body


class Vault:
    def __init__(self, root: Path | str):
        self.root = Path(root)

    def load(self) -> list[Note]:
        out: list[Note] = []
        for p in sorted(self.root.rglob("*.md")):
            rel = p.relative_to(self.root).as_posix()
            top = rel.split("/")[0]
            if top == "90-_meta":
                continue
            try:
                raw = p.read_text("utf-8")
            except OSError:
                continue
            fm, body = _parse_fm(raw)
            out.append(Note(p, rel, LAYER.get(top, "other"), fm, body,
                            _LINK.findall(body)))
        return out

    def by_layer(self, layer: str) -> list[Note]:
        return [n for n in self.load() if n.layer == layer]

    def search(self, query: str, limit: int = 8) -> list[Note]:
        """بازیابیِ ساده و شفاف — امتیازِ کلمه‌ای، بدونِ embedding.

        عمداً ساده: [UNKNOWN] بودنِ کیفیتِ retrieval بدتر از سادگی است. وقتی والت
        بزرگ شد، اینجا جای وصل‌کردنِ sqlite-vec است — نه زودتر.
        """
        terms = [t for t in re.split(r"\s+", query.strip()) if len(t) > 1]
        scored = []
        for n in self.load():
            hay = (n.title + " " + n.rel + " " + n.body).lower()
            s = sum(hay.count(t.lower()) for t in terms)
            if s == 0:
                continue                     # صفر تطابق ⇒ هرگز وارد نتیجه نشو
            s += 4 * sum(1 for t in terms if t.lower() in n.title.lower())
            if n.status == "🔴":
                s += 2                       # قرمز فقط *بینِ منطبق‌ها* اولویت می‌گیرد،
                                             # نه اینکه بدونِ تطابق وارد شود
            scored.append((s, n))
        scored.sort(key=lambda x: -x[0])
        return [n for _, n in scored[:limit]]

    def write(self, rel: str, fm: dict, body: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for k, v in fm.items():
            if isinstance(v, list):
                lines.append(f"{k}:\n" + "\n".join(f"  - {i}" for i in v))
            elif isinstance(v, bool):
                lines.append(f"{k}: {str(v).lower()}")
            elif isinstance(v, (int, float)):
                lines.append(f"{k}: {v}")
            else:
                lines.append(f'{k}: "{v}"')
        p.write_text("---\n" + "\n".join(lines) + "\n---\n\n" + body.strip() + "\n",
                     encoding="utf-8")
        return p

    def stats(self) -> dict:
        ns = self.load()
        by: dict[str, int] = {}
        red = 0
        for n in ns:
            by[n.layer] = by.get(n.layer, 0) + 1
            if n.status == "🔴":
                red += 1
        return {"notes": len(ns), "by_layer": by, "red": red,
                "links": sum(len(n.links) for n in ns)}
