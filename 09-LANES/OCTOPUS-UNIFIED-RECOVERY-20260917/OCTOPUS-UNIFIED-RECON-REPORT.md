# OCTOPUS-UNIFIED-RECON-REPORT — مأموریت RECOVERY-AND-SURGICAL-ROADMAP
MISSION=OCTOPUS-UNIFIED-RECOVERY-AND-SURGICAL-ROADMAP-20260917 · GOV_VERSION=V8 · LADDER=L2
MODE=READ_ONLY_RESEARCH_PLUS_ADDITIVE_REPORTING · START_UTC=2026-09-17T00:45:00Z (پس از رأی مالک) · END_UTC=2026-09-17T01:37:57Z
رأی مالک (ورودی این مأموریت، عیناً): «من مالکم و با این ایجنت کاملا موافقم موبه مو اجرا کن» → **1B (مدل فدرال) · 2A (هیچ حذف) · 3B (افزاینده‌فقط) · 4D (ترتیب safety→revenue→architecture→cognition)**

## executive verdict
OCTOPUS یک سامانهٔ چندبدنهٔ فدرال است (۱B) با حافظهٔ عظیمِ preserved: بدنهٔ سورس کانونی ofn-node/GitHub، بدنهٔ دانش/تصمیم F:\backup (۷۱,۲۳۵ فایل/۱۶.۵GB)، بدنهٔ deploy زنده روی 138، و سه بدنهٔ فرعی (Armin/langar/vbaa). **سه یافتهٔ حاکمیتی این نشست:** (۱) بدنهٔ runtime روی 138 (HEAD `63938eb`) از GitHub main (`dba9971`) جلوتر/واگراست — سه کپی واگرای همان پروژه؛ (۲) فقط ۸ از ۱۶۵ شاخه در main ادغام شده‌اند و ۱۵۷ شاخه محتوای یکتای unmerged دارند — «main» نوک کوه یخ است؛ (۳) کد کانونیک فایل **`HALT-ALL`** را می‌خواند درحالی‌که مستندات `HALT` می‌گویند (تأیید سورس). هیچ جراحی اجرا نشد؛ ۱۱ جراحی PROPOSED_ONLY با کلاس S0-S5 و ۱۰ کارت تصمیم تحویل شد.

## visibility/credential boundary
ari322 (https, keyring). مرئی: همهٔ repo data + rulesets/workflows/checks/reviews/alerts-metadata. نامرئی: audit log سازمان، job-log کامل، 180/182 امروز (ssh نشد). UNKNOWN هرجا شاهد نبود.

## فاز صفر — roots
ROOTS-INVENTORY.csv: همهٔ ریشه‌های F:\ (شامل ~۶۵ worktree)، کلون‌های ایزوله، .zcode، nested .git (depth≤3). Obsidian بسته بود؛ baseline dirty ثبت شد (بدون stash/reset). **runtime 138 فقط‌خواندنی:** HALT غایب (مسیرهای /home/ari/HALT و /HALT)؛ HEAD=63938eb (main محلی، ۴۵ dirty)؛ ۸۰ unit-file اُکتوپوس؛ پروسه‌های زنده: octopus-mesh×۵ + bridge + ofn.run + heartbeat؛ WAL=۰B.

## فاز یک — inventory کامل
چهار repo (امروز): شاخه‌ها 164/3/3/4 (ls-remote)، HEADهای verify، tags 16/0/0/0، releases 0، CODEOWNERS (`* @Elahe-z @aram-ui` GOV-V6)، ruleset فقط main (۴ قاعده)، ۲ alert باز telegram_bot_token. پنجره: ۲۳۲ commit یکتا (همه branch-only) + Armin/langar هرکدام ۲ merge. **BRANCH-ANALYSIS: 8 merged / 157 unmerged-ahead** (بزرگ‌ترین‌ها 213/213/209/126). والت: census امروز (۷۸ دقیقه): 71,235/16.5GB dedup؛ 315,445/66.4GB خام؛ excluded بزرگ: worktrees کلود 121,718 فایل/32.3GB.

## فاز دو — classification (چکیده)
قواعد ثابت اعمال شد (doc≠wired، test≠live، branch≠landed…). نقش‌های کلیدی: ofn-node=ARCHITECTURAL_SOURCE+LIVE_RUNTIME_CANDIDATE (runtime جلوتر از main ⇒ DEPLOYED≠TRACKED)؛ packs/lead+web/lead=LIVE (main+138)؛ revenue-بقیه=BRANCH/RUNTIME_ONLY؛ opslib+kernel=SAFETY_CONTROL (پوشش ناقص تا OD-4)؛ langar=TEST_ONLY+dormant؛ vbaa=PATCH_SUBSTRATE نه-adopted؛ Armin=RESEARCH_DOC_ONLY؛ ۱۲ CURRENT-TRUTH (۱ canonical + ۱ AUTO_SURFACE + ۱ UNKNOWN + ۹ pointer)؛ worktrees کلود=MIRROR_OR_EXPORT؛ 7,082 orphan=LEGACY_ORPHAN candidate.

## فاز سه — گراف
OCTOPUS-SYSTEM-GRAPH.json (نسخهٔ recovery): یال‌های جدید — diverges_from (runtime↔main)، reads (opslib→HALT-ALL)، calls (۳ مصرف‌کنندهٔ main)، unmerged_with_unique_content (۱۵۷ شاخه)، authorizes (CODEOWNERS)، naming_contradicts (workflows observation-* ↔ بازنشستگی R2-3)، branch/runtime_only (بدنهٔ revenue). سه نقشهٔ تخصصی: SAFETY-AND-RUNTIME-WIRING-MAP · BUSINESS-AND-REVENUE-PATH-MAP · COGNITIVE-SYSTEM-MAP.

## فاز چهار — حافظه/تکرار/supersession
OCTOPUS-FORGOTTEN-ITEMS.md (۱۵۷ شاخه unmerged؛ ۲۳۲ commit branch-only؛ runtime ahead؛ ۶ stale PR؛ ۷,۰۸۲ orphan؛ ۱,۰۵۲ broken-link baseline؛ ۷,۰۲۶ dup-group؛ ۱۲ CURRENT-TRUTH؛ AUTO1 باز؛ G22 unverified؛ fuse_hidden؛ observation-workflows؛ ۲ alert). SUPERSESSION-LEDGER + رأی 1B/2A/3B/4D ثبت شد.

## فاز پنج — test truth
ofn-node@main: 9664P/6F pre-existing(نام‌دار)/28S/8192sub · exit1 · 211s · کلون ایزوله — PASS با denominator.
langar: harness 13+22 سبز؛ pytest COLLECTION_FAILURE(SystemExit module-scope). vbaa: 23P+1xf+2xp. Armin: TESTS_ABSENT. هیچ dep نصب نشد؛ هیچ .env واقعی load نشد.

## فاز شش — خروجی‌ها
۲۱ فایل در این lane (۱۹ الزامی + ROOTS-INVENTORY + BRANCH-ANALYSIS). هیچ فایل موجودی تغییر نکرد؛ sidecar-قاعده رعایت شد؛ current-truth جدید ساخته نشد.

## فاز هفت — roadmap جراحی
۱۱ جراحی PROPOSED_ONLY (SURG-01..11) با کلاس/ریسک/blast-radius/precondition/rollback/validation — ترتیب: S1های صفرریسک → diff بدنه‌ها → OD-4 wiring پشت رأی → CRM → hygiene → cognition.

## فاز هشت — کارت‌های تصمیم
۱۰ کارت (DC-01..10؛ P0: PR71، OD-4-GO، هم‌ترازسازی بدنه‌ها، توکن‌ها؛ P1: CRM، 01-TRUTH، مرز repo↔vault، حفاظت شاخه؛ P2: langar، مهاجرت).

## blockers
همان ۱۰ کارت + گیت‌های بستهٔ G1..G7 + ممنوعیت‌های دائمی (بدون استثنا حتی با 1B..4D).

## next safe action
**کارت DC-02 (GO/NO-GO سیم‌کشی OD-4)** — چون PRE فریز است، doctor آماده است و تنها رأی مانده؛ هم‌زمان SURG-02 (sidecar مستند HALT) و فاز فقط‌خواندن SURG-03 بدون رأی قابل شروع‌اند (هر دو S1/فقط‌خواندن).

---
```text
MISSION=OCTOPUS-UNIFIED-RECOVERY-AND-SURGICAL-ROADMAP-20260917
START_UTC=2026-09-17T00:45:00Z
END_UTC=2026-09-17T01:37:57Z
MODE=READ_ONLY_RESEARCH_PLUS_ADDITIVE_REPORTING
REMOTE_MUTATIONS=0
EXISTING_FILE_MUTATIONS=0
NEW_ARTIFACTS_CREATED=20_files_in_this_lane
DELETED_ARTIFACTS=0
OVERWRITTEN_ARTIFACTS=0
RENAMED_OR_MOVED_ARTIFACTS=0
REPOS_SCANNED=4
RUNTIME_NODES_READ_ONLY_SCANNED=1(board138)
VAULT_ROOTS_SCANNED=90_recorded(ROOTS-INVENTORY.csv)+7_nested+174_obsidian_dirs
VAULT_RAW_COUNT=315445
VAULT_DEDUPED_COUNT=71235
EXACT_DUPLICATE_GROUPS=7026
DIVERGENT_COPY_GROUPS=7(repo↔vault same-path)+3(source bodies)
BROKEN_LINKS_BASELINE=1052
NEW_BROKEN_LINKS=0
ORPHANS=7082
CURRENT_TRUTH_COPIES=12
CANONICAL_BODY_CONFLICTS=3(runtime-vs-main; CURRENT-TRUTH-role; repo-vault-7files)
BRANCH_ONLY_COMMITS=232(window)/157-unmerged-branches
STALE_PRS=6
OPEN_OWNER_DECISIONS=10
SAFETY_FINDINGS=5(oracle-file-divergence;3-consumers-DOC_ONLY;3-divergent-bodies;HALT-absent-not-thrown;unprotected-157)
REVENUE_FINDINGS=5(table-without-writer;counters-mixed-units-history;PAINT-L5-real-authorized-historical-wal0B;VERIFIED_CASH=0;stale-funnel-6)
COGNITIVE_FINDINGS=4(97/100-invalid;observatory-workflows-vs-retirement;wild-arena-no-canary;multi-provider-live)
TEST_VERDICTS=PARTIAL_PASS/PARTIAL/TOTAL_PASS/TESTS_ABSENT
RUNTIME_CLAIMS_VERIFIED=8
RUNTIME_CLAIMS_UNVERIFIED=3(180;182;witness-182-today)
G0_INVENTORY_COMPLETE=true
G1_SNAPSHOT_VERIFIED=pending
G2_HASH_MANIFEST_VERIFIED=manifest-produced;verify-drill-pending
G3_OWNER_REVIEWED=pending
G4..G7=pending
NEXT_SINGLE_SAFE_ACTION=DC-02(OD-4 wiring GO/NO-GO)
```
