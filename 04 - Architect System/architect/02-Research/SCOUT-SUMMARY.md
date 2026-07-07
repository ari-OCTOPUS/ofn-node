---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
tags: [scout, architecture, summary, synthesis]
status: done
created: 2026-07-03
sources: ["[[04 - Architect System/architect/02-Research/SCOUT-A]]", "[[03 - Projects/Mining/04 - Research/SCOUT-B]]", "[[04 - Architect System/architect/02-Research/SCOUT-C]]"]
updated: 2026-07-04
---

# SCOUT-SUMMARY — سنتز نهایی سه ترک

> جمع‌بندی عملیاتی [[04 - Architect System/architect/02-Research/SCOUT-A|SCOUT-A]] (Orchestration & Governance)، [[03 - Projects/Mining/04 - Research/SCOUT-B|SCOUT-B]] (CPU/ARM Edge-Mining) و [[04 - Architect System/architect/02-Research/SCOUT-C|SCOUT-C]] (Adjacent-Field Borrowing).
> **اعتبارسنجی:** ۲۰ منبع اصلیِ [Verified] با یک ایجنت مستقل adversarial بازچک شد — همه resolve شدند و عنوان/محتوا منطبق بود. هیچ repo/paper/arXiv اختراعی وارد کاتالوگ نشد. سه تصحیح ریز اعمال شد (پایین).

---

## ۱. TOP BORROW CANDIDATES — رتبه‌بندی بر اساس adoption-ROI

> «قابلیت به‌دست‌آمده به ازای هر ساعت یکپارچه‌سازی.» این لیست عملیاتی است — از بالا شروع کن.

### ①  Huge pages + self-compile xmrig  ‹Track B›
- **چه می‌گیری:** تا **+۵۰٪** RandomX (huge pages) + چند درصد دیگر (1GB pages) + برد GCC/`-mcpu=cortex-a76`، همه **صفر وات اضافه**.
- **هزینه:** دقایق تا یک ساعت per board. `hugepages` در cmdline کرنل + یک فلگ config + یک build از سورس.
- **منبع:** xmrig hugepages/RandomX guide [Verified] · auto-joe/DocDrydenn build [Verified] → [[03 - Projects/Mining/04 - Research/SCOUT-B#B1|B1]], [[03 - Projects/Mining/04 - Research/SCOUT-B#B4|B4]]
- **چرا #۱:** بالاترین ROI خالص کل تحقیق — کمترین کار، بزرگ‌ترین دلتای فوری روی درآمد ماین.

### ②  LiteLLM به‌عنوان choke-point واحد  ‹Track A›
- **چه می‌گیری:** kernel در مرز مدل + spend-breaker. اگر ایجنت‌ها فقط virtual-key پراکسی را داشته باشند (egress firewall فقط پراکسی را باز بگذارد): tool_callهای غیرمجاز با regex قبل از رسیدن به ایجنت حذف می‌شوند (`default_action: deny`)، و `fail_closed_budget_enforcement: true` روی سقف خرج = breaker خودکار «نبود تاییدِ spend → 503».
- **هزینه:** یک بلوک YAML (احتمالاً LiteLLM را همین حالا داری).
- **منبع:** LiteLLM tool_permission + budgets [Verified] → [[04 - Architect System/architect/02-Research/SCOUT-A#A14|A14]], [[04 - Architect System/architect/02-Research/SCOUT-A#A27|A27]]
- **چرا بالا:** ارزان‌ترین upgrade منفردِ حاکمیت؛ هم‌زمان دو ضعف (kernel-bypass + خرج runaway) را می‌زند.

### ③  anchoring خارجی سرِ Anchor Ledger  ‹Track A ⨯ C›
- **چه می‌گیری:** «صاحب دیسک تاریخ را بازنویسی می‌کند» را می‌کشد. هر ساعت cron: `ots stamp` روی head hash (انکر Bitcoin، رایگان) + push head به git remote بیرون-box + (اختیاری) RFC 3161 TSA. سه ریشه اعتماد مستقل.
- **هزینه:** ~۱۰ خط + cron.
- **منبع:** OpenTimestamps client [Verified] · Russ Cox tlog + RFC 6962/3161 [Verified] → [[04 - Architect System/architect/02-Research/SCOUT-A#A19|A19]], [[04 - Architect System/architect/02-Research/SCOUT-C#C8|C8]], [[04 - Architect System/architect/02-Research/SCOUT-C#C9|C9]]
- **چرا بالا:** مستقیم‌ترین فیکسِ اصلی‌ترین ضعفِ نام‌بردهٔ Ledger، تقریباً رایگان.

### ④  XMRigCC — C2 فلیت ماین  ‹Track B›
- **چه می‌گیری:** کنترل کامل فلیت از راه دور (start/stop/reboot، config template یک‌کلیک، log viewer، upgrade) + **آلارم hashrate/offline via Telegram** + daemon زنده‌نگه‌دار. ARMv8-native.
- **هزینه:** یک install؛ سرور C2 یک process کوچک. مستقیم روی `Mining/Mining-1`.
- **منبع:** github.com/Bendr0id/xmrigCC (v3.4.9، Jan 2026، GPL-3) [Verified] → [[03 - Projects/Mining/04 - Research/SCOUT-B#B16|B16]]
- **چرا بالا:** نزدیک‌ترین چیز به «مدیر فلیت آمادهٔ ARM»؛ SSH دستی روی ماینرها را کامل حذف می‌کند.

### ⑤  بازقاب‌بندی kill-switch: heartbeat-lease + hardware watchdog + halted-safe boot  ‹Track A ⨯ C›
- **چه می‌گیری:** مهم‌ترین فیکس ساختاری حاکمیت. kill از «فرمان توقف» به **de-energize** تبدیل می‌شود: ایجنت فقط تا وقتی lease/heartbeat را نگه دارد اجرا می‌شود → نبود سیگنال = توقف پیش‌فرض (fail-safe). WDT سخت‌افزاری SoC، اگر supervisor/کرنل بمیرد reboot می‌کند؛ unitها auto-start نیستند → به halted-safe می‌نشیند.
- **هزینه:** S–M (طراحی مجدد مسیر kill + `RuntimeWatchdogSec` + unitها بدون auto-start).
- **منبع:** ISO 13850 E-stop [Verified] · Buytaert Pi watchdog [Verified] · LiteLLM budgets [Verified] → [[04 - Architect System/architect/02-Research/SCOUT-C#C4|C4]], [[04 - Architect System/architect/02-Research/SCOUT-A#A28|A28]], [[04 - Architect System/architect/02-Research/SCOUT-C#C6|C6]]
- **چرا بالا:** جواب مستقیم به «kill-switch وقتی خودِ supervisor مریض است» — از دکترین ۵۰-سالهٔ ایمنی صنعتی.

### ⑥  verdict غیرقابل‌انکار + ضد-fatigue: FIDO2 + schema چهارحالته + challenge/sterile  ‹Track A ⨯ C›
- **چه می‌گیری:** verdict انسانی واقعاً root-of-trust می‌شود — امضای کلید سخت‌افزاری FIDO2 (لمس فیزیکی = proof-of-presence، حتی با box روت‌شده جعل‌ناپذیر)؛ schema چهارحالته (approve/**edit**/respond/ignore) نگاشت‌شده به دکمه‌های inline تلگرام؛ UX از «کلیک Yes» به challenge→typed-response + حالت sterile (خفه‌کردن بقیه promptها هنگام گیت بحرانی).
- **هزینه:** S (یک کلید ~$30 + کد؛ schema را بگیر نه اپ Next.js).
- **منبع:** Yubico HITL [Verified] · agent-inbox [Verified] · SKYbrary sterile cockpit [Verified] → [[04 - Architect System/architect/02-Research/SCOUT-A#A18|A18]], [[04 - Architect System/architect/02-Research/SCOUT-A#A24|A24]], [[04 - Architect System/architect/02-Research/SCOUT-C#C3|C3]]
- **چرا بالا:** approval-fatigue بزرگ‌ترین شکست واقعی گیت solo است (۹۳٪ approve کور)؛ این سه با هم آن را می‌بندند.

### ⑦  استک فلیت: Tailscale + pyinfra + Beszel + systemd Restart  ‹Track B ⨯ C›
- **چه می‌گیری:** جایگزین کامل SSH دستی — mesh با NAT traversal (node پشت CGNAT پایدار)، config/exec agentless و idempotent با `--dry`، مانیتور فوق‌سبک با آلارم فرسایش eMMC، و self-heal با `Restart=on-failure`. همه OSS/رایگان.
- **هزینه:** S (چند نصب؛ همه sub-datacenter، بدون k8s).
- **منبع:** Tailscale/Headscale [Verified] · pyinfra [Verified] · Beszel [Verified] → [[03 - Projects/Mining/04 - Research/SCOUT-B#B14|B14]], [[03 - Projects/Mining/04 - Research/SCOUT-B#B15|B15]], [[03 - Projects/Mining/04 - Research/SCOUT-B#B17|B17]], [[03 - Projects/Mining/04 - Research/SCOUT-B#B18|B18]]
- **چرا بالا:** پایهٔ زیرساختِ همهٔ کارهای فلیت؛ زیرِ XMRigCC تمیز می‌نشیند.

### صف بعدی (PROTOTYPE — ارزش بالا، کار بیشتر)
| الگو | ترک | چرا در صف دوم |
|---|---|---|
| OS-sandbox `srt` (bubblewrap/seccomp) | [[04 - Architect System/architect/02-Research/SCOUT-A#A12|A12]] | فیکس قطعیِ kernel-bypass ولی نیازمند wrap هر ایجنت + allowlist باریک |
| OPA/Cedar PDP sidecar | [[04 - Architect System/architect/02-Research/SCOUT-A#A13|A13]] | لایه سیاست جدا و تست‌پذیر؛ یک باینری اضافه |
| DBOS durable execution | [[04 - Architect System/architect/02-Research/SCOUT-A#A8|A8]] | بقای crash کامل؛ نیازمند بازساختِ پایپ‌لاین به decorator |
| Tessera + witness cosigning | [[04 - Architect System/architect/02-Research/SCOUT-A#A20|A20]], [[04 - Architect System/architect/02-Research/SCOUT-A#A21|A21]] | ارتقای Ledger از hash-chain به tlog واقعی؛ بعد از ③ |
| device shadow self-hosted (Ditto/MQTT) | [[04 - Architect System/architect/02-Research/SCOUT-C#C15|C15]] | desired-state برای فلیت؛ اول روی RK3588 بنچ شود |
| Tari merge-mining | [[03 - Projects/Mining/04 - Research/SCOUT-B#B9|B9]] | دارایی جدید با هزینه hashpower صفر؛ اول pool سازگار ARM verify شود |

---

## ۲. WHO TO FOLLOW — اشتراک دائمی

**حاکمیت و ایجنت (Track A)**
- **Anthropic Engineering blog** (anthropic.com/engineering) — تنها منبعی که FNR/FPR واقعی گیت‌ها را منتشر می‌کند؛ الگوهای canonical + auto-mode + multi-agent.
- **Filippo Valsorda** (words.filippo.io · github/FiloSottile/torchwood · C2SP) — مرجع عملی tlog حداقلی + witness.
- **transparency.dev blog** — Tessera + شبکه witness (جانشین Trillian).
- **DBOS blog** (Qian Li / Peter Kraft) — durable execution «Postgres is all you need».
- **langchain-ai** (deepagents + agent-inbox) — سریع‌ترین تکامل primitives HITL.
- **گروه MAST برکلی** (Cemri/Stoica) — تنها dataset تجربی شکست multi-agent.

**ماین و فلیت (Track B)**
- **SChernykh** + **tevador** (github) — هستهٔ xmrig + طراح RandomX؛ محرک ARM64 JIT و هر برد efficiency.
- **JayDDee (cpuminer-opt)** — لیست الگوهای ساپورت AArch64 ≈ جهان عملی کوین‌های ARM-mineable.
- **BenDr0id (XMRigCC)** — تنها C2 ماین ARM-aware فعال.
- **henrygd (Beszel)** + **juanfont (Headscale)** — baseline سبک مانیتور/mesh.
- **miningpoolstats.stream/newcoins** + **bitcointalk board 159/160** — لبهٔ کشف لانچ‌های تازه.

**رشته‌های مجاور (Track C) — استانداردهای مرجع**
- **ISO 13850 + IEC 60204-1** — spec canonical kill-switch (de-energize، stop categories).
- **IEC 61508 / 61511 (SIL/SIS)** — دکترین «لایه ایمنی مستقل» برای طراحی kernel.
- **Cloudflare Eng blog (Code Orange)** — config-as-code + fail-small در مقیاس.

---

## ۳. GAPS — فرضیه‌های قابل‌جستجو برای run بعدی

**بنچ‌مارک‌های گم‌شده (مهم‌ترین — بدون این‌ها تصمیم‌ها نیمه‌کورند)**
1. دلتای واقعی H/s از LPDDR5-6400 OC + huge pages روی **RK3588 مشخص** — هیچ بنچ اولیه؛ فرضیه memory-bound → شاید +۱۰–۲۵٪. `[test: xmrig randomx orange pi 5 lpddr5 6400 bench]`
2. عدد VerusHash روی Orange Pi 5 (~6.75 MH/s @ 8W) و «~۱۰۰۰ H/s RandomX» فقط search-extracted — **روی برد خودت بنچ کن** قبل از هر تصمیم استراتژیک.
3. H/s برای yespower/GhostRider/AstroBWTv3 روی ARM64/RK3588 — همه جداول موجود x86‌اند. `[astrobwt aarch64 benchmark RK3588]`
4. RAM/CPU واقعی Restate/Inngest/Ditto روی ARM64 — `[restate idle memory ARM64]` · `[eclipse ditto raspberry pi RK3588]`

**حاکمیت**
5. رسپی کامل «srt bubblewrap + OPA + MCP gateway روی یک ARM SBC» منتشر نشده — احتمالاً باید خودمان بنویسیم/منتشر کنیم.
6. «two-person rule برای solo»: فرضیه — قفل تاخیری (verdict بعد از N ساعت cooling اجرا شود مگر cancel) به‌عنوان approver دوم. آیا معنادار است یا به two-factor تنزل می‌کند؟
7. KILLBENCH (arXiv:2511.13725) — benchmark امکان‌سنجی kill-switch خارجی؛ نسخه HTML را fetch کن [Unverified].
8. confidence کالیبره برای gating escalation — `[conformal prediction agent routing]`.
9. سیاست پذیرش Witness Network برای لاگ‌های خصوصی کوچک (prod vs testing list).

**فلیت و اسکاوتینگ**
10. مرجع «GitOps فلیت homelab <۵۰ node با systemd + git-pull» (بدون k8s)؟
11. premine/instamine % توسط هیچ API افشا نمی‌شود — automation از scraping explorer آزمایش‌نشده.
12. مدل کمّی «بقای کوین در ۱–۳ سال» وجود ندارد — **فرضیه: خودِ چارچوب discovery→classify→screen→exit یک سنتز نوآورانهٔ قابل‌انتشار است.**
13. viability هر PoW روی خود ESP32 (نه SBC) — مشکوک فقط الگوهای trivial؛ ESP32 احتمالاً node سنسور/امضا است نه ماینر.

---

## ۴. CONTRADICTIONS — اختلاف منابع معتبر (حل‌نشده)

**حاکمیت**
- **هزینه/فایده multi-agent:** Anthropic «ساده‌ترین را بساز» (Building Effective Agents) در برابر ادعای +۹۰.۲٪ (multi-agent research)؛ MAST می‌گوید سود MAS «اغلب حداقلی». آشتی: فقط برای کار breadth-first موازی و به قیمت ۱۵× توکن.
- **«گیت غیرقابل‌دورزدن» vendorها در برابر FNR ۱۷٪ Anthropic:** گیت‌های classifier نشت دارند؛ لایهٔ non-leaky فقط سقف‌های سخت‌اند (budget/watchdog/allowlist). **هر دو لایه لازم** — نه یکی.
- **E-stop سخت‌سیم آنالوگ نرم‌افزاری تمیز ندارد:** kill نرم‌افزاری روی همان بستری اجرا می‌شود که می‌خواهد متوقف کند. بهترین ترجمه heartbeat-lease است ولی ضعیف‌تر از de-energize واقعی → اگر سیستم به خرج/سخت‌افزار واقعی دست می‌زند، یک رله/PDU فیزیکی که kernel کنترل کند در نظر بگیر.
- **two-person در برابر solo:** قدرت دکترین همان انسان دوم مستقل است؛ solo M-of-N، coercion/خطا را کم می‌کند نه بدقضاوتی را — ریسک باقی‌مانده، نه حل‌شده.
- **FSS journald / CaMeL نقل‌قول‌ها:** جزئیات در [[04 - Architect System/architect/02-Research/SCOUT-A#CONTRADICTIONS|SCOUT-A]].

**ماین**
- **هش‌ریت RandomX روی RK3588:** Rock 5B **۷۳۰ H/s @ ۱۴W** [Verified] در برابر Orange Pi 5 **~۱۰۰۰ H/s/۵ هسته** [Unverified] — همان SoC، ~۳۷٪ فاصله. حل‌نشده؛ روی برد خودت اندازه بگیر.
- **governor=performance:** برای max H/s توصیه شده ولی H/s-per-watt را بدتر می‌کند — تضاد «raw H/s» با «هدف per-watt». با undervolt جبران کن.
- **«RandomX = CPU-only/ASIC-resistant» منسوخ شد:** ASICهای Bitmain X5/X9 (۲۰۲۴–۲۶) [Verified]. ادعای RandomX روی کوین جدید = **پرچم زرد**؛ yespower/yescrypt/GhostRider را روی محور دوام CPU بالاتر رتبه بده.
- **k3s/k0s در لبه:** طرفداران در برابر «برای فلیت solo خیلی سنگین» — اعداد (~۶۵۸–۷۵۰MB control-plane) طرف شکاک را تایید می‌کنند → **SKIP k8s**.

**فلیت/لاگ**
- **WORM قانونی در برابر self-hosted:** اصلاحیه SEC 17a-4 (۲۰۲۳) مسیر audit-trail بازساخت‌پذیر را باز کرد → «immutability = خرید WORM appliance» را خودِ رگولاتور نقض می‌کند.
- **«device shadow به cloud نیاز دارد» در برابر Ditto/aMQTT self-hosted** — به‌نفع self-host حل شد.
- **push فوری جهانی در برابر قطعی‌های ۲۰۲۵ Cloudflare** — خودِ حوزه حالا می‌گوید سرعت بدون gating یک باگ است.

---

## تصحیح‌های اعتبارسنجی (اعمال‌شده)
- **MAST** دقیقاً **۱۴** حالت شکست دارد (نه «~۱۴»). arXiv:2503.13657 = «Why Do Multi-Agent LLM Systems Fail?» [Verified].
- **AURA** عنوان دقیق: «AURA: An Agent Autonomy Risk Assessment Framework» (Exeter، Oct 2025)، arXiv:2510.15739 [Verified].
- **Tari** دقیق‌تر: RandomX **+ SHA3x** دو-الگویی، سمت RandomX با Monero merge-mined [Verified].

---
*این فایل + SCOUT-A/B/C طبق قانون اساسی vault در `00 - Inbox` هستند؛ گام بعد = دسته‌بندی: کارت‌های Track A/C→A به `04 - Architect System`، Track B به `03 - Projects/Mining`، و منابع ماندگار به `07 - Knowledge`.*
