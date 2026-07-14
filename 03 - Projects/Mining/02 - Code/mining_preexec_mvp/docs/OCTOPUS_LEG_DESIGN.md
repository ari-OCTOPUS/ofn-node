# طرح و پلن — پای Mining به‌عنوان زیرمجموعهٔ اختاپوس (دو مغز + تلگرام)

> نسخه: v1.0 · تاریخ: 2026-07-12 · وضعیت: **pre-execution / INFORM-only / propose-only**
> این سند «طرح» است، نه اجازهٔ اجرا. هیچ SSH/deploy/wallet/miner-control فعال نمی‌شود.

---

## 0. یک‌خطی

پای `Mining` یک **limb از ارگانیسم اختاپوس** (`_ops`) است که **دو مغز** دارد —
یکی برای **کنترل سخت‌افزار** (ناوگان Orange Pi + ESP32) و یکی برای **کشف کوین‌های
نوظهور** — و از طریق **مرکز تلگرام اختاپوس** به مالک وصل است. مثل بقیهٔ پاها
(`lead`, `ziman`, `cartographer`) کاملاً **propose-only** و **read-only floor** است.

---

## 1. جایگاه در اکوسیستم (رییس + پاها)

طبق `OCTOPUS-STRUCTURE.md`:

- **رییس = ارگانیسم `_ops`** (organism.py + cortex + heart + budget + …).
- **پاها = دامنه‌های `03 - Projects`** که با `MANIFEST.yaml` + `contracts/adapter.yaml`
  قراردادی‌اند و با `_ops/registry_scan.py` کشف می‌شوند.
- Mining «پای #۳» است (D-26: Accounting → Lead → Mining).

این طرح Mining را از یک «پوشهٔ پروژهٔ کشف‌شده» به یک **پای زندهٔ کد** (limb) در
`_ops/legs/mining_leg.py` ارتقا می‌دهد — دقیقاً هم‌الگو با `ziman_leg.py` و
`cartographer_leg.py`.

```
مالک (تلگرام: کاکپیت + verdict + kill)
        │  (فقط انسان)
   organism.py  ── beat loop ──►  wiring.mining_beat()  ──►  MiningLeg.tick()
        │                                                        │
        │                                          ┌─────────────┴─────────────┐
        │                                          │   دو مغزِ پای Mining        │
        │                                          │                            │
        │                              🛠 HardwareControlBrain   ⛏ CoinDiscoveryBrain
        │                              (ناوگان: سلامت/برق/دما)   (شکار کوین نوظهور)
        │                                          │                            │
        │                                          └──────────► Proposal(propose-only)
        ▼
telegram_center (کلید «mining» ⛏)  ◄── ORGANISM-STATE.json (بلوک mining)
```

---

## 2. دو مغز (طراحی)

### 2.1 🛠 مغز کنترل سخت‌افزار — `HardwareControlBrain`

**نقش:** سیستمِ عصبیِ ناوگان — سلامت، برق، دما، وضعیت نود. **read-only + propose-only.**

- می‌خواند: رجیستری سخت‌افزار، وضعیت نود، منبع/هزینهٔ برق.
- ارزیابی می‌کند: گیت برق (`<$0.05/kWh` یا solar/free)، دما، uptime، status نود.
- **هرگز اجرا نمی‌کند:** SSH (D-20)، deploy (D-20)، start/stop mining، تغییر config ریگ،
  دسترسی wallet (D-11). این‌ها `HARD_GATED` اند → fail-closed.
- خروجی: `fleet_health` report + proposal (draft) برای مالک.

**قاعدهٔ برق (کیل‌سوییچ ساختاری):** اگر هزینهٔ برق نود `>$0.05/kWh` و solar نباشد →
`ELECTRICITY HALT` (🔴). برقِ نامعلوم → 🟡 (نمی‌توان تأیید کرد، fail-closed).

### 2.2 ⛏ مغز کشف کوین — `CoinDiscoveryBrain`

**نقش:** شکار کوین‌های نوظهورِ CPU/ARM-پذیر. **read-only + propose-only.**

- طبقه‌بندی الگوریتم: yespower/verushash/randomx/… = ARM-viable (پس از اندازه‌گیری واقعی)؛
  sha256/kheavyhash/ethash/kawpow/… = GPU/ASIC-dominated → رد برای ناوگان CPU.
- امتیازدهی کاندید: سنِ لانچ (`≤۹۰ روز`)، dev activity، community، داده‌های شبکه.
- Death-watch (**D2 فقط**): `dev_dead ≥ ۸ هفته` یا `chain_stalled` یا `community_dead`.
  **payback/نقدشوندگی هرگز معیار قطع نیست** — فقط فیلد اطلاعاتی.
- **هرگز اجرا نمی‌کند:** buy/sell/withdraw (D-10)، wallet (D-11).
- خروجی: `coin_scout` draft + `death_watch` verdict — همه proposal.

---

## 3. قرارداد پا (Leg contract — ارث از `_ops/legs/leg.py`)

| قید | مقدار برای Mining |
|---|---|
| `leg_id` | `mining-fleet` |
| `organ` | `MINING` (در budgets نیست → `money_link=incubating`) |
| `read_allowlist` | فقط نوت‌های خودِ Mining (بدون wildcard) |
| `tools` | status_snapshot, fleet_health, coin_scout, death_watch, electricity_check |
| `budget_aud` | `0.0` ($0 — برق قید ساختاری، ابزارها رایگان) |
| `spawn` | `0` (INV-17) |
| `secrets` | `()` (همیشه خالی — D-11) |
| خروجی | فقط `Proposal` (propose-only) |
| متدهای send/publish/pay/trade | **وجود ندارند** (ساختاری) |

---

## 4. اتصال به اختاپوس (wiring)

- `wiring.make_mining_leg()` پشتِ فلگِ `OCTOPUS_WIRE_MINING` (پیش‌فرض **خاموش**).
- `wiring.mining_beat(leg, beat)` — STOP/HALT مقدم، status-only، هیچ اثر بیرونی.
- **عمداً خارج از `PAPER_FULL_FLAGS`**: چون Security Gate دامنهٔ Mining بسته است
  (read-only ⛔ تا چرخش ۴ ردیف CRITICAL + wallet seed rotation). فعال‌سازی فقط با
  **verdict صریح مالک** (`OCTOPUS_WIRE_MINING=1`). rollback = حذف همان خط.
- `organism.py`: ساخت leg + صدا زدن beat در حلقه (مثل ziman/cartographer).

---

## 5. اتصال به تلگرام

مرکز تلگرام اختاپوس (`_ops/telegram_center/`) از قبل جای «mining» را دارد:

- `render.LEGS["mining"] = "Mining"` ✓
- `render.LEG_ICONS["mining"] = "⛏"` ✓
- `center.LEG_KEYS` شامل `"mining"` ✓

کاری که این طرح می‌کند: `render._collect_legs` بلوکِ `mining` را از `ORGANISM-STATE.json`
می‌خواند (مثل cartographer) و به دایجستِ ۳خطیِ تلگرام نگاشت می‌کند. مالک هر تصمیم
(allocation/major switch/kill) را با یک‌تاپ آره/نه می‌بیند — ولی **هر اثر مالی/اجرایی
human-gated** است (D-10/D-20).

---

## 6. پلن مرحله‌ای (build order)

| گام | کار | معیار موفقیت | چه چیزی هنوز ساخته نشود |
|---|---|---|---|
| 1 | `mining_leg.py` (دو مغز، propose-only) | تست‌ها سبز؛ import سالم | هیچ SSH/deploy/wallet |
| 2 | `wiring.make_mining_leg` + `mining_beat` (flag-off) | flag off→None؛ flag on→incubating | خارج از PAPER_FULL |
| 3 | `organism.py` beat hook | state شامل بلوک mining | اجرای واقعی ماینر |
| 4 | تلگرام: نگاشت دایجست mining | دایجست ۳خطی در مرکز | نوتیف اجرایی |
| 5 | **verdict مالک** برای فعال‌سازی | `OCTOPUS_WIRE_MINING=1` | تا بسته‌شدن Security Gate |
| 6 | بعد از rotation: رجیستری واقعی + بنچمارک | H/s/W/temp واقعی | خرید/فروش خودکار |

---

## 7. ناوردی‌ها و کیل‌سوییچ

- STOP-ORGANISM / halted → beat فوراً None (کیل مقدم بر همه‌چیز).
- electricity ceiling → HALT ساختاری.
- wallet zero-access (D-11) → `secrets=()` verified در `TaskPacket`.
- D2-only death-watch → payback هرگز نمی‌کشد.
- fail-soft: یک limb هرگز ارگانیسم را نمی‌کشد.
- $0 · stdlib-only · offline · additive (هیچ ماژول موجودی خراب نمی‌شود).

---

## 8. رابطه با `mining_preexec_mvp`

پای `mining_leg.py` = رابطِ نازکِ Octopus-facing (نبض/دایجست/گیت‌ها).
پکیج `mining_preexec_mvp` = رانتایمِ پژوهشیِ عمیق‌تر (schemas، plans، CLI، gates).
پا در bet فقط status می‌دهد؛ کارِ سنگین (readiness/scout report) on-demand به همان
پکیج/subagent واگذار می‌شود — دقیقاً الگوی cartographer (نبض سبک + کار سنگینِ on-demand).
