#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingest.py — اسکنِ نو ⟶ حافظهٔ دکتر.

قاعدهٔ نوشتن (از چک‌لیستِ حافظهٔ محلی، §«autonomous write را محدود کرده‌ای؟»):
    **هر مشاهده‌ای خودکار به حافظهٔ بلندمدت تبدیل نمی‌شود.**
    اسکن ⟶ نوتِ اپیزودیک (همیشه). یافته ⟶ نوتِ اپیزودیک با شاهد.
    ولی هیچ‌کدام معادله یا قانون را overwrite نمی‌کنند — تعارض فقط flag می‌شود.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from vault import Vault


def ingest_scan(vault: Vault, scan: dict) -> dict:
    """یک اسکن (dict) را به والت اضافه می‌کند و تعارض‌ها را flag می‌کند.

    شکلِ منتظره:
      {"date": "2026-07-26", "suite": "294/294", "beat": 11862,
       "metrics": {"velocity_per_hr": {"value": 5.86, "provenance": "درون‌زاد",
                                       "receipt": "…", "status": "🔴"}},
       "findings": [{"id":"F-08","title":"…","status":"🔴","body":"…"}]}
    """
    d = str(scan.get("date") or date.today().isoformat())
    written, flags = [], []

    metrics = scan.get("metrics") or {}
    findings = scan.get("findings") or []

    body = [f"# 🔬 اسکنِ {d}", ""]
    for k, v in (("سوئیت", scan.get("suite")), ("beat", scan.get("beat")),
                 ("برنچ", scan.get("branch"))):
        if v:
            body.append(f"- **{k}:** `{v}`")
    if metrics:
        body += ["", "## سنجه‌ها", "",
                 "| سنجه | مقدار | منشأ | وضعیت | رأی؟ |", "|---|---|---|---|---|"]
        for name, m in metrics.items():
            prov = m.get("provenance", "نامعلوم")
            vote = "✅" if (prov == "برون‌زاد" and m.get("receipt")) else "❌"
            if vote == "❌":
                flags.append(f"{name}: {prov}"
                             + ("" if m.get("receipt") else " · بدونِ رسید"))
            body.append(f"| `{name}` | {m.get('value')} | {prov} | "
                        f"{m.get('status','')} | {vote} |")
    if findings:
        body += ["", "## یافته‌ها", ""]
        body += [f"- [[{f['id']}-{f['title'].replace(' ','-')}]] {f.get('status','')}"
                 for f in findings]
    if flags:
        body += ["", "> [!warning] سنجه‌های بی‌رأی (R-01)",
                 "> " + " · ".join(flags)]
    body += ["", "---", "[[MOC-اسکن‌ها]] · [[HOME]]"]

    p = vault.write(f"50-اسکن‌ها/SCAN-{d}.md",
                    {"type": "scan", "date": d, "suite": str(scan.get("suite", "")),
                     "tags": ["اسکن"]}, "\n".join(body))
    written.append(p.name)

    for f in findings:
        slug = f"{f['id']}-{f['title'].replace(' ', '-')}"
        p = vault.write(f"60-یافته‌ها/{slug}.md",
                        {"type": "finding", "id": f["id"],
                         "status": f.get("status", "🔴"), "scan": d, "tags": ["یافته"]},
                        f"# {f['id']} — {f['title']} {f.get('status','')}\n\n"
                        f"{f.get('body','')}\n\n---\n[[SCAN-{d}]] · [[R-01-قانونِ-خودارجاعی]]")
        written.append(p.name)

    return {"written": written, "flagged_metrics": flags,
            "note": "معادلات و قوانین دست‌نخورده ماندند — تعارض فقط flag شد"}


def ingest_file(vault: Vault, path: str | Path) -> dict:
    return ingest_scan(vault, json.loads(Path(path).read_text("utf-8")))
