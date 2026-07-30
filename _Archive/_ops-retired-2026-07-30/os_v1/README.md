# `_ops/os_v1/` — کدِ اجراییِ OCTOPUS OS v1

پیاده‌سازیِ کاملِ چیزهایی که `OCTOPUS-OS-v1.md` تعریف می‌کند.
**۴۷/۴۷ تست سبز.** stdlib-only، صفر وابستگیِ بیرونی (به‌جز `schumann_rx` که numpy/scipy می‌خواهد).

```
python _ops/os_v1/tests/test_os_v1.py     # باید 47 سبز · 0 قرمز بدهد
```

---

## چرا drop-in و نه پچ

طبقِ §۲.۱ خودِ OS، نوشتنِ موازیِ چند ایجنت روی درختِ زنده ممنوع است — و در ۲۵ جولای
یک نشستِ دیگر ۱۸ فایل نوشت. پس این‌ها **ماژولِ مستقل** هستند، نه پچ روی فایلِ زنده:
additive، flag-gated، fail-soft. کدِ موجود import می‌کند؛ هیچ خطی از `wiring.py` یا
`goal_directed.py` بازنویسی نمی‌شود.

---

## ماژول‌ها

| فایل | §OS | چه چیزی را می‌بندد |
|---|---|---|
| `honest_metric.py` | §۰ §۸ | هر هفت بیماریِ خودارجاعی — واکسنِ اجراپذیر |
| `outcome_ledger.py` | §۳ | تابعِ پاداش: تناقض ساختاراً ناممکن، درون‌زاد رأی نمی‌دهد |
| `efe.py` | §۳ | زمان‌بند با فرمِ ایمن (γ روی کلِ G، قید حذف می‌کند نه جریمه) |
| `mission_runner.py` | §۷ فاز۴ | worktree + گیتِ سوئیت؛ پچِ خراب صفر بایت اثر می‌گذارد |
| `silence.py` | §۷ فاز۲ | ۵۰ هشدارِ هم‌امضا ⇒ ۱ پیام |
| `leg_failure.py` | §۶ | علتِ افتادنِ لِگ — ۶۶ ری‌استارت، صفر تشخیص |
| `schumann_rx.py` | §۹ | گیرندهٔ آنتن با `w_q` و `verdict()` |

---

## سیم‌کشیِ پیشنهادی (flag-gated، پیش‌فرض خاموش)

### ۱ — سنجه‌های صادق

```python
from os_v1.honest_metric import Measurement, Provenance, MetricRegistry

reg = MetricRegistry()
reg.put(Measurement(
    "velocity_per_hr", vel, Provenance.DERIVED,
    receipt="pulse/velocity-stream.jsonl",
    components={"beats_self": beats, "consolidation_self": cons,
                "confirmed": confirmed, "effects": effects},
))
# دادهٔ واقعیِ ۲۵ جولای ⇒ share=1.000 ⇒ w_q=0 ⇒ حق رأی ندارد
reg.weighted("velocity_per_hr")   # 0.0 — نه اینکه بی‌سروصدا رد شود
```

> کلیدهایی که به `_self` ختم می‌شوند درون‌زاد شمرده می‌شوند. همین یک قرارداد،
> `metronome_share=0.9644` را به‌طور خودکار خفه می‌کند.

### ۲ — تابعِ پاداش

`goal_directed._close_intents` و `improve.improvement_rate` را جایگزین کن:

```python
from os_v1.outcome_ledger import close_intents, improvement_rate

closures = close_intents(intents, prior_rows, now_metrics, ts=opslib.now_iso())
for c in closures:
    opslib.append_jsonl(OUTCOMES, c.as_dict())      # schema outcome-closure.v2

ir = improvement_rate(all_rows)     # Measurement، نه dict
digest["improvement_rate"] = ir.as_dict()
```

**انتظار: عدد می‌افتد.** «۴۵٪» با مخرجِ غلط ساخته شده بود. اگر ایجنتی گزارش داد
عدد **بهتر** شد، کار را اشتباه فهمیده.

### ۳ — زمان‌بند

```python
from os_v1.efe import Policy, EFEConfig, evaluate, kernel_constraints

cons = kernel_constraints(
    stop_present=opslib.STOP_ORGANISM.exists(),
    budget_frozen=gate.frozen(),
    owner_verdict_available=bool(pending_owner_verdict),
)
r = evaluate(policies, cons, EFEConfig(gamma=4.0, beta_epistemic=0.25))
```

`β` به `BETA_EPISTEMIC_MAX = 0.5` کلیپ می‌شود. تست ثابت کرده که حتی با `β=999`
هیچ کنشِ قیدشکنی انتخاب نمی‌شود — **چون قید حذف می‌کند، جریمه نمی‌کند.**

### ۴ — ماموریتِ ایزوله

```python
from os_v1.mission_runner import MissionRunner

runner = MissionRunner(
    r"F:\backup",
    [sys.executable, "-X", "utf8", r"F:\backup\_ops\tests\run_all.py"],
    worktrees_dir=r"F:\backup\_worktrees",
    timeout_s=900,
)
res = runner.run(mission_id, apply_patch)
channel.send_text(res.card(), keyboard_if(res.may_merge))
```

`res.may_merge` فقط یعنی **آمادهٔ رأی**. merge بدونِ ✅ صریح رخ نمی‌دهد.

### ۵ — سکوت

```python
from os_v1.silence import SilenceGate, Msg, Kind

gate = SilenceGate(daily_cap=6)
ok, why = gate.allow(Msg(Kind.ALERT, text, topic), time.time())
if ok:
    channel.send_text(text)
else:
    opslib.alert([f"silence: {why}"])      # لاگ، نه پیام

digest = gate.merge_digest({t: body for t, body in per_topic.items()})
```

پیامِ `Kind.VERDICT` هرگز throttle نمی‌شود — آن کارِ مالک است، نه نویز.

### ۶ — علتِ لِگ

```python
from os_v1.leg_failure import FailureRecorder, capture

rec = FailureRecorder(Path(r"F:\backup\_ops\state"))
try:
    leg.tick()
except Exception as e:
    rec.record(capture(e, leg_id, opslib.now_iso(), beat=beat))
    raise                       # ← رفتارِ ری‌استارت دست‌نخورده می‌ماند
```

بعد از ۱۰ شکست، `rec.diagnose(leg_id)` می‌گوید علت واحد است یا پراکنده —
چیزی که ۶۶ ری‌استارتِ `lead-naghshi` هرگز نگفت.

---

## خاصیت‌هایی که تست **ثابت** می‌کند

| خاصیت | تست |
|---|---|
| سنجهٔ خودارجاع (share > 90%) رأی نمی‌دهد | `velocity` واقعی ⇒ `w_q=0` |
| سنجهٔ بی‌رسید رأی نمی‌دهد | `innervation_pct` |
| `delta_self` منفی clamp نمی‌شود | `publish_signed(-0.02573)` |
| هر کلید حداکثر یک بستار ⇒ تناقضِ ۲۰تایی ناممکن | ۳ baseline از یک id |
| رشدِ `total_discoveries` بیت را روشن نمی‌کند | درون‌زاد |
| مخرج = نیتِ متمایز، نه رکورد | ۸۳ رکورد روی ۴ کلید |
| نبودِ داده ⇒ `None`، نه صفرِ ساختگی | `improvement_rate([])` |
| **در هر β، کنشِ قیدشکن انتخاب نمی‌شود** | β = 0 … 999 |
| STOP ⇒ مجموعهٔ خالی، fail-closed | |
| γ بالا = قاطع‌تر، نه بی‌پرواتر | p(a): 0.55 → 0.96 |
| ۵۰ هشدارِ هم‌امضا ⇒ ۱ پیام | |
| **پچِ خراب ⇒ صفر بایت روی درختِ زنده** | تستِ حیاتیِ فازِ ۴ |
| پچی که عمداً به درختِ زنده بنویسد ⇒ گیر می‌افتد | خصمانه |
| فایلِ نوی untracked هم گیر می‌افتد | خصمانه |
| `__pycache__` گارد را الکی شلیک نمی‌کند | ضدِ آژیرِ دروغ |
| سبزِ کامل هم بدونِ رأی merge نمی‌کند | |

---

## دو باگی که خودِ تست‌ها در کدِ من گرفتند

ثبت می‌شود چون §۸ می‌گوید «نبودِ ❌ یعنی سبز نیست»:

1. **`live_fingerprint` خیلی حساس بود.** از `git status --porcelain` ساخته می‌شد و
   اجرای سوئیتِ پایه `__pycache__` می‌ساخت ⇒ گارد هر بار قرمز می‌شد. در تولید یعنی
   آژیرِ دروغ، و بعد از دو روز کسی جدی‌اش نمی‌گرفت — همان بیماریِ §۰ از آن سو.
   **اصلاح:** فقط تغییرِ فایل‌های tracked + فایل‌های untrackedِ غیرِ مصنوعِ ساخت.

2. **`SNR` در `schumann_rx` غلط تعریف شده بود** — باندِ ۷–۹ تقسیم بر «هرچیزِ بیرونِ
   باند»، که هارمونیک‌های خودِ شومان را نویز می‌شمرد. سیگنالِ واقعی `w_q=0.018` می‌گرفت.
   **اصلاح:** برجستگیِ قله نسبت به کفِ مجاورِ خودش در طیف.
