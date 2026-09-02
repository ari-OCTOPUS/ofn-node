# 07-INCIDENTS — گزارش‌دهی دوره‌ای (حالت مالک-غایب)

purpose: هر session/شب یک خلاصه: چه merge شد، چه مسدود ماند و چرا، چه رسیدی گرفته شد. مالک این را وقتی برمی‌گردد می‌خواند.
house rules: هر عدد با روش + بدنه (برنچ/SHA) · UNKNOWN نه FALSE · append-only.

---

## 2026-09-02 (session: ari322 local agent, F:\ scope)

**Merged: هیچ.** دلیل: گیت main قفل است (۴ چک الزامی شامل `require-independent-approval` + یک تأیید بازبین غیرنویسنده). حساب نویسندهٔ همهٔ PRها همان حساب پروکسی ari322 است — طبق درس #۵1 و متن CODEOWNERS، نویسنده تنها بازبین خودش نمی‌شود. عبور با پرچم admin = شل‌کردن policy = ممنون قانون آهنین.

**Opened (۴):**
- #70 `docs(agents): DEAD SOURCE labels` ×۴ هاروستر — D-31 گام ۱؛ 47pass/1skip محلی
- #71 (پیش‌نویس) `landing: release/p0 → main rebased` — تعارض CODEOWNERS با حکم ۷مسیره حل شد + SENSITIVE ورک‌فلو؛ منتظر بازبینی مستقل
- #72 `test(waiver): no external send while waiver active` — ۴ تست؛ گارد میزبان روی میزبانِ مسلح عمداً قرمز
- #73 همین سند

**رخداد ۶ ارسال — RESOLVED-AUTHORIZED:** مالک تصریح کرد مجوز ۲۰۲۶-۰۸-۳۱ واقعی بوده («بله اجازه دادم»). شش ایمیل واقعی به آژانس‌های NSW (TfNSW×2، HealthShare، E&H، DoE×2) زیر PAINT-L5-001 ثبت‌شده در `outbound-effects.sqlite3` روی board138. اولین ارسال سیزن = ۲۰۲۶-۰۹-۰۱T13:16:59Z. باقی‌مانده: تناقض متنی وایور فعال (external messaging not_authorized) با واقعیت مجاز — نیاز به re-scope یا چرخش راز (Q-08).

**Containment:** `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL` روی board138 با دست مالک clean-طرف `"0"` شد (بک‌آپ: `managed_flags.json.bak-20260902`).

**حالت مالک-غایب فعال شد** (دستور اجرایی مالک): پیش‌فرض GO برای کار برگشت‌پذیر. دو حکم تفسیری ایجنت — هر دو به نفع قفلی که مالک همان روز گذاشت:
1. merge فقط با `mergeable_state=clean` (یعنی چک‌ها + تأیید مستقلِ واقعی)؛ هرگز bypass اداری.
2. پرچم ارسال دوباره مسلح نمی‌شود — disarm امشبِ مالک + وایور فعال، بر دستور عمومی مقدم‌اند. مسیر درآمد تا `quote_drafted` پیش می‌رود؛ `quote_sent` منتظر GO/چرخش راز.

**پاکسازی والت:** ۱۰ آینهٔ CURRENT-TRUTH → pointer؛ 01-TRUTH → redirect؛ آرشیو هش‌پیچ در `99-ARCHIVE/mirror-cleanup-20260902/` (رسید در والتِ مالک). یافتهٔ تازه: `.claude/worktrees/` داخل والت ۷+ کپی کامل والت (worktree های ۳۰ اوت) نگه می‌دارد — ریشهٔ تکثیر آینه‌ها؛ دست‌نخورده، تصمیم حذف با مالک.

**مسدودها و دلیل:** #70/#71/#73 → منتظر بازبینی مستقل (Elahe-z). #72 → عمداً پشت #71 صف شده (base=release/p0؛ merge قبل از فرود باعث واگرایی دوباره می‌شود).

---

## ضمیمهٔ شواهد تاریخی — NBB-CP (۲۰۲۶-۰۸-۱۵)

> این الگوها قبلاً در پروژهٔ خواهر (NBB-CP) دیده شده و تکرار شده‌اند. هیچ‌کدام حذف نشد، فقط شناسهٔ درست گرفت.

دو سند زیر عیناً از آرشیو مالک (Downloads) افزوده شده‌اند؛ اسکن الگوی راز انجام شد (تمیز). درس‌های تعمیم‌یافتهٔ امروز:

1. **شمارندهٔ شناسهٔ واحد** — برخورد دو `C-008` مختلف در NBB-CP؛ واکسین امروز: `run_id` فقط در مرز قابل‌اعتماد ساخته می‌شود (TaskEnvelope)، و پیش از تخصیص هر شناسه، grep روی همهٔ بدنه‌ها.
2. **عدد زنده timestamp می‌خواهد** — coherence که در یک روز ۴ بار عوض شد ≫ درصد آمادگی بازوها؛ هر عدد با commit hash + ساعت اجرا قفل شود.
3. **تفکیک سه‌گانهٔ قفل‌ها** (به‌طراحی / فقط دست مالک / هرگز) ≫ همان قانون طلایی/آهنین دستور مالک-غایب.
4. **کارِ باز ≠ تناقض** — دو گزارش مستقل با علت مشترک، یک آیتم Truth Registry، نه دو.

نقشهٔ کامل نگاشت قواعد ۱۵-اوت به مؤلفه‌های ofn-node: سری D-31..D-34 (Downloads مالک).

### شواهد تاریخی — pointer، نه mirror (اصلاح ۲۰۲۶-۰۹-۰۲: دستور ادامهٔ مالک)

این فایل log عملیاتی append-only است؛ سند کامل اینجا mirror نمی‌شود (درس آینه‌های والت، همان روز).

| سند | محل اصلی (آرشیو immutable، فقط‌خواندنی) | SHA-256 | سطح شاهد |
|---|---|---|---|
| همسان‌سازی وضعیت شبانه + برخورد شناسهٔ C-008 | `F:/backup/99-ARCHIVE/nbb-cp-evidence-20260815/NIGHT-SYNC-C008-COLLISION.md` (9,775 bytes) | `ee0e8004c8a68af5fd8d5b550027d5298d68f870e45987b90d5fdf7a04fe195d` | B (گزارش ایجنت؛ در ۱۵ اوت بازآزمایی نشد) |
| گزارش نهایی همسان‌سازی — ۱۵ اوت ۲۰۲۶ | `F:/backup/99-ARCHIVE/nbb-cp-evidence-20260815/FINAL-SYNC-REPORT.md` (7,880 bytes) | `03290c8e2b07cbbdbb9a694979953394b99e6a49e6eff9e33a1dc8fa69e8e1ad` | A (اعداد از اجرای واقعی روی ماشین مالک) |

درس ← کنترل امروزی (هر درس، الان کد/قاعده کجاست):

1. شمارندهٔ شناسهٔ واحد (برخورد C-008) ← `ofn/kernel/envelope.py`: run_id فقط در `create_envelope()` ضرب می‌شود؛ رجکس سخت در `__post_init__` (PR #74).
2. عدد زنده timestamp می‌خواهد ← قانون سرصفحهٔ scope + «روش با عدد» در رسیدهای PR #70..#74.
3. تفکیک سه‌گانهٔ قفل‌ها ← قانون طلایی/آهنین دستور مالک-غایب + CODEOWNERS هفت‌مسیره (PR #71).
4. کارِ باز ≠ تناقض ← همین log: هر بلاکر یک بار با یک دلیل ثبت می‌شود، نه دو.

اصل‌ها در Downloads مالک نیز دست‌نخورده باقی‌اند؛ آرشیو بالا کپی فقط‌خواندنی با هش پین‌شده است.

## 2026-09-02 (session ii — continuation directive: no-idle)
- **commits/PRs:** #73 fixed in place (appendices → pointer+hash, same PR); #74 +commit (duplicate-event rejection, rollback_ref); #75 NEW (HALT RunGate + source_health + 7 chaos scenarios, stacked on #74); #76 NEW (campaign_envelope on release/p0, draft-only).
- **tests:** `pytest tests/test_envelope.py tests/test_run_store.py` = 50 passed @0b3bffd ~06:20Z; `pytest tests/test_run_gate.py tests/test_chaos_owner_absent.py` = 19 passed @0b3bffd ~06:40Z; `pytest tests/test_campaign_envelope.py` = 10 passed @110f6c0-base ~07:10Z. Full CI judged on the PRs.
- **merged:** NONE — all review-blocked (by design; reviewer = @Elahe-z).
- **review-blocked:** #70 #71(draft) #73 #74 #75 · #72 sequenced behind #71 (base rp0).
- **owner-blocked:** quote_sent chain (Q-05/rotation), waiver re-scope (Q-08), .claude/worktrees cleanup decision.
- **external effects:** ZERO (revenue lane stopped at campaign_envelope_ready with structural no-send pin).
- **receipts:** DEAD-SOURCE-LABELS / WAIVER-SEND-GATE-TEST (branch chore+waiver); P1-ENVELOPE-RUNSTORE (#74); HALT-CHAOS (#75); CAMPAIGN-ENVELOPE (#76); vault: MIRROR-CLEANUP + WORKTREES-INVENTORY (06-EVIDENCE/OCTOPUS-VAULT-MAINT-2026-09-02/).
- **worktree inventory (definitive count):** 22 registered worktrees of the vault repo (16 under .claude/worktrees + 6 on C: + main). 3 VERIFIED / 18 SUSPECTED / 1 UNKNOWN (w1-spine — active parallel session, status timed out). Four worktrees born TODAY (w1-free/money/scale/spine) → a parallel session is live on the vault repo; re-read their state before any vault write. Read-only; nothing pruned.
- **next executable action:** independent review of #70 → #74 → #75 (then #71 un-draft after CI) — reviewer's, not mine.

### POLICY — حاکمیت این log (2026-09-02، دستور evidence-hardening)

1. **Append-only**: ورودی‌های جدید فقط انتهای فایل، با تاریخ صعودی. تست `tests/test_incidents_log_policy.py` این را مکانیکاً چک می‌کند.
2. **بدون mirror متنی**: هیچ سند بیرونی verbatim اینجا کپی نمی‌شود؛ فقط pointer + full SHA-256 + byte size + سطح شاهد.
3. **«immutable» ادعا نمی‌شود**: آرشیو فقط read-only bit دارد (نوشتن رد شد — آزمون 2026-09-02، هش پس از تلاشِ نوشتن تغییر نکرد). در برابر نوشتهٔ دست‌privilege، کنترلِ مقید **هش** است نه attribute.

### راستی‌آزمایی مستقل pointerها (2026-09-02T05:05Z)

- `sha256sum` دوباره روی هر دو فایل آرشیو: هر دو هش با جدول بالا برابر — MATCH.
- آزمون نوشتن: `echo x >> NIGHT-SYNC-C008-COLLISION.md` → `Permission denied`؛ هش پس از تلاش تغییری نکرد.
- فرمان + خروجی در رسید session iii ثبت شد.

## 2026-09-02 (session iii — hourly operator 05:18Z, owner-absent)

- **branch / HEAD:** `feat/p1-envelope-runstore-20260902` `e41cc26da5e1f1f96fc99556d095635b9b0d2d44` (updates #74); `feat/arch-otel-token-inventory-20260902` `1dbfdbdde22efcfe62bf00258467d3e7a124dddc` (new PR).
- **files (P1 / #74):** `ofn/adapters/run_store.py`, `ofn/adapters/halt_flag.py`, `ofn/kernel/envelope.py`, `tests/test_run_store.py`, `tests/test_envelope.py`, P1 receipt JSON.
- **files (arch lane):** `ofn/kernel/otel_map.py`, `ofn/kernel/revenue_states.py`, `tools/worktree_inventory.py`, three tests, three contract docs, P5 receipt JSON.
- **tests P1:** `python3 -m pytest tests/test_envelope.py tests/test_run_store.py tests/test_kernel_purity.py -q` · `2026-09-02T05:25:11Z` · HEAD `e41cc26da5e1f1f96fc99556d095635b9b0d2d44` · exit 0 · **59 passed / 897 subtests / 0 fail / 0 skip**. Receipt: `docs/octopus-surgery/architecture/2026-09-02/receipts/P1-ENVELOPE-RUNSTORE-20260902.json`.
- **tests arch:** `python3 -m pytest tests/test_otel_map.py tests/test_revenue_states.py tests/test_worktree_inventory.py tests/test_kernel_purity.py -q` · `2026-09-02T05:25:11Z` · HEAD `1dbfdbdde22efcfe62bf00258467d3e7a124dddc` · exit 0 · **30 passed / 879 subtests / 0 fail / 0 skip**. Receipt: `docs/octopus-surgery/architecture/2026-09-02/receipts/P5-OTEL-TOKEN-INVENTORY-20260902.json`.
- **merged:** NONE — review-blocked by design (`require-independent-approval` + CODEOWNERS).
- **review-blocked:** #70 #71(draft) #73 #74 #75 #76 · #72 sequenced behind #71 (base `release/p0`).
- **owner-blocked:** `quote_sent` / `send_authorized` (no newer scoped authorization); secret rotation; partner voices; vault `.claude/worktrees` prune decision.
- **external effects:** ZERO. `campaign_envelope_ready` remains structurally ≠ `send_authorized` (`ofn/kernel/revenue_states.py`).
- **this-host worktree census:** `python3 tools/worktree_inventory.py --json` · `2026-09-02T05:24:48Z` · exit 0 · VERIFIED 1 / SUSPECTED 2 / UNKNOWN 0. SUSPECTED = this session's dirty lock-zone trees before commit. Nothing pruned. Vault census from session ii is a different body (`body_not_on_this_host`).
- **docs first-read:** `docs/octopus-os/MASTER-BLUEPRINT.md` and `CONTRIBUTING.md` **absent on main @67359a6** (UNKNOWN on this body, not FALSE). D-27 source pointer SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes, PR #66 blob). D-28 source pointer SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes, PR #67 blob). Evidence level B (git blob, not a second disk hash).
- **#76 CI:** full-suite red on `release/p0` base (`EffectorGate` token in `consent_store.py` docstring; `capability_token` `no-token-secret` on CI hosts). Not introduced by `campaign_envelope`. Left on that PR; no duplicate opened.
- **next executable action:** independent review of #74 (now includes close-with-ref + non-UTF-8 halt) then #75; land the new arch PR behind the same gate. Do not re-arm send.

## 2026-09-02 (session iv — CI trigger require-independent-approval on #74, 05:24Z)

Trigger: check-suite failure `require-independent-approval` ×2 on `feat/p1-envelope-runstore-20260902` @`92f5267913b6ec794e76537888b3d36eaa556176`. Author ari322 cannot approve their own change on a CODEOWNERS path. Gate working as designed (issue #51). Not a test failure — full-suite ubuntu was green.

- **blocker (exact):** REVIEW_REQUIRED / no independent approval. Merge blocked. Engineering continued on the same PR.
- **branch / HEAD:** `feat/p1-envelope-runstore-20260902` `3d52d7d1aabc35a20f97ff23d9f6cabbc2ff8a8a` (updates #74). File-lock zone: `/tmp/ofn-p1-harden` — `ofn/adapters/run_store.py`, `ofn/kernel/token_ceiling.py`, `tests/test_run_store.py`, `tests/test_token_ceiling.py`, P1 receipt JSON.
- **what landed on #74:** persist `budget_tokens` on `RUN_CREATED`; `BUDGET_DEBIT.payload.tokens` checked against per-run ceiling before write (0 budget authorizes no spend); `replay()` fail-closed on corrupt JSON (same as `_load`); store root `0700` (POSIX); new `ofn/kernel/token_ceiling.py` — both ceilings (per-run + `NodeQuota`); `grants_send` always False.
- **tests P1:** `python3 -m pytest tests/test_envelope.py tests/test_run_store.py tests/test_token_ceiling.py tests/test_kernel_purity.py tests/test_quota.py -q --tb=no` · `2026-09-02T05:33:09Z` · parent HEAD `e41cc26da5e1f1f96fc99556d095635b9b0d2d44` · exit 0 · **103 passed / 930 subtests / 0 fail / 0 skip**. Receipt: `docs/octopus-surgery/architecture/2026-09-02/receipts/P1-ENVELOPE-RUNSTORE-20260902.json` (block `store_token_ceiling_and_replay_20260902`).
- **not duplicated:** #75 HALT/chaos, #76 campaign_envelope, #77 OTel/revenue-states/inventory (DRAFT), #73 this log.
- **merged:** NONE — review-blocked by design.
- **review-blocked:** #70 #71(draft) #73 #74 #75 #76 #77(draft) · #72 sequenced behind #71.
- **owner-blocked:** `quote_sent` / `send_authorized` (no newer scoped authorization); secret rotation; partner voices; vault `.claude/worktrees` prune.
- **external effects:** ZERO.
- **this-host worktree census:** `git worktree list` · `2026-09-02T05:34:01Z` · exit 0 · 3 registered (`/workspace` this session @92f5267; `/tmp/ofn-p1-harden` VERIFIED clean after commit; `/tmp/ofn-incidents-iv` this lock-zone). Nothing pruned. Vault census remains `body_not_on_this_host`.
- **docs first-read:** `docs/octopus-os/MASTER-BLUEPRINT.md` and `CONTRIBUTING.md` still **absent on main @67359a6** (UNKNOWN, not FALSE). D-27 SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes) MATCH vs session iii. D-28 SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes) MATCH. Evidence level B (git blob).
- **next executable action:** independent review of #74 (now includes token ceiling + replay fail-closed) then #75; do not re-arm send.
