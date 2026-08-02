---
type: megaprompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, deep-scan, blackbox, telegram, painter, project-f, repair-planning]
created: 2026-08-02
updated: 2026-08-02
---

# مگاپرامپت — دیپ‌اسکنِ کامل: Octopus / Telegram / Painter / OnlyFans

> مأموریت: **دیپ‌اسکن، کشفِ ناشناخته‌ها، نقشه‌برداریِ معماری، تشخیصِ سیم‌کشی‌های خراب،
> برنامه‌ریزیِ تعمیر، و طراحیِ تست.** نه patch کورکورانه، نه موفقیتِ جعلی، نه ارسالِ واقعی.
> order: scan → report → plan → patch proposal.

---

## نقش و هدف

ایجنتِ GLM برای «دیپ‌اسکن، کشفِ ناشناخته‌ها، نقشه‌برداریِ معماری، تشخیصِ سیم‌کشی‌های خراب،
برنامه‌ریزیِ تعمیر، و طراحیِ تست». هدف فوری تغییر نیست؛ فهمیدنِ سیستم، پیدا کردنِ
جعبه‌سیاه‌ها، مشخص‌کردنِ مسیرهای ناقص، استخراجِ contractها، و ارائهٔ یک برنامهٔ تعمیرِ
مرحله‌ای، قابلِ تست و امن.

دامنهٔ هدف: Telegram (فرمان/اعلان/callback/رأی/approval/UI) · Octopus اصلی
(brain/organism/router/orchestrator) · پاها (worker/module/adapter/capability) ·
پای نقاشی (lead/quote/first-reply) · OnlyFans/Project-F (studio/pf_os/content) ·
مسیرِ فرمان Telegram→Octopus · مسیرِ dispatch Octopus→پاها · مسیرِ برگشتِ جواب ·
مسیرِ برگشت به Telegram/dashboard · جعبه‌سیاه‌ها (معلوم/خراب/ناشناخته).

---

## اصول غیرقابلِ نقض

- هیچ موفقیتِ جعلی: اگر API نیست → `MISSING_API`؛ اگر contract معلوم نیست → `MISSING_CONTRACT`؛
  workflow انسانی → APIِ ماشینی فرض نشود؛ نیمه‌کاره → `PARTIAL`؛ معلوم‌نیست → `UNKNOWN`؛
  خراب → `BROKEN` با evidence.
- بدونِ evidence هیچ مسیری `working` اعلام نشود.
- بدونِ اجازه هیچ پیام/SEND/PUBLISH/DELETE/PAY واقعی. هیچ secret/token/chat_id/PII در خروجی.
- patch مخرب/حذف فایل/پاکسازی ledger/migration خطرناک ممنوع.
- ترتیب: scan و report اول؛ بعد plan؛ بعد patch proposal.
- هر side-effect باید idempotency key داشته باشد؛ هر flow باید statusِ قابل‌مشاهده و
  حالت‌های `pending/running/blocked/failed/done` را پوشش دهد؛ هر خطا → status/reportِ قابلِفهم.
- اگر unsure → صریح بگو و مسیرِ کشف پیشنهاد بده.

---

## برداشتِ اولیه از معماری (اگر repo فرق داشت، با evidence بازسازی کن)

```txt
Telegram update/callback → bot handler → owner gate/allowlist
  → Octopus router/organism → command bus/dispatcher/capability-registry
  → target leg adapter → leg workflow → result/artifact/event/status
  → Octopus status aggregator → Telegram response/dashboard/log
```

---

## خروجی‌های موردِ انتظار

۱. واژه‌نامهٔ واقعی · ۲. نقشهٔ فایل/entrypoint · ۳. نقشهٔ runtime · ۴. نقشهٔ component ·
۵. فهرست جعبه‌سیاه · ۶. matrix قرارداد (input/output/error/status/idempotency) ·
۷. نقشهٔ Telegram ingress · ۸. commands · ۹. callbacks · ۱۰. approval flow ·
۱۱. Octopus routing · ۱۲. dispatch به پاها · ۱۳. برگشت جواب · ۱۴. وضعیتِ پای نقاشی ·
۱۵. وضعیتِ Project-F · ۱۶. state/queue/ledger/idempotency · ۱۷. security/privacy/secrets ·
۱۸. gapها · ۱۹. unknownها · ۲۰. برنامهٔ تعمیر · ۲۱. تستِ عادی · ۲۲. mutation/edge ·
۲۳. recovery/restart · ۲۴. سوال‌های owner · ۲۵. verdict نهایی.

---

## چک‌لیستِ ۲۰۰تایی (هر مورد: `PASS`/`FAIL`/`UNKNOWN`/`PARTIAL`/`NOT_APPLICABLE`)

برای هر `FAIL`/`UNKNOWN`/`PARTIAL` حداقل یک repair suggestion.

### A. دامنه، واژه‌نامه، ابهام‌زدایی (001-010)
001 معنیِ «اختاپوس اصلی» از فایل/entrypoint/naming · 002 معنیِ «پا/leg» از کلاس/پوشه/registry ·
003 «پای نقاشی» = کدام فایل/module/function/state · 004 «OnlyFans/Project-F» = کدام پوشه/workflow/runtime ·
005 نقشِ Telegram (command/notification/callback/vote/approval/miniapp) · 006 «سیم‌کشی» = import/registry/router/flag/callback/queue/bus ·
007 «جواب برگرداندن» = sync/event/message/poll/dashboard · 008 `UNCLEAR_TERM` · 009 `OWNER_DECISION_REQUIRED` ·
010 هیچ فرضِ معماری بدون evidence.

### B. موجودی repo، runtime، entrypoint (011-020)
011 تمام run-script/`.py`/`.js`/`.ts`/`.ps1`/`.bat`/`.sh` · 012 main loop/organism runner ·
013 capability/component registry یا plugin loader · 014 فایل‌های bot/command/callback/menu/notifier ·
015 فایل‌های painter/lead/quote/first-reply · 016 فایل‌های OnlyFans/Project-F/studio/pf_os ·
017 state/queue/ledger/jsonl/db/cache · 018 flagهای مرتبط · 019 تست‌های موجود ·
020 جداکردنِ active/archived/dead/skeleton/template/experimental.

### C. نقشهٔ Octopus اصلی (021-030)
021 main loop + heartbeat/beat/tick · 022 discoveryِ module/leg · 023 routing input→action ·
024 schemaهای command/event/proposal/task/result · 025 import مستقیم یا adapter/registry ·
026 halt/freeze/stop/emergency · 027 کجا statusِ کلی ساخته/aggregate می‌شود · 028 کجا خطا log/Telegram می‌رسد ·
029 failureِ یک leg = crash یا isolate · 030 اگر چند runtime، کدام canonical.

### D. جعبه‌سیاه و قرارداد (031-040)
031 ثبتِ همهٔ جعبه‌سیاه (name/path/role/owner/flag/status) · 032 input contract یا `MISSING_INPUT_CONTRACT` ·
033 output contract یا `MISSING_OUTPUT_CONTRACT` · 034 error contract یا `MISSING_ERROR_CONTRACT` ·
035 status/health function · 036 side effectها · 037 idempotency strategy · 038 تست → contract ·
039 جداسازیِ workflow انسانی از API واقعی · 040 `ok:true`+error / success بدون artifact = violation.

### E. Telegram ingress و احراز هویت (041-050)
041 webhook/polling/file-replay/mock · 042 entrypointِ message · 043 entrypointِ callback ·
044 allowlist/owner-chat-id (بدون چاپِ secret) · 045 commandهای مجاز · 046 commandهای خطرناک/مدیریتی ·
047 command ناشناخته = fail-closed؟ · 048 callback forged/replay/expired رد؟ · 049 actor → permission واقعی ·
050 خطا secret/PII echo نمی‌کند.

### F. Telegram routing، menu، callback (051-060)
051 `/start`/menu/dashboard · 052 commandهای painter/lead · 053 commandهای Project-F ·
054 callbackهای approve/reject/later/vote/notify · 055 callback بعد از restart resolve یا orphan ·
056 callback → action/proposal درست یا replay · 057 فقط routeهای مجاز به Octopus ·
058 trace_id/correlation_id · 059 double-tap = duplicate؟ · 060 خطای leg → پیامِ قابلِفهم.

### G. command bus از Octopus به پاها (061-070)
061 مسیرِ dispatch · 062 schema فرمان · 063 sync/async/queue/event · 064 انتخابِ target leg ·
065 leg ناشناخته = fail-closed یا crash · 066 بدون run_id/trace_id رد؟ · 067 side-effect بدون idempotency رد؟ ·
068 پشتیبانیِ partial/blocked/failed/done · 069 Telegram مستقیم leg را bypass نمی‌کند ·
070 اگر bus نیست، adapter/plan حداقلی.

### H. برگشت جواب از پاها به Octopus/Telegram (071-080)
071 leg: return/event/log/status-file · 072 Octopus کجا نتیجه را می‌خواند · 073 مستقیم به Telegram یا از approval/status ·
074 long-running = progress؟ · 075 timeout → blocked/failed · 076 پاسخِ duplicate = duplicate Telegram؟ ·
077 خروجیِ ناقص → success؟ · 078 artifact_id ثبت می‌شود (module/draft/reply/job) · 079 خطا → user-facing امن ·
080 اگر response path نیست، contract پیشنهادی.

### I. پای نقاشی / Painter / Lead (081-090)
081 inventory فایل‌ها · 082 مسیرِ intake · 083 مسیرِ quote/draft · 084 مسیرِ first reply ·
085 مسیرِ authorization/owner-approval/consent · 086 بدون consent/approval = outbound واقعی نه ·
087 synthetic/market-signal هرگز outbound · 088 quote: draft یا send · 089 first-reply: compose یا send ·
090 contract کامل (input/status/artifacts/errors).

### J. OnlyFans / Project-F / Studio (091-100)
091 inventory · 092 active/archived/skeleton/template · 093 مسیرِ Telegram ·
094 studio module build API واقعی یا workflow انسانی · 095 هیچ module_id/build_id جعلی ·
096 content workflow با privacy/consent/platform-rules · 097 token/credential echo نمی‌شود ·
098 automation بدون approval publish/send نمی‌کند · 099 اگر partially-known، unknown-map + adapter ·
100 contract کامل (commands/status/artifacts/errors).

### K. state، queue، ledger، idempotency (101-110)
101 فهرستِ state files · 102 queue/pending/retry · 103 ledger/receipt/history ·
104 idempotency key کجا تولید/ذخیره · 105 تکراریِ هم‌payload = NOOP/replay · 106 تکراریِ متفاوت‌payload = conflict ·
107 ledger write atomic · 108 retry بعدِ timeout = duplicate؟ · 109 pending بعدِ restart resume یا orphan ·
110 conventionِ idempotency key برای هر side-effect.

### L. permission، owner gate، halt، safety (111-120)
111 مسیرهای owner-approval · 112 action خطرناک = owner-gated · 113 halt/STOP/FREEZE قبلِ action ·
114 owner-spoof رد · 115 غیرمالک = read/status محدود · 116 پولی/خارجی/publish/delete جداگانه gate ·
117 approval → actionِ exact bind · 118 approval قدیمی روی payload نو replay نشود · 119 permission نامعلوم = deny ·
120 مسیرهای bypass احتمالیِ Telegram→leg مستقیم.

### M. error، retry، recovery (121-130)
121 خطای network/Telegram/external از contract-error جدا · 122 timeout policy · 123 retry policy ·
124 retry با backoff و سقف · 125 error در log دفن نمی‌شود · 126 partial failure قابل نمایش ·
127 recovery از state واقعی · 128 corrupted state fail-soft یا crash · 129 dead-letter/equivalent ·
130 next_action برای هر خطا.

### N. observability، status، event، dashboard (131-140)
131 status functionها · 132 aggregate کجا · 133 event spine/canonical jsonl · 134 trace_id ·
135 correlation_id · 136 unknown → green نمی‌شود · 137 dashboard/Telegram از source واحد یا تفسیر جدا ·
138 scrub secret/PII · 139 eventهای start/done/failed/blocked · 140 اگر mapper نیست، pure mapper.

### O. schema، validation، adapter contract (141-150)
141 schema Telegram→Octopus · 142 schema Octopus→leg · 143 schema leg→Octopus · 144 schema status ·
145 schema error · 146 schema artifact (module/draft/reply/vote/message) · 147 adapterها normalize خام ·
148 `ok:true`+error رد · 149 success بدون artifact رد · 150 adapterِ fail-closed برای هر جعبه‌سیاه.

### P. security، privacy، compliance (151-160)
151 secret reference (بدون مقدار) · 152 echo در log/error/status/Telegram · 153 PII مشتری نشت ·
154 outbound فقط با consent+approval · 155 Project-F با ToS/privacy/age/content · 156 upload/download امن ·
157 path traversal · 158 callback data حاوی secret/PII · 159 admin owner-only · 160 severity + repair.

### Q. تستِ عادی (161-170)
161 command معتبر route · 162 نامعتبر fail-closed · 163 owner-approval actionِ درست · 164 callback جعلی رد ·
165 dispatch painter = معتبر یا blocked واقعی · 166 dispatch Project-F = معتبر یا blocked واقعی ·
167 leg ناشناخته = blocked نه crash · 168 response به Telegram/status · 169 restart+resume · 170 flag-off parity.

### R. mutation، edge case، red-team (171-180)
171 حذف run_id = blocked · 172 حذف trace_id = blocked · 173 `ok:true+error` رد · 174 success بدون artifact رد ·
175 duplicate callback = duplicate نه · 176 approval A روی B replay نشود · 177 actor غیرمالک خطرناک نه ·
178 state ناشناخته green نه · 179 timeout+retry = duplicate نه · 180 direct Telegram→leg bypass رد.

### S. repair planning، patch control (181-190)
181 gap → critical/high/medium/low · 182 بدون‌ریسک از owner-gated · 183 فایل‌های احتمالی ·
184 rollback plan · 185 کوچک/additive/پشتِ flag · 186 live module بدونِ دلیل بازنویسی نه ·
187 adapter به‌جای fake-implementation · 188 before/after flow diagram · 189 تست قبلِ patch ·
190 اطمینان نداری → proposal + uncertainty.

### T. تحویل، گزارش، verification نهایی (191-200)
191 files/components scanned · 192 blackbox inventory · 193 wiring map · 194 broken paths ·
195 unknowns + owner questions · 196 repair plan مرحله‌ای · 197 test + mutation plan · 198 risk register ·
199 quick wins از blockers · 200 هیچ‌چیز بدونِ evidence/test/contract green نشود.

---

## قالبِ گزارش خروجی

```md
# Deep Scan Report — Octopus / Telegram / Painter / OnlyFans

## 1. Executive Summary
- وضعیتِ کلی · بزرگ‌ترین blocker · Telegram→Octopus→Leg→Response کامل؟ · painter dispatch؟ ·
  OnlyFans dispatch؟ · response به Telegram/dashboard؟ · side-effect idempotent؟

## 2. Terminology Resolution (table: اصطلاح/معنی/evidence/confidence)
## 3. Component Inventory (component/path/role/flag/status/tests)
## 4. Blackbox Contract Matrix (blackbox/input/output/status/errors/idempotency/verdict)
## 5. Telegram Wiring Map (txt)
## 6. Octopus Main Routing Map (txt)
## 7. Leg Dispatch Map (txt)
## 8. Response Return Map (txt)
## 9. Broken / Missing / Unknown (id/severity/gap/evidence/suggested repair)
## 10. Checklist Results (range/area/pass/fail/partial/unknown/notes)
## 11. Repair Plan (Phase 1 read-only mapping · 2 adapter contracts · 3 Telegram routing ·
       4 Octopus→leg dispatch · 5 response/status · 6 idempotency/retry/recovery · 7 tests/mutation)
## 12. Test Plan (unit · integration · e2e · mutation · restart/recovery · security/permission)
## 13. Owner Questions
## 14. Risk Register (risk/severity/affected/mitigation)
## 15. Final Verdict (safe-to-patch · needs-owner-decision · biggest-risk · next-step)
```

---

## روشِ کارِ اجباری

۱. اول فقط read-only scan. ۲. هیچ send/publish/delete/pay واقعی. ۳. secret/PII چاپ نشود.
۴. component map. ۵. contract استخراج. ۶. مسیرِ کامل با evidence:
`Telegram → Octopus → Leg → Result → Octopus → Telegram/Dashboard`.
۷. چک‌لیستِ ۲۰۰تایی item-by-item. ۸. برای هر FAIL/UNKNOWN/PARTIAL repair suggestion.
۹. اگر API نیست → adapterِ honest-blocked. ۱۰. workflow انسانی → machine-API فرض نشود.
۱۱. مسیرِ broken → fake-green نه. ۱۲. patch لازم → اول plan، بعد فایل‌ها، بعد تست.
۱۳. owner approval → مشخص و جدا. ۱۴. risk بالا → توقف + question. ۱۵. خروجی برای ایجنتِ بعدی قابلِ اجرا.

---

## خط قرمزهای نهایی
fake-green ممنوع · fake-success ممنوع · fake module_id ممنوع · ارسالِ واقعیِ Telegram بدونِ اجازه ممنوع ·
publish/send/delete/pay بدونِ owner approval ممنوع · echo secret/PII ممنوع · bypass owner gate ممنوع ·
تغییرِ بزرگ بدونِ تست ممنوع · reset/پاکسازیِ state بدونِ approval ممنوع · اگر نمی‌دانی، بگو.
```
