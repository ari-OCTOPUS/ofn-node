# 🔮 4D System — کشف نشانه‌های بُعد چهارم

سیستم مولتی‌ایجنت برای کشف نشانه‌های ساختار بُعد پنهان در داده‌های خام، بر اساس معادلات پروژه‌ی SOG.

## ⚡ شروع سریع

```bash
cd 4d_system

# نصب پکیج‌ها (یک‌بار)
pip install -r requirements.txt

# اجرای داشبورد
streamlit run run.py
```

سپس مرورگر را روی `http://localhost:8501` باز کنید.

## 🏗️ معماری

```
4D/                    ← مرجع تغییرناپذیر (فقط خوانده می‌شود)
└── 4.py, *.md, *.docx

4d_system/             ← کل سیستم
├── core/              ← موتور ریاضی (استخراج‌شده از 4.py)
│   ├── model.py       ← DARE, P_closed, S, S_b, Δ_self, E_shadow
│   ├── metrics.py     ← I_pred, empirical shadow, fit parameters
│   └── simulator.py   ← Monte-Carlo verification
├── data/              ← منابع داده
│   ├── synthetic.py   ← Gaussian, AR(1), ARMA, chaos
│   ├── physical.py    ← Brownian, oscillator, Lorenz, pendulum
│   └── real_api.py    ← Yahoo Finance, NOAA
├── agents/            ← تیم مولتی‌ایجنت
│   ├── orchestrator.py   ← رهبر (dispatch + gate)
│   ├── verifier.py       ← W0: راستی‌آزمایی لنگرها
│   ├── detector.py       ← W1: تشخیص سایه
│   ├── analyst.py        ← W2: تحلیل هندسی
│   └── reporter.py       ← W3: گزارش نهایی
├── llm/               ← کلاینت‌های API
│   ├── glm_client.py     ← GLM (Z.ai)
│   ├── fugu_client.py    ← Sakana Fugu
│   └── router.py         ← مسیریابی + mock mode
├── knowledge/
│   └── ledger.py         ← بارگذاری مرجع 4D/
├── ui/
│   └── app.py            ← داشبورد Streamlit
├── run.py                ← نقطه‌ی ورود
└── requirements.txt
```

## 🔑 تنظیم API Keys

1. فایل `.env.example` را به `.env` کپی کنید
2. کلیدهای خود را پر کنید:
   ```
   GLM_API_KEY=your-key
   FUGU_API_KEY=your-key
   ```

بدون کلید، سیستم در **mock mode** کار می‌کند (برای تست UI).

## 🧪 pipeline ایجنت‌ها

```
W0 (gate) → W1 (detect) → W2 (analyze) → W3 (report)
```

- **W0 Verifier**: لنگرهای عددی را با 4.py تطبیق می‌دهد. اگر FAIL ⟹ توقف.
- **W1 Detector**: E_shadow و ρ را روی داده تخمین می‌زند. آیا λρ≠0؟
- **W2 Analyst**: تفسیر هندسی (Takens، tesseract، Theorema Egregium).
- **W3 Reporter**: report card نهایی + جدول Rosetta.

## 📊 سه تب داشبورد

1. **🧪 آزمایش** — انتخاب داده، اجرای pipeline، مشاهده‌ی نتایج
2. **💬 کاوش** — گفت‌وگوی آزاد با ربات متخصص
3. **📚 مرجع** — مشاهده‌ی فایل‌های 4D/ و لنگرها

## ✅ تست

```bash
python run.py          # self-test کامل
python -m core.model   # تست لنگرها
```

## ⚖️ قانون طلایی

دایرکتوری `4D/` منبع تغییرناپذیر است. سیستم **هرگز** به آن نمی‌نویسد.
