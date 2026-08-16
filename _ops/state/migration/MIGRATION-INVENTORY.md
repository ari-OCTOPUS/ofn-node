# MIGRATION-INVENTORY — فاز ۵-الف STEP ۰ (ممیزی سطح MCP برای مهاجرت v2)

**تاریخ:** ۲۰۲۶-۰۸-۱۶ · **گام:** STEP ۰ مگاپرامپت فاز ۵-الف — «بدون نوشتن هیچ کدی»
**روش:** grep بازگشتی روی کل `F:\backup` + خواندن کاملِ تک‌تک فایل‌های دارای hit (شرح کامل در §۷)
**مرجع بالادست:** [DOC] [modelcontextprotocol/python-sdk releases — v2.0.0](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0) (موجودیتِ نسخه قبلاً با API زنده تأیید و در `06-EVIDENCE/OCTOPUS-V3-S1-BASELINE-2026-08-16.yaml:49` ثبت شده است)

---

## ۱ — خلاصهٔ اجرایی

1. **صفر استفاده از SDK رسمی.** در کل درخت، هیچ `import mcp` / `from mcp` وجود ندارد و رشتهٔ `mcp` در هیچ `requirements*.txt` / `pyproject.toml` / `Pipfile` / `environment.yml` از کل درخت pin نشده است. [REPO]
2. **کل سطح MCP واقعی = یک سرور دستی.** `_ops/octopus_mcp/server.py` (۴۱۱ خط): سرور stdio با JSON-RPC 2.0 خط‌به‌خط که در docstring خودش «بدون وابستگی pip» بودن را قید طراحی اعلام کرده است، به‌علاوهٔ سه فایل config کلاینت، یک تست، و یک import جانبی برای path-guard. [REPO]
3. **تنها الگوی پروتکل stateful قدیمی که واقعاً اجرا می‌شود:** پاسخ به handshake `initialize` و ثابت `PROTOCOL_VERSION = "2025-06-18"` — هر دو در همان یک فایل. [REPO]
4. **وضعیت تست امروز (بخشی از baseline):** `_ops/tests/test_octopus_mcp_search.py` → `FAIL 1 problem(s)` در `t_empty_query_is_handled`؛ سه چک دیگر گذشتند. قرارداد STEP ۱: بعد از مهاجرت نباید بدتر شود. [REPO]

## ۲ — الگوهای ممنوع/منسوخ مگاپرامپت ← نتیجهٔ grep روی کد

| الگو | hit در کد | hit در اسناد |
|---|---|---|
| `FastMCP` | **۰** | ۳ فایل (فهرست در §۵) |
| `ClientSession` (MCP) | **۰** — همهٔ ۱۲ خطِ grep مربوط به `aiohttp.ClientSession` و JSON-RPC اتریوم است (§۴) | ۰ |
| `initialize` به‌عنوان متد MCP | **۱** — `server.py:362` (+۲ کپی identical در worktreeها، §۳) | ۲ (مگاپرامپت‌های EQUIP) |
| `Mcp-Session-Id` | **۰** | ۳ |
| `mcp.types` / `mcp_types` / `import mcp` | **۰** | ۱ (evidence) |
| `Context.client_id` | **۰** | ۱ (evidence، به‌عنوان شرحِ حذف‌شدگان) |
| `RFC7523OAuthClientProvider` | **۰** | ۰ |
| `MCP_[A-Z]` (env var) | **۰** | ۱ (evidence) |
| `roots/` · `sampling/` · `logging/` (سه فیچر deprecated) | **۰** | ۰ |

## ۳ — سطح واقعی MCP درخت — ردیف‌به‌ردیف [REPO]

| path:line | آنچه هست | اثر مهاجرت v2 |
|---|---|---|
| `_ops/octopus_mcp/server.py:37` | `PROTOCOL_VERSION = "2025-06-18"` | قدیمی‌تر از رویزیون stateless 2026-07-28 — هدف ارتقا/حذف |
| `_ops/octopus_mcp/server.py:362-366` | پاسخ به متد `initialize` (برمی‌گرداند protocolVersion/capabilities/serverInfo) | handshake نسل stateful — هدف اصلی حذف در STEP ۲ |
| `_ops/octopus_mcp/server.py:367` | هندل `notifications/initialized` و `notifications/cancelled` | `initialized` پیوند handshake قدیم است؛ رفتار cancel بدونِ پاسخ باید حفظ شود |
| `_ops/octopus_mcp/server.py:369-390` | `tools/list` و `tools/call` | در v2 معتبر — بدون تغییر رفتاری |
| `_ops/octopus_mcp/server.py:12-13` | docstring: ترابرد stdio، JSON-RPC خط‌به‌خط، «بدون وابستگی pip» | قید طراحی روی انتخاب مسیر مهاجرت (§۶) |
| `_ops/octopus_mcp/server.py:329-343` | پنج ابزار: `list_tree` · `read_file_slice` · `hash_file` · `search_hybrid` · `propose_action` | بدون تغییر |
| `_ops/octopus_mcp/CONSTITUTION.md` | قانون read-only بودن سطح ابزار + صف تأیید مالک | قید سخت — مهاجرت نباید آن را بشکند |
| `.mcp.json` (ریشهٔ repo) | wiring کلاینت `octopus-vault` → `python -X utf8 _ops/octopus_mcp/server.py` | با ماندنِ stdio بدون تغییر |
| `.cursor/mcp.json` | `"mcpServers": {}` — خالی | هیچ (سطح MCP در Cursor فعال نیست) |
| `.claude/worktrees/fugu-ultra-remediation-d10abc/.mcp.json` + `_ops/octopus_mcp/server.py` همان‌جا | کپی راکد؛ server.py آن **byte-identical** با نسخهٔ اصلی (راستی‌آزمایی: `diff -q` ساکت) | صرفاً اگر آن worktree دوباره زنده شود معنا دارد |
| `.claude/worktrees/great-spence-d84352/.mcp.json` + `_ops/octopus_mcp/server.py` همان‌جا | همان وضعیت، همان identical | همان |
| `_ops/tests/test_octopus_mcp_search.py:71-73` | چک «کوئریِ خالی → صفر hit، نه استثنا» | امروز FAIL — رجوع به §۶ |
| `4d_system/memory/vectorstore.py:78,97` | `from octopus_mcp import server` — فقط برای بازاستفادهٔ `_denied()` (path-guard) | وابستگی ماژولی، نه پروتکلی؛ مهاجرت نباید این import را بشکند |
| `4d_system/tests/test_vectorstore_root_scope.py:171,175` | تستِ همان بازاستفاده | همان |

## ۴ — false positiveهای ثبت‌شده (برای grepهای جلسات بعدی)

- `03 - Projects/Lead-نقاشی/Lead-نقاشی.md:5782` — `aiohttp.ClientSession()`: کلاینت HTTP، هیچ ربطی به MCP ندارد. [REPO]
- `03 - Projects/Mining/02 - Code/Ai bots/QuantumAlphaBot/modules/onchain_lp_lock.py:164,174` — JSON-RPC **اتریوم** (`eth_call`)؛ پروتکل دیگری است. [REPO]
- `00 - Inbox/scout-digests/2026-07-06 tools.md:82` — اشارهٔ امنیتی به CVEهای اکوسیستم FastMCP؛ سند است، نه کد. [REPO]

## ۵ — ارجاع‌های سندی (فقط مستندات؛ اقدامی لازم ندارند)

- `06-EVIDENCE/OCTOPUS-V3-S1-BASELINE-2026-08-16.yaml:49` — ثبتِ ادعای نسخهٔ v2.0.0 و known gaps. [REPO]
- `agent-prompts/MEGAPROMPT-EQUIP-00-SHARED-CONTRACT-2026-08-16.md:80` — «Stateless. بدون initialize handshake. بدون Mcp-Session-Id». [REPO]
- `agent-prompts/MEGAPROMPT-EQUIP-08-G5-INFRA-2026-08-16.md:91` — فهرست MUST-NOT. [REPO]
- `CLAUDE.md:12` — ارجاع به CONSTITUTION سرور برای ایجنت‌های موازی. [REPO]

## ۶ — پیامد برای STEP ۱ و STEP ۲

**مسیر A — حداقلی، zero-dependency (توصیهٔ من):** [INFER] سرور دستی بماند؛ فقط لایهٔ پروتکل stateless شود: حذف پاسخِ `initialize`، ارتقای/حذف `PROTOCOL_VERSION` قدیمی، و تعیین رفتار در برابر `notifications/initialized` کلاینت‌های قدیمی. حجم تغییر تخمینی: ~۱۰ تا ۲۰ خط در همان یک فایل. چون dependency جدیدی وارد نمی‌شود، DEPENDENCY ADMISSION GATE اصلاً فعال نمی‌شود و قید «بدون وابستگی pip» در docstring سرور هم برقرار می‌ماند.

**مسیر B — پذیرش SDK رسمی `mcp==2.0.0`:** [INFER] با سه شرط گران: dependency جدید (Admission Gate کامل: pin+sha256، T-EXIT و…)، شکستن قید طراحیِ zero-dependency سرور، و بازنویسی حلقهٔ JSON-RPC. برای سروری که ۵ ابزار سادهٔ stdio دارد، نامتناسب به نظر می‌رسد — جز آنکه بخواهیم فیچرهای v2 (مثل Resolve(fn) برای HITL) را در همین سرور داشته باشیم.

**[UNKNOWN]:** رفتار دقیق سرور stateless در برابر پیام `initialize` کلاینت‌های هنوز-قدیمی (backward-compat، اگر اصلاً چیزی باید برگرداند) — در STEP ۲ از راهنمای رسمی مهاجرت خوانده شود: [DOC] https://py.sdk.modelcontextprotocol.io/migration/

**نکتهٔ baseline برای STEP ۱:** pytest این تست را نمی‌بیند (`python -m pytest … → no tests ran`) چون اسکریپت‌سبک است، نه تابع‌محور. baseline باید خروجی `PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_search.py` را ذخیره کند: **امروز `FAIL 1 problem(s)` — `t_empty_query_is_handled`، سه چک دیگر سبز.** [REPO]

**علت احتمالی شکست:** [INFER] `rg` روی PATH این ماشین هست (WinGet)؛ پس `t_search_hybrid("   ")` وارد مسیر `_rg_search` می‌شود و کوئریِ فقط-فاصله به‌عنوان pattern لفظیِ «سه فاصله» به rg می‌رسد که خطوط دارای سه‌فاصلهٔ متوالی را hit می‌کند و `content` ناخالی برمی‌گردد. مسیر fallback پایتونی (`_py_search`) همین مورد را درست هندل می‌کند (`"empty-query"`). رفعش در حیطهٔ STEP ۰ نیست — ثبت شد تا در مهاجرت گم نشود.

## ۷ — روش و محدودهٔ اسکن (بازتولیدپذیر)

- الگوهای grep شده روی کل درخت: `from mcp|import mcp|mcp\.types|mcp_types` · `FastMCP` · `ClientSession` · `RFC7523OAuthClientProvider|mcp-session-id|Context\.client_id` (case-insensitive) · `jsonrpc` · `"(initialize|tools/call|tools/list|notifications/initialized)"` · `MCP_[A-Z]` · `roots/list|sampling/createMessage|logging/setLevel|createMessage`
- مستثنی‌ها: `.git` · `__pycache__` · `node_modules` · `.venv` · `.pytest_cache`؛ فایل‌های باینری با `--binary-files=without-match` رد شدند.
- محدودیتِ کشف‌شده و جبران‌شده: یک گذرِ بازگشتیِ grep، پوشهٔ `.claude/worktrees` را گزارش نکرد؛ با `find` صریح پیدا و با `diff -q` تأیید شد که دو کپیِ server.py آن‌جا byte-identical با اصلی‌اند. grepهای بعدی روی این پوشه دقت کنند.
- اجرای تست: `PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_search.py` → خروجی خام: `FAIL test_octopus_mcp_search: 1 problem(s)` + `❌ کوئریِ خالی → صفر hit، نه استثنا`.
- فایل‌هایی که برای تگ [REPO] کامل خوانده شدند: `_ops/octopus_mcp/server.py` (۴۱۱ خط) · `_ops/tests/test_octopus_mcp_search.py` · `.mcp.json` · `.cursor/mcp.json` · هر دو `.mcp.json` در worktreeها · بخش‌های ارجاع‌شدهٔ `4d_system/memory/vectorstore.py` و `4d_system/tests/test_vectorstore_root_scope.py`.
