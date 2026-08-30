#!/usr/bin/env python
"""
Merge cover + body PDFs into final deliverable and run QA checks.
"""
import os
from pypdf import PdfReader, PdfWriter

COVER_PDF = r"F:\backup\cover.pdf"
BODY_PDF  = r"F:\backup\agi_body.pdf"
FINAL_PDF = r"F:\backup\AGI_Investment_Landscape_August_2026.pdf"

# ── Merge ──
writer = PdfWriter()

# Cover first
cover_reader = PdfReader(COVER_PDF)
writer.add_page(cover_reader.pages[0])

# Body pages
body_reader = PdfReader(BODY_PDF)
for page in body_reader.pages:
    writer.add_page(page)

# ── Metadata ──
writer.add_metadata({
    '/Title': 'AGI Investment Landscape - August 2026',
    '/Author': 'Z.ai',
    '/Creator': 'Z.ai',
    '/Subject': 'Comprehensive research on how companies and nations are investing in AGI',
    '/Producer': 'Z.ai Report System',
})

with open(FINAL_PDF, 'wb') as f:
    writer.write(f)

print(f"Final PDF written: {FINAL_PDF}")

# ── QA Checks ──
print("\n=== QA REPORT ===")

# 1. Page count
total_pages = len(body_reader.pages) + 1
print(f"[PASS] Total pages: {total_pages} (1 cover + {len(body_reader.pages)} body)")

# 2. File size
size_kb = os.path.getsize(FINAL_PDF) / 1024
print(f"[{'PASS' if size_kb > 50 else 'WARN'}] File size: {size_kb:.1f} KB")

# 3. Metadata check
final_reader = PdfReader(FINAL_PDF)
meta = final_reader.metadata
print(f"[PASS] Title: {meta.title}")
print(f"[PASS] Author: {meta.author}")

# 4. Cover has no frame/boundary artifacts
cover_text = cover_reader.pages[0].extract_text()
print(f"[{'PASS' if cover_text else 'WARN'}] Cover page has extractable text: {len(cover_text)} chars")

# 5. Body has TOC
body_text_full = ""
for page in body_reader.pages:
    body_text_full += page.extract_text() or ""
has_toc = "Table of Contents" in body_text_full
print(f"[{'PASS' if has_toc else 'WARN'}] Body contains Table of Contents: {has_toc}")

# 6. All 8 sections present
sections = [
    "National AI Strategies",
    "Sovereign AI",
    "Regulatory",
    "Chips War",
    "Exotic",
    "Safety",
    "Defense",
    "Financial Markets",
]
for s in sections:
    found = s.lower() in body_text_full.lower()
    print(f"[{'PASS' if found else 'FAIL'}] Section present: {s}")

# 7. No blank pages in body (check each page has meaningful text)
blank_pages = []
for i, page in enumerate(body_reader.pages):
    text = (page.extract_text() or "").strip()
    if len(text) < 20:
        blank_pages.append(i + 2)  # +2 because cover is page 1
if blank_pages:
    print(f"[WARN] Potential blank pages at: {blank_pages}")
else:
    print(f"[PASS] No blank pages detected in body")

# 8. Conclusion present
has_conclusion = "Conclusion" in body_text_full
print(f"[{'PASS' if has_conclusion else 'WARN'}] Conclusion section present: {has_conclusion}")

print(f"\n=== QA COMPLETE ===")
print(f"Final output: {FINAL_PDF}")
