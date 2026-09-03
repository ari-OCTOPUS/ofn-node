# OWNER PACK v4 — پیش‌نویس‌های آماده (۳ سپتامبر ۲۰۲۶، ~۰۰:۳۰ AEST)

**پایهٔ شواهد:** خواندن مستقیم GitHub (`ari-OCTOPUS/ofn-node`) در ~۱۴:۲۵Z توسط اورکستراتور.
**هیچ‌کدام از این متن‌ها ارسال نشده است.** ارسال فقط با دست مالک (حکم کانونیکال R3).

---

## حقیقت راستی‌آزمایی‌شده (سطح: GitHub مستقل)

```
MAIN_HEAD_SHA            = e68aedeb6d91669c8da660f5f423791b916a6a38  (مرج #66، 2026-09-02T14:10:18Z)
CODEOWNERS_ON_MAIN       = "* @Elahe-z"  (زنده از 14:02:19Z، کامیت 61b139fb)
CANARY_RESULT            = FAILED — #66 با base=61b139fb (قفل فعال) بدون رأی Elahe-z مرج شد
PR66_APPROVALS           = aram-ui ×3 ("app" 13:57:43 · "n" 14:02:51 · "nj" 14:06:50)
PR66_ELAHE_REVIEWS       = 0
PR66_MERGED_BY           = aram-ui @ 14:10:18Z
PR66_UNRESOLVED_BUGBOT   = 3 یافته روی octopus_survival/economy.py (حل‌نشده مرج شد)
PR106_STATE              = OPEN · BLOCKED · 0 review · requested_reviewers = (خالی)
PR106_IS_VALID_CANARY    = NO — الهه دعوت نشده؛ BLOCKED فقط یعنی «بدون رأی»
PR67_STATE               = OPEN · base=e68aedeb · Elahe-z دعوت شده · آخرین آپدیت 14:17:35Z
PR65_STATE               = OPEN (باید بررسی شود دیفش پس از مرج #66 خالی است یا نه)
DRAFT_PR_BACKLOG         = #82 #83 #87 #88 #93 #94 #95 #96 #97 #98 #99 #100 #104 #105 #77 (همه DRAFT، base کهنه)
MERGES_VERIFIED_DIRECTLY = #101 #84 #103 #102 #66  (۵ از ۸ ادعاشده)
MERGES_NOT_RE_VERIFIED   = #92 #70  (#85 در تاریخ main دیده شد)
```

### آنچه #66 روی main نشاند (بدون رأی انسانی)

`implementation` · `merge` · `deploy` · `wire` · `external_effect` · `board_access` · **`money`** = `true`
`propose_only_mode` = `false` · `auto_advance_waves` = `true` · `parallel_execution` = `true`

سقف‌های باقی‌مانده در کد: ۲۵ ارسال/روز · ۵۰ AUD/روز · بودجهٔ per-board صفر · کلید کشتار `OFN_EXTRA_CLOSED_GATES` · پنجرهٔ rollback ۲۴ ساعت.
خودِ PR تصریح می‌کند `OFN_WIRE_OUTBOUND=1` و `OFN_KEEP_GATES_OPEN=1` را پیش‌فرض نکرده است.

---

## ۱) پیام به Elahe-z (انگلیسی — برای GitHub یا تلگرام)

> Subject: Urgent governance ask — PR #106 review + retrospective on 8 merges (2026-09-02)
>
> Hi Elahe,
>
> Two asks, one urgent.
>
> **1. Please review PR #106** (`fix/r0-heartbeat-dep-20260903`). It restores one missing module
> (`outbound_worker.py`) so the board's heartbeat unit stops crashing. Small and low-risk.
>
> But #106 matters for a second reason: it is the test of the review gate itself.
> As of 14:02Z on 2 Sep, `.github/CODEOWNERS` is a single line — `* @Elahe-z` — which is
> supposed to make your approval mandatory on every path. We need to know whether that is
> actually enforced. So please do **not** approve it immediately. First tell me if you can see
> it, then approve when you are ready. If anyone else's approval makes it mergeable before
> yours, branch protection is broken and we need to fix the repo settings, not the file.
>
> **2. Retrospective, no action needed from you tonight.**
> Eight PRs were merged on 2 Sep by the `aram-ui` account, each self-approved, with zero
> reviews from you: #92, #70, #85, #101, #84, #103, #102 and #66. Most were owner-ordered
> content, so the concern is process, not intent — except one:
>
> **#66 ("D-27 unlock")** merged at 14:10Z, eight minutes *after* the `* @Elahe-z` lock went
> live and on a base that already contained it. It sets `money`, `wire`, `external_effect`,
> `deploy` and `merge` authorization to `true` and turns `propose_only_mode` off — 4,975 added
> lines across 32 files — and it carried three unresolved Cursor Bugbot findings on
> `octopus_survival/economy.py`. Hard caps (25 sends/day, AUD 50/day, per-board budget 0,
> kill-switch) are still in code, and outbound wiring is not defaulted on.
>
> If you have an opinion on whether #66 should stand or be reverted, I would like to hear it
> before we act. Nothing outbound has been sent, and no live process was restarted.
>
> Thanks,
> Ari

---

## ۲) رأی post-facto — متن ثبت در DECISIONS-LOG (تفکیک‌شده)

> ### V6 — رأی post-facto مالک دربارهٔ مرج‌های ۲ سپتامبر ۲۰۲۶
> **تاریخ رأی:** 2026-09-03 · **مبنا:** خواندن مستقیم GitHub در ~۱۴:۲۵Z
>
> **V6-a — هفت مرج فرآیندی:** #92 · #70 · #85 · #101 · #84 · #103 · #102
> حکم: **می‌پذیرم (accept, process-violation recorded).**
> دلیل: محتوای هر هفت مورد از پیش دستور مالک بود (R0-CLOSE lanes C/D، sanitize، waiver
> addendum). نقض، فرآیندی است نه محتوایی. حادثه در `docs/octopus-os/07-INCIDENTS.md`
> ثبت و بسته می‌شود. rollback درخواست نمی‌شود.
>
> **V6-b — مرج #66 (D-27 unlock):** حکم: ____________ (پر شود: «ابقا با شرط» یا «برگردان»)
> این مورد از V6-a جدا است چون فقط نقض فرآیندی نیست: مجوزهای `money` / `wire` /
> `external_effect` را روی main به `true` برد و `propose_only_mode` را خاموش کرد — در حالی
> که احکام کانونیکال R1 و R2 هنوز برقرارند.
> شرط‌های ابقا (اگر «ابقا» انتخاب شود):
> 1. `OFN_WIRE_OUTBOUND` و `OFN_KEEP_GATES_OPEN` خاموش بمانند تا رأی جداگانهٔ مالک.
> 2. سه یافتهٔ حل‌نشدهٔ Bugbot روی `octopus_survival/economy.py` در یک PR مستقل بسته شود.
> 3. سقف‌ها (۲۵ ارسال/روز، ۵۰ AUD/روز، per-board budget 0) با تست رگرسیون قفل شوند.
>
> **V6-c — کاناری:** نتیجهٔ آزمون قفل روی #66 = **رد**. ادعای «حفرهٔ V4 بسته شد» باطل و به
> `V4_HOLE_STATUS = OPEN (behaviourally unproven)` اصلاح می‌شود.
>
> **V6-d — مادهٔ ۱۰:** **باز نمی‌شود.** شرطِ «کاناری سبز» برآورده نشد. بازبینی پس از اینکه یک
> PR واقعی، رأی غیر-الهه‌ای بگیرد و همچنان BLOCKED بماند.
>
> **V6-e — دستور اصلاحی:** روی #106 فیلد `requested_reviewers` به Elahe-z ست شود تا کاناری
> معتبر شود. هیچ ری‌استارت یونیتی مجاز نیست. `FILES_I_MERGED=none`.

---

## ۳) ایمیل به MP Construct — سؤال ۳۰۶٫۹۰ دلار

> Subject: Invoice 002702 — $306.90 variance (Manly, Claim No 3)
>
> Hi [نام],
>
> Quick reconciliation question on the Manly job. Invoice **002702** was issued for
> **$16,500.00** (Claim No 3, 13 Aug 2026). The payment received in our account on
> **26 Aug 2026** was **$16,193.10** — a variance of **$306.90**.
>
> Could you confirm what the deduction relates to (retention, a back-charge, or a
> bank/processing fee)? I just want our records to match yours before we close the claim
> schedule.
>
> Also, for completeness: our books show three payments against the Manly contract —
> $18,414.00 (10 Jul), $24,858.90 (7 Aug) and $16,193.10 (26 Aug), totalling **$59,466.00**.
> If your ledger differs on any of these, let me know.
>
> Thanks,
> Ari
> [نام شرکت] · ABN [___]

---

## ۴) خط سابقهٔ درآمد برای متن DET (اصلاح‌شده)

**استفاده کن:**

> Over the current contract period we have invoiced and been paid **AUD 59,466.00** on a
> single commercial painting contract in Manly (Sydney), received in three progress payments
> between **10 July and 26 August 2026**, verified against our ANZ business account statement.
> Public liability insurance: **AUD 20M (Allianz)**.

**استفاده نکن:**
- ❌ «$۶۰k+ در ۹۰ روز گذشته» — پنجرهٔ ۹۰ روزه از ~۴ ژوئن شروع می‌شود و دو واریزی مه
  ($۶۳۷٫۳۷ و $۳۱۵٫۰۰) بیرونش می‌افتد؛ صورت‌حساب ANZ هم از ۵ مه شروع می‌شود.
- ❌ هر رقمی از Manly تا وقتی پاسخ سؤال $۳۰۶٫۹۰ نرسیده — DET ممکن است cross-check کند.
- ⛔ هیچ سند مالی (صورت‌حساب ANZ، شمارهٔ حساب) به مخزن عمومی نمی‌رود.

---

## ۵) پنج قدم فقط-از-دست-مالک (نسخهٔ ۴)

1. پیام Elahe-z (§۱) — از حساب خودت.
2. رأی V6-b دربارهٔ #66: «ابقا با شرط» یا «برگردان» (§۲).
3. ارسال DET با خط §۴ — از mailbox خودت (R3).
4. ایمیل MP Construct (§۳).
5. مادهٔ ۱۰: باز نکن تا کاناری معتبر سبز شود.
