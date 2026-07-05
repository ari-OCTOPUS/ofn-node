---
type: report
status: done
tags: [memory, phase0, security, recon]
created: 2026-07-04
created_by: claude-cowork
---

# 00 — Phase 0 Recon Report (SECURITY GATE + ROTATION GATE + Inventory)

**تاریخ اجرا:** 2026-07-04 · **ابزار:** Claude (Cowork) + python census/scanner · **قلمرو:** vault root `C:\Users\Armin\Desktop\backup` (تأییدشده)

## 🔴 Verdict — گیت‌ها

| گیت | وضعیت | نتیجه |
|---|---|---|
| ROTATION GATE (root `ROTATION_CHECKLIST.md`) | **۲۳/۲۳ ردیف OPEN — ۴ CRITICAL باز** (Monero seed · Bybit · OKX · Anthropic keys)؛ ۷ HIGH، ۱۲ MEDIUM | ⛔ **HALT بعد از Phase 0** — ingest/embedding ممنوع تا بسته‌شدن ۴ ردیف CRITICAL |
| SECRET SCAN (Phase 0b) | ۱ hit جدید: `03 - Projects/Lead-نقاشی/Lead-نقاشی.md` (الگوی generic-assignment) — **در checklist نیست** | ⚠️ مالک بررسی کند؛ اگر واقعی است → ردیف جدید در checklist + rotation |
| BACKUP GATE (Prime Directive 0) | تأیید نشده | ⛔ قبل از هر mutation در Phase ≥1، مالک باید backup رمزنگاری‌شدهٔ خارج از vault را تأیید کند |

## ۱) Census (فقط مسیرهای قابل‌دسترس؛ درخت‌های excluded جدا شمرده شد)

- **کل فایل‌های قابل‌دسترس:** 1,720 · بعلاوهٔ excluded-trees: `_code` 4753 · `_Duplicates` 303 · `secrets-export` 14
- **کاندیدای ingest (فقط `*.md` پس از ignore-set + secret-scan):** **372** نوت (از 385 md کل)
- **excluded فایل‌به‌فایل:** 31 (جزئیات: [[EXCLUDED]])

| پوشهٔ سطح‌بالا | فایل |
|---|---|
| 03 - Projects | 825 |
| 08 - Assets | 625 |
| 07 - Knowledge | 110 |
| 04 - Architect System | 84 |
| 00 - Inbox | 43 |
| 01 - Dashboard | 7 |
| _Templates | 6 |
| 05 - Agents | 4 |
| 06 - Architecture Maps | 4 |
| 10 - Telegram processing | 4 |
| 02 - Life OS | 2 |

| پسوند (top) | تعداد |
|---|---|
| .jpg | 862 |
| .md | 385 |
| .py | 181 |
| .pdf | 61 |
| .txt | 25 |
| .json | 21 |
| .jpeg | 20 |
| (none) | 17 |
| .sh | 16 |
| .bat | 15 |

## ۲) زبان و طبقه‌بندی (Phase 0e)

- **زبان بدنه:** mixed 270 · fa 51 · en 51 → embedding چندزبانه (bge-m3) الزامی است ✅ (با LOCKED DEFAULTS سازگار)
- **طبقه‌بندی:** project 106 · agent-report 69 · knowledge 59 · reference 53 · other 41 · index/dashboard 14 · log 13 · prompt 9 · template 5 · person 2 · inbox 1
- **لایهٔ process-log (خارج از recall):** agent-report + log + prompt ≈ 91 نوت (~24٪ کل) — جداسازی این لایه واقعاً ضروری است.

## ۳) Frontmatter و Schema

- 277/372 نوت frontmatter دارند (95 بدون FM → کاندیدای normalize در Phase 6).
- **Schema drift:** `Property Schema.md` فقط ۱۲ کلید تعریف می‌کند، ولی ۱۵+ کلیدِ پرکاربردِ خارج از schema در استفاده است: `epistemic_status`(77) `sources`(38) `created_by`(35) `kind`(20) `owner`(16) `salience`(14) … → یا schema به‌روز شود یا نوت‌ها normalize (تصمیم مالک، Phase 6).
- **آنارشی status:** ۱۸ مقدار متمایز، شامل statusهای جمله‌ایِ فارسی (`proposal — منتظر verdict آری…`) → کاندیدای controlled vocabulary.
- ⚠️ `06 - Architecture Maps/Property Schema.md` بایت غیر-UTF-8 دارد (خطای decode در ~3141) — قابل fix با یک بار re-save.

## ۴) گراف لینک (پس از اصلاح resolver: لینک‌های path-style و `\|` جدول‌ها)

- **اتصال:** 62.6٪ نوت‌ها حداقل یک لینک دارند · میانگین out-degree: 3.28
- **Orphan واقعی: 138** (لیست کامل در پیوست) — به تفکیک: project 71 · knowledge 47 · reference 8 · بقیه 12
- **Baseline برای CONNECTIVITY DELTA (متر اصلی موفقیت):** orphans=138, linked=62.6٪, avg_outdeg=3.28
- **لینک‌های شکستهٔ واقعی:** 21 (بیشترشان به فایل‌های excluded اشاره می‌کنند مثل `SECRETS-ROTATION-CHECKLIST` و `INGEST-EXCLUDED-SECRETS` — یعنی شکسته نیستند، به قرنطینه اشاره دارند)
- **Hub های اصلی:** SYSTEM-BLUEPRINT-v1 (78) · DECISIONS (66) · SYSTEM-BLUEPRINT-v2 (57) · scout synthesis 2026-07-04 (51) · architect/PROJECT (50) · HANDOFF (43)

## ۵) Duplicates

- **صفر** خوشهٔ exact-dup (hash) بین کاندیداها؛ **صفر** فایل با الگوی `(n)`/`- Copy` → پاکسازی 2026-07-03 مؤثر بوده. `_Duplicates/` (303 فایل) دست‌نخورده در قرنطینه.

## ۶) دارایی‌های meta (برای build روی آن‌ها، نه جایگزینی)

- `.base`: `01 - Dashboard/{Inbox,Projects,Scout Digests}.base` (۳)
- MOC/Index: ۱۰ فایل `_Index - *` + `SYSTEM_MAP` + `ECOSYSTEM` · Templates: ۶
- Validators و gitleaks.toml در `04 - Architect System/scripts/` موجودند (gitleaks binary در sandbox نبود — قبل از Phase 1 از ویندوز اجرا شود).

## ۷) ⚠️ Discrepancies برای تأیید مالک

1. **`_Archive/` وجود ندارد** — snapshot پاکسازی 2026-07-03 می‌گوید 3.2GB به آن منتقل شد. یا عمداً حذف/منتقل شده (مجاز بود) یا مشکل sync. تأیید کن.
2. Secret-hit جدید در `Lead-نقاشی.md` (بخش Verdict).
3. کپی سرگردان `ROTATION_CHECKLIST - هیپنوتیزم.md` در `07 - Knowledge` — احتمالاً جابه‌جایی اشتباه؛ نخواندمش.
4. Property Schema encoding (بخش ۳).

## ۸) STOP — منتظر «go»

طبق rotation gate، **Phase 1..7 قفل است** تا: (الف) بسته‌شدن ۴ ردیف CRITICAL توسط مالک، (ب) تأیید backup رمزنگاری‌شده، (ج) تعیین تکلیف hit جدید Lead-نقاشی. Recon کامل است؛ state این run در `/_memory/` و JSON های خام در sandbox موجود است.

---

## پیوست — لیست کامل 138 orphan

- `00 - Inbox/Prompt - اتصال همه پروژه‌ها به مغز کنترل.md`
- `03 - Projects/Accounting/2/SETUP_GUIDE.md`
- `03 - Projects/Crypto - etoro/lunarcrush-scraper/README.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/ARCHITECTURE_REVIEW_2026-07-02.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/CLAUDE_PROJECT_SETUP.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/CONFIG_parameters.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/GLOSSARY.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/MASTER_INSTRUCTIONS.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/PROJECT_FULL_CONTEXT.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/PROJECT_MANIFEST.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/ROADMAP.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-00_master_synthesis.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-01_architecture.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-02_financial_model.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-03_publishing.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-04_memory.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-05_human_approval_queue.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-06_audit_log.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-07_constitution_gate.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-08_eval.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-09_leads_consent_crm.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-10_prompts.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-11_engineering.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-12_australia.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-13_market_research.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/10_knowledge_base/KB-14_ecosystem.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/20_specs/MVP_system_requirements.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/20_specs/THREAT_MODEL.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/30_process/BRUSHLINE_theory_completion_prompt.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/30_process/CONSISTENCY_REPORT.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/30_process/DEEP_RESEARCH_PROMPT.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-00_operations_index.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-01_quoting_estimation_framework.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-02_site_inspection_checklist.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-03_job_workflow_sop.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-04_customer_journey.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-05_sales_scripts_objections.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-06_marketing_content_system.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-07_website_landing_structure.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-08_crm_pipeline.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/40_operations/OPS-09_nsw_operational_compliance.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/50_interface/TG-01_telegram_single_channel_design.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/90_reference/_REFERENCE_NOTE.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/99_archive/DEDUP_NOTE.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/CLAUDE_SELF_PROMPT.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/README.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/BRUSHLINE_CAPABILITIES.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/DEPLOY.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/PROMPTS_BACKLOG.md`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/infra-control/RUNBOOK.md`
- `03 - Projects/Lead-نقاشی/کاریابی/01_الگوهای_مخفی_نقاشی_سیدنی.md`
- `03 - Projects/Lead-نقاشی/کاریابی/02_طرح_ربات_تلگرام.md`
- `03 - Projects/Lead-نقاشی/کاریابی/03_roadmap_autonomous_bot.md`
- `03 - Projects/Lead-نقاشی/کاریابی/04_hunter_agent_prompt.md`
- `03 - Projects/Lead-نقاشی/کاریابی/06_پرامپت‌های_تحقیقاتی_گسترش_لیدگیری.md`
- `03 - Projects/Lead-نقاشی/کاریابی/bot/README.md`
- `03 - Projects/Lead-نقاشی/کاریابی/bot/prompts/hunter.md`
- `03 - Projects/Mining/02 - Code/Ai bots/LIVE_TEST_GUIDE.md`
- `03 - Projects/Mining/02 - Code/Ai bots/sentinel/SETUP_GUIDE.md`
- `03 - Projects/Mining/02 - Code/Ai bots/sentinel/TELEGRAM_SETUP.md`
- `03 - Projects/Mining/02 - Code/Robo-data/TESSERACT_بسته_آپدیت_v0.4_DualTrack.md`
- `03 - Projects/Mining/02 - Code/Robo-data/TESSERACT_بسته_آپدیت_v0.4_PQC.md`
- `03 - Projects/Ziman Galerry/control-brain/README.md`
- `03 - Projects/Ziman Galerry/control-brain/autostart/README.md`
- `03 - Projects/Ziman Galerry/ziman-agent/README.md`
- `03 - Projects/Ziman Galerry/ziman-agent/drafts/EXAMPLE-draft-offline.md`
- `03 - Projects/اونلی فنز/research-results/P1-channel-map.md`
- `03 - Projects/اونلی فنز/research-results/P10-analytics-experiment-loop.md`
- `03 - Projects/اونلی فنز/research-results/P3-reddit-engine.md`
- `03 - Projects/اونلی فنز/research-results/P4-persona-hooks.md`
- `03 - Projects/اونلی فنز/research-results/P5-funnel-geoblock.md`
- `03 - Projects/اونلی فنز/research-results/P6-owned-audience.md`
- `03 - Projects/اونلی فنز/research-results/P7-dm-automation.md`
- `03 - Projects/اونلی فنز/research-results/P8-s4s-network.md`
- `03 - Projects/اونلی فنز/research-results/P9-repurposing-pipeline.md`
- `04 - Architect System/architect/01-Project/INDEX.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-1-REPORT.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-2-REPORT.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-3-REPORT.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-4-REPORT.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-5-REPORT.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-6-REPORT.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-7-REPORT.md`
- `04 - Architect System/architect/04-Docs/fusion-audit/PASS-8-REPORT.md`
- `04 - Architect System/architect/_meta/DELETION-MANIFEST.md`
- `04 - Architect System/mycelial-arch.v-final.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/01_AI/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/02_Consciousness/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/03_Quantum/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/04_Mining/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/05_Neuroscience/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/06_Robotics/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/07_Marketing/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/08_Business/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/09_Prompts/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/10_Research/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/11_Experiments/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/12_Architecture/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/13_Frameworks/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/14_Workflows/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/15_Ideas/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/16_Future/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/17_Archive/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/DecisionLog.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/Experiments.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/Frameworks.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/INDEX.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/Ideas.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/KnowledgeGraph.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/LessonsLearned.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/OpenQuestions.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/Projects.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/PromptLibrary.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/README.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/Research.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/Roadmap.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/TODO.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/Timeline.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Fusion-World/CONTEXT_handoff_EN.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Fusion-World/THEORY_seam_detective.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/00_RESEARCH_PROMPTS.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/Hamfazi_Qodrat_Dual_Register_v1.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P0_scope_epistemic_guardrails.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P1_mechanism_map.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P2_method_taxonomy.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P2b_customization_methods.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P3_susceptibility_predictors.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P4_cross_domain_flow_peak.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P6_skeptical_audit.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/P7_final_synthesis.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Hypnosis-Research/nodes/X1_fusion_vs_real_hypnosis.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Neuro-HRV-Nof1/00-HANDOFF-context.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Neuro-HRV-Nof1/01-master-prompt.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Neuro-HRV-Nof1/neuro-research-prompt-checklist.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/PROJECT_EXPORT_COMPLETE.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/Silabi-Bot/roadmap.md`
- `07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/_PROJECT_INSTRUCTIONS.md`
- `CLAUDE.md`
