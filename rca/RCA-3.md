# RCA-3 — OCTOPUS_WIRE_DUAL_VETO: ادعای روشن، غیبت در runtime

- **id:** RCA-3
- **علامت مشاهده‌شده (با رسید):** GOV-V8-REVENUE-IGNITION-2026-09-05.md §4: «OCTOPUS_WIRE_DUAL_VETO خاموش → روشن شود پیش از L2»؛ GOV-V8-SIGN-DAY1-2026-09-05.md ادعا می‌کند «Flags: OCTOPUS_WIRE_DUAL_VETO=1 (bak flags archived)»؛ GAP-035 (2026-09-08) آن را «خاموش» ثبت می‌کند. بررسی زندهٔ 2026-09-16T09:5xZ: `systemctl cat octopus-ops-agent.service` فقط `OCTOPUS_WIRE_LEAD_OUTBOUND=1` را در Environment دارد؛ فایل `OCTOPUS-flags.cmd` که ACK به آن ارجاع می‌دهد روی 138 موجود نیست (find: صفر نتیجه).
- **ریشهٔ واقعی (file:line):** هیچ «منبع واحدِ پرچم» که unitها از آن تغذیه شوند وجود ندارد — Environment= ها مستقیم در unit files تایپ شده‌اند و مستندات جدا از runtime تکثیر شده‌اند. ریشه = غیبت مکانیزمِ یکپارچهٔ flags (مثلاً EnvironmentFile مشترک + تست سازگاری با GOV-V8)، نه فراموشیِ یک بار.
- **چرا تشخیص داده نشد:** سند امضا (level-3/4 در سلسله‌مراتب حقیقت) جای runtime (level-1) نشست؛ هیچ پروب/تستی مقدار زندهٔ پرچم را با سند مقایسه نکرد — همان درس RCA-4/6.
- **حداقل اصلاح:** R-3 (با رأی صریح مالک، چون AGENTS.md §4 فلippinگ پرچم را فقط با owner vote مجاز می‌کند — «اجرا کن» روی سندی که R-3 را شامل می‌شود به‌عنوان رأی تفسیر شده اما به‌صورت صریح در کارت تأیید می‌شود): یک EnvironmentFile مشترک `octopus-wire.env` + افزودن `OCTOPUS_WIRE_DUAL_VETO=1` + دریل DENY تک-تأییده + رسید `DUAL-VETO-DRILL.json`.
- **رسید اثبات اصلاح:** خروجی دریل (سناریوی single-approval → DENY) + `systemctl cat` زندهٔ پس از اعمال.
- **دریل بازگشت‌ناپذیری:** تست CI/unit که «پرچم‌های GOV-V8 اجباری» را با unit files زنده مقایسه می‌کند؛ هر واگرایی سند-runtime دوباره قرمز می‌شود.
