# 🐙 TG-LIVE-DEBUG-REPORT — فاز G

- **تاریخ:** 2026-07-18
- **نقش:** مهندس ارشد دیباگِ مقرِ فرماندهیِ تلگرام
- **روش:** بررسیِ زنده با env واقعی + `tg_api.diagnostics()` + state files (بدون leak)

---

## چک‌لیست دیباگ (۱۰ مورد)

### 1. ✅ آیا bot token درست است؟
- `token_present`: True (mask: `7992…`، ۴۶ نویسه)
- `token_source`: **`TG_CENTER_BOT_TOKEN`** (نه fallback — مستقل و امن)
- token هرگز در repr/log/diagnostics نشت نمی‌کند (`t_m_token_never_echoed`, `t_zz_diagnostics_no_token_leak`)

### 2. ✅ آیا poller conflict (409) وجود دارد؟
- دو long-poller تولیدی وجود دارد:
  - `approval_channel.py:299` — token = `TELEGRAM_BOT_TOKEN`
  - `tg_api.py:328` — token = `TG_CENTER_BOT_TOKEN`
- **بررسی زنده:** این دو **متفاوت‌اند** → **409 رخ نمی‌دهد** ✅
- 🛡️ **اصلاح فاز G:** اگر روزی `TG_CENTER_BOT_TOKEN` غایب باشد، `tg_api` حالا یک alert throttled می‌زند (`_alert_soft`) تا اپراتور بداند روی باتِ اصلی سوار شده و ریسکِ 409 با approval_channel وجود دارد. قبلاً این حالت بی‌صدا کشته می‌شد.

### 3. ✅ آیا callback_query دریافت می‌شود؟
- `tg_api.poll_updates` در `allowed_updates` شامل `"message"` و `"callback_query"` است (`tg_api.py:327`)
- `center.run_once` → `handle_update` → `_handle_callback` dispatch می‌کند
- `_is_owner` از `client.is_owner` قراردادی استفاده می‌کند (fail-closed)
- **تست e2e سبز:** `t_i_run_once_dispatches_and_advances_offset`, `t_s_ap_ok_approves_job_e2e`

### 4. ✅ آیا owner id درست است؟
- `TELEGRAM_OWNER_CHAT_ID`: `6150431610` (از env)
- `tg_api.is_owner` از `from.id` استفاده می‌کند (نه `chat.id`) — درست برای forum group
- `is_owner` fail-closed است (`t_j_is_owner_allowlist`)

### 5. ✅ آیا callback_dataها کوتاه و ASCII هستند؟
- همهٔ callbackها ASCII: `mn:*`, `lg:*:*`, `pw:*`, `pwc:*`, `map:*`, `ap:*:*:*`, `ok/no/later:*`
- idها با `_sanitize_id` (regex `[^A-Za-z0-9_\-]`) پاک می‌شوند، ≤64 نویسه
- تست `t_j_leg_actions_use_only_known_legs_in_template` سقف 64 بایت را چک می‌کند

### 6. ✅ آیا editMessageText درست کار می‌کند؟
- `tg_api.edit` با `parse_mode=HTML` پیام را edit می‌کند
- خطای «message is not modified» به‌عنوان موفق شمرده می‌شود (`t_z_edit_not_modified_is_success_no_alert`) — جلوگیری از alert کاذب
- ناوبریِ منو با `_edit_page` همان پیام را edit می‌کند (`t_l_menu_navigation_edits_in_place`)

### 7. ✅ آیا parse_mode HTML باعث fail می‌شود؟
- همهٔ رشته‌های dynamic با `_scrub` (containment) و `html.escape` (در detail).escape می‌شوند
- در `render.py` تابع `_esc` به‌طور سیستماتیک به‌کار رفته
- 🐛 **باگِ پیدا-و-رفع‌شده در فاز B+integration:** `_handle_approval_callback` (شاخه detail) از `_esc` استفاده می‌کرد که در `center.py` تعریف نشده بود → NameError → به‌جای نشان‌دادنِ کارتِ جزئیات، به پایانِ تابع می‌رسید. رفع: `html.escape` محلی. تست `t_t_ap_detail_shows_content_free_card_e2e` حالا آن را پوشش می‌دهد.

### 8. ✅ آیا topic/thread درست استفاده می‌شود؟
- ۹ تاپیک ساخته‌شده در config (lead/ziman/mining/crypto/accounting/studio_pf/system/knowledge/cartographer)
- `tg_api.send` با `topic_id` → `message_thread_id` می‌فرستد (forum group)
- `center_chat_id`: `-1004475788460` (`is_forum_center`: True)
- `create_topic` در `ensure_setup` idempotent است (`t_a_double_ensure_setup_idempotent`)

### 9. ✅ آیا center-config.json offset را درست نگه می‌دارد؟
- `last_offset`: `223882891` (restart-safe، در config ذخیره می‌شود)
- `run_once` offset را با `next_offset` پیش می‌برد (`t_i_run_once_dispatches_and_advances_offset`)
- offset خراب → `0` (try/except) → حلقه زنده می‌ماند

### 10. ✅ آیا STOP flags مانع اجرای bot شده‌اند؟
- `STOP-TG-CENTER`: False ✅
- `STOP-ORGANISM`: False ✅
- `HALT-ALL`: False ✅
- `RESTART-REQUESTED`: False ✅
- `master_halted()`: None ✅
- یعنی bot اگر RUN-TG-CENTER.bat اجرا شود، بلافاصله شروع به poll می‌کند.

---

## خلاصهٔ وضعیتِ زنده

| سیگنال | مقدار | ارزیابی |
|--------|-------|---------|
| wired | True | ✅ آمادهٔ اجرا |
| token_source | TG_CENTER_BOT_TOKEN | ✅ مستقل، نه fallback |
| owner_configured | True | ✅ |
| center_configured | True | ✅ |
| is_forum_center | True | ✅ سوپرگروهِ forum |
| topics_count | 9 | ✅ همهٔ پاها |
| status_message_id | True (set) | ✅ pinned |
| last_offset | 223882891 | ✅ restart-safe |
| commands_set | 4 | ✅ /menu /now /budget /revenue |
| STOP flags | همگی False | ✅ |
| master_halted | None | ✅ |

---

## باگ‌های پیدا و رفع‌شده در این فاز

| # | باگ | ریشه | رفع | تست |
|---|-----|------|-----|-----|
| 1 | `_handle_approval_callback` شاخه detail به NameError می‌رسید | `_esc` در center.py تعریف نشده بود | `html.escape` محلی | `t_t_ap_detail_shows_content_free_card_e2e` |
| 2 | ریسک 409 نهفته در fallback توکن | `tg_api` بی‌صدا به `TELEGRAM_BOT_TOKEN` fallback می‌کرد | alert throttled + ردیابی `token_source` | `t_za_token_source_tracked`, `t_zz_diagnostics_no_token_leak` |

---

## نتیجهٔ فاز G

مقرِ فرماندهی **آمادهٔ اجراست**. wiring کامل سبز است، 409 risk رفع شد، و یک باگِ پنهان در detail handler پیدا و رفع گردید. دستور اجرا:

```bat
cd /d F:\backup\_ops
RUN-TG-CENTER.bat
```

یا مستقیم:

```bat
python _ops\telegram_center\center.py
```

پس از اجرا، `/menu` در تلگرام باید کارتِ زندهٔ context-aware با دکمه‌های عملگرا (از جمله 🗺 نقشه‌برداری و 📮 صف تأیید جدید) نشان دهد.
