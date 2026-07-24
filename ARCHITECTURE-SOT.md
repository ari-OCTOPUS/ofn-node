# ARCHITECTURE-SOT — نقشه‌ی منبعِ حقیقتِ اجرایی (Source of Truth)

> Verdict 2026-07-18 integration-debug: این فایل کانونی‌ترین مرجع برای اینکه
> بدانی برای هر کار، کدام فایل/دایرکتوری canonical است.
> هر تغییری در معماری باید این‌جا هم به‌روز شود.

## 🎯 اصلِ بنیادین

پروژه‌ی اختاپوس چند لایه دارد، ولی **فقط `_ops/` ارگانیسمِ زنده‌ی اجرایی است**.
بقیه‌ی لایه‌ها یا dormant هستند، یا visualization، یا independent research.
هر تغییری که قرار است runtime را تحت تأثیر قرار دهد، باید در `_ops/` باشد.

## 📍 Source of Truth بر اساسِ concern

### ۱. ارگانیسمِ زنده (Live Organism)
| concern | canonical | جایگزین/دوم‌دار | وضعیتِ دوم‌دار |
|---------|-----------|-----------------|----------------|
| **main loop** | `_ops/organism.py` (port 8771) | `04 - Architect System/scripts/organism-watchdog.ps1` | DIVERGENT TWIN — split-brain note R-19. آن فقط supervisor است. |
| **state snapshot** | `_ops/state/ORGANISM-STATE.json` | - | تک‌منبع |
| **events log** | `_ops/state/events.jsonl` | - | append-only |

### ۲. مغز (Brain / Cognition)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **controller brain** | `_ops/cortex/cortex.py` (port 8772) | - | LIVE (coherence 0.91) |
| **LLM routing** | `_ops/cortex/model_router.py` | `4d_system/llm/router.py`, `survival-gateway/` | هر دو DORMANT — canonical فقط model_router |
| **local LLM** | `_ops/cortex/local_llm.py` (Ollama) | - | تک‌منبع |
| **doctor self-knowledge** | `_ops/doctor/self_knowledge.py` | `04 - Architect System/learning-engine/app/doctor_lite.py` | دومی standalone، NOT wired |

### ۳. بودجه و متابولیسم (Budget)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **budget definitions** | `_ops/budget/budgets.yaml` | - | تک‌منبع (verdict-خورده) |
| **budget gate** | `_ops/budget/organ_gate.py` | - | تک‌منبع |
| **NBB Control Plane** | - | `app/src/nbb_cp/` | DORMANT — فاز ۴-۵ آینده، هنوز وصل نشده |

### ۴. تلگرام (Telegram)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **private approval channel** | `_ops/budget/approval_channel.py` (bot #1) | - | LIVE |
| **group command centre** | `_ops/telegram_center/center.py` (bot #2) | - | LIVE |
| **creator studio (Saba)** | `03 - Projects/اونلی فنز/studio/saba_studio.py` | - | DORMANT (token ساخته‌نشده) |
| **bot registry** | `_ops/BOTS-REGISTRY.md` | - | مرجع |

### ۵. پاها (Legs / Business)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **wiring hub** | `_ops/wiring.py` (133KB) | - | تک‌منبعِ اتصالِ پاها |
| **legs** | `_ops/legs/*.py` | - | هر پا یک ماژول |
| **Project-F (Saba)** | `03 - Projects/اونلی فنز/` | - | standalone، فاز برنامه‌ریزی |

### ۶. حافظه و داک (Memory / Docs)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **genome ledger** | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | - | append-only hash-chain |
| **memory** | `_memory/` | - | docs |
| **architecture maps** | `06 - Architecture Maps/` | - | docs |

### ۷. Visualization / Dashboards
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **live cockpit UI** | `_ops/live/server.py` (port 8773) | - | LIVE |
| **HTML worlds** | `OCTOPUS/worlds/` | - | static visualization |

## 🚫 دایرکتوری‌های NOT wired (DORMANT)

این‌ها کد دارند ولی در runtime فعال نیستند. هر تغییری در آن‌ها **تأثیری در ارگانیسم زنده ندارد**.

| دایرکتوری | نقشِ اسمی | وضعیتِ واقعی | علامت‌گذاری |
|-----------|-----------|--------------|-------------|
| `_launchpad/second-brain-live/control-brain/` | second brain | DEAD — فقط docs و batch files | DEPRECATED.md |
| `survival-gateway/` | LiteLLM proxy | NOT DEPLOYED — docker-compose موجود ولی راه‌نرفته | DEPRECATED.md |
| `4d_system/` | research brain | INDEPENDENT — standalone experiment، wired نیست | DEPRECATED.md |
| `octopus_core/` | rebuild v2 | PARTIAL — event_bus/actuator موجود ولی consumer ندارد | (توضیح در README) |
| `app/` | NBB Control Plane | DESIGN — 12 invariant، 207 تست، ولی not connected | (توضیح در README) |

## 🔌 سیم‌کشیِ اصلی (Bridge Files)

این فایل‌ها backboneِ اتصالِ اجزاست. همه در `_ops/state/`.

| فایل | نویسنده | خواننده | نقش |
|------|---------|---------|-----|
| `cockpit-requests.jsonl` + `.cursor` + `.lock` | approval_channel | wiring.py:1184 | تلگرام → organism |
| `telegram/center-config.json` | telegram_center | telegram_center, cortex | وضعیتِ گروه |
| `telegram/approvals/*.json` | approval_channel | telegram_center | verdictها |
| `ORGANISM-STATE.json` | organism.py | همه | status snapshot |
| `events.jsonl` | events.py | cortex consumers | event log |
| `saba-bridge.jsonl` | (آینده) saba_brain | (آینده) wiring beat | Saba → organism (scaffold) |

## 📐 قواعدِ تغییر

1. **هر تغییری که قرار است runtime را تحت تأثیر قرار دهد، در `_ops/` باشد.**
2. **هر فایلِ canonical جدید** باید در این فایل ثبت شود.
3. **هر دایرکتوریِ dormant** باید `DEPRECATED.md` داشته باشد که به canonical اشاره کند.
4. **هیچ کدِ تکراری نساز** — اول این فایل را بررسی کن که آیا canonical موجود است.
5. **معماری به‌صورتِ incremental تکامل می‌یابد** — این فایل snapshotِ امروز است.

## 🧬 ثبتِ ۲۰۲۶-۰۷-۲۴ — اندامِ synapse (additive، پیش‌فرضِ خاموش)

| concern | canonical | وضعیت |
|---------|-----------|-------|
| SENSE (SOG روی تله‌متریِ خودِ ارگانیسم) | `_ops/synapse/sense.py` | SHADOW — فلگ `SYNAPSE_ENABLED` خاموش؛ خروجی فقط `_ops/synapse/out/`؛ importِ read-only از `4d_system/core/metrics.py` |
| مانیتورِ trajectory (P3) | `_ops/synapse/trajectory_monitor.py` | SHADOW — فلگ `TRAJECTORY_MONITOR_ENABLED` خاموش؛ wiring به event_bridge = tapِ مالک |
| سیاستِ egress (P1) | `_ops/synapse/egress_policy.py` | policy-as-data — enforce/wiring = tapِ مالک؛ deny-by-default |
| تست‌های synapse | `_ops/tests/test_synapse_sense.py` | [UNKNOWN تا اولین اجرای pytest] |

قاعده: هیچ‌کدام از این‌ها در runtimeِ فعلی اثر ندارند (فلگ‌ها خاموش). هر wiring آینده
در همین فایل ثبت و با verdictِ مالک انجام می‌شود.
