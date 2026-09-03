# GOV-V6 — قاعدهٔ دو-بازبینی (حکم مالک، ۳ سپتامبر ۲۰۲۶)

**حکم مالک (کلامی، همین نشست):** «الهه و aram تفاوتی ندارند، هر دو معتبرند — قوانین باید این باشد.»
**مبنای مجاز بودنِ تخفیف:** بدنهٔ PR #102 خودش نوشته بود «Relax/split scope only by an explicit
owner ruling after `verified_payment_count >= 1`». اکنون `verified_payment_count = 5`.
**پایهٔ شواهد فنی:** خواندن مستقیم GitHub در ~۱۴:۳۵Z · بدون هیچ نوشتن روی مخزن.

---

## ۰ — ابطال‌ها و اصلاح رکورد

| رکورد قبلی | وضعیت جدید |
|---|---|
| `V4_HOLE_STATUS = OPEN (behaviourally unproven)` | **`CLOSED_BY_OWNER_RULING`** |
| «۸ مرج بدون review معتبر» | **باطل** — رأی aram-ui رأی معتبر بازبین مجاز بود |
| GOVERNANCE-ANOMALY-WAVE3 / WAVE4-5 | عنوان اصلاح شود به `REVIEW-VALID / RULE-UNRECORDED`؛ فایل‌ها append-only بمانند، حذف نشوند |
| «تنها Elahe-z می‌تواند #102/#67/#106 را باز کند» | **باطل** |
| «مادهٔ ۱۰ تا سبزشدن کاناری باز نشود» | شرط بازتعریف شد — بند ۴ پایین |

خطای منشأ (ثبت صادقانه): اورکستراتور جملهٔ توضیحیِ داخل بدنهٔ PR #102 را به‌جای حکم مالک،
قاعدهٔ کانونیکال گرفت. درسِ روش: **ادعای متنِ یک PR ≠ حکم مالک.** قاعده فقط از
`ECONOMIC-LEARNING-RULINGS` / `DECISIONS-LOG` / کلام مالک می‌آید.

---

## ۱ — سطوح دسترسی واقعی (شاهد زنده)

```
ari322    = admin
aram-ui   = admin
Elahe-z   = write
```

هر سه مرجِ امروز از حساب admin انجام شد؛ هیچ bypass غیرمجازی رخ نداده است.

---

## ۲ — قاعدهٔ GOV-V6 (سه شرط، جایگزین V4/V5)

| # | شرط | چرا |
|---|---|---|
| R-V6-1 | تأییدکننده باید یکی از `Elahe-z` یا `aram-ui` باشد — **هر کدام تنها کافی است** | حکم مالک |
| R-V6-2 | **نویسنده ≠ تأییدکننده.** `ari322` نمی‌تواند PR خودش را approve کند | همین در ۱۴:۱۵ روی #67 درست عمل کرد |
| R-V6-3 | **رأی ربات رأی نیست.** `cursor[bot]` و هر app دیگر شرط را برآورده نمی‌کند | حفرهٔ واقعیِ باقی‌مانده — بند ۳ |

توصیهٔ چهارم (نه حکم): `Dismiss stale pull request approvals when new commits are pushed` = ON.

---

## ۳ — تنها حفرهٔ واقعیِ باقی‌مانده: رأی ربات

روی PR #102، حساب `cursor[bot]` در **۱۳:۵۹:۵۹Z** رأی `APPROVED` ثبت کرد با این متن:

> «Approved. All 17 CI checks on this head completed successfully, and no applicable
> approval policy requires human review. No reviewers assigned.»

و کد گیت فقط `login !== author` را می‌سنجد. پس یک رأی رباتی، **به‌تنهایی**، می‌تواند
`require-independent-approval` را سبز کند. این مستقل از بحث الهه/aram است و باید بسته شود.

---

## ۴ — CODEOWNERS اصلاح‌شده

فایل: `.github/CODEOWNERS`

```
# GOV-V6 — owner ruling 2026-09-03: Elahe-z and aram-ui are equally valid reviewers.
# Either one alone satisfies code-owner review. Author may never approve their own PR
# (enforced separately by .github/workflows/independent-review-gate.yml).
# Supersedes the V4 single-owner line, per the relaxation clause of PR #102
# ("relax only by owner ruling after verified_payment_count >= 1"); count is now 5.
* @Elahe-z @aram-ui
```

---

## ۵ — وصلهٔ ورک‌فلو اصلاح‌شده

فایل: `.github/workflows/independent-review-gate.yml`

کد فعلی روی main (`e68aedeb`) — عین متن:

```js
const approvers = [...latest.entries()]
  .filter(([login, state]) => state === 'APPROVED' && login !== author)
```

جایگزین GOV-V6:

```js
// GOV-V6 (owner ruling 2026-09-03): Elahe-z and aram-ui are equally valid human
// reviewers — either one alone is sufficient. Two things still do NOT count:
//   1. the author approving their own change  (ari322 on ari322's PR)
//   2. any bot / GitHub App approval — e.g. cursor[bot] APPROVED #102 at 13:59:59Z
//      with "no applicable approval policy requires human review"
const VALID_REVIEWERS = ['Elahe-z', 'aram-ui'];

const approvals = [...latest.entries()]
  .filter(([, state]) => state === 'APPROVED');

const approvers = approvals.filter(([login]) =>
  login !== author &&
  !login.endsWith('[bot]') &&
  VALID_REVIEWERS.includes(login)
);

if (approvers.length === 0) {
  const seen = approvals.map(([l]) => l).join(', ') || 'none';
  core.setFailed(
    `No valid independent approval on a sensitive path. Author: ${author}. ` +
    `Approvals seen: ${seen}. Required: one of ${VALID_REVIEWERS.join(' or ')}, ` +
    'and not the author. Bot/App approvals do not satisfy this check. ' +
    'This check is deliberately separate from the branch ruleset: lowering ' +
    'required-approvals does not satisfy it. See issue #51 and GOV-V6.');
}
```

**احتیاط پیاده‌سازی:** اگر `latest` فقط `state` را نگه می‌دارد، الگوی `login.endsWith('[bot]')`
کافی است و نیازی به `authorAssociation` نیست. اگر خواستی محکم‌تر باشد، هنگام ساختن `latest`
مقدار `review.user.type` را هم ذخیره کن و `type !== 'Bot'` را اضافه کن.

---

## ۶ — تست منفی اجباری (بدون این، وصله بی‌اعتبار است)

معیاری که نمی‌تواند رد شود، معیار نیست (درس ADR-041 از شکست معیار P3).

| سناریو | نتیجهٔ لازم |
|---|---|
| PR نویسندهٔ ari322، فقط رأی `ari322` | **FAIL** |
| PR نویسندهٔ ari322، فقط رأی `cursor[bot]` | **FAIL** |
| PR نویسندهٔ ari322، فقط رأی `aram-ui` | **PASS** |
| PR نویسندهٔ ari322، فقط رأی `Elahe-z` | **PASS** |
| PR نویسندهٔ aram-ui، فقط رأی `aram-ui` | **FAIL** |

---

## ۷ — صف: وضعیت جدید

| PR | وضعیت زیر GOV-V6 |
|---|---|
| #67 (D-28، مسیر حساس) | آزاد — با یک رأی از aram-ui یا Elahe-z قابل merge؛ رأی ۱۴:۱۶:۴۰ معتبر بود |
| #106 (heartbeat dep) | آزاد؛ کاناری بازتعریف شد به آزمون «رأی ربات/خودتأییدی باید FAIL شود» |
| #73 · #65 · #76 · #72 | آزاد، ولی base کهنه — قبل از merge sync شوند |
| ۱۵ PR درافت (#82…#105) | بدون تغییر، DRAFT |
| **#66 (D-27 unlock)** | **رأی محتوایی مالک لازم است — بند ۸** |

---

## ۸ — تنها رأی باقی‌ماندهٔ مالک: #66

این مورد ربطی به «کی review کرد» ندارد. مسئله دامنه است: #66 روی main این‌ها را `true` کرد —
`implementation` · `merge` · `deploy` · `wire` · `external_effect` · **`money`** · `board_access` —
و `propose_only_mode` را `false` کرد، در حالی که احکام کانونیکال R1 و R2 هنوز در
`OWNER-CANONICALIZATION-CLOSEOUT-ORDER-REV2` برقرارند.

وضعیت ایمنی فعلی: سقف‌ها در کد هستند (۲۵ ارسال/روز · ۵۰ AUD/روز · per-board budget 0 ·
کلید کشتار `OFN_EXTRA_CLOSED_GATES` · rollback ۲۴ ساعت) و `OFN_WIRE_OUTBOUND` /
`OFN_KEEP_GATES_OPEN` پیش‌فرض روشن **نیستند**. پس فوریت خطر وجود ندارد.

**رأی لازم:** «ابقا» یا «برگردان».
اگر «ابقا»: R1/R2 در سند کانونیکال با یک addendum به‌روز شوند تا سند و کد یک چیز بگویند،
و سه یافتهٔ حل‌نشدهٔ Bugbot روی `octopus_survival/economy.py` در یک PR جدا بسته شود.

---

## ۹ — دستور اجرا (برای ایجنتِ دارای دسترسی نوشتن)

```powershell
cd F:\ofn-node
git fetch origin
git checkout -b gov/v6-two-reviewer-rule-20260903 origin/main

# ۱) .github/CODEOWNERS  → بند ۴
# ۲) .github/workflows/independent-review-gate.yml → بند ۵
# ۳) tests: پنج سناریوی بند ۶ را به‌عنوان تست قفل اضافه کن

git add .github/CODEOWNERS .github/workflows/independent-review-gate.yml
git commit -m "gov(v6): Elahe-z and aram-ui are equally valid reviewers; author self-approval and bot approvals still refused

Owner ruling 2026-09-03. Supersedes the V4 single-owner CODEOWNERS line via the
relaxation clause of #102 (verified_payment_count is now 5).

Keeps two invariants: author != approver, and no bot/App approval counts
(cursor[bot] APPROVED #102 at 13:59:59Z with 'no applicable approval policy
requires human review').

FILES_I_MERGED=none"
git push -u origin gov/v6-two-reviewer-rule-20260903

gh pr create -R ari-OCTOPUS/ofn-node --base main `
  --title "gov(v6): two valid reviewers (Elahe-z | aram-ui); refuse self-approval and bot approvals" `
  --body "Owner ruling 2026-09-03. See GOV-V6. Negative tests included: author-only and bot-only approvals must FAIL."
```

سپس در `Settings → Branches → main`: گزینهٔ `Dismiss stale approvals on new commits` روشن، و
`require-independent-approval` به‌عنوان Required Status Check ثبت شود تا شکستنش واقعاً merge را
ببندد.

**ری‌استارت یونیت همچنان ممنوع (R4). `OFN_WIRE_OUTBOUND` خاموش تا رأی بند ۸.**
