#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OP-5 — شبیه‌سازیِ H9-v2 (برچسب-اول) روی دادهٔ موجود. PROPOSAL ONLY — بدون wiring.

روش: همان قاضیِ قفل‌شدهٔ T3 (توکن تخصصی هر مأموریت، حداقل ۱ تطابق در gist)،
همان پیکرهٔ semantic_memory.jsonl، همان فرمول رتبه‌بندی v1 (کپیverbatim از
_ops/three_role.py archive_seed) — فقط یک کلید مرتب‌سازی جلوتر: برچسبِ دامنه.
برچسب‌ها از سرشماری OP-7 (دیکشنری MISSIONS). عدد بهبود = اختلاف نرخ نوتِ مرتبط.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

SRC = Path(r"F:/backup/_ops/state/semantic_memory.jsonl")
K = 3
JUDGE = json.load(open(
    r"F:/backup/09-LANES/H9-TESTBATTERY-20260909/T3_seed_quality.json",
    encoding="utf-8"))["judge_locked_before_evaluation"]["tokens"]
MISSION_DOMAIN = {
    "shelf_check_zm_gallery_0013": "ziman/store",
    "store_order_check": "ziman/store",
    "checkout1_order_check": "ziman/store",
    "organism_liveness_check": "infrastructure/ops",
}
DOMAINS = json.loads(Path(
    r"F:/backup/09-LANES/MP-OPERATORS-01-20260909/evidence/op7-census-output.json"
).read_text(encoding="utf-8"))  # فقط برای گزارش؛ برچسب‌گذاری زیر مستقل است
_KW = {
    "ziman/store": ["زیمان", "ziman", "شاپیفای", "shopify", "فروشگاه", "قفسه",
                    "گالری", "zm-", "zm_", "محصول", "سفارش", "checkout"],
    "painting/leads": ["نقاشی", "پینت", "painting", "لید", "airtasker",
                       "gumtree", "gbp", "مشتری", "کوت", "quote"],
    "studio/creator": ["استودیو", "studio", "اونلی فنز", "onlyfans", "فنز",
                       "creator", "صبا", "saba"],
    "infrastructure/ops": [
        "ارگانیسم", "دیمن", "organism", "138", "180", "بکاپ", "گیت", "بیت",
        "beat", "کرون", "cron", "ssh", "systemd", "wire", "gov", "بودجه",
        "budget", "cortex", "mesh", "sparse", "h9", "حافظه", "memory",
        "tick", "تایمر", "لجر", "رسید", "قلب", "مغز", "ستون فقرات",
        "pacemaker", "پیس‌میکر", "خودمدل", "خودمختاری", "نقطهٔ مرده",
        "سرچ عمیق", "provider", "پروایدر"],
}

rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines()
        if l.strip()]


def tag_of(r: dict) -> str | None:
    g = str(r.get("gist", ""))
    for dom, kws in _KW.items():
        if any(re.search(re.escape(k), g, re.IGNORECASE) for k in kws):
            return dom
    return None


def tokens(s: str) -> set:
    return set(re.findall(r"[a-zA-Z\u0600-\u06FF]{3,}", s.lower()))


def relevant(gist: str, mission: str) -> bool:
    g = gist.lower()
    return any((re.search(r"[a-zA-Z]", t) and re.search(
        r"(?<![a-zA-Z])" + re.escape(t) + r"(?![a-zA-Z])", g))
        or (not re.search(r"[a-zA-Z]", t) and t in g)
        for t in JUDGE[mission])


def seed(mission: str, tag_first: bool, ctx_extra: str = "") -> list[str]:
    ctx = MISSION_CTX[mission] + " " + ctx_extra
    ctx_tokens = tokens(ctx)

    def rank(r: dict):
        g = str(r.get("gist", ""))
        rt = set(re.findall(r"[a-zA-Z\u0600-\u06FF]{3,}", g.lower()))
        overlap = len(ctx_tokens & rt)
        try:
            sal = float(r.get("salience") or 0.0)
        except (TypeError, ValueError):
            sal = 0.0
        if tag_first:
            return (tag_of(r) == MISSION_DOMAIN[mission], overlap > 0,
                    overlap * 10 + sal)
        return (overlap > 0, overlap * 10 + sal)

    return [str(r.get("gist", "")) for r in
            sorted(rows, key=rank, reverse=True)[:K]]


MISSION_CTX = {
    m: json.dumps({"mission": m}, ensure_ascii=False) for m in JUDGE}
# زمینهٔ واقعی‌نما: عنوان مأموریت همان‌طور که مدیر می‌بیند
import sys  # noqa: E402
sys.path.insert(0, r"F:/backup/_ops")
try:
    from three_role import MISSIONS
    MISSION_CTX = {m: MISSIONS[m]["title"] for m in JUDGE}
except Exception:
    pass

out = {"mode": "SIMULATION-ONLY (OP-5 proposal input)", "k": K,
       "n_corpus": len(rows), "per_mission": {}}
for m in JUDGE:
    v1 = seed(m, tag_first=False)
    v2 = seed(m, tag_first=True)
    out["per_mission"][m] = {
        "v1_rate": sum(relevant(g, m) for g in v1) / K,
        "v2_simulated_rate": sum(relevant(g, m) for g in v2) / K,
        "v1_top1": v1[0][:70], "v2_top1": v2[0][:70],
        "corpus_notes_with_mission_domain_tag": sum(
            1 for r in rows if tag_of(r) == MISSION_DOMAIN[m]),
    }
out["tag_distribution"] = dict(Counter(tag_of(r) for r in rows))
print(json.dumps(out, ensure_ascii=False, indent=1))
