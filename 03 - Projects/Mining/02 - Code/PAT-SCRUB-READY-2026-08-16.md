# R1 — پچِ آمادهٔ پاک‌سازی PAT (بعد از چرخشِ مالک، نه قبل)

**وضعیت (2026-08-16):** PAT گیت‌هاب (`github_pat_…` — مقدار کامل فقط در خودِ
`scout_all_in_one.py:38` و تاریخِ git) هنوز **چرخیده نشده** (gh CLI هم نصب
نیست — چرخش فقط از وب‌اکانت مالک ممکن است).

**قاعدهٔ مگاپرامپت R1:** پاک‌سازیِ فایل فقط **بعد از** چرخش (اگر قبل از چرخش
پاک شود، توکنِ زنده فقط از تاریخِ git قابل‌دیدن می‌ماند و اسکریپت هم می‌شکند —
بدترینِ هر دو دنیا).

## قدم‌های مالک (به‌ترتیب)

1. **چرخش** در github.com → Developer settings → Tokens: توکنِ قدیمی را
   revoke کن؛ توکنِ نو با کمینهٔ scope بساز و در `.env` بگذار: `GITHUB_TOKEN=…`
2. **پاک‌سازی** — اسکریپتِ زیر با پیشوند match می‌کند، مقدارِ کامل را
   جایی کپی نمی‌کند:

```bash
cd /f/backup
python - <<'EOF'
import re
from pathlib import Path
p = Path("03 - Projects/Mining/02 - Code/Robo-data/scout_all_in_one.py")
s = p.read_text(encoding="utf-8")
pat = re.compile(r'GITHUB_TOKEN: str = "github_pat_[A-Za-z0-9_]+"')
assert pat.search(s), "توکنِ هارد-کد پیدا نشد — شاید قبلاً پاک شده"
s = pat.sub('GITHUB_TOKEN: str = __import__("os").environ.get("GITHUB_TOKEN", "")', s, count=1)
p.write_text(s, encoding="utf-8")
print("scrubbed: PAT -> env (prefix-matched, no literal copied)")
EOF
git add "03 - Projects/Mining/02 - Code/Robo-data/scout_all_in_one.py"
git commit -m "fix(mining): scrub hardcoded GitHub PAT -> env (R1, post-rotation)"
```

3. کلیدهای شخص‌ثالثِ همان فایل (CoinGecko/SoChain — خطوط ۳۹-۴۰) طبق triage
   گزارشِ gitleaks (`_ops/tests/_baselines/gitleaks-full-20260815.json`):
   «چرخش/حذف/مستندسازی» — تصمیم با مالک؛ ریسکِ پایین‌تر از PAT.

## نکته
پاک‌سازیِ تاریخِ git (BFG) فقط با رأیِ صریحِ مالک — جدا از این پچ.
gitleaks بعد از اعمالِ پچ دوباره اجرا شود (قانونِ خانه).

## هشدار 2026-08-16 ~04:1x
اسکریپت‌های بررسی PAT با الگوی `ghp_` فقط توکن کلاسیک را می‌بینند — توکن واقعی
این فایل **`github_pat_…`** است (fine-grained) ⇒ چنین چکی «سبز کاذب» می‌دهد.
اسکریپتِ پاک‌سازی همین فایل با prefix-match درست است.
