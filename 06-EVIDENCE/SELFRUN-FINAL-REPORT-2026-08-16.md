---
type: evidence-report
created: 2026-08-16 ~16:2x
mission: MEGAPROMPT-SELFRUN-FINAL F1..F10 — اجرای کامل با اجازه‌های واقعی مالک
agent: ZCode (GLM-5.3)
---

# SELFRUN-FINAL — گزارش پایانی

| F | نتیجه | شاهد/کامیت |
|---|---|---|
| F1 PAT پچ + R1 | ✅ | `github_pat_` صفر در فایل → env · R1 بسته (e151b2f) |
| F2a C-026 گیت enabled | ✅ اعمال | پچ صبحگاهی applied · تست xfail→positive exit=0 (8bdd9c7) |
| F2b DARE گارد | ✅ اعمال | `P_closed` هر دو مسیر کف 1e-12 · تست→positive 5/5 (8bdd9c7) |
| F2c manifest بازسازی | ✅ | ۱۴ digest + پاکت NO-GO · **امضای قدیمی stale — دو فرمان دست مالک (پایین)** |
| F3 m پیاده‌سازی | ✅ | `_ops/margin/` (۴ خانواده + m_of + gate 0.1) + shadow_log · تست 6/6 (986f90f) |
| F4 ثبت در run_all | ✅ | +۳ تست (margin/sog/selfheal) — WORKLOCK چک شد (986f90f) |
| F5 ریشه‌یابی فرضیه‌ها | ✅ **باگ نیست** | ۵۲ ردیف امروز همگی status=dedup (append-only برچسب‌خورده) · active امروز=۰ · صف فعال ۳۸۲→۳۹۷ = ظرف ≤10/روز سالم |
| F6 R27 | ✅ از قبل فیکس | `_strip_reasoning_preamble` زنده · تست سبز — توسط سشن موازی |
| F7 C-014 اثبات نهایی | ✅ | evidence.db: از غیرفعالی فقط :06 (seq 24-31) — سری :36 مرده |
| F8 OFN دستورها | ✅ | الحاقیهٔ git-remote در MORNING-CARDS (روی برد: push به شاخهٔ ofn/board-snapshot؛ محلی: mirror بدون overwrite) |
| F9 سنجش چهارم | ✅ | 1.000 پیوسته · all-time 0.980 · fold پیوسته · ⚠️ germline 1.0h |
| F10 همگامی/بستن | ✅ | CONTRADICTIONS/MEASUREMENT/MORNING-CARDS بروز · WORKLOCK آزاد · ۷ کامیت/۷ پوش |

## ⏳ فقط دو فرمان دست مالک (امضای TCB پس از F2)
```powershell
cd F:\backup
openssl pkeyutl -sign -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" -rawin -in "4d_system\config\trust-boundary.json" -out "4d_system\config\trust-boundary.json.sig"
openssl pkeyutl -verify -pubin -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" -rawin -in "4d_system\config\trust-boundary.json" -sigfile "4d_system\config\trust-boundary.json.sig"
```
(تا امضا/ری‌استارت بعدی، پروسه‌های زنده کدِ پیش از F2 را دارند — فیکس‌ها در درخت و git اند.)

## چک‌لیست
راز صفر (PAT با prefix-match، مقدار هرگز چاپ نشد) · فلگ تازه صفر · حذف صفر · هر رفتار نو با تست در همان کامیت · پوش بعد هر کامیت (۷/۷) · شناسهٔ آزاد: **C-031**
