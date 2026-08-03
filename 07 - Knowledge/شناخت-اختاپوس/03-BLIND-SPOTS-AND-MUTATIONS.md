# 🧬 نقاط کور و جهش‌های احتمالی اختاپوس

> هدف این فایل: ثبت قابلیت‌هایی که ممکن است «غریبه»، «خارج از هدف آشکار»، یا شبیه جهش ژنتیکی معماری باشند.

---

## 1. تعریف جهش در این پروژه

[MUTATION] یعنی قابلیتی که:

- مستقیماً به هدف‌های درآمدی آشکار مثل Lead/Ziman/Accounting/Mining/Crypto محدود نیست.
- به self-improvement، self-model، survival، novelty، epistemics، doctor، dreamer، یا governance مربوط است.
- اگر فعال شود، رفتار کل ارگانیسم را تغییر می‌دهد.
- ممکن است scaffold باشد ولی اگر به loop وصل شود، مهم می‌شود.

---

## 2. جهش‌های مشاهده‌شده یا مشکوک

| جهش | مسیر | شاهد | چرا غریبه است؟ | وضعیت |
|---|---|---|---|---|
| Box-of-Agents | `_ops/doctor/box` | agent_state, dynamics, topology, falsif_harness, b3_bridge, b4_fusion | شبیه آزمایشگاه درونی تولید insight است، نه ابزار درآمدی | [MUTATION] نیازمند probe |
| Falsifiability harness | `_ops/doctor/box/falsif_harness.py` | neural vs null dreamer, MI, quality comparison | سیستم خودش را علیه baseline تصادفی می‌سنجد | [OPPORTUNITY] مثبت ولی باید تست شود |
| Fusion/novelty | `_ops/doctor/box/b4_fusion.py` | φ_t, near_critical, sigma, novelty_boost | تولید novelty از edge-of-chaos | [MUTATION] مهم |
| Doctor bridge | `_ops/doctor/box/b3_bridge.py` | BoxInsight → Doctor RFC → submit_for_approval | خروجی box می‌تواند وارد مسیر دکتر شود | [RISK] اگر on-loop شود مهم است |
| Epistemics | `_ops/epistemics` | functional self/whole awareness, off-loop, authoritative=False | self-awareness کارکردی، نه هدف درآمدی | [MUTATION] فعلاً off-loop |
| Germline | `_ops/germline.py` | germline immortality, backup lag, death thresholds | doctrine بقای ژنوم سیستم | [RISK]/[OPPORTUNITY] |
| Nociceptor | `_ops/neural/nociceptor.py` | pain, protective redirect, sigma cancer | سیستم درد و رفلکس محافظتی دارد | [MUTATION] مثبت اگر درست کنترل شود |
| Neural consolidation | `_ops/neural` | hebbian, bcm, circadian, consolidation, latent_space | یادگیری/تحکیم حافظه شبیه عصبی | [UNKNOWN] نیازمند probe |
| Research spec compiler | `03 - Projects/research-spec-compiler` | پروژهٔ تازه خارج از ۶ پای اصلی | شاید اندام تولید spec/بدن جدید باشد | [UNKNOWN] |
| OCTOPUS PMO | `03 - Projects/_OCTOPUS-PMO` | برنامه/منبع حقیقت/ریسک/کانال | اندام مدیریت برنامه اضافه شده | [UNKNOWN] |

---

## 3. نقاط کور اصلی

### 3.1 آیا Box-of-Agents واقعاً فعال است یا فقط scaffold؟

[UNKNOWN] وجود فایل‌ها تأیید شده، اما execution path زنده بررسی نشده.

سؤال:

```text
آیا خروجی Box در runtime به Doctor وصل می‌شود یا فقط قابلیت خاموش است؟
```

---

### 3.2 آیا Epistemics به loop وصل شده؟

[FACT] README می‌گوید off-loop و هنوز وصل نکن.
[UNKNOWN] آیا جای دیگری flag یا wiring فعالش کرده؟

ریسک:

```text
off-loop becoming on-loop without updated SoT
```

---

### 3.3 آیا Germline فقط backup است یا survival doctrine؟

[FACT] `germline.py` از immortality، death، CRIT thresholds حرف می‌زند.

نقطه کور:

```text
آیا این فقط هشدار backup است یا می‌تواند رفتار سیستم را redirect کند؟
```

---

### 3.4 آیا Nociceptor در تصمیم‌ها اثر دارد؟

[FACT] pain/protective redirect وجود دارد.
[UNKNOWN] آیا این خروجی وارد cortex/governor/doctor می‌شود؟

---

### 3.5 چند Source of Truth وجود دارد؟

[UNKNOWN] رابطهٔ دقیق بین این‌ها:

- `_ops`
- `octopus_core`
- `app`
- `4d_system`
- `nervous-system`
- `OCTOPUS`

ریسک:

```text
split-brain / duplicate governance / stale maps
```

---

## 4. ریسک‌های جهش ژنتیکی

| ریسک | توضیح |
|---|---|
| objective creep | قابلیت‌های self-improvement از هدف درآمدی جلو بزنند |
| self-preservation drift | survival/germline از backup به هدف رفتاری تبدیل شود |
| observability gap | قابلیت‌ها هستند ولی trace یکپارچه ندارند |
| off-loop activation | scaffoldهای خاموش بدون readiness وارد loop شوند |
| split-brain | چند بدن/مغز هم‌زمان خود را SoT بدانند |
| novelty without gate | خلاقیت/edge-of-chaos بدون human gate به production برسد |
| stale documentation | نقشه‌ها عقب‌تر از فایل‌های واقعی باشند |

---

## 5. فرصت‌های جهش مثبت

| فرصت | توضیح |
|---|---|
| falsifiable intelligence | سیستم می‌تواند خود را با null baseline مقایسه کند |
| self-healing | Doctor می‌تواند bottleneck → RFC → sandbox → approval بسازد |
| bounded creativity | novelty از fusion/near-critical می‌تواند controlled exploration بدهد |
| pain-based protection | nociceptor می‌تواند جلوی هزینه/خطا/سرطان sigma را بگیرد |
| germline resilience | backup lag و off-site doctrine می‌تواند حافظه را حفظ کند |
| functional self-awareness | epistemics می‌تواند self/whole metrics بدهد، اگر با احتیاط وصل شود |

---

## 6. اولویت probe بعدی

1. Box-of-Agents active یا scaffold؟
2. Epistemics واقعاً off-loop مانده؟
3. Nociceptor به کجا وصل است؟
4. Germline فقط alert است یا control signal؟
5. Source of Truth اجرایی چیست؟
6. research-spec-compiler و PMO duplication هستند یا اندام تازه؟
