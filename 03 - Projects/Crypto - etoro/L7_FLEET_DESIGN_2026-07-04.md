---
type: design
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
tags: [crypto, L7, fleet, mining, mqtt, skeleton-code]
version: 1.0
created: 2026-07-04
updated: 2026-07-04
parent: "[[03 - Projects/Crypto - etoro/CRYPTO_ARCHITECTURE_v1_2026-07-04]]"
---

# 🛰️ L7 — MINING / COMPUTE FLEET: طراحی تفصیلی + اصلاح‌ها

> عمیق‌سازیِ L7 روی کدِ واقعیِ `Ai bots/fleet/` (manager، worker_agent، watchdog، hashrate_oracle، models) + firmware ESP32. قانون: **کد واقعی > سند**.

---

## 1. Quick Summary

L7 = ناوگانِ سخت‌افزاری که mining را اجرا و hashrate را به L3 (edge ENERGY) پل می‌زند. کد **ساخته و منسجم** است (REST + heartbeat + watchdog + oracle)، ولی سه شکافِ واقعی دارد: **(الف)** شمارِ worker در کد ۹ است ولی inventory ۱۶ → hashrate همه‌جا کم‌شماری می‌شود؛ **(ب)** ناوگان به **kill-switch احترام نمی‌گذارد** (نقضِ D-06)؛ **(ج)** مغز (OPi5+) **SPOF** است و ESP32ها (۱۰ در کد / ۱۴۰ در انبار) عملاً استفاده نشده‌اند.

**حکم:** با یک kill-switch hook + تصحیحِ شمار + پلنِ ESP32، L7 امن و کامل می‌شود. deploy فقط بعد از باز شدنِ گیت.

---

## 2. ناوگانِ واقعی امروز (از کد)

| جزء | فایل | نقش | نکته |
|---|---|---|---|
| **Fleet Manager** | `fleet/manager.py` | Flask REST `:7700` روی OPi5+ | `/target /report /register /fleet /set_target /clear_target /ping` · بدونِ auth (LAN-only) · `fleet_state.json` می‌نویسد |
| **Worker Agent** | `fleet/worker_agent.py` | هر OPi5 Pro | poll `/target` هر ۳۰s → XMRig(randomx) / cpuminer(بقیه) → report temp/load/hashrate |
| **Watchdog** | `fleet/watchdog.py` | RPi3B | ping هر ۶۰s؛ ۳ fail → alert تلگرام + SSH-restart (پیش‌فرض **off**، D-20) |
| **Hashrate Oracle** | `fleet/hashrate_oracle.py` | پل به L3 | `fleet_state.json` → `fleet_config.json`؛ منبع MEASURED/ESTIMATED/MISSING → EdgeClassifier |
| **Sensors** | `deploy/esp32/firmware.py` | ESP32 (MicroPython) | WiFi → register SENSOR → heartbeat ۶۰s (+DS18B20 اختیاری) |
| **Models** | `fleet/models.py` | dataclasses مشترک | ARM_HASHRATE_HS per-algo · `WORKER_COUNT=9` ⚠️ · `is_alive<120s` |
| **systemd** | `deploy/systemd/*` | همیشه‌روشن + timerها | manager/worker/watchdog always-on · QA+Coordinator هر ۶h |

---

## 3. توپولوژی و جریان

**LAN 192.168.1.0/24:** OPi5+ (`.100`، brain+manager) · ۱۶× OPi5 Pro (`.101–.116`، workers) · RPi3B (`.110→ .117`، watchdog) · ESP32×۱۴۰ (`.120+`، sensors) · ۲× FPGA (USB/UART).

**Control flow:** Coordinator → `POST /set_target` → Manager → workerها `GET /target` (۳۰s) → miner start/stop → `POST /report` → `fleet_state.json` → Oracle → `fleet_config.json` → **EdgeClassifier ENERGY (L3)**.
**Health:** worker heartbeat → Manager؛ Manager ping → Watchdog → Telegram (اگر مغز down).

---

## 4. شکاف‌ها (از کد)

| # | شکاف | شاهد | اثر |
|---|---|---|---|
| G-L7-1 | **`WORKER_COUNT=9`** ولی inventory ۱۶ | `models.py:34` | `fleet_hashrate_for_algo`=۹×… → کم‌شماری در Oracle و ENERGY edge |
| G-L7-2 | **بدونِ kill-switch** | fleet هیچ‌جا `halted`/`STOP` را چک نمی‌کند | نقضِ D-06؛ `/halt` جلوی mining را نمی‌گیرد |
| G-L7-3 | **SPOF مغز** | یک OPi5+؛ watchdog فقط alert/SSH (off) | down شدنِ مغز = توقفِ کل بدونِ failover |
| G-L7-4 | **ESP32 ۱۰ vs ۱۴۰** | firmware `s01..s10` | ۱۳۰ برد بلااستفاده؛ فرصتِ mesh + DePIN |
| G-L7-5 | **`:7700` بدونِ auth** | manager.py (عمداً LAN-only) | اگر LAN نشت کند، هر کس target ست می‌کند |
| G-L7-6 | **wallet روی worker** | `WALLET_ADDR` env | ⚠️ فقط آدرسِ **دریافت** (public) مجاز است؛ کلیدِ خرج off-box (P10) |

---

## 5. طراحیِ هدف + اصلاح‌ها (اسکلت)

### 5.1 — kill-switch hook (G-L7-2، مهم‌ترین)

worker و manager باید قبل از هر اکشن `halted`/`STOP` را چک کنند. اسکلت برای `worker_agent.py` (ابتدای حلقه):

```python
from pathlib import Path
STOP_FILE = Path(os.getenv("STOP_FILE", "/opt/ai-bots/STOP"))

def _halted() -> bool:
    # فایلِ STOP = mirror؛ در deploy واقعی، flag `halted` در DB هم چک شود
    return STOP_FILE.exists()

# داخل main() loop، قبل از _fetch_target():
    if _halted():
        if _miner_proc and _miner_proc.poll() is None:
            log.warning("KILL-SWITCH active → stopping miner"); _stop_miner()
        _send_report(0.0); time.sleep(POLL_INTERVAL); continue
```
و در `manager.py` → `/target` وقتی `_halted()` است `null` برگرداند (fail-closed). این D-06 را در L7 عملی می‌کند.

### 5.2 — تصحیحِ شمار (G-L7-1) → به Patch 2 در `L3_patches/APPLY_L3_PATCHES.md` ارجاع
`WORKER_COUNT=16` + `FLEET_HASHRATE_HS=20400`. یک منبعِ واحد: `models.py` را canonical کن و `edges.yaml` از آن مشتق شود (حذفِ duplication).

### 5.3 — پلنِ ۱۴۰ ESP32 (G-L7-4)
- **~۲۰ SENSOR** (نزدیک هر worker + محیط): temp/heartbeat فعلی.
- **~۱۲۰ ESP32-C3** → **DePIN beacon** (GEODNET/ONOCOY، طبقِ «Pure Qolk»): accumulation، zero withdrawal. مصرفِ <۵W هرکدام روی solar.
- Firmware نقش‌محور: `ROLE=SENSOR|DEPIN` در config.

### 5.4 — failover مغز (G-L7-3)
Watchdog (RPi3B) از «alert-only» به **promote**: اگر مغز >N دقیقه down، یک OPi5 Proِ standby را با `fleet-manager.service` بالا بیاور (state از `current_target.json`ِ replicate‌شده). SSH-restart طبقِ D-20 **HITL** بماند.

### 5.5 — امنیتِ `:7700` (G-L7-5)
bind فقط به LAN IP (نه `0.0.0.0`) + `ufw` allow از subnet + توکنِ اشتراکی در header برای `/set_target`/`/clear_target`. هرگز internet-exposed.

---

## 6. Governance alignment

- **Kill-switch (D-06):** §5.1 اجباری قبل از deploy.
- **SSH (D-20):** auto-restart/promote → HITL، نه خودکارِ بی‌گیت.
- **Keys (P10/D-11):** آدرسِ دریافت روی worker OK؛ seed/کلیدِ خرج **off-box**.
- **Mining = INFORM only (D-10):** ناوگان فقط سیگنال/اجرای mining می‌دهد؛ **هیچ اجرای مالی** (فروش/سواپ) — آن مسیرِ انسانی است.
- **Budget:** توانِ solar + سایشِ سخت‌افزار زیرِ سقفِ Mining (charter §Budget).

---

## 7. Trade-offs (score 1–10؛ بالاتر=بهتر)

| تصمیم | Cost | Complexity | Scalability | Security | Time | حکم |
|---|---|---|---|---|---|---|
| kill-switch hook | 10 | 9 | — | 10 | 9 | ✅ اجباری، کم‌کد، حاکمیتی |
| WORKER_COUNT single-source | 9 | 8 | 7 | 7 | 8 | ✅ رفعِ کم‌شماری |
| ۱۲۰ ESP32 → DePIN | 7 | 5 | 8 | 7 | 4 | ✅ accumulation؛ ولی کارِ firmware |
| standby-brain failover | 6 | 4 | 6 | 7 | 3 | ⚠️ ارزش بالا، پیچیده → فازِ بعد |
| توکن روی `:7700` | 9 | 8 | — | 9 | 8 | ✅ دفاعِ ارزان |

---

## 8. Next steps (بعد از باز شدنِ گیت)

1. **kill-switch hook** (§5.1) را به worker + manager اضافه کن — پیش‌نیازِ هر deploy.
2. **WORKER_COUNT=16** (تک‌منبع در `models.py`) + `edges.yaml` مشتق.
3. **firmware نقش‌محور** برای ESP32 (SENSOR vs DEPIN) — شروع با ۱۰ SENSOR فعلی، بعد C3 beaconها.

> ⚠️ همه paper/design تا §Security Gate باز نشده؛ deploy = rotation + TOP-5 audit + Phase-4 prompt + verdict (قاعدهٔ registry).

---

## Sources (vault، read-only)

`fleet/manager.py` · `fleet/worker_agent.py` · `fleet/watchdog.py` · `fleet/hashrate_oracle.py` · `fleet/models.py` · `deploy/esp32/firmware.py` · `deploy/systemd/*` · `ARCHITECT_CHARTER` (D-06/10/20، P10) · `CRYPTO_ARCHITECTURE_v1` · `L3_patches/APPLY_L3_PATCHES.md`.

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]
