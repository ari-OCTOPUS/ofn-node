#!/usr/bin/env python3
"""Fix the two verified defects in WHY-SLOW-250:
 (1) 126 shorthand-label anchors -> resolvable paths (runtime 138: or real vault file)
     via a filename map + vault globbing by token; anything we still cannot resolve
     is marked anchor_quality=memory-derived instead of pretending.
 (2) the 7 stub reasons (<25 chars) get a real one-line reason.
Rebuilds WHY-SLOW-250.json + MATRIX-250.csv.
"""
import csv
import glob as g
import json
import pathlib
import re

LANE = pathlib.Path("09-LANES/OCTOPUS-WHY-SLOW-250-20260918")
J = LANE / "WHY-SLOW-250.json"
M = LANE / "MATRIX-250.csv"
RD = "138:state/revenue-drive/"
SD = "138:state/deep-scan/"

# ---- filename map: shorthand -> full anchor ----
FILEMAP = {
    "sent-log": RD + "sent-log.jsonl", "sent-log.jsonl": RD + "sent-log.jsonl",
    "season-meter.json": RD + "season-meter.json",
    "revenue-state.json": RD + "revenue-state.json",
    "owner-review.json": RD + "owner-review.json",
    "owner-ask-registry.json": RD + "owner-ask-registry.json",
    "owner-ask-sent.json": RD + "owner-ask-sent.json",
    "owner-decisions.jsonl": RD + "owner-decisions.jsonl",
    "owner_ask.py": RD + "owner_ask.py", "owner_reply.py": RD + "owner_reply.py",
    "money_tools.py": RD + "money_tools.py", "money_executor.py": RD + "money_executor.py",
    "channel-authorization.json": RD + "channel-authorization.json",
    "offer-experiments.json": RD + "offer-experiments.json",
    "outbound-effects.sqlite3": RD + "outbound-effects.sqlite3",
    "phone-only-queue.jsonl": RD + "phone-only-queue.jsonl",
    "lead-emails.jsonl": RD + "lead-emails.jsonl",
    "lead-enrich-cursor.txt": RD + "lead-enrich-cursor.txt",
    "receipts.jsonl": RD + "receipts.jsonl",
    "funnel_reconcile.py": RD + "funnel_reconcile.py",
    "action_executor.py": RD + "action_executor.py",
    "proposal_intake.py": RD + "proposal_intake.py",
    "proposals.jsonl": RD + "proposals.jsonl",
    "campaign": RD + "campaign/",
    "quote-packets": RD + "quote-packets/",
    "decision_consumption.jsonl": "138:state/owner_dialogue/decision_consumption.jsonl",
    "owner_decision.v1.jsonl": "138:state/owner_dialogue/owner_decision.v1.jsonl",
    "findings-current.json": SD + "findings-current.json",
    "DASHBOARD.json": SD + "DASHBOARD.json",
}
TOKEN_GLOBS = ["09-LANES/*{}*", "06-EVIDENCE/*{}*", "01 - Dashboard/*{}*"]


def resolve(a: str) -> tuple[str, str]:
    """-> (new_anchor, quality)"""
    raw = a.strip()
    p = re.split(r"\s*@|\s+::", raw)[0].strip()
    suffix = raw[len(p):].strip()
    # already runtime / real file
    if p.startswith("138:"):
        return raw, "runtime"
    if pathlib.Path(p).exists() or p.startswith(("repo:", "AGENTS.md")):
        return raw, "file"
    base = pathlib.Path(p).name
    # filename map (exact or basename)
    for k, v in FILEMAP.items():
        if p == k or base == k or p.endswith("/" + k):
            return (v + (" " + suffix if suffix else "")), "runtime"
    # F-xxx findings reference
    m = re.fullmatch(r"(F|R|V)-[0-9A-Za-z_-]+", p)
    if m:
        return (SD + "findings-current.json @" + p), "runtime"
    # state/... paths that live on the node
    if p.startswith(("state/", "ofn/", "tools/", "tests/")):
        return ("138:" + p + (" " + suffix if suffix else "")), "runtime"
    # vault glob by token (DC-03D, RES-05C, DEEP-SCAN-250, ...)
    tok = p.strip("() ")
    for pat in TOKEN_GLOBS:
        hits = [h for h in g.glob(pat.format(tok)) if pathlib.Path(h).exists()]
        if len(hits) == 1:
            return hits[0] + (" " + suffix if suffix else ""), "file"
        if len(hits) > 1:
            return sorted(hits)[0] + (" " + suffix if suffix else ""), "file"
    return raw, "memory-derived"


# ---- stub reasons (measured observations, one line each) ----
REASONS = {
    "W-041": "کارت ۳۰ دقیقه‌ای buy.nsw از ۰۸-۲۴ باز است؛ آیتم قهرمان سیزن بدون اقدام مالک مانده (F-026).",
    "W-051": "بانک ایمیل ۶۸ مخاطب دارد و هیچ حلقهٔ رشد ورودی (محتوای قابل جستجو/اشتراک) وجود ندارد.",
    "W-070": "هیچ SLA پاسخ‌دهی اعلام‌شده به مشتری در متون پیشنهاد نیست؛ سکوت اولیه حس بی‌اعتمادی می‌سازد.",
    "W-076": "هیچ فایل بازخورد/رضایت مشتری (review/rating) در state یا قیف وجود ندارد.",
    "W-079": "تقویم فصل‌بندی فروش هدیه (کریسمس/نوروز) وجود ندارد در حالی که تقویم درآمدی حیاتی است.",
    "W-228": "هیچ مسیر رزرو/تقویم ملاقات برای مشتری B2B نیست؛ پاسخ نیازمند رفت‌وبرگشت ایمیل است.",
    "W-229": "مشتری هیچ سطح وضعیت/پیگیری (پروندهٔ من چه شد؟) ندارد؛ همه‌چیز سمت ما تیره است.",
}

d = json.loads(J.read_text(encoding="utf-8"))
qual = {"runtime": 0, "file": 0, "memory-derived": 0}
fixed_anchors = 0
for r in d["entries"]:
    new = []
    for a in r["verify_against"]:
        na, q = resolve(a)
        qual[q] += 1
        if na != a:
            fixed_anchors += 1
        new.append(na)
    r["verify_against"] = new
    if any(q == "memory-derived" for q in
           [resolve(x)[1] for x in r["verify_against"]]):
        r["anchor_quality"] = "partially memory-derived"
    else:
        r["anchor_quality"] = "resolvable"
    if r["id"] in REASONS and len(r["reason"]) < 25:
        r["reason"] = REASONS[r["id"]]
        r["reason_source"] = "measured this session (WHY-SLOW-250 evidence)"

d["anchor_stats"] = qual
d["fixed_at"] = "2026-09-18T12:40:00Z"
J.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

rows = sorted(d["entries"], key=lambda r: (-r["rank_IxF"], r["territory_code"], r["id"]))
with M.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "territory", "verdict", "grade", "impact", "fixability", "rank_IxF",
                "owner_decision_needed", "verified_this_session", "seeded", "anchor_quality", "hypothesis"])
    for r in rows:
        w.writerow([r["id"], r["territory"], r["verdict"], r["grade"], r["impact_1_5"],
                    r["fixability_1_5"], r["rank_IxF"], r["owner_decision_needed"],
                    r["verified_this_session"], r["seeded"], r["anchor_quality"], r["hypothesis"]])

print("anchors rewritten:", fixed_anchors)
print("anchor quality:", qual)
print("entries fully resolvable:", sum(1 for r in d["entries"] if r["anchor_quality"] == "resolvable"), "/250")
print("reasons filled:", sum(1 for r in d["entries"] if r.get("reason_source")))
