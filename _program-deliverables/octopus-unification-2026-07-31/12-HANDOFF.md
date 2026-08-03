# 12 — HANDOFF · مأموریتِ یکپارچه‌سازی ۲۰۲۶-۰۷-۳۱

## وضعیت در یک نگاه

```text
Branch      claude/octopus-code-integration-175ecb   (9f14901 → ff ce35f61 → +6 کامیت)
Status      INTEGRATED_IN_SANDBOX + READY_FOR_OWNER_LIVE_GATE
Baseline    399 سوییت، 36 قرمز (29 CONFLICTED + 7 pre-existing)
Final       420 سوییت، 35 قرمز (1 فیکس، 0 قرمزِ نو، 21 ثبتِ نو همه سبز)
Mutation    19/19 قرمز، restore سبز
Live tree   از اول تا آخر دست‌نخورده (صفر restart/فلگ/send)
```

## کامیت‌ها (به ترتیب)

```text
2ac7e9b + f2fceee   نجاتِ ۶۳ فایلِ کدِ بی‌گیت (owner_console، epoch_guard، ۴۴ تست)
a9492c7             پذیرشِ v2: mission_contract + memory gate/store
0a303af             VQ-STATE-WRITE-001: LockedJson سخت شد + blocker ِ snapshot
830e38c             درزِ کارتِ mission + retrieval ِ حافظه (هر دو flag-off)
1247040             MANIFEST_INVALID visible + manifest ِ WD + ثبتِ ۲۱ سوییت
(+ کامیتِ اسناد/رجیستری بعد از این فایل)
```

## قدمِ بعدیِ نشستِ بعد (به ترتیبِ اولویت)

۱. کارت‌ها به مالک: **merge** · **VQ-MISSION-CARD-ARM-001** (دو mission ِ واقعی
   منتظرند) · **VQ-MEMORY-READ-ARM-001** · **VQ-LIVE-DIRTY-RECONCILE-001**.
۲. پس از reconcile ِ درختِ زنده: ۲۸ سوییتِ CONFLICTED را دوباره بدوان و
   `test_tg_callback_emitter_parity` را در run_all ثبت کن.
۳. A/B ِ §۱۰.۵ حافظه وقتی `action_memories_used` چند چرخه داده جمع کرد.
۴. VQ-MISSION-RECONCILE-001 (۶ vs ۱۲ وضعیت) — مهاجرتِ واقعی، جلسهٔ خودش.
۵. ۷ قرمزِ pre-existing ِ HEAD (فهرست در `01-BASELINE-TESTS.md`) — لِین‌هایشان.

## تله‌هایی که این نشست دید — تکرارشان نکن

۱. **قرمزِ ناشناخته روی شاخهٔ تمیز اول «جفتِ dirty» است، بعد باگ.** ۲۹/۳۶ قرمز
   این بودند. اول `git -C F:\backup status --short -- _ops/`.
۲. **PermissionError ِ پاکسازیِ tmp در ویندوز TypeError ِ واقعی را می‌پوشاند**
   (ccv2: search(tenant_id=…) روی store ِ v1 → WinError32 ِ گمراه‌کننده).
۳. **تستِ untracked را با جفتِ سوژه‌اش نجات بده** وگرنه قرمزِ دائمی می‌کاری.
۴. **run_all env ست نمی‌کند** — پینِ کامل (بلوکِ §۵ ِ 00-doc) وظیفهٔ شِل است؛
   `GENOME_DIR` جدا لازم است چون opslib:43 به `F:\backup` پین است.
۵. تست‌های non-harness روی ORG_ROOT=worktree چند فایلِ state ِ tracked ِ worktree
   را dirty می‌کنند (`governor-alerts.md`، `channel-status.json`،
   `school-awareness.json`) — نویزِ خودت را قبل از commit برگردان و `git add`
   همیشه مسیر-به-مسیر.
۶. **MANIFEST_ROOTS هم‌پوشان‌اند** — dedup ِ معتبرها با cid کافی نیست؛ نامعتبرها
   بدونِ dedup ِ مسیر دوبار شمرده می‌شوند (تستِ خودم گرفت).
۷. حلقهٔ `while read` ِ bash روی فایلِ لیستِ ویندوزی CR می‌گذارد → pathspec ِ
   `file.py?`؛ اول `tr -d '\r'`.

## فایل‌هایی که هرگز لمس نشدند (عمداً)

```text
organism.py · wiring.py · center.py · approval_channel.py · OCTOPUS-flags.cmd
PRE-0/** · heart/** · هر فایلِ dirty ِ درختِ زنده (فقط ۳ فایلِ v2 «کپی» شد)
```

## خروجی‌های این دایرکتوری

```text
00-REALITY-BASELINE.md        git inventory · تصحیحِ snapshot ِ مگاپرامپت · جدولِ اجزا
01-BASELINE-TESTS.md          ۳۹۹ سوییت + طبقه‌بندیِ ۳۶ قرمز (+ baseline-classification.json)
02-CONFLICT-MAP.md            درختِ زنده vs گیت + کارتِ reconcile
04-IMPLEMENTATION-LOG.md      کامیت‌به‌کامیت با شاهد
05-MUTATION-EVIDENCE.md       ۱۹ جهش + نگاشت به §۱۷.۲
08-MEMORY-INTEGRATION.md      واقعیتِ write-only → درزِ read + مرزِ A/B
11-ROLLBACK.md                برگشتِ دقیق per-commit
LIVE-GATE-CARD-MISSION-CARD.md  کارتِ arm (دو بندِ جدا)
FINAL-VERDICT.md              حکمِ صادق
baseline-run-all.log · final-run-all.log   لاگ‌های کامل
```

اسنادِ 03/06/07/09/10 ِ فهرستِ §۲۴ جدا ساخته نشدند — محتوایشان در همین
فایل‌هاست (00/02/04/05/08)؛ فایلِ خالی برای پرکردنِ فهرست = «گزارشِ صرف» ِ ممنوع.
E2E ِ تازه لازم نبود: `06-E2E-TRACE.json` ِ ۰۷-۳۰ سرِ جاست و زنجیره از آن زمان
فقط سخت‌تر شده (همان سوییت‌ها سبز)؛ تکرارِ مصنوعی‌اش شاهدِ تازه نمی‌ساخت.
