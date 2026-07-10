# مگاپرامپت ساخت — Octopus Telegram Cockpit v2

> **برای ایجنتِ کدنویس:** این سند خودبسنده است. همه‌چیز را از همین‌جا بساز. کد واقعی را ملاک بگیر (`file:function`)، هرگز قابلیت اختراع نکن. زبانِ روایت فارسی، زبانِ کد/مسیر/نام‌تابع/دستور تلگرام انگلیسی.
> **هسته‌ی کار:** فایلِ موجود `_ops/budget/approval_channel.py` را **گسترش بده، بازنویسی نکن، نشکن**. cockpit یک لایه‌ی **VIEW + routing** روی همین کانال است. تنها مسیرِ settle پول (`approve → _on_human_judgment → EffectorGate.settle`) دست‌نخورده می‌ماند و هرگز از نو پیاده نمی‌شود.
> **گروندینگِ حیاتی (خواندنی قبل از هر تصمیم معماری):** UX زنده‌ی امروز، scheme سومی به‌نامِ `menu:<page>` دارد که در `dispatch_callback` مسیریابی می‌شود (`_dispatch_menu`)، یک `MENU_KEYBOARD` سطحِ کلاس، `_menu_queue`، و `_main_menu` که **همین حالا** `reply_markup=MENU_KEYBOARD` برمی‌گرداند. پس **scheme موازیِ جدید (`nav:`) نساز**؛ همین `menu:` را **گسترش بده**. صفحاتِ موجود: `status/lead/queue/lab/stop/stop_confirm/main`.

---

## ۰. پیش‌نیازِ خواندن (قبل از هر خط کد)

۱. `F:\backup\_ops\budget\approval_channel.py` را کامل بخوان — به‌ویژه: `handle_command`, `dispatch_callback` (**امضایِ واقعی: `def dispatch_callback(self, data: str)`؛ `poll_once` آن را با `self.dispatch_callback(str(text))` صدا می‌زند**), `_dispatch_menu`, `MENU_KEYBOARD`, `_menu_queue`, `_main_menu` (**همین الان `reply_markup=MENU_KEYBOARD` دارد**), `poll_once`, `_read_mode_color`, `status_report_v2`, `request_approval_card`, `_do_approve`, `rfc_card`, `_dispatch_rfc`, `pop_rfc_verdicts`, `_new_token`, `_cteq`, `_count_pending`, `_pending`, `_pending_rfc`, `kill_switch`.
۲. `_ops/wiring.py` — `wire_summary`, `make_telegram_channel`, `enrich_state_with_germline`, `resolve_profile`, `append_outbox`, `make_scheduler`.
۳. `_ops/export_status.py` — `build_bundle`, `main`, `_chrono_summary`, `_genome_ledger_summary`, **`_SECRET_PATTERNS`** (اسکنِ خروجی).
۴. `_ops/dashboard/server.py` — `_write_env` (نوشتنِ `_ops/OCTOPUS-flags.cmd`), `_do_restart` (نوشتنِ `STOP-ORGANISM` + `RESTART-REQUESTED`), `page_capabilities`, `page_channels`.
۵. `_ops/brain/cockpit.py:BrainCockpit` — `legs_status`, `approval_queue_html`, `organism_status`, `money_shadow`, `alarms`.
۶. `_ops/afferent/sensory_bus.py:_contains_pii` و `_ops/live_loop.py:verify_no_pii_in_signals` (ردلاینِ PII و Project-F).
۷. یک تستِ نمونه از `_ops/tests/` بخوان تا سبکِ `harness.run` و httpِ تزریقی را بفهمی.
۸. **هیچ‌جا `import organism` نکن.** read-modelها فقط `_ops/state/*.json` (و `chrono.db` mode=ro) را می‌خوانند (استقلالِ crash — مثل `panel/server.py` و `dashboard/server.py`).

---

## ۱. مأموریت + Invariantهای امنیتیِ غیرقابل‌مذاکره

### مأموریت
یک «کابینِ بازرسی» تلگرامی بساز که **هر قابلیتِ واقعیِ ارگانیسم** را در قالبِ ۸ تبِ طراحیِ مالک (`Octopus.pptx`) سطح‌بندی کند: خواندن (status) آزاد، و هر کنترل از پشتِ کارتِ تأییدِ human-gated. cockpit فقط **می‌بیند** و **مسیر می‌دهد**؛ هرگز خودش اثر نمی‌گذارد.

### Invariantها (طراحی باید همه را حفظ کند — نقضِ هرکدام = رد)

| # | Invariant | اجرا در کد |
|---|---|---|
| **INV-1** | **Read آزاد؛ هر WRITE/پول/برگشت‌ناپذیر = human-append از کارتِ تأیید (توکنِ ضدجعل) → gate.settle.** مسیرِ settleِ پول دیگری وجود ندارد و ساخته نمی‌شود. | `_do_approve → _on_human_judgment → _settle_effect → gate.settle` |
| **INV-2** | **Gate chain:** `organ_gate → money_gate → capability_gate → live_gate`. **LIVE GATE تا 2026-07-21 قفل** (صفر اکشنِ پولی قبل از آن). | `capability_gate.py:require`, `opslib.py:live_gate_open` |
| **INV-3** | **σ anti-cancer سقفِ سختِ تکثیر = 1.0.** cockpit فقط نمایش می‌دهد. | `replication.py:sigma_state` |
| **INV-4** | `STOP-ORGANISM` / `FREEZE` / `halt` کلیدهای مطلقِ خاموشی‌اند. **فایل authoritative است؛ bot فقط trigger.** مسیرِ `menu:stop → menu:stop_confirm → kill_switch` هم دست‌نخورده می‌ماند. | `kill_switch`, `EffectorGate.force_closed`, `_dispatch_menu` |
| **INV-5** | **توکنِ ربات SECRET است:** فقط env (`TELEGRAM_BOT_TOKEN`)، هرگز در prompt/log/commit؛ URLِ حاویِ توکن هرگز log نمی‌شود. | `.wired`, `poll_once` |
| **INV-6** | **Propose-only در همه‌جا.** bot فقط flowِ human-gated را trigger می‌کند، هرگز auto-act نمی‌کند. | همه‌ی `kind:control` |
| **INV-7** | **read-model هرگز `organism.py` import نمی‌کند و هیچ subsystem cycle را inline در poll process اجرا نمی‌کند.** فقط `_ops/state/*.json` + `chrono.db` (mode=ro، uri، timeout=1). | helperهای جدید |
| **INV-8** | **owner-allowlist:** فقط `TELEGRAM_OWNER_CHAT_ID` فرمان می‌دهد؛ بقیه skip (offset پیش می‌رود). | `poll_once` |
| **INV-9** | **fail-soft:** خطای یک handler هرگز poll loop را نمی‌کشد → `opslib.alert`، ادامه. | `poll_once` try/except |
| **INV-10** | **stdlib-only** (`urllib`), **RTL Persian HTML**, quarantine (هر inbound = DATA نه command؛ هر `<verb>`/`<key>`/`<page>` در callback_data هم DATA است و باید علیه allowlist اعتبارسنجی شود). | `poll_once`, `send_text` |
| **INV-11** | **secret-guard:** cockpit هیچ فایلِ secret/OWNER-PROFILE/.env/wallet/seed را نمی‌خواند و echo نمی‌کند. | §۱.۱ + `export_status.py:main` |
| **INV-12** | **redactionِ خروجی:** *هر* متنِ رندرشده (کارت‌ها، mirrorهای خام state/alerts/log) قبل از ارسال از یک پاسِ redaction عبور می‌کند؛ اگر الگوی secret/PII match شد، بدنه‌ی کارت با «⚠️ محتوا به‌دلیلِ الگوی حساس حذف شد» جایگزین می‌شود. | `send_text` / هر render helper |
| **INV-13** | **کنترلِ `act:` تک‌مصرف و ضدجعل است:** هر دکمه‌ی `act:` توکن را در یک رجیستریِ اختصاصیِ `_pending_act` (زیرِ lock) mint می‌کند؛ dispatch آن را با `_cteq` علیه نسخه‌ی **ذخیره‌شده** می‌سنجد، در نبود/انقضا/غیرpending رد می‌کند، و **قبل از اجرا** با flipِ status مصرف می‌کند (anti-replay). | §۲.۳ + `_pending_act` |

> **قاعده‌ی طلایی برچسب‌گذاری:** هر قابلیت را دقیقاً یکی از این سه برچسب بگیرد و روی کارت نشان بده:
> - 🟢 **read-now** — همین حالا زنده و خواندنی.
> - 🟡 **needs-flag** — کد هست ولی `OCTOPUS_WIRE_*` خاموش؛ cockpit فقط وضعیتِ «OFF» + آخرین دیتای موجود را نشان می‌دهد، هرگز flag را مستقیم روشن نمی‌کند مگر از مسیرِ کنترل‌شده‌ی `act:flag:<name>:<token>` → `_write_env` (human-append + capability_gate؛ اثر در boot بعدی).
> - 🔴 **needs-live-gate** — تا 2026-07-21 و بازشدنِ gate صفر است؛ کارت «🔒 قفل» می‌شود.

### ۱.۱ حلِ صریحِ تعارضِ OWNER-PROFILE (رفعِ ابهام)
کاتالوگ `panel/server.py:_load_profile` («/me» tone/autonomy/risk) را به‌عنوان محرکِ رفتار bot فهرست می‌کند، ولی INV-11 خواندنِ `OWNER-PROFILE` توسطِ cockpit را ممنوع می‌کند. **تصمیمِ قطعی:** cockpit **هرگز `OWNER-PROFILE` را مستقیم نمی‌خواند**. هیچ کارتی پروفایلِ مالک را surface نمی‌کند. اگر بعداً نمایِ curated (فقط `tone/autonomy/risk`، هرگز PII/آدرس/شخصی) لازم شد، باید از یک فایلِ مشتق‌شده‌ی غیرsecret (`state/*.json`) بیاید که سمتِ organism نوشته می‌شود، نه از `OWNER-PROFILE`. این‌جا مبهم گذاشته نمی‌شود: **پیش‌فرض = exclude کامل.**

---

## ۲. معماریِ منو — گسترشِ `menu:` (نه scheme موازی)

### ۲.۱ سه schemeِ موجود که دست‌نخورده می‌مانند
`dispatch_callback` امروز **دقیقاً سه scheme** را می‌شناسد (نه دو):
- `menu:<page>` — ناوبریِ زنده (`_dispatch_menu`)؛ صفحاتِ موجود: `status/lead/queue/lab/stop/stop_confirm/main`. `MENU_KEYBOARD` سطحِ کلاس و `_main_menu` (که `reply_markup=MENU_KEYBOARD` دارد) بخشی از همین‌اند.
- `app:<verb>:<effect_id>:<token>` (پول، T-2) — دقیقاً ۴ بخشِ colon.
- `rfc:<verb>:<rfc_id>:<token>` (تکامل، W-3).

**cockpit این scheme را می‌سازد/گسترش می‌دهد — بدون scheme موازی:**

| scheme | وضعیت | معنا | نمونه |
|---|---|---|---|
| `menu:<page>` | **موجود — گسترش** | ۸ تبِ جدید به‌عنوان صفحاتِ menu اضافه می‌شود | `menu:overview`, `menu:main`, `menu:safety`, `menu:queue` |
| `card:<tab>:<key>` | **جدید** | رندرِ یک detail-card خواندنی | `card:money:organs`, `card:doctor:box` |
| `pg:<tab>:<key>:<n>` | **جدید** | صفحه‌بندیِ لیست بلند | `pg:alerts:rules:2` |
| `act:<verb>:<key>:<token>` | **جدید** | trigger یک flowِ human-gated (کارتِ `app:`/`rfc:` می‌سازد یا فایلِ کنترل می‌نویسد) | `act:export:raw:<token>`, `act:flag:reconcile:<token>` |

`menu:`/`card:`/`pg:` هیچ توکن نمی‌خواهند (read-safe، فقط render). `act:` **حتماً** token را با `_cteq` علیه رجیستریِ `_pending_act` می‌سنجد (INV-13).

### ۲.۲ اسکلتِ درستِ `dispatch_callback` (امضایِ واقعی — کپیِ کورکورانه ممنوع)
> `dispatch_callback` یک **رشته** می‌گیرد، یک‌بار split می‌کند، و به sub-dispatcherها یک **لیستِ pre-split (`parts`)** می‌دهد — نه dict. قراردادِ صدا زدن با `poll_once` تغییر نمی‌کند.

```python
def dispatch_callback(self, data):          # data: str  (poll_once → self.dispatch_callback(str(text)))
    parts = str(data or "").split(":")
    head = parts[0] if parts else ""
    # --- EXISTING (unchanged) ---
    if head == "menu": return self._dispatch_menu(parts)   # extended below with 8 tab pages
    if head == "rfc":  return self._dispatch_rfc(parts)
    if head == "app":  return self._dispatch_app(parts)     # money settle, exactly 4 colon parts
    # --- NEW cockpit read/nav layer ---
    if head == "card": return self._dispatch_card(parts)
    if head == "pg":   return self._dispatch_page(parts)
    if head == "act":  return self._dispatch_act(parts)     # INV-13 token verify → app:/rfc: or control-file
    return  # unknown scheme → «نادیده» (allowlist reject)
```

> **قاعده‌ی افزودن:** شاخه‌های `menu`/`rfc`/`app`ِ موجود دقیقاً همان‌جا و همان‌گونه می‌مانند؛ فقط شاخه‌های `card`/`pg`/`act` کنارشان اضافه می‌شوند و `_dispatch_menu` با ۸ صفحه‌ی تب گسترش می‌یابد. `menu:stop`/`menu:stop_confirm` (killِ زنده) دست نمی‌خورد.

### ۲.۳ رجیستریِ `_pending_act` (seamِ جدید — بازاستفاده نیست)
`_new_token(self, effect_id, amount_aud)` **money-keyed** است (amount می‌خواهد، `self._pending[effect_id]['_n']` را می‌خواند). برای کنترل‌های غیرپولی/غیرrfc، **هیچ رجیستری/مدلِ توکنی وجود ندارد** — این seam را بساز:

- یک dict سطحِ نمونه: `self._pending_act = {}` (زیرِ همان lockِ موجود).
- یک minter بدونِ amount: `_new_act_token(self, action_id)` که یک nonce می‌سازد و `{token, verb, key, status:'pending', expires_at}` را زیرِ lock ذخیره می‌کند و token را برمی‌گرداند. **هر رندرِ دکمه‌ی `act:` باید این را صدا بزند** و token را در callback_data بگذارد.
- verifier در `_dispatch_act(parts)`:
  1. `verb, key, token = parts[1], parts[2], parts[3]`.
  2. **allowlist:** `verb`/`key` را علیه enum بسته اعتبارسنجی کن (§۲.۴)؛ ناشناخته → «نادیده».
  3. `entry = self._pending_act.get(action_id)`؛ اگر نبود/`expires_at` گذشته/`status != 'pending'` → رد.
  4. `_cteq(token, entry['token'])` علیه نسخه‌ی **ذخیره‌شده**؛ عدمِ تطابق → رد.
  5. `entry['status'] = 'consumed'` (**قبل از هر اثر** — تک‌مصرف/anti-replay).
  6. `_killed()`/STOP را چک کن؛ اگر killed → فقط پیغام، اجرا نکن.
  7. سپس effect را اجرا کن.
- **کنترل‌های پول/rfc از `_pending_act` استفاده نمی‌کنند:** verdictِ فاز و هر write حاکمیتی باید از رجیستریِ موجودِ `rfc_card`/`_pending_rfc` بروند؛ settleِ پول فقط `_do_approve → gate.settle`. کنترل‌های غیرپولی/غیرrfc پس از verifyِ توکن **مستقیم** اجرا می‌شوند (نه از راهِ `request_approval_card`).

### ۲.۴ allowlistِ بسته‌ی `act` (ضدquarantine — INV-10)
`_dispatch_act` قبل از هر کاری `verb` و `key` را علیه این enum بسته چک می‌کند؛ هر چیزِ خارج از آن → «نادیده». هرگز `key`ِ رسیده از callback را مستقیم به `remove()`/`ingest()`/مسیرِ فایل نده.

```
verbs  = {export, flag, restart, stop, freeze, sweep, doctor, consolidate, ideas,
          latent, school, ingest, lead, idea, cardiac, lab, reveal, phase, baseline, metric}
keys per verb = یک set صریح (مثلاً flag∈{reconcile,barbell,fitness,epistemics,cardiac,selfheal,
          chamber_t,scheduler,...}؛ ingest∈{crypto,acct}؛ lead∈{claim,conflict}؛ latent∈{forget}؛
          restart∈{organism, <leg-id از فهرستِ ثابت>}؛ lab∈{start1,start2,start3})
```

### ۲.۵ گیتِ سختِ live برای `act`های پول‌خور (fail-closed در لایه‌ی cockpit)
برای هر verbِ پول‌خور، برچسبِ 🔴 **کافی نیست**. `_dispatch_act` باید **پیش از اجرا** `opslib.live_gate_open(activation_flag)` و `capability_gate.is_open(...)` را چک کند؛ اگر CLOSED (که تا 2026-07-21 هست) → **refuse در همان لایه** («🔒 قفلِ live-gate تا 2026-07-21»)، نه واگذاری به ماژولِ پایین‌دست. `reconcile.run` و `governor_epoch.run_epoch` **دکمه‌ی مستقیمِ bot نیستند** (settle-driver پول‌اند)؛ فقط read باقی می‌مانند و هر فعال‌سازی باید از کارتِ تأییدِ پول + گیتِ سخت برود.

### ۲.۶ قاعده‌ی اجرای inline (استقلالِ crash + liveness — INV-7)
فقط **read-model + نوشتنِ فایل‌های کنترلِ امن** ممکن است inline در poll process اجرا شوند: `STOP` (`kill_switch`), `FREEZE` (`opslib.freeze`), `sweep_stale_effects`, `export` (`export_status.main`), `flag-write` (`_write_env`), `restart` (`_do_restart`). **هیچ subsystem cycleِ mutating/طولانی inline اجرا نمی‌شود** (`doctor.run_cycle`, `governor_epoch.run_epoch`, `wiring.consolidation_beat/idea_beat`, `school_bridge.learn_from`, `ingest_raw.run`): این‌ها یا باید bounded/near-instant باشند یا out-of-band dispatch شوند (نوشتنِ یک request-flag که organism مصرف می‌کند). هر act handler `_killed()`/STOP را **قبل و بعد** چک می‌کند. در سند مشخص کن کدام ماژول‌های import‌شده تأییداً هیچ import سطحِ بالای organism ندارند؛ اگر ماژولی چنین وابستگی داشت، آن act را out-of-band کن.

### ۲.۷ درختِ منو (آینه‌ی ۸ تب + queue)

```
/start  → _main_menu (mode-color header + 📥 صفِ تأیید: N) + [8 tab buttons] + [🔄 menu:main]
│
├─ 1 menu:overview  📊 نمای کلی
├─ 2 menu:blueprint 🧭 بلوپرینت P0–P6
├─ 3 menu:brain     🧠 حافظه و مغز
├─ 4 menu:doctor    🩺 دکتر و تکامل
├─ 5 menu:money     💰 پول و متابولیسم
├─ 6 menu:school    🎓 مدرسه
├─ 7 menu:safety    🛡️ ایمنی
├─ 8 menu:alerts    🚨 هشدارها و خام
└─   menu:queue     📥 صف تأیید (موجود — گسترش‌یافته)

هر تب: کارتِ خلاصه + ردیفی از دکمه‌های card:<tab>:<key> + [⬅️ بازگشت menu:main]
هر لیستِ بلند: دکمه‌های [◀️ pg:...:n-1] [n/N] [pg:...:n+1 ▶️]
```

### ۲.۸ جدولِ کاملِ command / button

**Commandهای موجود (حفظِ کامل — بخش ۸):**

| Command | تابع | وضعیت |
|---|---|---|
| `/start` | `handle_command → _main_menu` | حفظ + گسترشِ MENU_KEYBOARD |
| `/status` | `status_report_v2` | حفظِ کامل |
| `/lead` , `/lead <name>\|<aud>\|<cell>` | `_cmd_lead_prompt` / `_cmd_lead_parse` | حفظِ کامل |
| `/stop` , `menu:stop/stop_confirm` | `kill_switch` | حفظِ کامل |

**Commandهای جدید (میان‌بُر — هرکدام معادلِ یک `menu:`):**

| Command | معادل | تب |
|---|---|---|
| `/overview` | `menu:overview` | 1 |
| `/blueprint` | `menu:blueprint` | 2 |
| `/brain` | `menu:brain` | 3 |
| `/doctor` | `menu:doctor` | 4 |
| `/money` | `menu:money` | 5 |
| `/school` | `menu:school` | 6 |
| `/safety` | `menu:safety` | 7 |
| `/alerts` | `menu:alerts` | 8 |
| `/queue` | `menu:queue` | صف |
| `/reentry` | `reentry_packet` (resurface) | 7 |

همه در `_set_my_commands` ثبت شوند (توکن هرگز log نشود).

---

## ۳. تب‌به‌تب — دکمه، تابعِ واقعی، محتوای کارت، مسیرِ گیت، برچسب

> نمادگذاری: **[R]** read · **[C]** control (human-gated). هر ردیف: `دکمه → file:function → کارت نشان می‌دهد → گیت/برچسب`.
> **قاعده‌ی منبعِ read:** کارت‌های read منبعِ خود را روی **`state/*.json` یا `chrono.db`** بگذارند، نه توابعِ compute/beat. جایی که کاتالوگ نامِ تابعِ compute می‌دهد، دیتاسورس را در ستونِ «تابع» به json مربوط ترجمه کن.

### تب ۱ — Overview (نمای کلی) · `menu:overview`

سربرگ = `_read_mode_color` + بَجِ `📥 صفِ تأیید: N` از `_count_pending`.

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| کارتِ اصلی | read-model روی `state/ORGANISM-STATE.json` | halted/frozen/stop، ماه AUD / امروز USD، suspect_zero_total، conflicts×N، epoch pressure + next_epoch_minutes، protective_skip، **⏳ فرسایش متابولیک (metabolic_age)**، **🧬 age_tick (فلاشِ بعدی در N ضربان)** | 🟢 [R] |
| mode-color | `approval_channel.py:_read_mode_color` | 🟢/🟡/🔴 + mode_focus | 🟢 [R] |
| σ ضدسرطان | `state/replication-latest.json` (منبعِ `sigma_state`) | σ_effective، zone (healthy/cancer-axis/pre-replication)، proposed/approved | 🟢 [R] |
| `card:overview:vitals` | `approval_channel.py:status_report` (resurface T-5) | suspect_zero_total، halted، frozen ❄️، ts آخرین tick | 🟡 [R] resurface |
| ♥️ ضربان | `state/ORGANISM-STATE.json` + `chrono.db` (mode=ro) — نه `rhythm_beat` | mode_color، T_beat، hrv، tau، beat_seq، HLC، legs alive/suspected/failed، metabolic_age، effects_pending | 🟢 [R] |
| ساعت زیستی | `wiring.py:circadian_readiness` (خواندنی از state) | phase، readiness، is_maintenance، best_platform | 🟢 [R] |
| **۶ پا (mirror)** | `_ops/brain/cockpit.py:BrainCockpit.legs_status` | ۶ legِ رسمی با icon/color/desc — **project-f صریحاً یکی از ۶ نام‌برده شود** | 🟡 [R] mirror |
| پروژه‌ها (mirror) | `_ops/panel/server.py:_scan_projects` | active count، open_actions، focus | 🟢 [R] |
| `card:queue:pending` (بَج + کارت) | `_count_pending` + `BrainCockpit.approval_queue_html`، status از `chrono.py:EffectorGate.status_of` | لیستِ کارت‌های پولِ pending: project·action·amount·guard، **هرگز self-approved**؛ هر ردیف [✅][❌][⏳] → کارتِ `app:` موجود | 🟢 [R] + مسیر به [C] |

### تب ۲ — Blueprint P0–P6 · `menu:blueprint`

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| فازها 7/7 | `state/phase-gate-state.json` (منبعِ `get_phase_state`) | current_phase، transitions، verdicts (7/7)، awaiting_human_verdict | 🟢 [R] |
| baseline list | `_ops/baseline.py:get_all_baselines` (از state) | P0..P6 با phase_id/label/ts | 🟢 [R] |
| `card:blueprint:diff` | `_ops/baseline.py:compare_baseline` | passed، diffs، verdict، money_changed | 🟢 [R] |
| readiness | `phase_gate.py:pre_phase_check` (read) | blockers، warnings، per-check | 🟢 [R] |
| pre-registered metrics | `_ops/baseline.py:check_pre_registered` (R13) | metric/threshold/actual/passed | 🟢 [R] |
| **transition gate** | `phase_gate.py:transition_gate` (read) | allowed?، post/pre، handoff، awaiting-verdict | 🟢 [R] |
| held-out | `held_out_evaluator.py:evaluate_held_out` (از state) | suite N/5، chain، seals، anti_hacking_flag | 🟢 [R] |
| P3 BCM | `state/bcm-weights.json` | bcm_saturation، θ، pruned | 🟢 [R] |
| P4 sparse | `state/sparse-predictor.json` | sparsity_ratio، filtered/novel | 🟢 [R] |
| P5 chamber-T | `state/chamber-temperature.json` / `wire_summary`(`wire_chamber_t`) | **«RED / OFF»** T، explore، merge_rate، stagnation | 🔴 [R] R20 (owner-explicit only) |
| P6 Fisher | `state/fisher-latest.json` **اگر نوشته می‌شود؛ وگرنه «not-wired — needs persist»** | fisher_condition_number، advisory_weights، `authoritative:false` | 🟡 [R] |
| spectral | `state` (منبعِ `spectral_mine`/`publish_tick_signals`) | σ، spectral_gap، eigvals | 🟢 [R] |
| `card:blueprint:review` → verdict | `rfc_card`/`_pending_rfc` → `review_bus.py:mark_human_verdict` | لیست reviews + [approve/reject/needs-revision] | 🟡 [C] human-append (**از راهِ رجیستریِ rfc، نه act**) |
| `act:baseline:capture:<token>` | `_ops/baseline.py:capture_baseline` | گرفتنِ baselineِ فاز | 🟡 [C] human-append |
| `act:metric:prereg:<token>` | `_ops/baseline.py:pre_register_metric` | ثبتِ معیارِ فاز | 🟡 [C] human-append |
| `act:phase:transition:<token>` | `phase_gate.py:transition_gate` (recordِ X→Y) | ثبتِ گذارِ فاز | 🟡 [C] human-append |

> **verdictِ فاز (governance):** چون money-capability را گیت می‌کند، **forgeable نباشد** — از رجیستریِ `rfc_card`/`_pending_rfc` برود، **نه** از `act:`. `act:phaseverdict` حذف شد.

### تب ۳ — Memory & Brain · `menu:brain`

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| consolidation | tail `neural/consolidation.json` | cycle #، last-cycle age (R18)، ۳ insight آخر | 🟢 [R] |
| verify gate | `neural/consolidation.json` (منبعِ `_verify_source`) | verified/discarded sources | 🟢 [R] |
| latent R^32 | `state/latent-vectors.json` | count، keys_by_layer، dim=32 | 🟢 [R] |
| nearest | `state/latent-vectors.json` (منبعِ `nearest`) | neighbor keys + scores | 🟢 [R] |
| BCM saturation | `state/bcm-weights.json` (R19) | saturation vs 1.0، θ_mean، pruned | 🟢 [R] |
| sparse | `state/sparse-predictor.json` (+`heavy_tail_share`) | sparsity_ratio، heavy-tail share | 🟢 [R] |
| Hebbian | `neural/hebbian.json` | top fire-together pairs + strength | 🟢 [R] |
| neural snapshot | `state` (منبعِ `SignalHub.latest_dict`) | beat، pain_level، sections | 🟢 [R] |
| pain | `state` (منبعِ `Nociceptor.measure`) | pain_level، contributors، protective_mode | 🟢 [R] |
| idea-graph | `state/idea-graph-latest.json` | nodes/edges/broken/clusters/bridges، **broken_targets** | 🟢 [R] |
| hubs/clusters/bridges | `state/idea-graph-latest.json` | لیست‌ها | 🟢 [R] |
| **proposed edges** | `idea_graph.py:proposed_edges` (از state) | یال‌های پیشنهادی + `broken_targets` | 🟢 [R] |
| **اسپرینت (stub)** | `neural/sprint.py:SprintRunner` | «ساخته‌شده ولی هرگز tick نشده — inactive/stub» | 🟡 [R] stub |
| replay state | `_ops/checkpoint.py:replay_state_at` (read) | last_event، replay_seconds، within_5s | 🟢 [R] |
| `act:idea:accept:<token>` | `idea_graph.py:proposed_edges` → پذیرشِ یال (human-append vault edit؛ owner wikilink اضافه می‌کند) | یالِ پذیرفته‌شده | 🟡 [C] human-append vault |
| `act:consolidate:run:<token>` | out-of-band request-flag → `wiring.py:consolidation_beat` | → کارتِ تأیید (capability_gate + $0) | 🟡 [C] needs-flag |
| `act:ideas:rebuild:<token>` | out-of-band request-flag → `wiring.py:idea_beat` | rebuild read-only، STOP-honored | 🟢 [C] |
| `act:latent:forget:<token>` | `SharedLatentSpace.remove` (**key فقط از allowlist، نه از callback خام**) | index-only forget، history حفظ | 🟡 [C] irreversible-index |

### تب ۴ — Doctor & Evolution · `menu:doctor`

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| doctor cycle | `state` (خروجیِ اخیرِ `run_cycle`) | bottleneck، rfc_id، status، beat، evolution/box | 🟢 [R] |
| bottleneck | `state` (منبعِ `Doctor.mine`) | key، severity، score، lambda_persist | 🟢 [R] |
| trace | `state` (منبعِ `_gather_trace`) | organs، conflicts، sigma، effects_pending، frozen/halted | 🟢 [R] |
| RFC verdicts queue | `pop_rfc_verdicts` + `_chrono_summary` rfc_verdicts_tail | verdicts awaiting doctor، total | 🟢 [R] |
| **RFC detail** (`card:doctor:rfc`) | `state` + `doctor.py:run_sandbox` (sandbox/critic) | rfc body + **sandbox/critic: exit، verdict، concerns** | 🟢 [R] |
| **swept/resubmitted** | `doctor.py:_sweep_stale_rfcs` (از state) | swept، resubmitted counts | 🟢 [R] |
| chamber | `state` (منبعِ `run_chamber`) | confidence، rounds، temperature | 🟢 [R] |
| archive (MAP-Elites) | `evolution.py:RFCArchive` (از state) | size/cells، best-in-cell | 🟢 [R] |
| **`card:doctor:evolution`** | `run_cycle` result['evolution'] (از state) — `evolution.measured_lift`/`tournament_rank`/`doctor._evolve_rfc` | archive size، candidates، **winner_lift اندازه‌گیری‌شده، dropped?**، tournament survivor rfc_id | 🟡 [R] propose-only behind-flag |
| attention budget | `state` (منبعِ `attention_gate`) | pending، caps 3/5، allow | 🟢 [R] |
| suppressed | `state` (منبعِ `should_skip_bottleneck`) | bottleneckهای ≥3× رد | 🟢 [R] |
| **BOX cluster** (`card:doctor:box`) | `state/doctor_box.json` (**نیازمندِ persist**، §۶.۴) | stepped، tick، phi_t، submitted_count، falsif_majority، warden 2%، budget_used | 🟡 [R] needs-persist |
| ↳ box_memory | `archivist.coarse_grain` (از `doctor_box.json`) | size/cap، within_boundary | 🟡 [R] |
| ↳ box_topology | `topology.build_topology` (از `doctor_box.json`) | edge_count، is_full_mesh?=no | 🟡 [R] |
| ↳ box_agents | `agent_state.AgentState` (از `doctor_box.json`) | per-agent role/lifecycle/stress/safety_score | 🟡 [R] |
| ↳ mood/stability | `dynamics.global_mood` (G_t) + `sensors.rho_jacobian` (ρ(J)) | خطوطِ صریحِ G_t و ρ(J) | 🟡 [R] |
| box fusion φ_t | `state/doctor_box.json` (منبعِ `compute_phi_t`) | σ، spectral_gap، near_critical | 🟡 [R] |
| box falsif | `state/doctor_box.json` (منبعِ `run_falsif_suite`) | neural_majority، wins n/3، MI neural vs null | 🟡 [R] |
| box warden | `state/doctor_box.json` (منبعِ `Warden.check_budget`) | 2% cap، STOP-obey، ρ/allostatic، quarantined | 🟡 [R] |
| **scheduler: OFF** | `wiring.py:make_scheduler`/`wire_summary` (F19 SCHEDULER_DISPATCH) | flag state OFF | 🟡 [R] needs-flag |
| **anticipation queue** | `chrono.py:Pacemaker.schedule`/anticipation_queue (از state) | «⏰ صف پیش‌بینی»: pending scheduled tasks + due_beat | 🟡 [R] needs-flag |
| **خوددرمانی: OFF** | `chrono.py:Pacemaker.beat_once` (OCTOPUS_WIRE_SELFHEAL) از state | flag state، recent restart count، circuit-breaker throttle alerts | 🟡 [R] needs-flag |
| **Project-F routing** (`card:doctor:projectf`) | `live_loop.py:process_project_f_draft` (W-1) از state | routed/guards_passed/submitted؛ draftهای high-risk به صفِ تأیید به‌صورتِ **$0 money-locked**؛ **ردلاین `verify_no_pii_in_signals` (containment)** | 🟡 [R] + مسیر به queue |
| epistemics | `state/epi-latest.json` | 5 metric + confidence + «not authoritative» | 🟡 [R] needs-flag |
| debate | `state` (whitelist topics، last verdict) | topics whitelist، OFF | 🔴 [R] needs-live-gate |
| lab list | `approval_channel.py:lab_status` (resurface) | active exp names/end_date | 🟡 [R] resurface |
| `act:doctor:run:<token>` | out-of-band request-flag → `doctor.py:Doctor.run_cycle` | → کارتِ تأیید (propose-only، no money/merge) | 🟢 [C] human-append |
| RFC merge/deny | `rfc_card` → `_dispatch_rfc` (**موجود، دست‌نخورده**) | [merge پشتِ flag/رد] | 🟡 [C] human-append |
| `act:lab:start1..3:<token>` | `approval_channel.py:start_experiment` (resurface) | seal sha256، calendar | 🟡 [C] |
| `/reveal` | `approval_channel.py:reveal_experiment` | prediction پس از end_date | 🟡 [R] |
| `act:restart:<leg>:<token>` | `doctor.py:Doctor.restart_from_known_good` (leg از allowlist) | reset leg to alive | 🟡 [C] needs-flag |

### تب ۵ — Money & Metabolism · `menu:money`

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| مصرف | `state/telemetry-latest.json` | month AUD vs cap، today USD، FX tag، per-organ | 🟢 [R] |
| مشکوکِ صفر | `state/telemetry-latest.json` (R6) | suspect_zero_total | 🟢 [R] |
| سقف‌های مؤثر | `04 - Architect System/scripts/budget_gate.py:_caps` (read) | day/month/disaster AUD + FX + src | 🟢 [R] |
| شمارنده‌ی سراسری | `budget_gate.py` state (read-only) | today USD / month AUD / halted | 🟢 [R] |
| ارگان‌ها | `state` (منبعِ `organ_gate.status` + `organ_table`) (R22) | floor/cap/spent per organ، frozen/halted | 🟢 [R] |
| شبیه‌سازی گیت | `organ_gate.reserve` (dry، read-only preview) | allow/deny + reason برای organ/est فرضی | 🟢 [R] preview |
| فشار متابولیک | `state` (منبعِ `governor_epoch.pressure_state`) | spend_velocity، deadline_proximity، anomaly، pressure | 🟢 [R] |
| اپوک بعدی | `governor_epoch.py:epoch_length_minutes` (read) | next_epoch_minutes | 🟢 [R] |
| تخصیص سایه | `governor_epoch.py:allocate_dry` (read) | per-organ grant، H1 ok | 🟢 [R] |
| **گاورنر LLM: قفل** | `governor_epoch.py:allocate_llm` status (از state) | تخصیصِ خودمتریکِ DeepSeek؛ **«🔒 قفل تا 2026-07-21»**؛ هر فعال‌سازی از کارتِ money-approval (token → settle) — **هیچ triggerِ live قبل از gate** | 🔴 [R] needs-live-gate |
| باربل | `state` (منبعِ `barbell_allocate`) | core/satellite، culled، «OFF» | 🟡 [R] needs-flag |
| فیشر | `state/fisher-latest.json` (اگر نوشته می‌شود) | condition_number، advisory_weights، «OFF» | 🟡 [R] |
| fitness سلول‌ها | `state` (منبعِ `fitness.compute` + `_tamper_check`) (R10) | acceptance/efficiency/waste، authoritative flag (shadow 28d)، integrity_alerts | 🟡 [R] |
| **fitness: shadow (OFF)** | `wiring.py:append_outbox`/`wire_summary` (WIRE_FITNESS، R10) | EXPERIENCE outboxِ measure-only — «shadow (OFF)» | 🟡 [R] needs-flag |
| **crypto brief** | `_ops/afferent/ingest_raw.py:summarize_crypto_file` (از state/note) | daily market brief: signal counts، top symbols | 🟢 [R] |
| درآمد محقق (CONFIRMED) | `state` (منبعِ `attribution.confirmed_revenue`) | by_cell AUD، coverage %، claimed vs confirmed — **CONFIRMED فقط reconcile-actor، read** | 🟢 [R] |
| وضعیت لید (fold) | `state` (منبعِ `attribution.fold`) | latest state per attribution_id | 🟢 [R] |
| reconcile status | `state` (منبعِ `reconcile.run`) (R11) | «OFF» + last report وقتی روشن | 🟡 [R] needs-flag |
| leg HLC | `state` (منبعِ `leg.status` + `money_link`) | leg_id، hlc، money_link active/incubating، proposals | 🟢 [R] |
| cardiac | `state` (منبعِ `effective_period`/`bio_rhythm`/`BeatBudget.status`) | period_s، pace، budget، «OFF» (WIRE_BIO) | 🟡 [R] needs-flag |
| money-gate آستانه | `money_gate.py:check` (read) | human_gate_aud (AU$20)، allow/deny نمونه | 🟢 [R] |
| settle authorized? | `approval_channel.py:approval_for` | per-effect human-approval record | 🟢 [R] |
| کارتِ تأییدِ پول | `request_approval_card → _do_approve` (**موجود**) | [تأیید/رد/بعداً]، guard `organ✅·money🔒·cap✅` | 🔴 [C] needs-live-gate |
| `/lead` intake | `_cmd_lead_prompt`/`_cmd_lead_parse` → `LeadLeg.intake`/`attribution.propose` (**موجود**) | attribution_id (PROPOSAL) | 🟢 [C] human-append |
| **draft quote (preview)** | `lead_leg.py:LeadLeg.draft_quote` (read preview) | پیش‌نمایشِ کوت | 🟢 [R] optional |
| `act:lead:claim:<token>` | `attribution.claim`/`LeadLeg.claim` (owner: ref+amount) | ثبتِ کوت → CLAIMED | 🟢 [C] human-append |
| `act:lead:conflict:<token>` | `attribution.conflict` | علامتِ تعارض (human dispute) | 🟢 [C] human-append |

> **صریح:** `organ_gate.settle`/`budget_gate.settle`/`attribution.confirm`/`reconcile.run`/`governor_epoch.run_epoch` هرگز دکمه‌ی مستقیمِ bot نیستند — لایه‌ی حسابداری/reconcile-actor‌اند. تنها settleِ تلگرامیِ پول = کارتِ تأییدِ موجود. `act:reconcile:run`/`act:epoch:run` **حذف شدند** (رجوع به §۲.۵).

### تب ۶ — School · `menu:school`

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| آگاهی مدرسه | `state/school-awareness.json` (R17) | mean 0..1 + ignited count | 🟢 [R] |
| per-cell | `state/school-awareness.json` (منبعِ `awareness_of`) | awareness یک topic_id | 🟢 [R] |
| همه سلول‌ها | `state/school-awareness.json` (منبعِ `full_awareness_vector`) | heat vector مرتب | 🟢 [R] |
| afferent beat | `state` (منبعِ `afferent_beat`) | school_report، n_observations، alarm | 🟢 [R] |
| afferent ratio | `state` (منبعِ `SensoryBus.status`) | ratio، «dreaming» alarm | 🟡 [R] not-wired (transient؛ §۶.۴) |
| classifier preview | `sensory_bus.classify` (read) | obs→topics mapping | 🟡 [R] stub |
| crypto brief | `ingest_raw.py:summarize_crypto_file` (از state/note) | signal counts، top symbols | 🟢 [R] |
| `act:school:learn:<token>` | out-of-band → `school_bridge.learn_from` | ignited topics + proposed edges، $0 | 🟢 [C] human-append |
| `act:ingest:crypto\|acct:<token>` | out-of-band → `ingest_raw.run` (**key فقط از allowlist**) | summary notes، ratio before/after | 🟡 [C] human-append |

### تب ۷ — Safety · `menu:safety`

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| kill vitals | `chrono.py:EffectorGate.force_closed` (از state) | halted/STOP/FREEZE reason | 🟢 [R] |
| σ gauge | `state/replication-latest.json` (منبعِ `sigma_state`) | sigma/zone | 🟢 [R] |
| germline | `state` (منبعِ `germline.lag_alarm`/`enrich_state_with_germline`) (R8) | lag_h، severity، last hourly/bundle | 🟢 [R] |
| live-gate دوقفله | `opslib.py:live_gate_open` (read) | 🔒 قفل تا 2026-07-21 + هر flag | 🔴 [R] |
| capability/live gate | `capability_gate.py:is_open` (R5/R24) | capability_ok، LIVE_ENABLED، closed-reason | 🔴 [R] |
| **قابلیت‌ها/flagها (mirror)** | `dashboard/server.py:page_capabilities` (از `OCTOPUS-flags.cmd`/state) | ۱۹ flag + cadenceها، وضعیتِ هرکدام | 🟢 [R] mirror |
| protective halt | `state` (منبعِ `protective_override`/`protective_skip`) | mode، reason، suppressible | 🟢 [R] |
| money-code integrity | `_ops/baseline.py:_fingerprint_money_sources` (read) | 24-char fingerprint، changed? | 🟢 [R] |
| **تعارض متابولیک** | `state` (منبعِ `telemetry.py:reconcile`، I3) | conflicts[] (cap breach، divergence %، billed vs telemetry)، frozen/STOP-METABOLIC، **متنِ رفعِ دستی (bot fix را نشان می‌دهد، auto-clear نمی‌کند)** | 🟢 [R] |
| pipe wired | `approval_channel.py:wired` | token+owner present (توکن masked 4 char) | 🟢 [R] |
| profile | `wiring.py:resolve_profile` | profile: paper-full (**نه OWNER-PROFILE**) | 🟢 [R] |
| wiring gates | `wiring.py:wire_summary` (R24) | همه‌ی wire_* + cadence | 🟢 [R] |
| token model | `_new_token`/`_new_act_token`/`_cteq` | توضیحِ ضدجعل + تک‌مصرفیِ `act` (نمایش، نه مقدار) | 🟢 [R] |
| leg isolation | `leg.py:Leg.read_brief` (read) | spawn=0، secrets=0، no wildcard | 🟢 [R] |
| PII guard | `sensory_bus._contains_pii` / `live_loop.verify_no_pii_in_signals` (از state) | N patterns، 0 leaks، bus PII pass | 🟢 [R] |
| **گارد مسیر LLM** | `debate/client.py:DeepSeekClient.__init__` (read status) | host allowed / key present (env-only) / price locked، قاعده‌ی no-fallback | 🔴/🟡 [R] |
| **گارد تزریق مناظره** | `debate/topics.py:wrap` (I10) | topic-as-data hardening (data-not-instruction) | 🟢 [R] |
| **inbound quarantine (bounded)** | `poll_once` (owner inbound = DATA، cap 1000ch) | وضعیتِ quarantine؛ tailِ اختیاری در تبِ Alerts | 🟢 [R] |
| **نرخ تناقض** | `box sensors.contradiction_rate` | «آژیر اگر →۰ (groupthink)» — **not-wired تا اتصال به run_tick** | 🟡 [R] not-wired |
| reflexes | `state` (منبعِ `ReflexArc.evaluate`) | active reflexes + severity | 🟢 [R] |
| replication cap | `state/replication-latest.json` (منبعِ `evaluate`) | max_cells=6، eligible، would_propose، live_gate why | 🔴 [R] needs-live-gate |
| pending effects (R16) | `chrono.py:EffectorGate.status_of` + `reentry_packet` | pending count، frozen gated_effect | 🟢 [R] |
| `/reentry` | `approval_channel.py:reentry_packet` (resurface) | pending cards + frozen effects پس از gap | 🟡 [R] resurface |
| `/stop` / `menu:stop_confirm` | `kill_switch` (**موجود، دست‌نخورده**) | نوشتنِ STOP-ORGANISM | 🟢 [C] absolute |
| `act:freeze:on:<token>` | `opslib.py:freeze` | نوشتنِ FREEZE.flag | 🟡 [C] needs-flag |
| `act:sweep:effects:<token>` | `chrono.py:EffectorGate.sweep_stale_effects` | refuse pending >72h | 🟡 [C] human-append |
| **`act:flag:<name>:<token>`** | `dashboard/server.py:_write_env` → `_ops/OCTOPUS-flags.cmd` (human-append + capability_gate) | نوشتنِ اتمیکِ یک flag (reconcile/barbell/fitness/epistemics/cardiac/selfheal/chamber_t/scheduler/...)؛ **flagهای پرخطر confirm صریح**؛ اثر در boot بعدی | 🟡 [C] controlled flags-write |
| **`act:restart:organism:<token>`** | `dashboard/server.py:_do_restart` → STOP-ORGANISM + RESTART-REQUESTED | «clean exit + reboot ≤5min» — **تنها راهِ اعمالِ تغییرِ flag**؛ جفت با `act:flag` | 🟢 [C] human-append |

### تب ۸ — Alerts & Raw · `menu:alerts`

| دکمه/کارت | تابع/منبع | نشان می‌دهد | برچسب |
|---|---|---|---|
| ۲۴ قاعده R1..R24 | `state/export/octopus-status-bundle.json` (منبعِ `build_bundle`، paginated) | هر قاعده 🟢/🟡/🔴 + مقدار منبع | 🟢 [R] |
| governor alerts 24h (R23) | tail `governor/governor-alerts.md` (**پس از redaction**) | آخرین ۳۰ سطر | 🟢 [R] |
| genome chain (R14) | `export_status.py:_genome_ledger_summary` | records، verify-scars ✅/❌ | 🟢 [R] |
| chrono (R11/R15/R16/R12) | `export_status.py:_chrono_summary` | heartbeats، effects_by_status، verdicts_tail | 🟢 [R] |
| data-freshness (R1) | `state` (منبعِ `doctor.stable_read`) | per-file verdict | 🟢 [R] |
| **structured log tail** | **فایلِ خروجیِ JSONLِ FileEmitter** (tail) — **نه `octo_log` که فقط emitter/write است** (redacted) | gate/approval_state/cost_usd/errors | 🟢 [R] |
| advisory feed | `state` (منبعِ `live_loop.advisory_signals`) | RHYTHM/SPECTRAL/AFFERENT/DOCTOR | 🟢 [R] |
| HRV alarm | `state`/`chrono.db` (منبعِ `Rhythm.hrv_alarm`) | hrv-collapse chip | 🟢 [R] |
| **channels** | `state/channel-status.json` (منبعِ `dashboard/server.py:page_channels`) | per-channel live/mode/required_env | 🟢 [R] |
| raw state (mirror) | read مستقیمِ `state/ORGANISM-STATE.json` (**پس از redaction — INV-12**) | ORGANISM-STATE.json خام | 🟢 [R] |
| inbound quarantine tail | log quarantine (bounded، redacted) | آخرین inboundهای DATA | 🟢 [R] |
| bot loop heartbeat | `approval_channel.py:poll_once` | updates processed، offset | 🟢 [R] |
| ledger replay | `_ops/checkpoint.py:replay` (read) | filtered ledger events | 🟢 [R] |
| `act:export:raw:<token>` | `export_status.py:main` | regenerate bundle (secret-scanned) → OK <KB> یا ABORT(secret) | 🟢 [C] read-only export |

> **BrainCockpit mirrors — بازاستفاده vs تکرار:** `approval_queue_html` (صف، تبِ Overview/queue) و `legs_status` (۶ پا) **بازاستفاده** می‌شوند. `organism_status`/`money_shadow`/`alarms` با کارت‌های خام state/telemetry/alertsِ همین سند هم‌پوشانی دارند — **یکی را انتخاب کن، پیاده‌سازیِ تکراری نساز**؛ در کد مشخص کن کدام mirror معتبر است.

---

## ۴. پوششِ کلِ بدن — چک‌لیستِ «هر subsystem حداقل یک read»

| Cluster | read کجا | control (human-gated) |
|---|---|---|
| Telegram Surface | Overview mode-color/status/queue-badge، Safety pipe/token، Alerts loop/channels | `/lead`, approve card, `/stop`, `act:doctor:run` |
| Overview Vitals · 24 rules · Safety | Overview vitals + age_tick، Alerts R1..R24، Safety gates/flags | `act:export:raw`, `act:freeze:on`, `/stop`, `act:restart:organism`, `act:flag:*` |
| Money & Metabolism | Money tab کامل + governor-LLM + fitness-shadow + crypto-brief | `/lead`, `act:lead:claim/conflict`, پول card |
| Doctor & Evolution + phase-gate | Doctor + Blueprint tabs (evolution sub-report، sandbox/critic، swept) | `act:doctor:run`, RFC merge/deny, `act:restart:<leg>`, review verdict (rfc), `act:phase:transition`, `act:baseline:capture`, `act:metric:prereg` |
| Doctor Box (B0–B4) | Doctor box cards (memory/topology/agents/G_t/ρ(J)، پس از persist) | فقط از راهِ RFC card (b3_bridge) |
| Memory & Brain (neural/idea/sprint) | Brain tab کامل + proposed-edges + sprint stub | `act:consolidate:run`, `act:ideas:rebuild`, `act:latent:forget`, `act:idea:accept` |
| Heart/Legs/Live-Loop/Epistemics/Debate/Project-F | Overview heart، Money legs، Doctor epistemics/debate/projectf/scheduler/selfheal، Alerts advisory | `act:sweep:effects`, `act:cardiac:stimulate`, `/lead` (bus), debate (🔴 gate) |
| School/Afferent + UI mirrors | School tab، mirrorها در Overview/Alerts/Safety-flags | `act:school:learn`, `act:ingest` |

> **cardiac stimulate:** ردیفِ Money «cardiac» read است؛ کنترلِ `act:cardiac:stimulate:<token>` (human-append، needs-flag، WIRE_BIO) به‌طورِ گذرا tempo را nudge می‌کند و factor را روی کارتِ rhythm نشان می‌دهد.
> هر قابلیتِ **not-wired/stub** که هنوز state json ندارد (afferent ratio، box report قبل از persist، sprint، fisher اگر persist نشود، contradiction_rate) روی کارت با «not-wired — منبعِ read موجود نیست» شفاف علامت بخورد، هرگز جعل نشود.

---

## ۵. قراردادهای UX

- **RTL Persian HTML** با همان helperهای `send_text` (parse_mode HTML). هر کارت با `‏` شروع، `<b>` برای تیتر.
- **redactionِ خروجی (INV-12):** `send_text` (یا هر render helper) قبل از ارسال، بدنه را با `export_status._SECRET_PATTERNS` + `sensory_bus._contains_pii`/`live_loop.verify_no_pii_in_signals` اسکن می‌کند؛ match → جایگزینیِ کاملِ بدنه با «⚠️ محتوا به‌دلیلِ الگوی حساس حذف شد». مخصوصاً tailهای خامِ state/log/alerts/quarantine.
- **خط‌جداکننده:** `\n➖➖➖➖➖\n` بین بخش‌ها (هم‌سبکِ `status_report_v2`).
- **mode-color header** بالای هر کارت: `_read_mode_color()` → `🟢/🟡/🔴 · <focus>`؛ روی `/start` و Overview بَجِ `📥 صفِ تأیید: N`.
- **آیکن‌ها:** 📊 وضعیت، 💰 پول، σ، ❄️ frozen، 🛑 stop، 🎓 school، 🩺 doctor، 🧠 brain، 🛡️ safety، 🚨 alerts، ♥️ heart، ⏰ anticipation، 🧬 age_tick، 🔒 gate-locked، ✅/❌/⏳ کارت.
- **برچسبِ سه‌حالته** روی هر قابلیت: `🟢 زنده` / `🟡 پشتِ flag (OFF)` / `🔴 قفلِ live-gate`.
- **دکمه‌ی `act:` هنگامِ رندر token را در `_pending_act` mint می‌کند** (`_new_act_token(action_id)`)؛ توکن فقط داخلِ callback_data، هرگز در متنِ نمایشی.
- **صفحه‌بندی:** لیست‌های بلند (۲۴ قاعده، organs، ledger tail، latent keys، flags) با `pg:<tab>:<key>:<n>`؛ هر صفحه ≤ ~۸ آیتم؛ نوارِ `[◀️] n/N [▶️]`.
- **دکمه‌ی back:** هر کارت `[⬅️ بازگشت]` → `menu:<parent>`؛ منوهای تب → `menu:main`.
- **fail-soft render:** هر helper اگر فایل نبود/خراب بود، خطِ «—» یا «داده در دسترس نیست» بدهد، هرگز exception به loop نرساند.
- **هرگز توکنِ ربات یا secret روی کارت نیاید.**

---

## ۶. نقشه‌ی پیاده‌سازی

### ۶.۱ گسترشِ `approval_channel.py` (هسته)
1. **`MENU_KEYBOARD` / `_main_menu`**: `MENU_KEYBOARD` را با ۸ دکمه‌ی `menu:<tab>` + `[🔄 menu:main]` گسترش بده. `_main_menu` **همین حالا** `reply_markup=MENU_KEYBOARD` دارد — همان keyboard را غنی کن، «markupِ نبوده» اضافه نکن. بَجِ `📥 صفِ تأیید: N` از `_count_pending` در سربرگ.
2. **`_dispatch_menu`**: ۸ صفحه‌ی تب (`overview…alerts`) + غنی‌سازیِ `queue` را اضافه کن؛ صفحاتِ موجود (`status/lead/queue/lab/stop/stop_confirm/main`) دست‌نخورده.
3. **`handle_command`**: commandهای جدید (`/overview`…`/alerts`, `/queue`, `/reentry`) را به همان رندرِ `menu:<tab>` route کن. commandهای موجود دست‌نخورده.
4. **`dispatch_callback`**: طبقِ اسکلتِ §۲.۲ — امضایِ رشته‌ای حفظ، `parts` لیست، شاخه‌های `card`/`pg`/`act` کنارِ `menu`/`rfc`/`app`. متدهای جدید: `_dispatch_card`, `_dispatch_page`, `_dispatch_act`.
5. **رندرها**: برای هر تب یک `_render_<tab>()` که از read-model helperها می‌خواند و HTML+keyboard می‌سازد.
6. **`act:` control**: `_dispatch_act` طبقِ §۲.۳–۲.۶ (رجیستریِ `_pending_act`، allowlist، live-gate fail-closed، inline-only، `_killed()` قبل/بعد). سپس یا (a) کارتِ `app:`/`rfc:` می‌سازد، یا (b) فایلِ کنترل می‌نویسد از راهِ توابعِ موجود (`kill_switch`, `opslib.freeze`, `export_status.main`, `_write_env`, `_do_restart`, `sweep_stale_effects`). **هیچ settleِ مستقیم؛ هیچ subsystem cycleِ inline.**
7. **`_new_act_token`/`_pending_act`**: seamِ جدیدِ §۲.۳ را بساز (money/rfc از رجیستریِ خودشان).
8. **`_set_my_commands`**: منوی جدید را ثبت کن (توکن log نشود).

### ۶.۲ read-model helperهای جدید (stdlib-only، بدون `import organism`، بدون compute)
یک ماژولِ جدید: **`_ops/budget/cockpit_readmodel.py`** (تزریق‌شونده به کانال). فقط `json`, `os`, `pathlib`, `sqlite3`. توابع (هرکدام fail-soft → `{}`/`None`):

```
read_state()            -> state/ORGANISM-STATE.json         (Overview vitals, heart, age_tick)
read_sigma()            -> state/replication-latest.json     (σ zone)
read_telemetry()        -> state/telemetry-latest.json       (spend)
read_metabolic_recon()  -> state (telemetry.reconcile output: conflicts/frozen)
read_school()           -> state/school-awareness.json
read_latent()           -> state/latent-vectors.json
read_bcm()              -> state/bcm-weights.json
read_sparse()           -> state/sparse-predictor.json
read_idea()             -> state/idea-graph-latest.json      (+ broken_targets, proposed_edges)
read_chamber_t()        -> state/chamber-temperature.json    (RED/off)
read_fisher()           -> state/fisher-latest.json | «not-wired» اگر فایل نبود
read_epi()              -> state/epi-latest.json
read_box()              -> state/doctor_box.json             (memory/topology/agents/G_t/ρ(J); §۶.۴)
read_evolution()        -> state (run_cycle result['evolution'] sub-report)
read_projectf()         -> state (process_project_f_draft: routed/guards_passed/submitted)
read_governor_llm()     -> state (allocate_llm status — locked)
read_scheduler()        -> state (make_scheduler/anticipation_queue)
read_selfheal()         -> state (selfheal flag/restart-count/circuit-breaker)
read_capabilities()     -> OCTOPUS-flags.cmd + state (page_capabilities mirror: 19 flags + cadences)
read_channels()         -> state/channel-status.json         (page_channels mirror)
read_crypto_brief()     -> state/note (summarize_crypto_file)
read_phase()            -> state/phase-gate-state.json
read_queue()            -> _count_pending + BrainCockpit.approval_queue_html + EffectorGate.status_of
read_bundle()           -> state/export/octopus-status-bundle.json  (24 rules R1..R24)
read_chrono_ro()        -> chrono.db  (رجوع به قاعده‌ی زیر)
tail_governor_alerts()  -> governor/governor-alerts.md (last 30)
tail_structured_log()   -> فایلِ JSONLِ FileEmitter (last N) — نه octo_log
```

**قاعده‌ی `read_chrono_ro` (اجباری):** اتصال read-only با URI و timeout کوتاه تا هرگز lockِ pacemaker را مسدود نکند:
```python
con = sqlite3.connect("file:.../chrono.db?mode=ro&immutable=1", uri=True, timeout=1)
```
فقط queryهای read-only، همیشه `close()`، و در `sqlite3.OperationalError` → fail-soft `{}` (DBِ busy/locked نه crash کند نه بلاک).

برای R1..R24 ترجیحاً **bundle آماده** را بخوان؛ اگر کهنه بود، دکمه‌ی `act:export:raw` را پیشنهاد بده (خودت `build_bundle` را import/اجرا نکن مگر همان `export_status.main` که secret-scan دارد).

### ۶.۳ اتصال از راهِ factory
کانالِ زنده را **از `wiring.py:make_telegram_channel`** بگیر (gate/ledger/leg تزریق‌شده). cockpit کانالِ خودش را نمی‌سازد. read-model را به constructor تزریق کن.

### ۶.۴ پیش‌نیازهای persist (تا read-model چیزی برای خواندن داشته باشد)
- **Box report:** `doctor.py` باید `result['box']` (شاملِ memory/topology/agents/G_t/ρ(J)) را به `_ops/state/doctor_box.json` بنویسد (atomic). بدون آن، تبِ box و زیرردیف‌هایش منبعِ read ندارند → کارت را «not-wired — نیازمندِ persist در doctor» علامت بزن + TODO.
- **Afferent ratio:** transient است. پیش‌فرضِ MVP: «not-wired شفاف».
- **Fisher:** وجودِ `state/fisher-latest.json` را **تأیید کن**؛ اگر نوشته نمی‌شود، مثلِ box «not-wired — needs persist» رفتار کن، فرض نکن فایل هست.

### ۶.۵ فایل‌های جدید (فهرست)
- `_ops/budget/cockpit_readmodel.py` (helperهای بالا).
- `_ops/tests/test_cockpit_v2.py` (بخش ۷).
- (اختیاری، اگر doctor persist را انجام دادی) ویرایشِ `_ops/doctor/doctor.py` برای نوشتنِ `doctor_box.json`.
- **بدونِ فایلِ جدیدِ دیگر.** cockpit عمدتاً متدهای جدید در همان `approval_channel.py` است.

---

## ۷. پذیرش (Acceptance)

### ۷.۱ تست‌ها — offline، http تزریقی، هم‌سبکِ `_ops/tests/` با `harness.run`
یک `FakeHTTP` تزریق کن که `getUpdates`/`sendMessage` را mock می‌کند.

1. **`test_menu_routing`**: `menu:overview..alerts` هر ۸ تب یک کارتِ HTML با mode-color header برمی‌گرداند؛ `menu:main` منوی اصلی با MENU_KEYBOARDِ گسترش‌یافته؛ `menu:queue` صفِ pending.
2. **`test_dispatch_signature`**: `dispatch_callback` یک **رشته** می‌گیرد؛ `dispatch_callback("app:approve:e1:tok")` بدونِ TypeError کار می‌کند (assert علیه رگرسیونِ `cb["data"]`).
3. **`test_callback_backcompat`**: `menu:stop_confirm` هنوز `STOP-ORGANISM` می‌نویسد؛ `app:approve:<eid>:<token>` settle؛ `rfc:merge:<rid>:<token>` verdict — بدونِ regression.
4. **`test_new_schemes_no_token_for_reads`**: `menu:`/`card:`/`pg:` بدون token پاسخ می‌دهند؛ `act:` بدون token صحیح → «رد».
5. **`test_act_token_single_use`**: یک `act:` معتبر یک‌بار اجرا می‌شود؛ **replayِ همان callback_data بارِ دوم → رد** (status=consumed)؛ token منقضی/غایب → رد.
6. **`test_act_allowlist`**: `act:<verb ناشناخته>` و `act:latent:forget:<key خارج از allowlist>` → «نادیده»، هیچ اثر.
7. **`test_act_money_fail_closed`**: تلاش برای هر actِ پول‌خور قبل از 2026-07-21 در لایه‌ی cockpit refuse می‌شود؛ `act:reconcile:run`/`act:epoch:run` به‌عنوان دکمه‌ی مستقیم **وجود ندارند**.
8. **`test_act_no_inline_subsystem`**: `act:doctor:run`/`act:consolidate:run` هیچ subsystem cycleِ mutating را inline صدا نمی‌زنند (out-of-band flag یا کارتِ تأیید)؛ grep-assert علیه صدا زدنِ مستقیمِ `run_cycle(`/`run_epoch(` در handler.
9. **`test_settle_path_unique`**: تنها مسیرِ `gate.settle` = `_do_approve`. grep-assert.
10. **`test_readmodel_no_organism_import`**: `cockpit_readmodel` هیچ‌جا `import organism` ندارد (AST/متن).
11. **`test_chrono_ro_uri`**: `read_chrono_ro` با URI `mode=ro&immutable=1` و `timeout=1` وصل می‌شود؛ روی `OperationalError` → `{}` بدونِ crash.
12. **`test_readmodel_failsoft`**: با state dir خالی، هر helper `{}`/`None` و کارت‌ها «داده در دسترس نیست».
13. **`test_pagination`**: ۲۴ قاعده و لیستِ flags در N صفحه؛ مرزهای `pg:` درست.
14. **`test_owner_allowlist`**: update با chat_id غیرمالک skip (offset پیش، no send).
15. **`test_live_gate_locked_labels`**: کارت‌های پول/reconcile/governor-LLM/replication برچسبِ 🔴 «قفل تا 2026-07-21».
16. **`test_flag_off_labels`**: barbell/fitness(+shadow)/epistemics/chamber_t/cardiac/scheduler/selfheal برچسبِ 🟡 «OFF»؛ flag را روشن نمی‌کنند مگر از `act:flag:*`.
17. **`test_no_secret_in_output`**: علاوه بر کارت‌های تولیدیِ cockpit، **یک fixtureِ مسموم** (state/alerts/log با wallet/`sk-`/PII) تزریق کن و assert کن هیچ‌کدام از mirrorهای خام leak نمی‌کنند (redaction فعال، بدنه جایگزین می‌شود).
18. **`test_queue_surface`**: `_count_pending`>0 → بَج + `card:queue:pending` کارت‌ها را با status از `EffectorGate.status_of` (نه self-approved) نشان می‌دهد؛ هر ردیف به `app:` route می‌شود.
19. **`test_failsoft_loop`**: خطای عمدی در یک render → `opslib.alert` + loop زنده.
20. **`test_existing_commands_preserved`**: `/start`,`/status`,`/lead`,`/stop` + `menu:stop_confirm` رفتارِ قبلی.
21. **`test_phaseverdict_via_rfc`**: verdictِ فاز از رجیستریِ `_pending_rfc` می‌رود، نه `act:` (grep-assert علیه `act:phaseverdict`).

اجرا: `python "_ops/tests/test_cockpit_v2.py"` از راهِ `harness.run`؛ باید سبز شود و به سوییتِ کلی regression نزند.

### ۷.۲ چک‌لیستِ smoke دستی (offline)
- [ ] `/start` منوی ۸-دکمه‌ای + بَجِ `📥 صفِ تأیید: N`.
- [ ] هر ۸ تب + `menu:queue` باز، back کار می‌کند.
- [ ] `/status` و `status_report_v2` و `menu:stop_confirm` بدون تغییر.
- [ ] کارتِ پولِ نمونه [تأیید/رد/بعداً] → approve → $0 (live-gate قفل)، status ثبت.
- [ ] `act:` تک‌مصرف: بارِ دوم → «رد».
- [ ] `act:flag:reconcile` → `_write_env` (append)؛ `act:restart:organism` → STOP+RESTART-REQUESTED.
- [ ] `act:lead:claim` → CLAIMED؛ `act:lead:conflict` → علامتِ تعارض.
- [ ] `act:export:raw` → «OK <KB>» یا «ABORT(secret)».
- [ ] `/stop` → STOP-ORGANISM؛ حذفِ فایل = recover.
- [ ] هیچ توکن/secret/PII در لاگ یا کارت (fixtureِ مسموم redact شد).

---

## ۸. تضمینِ عدم‌regression (صریح)

**همه‌ی این‌ها بی‌کم‌وکاست حفظ می‌شوند:**
- Commandها: `/start`, `/status`, `/lead`, `/lead <args>`, `/stop`.
- **سه** Callback scheme: `menu:<page>` (شاملِ `status/lead/queue/lab/stop/stop_confirm/main` + `MENU_KEYBOARD` + `_dispatch_menu` + `_menu_queue` + `_main_menu` که `reply_markup=MENU_KEYBOARD` دارد)، `app:<verb>:<effect_id>:<token>` (۴ بخشی)، و `rfc:<verb>:<rfc_id>:<token>` — **دست‌نخورده**؛ فقط `card`/`pg`/`act` کنارشان اضافه و `menu` با ۸ تب گسترش می‌یابد.
- امضایِ `dispatch_callback(self, data: str)` و قراردادِ `poll_once → self.dispatch_callback(str(text))` — **بدون تغییر**؛ sub-dispatcherها لیستِ `parts` می‌گیرند.
- مسیرِ `menu:stop → menu:stop_confirm → kill_switch` (killِ زنده) — دست‌نخورده.
- کارتِ پول: token، [approve/deny/later]، `_do_approve → _on_human_judgment → EffectorGate.settle` — **تنها مسیرِ settle**.
- RFC: `rfc_card`، `_dispatch_rfc`، `pop_rfc_verdicts`، anti-clobber guard.
- `poll_once`: long-poll $0-idle، owner-allowlist، quarantine (inbound=DATA)، atomic offset، fail-soft، run_forever/kill-check.
- Lab (`start_experiment`/`reveal_experiment`/`lab_status`)، `reentry_packet`، legacy `status_report`: **resurface** نه حذف.
- `.wired` interlock، `_new_token`/`_cteq`، `approval_for`/`_record_approval`.

**اگر هر تستِ موجود قرمز شد، تغییرِ تو غلط است — router را نشکن.**

---

### پیوستِ سریع — نگاشتِ ۲۴ قاعده → منبع (همه از `state/export/octopus-status-bundle.json`)
R1 `stable_read` · R2 halted · R3 FREEZE · R4 STOP · R5 `capability_gate.is_open` · R6 suspect_zero · R7 conflicts · R8 `germline.lag_alarm` · R9 `sigma_state` · R10 `fitness.compute`(+shadow outbox) · R11 reconcile/`_chrono_summary` · R12 `phase_gate`/verdicts · R13 `check_pre_registered` · R14 `_genome_ledger_summary` · R15 heartbeats · R16 effects_pending · R17 `school_bridge.mean_awareness` · R18 consolidation age · R19 `bcm.saturation` · R20 `temperature.current` (RED/off) · R21 `fisher` (advisory؛ اگر persist) · R22 `organ_table` · R23 governor-alerts tail · R24 `wire_summary`.

> **پایان.** بساز، تست کن، سبز کن، هیچ مسیرِ موجود (`menu:`/`app:`/`rfc:`) را نشکن، هیچ قابلیت را جعل نکن، هیچ subsystem cycle را inline اجرا نکن، هیچ secret/PII را echo نکن.