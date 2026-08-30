@agent-prompts/_PROJECT_INSTRUCTIONS.md

## Claude Code — نکات اجرایی این vault

<!-- برای آری: خط اول، قانون اساسی را import می‌کند (یک منبع حقیقت، بدون کپی). این پایین فقط نکات مخصوص Claude Code است. -->

### ترتیب خواندن (کم‌هزینه → عمیق)

1. شروع هر جلسه: `01 - Dashboard/HANDOFF.md` و نگاهی به `00 - Inbox`.
2. جهت‌یابی: `01 - Dashboard/Home.md` → MOC بخش مربوط → فقط بعد، نوت‌های تکی.
3. قبل از هر کاری داخل پوشه یک پروژه: PROJECT.md همان پروژه.
4. کار با سطحِ MCP یا ایجنت‌های موازی: `_ops/octopus_mcp/CONSTITUTION.md` (پروتکلِ چندمغزی + صفِ پیشنهاد).

### محدوده منفی

- `_Archive` و `_Duplicates` را باز نکن مگر صریحاً خواسته شود (فقط مقصد انتقال‌اند).
- `09 - People` را برای کارهای غیرمرتبط با اشخاص نخوان.
- مسیرهای فهرست‌شده در `.agentignore` هرگز خوانده، نوشته یا echo نمی‌شوند.

### جستجوی این vault (مستقیم ripgrep — بدون MCP)

- بر اساس فرانت‌متر: `rg -l "status: active" -g "*.md"`
- محتوای یک پروژه: `rg -i "<کلیدواژه>" "03 - Projects" -t md -C 3`
- چک dedup تلگرام: `rg "message_id: <id>" "10 - Telegram processing"`

### پایان جلسه

1. بخش‌های `## Active Context` و `## Progress` هر PROJECT.md لمس‌شده را تازه کن.
2. `01 - Dashboard/HANDOFF.md` را بازنویسی کن — فقط wikilink، نه کپی محتوا، نه secret.
3. اگر بیش از ~۵ فایل تغییر کرد: commit با پیام `agent-checkpoint: <خلاصه>`.
4. بعد از ویرایش دسته‌ای: هر دو اسکریپت اعتبارسنجی در `04 - Architect System/scripts/` را اجرا کن.
