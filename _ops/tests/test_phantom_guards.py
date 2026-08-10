"""test_phantom_guards — دو کلاسِ «phantom» با یک قاعده بسته می‌شوند.

هر دو خانواده یک شکل دارند: **آرتیفکتی که وجود دارد، ولی خانه‌ای ندارد.**

  ۱) تستی که در `run_all.py::TESTS` ثبت شده ولی `git ls-files` نمی‌شناسدش.
     روی درختِ زنده سبز می‌دود؛ روی یک clone تازه فایل اصلاً نیست. یعنی
     رجیستری یک پوششی را ادعا می‌کند که در مخزن وجود ندارد.
  ۲) نامِ فلگی که کد می‌خواندش ولی در `_ops/OCTOPUS-flags.cmd` صفر بار
     ظاهر می‌شود. مالک نمی‌تواند با عوض‌کردنِ یک **مقدار** مسلحش کند —
     اول باید **نام** را اضافه کند. پس رأیی دربارهٔ آن فلگ خانه ندارد.

⚠️ چرا این تست امروز **سبز** است و چرا سبزیش دروغ نیست
────────────────────────────────────────────────────────────────────────
طرح می‌گوید این گارد «روزِ اول بلند است و نکته همین است». بلندی را با
**قرمزی** پیاده نکردم، با **دفترِ منجمد**. دلیلِ سنجیده‌شده: در
`run_all.py::__main__` هر `failed` غیرخالی `revoke_capability()` را صدا
می‌زند. یک قرمزِ دائمیِ عمدی، مارکرِ قابلیتِ کلِ ارگانیسم را برای همیشه
باطل می‌کند — یعنی این گارد به‌جای گزارشِ بدهی، یک اثرِ زندهٔ سیستمی
می‌گذارد. آن تصمیم مالِ مالک است، نه مالِ گارد.

پس «سبز» این‌جا دقیقاً یک چیز یعنی: **مجموعهٔ متخلفان با دفترِ ثبت‌شده
بایت‌به‌بایت یکی است.** و چهار چیز جلوی دروغ‌شدنش را می‌گیرد:

  الف) بدهی **در خودِ سورس** است، نه پشتِ یک صفر. `PHANTOM_TESTS` هر ۱۳
       نام و `UNDECLARED_FLAGS` هر ۱۸۸ نام را لفظاً می‌برد. کسی نمی‌تواند
       این فایل را بخواند و درخت را تمیز بپندارد.
  ب) تساویِ **دقیقِ مجموعه**، دوطرفه. متخلفِ نو ⇒ قرمز. متخلفی که رفع شد
       ولی دفتر پایین نیامد ⇒ هم قرمز. پس عدد نه به بالا و نه به پایین
       نمی‌پوسد.
  ج) گاردِ «اسکنر خراب است». اگر git جواب ندهد، یا صفر تستِ ثبت‌شده، یا
       صفر فلگِ خوانده‌شده، یا صفر اعلان پیدا شود ⇒ **قرمز**، نه سبز.
       این دقیقاً همان حالتی است که در این vault یک‌بار گاردِ سبز ساخت.
  د) `AST_BLIND_SPOTS` منجمد است. فایلی که parse نمی‌شود، برای اسکنِ AST
       نامرئی است؛ نقطهٔ کورِ **نو** دامنه را بی‌صدا کوچک می‌کند ⇒ قرمز.

اگر مالک بلندیِ قرمز بخواهد، تبدیلش یک خط است: `assert not offenders`.
عمداً این کار را نکردم چون هزینه‌اش revoke است نه یک خطِ قرمز.

اعدادِ سنجیده‌شدهٔ ۲۰۲۶-۰۸-۰۳ (نه اعدادِ سند — سند سه‌تایشان را اشتباه
می‌گفت؛ تفاوت‌ها در `SPEC_VS_MEASURED` ثبت شده).
"""
import ast
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("phantom-guards")

_OPS = harness.SELF_OPS
_REPO = _OPS.parent
_RUN_ALL = _OPS / "tests" / "run_all.py"
_FLAGS_CMD = _OPS / "OCTOPUS-flags.cmd"
FLAGS_CMD_ENV_BLOCKED = False  # set True by declared_flag_names() if flags.cmd absent

# ── دفترِ منجمد ────────────────────────────────────────────────────────────
# ۲۰۲۶-۰۸-۰۴ — این دفتر **پرداخت شد**، پاک نشد. تا ۰۸-۰۳ سیزده تستِ ثبت‌شده
# در TESTS بودند که git نمی‌شناختشان: روی درختِ زنده سبز می‌دویدند و روی یک
# clone تازه اصلاً وجود نداشتند. کامیتِ `9f7c4a8` هر سیزده را وارد گیت کرد.
#
# مستقل سنجیده شد، نه از روی ادعای خودِ گارد: `git ls-files --error-unmatch`
# روی هر سیزده مسیر ⇒ صفر untracked، و `git cat-file -e HEAD:<path>` ⇒ موجود.
#
# نام‌ها عمداً این‌جا می‌مانند (به‌عنوان تاریخچه، نه بدهی) چون تنها راهِ فهمیدنِ
# اینکه یک دفترِ تهی «پرداخت‌شده» است نه «پاک‌شده»، همین است. گاردِ
# `t_the_ledger_is_not_empty` حالا تهی‌بودن را به شاهد گره می‌زند نه به قاعده.
PHANTOM_TESTS_PAID_2026_08_04 = (
    "test_control_plane.py", "test_dark_capabilities.py",
    "test_invoice_unpayable_is_loud.py", "test_lead_card.py",
    "test_lead_email_intake.py", "test_lead_first_reply.py",
    "test_lead_form_notification.py", "test_lead_inbound_consent.py",
    "test_lead_property_extract.py", "test_lead_scorer_farsi.py",
    "test_new_capability_cards.py", "test_proposal_counter_durable.py",
    "test_sync_agent.py",
)
PHANTOM_TESTS = ()

# ۱۸۸ نامِ فلگ که کدِ `_ops/**/*.py` می‌خواندشان و در OCTOPUS-flags.cmd صفر
# بار ظاهر می‌شوند. فقط **نام** — هیچ مقداری از آن فایل خوانده/چاپ نمی‌شود.
UNDECLARED_FLAGS = (
    # ۲۰۲۶-۰۸-۰۳ — تنها ورودیِ افزوده‌شده پس از انجماد، با رأیِ متناظرش:
    # گامِ ۱۷ (C7) این را برای پلهٔ سایه معرفی کرد. سه حالت دارد و پیش‌فرضش
    # `shadow` است، یعنی عددهای منتشرشده دست‌نخورده می‌مانند و فقط حقیقتِ
    # چرخهٔ عمر کنارشان می‌نشیند. تنها حالتِ `lifecycle` منبع را عوض می‌کند و
    # آن **رأیِ مالک** است. اعلامش در `OCTOPUS-flags.cmd` گامِ ۲۱ ِ طرح است —
    # همان‌جا که سه فلگِ دیگر هم منتظرند. تا آن رأی، این‌جا ثبت می‌شود نه پنهان.
    "OCTOPUS_PROPOSAL_METRICS_SOURCE",
    # ۲۰۲۶-۰۸-۰۴ — نُه knob ِ **فقط-هارنس**. هر کدام دقیقاً یک خواننده دارند و آن
    # خواننده یک فایلِ `_ops/tests/**` است؛ صفر خوانندهٔ تولیدی (گرپِ بی‌سقف روی
    # کلِ `_ops`). پس نبودشان از پروفایلِ بوت اشتباه نیست — **الزام** است: اگر
    # نامشان به OCTOPUS-flags.cmd برود، `apply_profile` ممکن است روزی روشنشان کند
    # و یک knob ِ تست به تولید نشت می‌کند. این‌جا ثبت می‌شوند تا «بی‌اعلان» بودنشان
    # یک تصمیمِ نوشته‌شده باشد، نه یک فراموشی.
    #
    # ⚠️ سه‌تای اولِ زیر یک شکافِ **دیگر** را هم لو می‌دهند و همان‌جا ثبت شد:
    # `test_outbound_owner_transport.py` این نام‌ها را ست می‌کند و انتظار دارد
    # `outbound_worker` به آن‌ها گوش دهد — ولی آن transport هرگز نوشته نشد
    # (`git log -S owner_chat_sent` خالی)، تولید `TELEGRAM_OWNER_CHAT_ID` می‌خواند
    # نه `OCTOPUS_OWNER_CHAT_ID`، و فایل در run_all ثبت نیست پس ۵ قرمزش نامرئی بود.
    # رفعش رأیِ مالک است (مسیرِ ارسال، رأیِ ایستادهٔ «فعلاً هیچ ارسالی») — نه کارِ گارد.
    "OCTOPUS_LEAD_OUTBOUND_TARGET", "OCTOPUS_OWNER_CHAT_ID",
    "OCTOPUS_WIRE_LEAD_MIGRATE_PRODUCERS", "OCTOPUS_MINIAPP_CACHE_TTL_S",
    "OCTOPUS_TEST_ALLOW_LIVE_STATE", "OCTOPUS_TEST_ISOLATION_ECHO",
    "OCTOPUS_TEST_ISOLATION_LOG", "OCTOPUS_TEST_LIVE_STATE_GUARD",
    "OCTOPUS_TEST_NET_GUARD",
    # 2026-08-08: OCTOPUS_TEST_SNAPSHOT_CANARY_V001 added — used by
    # test_control_plane_live_snapshot.py (env-mutation canary); not declared in flags.cmd.
    "OCTOPUS_TEST_SNAPSHOT_CANARY_V001",
    # 2026-08-06 -- ceiling lowered on both sides of the drift:
    #   * 65 names formerly here are now declared via the bulk `set FLAG=1`
    #     block near the end of OCTOPUS-flags.cmd (dated 2026-08-04/05/06),
    #     but this ratchet was never dropped to match -- fixed but not
    #     lowered. Removed.
    #   * 4 new undeclared reads the live AST scan found this session, none
    #     of them boolean wires (two path overrides, one probe process
    #     label, one numeric quota share) -- given declaration-site comments
    #     in OCTOPUS-flags.cmd instead (no value armed, just the NAME), so
    #     they don't land here either. Citation:
    #       OCTOPUS_CURRENT_TRUTH -- telegram_center/miniapp_state.py::_find_truth
    #       OCTOPUS_OUTCOMES_DB -- agi2027_control/ops_actions.py::_outcomes_conn
    #       OCTOPUS_PROC_NAME -- reach_probe.py::_proc_name
    #       OCTOPUS_SELF_PATCH_CALL_SHARE -- self_patch.py::SELF_PATCH_SHARE_ENV
    # Remaining names below are re-verified against a fresh AST scan of
    # _ops/**/*.py (this session, 2026-08-06).
    "OCTOPUS_ACTION_BRIDGE_HMAC", "OCTOPUS_AGENT_GATEWAY_PORT",
    "OCTOPUS_AGENT_MAX_BYTES", "OCTOPUS_AGENT_OWNER_SECRET",
    "OCTOPUS_AGENT_PEERS", "OCTOPUS_AGENT_RATE_PER_MIN",
    "OCTOPUS_AGENT_SECRET_PEERAGI1", "OCTOPUS_AGI2027_RUNTIME_DIR",
    "OCTOPUS_ARM_SECRET", "OCTOPUS_BCM_BETA",
    "OCTOPUS_BEAT_PARALLEL", "OCTOPUS_BOOT_RECONCILE_EXEC_H",
    "OCTOPUS_C6_RUNNING_STALE_H", "OCTOPUS_CB_TTL_S",
    "OCTOPUS_CHAMBER_T_MAX", "OCTOPUS_CHAMBER_T_MIN",
    "OCTOPUS_CHAMBER_T_WINDOW", "OCTOPUS_CODE_AUTOAPPLY_LOWRISK",
    "OCTOPUS_CODE_BRAIN_LOCAL_MODEL", "OCTOPUS_CODE_BRAIN_LOCAL_TIMEOUT_S",
    "OCTOPUS_CODE_SHADOW_SUITE_TIMEOUT_S", "OCTOPUS_CONSOLIDATION_COMPRESS",
    # 2026-08-08: OCTOPUS_CONSOLIDATION_DEDUP_* added — three flags introduced by
    # the fuzzy-dedup fix (commit f234d52) for consolidation.py. DEDUP_SIM has a
    # default in code (consolidation.py:74) but none are declared in flags.cmd.
    "OCTOPUS_CONSOLIDATION_DEDUP_FUZZY", "OCTOPUS_CONSOLIDATION_DEDUP_N",
    "OCTOPUS_CONSOLIDATION_DEDUP_SIM",
    "OCTOPUS_CONSOLIDATION_FLOOR_SEC", "OCTOPUS_CONTROL_PLANE_INTERVAL",
    "OCTOPUS_CONTROL_PLANE_LOCK_PORT", "OCTOPUS_CPU_MAX_PCT",
    "OCTOPUS_DEBATE_LOCAL_BUDGET_S", "OCTOPUS_DEBATE_QUEUE_COOLDOWN_H",
    "OCTOPUS_DEFER_TTL_S", "OCTOPUS_FUGU_KILL",
    "OCTOPUS_GOVERNOR_MAX_TOKENS", "OCTOPUS_HOLD_POLICY_DIR",
    "OCTOPUS_IMAP_USE_GMAIL", "OCTOPUS_INGEST_MAX_BYTES",
    "OCTOPUS_INGEST_RATE_PER_MIN", "OCTOPUS_INGEST_SECRET_N8N_DA",
    "OCTOPUS_INGEST_SOURCES", "OCTOPUS_INITIATIVE_UNCAPPED",
    "OCTOPUS_JOURNEY_TASK", "OCTOPUS_LANGAR_DIR",
    "OCTOPUS_LANGAR_ROUTE_DERIVE", "OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE",
    "OCTOPUS_LEAD_DRAFT_THRESHOLD", "OCTOPUS_LEAD_EMAIL_INBOUND_CONSENT",
    "OCTOPUS_LEAD_FA_VOCAB", "OCTOPUS_LEAD_FORM_SENDERS",
    "OCTOPUS_LEAD_INBOX_PORT", "OCTOPUS_LEAD_OWNER_ADDRESSES",
    "OCTOPUS_LEAD_PROPERTY_EXTRACT", "OCTOPUS_LEAD_STALE_HOURS",
    "OCTOPUS_LEAD_SUPPRESSION_SALT", "OCTOPUS_LEDGER_PATH",
    "OCTOPUS_LEDGER_PY", "OCTOPUS_LEG_FRESH_SECS",
    "OCTOPUS_LEG_MANIFEST_DIR", "OCTOPUS_LEG_TASKS_DIR",
    "OCTOPUS_MINIAPP_PORT", "OCTOPUS_MINIAPP_URL",
    # 2026-08-07: OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV — یک فلگِ dev-only opt-in
    # است که در commit da9ab3b معرفی شد (miniapp_gateway.py:117::read_gate_enabled).
    # کامنتِ inline می‌گوید «فقط تست/دیباگ با opt-in توسعه‌دهنده»، پیش‌فرض `"0"`،
    # و fail-closed است (`!= "1"`). در OCTOPUS-flags.cmd اعلام نمی‌شود چون عمداً
    # نباید در تولید مسلح شود — declare‌کردنش در پروفایلِ بوت ممکن است روزی
    # روشنش کند و یک دورزدنیِ امنیتیِ dev-only را به تولید نشت دهد. این‌جا ثبت
    # می‌شود (نه در flags.cmd) تا «بی‌اعلان» بودنش یک تصمیمِ نوشته‌شده باشد، نه
    # فراموشی — هم‌سبکِ OCTOPUS_TEST_*های بالا.
    "OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV",
    "OCTOPUS_MINING_STOP_INTENT_FILE", "OCTOPUS_MINING_SWAP_DECISION_FILE",
    "OCTOPUS_MINING_SWITCH_RECEIPT_FILE", "OCTOPUS_MODULE_MANIFEST_EVERY_N",
    # 2026-08-07: OCTOPUS_NEURAL_LEARNED_APPLY removed — now `set =1` (armed, note 23).
    "OCTOPUS_OBS_ALERT_EVERY_S",
    "OCTOPUS_OBS_COHERENCE_MIN", "OCTOPUS_OBS_STALE_MAX",
    "OCTOPUS_ONE_HEARTBEAT", "OCTOPUS_ONE_HEARTBEAT_ACT_ARMED",
    "OCTOPUS_OPS_AUDIT_PATH", "OCTOPUS_OPS_DB_PATH",
    "OCTOPUS_OPS_IDEMPOTENCY_PATH", "OCTOPUS_OPS_RUNTIME_DIR",
    "OCTOPUS_OWNER_VERDICTS", "OCTOPUS_PROFILE",
    "OCTOPUS_RAM_MAX_PCT", "OCTOPUS_RG_EXE",
    "OCTOPUS_SMTP_FROM", "OCTOPUS_SMTP_HOST",
    "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_PORT",
    "OCTOPUS_SMTP_USER", "OCTOPUS_SPARSE_ERROR_THRESHOLD",
    "OCTOPUS_STATE_DIR", "OCTOPUS_STATE_ROOT",
    "OCTOPUS_TEACHER_DAILY", "OCTOPUS_THESIS_LEDGER",
    "OCTOPUS_TOOL_REQUEST_CAP_PER_DAY", "OCTOPUS_TOOL_REQUEST_MIN_GAP_S",
    "OCTOPUS_VAULT_ROOT", "OCTOPUS_WATCHDOG_STALL_REVIVE",
    "OCTOPUS_WHISPER_MAX_S", "OCTOPUS_WIRE_ACCT_CLOUD",
    "OCTOPUS_WIRE_AUTHZ_SHADOW", "OCTOPUS_WIRE_BUDGET_FRUSTRATION",
    "OCTOPUS_WIRE_CHAMBER_T", "OCTOPUS_WIRE_COMPANY_BOOKS",
    # 2026-08-07: OCTOPUS_WIRE_CONSENT_FW removed — now `set =1` (armed, note 23).
    "OCTOPUS_WIRE_CORTEX_REVIVE",
    # 2026-08-08: OCTOPUS_WIRE_CORTEX_THINK_RICH removed from this ledger — the typo
    # (word-order swap of OCTOPUS_WIRE_CORTEX_RICH_THINK) was fixed in
    # test_cortex_rich_think_heart.py:67, so the misspelled flag is no longer emitted
    # and no longer needs to be tracked here. -1 from the count.
    "OCTOPUS_WIRE_EMAIL", "OCTOPUS_WIRE_FITNESS",
    "OCTOPUS_WIRE_INGEST_EXAMPLE", "OCTOPUS_WIRE_INITIATIVE",
    "OCTOPUS_WIRE_LEAD_BOUNDARY", "OCTOPUS_WIRE_LEAD_CARD_CONTACT",
    "OCTOPUS_WIRE_LEAD_EMAIL_INTAKE", "OCTOPUS_WIRE_LEAD_FIRST_REPLY",
    "OCTOPUS_WIRE_LEAD_FIRST_RESPONSE", "OCTOPUS_WIRE_LEAD_FIRST_RESPONSE_LLM",
    "OCTOPUS_WIRE_LEAD_INBOX", "OCTOPUS_WIRE_LEAD_LLM",
    "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL", "OCTOPUS_WIRE_LEAD_SUPPRESSION",
    "OCTOPUS_WIRE_ORGANISM_SYNDROME", "OCTOPUS_WIRE_TEST_AUDIT",
    "OCTOPUS_WIRE_TG_CONTROL", "OCTOPUS_WIRE_TICK_WORKERS",
    "OCTOPUS_WIRE_TRADEQUOTE", "OCTOPUS_WIRE_VALUE_LEDGER",
    "OCTOPUS_WIRE_VAULT_AUTO_WRITE", "OCTOPUS_WIRE_ZTEST",
)

# فایل‌هایی که `ast.parse` نمی‌پذیردشان ⇒ برای این اسکن **نامرئی**اند.
# منجمد، چون نقطهٔ کورِ نو دامنه را بی‌صدا کوچک می‌کند.
AST_BLIND_SPOTS = (
    "_ops/agi2027_control/integration.py",
    "_ops/agi2027_control/runtime.py",
    "_ops/agi2027_control/tests/test_runtime.py",
    "_ops/patch_backups/control-close-and-passthrough-20260802-171006/integration.py",
)

# سه فلگی که سند اسمشان را برد. اهمیتشان این‌جا **روشِ کشف** است: هر سه فقط
# از راهِ ثابتِ ماژول خوانده می‌شوند (`FLAG_ENV = "..."` بعد `flag(FLAG_ENV)`)،
# نه با رشتهٔ لفظی داخلِ خودِ فراخوانی. آشکارسازِ فقط-لفظی هر سه را از دست
# می‌دهد و مجموعهٔ متخلفان را بی‌صدا کوچک می‌کند. لنگرِ نماد:
#   _ops/heart/pulse_arbiter.py::FLAG_ENV
#   _ops/dashboard/server.py::DEADWRITE_FLAG   ·  _ops/live/server.py::DEADWRITE_FLAG
#   _ops/telegram_center/pf_miniapp.py::FLAG
# ۲۰۲۶-۰۸-۰۶ — هر سه لنگر حالا در OCTOPUS-flags.cmd اعلان دارند (bulk
# `set FLAG=1` نشست‌های ۰۸-۰۴/۰۵/۰۶)، پس این تاپل موقتاً تهی است. تهی‌بودنش
# «بی‌دندان‌شدن» نیست — t_the_ledger_is_not_empty فقط PHANTOM_TESTS یا
# UNDECLARED_FLAGS را می‌خواهد، نه این تاپل را؛ و t_indirect_flag_reads_are_
# still_detected هر سه نام را از DETECTOR_ONLY_CANARIES هنوز کشف می‌کند.
INDIRECT_READ_CANARIES = ()

# ۲۰۲۶-۰۸-۰۴ — `OCTOPUS_PF_MINIAPP` از فهرستِ بالا **جابه‌جا** شد، نه حذف.
# این گارد دو ادعای مستقل داشت که در یک تاپل قاطی شده بودند:
#   (۱) آشکارسازِ خواندنِ غیرمستقیم هنوز پیدایش می‌کند  ← دندانِ واقعی
#   (۲) هنوز در OCTOPUS-flags.cmd بی‌اعلان است          ← فقط دفترداری
# حالا اعلان دارد، پس ادعای (۲) دربارهٔ آن غلط است. حذفِ کاملش ادعای (۱) را
# هم می‌کشت و یکی از سه لنگرِ آشکارساز بی‌صدا از بین می‌رفت — همان فرسایشی که
# خودِ این فایل قرار است بگیرد. پس فقط ادعای (۱) رویش می‌ماند.
# لنگرِ نماد: _ops/telegram_center/pf_miniapp.py::FLAG
#
# ۲۰۲۶-۰۸-۰۶ — `OCTOPUS_WIRE_PULSE_ARBITER` و `OCTOPUS_WIRE_DEADWRITE_CARDS`
# هم عیناً همان مسیر را رفتند: bulk `set FLAG=1` در OCTOPUS-flags.cmd (نشست‌های
# ۰۸-۰۵/۰۸-۰۶) حالا اعلانشان می‌کند، پس ادعای (۲) دربارهٔ هر دو غلط شد. (نکته:
# DEADWRITE_CARDS قبلِ این جلسه هم اعلان داشت — چون هر دو در یک تاپل بودند و
# assert روی اولی [PULSE_ARBITER] fail-fast می‌کرد، این گارد هرگز به دومی
# نمی‌رسید تا آشکار شود.) هر دو جابه‌جا شدند نه حذف — ادعای (۱) هنوز رویشان
# می‌ماند و خودِ گارد پایین (t_indirect_flag_reads_are_still_detected) پیغامِ
# خودش همین جابه‌جایی را می‌خواست (نه حذفِ نام از هیچ‌کجا).
# لنگرِ نماد: _ops/heart/pulse_arbiter.py::FLAG_ENV ·
#             _ops/dashboard/server.py::DEADWRITE_FLAG ·
#             _ops/live/server.py::DEADWRITE_FLAG
DETECTOR_ONLY_CANARIES = (
    "OCTOPUS_PF_MINIAPP",
    "OCTOPUS_WIRE_PULSE_ARBITER",
    "OCTOPUS_WIRE_DEADWRITE_CARDS",
)

# اعدادِ سند در برابرِ اعدادِ سنجیده‌شده — واقعیت گزارش می‌شود، نه spec.
SPEC_VS_MEASURED = """\
سند: «۵ فایلِ untracked · ۳ فلگِ بی‌اعلان · ۱۵۱ در برابرِ ۱۴۸»
سنجیده (۲۰۲۶-۰۸-۰۳، همین درخت):
  · ۱۳ تستِ ثبت‌شده untracked — نه ۵. (سند به ۵ فایلِ *پیاده‌سازیِ* sync_agent
    اشاره داشت و فرض کرده بود test_sync_agent.py کامیت شده؛ نیست.)
  · ۱۸۸ فلگِ خوانده‌شدهٔ بی‌اعلان — نه ۳. آن سه واقعاً بی‌اعلان‌اند، ولی
    ۱۸۵ تای دیگر هم همین‌طورند (۷۱ تا با پیشوندِ OCTOPUS_WIRE_).
  · «۱۵۱ در برابرِ ۱۴۸» بازتولید نشد: هر چهار flags-loaded-*.json دقیقاً
    ۱۴۶ نامِ OCTOPUS_ دارند و هر چهار شاملِ OCTOPUS_WIRE_SYNC_AGENT اند.
    ۱۵۱ عددِ *اعلان‌های داخلِ OCTOPUS-flags.cmd* است، نه هیچ اختلافِ زنده."""

_FLAG_NAME = re.compile(r"^OCTOPUS_[A-Z0-9_]+$")
_FLAG_IN_TEXT = re.compile(r"\bOCTOPUS_[A-Z0-9_]+\b")
_ENV_READ_FUNCS = {"getenv", "flag", "_flag", "env_flag", "_env_flag",
                   "flag_on", "_flag_on"}


# ─── جمع‌آوری (همه فقط‌خواندنی) ────────────────────────────────────────────
def _git(*args):
    """git فقط‌خواندنی. شکستش **استثنا** است، نه مجموعهٔ تهی — مجموعهٔ تهی
    این گارد را بی‌صدا سبز می‌کند و همان دروغی است که باید نگیرد."""
    try:
        r = subprocess.run(["git", *args], cwd=str(_REPO), capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        raise RuntimeError(f"git اجرا نشد (PATH؟): {e}") from e
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} rc={r.returncode}: "
                           f"{(r.stderr or '').strip()[:200]}")
    return r.stdout


@lru_cache(maxsize=1)
def tracked_paths():
    return frozenset(p.replace("\\", "/")
                     for p in _git("ls-files", "-z").split("\0") if p)


def _tests_list(source, label):
    for node in ast.parse(source).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "TESTS"):
            return tuple(e.value for e in node.value.elts
                         if isinstance(e, ast.Constant))
    raise RuntimeError(f"TESTS در {label} پیدا نشد — اسکنر خراب است")


@lru_cache(maxsize=1)
def registered_tests():
    return _tests_list(_RUN_ALL.read_text("utf-8"), "run_all.py (درختِ کار)")


@lru_cache(maxsize=1)
def head_registered_tests():
    return _tests_list(_git("show", "HEAD:_ops/tests/run_all.py"),
                       "HEAD:run_all.py")


@lru_cache(maxsize=1)
def head_test_files():
    out = _git("ls-tree", "-r", "--name-only", "HEAD", "_ops/tests/")
    return frozenset(line.rsplit("/", 1)[-1] for line in out.splitlines() if line)


def _is_env_read(call):
    f = call.func
    if isinstance(f, ast.Attribute):
        if f.attr == "getenv" and isinstance(f.value, ast.Name) and f.value.id == "os":
            return True
        if f.attr in ("get", "setdefault", "pop"):
            v = f.value
            if ((isinstance(v, ast.Attribute) and v.attr == "environ")
                    or (isinstance(v, ast.Name) and v.id == "environ")):
                return True
        if f.attr in _ENV_READ_FUNCS:
            return True
    return isinstance(f, ast.Name) and f.id in _ENV_READ_FUNCS


def _is_environ(node):
    return ((isinstance(node, ast.Attribute) and node.attr == "environ")
            or (isinstance(node, ast.Name) and node.id == "environ"))


def flag_reads_in(tree):
    """نام‌های فلگی که این ماژول واقعاً **می‌خواند**.

    دو لایه، و لایهٔ دوم اجباری است: الگوی غالبِ این مخزن
    `FLAG = "OCTOPUS_X"` در سطحِ ماژول است و بعد `flag(FLAG)`. آشکارسازِ
    فقط-لفظی هر سه فلگِ نام‌بردهٔ سند را از دست می‌دهد (t_indirect_… همین را
    قفل می‌کند)."""
    consts = {}
    for node in ast.walk(tree):
        tgt = val = None
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            tgt, val = node.targets[0].id, node.value
        elif (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                and node.value is not None):
            tgt, val = node.target.id, node.value
        if (tgt and isinstance(val, ast.Constant) and isinstance(val.value, str)
                and _FLAG_NAME.match(val.value)):
            consts[tgt] = val.value

    def resolve(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and _FLAG_NAME.match(n.value):
            return n.value
        if isinstance(n, ast.Name):
            return consts.get(n.id)
        if isinstance(n, ast.Attribute):
            return consts.get(n.attr)
        return None

    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_env_read(node):
            for a in node.args:
                if (r := resolve(a)):
                    found.add(r)
        elif isinstance(node, ast.Subscript) and _is_environ(node.value):
            if (r := resolve(node.slice)):
                found.add(r)
        elif isinstance(node, ast.Compare):
            if any(isinstance(o, (ast.In, ast.NotIn)) for o in node.ops) \
                    and any(_is_environ(c) for c in node.comparators):
                if (r := resolve(node.left)):
                    found.add(r)
    return found


@lru_cache(maxsize=1)
def scan_source():
    """(reads: name -> sorted relpaths, blind_spots: sorted relpaths)"""
    reads, blind = {}, []
    for p in sorted(_OPS.rglob("*.py")):
        rel = p.relative_to(_REPO).as_posix()
        try:
            tree = ast.parse(p.read_text("utf-8", errors="replace"))
        except (SyntaxError, ValueError, OSError):
            blind.append(rel)
            continue
        for name in flag_reads_in(tree):
            reads.setdefault(name, set()).add(rel)
    return ({k: tuple(sorted(v)) for k, v in reads.items()}, tuple(sorted(blind)))


@lru_cache(maxsize=1)
def declared_flag_names():
    """فقط **نام**‌ها از محلِ اعلام. هیچ مقداری خوانده، نگه‌داشته یا چاپ نمی‌شود.

    2026-08-10: OCTOPUS-flags.cmd is gitignored/live-local. In a clean worktree
    or CI it does not exist. Return empty frozenset and set FLAGS_CMD_ENV_BLOCKED
    so callers can report ENV_BLOCKED honestly instead of crashing.
    """
    if not _FLAGS_CMD.exists():
        global FLAGS_CMD_ENV_BLOCKED
        FLAGS_CMD_ENV_BLOCKED = True
        return frozenset()
    text = _FLAGS_CMD.read_text("utf-8", errors="replace")
    return frozenset(_FLAG_IN_TEXT.findall(text))


def untracked_registered():
    tr = tracked_paths()
    return tuple(sorted(n for n in registered_tests()
                        if (_OPS / "tests" / n).exists()
                        and f"_ops/tests/{n}" not in tr))


def absent_registered():
    return tuple(sorted(n for n in registered_tests()
                        if not (_OPS / "tests" / n).exists()))


def undeclared_reads():
    reads, _ = scan_source()
    declared = declared_flag_names()
    return tuple(sorted(n for n in reads if n not in declared))


def _drift(current, baseline, unit):
    cur, base = set(current), set(baseline)
    new, gone = sorted(cur - base), sorted(base - cur)
    parts = []
    if new:
        parts.append(f"متخلفِ نو ({len(new)}): {new}")
    if gone:
        parts.append(f"رفع‌شده ولی دفتر پایین نیامد ({len(gone)}): {gone} — "
                     f"{unit} را در همین فایل به {len(cur)} برسان")
    return "؛ ".join(parts)


# ─── گاردها ────────────────────────────────────────────────────────────────
def t_fixture_is_isolated_from_the_live_vault():
    """هر مسیرِ فیکسچر باید بیرونِ درختِ زنده باشد — پیش از هر ادعای دیگری."""
    root = Path(ENV["root"]).resolve()
    live = Path(os.environ.get("REAL_VAULT", r"F:\backup")).resolve()
    assert root != live, f"ریشهٔ فیکسچر خودِ درختِ زنده است: {root}"
    assert live not in root.parents, f"فیکسچر زیرِ درختِ زنده ساخته شد: {root}"
    for key in ("OPS_DIR", "OCTOPUS_STATE_DIR", "BRAIN_DIR", "GENOME_DIR"):
        pinned = Path(ENV[key]).resolve()
        assert pinned == root or root in pinned.parents, \
            f"{key} به فیکسچر pin نشده: {pinned}"


def t_scanner_is_not_broken():
    """«تمیز گزارش کرد» و «چیزی نخواند» دو چیزند و اسکالرِ سبز یکسانی دارند.

    این گارد اولی را از دومی جدا می‌کند. اگر git نجواب بدهد، یا رجیستری خالی
    برگردد، یا صفر فلگ خوانده/اعلام شود — قرمز، نه سبز.

    2026-08-10: وقتی OCTOPUS-flags.cmd غایب است (worktree/CI)، بخشِ declared-count
    از این گارد skip می‌شود — ENV_BLOCKED صادقانه، نه سبزِ جعلی روی دادهٔ مفقود."""
    tr = tracked_paths()
    assert len(tr) > 1000, f"git ls-files فقط {len(tr)} مسیر داد — اسکنر خراب است"
    assert f"_ops/tests/{_RUN_ALL.name}" in tr, "خودِ run_all.py هم tracked نیست؟"
    reg = registered_tests()
    assert len(reg) > 400, f"TESTS فقط {len(reg)} ورودی داد — پارسِ رجیستری خراب است"
    assert len(set(reg)) == len(reg), \
        f"ورودیِ تکراری در TESTS: {sorted({n for n in reg if reg.count(n) > 1})}"
    reads, _ = scan_source()
    assert len(reads) > 200, f"فقط {len(reads)} نامِ فلگ خوانده شد — آشکارساز خراب است"
    if not FLAGS_CMD_ENV_BLOCKED:
        declared = declared_flag_names()
        assert len(declared) > 100, \
            f"فقط {len(declared)} اعلان در {_FLAGS_CMD.name} — خواندنِ محلِ اعلام خراب است"


def t_no_registered_test_is_missing_from_disk():
    """ورودیِ اشاره‌به-فایلِ‌ناموجود سوییت را **دائم** قرمز می‌کند (ریشهٔ C-01/C-04).
    این یکی آستانه ندارد: صفر یعنی صفر."""
    absent = absent_registered()
    assert not absent, f"{len(absent)} ورودیِ TESTS فایل ندارند: {list(absent)}"


def t_registered_tests_are_tracked_by_git():
    """تستی که git نمی‌شناسدش، روی clone تازه وجود ندارد — پس پوششی که
    رجیستری ادعا می‌کند، در مخزن نیست."""
    current = untracked_registered()
    drift = _drift(current, PHANTOM_TESTS, "PHANTOM_TESTS")
    assert not drift, f"دفترِ phantomها تکان خورد — {drift}"
    assert len(current) == len(PHANTOM_TESTS), \
        f"شمارِ phantom {len(current)} ≠ دفترِ {len(PHANTOM_TESTS)}"


def t_every_phantom_is_a_phantom_on_a_fresh_clone():
    """تشدیدکننده: ورودی در HEAD ثبت است **و** فایل در درختِ HEAD نیست.
    یعنی این‌ها آرتیفکتِ درختِ کثیفِ محلی نیستند؛ یک clone تازه هر ۱۳ را
    به‌عنوان تستِ ثبت‌شدهٔ بی‌فایل تحویل می‌گیرد."""
    head_reg, head_files = set(head_registered_tests()), head_test_files()
    assert len(head_files) > 300, \
        f"ls-tree فقط {len(head_files)} فایل داد — اسکنر خراب است"
    fresh = sorted(n for n in untracked_registered()
                   if n in head_reg and n not in head_files)
    assert sorted(fresh) == sorted(PHANTOM_TESTS), (
        f"phantomِ clone-تازه {len(fresh)} ≠ دفترِ {len(PHANTOM_TESTS)}: "
        f"نو={sorted(set(fresh) - set(PHANTOM_TESTS))} "
        f"گم={sorted(set(PHANTOM_TESTS) - set(fresh))}")


def t_every_flag_read_has_a_declaration_site():
    """نامی که در OCTOPUS-flags.cmd نیست را مالک نمی‌تواند با عوض‌کردنِ یک
    **مقدار** مسلح کند؛ اول باید نام را اضافه کند. پس رأی خانه ندارد.

    2026-08-10: در غیابِ OCTOPUS-flags.cmd (worktree/CI)، declared = empty ⇒
    همه reads بی‌اعلان دیده می‌شوند. این گارد skip می‌شود — ENV_BLOCKED صادقانه."""
    if FLAGS_CMD_ENV_BLOCKED:
        return  # ENV_BLOCKED — declared set is empty; can't meaningfully check
    current = undeclared_reads()
    drift = _drift(current, UNDECLARED_FLAGS, "UNDECLARED_FLAGS")
    assert not drift, f"دفترِ فلگ‌های بی‌اعلان تکان خورد — {drift}"
    assert len(current) == len(UNDECLARED_FLAGS), \
        f"شمارِ بی‌اعلان {len(current)} ≠ دفترِ {len(UNDECLARED_FLAGS)}"


def t_indirect_flag_reads_are_still_detected():
    """گاردِ خودِ آشکارساز.

    هر سه فلگِ نام‌بردهٔ سند فقط از راهِ ثابتِ ماژول خوانده می‌شوند. اگر کسی
    `flag_reads_in` را به «فقط رشتهٔ لفظیِ داخلِ فراخوانی» ساده کند، این سه
    از مجموعهٔ خوانده‌شده می‌افتند، بی‌اعلان‌ها از ۱۸۸ به ۱۸۵ می‌رسد و
    دفتر «تمیزتر» به‌نظر می‌آید. اسکنِ کورشده نباید سبز بدهد.

    2026-08-10: بخشِ `not in declared` وقتی flags.cmd غایب است skip می‌شود
    (declared = empty ⇒ همه declared نیستند). بخشِ `in reads` همچنان چک می‌شود."""
    reads, _ = scan_source()
    declared = declared_flag_names()
    for name in INDIRECT_READ_CANARIES:
        assert name in reads, (
            f"«{name}» دیگر به‌عنوان خوانده‌شده کشف نمی‌شود — آشکارسازِ "
            f"غیرمستقیم کور شد (لنگر: pulse_arbiter.py::FLAG_ENV، "
            f"dashboard/server.py::DEADWRITE_FLAG، pf_miniapp.py::FLAG)")
        if not FLAGS_CMD_ENV_BLOCKED:
            assert name not in declared, (
                f"«{name}» حالا در {_FLAGS_CMD.name} اعلان دارد — خبرِ خوب، ولی "
                f"از INDIRECT_READ_CANARIES و UNDECLARED_FLAGS حذفش کن "
                f"(به DETECTOR_ONLY_CANARIES منتقلش کن تا لنگرِ آشکارساز نمیرد)")
    # لنگرهایی که دیگر بی‌اعلان نیستند ولی هنوز باید **کشف** شوند. اگر
    # `flag_reads_in` به «فقط رشتهٔ لفظی» ساده شود، این‌ها هم می‌افتند.
    for name in DETECTOR_ONLY_CANARIES:
        assert name in reads, (
            f"«{name}» دیگر کشف نمی‌شود — آشکارسازِ غیرمستقیم کور شد "
            f"(لنگر: pf_miniapp.py::FLAG)")


def t_ast_blind_spots_are_frozen():
    """فایلی که parse نمی‌شود برای این اسکن نامرئی است. نقطهٔ کورِ **نو**
    دامنه را بی‌صدا کوچک می‌کند و بی‌اعلان‌ها را دروغین پایین می‌آورد."""
    _, blind = scan_source()
    drift = _drift(blind, AST_BLIND_SPOTS, "AST_BLIND_SPOTS")
    assert not drift, f"نقاطِ کورِ AST تکان خورد — {drift}"


def t_the_ledger_is_not_empty():
    """دفترِ تهی یعنی این فایل دیگر چیزی را قفل نمی‌کند — و بدترین حالتِ
    ممکن است: سبزِ کاملاً بی‌معنا که شبیهِ درختِ تمیز به‌نظر می‌رسد.

    ۲۰۲۶-۰۸-۰۴ — این گارد با `t_registered_tests_are_tracked_by_git` به تضادِ
    واقعی خورد: هر ۱۳ phantom در کامیتِ `9f7c4a8` tracked شدند (مستقل سنجیده:
    `git ls-files --error-unmatch` روی هر ۱۳ ⇒ صفر untracked)، پس آن گارد
    دفترِ ۰ می‌خواست و این گارد دفترِ >۰. فایل با هیچ مقداری سبز نمی‌شد.

    رفع، بدونِ کندکردنِ دندان: تهی‌بودن دیگر **ممنوع** نیست، بلکه به **شاهد**
    گره خورده. دفتری فقط وقتی می‌تواند تهی باشد که واقعیتِ سنجیده هم تهی باشد.
    پس «خالی‌کردنِ دفتر برای سبزشدن» همچنان قرمز است — چون آن‌وقت واقعیت
    تهی نیست — ولی «بدهی واقعاً پرداخت شد» دیگر برای همیشه قرمز نمی‌ماند.
    و شرطِ اصلیِ خودِ گارد سرِ جایش می‌ماند: این فایل باید چیزی قفل کند."""
    if not PHANTOM_TESTS:
        measured = untracked_registered()
        assert not measured, (
            "PHANTOM_TESTS تهی شد ولی واقعیت تهی نیست — دفتر برای سبزشدن "
            f"خالی شده، نه چون بدهی پرداخت شده: {measured}")
    assert len(UNDECLARED_FLAGS) > 0, "UNDECLARED_FLAGS تهی شد"
    assert PHANTOM_TESTS or UNDECLARED_FLAGS, \
        "هر دو دفتر تهی — این فایل دیگر هیچ چیزی قفل نمی‌کند"
    assert len(set(PHANTOM_TESTS)) == len(PHANTOM_TESTS), "تکرار در PHANTOM_TESTS"
    assert len(set(UNDECLARED_FLAGS)) == len(UNDECLARED_FLAGS), "تکرار در UNDECLARED_FLAGS"
    assert all(_FLAG_NAME.match(n) for n in UNDECLARED_FLAGS), \
        f"نامِ بدشکل در دفتر: {[n for n in UNDECLARED_FLAGS if not _FLAG_NAME.match(n)]}"


# ─── گزارشِ بلند (هر اجرا، حتی وقتی سبز است) ───────────────────────────────
def _wrap(names, per_line=4, indent="      "):
    return "\n".join(indent + "  ".join(names[i:i + per_line])
                     for i in range(0, len(names), per_line))


def report():
    reads, blind = scan_source()
    declared = declared_flag_names()
    untracked = untracked_registered()
    undeclared = undeclared_reads()
    head_reg, head_files = set(head_registered_tests()), head_test_files()
    fresh = sorted(n for n in untracked if n in head_reg and n not in head_files)
    wire = [n for n in undeclared if n.startswith("OCTOPUS_WIRE_")]

    print("\n" + "═" * 74)
    print("  دفترِ phantom — شمارشِ دقیق، نامِ کامل. سبز = «مثلِ دفتر»، نه «تمیز».")
    print("═" * 74)
    print(f"  رجیستری: {len(registered_tests())} ورودیِ TESTS "
          f"({len(head_registered_tests())} در HEAD) · tracked در مخزن: {len(tracked_paths())}")
    print(f"  [۱] ثبت‌شده ولی untracked: {len(untracked)} "
          f"(از این‌ها phantomِ clone-تازه: {len(fresh)})")
    print(_wrap(list(untracked), 2))
    print(f"  [۲] نامِ فلگِ خوانده‌شده در _ops/**/*.py: {len(reads)} · "
          f"اعلان‌شده در {_FLAGS_CMD.name}: {len(declared)} · "
          f"بی‌اعلان: {len(undeclared)} (از این‌ها OCTOPUS_WIRE_*: {len(wire)})")
    print(_wrap(list(undeclared), 3))
    print(f"  [۳] نقاطِ کورِ AST (parse نشد ⇒ نامرئی): {len(blind)}")
    print(_wrap(list(blind), 1))
    print("─" * 74)
    print(SPEC_VS_MEASURED)
    print("═" * 74)


if __name__ == "__main__":
    # گزارش fail-soft است، گاردها نه. کشفِ جهشِ M4: وقتی git از کار افتاد،
    # `report()` استثنا داد و کلِ اجرا **پیش از** رسیدن به گاردها مرد — یعنی
    # خواننده یک traceback می‌دید به‌جای حکمِ دقیقِ «اسکنر خراب است». خروجی
    # همچنان قرمز بود، ولی تشخیص بدتر از چیزی بود که باید. حالا گزارش بلند
    # شکست می‌خورد و گاردها به‌هرحال می‌دوند.
    try:
        report()
    except Exception as e:   # noqa: BLE001
        print(f"\n⚠️ گزارشِ دفتر شکست خورد ({type(e).__name__}: {e}) — "
              f"گاردها با این حال اجرا می‌شوند؛ حکم را از آن‌ها بخوان.")
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    if FLAGS_CMD_ENV_BLOCKED:
        print(f"\nENV_BLOCKED: {_FLAGS_CMD.name} غایب (worktree/CI) — "
              f"flag-declaration checks degraded to empty-declared set; "
              f"NOT green over missing data.")
    if FLAGS_CMD_ENV_BLOCKED:
        # ENV_BLOCKED: flag-declaration subtests were SKIPPED, not passed.
        # exit(2) = SKIP, so run_all does NOT count this as PASS.
        # The non-declaration subtests still ran and are reported above.
        print(f"\n⏭️ test_phantom_guards: SKIP (ENV_BLOCKED — {_FLAGS_CMD.name} غایب; "
              f"{len(checks) - failed}/{len(checks)} non-declaration checks ran, "
              f"flag-declaration checks skipped — NOT PASS)")
        sys.exit(2)
    print(f"\n{'✅' if not failed else '❌'} test_phantom_guards: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
