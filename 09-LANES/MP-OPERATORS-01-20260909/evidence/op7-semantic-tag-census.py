#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OP-7 — سرشماری برچسب‌پذیریِ نوت‌های حافظهٔ معنایی (فقط‌خواندنی).

هیچ نوتی تغییر نمی‌کند. خروجی: چند نوت از روی gist اصلاً قابل‌برچسب‌اند
(ورودیِ برآورد هزینهٔ مهاجرت برای OP-5/H9-v2). دیکشنری دامنه از
MISSIONS (_ops/three_role.py) + طرح OP-5: زیمان/نقاشی/استودیو/زیرساخت.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

SRC = Path(r"F:/backup/_ops/state/semantic_memory.jsonl")

DOMAINS = {
    "ziman/store": [
        "زیمان", "ziman", "شاپیفای", "shopify", "فروشگاه", "قفسه", "گالری",
        "zm-gallery", "zm_", "zm-", "محصول", "دامنهٔ", "دامنه", "domain",
        "checkout", "سفارش", "order", "seo", "تم", "theme", "قیمت",
    ],
    "painting/leads": [
        "نقاشی", "پینت", "painting", "painter", "لید", "lead", "airtasker",
        "gumtree", "gbp", "google business", "مشتری", "بازاریابی محلی",
        "کوت", "quote", "استعلام قیمت",
    ],
    "studio/creator": [
        "استودیو", "استوديو", "studio", "اونلی فنز", "onlyfans", "فنز",
        "creator", "خالق محتوا", "saba", "صبا",
    ],
    "infrastructure/ops": [
        "ارگانیسم", "دیمن", "daemon", "organism", "۱۳۸", "138", "180",
        "182", "بکاپ", "backup", "گیت", "git", "بیت", "beat", "کرون",
        "cron", "ssh", "systemd", "wire", "gov", "بودجه", "budget",
        "cortex", "mesh", "sparse", "پروسه", "nginx", "سقف", "h9",
        "h4", "h8", "حافظه", "memory", "tick", "تایمر", "timer",
        "لجر", "ledger", "رسید", "receipt",
        # relaxed pass — آناتومی ارگانیسم (طبقهٔ زیرساخت)
        "قلب", "مغز", "ستون فقرات", "pacemaker", "پیس‌میکر", "خودمدل",
        "خودمختاری", "نقطهٔ مرده", "نقطه مرده", "سرچ عمیق", "provider",
        "پروایدر", "web_research",
    ],
}


def tag(gist: str) -> tuple[str, list[str]]:
    hits = []
    for dom, kws in DOMAINS.items():
        for kw in kws:
            if re.search(re.escape(kw), gist, re.IGNORECASE):
                hits.append(dom)
                break
    hits = sorted(set(hits))
    if not hits:
        return "untaggable", []
    if len(hits) == 1:
        return "single", hits
    return "ambiguous", hits


rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines()
        if l.strip()]
cats, singles, amb_pairs, tagged_domain = Counter(), [], Counter(), Counter()
for r in rows:
    cat, hits = tag(str(r.get("gist", "")))
    cats[cat] += 1
    if cat == "single":
        singles.append((r.get("ts", ""), hits[0]))
        tagged_domain[hits[0]] += 1
    elif cat == "ambiguous":
        amb_pairs["+".join(hits)] += 1

out = {
    "total_notes": len(rows),
    "megaprompt_said": 322,
    "note": "1 net new note since megaprompt — both numbers reported",
    "taggable_single_domain": cats["single"],
    "taggable_ambiguous_multi": cats["ambiguous"],
    "untaggable_no_signal": cats["untaggable"],
    "taggable_at_all": cats["single"] + cats["ambiguous"],
    "single_domain_breakdown": dict(tagged_domain),
    "top_ambiguous_pairs": dict(amb_pairs.most_common(8)),
    "cost_estimate_for_OP5": {
        "auto_taggable_clean": cats["single"],
        "needs_human_or_rule_review": cats["ambiguous"] + cats["untaggable"],
    },
}
print(json.dumps(out, ensure_ascii=False, indent=1))
sys.exit(0)
