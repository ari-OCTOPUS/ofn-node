# نقشهٔ اجرایی: شهر محلی OCTOPUS

پاسخ مالک و وضعیت نهایی در [00_OWNER_ANSWER_FA.md](00_OWNER_ANSWER_FA.md) است. این صفحه فقط نقشهٔ لایه‌ها را می‌دهد؛ جزئیات تکرار نشده‌اند.

## بدن فیزیکی

- Orange Pi 5 Pro، `aarch64`، Debian 13 و kernel `6.1.115-vendor-rk35xx`. RAM فیزیکی حدود `4.10 GB` و eMMC ریشه حدود `61.3 GB` است. `[RUNTIME-VERIFIED] /proc/device-tree/model؛ /etc/os-release:1-6؛ uname/free/lsblk snapshot`.
- root برابر `89%` مصرف و `7,026,900,992` بایت آزاد داشت. این مقدار از آستانهٔ یک GiB کد بالاتر است، ولی headroom عملی کم است. `[RUNTIME-VERIFIED] df /؛ /opt/octopus/lab/ofn/organism/homeostasis/core.py:6-9,57-85`.
- مصرف تخصیص‌یافتهٔ `/opt/octopus` حدود `815M` است: models `410M`، lab `311M`، gateway `55M`، runtime `36M`، research-intake `2.4M`، a2-lab `1.6M` و OFN-L4 `72K`. `[RUNTIME-VERIFIED] du snapshot`.
- فشارهای اصلی: ۴ GB RAM، eMMC نسبتاً پر، مدل 410M، llama RSS اوج حدود 845 MiB و نبود GPU سازگار vLLM. `[LOCAL-LIVE] /opt/octopus/lab/evidence/SOAK-RESULTS.json:10-16؛ /opt/octopus/lab/artifacts/vllm-block-size/preflight.json:15-29`.

### استعارهٔ «بدن»

A) **Vibe Coding:** برد بدنهٔ کشتی است؛ RAM غذا، دما تب و eMMC انبار آن است.  
B) **ترجمهٔ مهندسی:** منابع kernel/sysfs و `statvfs` به signalهای اندازه‌گیری‌شده و stateهای سلامت تبدیل می‌شوند.  
C) **محدودیت:** برد بدن زیستی نیست؛ کمبود RAM یا گرما هیچ انگیزه، درد یا حیات ایجاد نمی‌کند. `[LOCAL-CODE] homeostasis/core.py:17-100`.

## چهار ناحیهٔ معماری

1. **L0 continuity — LIVE_WITH_GAP**  
   gateway و heartbeat مشاهده/عرضه می‌کنند؛ mirror فقط pull است و اکنون blocked؛ NATS client-only و disconnected است. این لایه authority برای فرمان‌دادن ندارد. `[LOCAL-CODE] /opt/octopus/gateway/app.py:24-27,96-157؛ /opt/octopus/bin/nats-observe.py:1-4,95-112؛ /opt/octopus/state/{sync.json,nats.json}`.

2. **ارگانیسم مرجع — LIVE_WITH_GAP**  
   `/opt/octopus/lab/ofn/organism` مرجع اجرای امروز است: EventKernel + SQLite + identity + episodic memory + homeostasis + ask/Qwen. gap اصلی، source/runtime drift و نبود enforce صریح برای تعداد memory read است. `[LOCAL-LIVE] service octopus-organism-lab.service؛ /etc/systemd/system/octopus-organism-lab.service:8-23`.

3. **OFN-L4 — SCAFFOLD**  
   قرارداد v2، زمان monotonic، body، homeostat، arbiter، identity، store و Δθ نوشته شده‌اند؛ هیچ daemon یا runtime فعال وجود ندارد. `[LOCAL-SCAFFOLD] /opt/octopus/ofn-l4؛ listener 8091 absent`.

4. **آزمایشگاه آفلاین vLLM — OFFLINE_TESTED/BLOCKED_NO_GPU**  
   hash/APC، cache salt، metrics parser، block estimator، W1–W5، result store و Pareto محلی‌اند؛ GPU benchmark، winner و deployment وجود ندارند. `[LOCAL-OFFLINE-LAB] /opt/octopus/lab/ofn/{adapters,benchmarks}؛ /opt/octopus/lab/artifacts/vllm-block-size`.

## سه codebase که نباید یکی فرض شوند

- **زنده و authoritative:** `/opt/octopus/lab/ofn/organism`، نسخهٔ دیسکی `0.6.0`، service فعال. `[LOCAL-LIVE] /opt/octopus/lab/ofn/organism/__init__.py:1-2`.
- **آینده و disconnected:** `/opt/octopus/ofn-l4`، نسخهٔ `0.1.0-preflight`، `ALIVE_CLAIM=False` و `CONSCIOUS_CLAIM=False`. `[LOCAL-SCAFFOLD] /opt/octopus/ofn-l4/ofnl4/__init__.py:1-13`.
- **پژوهش قرنطینه‌ای:** `/opt/octopus/research-intake/lab/proto-organism`، سند 22/22 تست آفلاین؛ authority و اتصال runtime ندارد. `[LOCAL-OFFLINE-LAB] /opt/octopus/research-intake/lab/proto-organism/README.md:1-8,32`.

## مسیر حقیقت و اختیار

```text
سنسورهای local + LAN allowlist
            |
            v
homeostasis / afferent
            |
            v
EventKernel --commit--> SQLite events + outbox
            |                    |
            |                    +--> episodic memory
            +--> identity ledger
            |
            v
public state / vault / ask cascade / optional Qwen

OFN-L4 -------- disconnected scaffold
vLLM/GPU ------ offline design; external execution only
```

منبع حقیقت پایدار ارگانیسم، SQLite و hash-chain است؛ Qwen منبع هویت نیست. autonomy در تمام مسیر `PROPOSE_ONLY` می‌ماند و مدرسه/رشد آن را تغییر نمی‌دهد. `[LOCAL-CODE] runtime/app.py:195-215؛ growth/parent.py:194-204؛ identity/heartbeat.py:14-28`.

## وضعیت سریع

- LIVE: L0 gateway، organism، SQLite، afferent، soak، llama.cpp/Qwen.
- LIVE_WITH_GAP: mirror/backup، mandatory retrieval metric، attestation بدون anchor، source/runtime match.
- IMPLEMENTED_DISCONNECTED: WAN general path، Δθ.
- SCAFFOLD: OFN-L4.
- OFFLINE_TESTED: APC sha256، cache salt، block harness، WBE proto scaling.
- BLOCKED_DEPENDENCY: sha256_cbor و pymdp.
- BLOCKED_NO_GPU: GPU benchmark و vLLM runtime.
- DOCUMENT_ONLY: Hybrid/Mamba cache و Active Inference policy loop.

واژگان رسمی در [17_GLOSSARY_FA.md](17_GLOSSARY_FA.md) و ردیف‌های دقیق در [13_LOCAL_PRESENCE_MATRIX.csv](13_LOCAL_PRESENCE_MATRIX.csv) هستند.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
