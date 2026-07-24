---
type: reference
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [onlyfans, spec, fable5]
created: 2026-07-04
updated: 2026-07-04
---

# FABLE5 BUILD SPEC — سیستم عملیاتی feet content
### نسخه‌ی click-by-click برای ساخت مستقیم · مکمل Master Playbook

> هدف: با کمترین اصطکاک، سیستم ردیابی محتوا/فروش/مشتری/مالی/کامپلاینس را بسازی.
> **ترتیب ساخت پیشنهادی:** اول ۴ دیتابیس هسته (Assets → Calendar → Fan CRM → Finance)، بعد بقیه.

---

## 🟢 MINIMAL BUILD (روز ۱ — ۴ دیتابیس کافی برای شروع)

اگر وقت کم داری، فقط این ۴ تا را بساز؛ بقیه را در هفته‌ی ۲ اضافه کن.

1. **Content Assets** (چه محتوایی داری/آماده است)
2. **Content Calendar** (کِی کجا post می‌شود)
3. **Fan CRM** (خریدارها و مرزهایشان)
4. **Finance Tracker** (هر فروش و خالصش)

---

## دیتابیس‌ها — تعریف دقیق فیلد

### DB1 · Master Dashboard  *(بعد از بقیه بساز)*
| Field | Type | مقدار/فرمول |
|---|---|---|
| Metric | text | نام KPI |
| Value | rollup/number | از DBهای مربوط |
| Target | number | هدف |
| Period | select | Week / Month |

**Views:** `This Week` · `Month Overview`

---

### DB2 · Content Assets
| Field | Type | گزینه‌ها |
|---|---|---|
| Asset ID | text (title) | مثل `PED-001` |
| Type | select | photo · video |
| Theme | select | Pedicure · Soles · Cozy · Golden · Seasonal · POV |
| Status | status | idea → shot → edited → ready → posted |
| Platforms | multi-select | OF · X · Reddit · FeetFinder · Fansly |
| Watermark | checkbox | — |
| Metadata-removed | checkbox | — |
| Caption | text | — |
| Shoot date | date | — |
| Performance | number | (کلیک/فروش نسبت‌داده‌شده) |
| Offer | relation → DB4 | — |

**Views:** `Board by Status` (group=Status) · `Ready-to-post` (filter: Status=ready AND Watermark=✓ AND Metadata-removed=✓)

---

### DB3 · Content Calendar
| Field | Type | گزینه‌ها |
|---|---|---|
| Date | date (title یا date) | — |
| Platform | multi-select | OF · X · Reddit · FeetFinder |
| Asset | relation → DB2 | — |
| Caption | text | — |
| CTA | text | — |
| Free/Paid | select | free · paid |
| Status | status | planned → posted |
| Result | number | کلیک/فروش |

**Views:** `Calendar` (by Date) · `This Week` (table, filter: this week)

---

### DB4 · Offers & Pricing
| Field | Type | گزینه‌ها |
|---|---|---|
| Name | text (title) | Starter PPV … |
| Type | select | Free · PPV · Bundle · Custom · VIP |
| Price | number | USD |
| Includes | text | — |
| Funnel-stage | select | acquire · first-buy · repeat · custom · recurring |
| Sales | rollup ← DB9 | count |
| Revenue | rollup ← DB9 | sum(Gross) |

**Views:** `Ladder` (sort by Price) · `Top Sellers` (sort by Revenue)
**Starter rows:** Welcome $0 · Starter PPV $6 · Themed Set $12 · Premium Bundle $30 · Custom Photo $20–40 · Custom Video $50–100 · Monthly VIP $20.

---

### DB5 · Marketing Channels
| Field | Type |
|---|---|
| Channel | text (title) |
| Profile/handle | text |
| Rules | text |
| Allowed-content | text |
| Weekly-posts | number |
| Clicks | number |
| Conversions | number |

**Views:** `Table` · `By Conversion` (sort desc)
**Starter rows:** X · Reddit · FeetFinder · Fansly · IG(SFW).

---

### DB6 · Fan CRM
| Field | Type | گزینه‌ها |
|---|---|---|
| Username | text (title) | — |
| Platform | select | OF · FeetFinder · Fansly |
| First-touch | date | — |
| Purchases | number | — |
| LTV | number | مجموع خرج |
| Interests | multi-select | Pedicure · Soles · Cozy · POV · Custom |
| Boundaries/notes | text | **مهم: مرزها و درخواست‌ها** |
| Status | select | lead · buyer · repeat · VIP · inactive |

**Views:** `By Status` (board) · `VIP list` (filter: Status=VIP) · `Reactivation` (filter: Status=inactive)

---

### DB7 · Experiment Log
| Field | Type |
|---|---|
| Hypothesis | text (title) |
| Channel | select |
| Variable | text |
| KPI | text |
| Result | text |
| Decision | text |
| Date | date |

**Views:** `Running` · `Decided`
**Starter:** ۱۰ آزمایش T1–T10 از Section 13 پلی‌بوک.

---

### DB8 · Compliance Vault
| Field | Type | گزینه‌ها |
|---|---|---|
| Item | text (title) | — |
| Status | status | todo → done |
| Consent | checkbox | — |
| Content-date | date | — |
| Backup-location | text | — |
| Notes | text | — |

**Views:** `Checklist` (board by Status) · `Needs attention` (filter: Status≠done)
**Starter rows:** ۱۱ آیتم چک‌لیست Section 17.

---

### DB9 · Finance Tracker
| Field | Type | فرمول |
|---|---|---|
| Date | date | — |
| Source | select | Sub · PPV · Custom · Tip |
| Gross | number | مبلغ ناخالص USD |
| Platform-fee | formula | `Gross * 0.20` (OF/Fansly) — برای FeetFinder Basic `Gross*0.15` |
| Net | formula | `Gross - Platform-fee - Expense` |
| Expense | number | هزینه (اختیاری در همان ردیف) |
| Category | select | gear · subscription · promo · other |
| Tax-note | text | برای ATO |
| Offer | relation → DB4 | — |

**Views:** `This Month` (filter: this month) · `By Source` (group=Source)
**فرمول Net نمونه (Fable5-style):** `prop("Gross") - prop("Platform-fee") - prop("Expense")`

---

### DB10 · Idea Bank
| Field | Type | گزینه‌ها |
|---|---|---|
| Idea | text (title) | — |
| Type | select | photo · video |
| Pillar | select | Cozy · Pedicure · Golden · Seasonal · POV |
| Priority | select | 1 · 2 · 3 |
| Status | status | idea → queued → shot |

**Views:** `Priority Board` (group=Priority) · `Queued for next shoot` (filter: Status=queued)
**Seed:** ۱۰۰ ایده‌ی Section 7 را اینجا وارد کن (یا top ۲۰ برای شروع).

---

## 🔗 Relation Map (خلاصه)

```
Idea Bank(DB10) ──► Content Assets(DB2) ──► Content Calendar(DB3)
Content Assets(DB2) ──► Offers(DB4) ◄──rollup── Finance(DB9) ──► Fan CRM(DB6)
Marketing Channels(DB5) ──(clicks)──► Fan CRM(DB6)
Experiment Log(DB7) ──informs──► Offers/Calendar/Channels
Compliance Vault(DB8) ──guards──► Content Assets(DB2)
Master Dashboard(DB1) ◄──rollups── همه
```

**روابط کلیدی که باید بسازی (relation fields):**
1. DB2.Offer → DB4  (هر asset به کدام offer فروخته شد)
2. DB3.Asset → DB2  (تقویم به asset)
3. DB9.Offer → DB4  (هر فروش به offer → منبع rollup فروش/درآمد)
4. DB4.Sales/Revenue = rollup از DB9

---

## ▶️ ترتیب ساخت (۳۰–۴۵ دقیقه)
1. DB2 Content Assets → فیلدها + دو view.
2. DB4 Offers → ۷ ردیف starter.
3. DB3 Calendar → relation به DB2.
4. DB6 Fan CRM.
5. DB9 Finance → relation به DB4 + فرمول Net.
6. DB4: rollup Sales/Revenue از DB9.
7. DB8 Compliance → ۱۱ ردیف.
8. DB10 Idea Bank → seed از Section 7.
9. DB5 Channels + DB7 Experiments.
10. DB1 Dashboard → rollupهای KPI (Section 14).

*پایان Build Spec*
