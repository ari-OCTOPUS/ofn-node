#!/usr/bin/env python
"""
Generate the cover page for the AGI Investment Landscape report using ReportLab canvas.
Template 01: HUD Data Terminal - Ultra-Thick Vertical Anchor Line
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfgen import canvas

# ── Fonts ──
FONT_DIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont('TimesNewRoman', os.path.join(FONT_DIR, 'times.ttf')))
pdfmetrics.registerFont(TTFont('TimesNewRomanBold', os.path.join(FONT_DIR, 'timesbd.ttf')))
pdfmetrics.registerFont(TTFont('Calibri', os.path.join(FONT_DIR, 'calibri.ttf')))
pdfmetrics.registerFont(TTFont('CalibriBold', os.path.join(FONT_DIR, 'calibrib.ttf')))
registerFontFamily('TimesNewRoman', normal='TimesNewRoman', bold='TimesNewRomanBold')

# ── Palette ──
PAGE_BG      = colors.HexColor('#f1f1f0')
HEADER_FILL  = colors.HexColor('#766c50')
ACCENT       = colors.HexColor('#1f7693')
TEXT_PRIMARY  = colors.HexColor('#252422')
TEXT_MUTED    = colors.HexColor('#7e7c74')

# ── Page ──
W, H = A4
U = W * 0.05  # base spacing unit
OUTPUT = r"F:\backup\cover.pdf"

c = canvas.Canvas(OUTPUT, pagesize=A4)
c.setTitle('AGI Investment Landscape August 2026')
c.setAuthor('Z.ai')

# ═══════════════════════════════════════════
# Layer 0: Background fill
# ═══════════════════════════════════════════
c.setFillColor(PAGE_BG)
c.rect(0, 0, W, H, fill=True, stroke=False)

# ═══════════════════════════════════════════
# Layer 1: Grid background (CLIPPED)
# ═══════════════════════════════════════════
c.saveState()
clip_path = c.beginPath()
clip_path.rect(0, 0, W, H)
c.clipPath(clip_path, stroke=0)

grid_color = colors.Color(0.463, 0.424, 0.314, alpha=0.04)  # HEADER_FILL at 4% opacity
grid_spacing = 50
c.setStrokeColor(grid_color)
c.setLineWidth(0.5)

# Horizontal grid lines
for y in range(0, int(H) + grid_spacing, grid_spacing):
    c.line(0, y, W, y)
# Vertical grid lines
for x in range(0, int(W) + grid_spacing, grid_spacing):
    c.line(x, 0, x, H)

c.restoreState()

# ═══════════════════════════════════════════
# Layer 2: Structure lines
# ═══════════════════════════════════════════
# Left anchor line (thick)
anchor_x = 0.12 * W
c.setStrokeColor(HEADER_FILL)
c.setLineWidth(6)
c.line(anchor_x, 0.1 * H, anchor_x, 0.9 * H)

# Meta separator line
content_x = anchor_x + 30
meta_y = 0.70 * H
c.setStrokeColor(colors.Color(0.463, 0.424, 0.314, alpha=0.35))
c.setLineWidth(1)
c.line(content_x, meta_y, content_x + W * 0.4, meta_y)

# Bottom accent stripe
c.setFillColor(ACCENT)
c.rect(0, 0, W, 4, fill=True, stroke=False)

# ═══════════════════════════════════════════
# Layer 3: Content
# ═══════════════════════════════════════════
content_x = anchor_x + 30

# A - Kicker (report type)
c.setFillColor(colors.Color(0.149, 0.149, 0.133, alpha=0.60))
c.setFont('Calibri', 16)
c.drawString(content_x, H - 0.15 * H, 'RESEARCH INTELLIGENCE REPORT')

# B - Hero Title
# "AGI Investment" in primary, "Landscape" in accent
title_y = H - 0.30 * H
c.setFillColor(TEXT_PRIMARY)
c.setFont('TimesNewRomanBold', 52)
c.drawString(content_x, title_y, 'AGI Investment')

# Measure "Landscape" to position below
c.setFont('TimesNewRomanBold', 52)
tw = c.stringWidth('AGI Investment', 'TimesNewRomanBold', 52)
c.setFillColor(ACCENT)
c.drawString(content_x, title_y - 60, 'Landscape')

# C - Summary
summary_y = H - 0.52 * H
c.setFillColor(colors.Color(0.149, 0.149, 0.133, alpha=0.85))
c.setFont('TimesNewRoman', 16.5)
summary_lines = [
    'How companies and nations are investing in artificial general intelligence',
    'through policy, geopolitics, regulation, and exotic non-traditional',
    'approaches \u2014 25+ investment topics across 8 strategic categories.',
]
line_h = 16.5 * 1.6
for i, line in enumerate(summary_lines):
    c.drawString(content_x, summary_y - i * line_h, line)

# D - Meta (date)
meta_y_text = H - 0.76 * H
c.setFillColor(TEXT_MUTED)
c.setFont('Calibri', 13)
c.drawString(content_x, meta_y_text, 'Date')
c.setFillColor(TEXT_PRIMARY)
c.setFont('Calibri', 19)
c.drawString(content_x, meta_y_text - 24, 'August 2026')

# Footer
c.setFillColor(colors.Color(0.149, 0.149, 0.133, alpha=0.50))
c.setFont('Calibri', 10)
c.drawString(content_x, 0.05 * H + 10, 'Prepared by Z.ai  |  Confidential Research Report')

c.save()
print(f"Cover PDF generated: {OUTPUT}")
