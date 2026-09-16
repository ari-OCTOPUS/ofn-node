# R01-TEST-MATRIX — دستور، محیط، exit، مدت، شبکه، نتیجه

run: R01-191-20260818-2217 · محیط: Windows 10 · Git Bash · Python 3.13 (`python -X utf8`) · cwd=`F:\backup`
شبکه: **صفر** — هیچ تستی تماس شبکه نداشت/نداشت (پیش‌چک کلیدواژه‌های requests/subprocess/socket روی envelope-test: خالی).
ثبت صادقانه: در اجرای اول، exit codeها به‌اشتباه از انتهای pipeline (tail) گرفته شد و بی‌اعتبارند؛ اجرای دوم و بعدی‌ها exit مستقیم دارند. هر دو اجرا در `02-test-matrix-runs.txt` محفوظ‌اند.

| # | هدف | دستور | exit | مدت | نتیجه |
|---|---|---|---|---|---|
| T1 | طبقه‌بندی نردبان اقدام | `pytest -q _ops/action_bridge/tests/test_classifier.py` | 5 | 2s | **no tests ran** — الگوی `t_*`، pytest collect نمی‌کند |
| T2 | سیاست صف فرضیه R16 | `pytest -q 4d_system/tests/test_hypothesis_policy_r16.py` | 0 | 2s | ۱۱ تست پاس (`[100%]`) |
| T3 | verifier کتابچهٔ ریاضی | `pytest -q _ops/tests/test_verify_math_atlas.py` | 0 | 3s | **41 passed** in 1.55s |
| T4 | قرارداد Evidence Envelope | `pytest -q _ops/tests/test_evidence_envelope_handshake.py` | 5 | 1s | no tests ran — الگوی `t_*` |
| T5 | همان T1 با درایور سفارشی | `PYTHONPATH=. python run_t_tests.py test_classifier.py` (cwd=tests) | 0 | <1s | **۲۴ اجرا / ۲۴ پاس / ۰ شکست** |
| T6 | همان T4 با درایور سفارشی | `python run_t_tests.py test_evidence_envelope_handshake.py` (cwd=_ops/tests) | 0 | <1s | **۶ اجرا / ۵ پاس / ۱ نیازمند fixture (`t_atomic_write_nonzero(tmp)`)** — شکست نبود؛ محدودیت درایور |
| T7 | صحت MANIFEST مرحلهٔ F1 (شرط D1 مالک) | `sha256sum -c …/MANIFEST.sha256` | 0 | <1s | **27/27 OK** — ثبت در `06-EVIDENCE/F1-191-20260818-2122/D1-MANIFEST-VERIFY.txt` |

## یافته‌های ماتریس

1. **شکاف کشف تست (MED):** دو فایل «تست» با ۳۰ تابع واقعی، زیر pytest استاندارد صفر collect می‌شوند (exit=5). هر ادعای «تست سبز» باید runner را نام ببرد؛ در غیر این صورت «سبز» بی‌معناست. (BUG-REGISTER B3)
2. نتیجهٔ واقعی policy/classifier/envelope/math-atlas در اجرای مستقیم: ۷۰ assertion-function پاس، ۰ شکست واقعی.
3. suite-wide claim نمی‌کنم — فقط همین هفت هدف اجرا شد (طبق «targeted first» مالک).

## تست‌های اجباری مالک — وضعیت پاسخ (از نگاشت کد 03-code-map)

| تشخیص要求的 | وضعیت | شاهد |
|---|---|---|
| prediction قبل از outcome ثبت می‌شود؟ | **PARTIAL/UNVERIFIED** — anticipation_queue (insert/consume/delete در chrono.py:1252/1405/1416) موجود؛ اما امتیازدهیِ پیش‌بینیِ منجمدشده فقط در اسناد watch (کامیت 03c3bf0: n=80، Brier 0.0001، همه y=1 → calibration تست‌نشده). حلقهٔ runtime اثبات نشد. | 03-code-map (b) |
| پذیرش حافظه evidence/تناقض‌جویی می‌خواهد؟ | **NOT FOUND در مسیر ingest** — `self_loop_ingest.py` → `self-loop-ingest.jsonl` (۹۹۴KB، فعال، بی‌گیت دیده نشد). قرارداد admission وجود ندارد. | 03-code-map (d) |
| بازیابی provenance/timestamp/confidence/expiry برمی‌گرداند؟ | **PARTIAL** — confidence در schema هست (store.py:67,140)؛ provenance و expiry **دیده نشد**. | 03-code-map (c) |
| خروجی مدل بدون تأیید وارد canonical می‌شود؟ | **RISK-OPEN** — مسیر ingest خام فعال است؛ گیت admission یافت نشد (همان ردیف بالا). بازبینی عمیق‌تر = F3/R02. | 03-code-map (d) |
| خطا/retry/timeout/budget/receipt در API قابل مشاهده است؟ | **UNVERIFIED** — ۱۰+ ماژول شبکه شناسایی شد (outbound_https، approval_channel، email_inbound، web_research، …)؛ قرارداد یکنواخت receipt دیده نشد. نگاشت کامل = R01-API-BOUNDARY. | 03-code-map (e) |
| «یادگیری» پیش‌بینی آینده را عوض می‌کند یا فقط متن می‌افزاید؟ | **UNPROVEN** — ذخیره/بازیابی قوی است؛ اثر بر تصمیم بعدی اثبات نشد (gated_effect=۰ در chrono). | 07c + 03-code-map |
| shutdown/deny بر همهٔ اولویت‌ها غلبه می‌کند؟ | **DESIGNED-PRESENT** — opslib.py:357–367: HALT-ALL (پنیک) > STOP(معمار) > halted()؛ enforcement در هر حلقه/کانکتور = CLAIMED، تست runtime نشده. | 03-code-map (g) |
| ID تکراری تناقض/شاهد؟ | **PASS** — events.jsonl: ۴٬۶۷۵ شناسه، ۰ تکرار. (نکتهٔ جزئی: ۴٬۶۳۱ newline در برابر ۴٬۶۷۵ خط parse — احتمالاً CRLF/خط آخر؛ ثبت شد.) | 03-code-map (h) |
