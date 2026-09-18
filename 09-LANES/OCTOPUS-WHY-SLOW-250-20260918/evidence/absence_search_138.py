#!/usr/bin/env python3
"""Absence-proof searches on node 138 for the 12 weak WHY-SLOW-250 entries.
Prints one JSON line per claim: hits + a sample so a hit is never silently
treated as an absence."""
import json
import subprocess

NEEDLES = {
    "W-070": r"SLA|response.?within|پاسخ.*(ساعت|دقیقه)|within (2|two) hours",
    "W-072": r"value.?based.?pricing|per[-_ ]unit|outcome.?based|قیمت.*(نتیجه|واحد)",
    "W-076": r"testimonial|customer.?review|feedback\.(json|jsonl)|رضایت.?مشتری",
    "W-078": r"lead.?time|delivery.?window|capacity.?plan|زمان.?تحویل|ظرفیت.?هفتگی",
    "W-079": r"christmas|new.?year|nowruz|نوروز|کریسمس|gift.?season|فصل.?هدیه",
    "W-082": r"etsy|marketplace|amazon.?handmade|instagram.?shop|فروشگاه.?آنلاین",
    "W-144": r"holdout|hold.?out|fixture.*train|train.*fixture",
    "W-228": r"calendly|booking|appointment|رزرو|نوبت.?دهی",
    "W-229": r"status.?page|case.?status|tracking.?link|پیگیری.?پرونده|وضعیت.?سفارش",
    "W-230": r"whatsapp|twilio|sendsms|\bsms\b|پیامک|واتساپ",
    "W-234": r"\bTAM\b|\bSAM\b|market.?size|اندازه.?بازار",
    "W-235": r"persona|buyer.?interview|پرسونا|مصاحبه.*خریدار",
}
ROOTS = ["/home/ari/ofn/state", "/home/ari/ofn/ofn", "/home/ari/octopus-mesh/bin"]
out = {}
for wid, pat in NEEDLES.items():
    cmd = ("grep -rniE %s %s 2>/dev/null | grep -viE '__pycache__|\\.pyc' | head -4"
           % (json.dumps(pat), " ".join(ROOTS)))
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    lines = [l for l in (r.stdout or "").splitlines() if l.strip()]
    # count without the head cap
    c = subprocess.run(cmd.replace("| head -4", "| wc -l"), shell=True,
                       capture_output=True, text=True, timeout=120)
    n = int((c.stdout or "0").strip() or 0)
    out[wid] = {"hits": n, "sample": [l[:150] for l in lines[:3]], "pattern": pat}
print(json.dumps(out, ensure_ascii=False))
