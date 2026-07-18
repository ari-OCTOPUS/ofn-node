# 🐙 اختاپوس — نقشهٔ اتصال در یک نگاه
**تاریخ:** 2026-07-18 · **حالت:** read-only scan · **نسخهٔ کامل:** `OCTOPUS-DEEP-CONNECTIVITY-AUDIT-2026-07-18.md`

---

## ✅ وصل و واقعی (مغز زنده است)

| جزء | دلیلِ اطمینان |
|---|---|
| **Auth / RBAC** | `center.py:487` — غیرمالک سکوت مطلق، fail-closed |
| **Intent classifier** | rule-based، در production (نه فقط تست) — `center.py:557` |
| **Action Graph** | ۱۷ ActionSpec با risk/approval/rollback، تست‌شده |
| **Approval Queue** | lifecycle کامل، dual-persistence (octopus + legacy)، atomic write |
| **code_autonomy** | git worktree ایزوله واقعی، deny-list + allow-list، auto-rollback |
| **Worktree isolation** | enforced (نه convention)، REAL_VAULT env، cleanup در finally |
| **Capability gate** | fingerprint-checked، triple-AND، فعلاً عمداً بسته |
| **Telemetry** | AU$0.03/mo vs AU$30 cap، ۵ مصرف‌کنندهٔ زنده |
| **Model routing (LLM)** | سه‌لایه (local→GLM→Fugu)، در مسیر تصمیم واقعی (cortex/doctor/improve) |
| **Redaction (INV-12)** | در همهٔ خروجی‌های telegram/log/mission اعمال می‌شود |
| **Governance** | HANDOFF.md (۳۵KB)، CLAUDE.md، _PROJECT_INSTRUCTIONS.md — همگی به‌روز |
| **Self-knowledge / heartbeat** | doctor_self-knowledge در حال اجرا، beat در حال پیشرفت |

---

## 🟡 نیمه‌وصل (قطعات هست، حلقه کامل نیست)

| جزء | چه چیز گم است |
|---|---|
| **Telegram Center** | کد کامل ولی `_octopus/logs/telegram.log` خالی — فعلاً poll نمی‌کند |
| **Mission Genome** | data-model کامل ولی ۴ state پایانی (`applied/monitored/done/reverted`) فقط enum |
| **Fitness score** | از heuristic (claim‌های ثبت‌شده) نه از outcome واقعی |
| **Doctor RFC loop** | RFC در `submitted` گیر می‌کند (`sandbox_result: null`) |
| **Calibration / Spectral / Temperature** | مکانیزم هست ولی در tick صدا زده نمی‌شوند |
| **Evolution** | propose-only، sandbox، `$0` — وصل به tick نه |
| **Accounting** | txn-store محلی (۵۷۶ txn) ولی فاقد bank feed و organ-attribution بیرونی |
| **Crypto leg** | فقط گزارش freshness از دادهٔ stale محلی |

---

## 🔴 قطع یا نمایشی (فقط ظاهر اتصال)

| جزء | واقعیت |
|---|---|
| **Mission production persistence** | `_ops/state/telegram/missions/` **وجود ندارد** — هیچ missionی در production نرسیده |
| **`ms:test` / `ms:review` callbacks** | فقط `add_note` + `set_state(planned)` — اجرا نمی‌کنند (صادقانه در docstring اعتراف شده) |
| **`actions.py` skeleton** | هیچ‌کس import نمی‌کند — render.py مستقیماً callback‌ها را hardcode می‌کند |
| **`/lead` command** | در business-brain به آن اشاره شده ولی در `center.py:503-510` handler نیست |
| **Lead inbox** | `_ops/state/legs/lead-inbox/` وجود ندارد |
| **Ziman catalog** | `ziman-catalog.json` وجود ندارد |
| **Chamber (adversarial debate)** | stub کامل، بدون LLM call، هرگز صدا زده نمی‌شود |
| **Observability CLIs** | health/budget/flag/leg monitors فقط دستی، در runtime صدا زده نمی‌شوند |
| **Tracer decorator** | هیچ caller در production ندارد |
| **Harvest / Email / PocketSmith** | همه flag-off (DORMANT) |

---

## ⚫ خطرناک — فعلاً نباید وصل شود

| موضوع | چرا |
|---|---|
| **`LIVE-ENABLED.flag`** | غایب — یعنی capability gate همیشه closed (paper mode). به‌عمد. قبل از تأیید owner و تست repairها، **MAKE Nکن**. |
| **`money_locked: true`** | در `octopus_state.json` — پول عمداً قفل است. باز کردنش owner decision است. |
| **Auto-launch TG center** | rule: شروع server/bot ممنون. فقط owner `RUN-TG-CENTER.bat` را اجرا کند. |
| **Auto-sandbox RFCها** | risk متوسط — sandbox اجرای کد است. به تأیید owner. |
| **دو source of truth برای approval** | octopus `approvals.json` + legacy `approvals/*.json` — قبل از unify، drift ممکن است. |

---

## 💰 گلوگاه مسیر پول

**اولین گرهٔ شکسته: ثبت lead.**

```
market signal → [❌ lead-inbox مفقود] → product → pricing → outreach → customer → payment → accounting → survival
                       ↑
                 اینجا می‌میرد
```

- **هیچ lead واقعی** در سیستم ثبت نشده (`lead-inbox/` وجود ندارد).
- **هیچ محصولی** در کاتالوگ نیست (`ziman-catalog.json` وجود ندارد).
- **هیچ E3+ evidence‌ای** در کل `_ops/state/` یافت نشد.
- **`business-brain-latest.json` خودش می‌گوید:** «هنوز درآمدِ تأییدشده‌ای ثبت نشده».

**کوچک‌ترین repair:** اضافه‌کردن `/lead <text>` handler به `center.py` + persist به `lead-inbox/<id>.json`. ~۳۰ خط.

---

## 🧠 گلوگاه مغز و حافظه

**Mission Runner وجود ندارد.**

```
intent → mission create → approval → [❌ runner مفقود] → artifact → evidence → learning
                                          ↑
                                    اینجا حلقه می‌شکند
```

- پرامپت CODEX-1 آماده در `00 - Inbox/2026-07-18 Prompt-CODEX-1 - Mission Runner v0 (isolated executor).md`.
- پنج organ همزمان با ساختنش زنده می‌شوند: Mission، Action Graph، Approval، code_autonomy، Doctor.
- فقط ۵ اکشن allowlist، همگی read یا low-risk، در worktree ایزوله.
- Risk بسیار پایین؛ قبل از `LIVE-ENABLED.flag` هم قابل ساختن/تست.

---

## 👤 تنها تصمیم‌های لازم از مالک (۷ تا، به ترتیب اولویت)

1. **ساختن `mission_runner.py`؟** (CODEX-1 آماده است) → پیشنهاد: **بله** با همان scope.
2. **اضافه‌کردن `/lead` + ثبت اولین lead واقعی؟** → پیشنهاد: **بله**.
3. **اجرای Telegram Center (`RUN-TG-CENTER.bat`)؟** → پیشنهاد: **بله**.
4. **auto-sandbox کردن RFCها در doctor tick؟** → پیشنهاد: **بله** (read-only sandbox).
5. **`LIVE-ENABLED.flag`؟** → پیشنهاد: **صبر کن** تا #۱ و #۲ تست شوند.
6. **genome-system: ادغام یا بایگانی؟** → پیشنهاد: **همان‌طور که هست** (ledger-only).
7. **`_memory/`: ماشین یا انسان؟** → پیشنهاد: **انسانی (مستندات)**.

---

## ➡️ قدم بعدی واحد

> **تأیید پرامپت CODEX-1 و ساختن `mission_runner.py`.**
>
> ۵ اکشن، worktree ایزوله، artifact در `_agent_reports/missions/<mid>/run-<ts>/`.
> Risk پایین، اثر بالا، پیش‌نیازِ ۴disconnect دیگر.

---

*این گزارش نتیجهٔ ممیزی read-only است. هیچ فایلی تغییر نیافت، هیچ تستی اجرا نشد، هیچ commit/branch‌ای دستکاری نشد، هیچ سروری فعال نشد.*
