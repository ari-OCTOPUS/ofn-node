---
type: evidence-note
created: 2026-08-16 ~03:1x local (پایان جلسهٔ ۸ ساعته)
mission: سنجش ۸ ساعتهٔ حافظه/یادگیری/خودترمیمی — به درخواست مالک
level: A (همه با اجرای زنده؛ فرمان‌ها برای بازتولید ثبت شده‌اند)
baseline_for: "ایجنت بعدی باید همین اعداد را با همین فرمان‌ها دوباره بگیرد و مقایسه کند"
---

# MEASUREMENT — حافظه/یادگیری/خودترمیمی (19:00 08-15 ← 03:10 08-16)

## Baseline ثبت‌شده (سطح A)

### حافظه
| متریک | عدد | فرمان بازتولید |
|---|---|---|
| read-before-decision امشب (id 34217..34429) | **30/30 = 1.0** | `cd 4d_system && python -X utf8` → کوئری dashboard_events، نسبتِ کارهای تصمیم (creative/conclude/introspect) با memory.read در همان trace قبل از completion |
| read-before-decision کل تاریخ | 30/39 = 0.769 (۹ کارِ pre-fix دوران جولای — بلندِ صادقانه) | همان |
| readback | 1/1 = 1.0 | همان (memory.readback) |
| dedup | ۱۳ create → ۱ نوشتن (hypotheses 1062→1063) | شمارش rows با timestamp امروز |
| انبار 4d | experiments 11 · hypotheses 1063 · rhythms **3140** (+7 امشب) · reflections 2 | sqlite COUNT |
| consolidation | 625 سیکل، آخرین ts=19:20 (پیش از فیکس)؛ **فیکس fold از ری‌استارت 00:52 مستقر است — شاهدش در چرخهٔ بعدی** | تحلیل neural/consolidation.json |
| recall_reach | events 58 · reach_median 2.0 · self_ratio 0.0112 (بدون شلیک دور جدید) | ORGANISM-STATE.json |

### یادگیری
| متریک | عدد | فرمان |
|---|---|---|
| هبیَن (بازنویسی 02:25 — یادگیری فعال) | top: `afferent_starved↔errors_high` 0.506 (37 هم‌وقوعی) | `_ops/neural/hebbian.json` (لیست؛ strength) |
| کالیبراسیون بیزی | n=292 · Brier 0.1738 · AURC 0.3175 · ungraded 184 | `_ops/state/cortex/calibration-latest.json` |
| کشفیات / semantic_memory / c6 | 135 · 236 خط · 104 گذار | شمارش خطوط jsonl |
| رویدادهای ارگانیسم امشب | 92 | `_ops/state/events.jsonl` با ts>1786710000 |
| frontier | از مسیرهای من خوانده نشد (CURRENT-REALITY: 27 ناحیه — unverified توسط من) | — |

### خودترمیمی
| متریک | عدد | فرمان |
|---|---|---|
| ری‌استارت‌ها | **۲ ری‌استارت کاملِ کنترل‌شده**: 20:52 (PIDs 16584/4176/1632/15080/18060) و **00:52-00:57** (21744/9380/8536/16620/27240) — هر دو از گیتِ 300s رد شدند؛ ارگانیسم started=00:54:27 | netstat + Get-Process + ORGANISM-STATE.started |
| مدارشکن orchestr | باز در ~21:00 → **closed, fail_count=0 در 03:10** | `_ops/state/circuit-state.json` |
| BOM (C-010) | رفع‌شده و پایدار (بدون BOM) | خواندن بایت اول circuit-state.json |
| مینیاپ-واچداگ | 104 خط امشب؛ آخرین 03:08 «gateway up, tunnel up» | `_ops/state/miniapp-watchdog-log.txt` |
| watchdog مرکزی | 37 خط؛ آخرین 03:04 «cortex: alive on 8772» | `_ops/state/watchdog-log.txt` |
| کلیدهای کشتن | STOP/HALT/kill.switch هر سه غایب | وجود فایل‌ها |
| germline_lag | 0.87h → **0.22h** | ORGANISM-STATE.json |
| beat | 36878 (19:47) → **37303** (03:08)؛ ~58/h روان · halted=None · conflicts=[] | ORGANISM-STATE.json |
| دانش/کد | ۹ کامیت امشب (8a5e98b→576c7fb) | git log |

## نکات باز برای ایجنت بعدی
1. **PID 22044** (python، بالا آمده 03:09:09) — منشأ نامشخص؛ ردیابی شود.
2. ری‌استارت 00:52 از طرف چه کسی/چه چیزی بود؟ (من در 20:52 انجام دادم؛ 00:52 نه — احتمالاً سشن موازی؛ کدِ مستقر با HEAD آن لحظه تطبیق شود)
3. consolidation: اولین چرخهٔ بعد از ری‌استارت 00:52 باید fold در ردیف‌های غنی را نشان دهد (repeats≥2 با latent_vector) — یا فیکس شکست خورده است.
4. daemon 4d هنوز خاموش — telemetry پیوسته ندارد؛ اجراهای من (4d) تنها منبعِ امشب بودند.
5. recall صفر شلیک جدید — «به‌یادآوریِ دور» همچنان ضعیف‌ترین حلقهٔ حافظه.
