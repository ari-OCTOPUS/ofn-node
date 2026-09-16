---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: idea
created_by: agent
sources:
  - https://www.getpassionfruit.com/blog/how-to-connect-claude-mcp-to-your-entire-marketing-stack-with-claude-connector
  - https://www.thevibemarketer.com/guides/ai-agent-builders-2025
  - https://www.3pillar.ai/insights/blog/comparison-crewai-langgraph-n8n/
  - https://powerreach.ai/blog/what-the-ai-marketing-stack-that-actually-works-in-2026-looks-like-and-why-most-businesses-are-still-behind/
tags: [marketing, ai-agents, tooling]
created: 2026-07-06
updated: 2026-07-06
---

# ابزارهای موجود برای معماری ایجنت‌های بازاریاب — ممیزی 2026-07-06

> ممیزی پلاگین‌ها/skillهای متصل به Claude Cowork در این سیستم + خلاصه نظر جامعه. کاندید Inbox — verdict آری برای بایگانی در `07 - Knowledge` لازم است.

## ۱. موجودی فعلی (متصل و آماده استفاده)

| لایه | ابزار | چه می‌کند | وضعیت |
|---|---|---|---|
| SEO / Content | **searchfit-seo** (~۲۰ skill + ۳ agent) | seo-audit، content-strategy، content-brief، create-content، keyword-clustering، schema-markup، **ai-visibility (GEO/AEO)**، competitor-analyzer | ✅ آماده |
| Ads | **adspirer-ads-agent** | best-practices کمپین، campaign-performance، keyword-research با CPC واقعی (Google/Meta/LinkedIn/TikTok) | ⚠️ MCP نیاز به auth |
| Outreach / Sales | **sales** plugin | account-research، draft-outreach، call-prep، competitive-intelligence، pipeline-review، create-an-asset | ✅ skillها آماده؛ apollo/outreach/close نیاز auth |
| Data / Prospecting | **zoominfo** | build-list، score-leads، personalize-email، tam-sizer، find-similar | ✅ (وابسته به اکانت ZoomInfo) |
| Data / Community | **common-room**, **grasp** | سیگنال اکانت، contact research، list building | ⚠️ common-room نیاز auth |
| SMB Marketing | **small-business** | content-strategy از داده فروش، run-campaign، canva-creator، lead-triage، customer-pulse | ⚠️ Canva/HubSpot/QuickBooks نیاز auth |
| Web Research | **tavily** (search/extract/crawl/research)، Parallel web_search، exa | تحقیق چندمنبعه با citation؛ crawl سایت رقبا | ✅ tavily/Parallel؛ exa نیاز auth |
| کانال‌ها | **slack**، **monday.com**، **wix** | پیام‌رسانی تیمی، برد کمپین/CRM سبک، سایت/فروشگاه | ⚠️ اکثراً نیاز auth |
| Browser | **Claude in Chrome**, computer-use | اتوماسیون وب‌اپ‌های بدون MCP | ✅ |
| ساخت ایجنت | **skill-creator**، **create-cowork-plugin**، **scheduled tasks**، **artifacts** | ساخت skill/plugin سفارشی، اجرای زمان‌بندی‌شده، داشبورد زنده | ✅ کلیدی‌ترین لایه |
| زیرساخت سنگین‌تر | **datarobot-agent-assist** (LangGraph/CrewAI scaffold + deploy + monitoring)، **pixeltable** (پایپ‌لاین داده/RAG)، **qdrant** (vector DB) | وقتی ایجنت باید خارج از Cowork زندگی کند | ✅ skillها آماده |

## ۲. توصیه استفاده (به ترتیب ROI برای این vault)

1. **شروع بدون کد، داخل Cowork:** searchfit-seo + tavily + scheduled task = ایجنت content/SEO هفتگی برای Lead-نقاشی و Ziman Galerry. هزینه صفر اضافه، سریع‌ترین نتیجه.
2. **لایه دوم — outreach:** sales:draft-outreach + zoominfo برای B2B؛ برای بیزنس محلی (نقاشی) بیشتر Google Business/SEO محلی می‌ارزد تا cold outreach.
3. **سفارشی‌سازی:** با skill-creator یک skill اختصاصی «بازاریاب Lead-نقاشی» بساز که SOP و لحن آری را داشته باشد؛ با schedule اجرای دوره‌ای.
4. **فقط اگر لازم شد:** ایجنت مستقل خارج از Cowork با LangGraph (production) یا CrewAI (پروتوتایپ چند-ایجنته) — via datarobot-agent-assist. برای حجم فعلی توصیه نمی‌شود (پیچیدگی > سود).

## ۳. نظر جامعه (خلاصه تحقیق وب)

- **اجماع:** مارکترها با n8n/Zapier شروع کنند؛ دولوپرها LangGraph برای production و CrewAI برای پروتوتایپ. هیچ فریمورک واحدی «بهترین» نیست.
- **Stack رایج ۲۰۲۶:** Clay + Claude + n8n + بازبینی انسانی قبل از ارسال به مشتری.
- **ترند:** AEO/GEO (دیده‌شدن برند در جواب‌های AI) دارد جای SEO کلاسیک را می‌گیرد — skill ai-visibility دقیقاً همین است.
- **هشدار:** «agent-washing» زیاد است؛ فقط ۱۵٪ استک‌ها واقعاً اجرای تکراری را از انسان می‌گیرند. Outreach قالبی ۳ سال است response rate نزولی دارد — شخصی‌سازی + review انسانی شرط است.

## ۴. قیود این vault (یادآوری)

- هیچ ارسال/publish خودکار بدون verdict آری؛ هر ایجنت بازاریاب باید draft-only باشد (approve-first مغز دوم).
- خروجی ایجنت‌ها → Inbox-first؛ audit log تاریخ‌دار در لاگ پروژه مربوطه.

## قدم‌های بعدی پیشنهادی

- [ ] verdict آری: کدام پروژه اول؟ (پیشنهاد: Lead-نقاشی)
- [ ] authorize کردن connectorهای لازم در تنظیمات claude.ai (حداقل: Canva اگر تولید بصری می‌خواهیم)
- [ ] ساخت skill سفارشی بازاریاب با skill-creator بعد از verdict
