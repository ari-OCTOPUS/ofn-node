# SAFETY-AND-RUNTIME-WIRING-MAP — OCTOPUS 2026-09-17
# lane: OCTOPUS-UNIFIED-RECOVERY-20260917 · فقط شواهد همین نشست/اسناد قفل‌شده؛ هیچ ادعای wired بدون شاهد

## ۱. HALT — oracle کانونیک و خواننده‌هایش

**Oracle (main@dba9971):** `ofn/budget/opslib.py:20` → `HALT_FLAG = OFN_ROOT / "HALT-ALL"` · `master_halted() :28` فقط وجود فایل را می‌خواند.

**⚠ واگرایی مسیرِ مستند:** AGENTS.md والت می‌گوید kill switch = `F:\ofn-node\HALT`؛ سورس main فایل **`HALT-ALL`** را می‌خواند؛ AGENTS.md خود repoی ofn-node هیچ خط HALT ندارد. این همان mismatch چهارم OD-4 (path_divergence) است — اکنون از سورس main مستقل تأیید شد.
**وضعیت سوییچ:** هیچ فایل `HALT*` در worktree repo نیست؛ روی 138 هم `/home/ari/HALT` و `/HALT` هر دو غایب‌اند → kill switch فعال نیست.

**خواننده‌های master_halted روی main (git grep، غیر تست):**
| سایت | نقش |
|---|---|
| `ofn/agents/capability_token.py:87` | گیت توکن |
| `ofn/agents/release_pipeline.py:106,184` | release/kill مسیر |
| `ofn/agents/outbound_worker.py:214,451` (+ کامنت فارسی :212) | رد transport هنگام halt |
| `imap_listener.py:43,180` | پرچم جداگانهٔ campaign-scoped (نه oracle کانونیک) |
| جمع کل سایت‌های is_halted/master_halted در `ofn/` روی main | ۱۹ |

**نقشهٔ OD-4 (درخت زندهٔ F:\ofn-node @0da921b+dirty، رسید e150099):** ۳ مصرف‌کنندهٔ مسیر-WIRED ولی پوشش DOC_ONLY — `node.py:3607 publish_to_telegram` · `router.py:ask` (گیت قبل از _charge()@164) · `assistant_update.py:main` (اولین فراخوان brain :28). دو primitive کِرنلی P-1 `start_permit.py:136` و P-2 `stale_class.py:335` = TESTED_ONLY با صفر caller تولیدی (خارج از دامنه). **سیم‌کشی شروع نشده**؛ پروتکل PRE/POST فریز شده؛ دقیقاً ۴ فایل تغییر می‌کنند؛ oracle همیشه همان `opslib.master_halted()`.

## ۲. سه بدنهٔ واگرای سورس (یافتهٔ جدید این نشست)
| بدنه | HEAD | dirty | نقش طبق مدل فدرال مالک (1B) |
|---|---|---|---|
| GitHub `main` | `dba9971` | — | canonical سورس |
| `F:\ofn-node` (شاخهٔ fix/opslib-import-boundary) | `0da921b` | ۲۴۶ | کارگاه lane ها |
| **board138 runtime (شاخهٔ main محلی)** | **`63938eb`** | ۴۵ | canonical وضعیت deploy |

⚠ runtime روی کامتی است که در GitHub main نیست → «merged ≠ deployed؛ deployed ≠ tracked». هیچ‌یک از سه بدنه با هم یکی نیست.

## ۳. بودجه/گیت/شاهد
- `BUDGET.json` در ریشهٔ repo روی main وجود ندارد (ls-tree=0) — کانون بودجه در مسیر runtime/دیتاست (ROOTFIX: سقف canon ۵۰۰AUD/ماه)؛ گیت‌های پول در `data/gates.json` (فایل محافظت‌شدهٔ OD-4).
- شاهد مستقل ۱۸۲: الزام Class B روی 138 (v1.3.0-witness، بدون fallback) — فعال طبق قرارداد GOV؛ این نشست دوباره ping نشد (UNKNOWN امروز).
- ۱۱۹+ فایل گیت/تایمر: **۸۰ unit-file با نام octopus روی 138** + ۱۱+ timer فعال (بازبینی امروز) از جمله `octopus-budget-monitor.timer` و `octopus-autonomy-supervisor.timer`.
- CODEOWNERS روی main: `* @Elahe-z @aram-ui` — هر کدام به‌تنهایی review معتبر (GOV-V6، رأی 2026-09-03)؛ نویسنده هرگز PR خودش را approve نمی‌کند (independent-review-gate.yml).
- کانال خروجی: فقط Telegram با رسید (ایمیل بازنشسته R2-3)؛ الگوی تأیید مالک «تأیید <8hex>».

## ۴. درزهای بی‌صداکننده (seam بدون caller تولیدی)
`RunGate` (adapters/run_gate.py) · `decide_start` · `admit_refresh` — هر سه می‌گویند «scheduler باید صدا بزند»؛ مصرف‌کنندهٔ بیرون-repo برای lane قابل‌رؤیت نیست (bounded unknown، ثبت OD-4).
**هشدارِ این نقشه:** تا OD-4 سیم نشود، این درزها بسته نمی‌مانند؛ کنترلِ «اعلام‌شده ≠ سیم‌شده» باید با رسید POST اثبات شود، نه با تست سبز (درس ۹۷/۱۰۰).
