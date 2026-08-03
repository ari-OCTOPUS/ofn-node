"""
bot.py — هندلرها و گفتگوهای بات LANGAR

اصول LANGAR که در کد رعایت شده:
- gate قبل از هر پیام خروجی  → دکوریتور guarded
- فقط OWNER_ID پاسخ می‌گیرد   → دکوریتور owner_only
- kill-switch واقعی           → /halt و /resume از gate معاف‌اند
- Human-write-only برای verdict→ تأیید با دکمه‌ی inline
- در شک: سکوت                 → غریبه و حالت halted = هیچ پاسخی
"""

from __future__ import annotations

import datetime as _dt
import functools
import logging
import os
from datetime import date
from pathlib import Path

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import ai
import coach
import db
import hrv
import menus
import muse
import pro_client

log = logging.getLogger("langar")

# مراحل ConversationHandler برای /log
RMSSD, SLEEP, USED, LOC, NOTE = range(5)
# مرحله‌ی ConversationHandler برای /ask
ASK_ANSWER = 10
# مراحلِ ConversationHandler برای /checkin
CK_MOOD, CK_ENERGY, CK_STRESS = 30, 31, 32
# habits / reviews / experiments / muse / delete
HABIT_TITLE, HABIT_CUE, HABIT_ACTION, HABIT_MIN = 40, 41, 42, 43
REVIEW_Q = 50
EXP_TITLE, EXP_HYP, EXP_INT, EXP_DESIGN = 60, 61, 62, 63
MUSE_WAIT = 70
DEL_CONFIRM = 80


def _brain_prompt() -> str | None:
    """پرامپتِ مغز را از BRAIN_PROMPT.md می‌خواند (اگر باشد)."""
    p = Path(__file__).resolve().parent / "BRAIN_PROMPT.md"
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None

# تبدیل ارقام فارسی/عربی به انگلیسی
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def _en(s: str) -> str:
    return s.translate(_DIGITS)


def _owner_id() -> str:
    """تنبل خوانده می‌شود تا به ترتیبِ import و زمانِ load_dotenv وابسته نباشد."""
    return os.environ.get("OWNER_ID", "")


# CORE / Researcher / PatchManager — توسطِ main.py تزریق می‌شوند (همه اختیاری).
_CORE = None
_RESEARCHER = None
_PATCH = None


def set_core(core) -> None:
    global _CORE
    _CORE = core


def set_researcher(r) -> None:
    global _RESEARCHER
    _RESEARCHER = r


def set_patch(pm) -> None:
    global _PATCH
    _PATCH = pm


_AILAB = None
_BUDGET = None


def set_ailab(lab) -> None:
    global _AILAB
    _AILAB = lab


def set_budget(b) -> None:
    global _BUDGET
    _BUDGET = b


# ----------------------------------------------------------------------
# دکوریتورها — هسته‌ی امنیت و gate
# ----------------------------------------------------------------------

def owner_only(func):
    """فقط OWNER_ID اجازه دارد. غریبه = سکوت کامل."""
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or str(user.id) != _owner_id():
            log.warning("درخواست رد شد از کاربر غیرمجاز: %s", user.id if user else "?")
            return  # سکوت — نه پیام خطا
        return await func(update, ctx)
    return wrapper


def guarded(func):
    """owner_only + بررسی halt. اگر halted باشد سکوت کامل.
    این را روی هر هندلری بگذار که نباید در حالت توقف کار کند.
    """
    @owner_only
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if db.is_halted():
            return  # سکوت کامل
        return await func(update, ctx)
    return wrapper


# ----------------------------------------------------------------------
# kill-switch — از gate معاف (وگرنه پس از halt هرگز روشن نمی‌شود)
# ----------------------------------------------------------------------

@owner_only
async def cmd_halt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db.set_config("halted", "1")
    await update.message.reply_text("⏸ سیستم متوقف شد. همه‌ی ماژول‌ها ساکت‌اند. برای ادامه: /resume")


@owner_only
async def cmd_resume(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db.set_config("halted", "0")
    await update.message.reply_text("▶ سیستم دوباره فعال شد.")


@owner_only
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """status هم از gate معاف است تا همیشه بتوانی وضعیت را ببینی."""
    state = "⏸ متوقف (halted)" if db.is_halted() else "▶ فعال (active)"
    row = db.last_log()
    if row:
        last = (
            f"آخرین log: #{row['id']} · {row['ts']}\n"
            f"  RMSSD={row['rmssd']}  خواب={row['sleep']}  "
            f"مصرف={'بله' if row['used'] else 'خیر' if row['used'] is not None else '—'}  "
            f"مکان={row['loc'] or '—'}"
        )
    else:
        last = "هنوز هیچ log ثبت نشده."
    await update.message.reply_text(f"وضعیت سیستم: {state}\n\n{last}")


# ----------------------------------------------------------------------
# /start
# ----------------------------------------------------------------------

@guarded
async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(menus.main_menu_text(),
                                    reply_markup=menus.main_menu_keyboard())


@guarded
async def on_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data.split(":", 1)[1]
    if key == "main":
        await q.edit_message_text(menus.main_menu_text(), reply_markup=menus.main_menu_keyboard())
    elif key in menus.MENU:
        await q.edit_message_text(menus.category_text(key),
                                  reply_markup=menus.category_keyboard(key))


@guarded
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # تجربه‌ی تمیز: منوی دسته‌بندی‌شده به‌جای فهرستِ بلند
    await update.message.reply_text(menus.main_menu_text(),
                                    reply_markup=menus.main_menu_keyboard())


@guarded
async def cmd_start_full(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """فهرستِ کاملِ متنی (برای backward-compat؛ از /help_all)."""
    await update.message.reply_text(
        "سلام 👋 من بات LANGAR هستم — همراهِ همیشه‌روشن برای RMSSD و بینش‌ها.\n\n"
        "دستورها:\n"
        "/log — ثبت RMSSD و تگ‌های امروز\n"
        "/checkin — چک‌اینِ سریع حال/انرژی/استرس\n"
        "/today — خلاصه‌ی امروز + streak\n"
        "/rmssd <RRها> — محاسبه‌ی سریع RMSSD از داده‌ی خام\n"
        "/rmssd_help — راهنمای اندازه‌گیری\n"
        "/trend [N] — ترند N روز اخیر (پیش‌فرض ۷)\n"
        "/ask — سؤالِ کارگاهِ امروز (مغزِ دوم)\n"
        "/reflect <متن> — ثبت یک بازتابِ آزاد\n"
        "/insight <متن> — ثبت یک بینش با تگ E/S/P\n"
        "/recheck — داوری بینش‌ها · /insights · /insight_stats\n"
        "/habit · /habits · /done · /habit_report — عادت‌ها\n"
        "/review_daily|weekly|monthly — مرورها\n"
        "/experiment · /experiments · /experiment_report — آزمایش‌ها\n"
        "/coach — پیشنهادِ آرامِ داده‌محور\n"
        "/muse_help · /import_muse — ورودِ Muse\n"
        "/export · /export_csv · /privacy\n"
        "/status — وضعیت · /halt — توقف · /resume — ادامه"
    )


# ----------------------------------------------------------------------
# /log — ConversationHandler پنج‌مرحله‌ای
# ----------------------------------------------------------------------

@guarded
async def log_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "ثبت log امروز. هر زمان خواستی لغو کنی: /cancel\n\n"
        "۱/۵ — RMSSD امروز صبح؟\n"
        "• اگر عددِ RMSSD را داری، همان را بفرست (مثل 42.5)\n"
        "• اگر داده‌ی خامِ دستگاه را داری، فواصلِ ضربان (RR/IBI) را با فاصله بفرست "
        "(مثل: 812 799 824 …) تا خودم RMSSD را حساب کنم\n"
        "• یا /skip",
        reply_markup=ReplyKeyboardRemove(),
    )
    return RMSSD


async def log_rmssd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    nums = hrv.parse_numbers(update.message.text)
    if not nums:
        await update.message.reply_text(
            "عددِ معتبری ندیدم. یا یک عدد RMSSD بفرست (مثل 42.5)، "
            "یا چند فاصله‌ی RR با فاصله (مثل 812 799 824)، یا /skip"
        )
        return RMSSD

    if len(nums) == 1:
        # یک عدد = خودِ RMSSD
        ctx.user_data["rmssd"] = nums[0]
    else:
        # چند عدد = داده‌ی خامِ RR → محاسبه‌ی RMSSD
        res = hrv.compute_rmssd(nums)
        if not res["ok"]:
            await update.message.reply_text(
                f"نتوانستم RMSSD را حساب کنم: {res['reason']} دوباره بفرست یا /skip"
            )
            return RMSSD
        ctx.user_data["rmssd"] = round(res["rmssd"], 1)
        note = (
            f"🧮 RMSSD محاسبه شد: {res['rmssd']:.1f} ms "
            f"(از {res['n_used']} فاصله"
            + (f"، {res['n_dropped']} موردِ پرت حذف شد" if res["n_dropped"] else "")
            + ")"
        )
        if res["n_used"] < 10:
            note += "\n⚠️ نمونه کم است؛ برای پایداری ≥۳۰ ضربان توصیه می‌شود."
        await update.message.reply_text(note)
    return await _ask_sleep(update)


@guarded
async def cmd_rmssd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """محاسبه‌ی سریعِ RMSSD از RR خام، بدون ثبت در log."""
    nums = hrv.parse_numbers(" ".join(ctx.args))
    if len(nums) < 2:
        await update.message.reply_text(
            "استفاده: /rmssd به‌همراهِ فواصلِ RR (ms) با فاصله.\n"
            "مثال: /rmssd 812 799 824 805 818"
        )
        return
    res = hrv.compute_rmssd(nums)
    if not res["ok"]:
        await update.message.reply_text(f"محاسبه نشد: {res['reason']}")
        return
    msg = (
        f"🧮 RMSSD = {res['rmssd']:.1f} ms\n"
        f"از {res['n_used']} فاصله"
        + (f" ({res['n_dropped']} موردِ پرت حذف شد)" if res["n_dropped"] else "")
    )
    if res["n_used"] < 10:
        msg += "\n⚠️ نمونه کم است؛ برای پایداری ≥۳۰ ضربان توصیه می‌شود."
    await update.message.reply_text(msg)


async def log_rmssd_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["rmssd"] = None
    return await _ask_sleep(update)


async def _ask_sleep(update: Update):
    kb = ReplyKeyboardMarkup([["1", "2", "3", "4", "5"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("۲/۵ — خوابِ دیشب؟ (۱=خیلی بد … ۵=عالی)", reply_markup=kb)
    return SLEEP


async def log_sleep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = _en(update.message.text.strip())
    if txt not in {"1", "2", "3", "4", "5"}:
        await update.message.reply_text("یک عدد بین ۱ تا ۵ بفرست.")
        return SLEEP
    ctx.user_data["sleep"] = int(txt)
    kb = ReplyKeyboardMarkup([["بله", "خیر"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("۳/۵ — دیشب مصرف داشتی؟", reply_markup=kb)
    return USED


async def log_used(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt in {"بله", "اره", "آره", "yes", "y"}:
        ctx.user_data["used"] = 1
    elif txt in {"خیر", "نه", "no", "n"}:
        ctx.user_data["used"] = 0
    else:
        await update.message.reply_text("«بله» یا «خیر».")
        return USED
    kb = ReplyKeyboardMarkup([["خانه", "کار", "جای دیگر"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("۴/۵ — کجا بودی؟", reply_markup=kb)
    return LOC


async def log_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {"خانه": "home", "کار": "work", "جای دیگر": "other"}
    ctx.user_data["loc"] = mapping.get(update.message.text.strip(), "other")
    await update.message.reply_text(
        "۵/۵ — یادداشت؟ (اختیاری — بینش را با تگ [E]/[S]/[P] بنویس، یا /skip)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NOTE


async def log_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["note"] = update.message.text.strip()
    return await _save_log(update, ctx)


async def log_note_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["note"] = None
    return await _save_log(update, ctx)


async def _save_log(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = ctx.user_data
    new_id = db.add_log(d.get("rmssd"), d.get("sleep"), d.get("used"), d.get("loc"), d.get("note"))
    await update.message.reply_text(
        f"✅ ثبت شد (#{new_id}).\n"
        f"RMSSD={d.get('rmssd') if d.get('rmssd') is not None else '—'}  "
        f"خواب={d.get('sleep')}  مصرف={'بله' if d.get('used') else 'خیر'}  "
        f"مکان={d.get('loc')}",
        reply_markup=ReplyKeyboardRemove(),
    )
    if _CORE is not None:
        try:
            _CORE.register_interaction("log", content={"sleep": d.get("sleep"),
                                                       "rmssd": d.get("rmssd"),
                                                       "used": d.get("used")})
        except Exception:
            log.exception("core register_interaction failed")
    ctx.user_data.clear()
    # اگر آزمایشِ فعالی هست, رعایتِ امروزش را بپرس (یادآوریِ حینِ /log)
    exps = db.list_experiments("active")
    if exps:
        e = exps[0]
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ بله", callback_data=f"expday:{e['id']}:yes"),
            InlineKeyboardButton("◐ نیمه", callback_data=f"expday:{e['id']}:partial"),
            InlineKeyboardButton("❌ نه", callback_data=f"expday:{e['id']}:no"),
        ]])
        await update.message.reply_text(
            f"🧪 آزمایشِ «{e['title']}» — امروز قانونش را رعایت کردی؟", reply_markup=kb
        )
    return ConversationHandler.END


async def log_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ----------------------------------------------------------------------
# /trend
# ----------------------------------------------------------------------

def _fmt_corr(c):
    if c is None:
        return "—  (داده کافی نیست)"
    sign = "+" if c >= 0 else "−"
    return f"{sign}{abs(c):.2f}"


@guarded
async def cmd_trend(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = 7
    if ctx.args:
        try:
            n = max(2, min(90, int(_en(ctx.args[0]))))
        except ValueError:
            pass

    t = db.trend_extended(n)
    if t["count_rmssd"] == 0:
        await update.message.reply_text("هنوز RMSSD کافی ثبت نشده. اول چند روز /log بزن.")
        return

    best, worst = t["best"], t["worst"]
    msg = [
        f"📊 ترند {t['count']} رکورد اخیر ({t['count_rmssd']} مورد با RMSSD · "
        f"completeness {t['completeness']*100:.0f}%)",
        f"RMSSD میانگین: {t['mean_rmssd']:.1f} ms",
    ]
    if t["baseline_30"] is not None:
        vs = t["vs_baseline"]
        arrow = "↑" if (vs or 0) > 0 else "↓" if (vs or 0) < 0 else "≈"
        msg.append(f"baselineِ ۳۰روزه: {t['baseline_30']:.0f} ms · فعلی {arrow} ({vs:+.0f} ms)")
    msg.append(f"بهترین: {best['ts'][:10]} ({best['rmssd']:.0f} ms · خواب {best['sleep']})")
    msg.append(f"ضعیف‌ترین: {worst['ts'][:10]} ({worst['rmssd']:.0f} ms · خواب {worst['sleep']})")
    msg.append(f"همبستگی خواب↔RMSSD: {_fmt_corr(t['corr_sleep'])}")
    msg.append(f"همبستگی مصرف↔RMSSD: {_fmt_corr(t['corr_used'])}")
    if t["low_quality"]:
        msg.append(f"⚠️ {t['low_quality']} رکورد با کیفیتِ پایین — با احتیاط تفسیر کن.")
    msg.append("ℹ️ همبستگی ≠ علیت؛ با n کوچک فقط نشانه است، نه نتیجه.")
    await update.message.reply_text("\n".join(msg))


# ----------------------------------------------------------------------
# /insight — ثبت بینش با تگ E/S/P و recheck
# ----------------------------------------------------------------------

@guarded
async def cmd_insight(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args).strip()
    if not text:
        await update.message.reply_text("استفاده: /insight <متنِ بینش>")
        return
    ctx.user_data["insight_text"] = text
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("E — مستحکم", callback_data="tag:E"),
        InlineKeyboardButton("S — حدس", callback_data="tag:S"),
        InlineKeyboardButton("P — استعاره", callback_data="tag:P"),
    ]])
    await update.message.reply_text(f"بینش:\n«{text}»\n\nتگش چیست؟", reply_markup=kb)


@guarded
async def on_tag(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tag = q.data.split(":", 1)[1]
    text = ctx.user_data.get("insight_text")
    if not text:
        await q.edit_message_text("متنِ بینش پیدا نشد. دوباره /insight بزن.")
        return
    # recheck = فردا (داوری در حالت هوشیار، طبق E4)
    from datetime import timedelta
    recheck = (date.today() + timedelta(days=1)).isoformat()
    new_id = db.add_insight(text, tag, recheck)
    ctx.user_data.pop("insight_text", None)
    await q.edit_message_text(
        f"💡 بینش #{new_id} ثبت شد با تگ [{tag}].\n"
        f"تاریخ داوری: {recheck} (با /recheck یادآوری می‌شود)."
    )


# ----------------------------------------------------------------------
# /recheck — بینش‌های امروز + داوری انسانی (HITL)
# ----------------------------------------------------------------------

@guarded
async def cmd_recheck(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    today = date.today().isoformat()
    rows = db.insights_due(today)
    if not rows:
        await update.message.reply_text("امروز بینشی برای داوری نیست. ✅")
        return
    for r in rows:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ تأیید", callback_data=f"verdict:confirmed:{r['id']}"),
            InlineKeyboardButton("❌ رد", callback_data=f"verdict:refuted:{r['id']}"),
        ]])
        await update.message.reply_text(
            f"بینش #{r['id']} [{r['tag']}] از {r['ts'][:10]}:\n«{r['content']}»\n\nداوریِ امروزت؟",
            reply_markup=kb,
        )


@guarded
async def on_verdict(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """فقط انسان verdict را می‌نویسد — برگشت‌ناپذیر (write-once)."""
    q = update.callback_query
    await q.answer()
    _, verdict, sid = q.data.split(":")
    try:
        db.record_verdict(int(sid), verdict)
    except db.AlreadyJudged as e:
        cur = "تأیید" if e.current == "confirmed" else "رد"
        await q.edit_message_text(
            f"{q.message.text}\n\n⚠️ این بینش قبلاً «{cur}» شده و برگشت‌ناپذیر است."
        )
        return
    except Exception:
        log.exception("record_verdict failed")
        await q.edit_message_text(f"{q.message.text}\n\n⚠️ خطا در ثبت داوری.")
        return
    label = "✅ تأیید شد" if verdict == "confirmed" else "❌ رد شد"
    await q.edit_message_text(f"{q.message.text}\n\n→ {label} (برگشت‌ناپذیر)")


# ----------------------------------------------------------------------
# مغزِ دوم — /ask (کارگاهِ روزانه) و /reflect (بازتابِ آزاد)
# ----------------------------------------------------------------------

def _gen_question():
    """سؤالِ امروز را با کلیدِ اختیاریِ CLAUDE_KEY می‌سازد (با fallback آفلاین)."""
    return ai.daily_question(
        database=db,
        api_key=os.environ.get("CLAUDE_KEY") or None,
        model=os.environ.get("LANGAR_MODEL") or None,
        system_prompt=_brain_prompt(),
    )


@guarded
async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if _CORE is not None:
        # مسیرِ CORE: مولتی‌ایجنت + لحنِ تطبیقی
        text = _CORE.get_daily_question()
        ctx.user_data["ask_domain"] = "core"
        ctx.user_data["ask_text"] = text
    else:
        q = _gen_question()
        ctx.user_data["ask_domain"] = q["domain"]
        ctx.user_data["ask_text"] = q["text"]
        text = q["text"]
    await update.message.reply_text(
        f"{text}\n\n— پاسخت را بنویس تا در کارگاه ثبت شود، یا /skip",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_ANSWER


async def ask_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    domain = ctx.user_data.get("ask_domain", "free")
    question = ctx.user_data.get("ask_text", "")
    new_id = db.add_reflection(domain, question, answer)
    ctx.user_data.pop("ask_domain", None)
    ctx.user_data.pop("ask_text", None)
    if _CORE is not None:
        try:
            _CORE.register_interaction("ask_answer", response=answer)
        except Exception:
            log.exception("core register_interaction failed")
    await update.message.reply_text(f"📝 ثبت شد در کارگاه (#{new_id}). فردا ادامه می‌دهیم.")
    return ConversationHandler.END


async def ask_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("ask_domain", None)
    ctx.user_data.pop("ask_text", None)
    await update.message.reply_text("باشد، امروز رد شد. هر وقت خواستی /ask بزن.")
    return ConversationHandler.END


@guarded
async def cmd_reflect(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args).strip()
    if not text:
        await update.message.reply_text("استفاده: /reflect <هر چیزی که می‌خواهی ثبت کنی>")
        return
    new_id = db.add_reflection("free", None, text)
    await update.message.reply_text(f"📝 بازتابِ آزاد ثبت شد (#{new_id}).")


async def morning_ping(ctx: ContextTypes.DEFAULT_TYPE):
    """پینگِ صبحگاهیِ خودکار — gate را رعایت می‌کند (در حالت halted ساکت)."""
    if db.is_halted():
        return
    owner = _owner_id()
    if not owner:
        return
    await ctx.bot.send_message(
        chat_id=int(owner),
        text="☀️ صبح بخیر. سؤالِ کارگاهِ امروز آماده است — /ask بزن.\n"
             "و اگر بینشی برای داوری داری: /recheck",
    )


# ----------------------------------------------------------------------
# /rmssd_help — راهنمای اندازه‌گیریِ درستِ RMSSD
# ----------------------------------------------------------------------

@guarded
async def cmd_rmssd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📏 اندازه‌گیریِ درستِ RMSSD (برای داده‌ی قابلِ‌مقایسه)\n\n"
        "• صبح، بلافاصله بعد از بیدارشدن.\n"
        "• قبل از قهوه، نیکوتین، غذا، حرکتِ سنگین و استرسِ گوشی.\n"
        "• هر روز با همان وضعیتِ بدن (ترجیحاً درازکش یا نشسته).\n"
        "• حداقل ۳ تا ۵ دقیقه.\n"
        "• عادی نفس بکش؛ تنفسِ عمیقِ عمدی نکن.\n"
        "• مقدار را بر حسب ms ثبت کن.\n"
        "• اگر سیگنال نویزی/لرزان/شل بود، کیفیت را پایین علامت بزن.\n\n"
        "داده‌ی خام داری؟ فواصلِ RR را با /rmssd بده تا خودم حساب کنم."
    )


# ----------------------------------------------------------------------
# /today — خلاصه‌ی امروز (+ streak)
# ----------------------------------------------------------------------

@guarded
async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    today = date.today().isoformat()
    logs = db.logs_on(today)
    ds = db.get_daily_state(today)
    streak = db.log_streak()

    parts = [f"📅 امروز ({today}) — streakِ ثبت: {streak} روز"]
    if logs:
        last = logs[-1]
        used = "بله" if last["used"] == 1 else "خیر" if last["used"] == 0 else "—"
        rm = f"{last['rmssd']:.0f} ms" if last["rmssd"] is not None else "—"
        parts.append(f"log: RMSSD={rm} · خواب={last['sleep']} · مصرف={used} · مکان={last['loc'] or '—'}")
    else:
        parts.append("هنوز log امروز ثبت نشده — /log یا /checkin")
    if ds:
        sub = []
        for k, lbl in [("mood", "حال"), ("energy", "انرژی"), ("stress", "استرس")]:
            if ds[k] is not None:
                sub.append(f"{lbl}={ds[k]}")
        if sub:
            parts.append("چک‌این: " + " · ".join(sub))
    await update.message.reply_text("\n".join(parts))


# ----------------------------------------------------------------------
# /checkin — ثبتِ سبکِ حال/انرژی/استرس (بدونِ RMSSD)
# ----------------------------------------------------------------------

def _kb15():
    return ReplyKeyboardMarkup([["1", "2", "3", "4", "5"]], one_time_keyboard=True, resize_keyboard=True)


@guarded
async def checkin_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ck"] = {}
    await update.message.reply_text(
        "چک‌اینِ سریع (هر مرحله /skip). ۱/۳ — حال‌وهوا (mood)؟ (۱..۵)",
        reply_markup=_kb15(),
    )
    return CK_MOOD


async def _ck_num(update, ctx, field, nxt_text, nxt_state):
    txt = _en(update.message.text.strip())
    if txt not in {"1", "2", "3", "4", "5"}:
        await update.message.reply_text("یک عدد بین ۱ تا ۵ بفرست یا /skip")
        return None
    ctx.user_data["ck"][field] = int(txt)
    await update.message.reply_text(nxt_text, reply_markup=_kb15())
    return nxt_state


async def ck_mood(update, ctx):
    r = await _ck_num(update, ctx, "mood", "۲/۳ — انرژی (energy)؟ (۱..۵)", CK_ENERGY)
    return CK_MOOD if r is None else r


async def ck_mood_skip(update, ctx):
    await update.message.reply_text("۲/۳ — انرژی (energy)؟ (۱..۵)", reply_markup=_kb15())
    return CK_ENERGY


async def ck_energy(update, ctx):
    r = await _ck_num(update, ctx, "energy", "۳/۳ — استرس (stress)؟ (۱..۵)", CK_STRESS)
    return CK_ENERGY if r is None else r


async def ck_energy_skip(update, ctx):
    await update.message.reply_text("۳/۳ — استرس (stress)؟ (۱..۵)", reply_markup=_kb15())
    return CK_STRESS


async def _ck_save(update, ctx):
    ck = ctx.user_data.get("ck", {})
    db.upsert_daily_state(date.today().isoformat(), **ck)
    ctx.user_data.pop("ck", None)
    shown = " · ".join(f"{k}={v}" for k, v in ck.items()) or "بدونِ مقدار"
    await update.message.reply_text(f"✅ چک‌این ثبت شد ({shown}).", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def ck_stress(update, ctx):
    txt = _en(update.message.text.strip())
    if txt not in {"1", "2", "3", "4", "5"}:
        await update.message.reply_text("یک عدد بین ۱ تا ۵ بفرست یا /skip")
        return CK_STRESS
    ctx.user_data["ck"]["stress"] = int(txt)
    return await _ck_save(update, ctx)


async def ck_stress_skip(update, ctx):
    return await _ck_save(update, ctx)


async def checkin_cancel(update, ctx):
    ctx.user_data.pop("ck", None)
    await update.message.reply_text("چک‌این لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ----------------------------------------------------------------------
# /insight_stats — آمارِ بینش‌ها
# ----------------------------------------------------------------------

@guarded
async def cmd_insight_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = db.insight_stats()
    if s["total"] == 0:
        await update.message.reply_text("هنوز بینشی ثبت نشده. با /insight شروع کن.")
        return
    rate = f"{s['confirm_rate']*100:.0f}%" if s["confirm_rate"] is not None else "—"
    await update.message.reply_text(
        f"📈 آمارِ بینش‌ها (کل: {s['total']})\n"
        f"تگ‌ها: E={s['by_tag']['E']} · S={s['by_tag']['S']} · P={s['by_tag']['P']}\n"
        f"تأیید={s['confirmed']} · رد={s['refuted']} · در انتظار={s['pending']}\n"
        f"نرخِ تأیید: {rate}\n"
        f"داوریِ عقب‌افتاده: {s['overdue']}" + (" — /recheck بزن" if s["overdue"] else "")
    )


# ----------------------------------------------------------------------
# Phase 2 — عادت‌ها (/habit /habits /done /habit_report)
# ----------------------------------------------------------------------

@guarded
async def habit_start(update, ctx):
    ctx.user_data["habit"] = {}
    await update.message.reply_text("عادتِ جدید. عنوانش؟ (/cancel برای لغو)",
                                    reply_markup=ReplyKeyboardRemove())
    return HABIT_TITLE


async def habit_title(update, ctx):
    ctx.user_data["habit"]["title"] = update.message.text.strip()
    await update.message.reply_text("نشانه/محرک (cue)؟ مثلاً «بعد از بیدارشدن» — یا /skip")
    return HABIT_CUE


async def habit_cue(update, ctx, skip=False):
    ctx.user_data["habit"]["cue"] = None if skip else update.message.text.strip()
    await update.message.reply_text("اقدام (action)؟ مثلاً «۵ دقیقه اندازه‌گیری» — یا /skip")
    return HABIT_ACTION


async def habit_action(update, ctx, skip=False):
    ctx.user_data["habit"]["action"] = None if skip else update.message.text.strip()
    await update.message.reply_text("نسخه‌ی حداقلی (روزِ سخت)؟ مثلاً «۶۰ ثانیه ساکت بنشین» — یا /skip")
    return HABIT_MIN


async def habit_min(update, ctx, skip=False):
    h = ctx.user_data["habit"]
    h["min_version"] = None if skip else update.message.text.strip()
    hid = db.add_habit(h["title"], h.get("cue"), h.get("action"), h.get("min_version"))
    ctx.user_data.pop("habit", None)
    await update.message.reply_text(f"✅ عادت #{hid} ساخته شد: {h['title']}")
    return ConversationHandler.END


async def habit_cue_skip(update, ctx):    return await habit_cue(update, ctx, skip=True)
async def habit_action_skip(update, ctx): return await habit_action(update, ctx, skip=True)
async def habit_min_skip(update, ctx):    return await habit_min(update, ctx, skip=True)


async def habit_cancel(update, ctx):
    ctx.user_data.pop("habit", None)
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


@guarded
async def cmd_habits(update, ctx):
    hs = db.list_habits(active_only=True)
    if not hs:
        await update.message.reply_text("هنوز عادتی نداری. با /habit بساز.")
        return
    lines = []
    for h in hs:
        st = db.habit_streak(h["id"])
        lines.append(f"#{h['id']} {h['title']} — streak: {st} روز")
    await update.message.reply_text("🌱 عادت‌ها:\n" + "\n".join(lines) + "\n\nثبتِ امروز: /done")


@guarded
async def cmd_done(update, ctx):
    hs = db.list_habits(active_only=True)
    if not hs:
        await update.message.reply_text("عادتی نداری. با /habit بساز.")
        return
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"✅ {h['title']}", callback_data=f"done:{h['id']}")] for h in hs]
    )
    await update.message.reply_text("کدام عادت را امروز انجام دادی؟", reply_markup=kb)


@guarded
async def on_done(update, ctx):
    q = update.callback_query
    await q.answer()
    hid = int(q.data.split(":")[1])
    db.mark_habit(hid, date.today().isoformat(), "done")
    h = db.get_habit(hid)
    st = db.habit_streak(hid)
    await q.edit_message_text(f"✅ «{h['title']}» امروز انجام شد. streak: {st} روز 🔥")


@guarded
async def cmd_habit_report(update, ctx):
    hs = db.list_habits(active_only=True)
    if not hs:
        await update.message.reply_text("عادتی نداری.")
        return
    lines = []
    for h in hs:
        st = db.habit_streak(h["id"])
        missed = db.habit_recent_missed(h["id"], 7)
        tip = ""
        if missed >= 3 and h["min_version"]:
            tip = f" — روزِ سخت؟ نسخه‌ی حداقلی: «{h['min_version']}»"
        lines.append(f"#{h['id']} {h['title']}: streak {st} · ۷روزِ اخیر {7-missed}/۷{tip}")
    await update.message.reply_text("📋 گزارشِ عادت‌ها:\n" + "\n".join(lines) +
                                    "\nبدونِ قضاوت — فقط مشاهده.")


# ----------------------------------------------------------------------
# Phase 2 — مرورها (/review_daily /review_weekly /review_monthly)
# ----------------------------------------------------------------------

_REVIEW_Q = {
    "daily": ["چه چیزی امروز انرژی داد؟", "چه چیزی انرژی را بُرد؟", "فردا یک چیز را چه تغییر می‌دهی؟"],
    "weekly": ["چه چیزی این هفته کار کرد؟", "چه چیزی آسیب زد؟", "چه چیزی ادامه یابد؟",
               "چه چیزی متوقف شود؟", "چه چیزی را بعد آزمایش کنی؟"],
    "monthly": ["الگوی بزرگِ این ماه؟", "بهترین/بدترین هفته؟", "قوی‌ترین فرضیه؟",
                "کدام عادت بماند/برود؟"],
}


def _period_bounds(rtype):
    today = date.today()
    if rtype == "weekly":
        return (today - _dt.timedelta(days=7)).isoformat(), today.isoformat()
    if rtype == "monthly":
        return (today - _dt.timedelta(days=30)).isoformat(), today.isoformat()
    return today.isoformat(), today.isoformat()


def _auto_summary(rtype):
    days = 7 if rtype == "weekly" else 30 if rtype == "monthly" else 1
    t = db.trend(days if days > 1 else 7)
    s = db.insight_stats()
    parts = []
    if t["mean_rmssd"] is not None:
        parts.append(f"RMSSD میانگین: {t['mean_rmssd']:.0f} ms ({t['count_rmssd']} رکورد)")
    parts.append(f"بینش‌ها: تأیید {s['confirmed']} · رد {s['refuted']} · در انتظار {s['pending']}")
    return " · ".join(parts)


async def _review_entry(update, ctx, rtype):
    ctx.user_data["rv"] = {"type": rtype, "qs": list(_REVIEW_Q[rtype]), "ans": [], "i": 0}
    if rtype in ("weekly", "monthly"):
        await update.message.reply_text("📆 خلاصه‌ی خودکار:\n" + _auto_summary(rtype))
    await update.message.reply_text(f"۱. {ctx.user_data['rv']['qs'][0]}  (/skip یا /cancel)",
                                    reply_markup=ReplyKeyboardRemove())
    return REVIEW_Q


@guarded
async def review_daily(update, ctx):   return await _review_entry(update, ctx, "daily")
@guarded
async def review_weekly(update, ctx):  return await _review_entry(update, ctx, "weekly")
@guarded
async def review_monthly(update, ctx): return await _review_entry(update, ctx, "monthly")


async def review_answer(update, ctx, skip=False):
    rv = ctx.user_data.get("rv")
    if not rv:
        return ConversationHandler.END
    rv["ans"].append("" if skip else update.message.text.strip())
    rv["i"] += 1
    if rv["i"] < len(rv["qs"]):
        await update.message.reply_text(f"{rv['i']+1}. {rv['qs'][rv['i']]}  (/skip)")
        return REVIEW_Q
    import json as _j
    answers = dict(zip(rv["qs"], rv["ans"]))
    ps, pe = _period_bounds(rv["type"])
    summary = _auto_summary(rv["type"]) if rv["type"] != "daily" else ""
    db.add_review(rv["type"], ps, pe, _j.dumps(answers, ensure_ascii=False), summary)
    ctx.user_data.pop("rv", None)
    await update.message.reply_text("✅ مرور ثبت شد.")
    return ConversationHandler.END


async def review_skip(update, ctx):   return await review_answer(update, ctx, skip=True)
async def review_cancel(update, ctx):
    ctx.user_data.pop("rv", None)
    await update.message.reply_text("مرور لغو شد.")
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Phase 2 — /insights (فهرست)
# ----------------------------------------------------------------------

@guarded
async def cmd_insights(update, ctx):
    rows = db.all_insights()[-10:]
    if not rows:
        await update.message.reply_text("هنوز بینشی ثبت نشده.")
        return
    mark = {"pending": "⏳", "confirmed": "✅", "refuted": "❌"}
    lines = [f"{mark.get(r['verdict'],'?')} #{r['id']} [{r['tag']}] {r['content'][:60]}" for r in rows]
    await update.message.reply_text("💡 آخرین بینش‌ها:\n" + "\n".join(lines))


# ----------------------------------------------------------------------
# Phase 3 — /coach (قاعده‌محور)
# ----------------------------------------------------------------------

@guarded
async def cmd_coach(update, ctx):
    t = db.trend(5)
    baseline = db.rmssd_baseline(30)
    recent = t["mean_rmssd"]
    rows = db.recent_logs(5)
    sleep_low = any((r["sleep"] is not None and r["sleep"] <= 2) for r in rows)
    used_recent = any(r["used"] == 1 for r in rows)
    s = db.insight_stats()
    habit_missed = max((db.habit_recent_missed(h["id"], 7) for h in db.list_habits()), default=0)
    exps = db.list_experiments("active")
    adh = None
    if exps:
        rep = db.experiment_report(exps[0]["id"])
        adh = rep.get("adherence")
    cctx = {
        "n_logs": t["count"],
        "rmssd_below_baseline": (recent is not None and baseline is not None and recent < baseline),
        "sleep_low": sleep_low,
        "used_recently": used_recent,
        "insight_confirm_rate": s["confirm_rate"],
        "insights_judged": s["confirmed"] + s["refuted"],
        "days_since_export": db.days_since_last_export(),
        "exp_active": bool(exps),
        "exp_adherence": adh,
        "habit_missed": habit_missed,
    }
    await update.message.reply_text(coach.format_report(coach.recommend(cctx)))


# ----------------------------------------------------------------------
# Phase 4 — آزمایش‌ها (/experiment /experiments /experiment_stop /experiment_report)
# ----------------------------------------------------------------------

@guarded
async def exp_start(update, ctx):
    ctx.user_data["exp"] = {}
    await update.message.reply_text("آزمایشِ N-of-1. عنوان؟ (/cancel)", reply_markup=ReplyKeyboardRemove())
    return EXP_TITLE


async def exp_title(update, ctx):
    ctx.user_data["exp"]["title"] = update.message.text.strip()
    await update.message.reply_text("فرضیه؟ مثلاً «کافئینِ دیروقت RMSSD صبح را پایین می‌آورد»")
    return EXP_HYP


async def exp_hyp(update, ctx):
    ctx.user_data["exp"]["hypothesis"] = update.message.text.strip()
    await update.message.reply_text("مداخله؟ مثلاً «بعد از ساعت ۱۴ کافئین نخور، ۱۴ روز»")
    return EXP_INT


async def exp_int(update, ctx):
    ctx.user_data["exp"]["intervention"] = update.message.text.strip()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("AB", callback_data="expdes:ab"),
        InlineKeyboardButton("یک‌روزدرمیان", callback_data="expdes:alternating"),
        InlineKeyboardButton("قبل/بعد", callback_data="expdes:before_after"),
    ]])
    await update.message.reply_text("طرحِ آزمایش؟", reply_markup=kb)
    return EXP_DESIGN


@guarded
async def exp_design(update, ctx):
    q = update.callback_query
    await q.answer()
    design = q.data.split(":")[1]
    e = ctx.user_data.get("exp", {})
    eid = db.add_experiment(e.get("title"), e.get("hypothesis"), e.get("intervention"), design)
    ctx.user_data.pop("exp", None)
    note = "" if design != "before_after" else "\n(توجه: قبل/بعد شواهدِ ضعیف می‌دهد.)"
    await q.edit_message_text(f"🧪 آزمایش #{eid} فعال شد.{note}\n"
                              "هر روز بعد از /log می‌پرسم قانون را رعایت کردی یا نه.")
    return ConversationHandler.END


async def exp_cancel(update, ctx):
    ctx.user_data.pop("exp", None)
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


@guarded
async def cmd_experiments(update, ctx):
    es = db.list_experiments("active")
    if not es:
        await update.message.reply_text("آزمایشِ فعالی نداری. با /experiment بساز.")
        return
    lines = [f"#{e['id']} {e['title']} — از {e['start_date']} ({e['design']})" for e in es]
    await update.message.reply_text("🧪 آزمایش‌های فعال:\n" + "\n".join(lines) +
                                    "\n\nگزارش: /experiment_report  ·  توقف: /experiment_stop")


@guarded
async def cmd_experiment_stop(update, ctx):
    es = db.list_experiments("active")
    if not es:
        await update.message.reply_text("آزمایشِ فعالی نیست.")
        return
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"⏹ {e['title']}", callback_data=f"expstop:{e['id']}")] for e in es]
    )
    await update.message.reply_text("کدام را متوقف کنم؟", reply_markup=kb)


@guarded
async def on_expstop(update, ctx):
    q = update.callback_query
    await q.answer()
    eid = int(q.data.split(":")[1])
    db.set_experiment_status(eid, "completed", date.today().isoformat())
    await q.edit_message_text("⏹ آزمایش تمام شد. گزارش: /experiment_report")


@guarded
async def cmd_experiment_report(update, ctx):
    es = db.list_experiments(None)
    if not es:
        await update.message.reply_text("آزمایشی نداری.")
        return
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{e['title']} ({e['status']})", callback_data=f"exprep:{e['id']}")]
         for e in es[:8]]
    )
    await update.message.reply_text("گزارشِ کدام آزمایش؟", reply_markup=kb)


@guarded
async def on_exprep(update, ctx):
    q = update.callback_query
    await q.answer()
    rep = db.experiment_report(int(q.data.split(":")[1]))
    if not rep["ok"]:
        await q.edit_message_text(rep["reason"])
        return
    bm = f"{rep['baseline_mean']:.0f}" if rep["baseline_mean"] is not None else "—"
    im = f"{rep['intervention_mean']:.0f}" if rep["intervention_mean"] is not None else "—"
    dl = f"{rep['delta']:+.0f} ms" if rep["delta"] is not None else "—"
    adh = f"{rep['adherence']*100:.0f}%" if rep["adherence"] is not None else "—"
    await q.edit_message_text(
        f"🧪 {rep['title']}\nفرضیه: {rep['hypothesis']}\n"
        f"RMSSD پایه: {bm} ({rep['n_baseline']}) · مداخله: {im} ({rep['n_intervention']})\n"
        f"اختلاف: {dl} · پایبندی: {adh}\n"
        "⚠️ این اثبات نیست؛ یک سیگنالِ شخصی است."
    )


async def on_expday(update, ctx):
    """ثبتِ رعایتِ قانونِ آزمایش برای امروز (از دکمه‌ی پایانِ /log)."""
    q = update.callback_query
    await q.answer()
    _, eid, val = q.data.split(":")
    db.mark_experiment_day(int(eid), date.today().isoformat(), val)
    lbl = {"yes": "رعایت شد", "no": "رعایت نشد", "partial": "نیمه"}.get(val, val)
    await q.edit_message_text(f"🧪 آزمایشِ امروز: {lbl}.")


# ----------------------------------------------------------------------
# Phase 5 — Muse (/muse_help /import_muse)
# ----------------------------------------------------------------------

@guarded
async def cmd_muse_help(update, ctx):
    await update.message.reply_text(
        "🧠 ورودِ Muse 2 / Mind Monitor\n\n"
        "• فقط Muse 2 مدلِ MU03 (دارای PPG) RMSSD می‌دهد؛ Muse 2016/MU02 ندارد.\n"
        "• در Mind Monitor الگوریتم‌ها/PPG را فعال کن.\n"
        "• صبح ۳ تا ۵ دقیقه ضبط کن.\n"
        "• CSV را export کن و با /import_muse بفرست.\n"
        "• اگر ستونِ RR/IBI باشد دقیق است؛ اگر فقط PPG باشد، تخمینِ تقریبی می‌زنم.\n"
        "⚠️ PPGِ Muse نویزی است — سیگنالِ شخصی، نه دقتِ بالینی."
    )


@guarded
async def muse_start(update, ctx):
    await update.message.reply_text(
        "فایلِ CSVِ Mind Monitor را همین‌جا بفرست (به‌صورتِ سند/Document). /cancel برای لغو."
    )
    return MUSE_WAIT


async def muse_receive(update, ctx):
    doc = update.message.document
    if not doc:
        await update.message.reply_text("یک فایلِ CSV بفرست یا /cancel.")
        return MUSE_WAIT
    f = await doc.get_file()
    raw = await f.download_as_bytearray()
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        await update.message.reply_text("فایل خوانده نشد.")
        return ConversationHandler.END
    res = muse.compute_from_csv(text)
    db.add_measurement_import(
        file_name=doc.file_name, source=res.get("source"),
        detected_columns=",".join(res.get("detected_columns") or [])[:500],
        sample_rate=res.get("sample_rate"), duration_sec=res.get("duration_sec"),
        rmssd=res.get("rmssd"), mean_hr=res.get("mean_hr"),
        beat_count=res.get("beat_count"), quality=res.get("quality"),
        artifact_ratio=res.get("artifact_ratio"), notes=res.get("reason"),
    )
    if not res["ok"]:
        await update.message.reply_text(f"❌ {res['reason']}")
        return ConversationHandler.END
    ctx.user_data["muse_rmssd"] = res["rmssd"]
    ctx.user_data["muse_quality"] = res["quality"]
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ استفاده در log امروز", callback_data="muse:use"),
        InlineKeyboardButton("❌ نه", callback_data="muse:discard"),
    ]])
    await update.message.reply_text(
        f"🧮 RMSSD ≈ {res['rmssd']} ms · کیفیت: {res['quality']} · ضربان: {res['beat_count']}\n"
        f"{res.get('reason') or ''}\nاز این برای log امروز استفاده کنم؟",
        reply_markup=kb,
    )
    return ConversationHandler.END


@guarded
async def on_muse(update, ctx):
    q = update.callback_query
    await q.answer()
    if q.data.endswith("discard"):
        await q.edit_message_text("باشد، استفاده نشد.")
        return
    rm = ctx.user_data.get("muse_rmssd")
    ql = ctx.user_data.get("muse_quality")
    if rm is None:
        await q.edit_message_text("مقدار پیدا نشد. دوباره /import_muse بزن.")
        return
    lid = db.add_log(rm, None, None, None, "از Muse",
                     rmssd_quality=ql, rmssd_source="muse_mind_monitor")
    await q.edit_message_text(f"✅ در log امروز ثبت شد (#{lid}، RMSSD={rm}).")


async def muse_cancel(update, ctx):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Researcher — /research /architect و اهداف /goal /goals
# ----------------------------------------------------------------------

def _fmt_research(out: dict) -> str:
    scored = out.get("source_scores") or []
    if scored:
        src_txt = "\n".join(f"  [{i+1}] ({s.get('score')}) {s.get('url')}"
                            for i, s in enumerate(scored))
    else:
        src = out.get("sources") or []
        src_txt = "\n".join(f"  [{i+1}] {u}" for i, u in enumerate(src[:5])) or "  —"
    unc = out.get("uncertainty") or {}
    unc_txt = f"\n📉 عدم‌قطعیت: {unc.get('level','?')} ({unc.get('reason','')})" if unc else ""
    prop = out.get("proposal", {})
    if isinstance(prop, dict) and prop.get("type") == "experiment":
        ptxt = prop.get("text", "")
    elif isinstance(prop, dict) and prop.get("ok"):
        ptxt = f"diff ذخیره شد: {prop.get('path')} (خودت بازبینی/اعمال کن)"
    else:
        ptxt = (prop or {}).get("reason", "—") if isinstance(prop, dict) else "—"
    rid = out.get("id")
    return (f"🎯 هدف: {out.get('target')}  ·  پژوهش #{rid}{unc_txt}\n\n"
            f"{out.get('brief')}\n\n🧪 گامِ بعد: {ptxt}\n\n"
            f"📚 منابع (با امتیازِ کیفیت):\n{src_txt}\n\n"
            f"داوریِ نسخه‌بندی‌شده: /research_verdict {rid} <confirmed|refuted>")


@guarded
async def cmd_research(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if _RESEARCHER is None:
        await update.message.reply_text("پژوهشگر فعال نیست (در main ساخته نشده).")
        return
    q = " ".join(ctx.args).strip()
    if not q:
        await update.message.reply_text("استفاده: /research <سؤال یا فرضیه>")
        return
    await update.message.reply_text("🔎 در حالِ پژوهش…")
    # اول بک‌اندِ pro؛ اگر fallback=True بود، خودکار به researcherِ محلی برگرد
    pro = pro_client.ProClient().research(q, target="armin")
    if not pro.get("fallback"):
        src = pro.get("sources") or []
        s = "\n".join(f"  • {x.get('url') if isinstance(x, dict) else x}" for x in src[:5]) or "  —"
        unc = (pro.get("uncertainty") or {}).get("level", "?")
        await update.message.reply_text(
            f"🔎 منبع: langar-pro · decision #{pro.get('decision_id')}\n\n"
            f"{pro.get('brief', '')}\n\n📉 عدم‌قطعیت: {unc}\n📚 منابع:\n{s}")
        return
    # fallback محلی
    try:
        out = _RESEARCHER.research(q, target="armin", goals=db.get_goals())
    except Exception:
        log.exception("research failed")
        await update.message.reply_text("خطا در پژوهش.")
        return
    await update.message.reply_text("🔎 منبع: محلی (local researcher)\n\n" + _fmt_research(out))


@guarded
async def cmd_architect(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if _RESEARCHER is None:
        await update.message.reply_text("پژوهشگر فعال نیست.")
        return
    goals = db.get_goals()
    if not goals:
        await update.message.reply_text("اول با /goal <هدف> چند هدف تعریف کن.")
        return
    await update.message.reply_text("🏗 در حالِ طراحیِ معماری بر اساسِ اهداف…")
    try:
        out = _RESEARCHER.propose_architecture([g["text"] for g in goals])
    except Exception:
        log.exception("architect failed")
        await update.message.reply_text("خطا در طراحی.")
        return
    src = out.get("sources") or []
    s = "\n".join(f"  [{i+1}] {u}" for i, u in enumerate(src[:5])) or "  —"
    await update.message.reply_text(f"🏗 پیشنهادِ معماری (self):\n\n{out.get('design')}\n\n📚 {s}")


@guarded
async def cmd_goal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args).strip()
    if not text:
        await update.message.reply_text("استفاده: /goal <هدفِ فعلی‌ات>")
        return
    goals = db.add_goal(text)
    await update.message.reply_text(f"🎯 هدف اضافه شد ({len(goals)} هدف). با /architect طراحیِ نو بگیر.")


@guarded
async def cmd_goals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    goals = db.get_goals()
    if not goals:
        await update.message.reply_text("هنوز هدفی نداری. /goal <متن>")
        return
    lines = [f"{i+1}. {g['text']} ({g.get('ts','')})" for i, g in enumerate(goals)]
    await update.message.reply_text("🎯 اهداف:\n" + "\n".join(lines))


@guarded
async def cmd_patch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if _PATCH is None:
        await update.message.reply_text("patch manager فعال نیست.")
        return
    issue = " ".join(ctx.args).strip()
    if not issue:
        await update.message.reply_text("استفاده: /patch <توضیحِ بهبودِ موردِ نظر>")
        return
    res = _PATCH.generate_patch(issue)
    if not res.get("ok"):
        await update.message.reply_text(f"diff تولید نشد: {res.get('reason')}")
        return
    await update.message.reply_text(
        f"🧩 diff ذخیره شد:\n{res.get('path')}\n"
        "خودت بازبینی و با git/ویرایشگر اعمال کن. بات اجرا نمی‌کند (سطح ۲).")


@guarded
async def cmd_events(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db.recent_events(15)
    if not rows:
        await update.message.reply_text("رویدادی ثبت نشده.")
        return
    lines = [f"{r['ts'][11:19]} · {r['type']}" for r in rows]
    await update.message.reply_text("🛰 رویدادهای اخیر:\n" + "\n".join(lines))


@guarded
async def cmd_contract(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from core.contract import Contract
    await update.message.reply_text(Contract.load(db).render())


@guarded
async def cmd_research_verdict(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("استفاده: /research_verdict <id> <confirmed|refuted>")
        return
    try:
        rid = int(_en(ctx.args[0]))
    except ValueError:
        await update.message.reply_text("idِ نامعتبر.")
        return
    verdict = ctx.args[1].strip().lower()
    if verdict not in ("confirmed", "refuted"):
        await update.message.reply_text("verdict باید confirmed یا refuted باشد.")
        return
    note = " ".join(ctx.args[2:])
    db.record_research_verdict(rid, verdict, note)
    hist = db.verdict_history("research", rid)
    await update.message.reply_text(
        f"✅ داوریِ پژوهش #{rid} ثبت شد: {verdict} (نسخه {len(hist)}).\n"
        "تاریخچه تغییرناپذیر است؛ توصیه‌ی فعلی به‌روز شد.")


# ----------------------------------------------------------------------
# /streak
# ----------------------------------------------------------------------

@guarded
async def cmd_streak(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = db.log_streak()
    await update.message.reply_text(f"🔥 streakِ ثبت: {s} روزِ پیاپی." if s
                                    else "هنوز streakی نداری — امروز /log یا /checkin بزن.")


# ----------------------------------------------------------------------
# AI-Lab — آزمایشگاهِ مستقلِ هوش مصنوعی
# ----------------------------------------------------------------------

async def _ailab_query(update, kind, topic):
    if _AILAB is None:
        await update.message.reply_text("AI-Lab فعال نیست (در main ساخته نشده).")
        return
    await update.message.reply_text("🤖 AI-Lab در حالِ کار…")
    try:
        out = _AILAB.query(kind, topic)
    except Exception:
        log.exception("ailab query failed")
        await update.message.reply_text("خطا در AI-Lab.")
        return
    src = out.get("sources") or []
    s = "\n".join(f"  • {u}" for u in src[:5]) or "  — (آفلاین/بدونِ منبع)"
    await update.message.reply_text(f"🤖 AI-Lab · {kind}\nموضوع: {out['topic']}\n\n"
                                    f"{out['content']}\n\n📚 منابع:\n{s}")


@guarded
async def cmd_ailab(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI-Lab | آزمایشگاهِ هوش مصنوعی\n"
        "تحقیق و طراحی درباره‌ی خودِ AI — جدا از داده‌ی شخصیِ تو.\n\n"
        "/ai_research <موضوع> — تحقیق\n"
        "/ai_digest — خلاصه‌ی پیشرفت‌ها\n"
        "/ai_architect <موضوع> — طراحی معماری\n"
        "/ai_memory <موضوع> — حافظه/بازیابی\n"
        "/ai_benchmark — طراحیِ تستِ سنجش\n"
        "/ai_safety — ریسک و محدودیت‌ها\n"
        "/ai_ideas [متن] — ثبت/فهرستِ ایده\n"
        "/ai_roadmap — نقشه راه\n"
        "/ai_propose_update <ailab|human|system> <توضیح> — پیشنهادِ diff (بدونِ اجرا)\n\n"
        "⚠️ AI-Lab فقط پیشنهاد می‌سازد؛ هیچ تغییری بدونِ تأییدِ تو اعمال نمی‌شود.")


@guarded
async def cmd_ai_research(update, ctx):
    t = " ".join(ctx.args).strip()
    if not t:
        await update.message.reply_text("استفاده: /ai_research <موضوع>")
        return
    await _ailab_query(update, "research", t)


@guarded
async def cmd_ai_digest(update, ctx):
    await _ailab_query(update, "digest", " ".join(ctx.args).strip() or "مهم‌ترین پیشرفت‌های اخیرِ AI")


@guarded
async def cmd_ai_architect(update, ctx):
    await _ailab_query(update, "architect", " ".join(ctx.args).strip() or "معماریِ AI-nativeِ LANGAR")


@guarded
async def cmd_ai_memory(update, ctx):
    await _ailab_query(update, "memory", " ".join(ctx.args).strip() or "سیستمِ حافظه و بازیابی")


@guarded
async def cmd_ai_benchmark(update, ctx):
    await _ailab_query(update, "benchmark", " ".join(ctx.args).strip() or "سنجشِ عملکردِ LANGAR")


@guarded
async def cmd_ai_safety(update, ctx):
    await _ailab_query(update, "safety", " ".join(ctx.args).strip() or "ریسک‌های امنیتیِ سیستم")


@guarded
async def cmd_ai_ideas(update, ctx):
    if _AILAB is None:
        await update.message.reply_text("AI-Lab فعال نیست.")
        return
    text = " ".join(ctx.args).strip()
    if text:
        iid = _AILAB.add_idea(text)
        await update.message.reply_text(f"💡 ایده #{iid} ثبت شد.")
        return
    ideas = _AILAB.list_ideas()
    if not ideas:
        await update.message.reply_text("هنوز ایده‌ای نیست. /ai_ideas <متن>")
        return
    await update.message.reply_text("💡 ایده‌های AI-Lab:\n"
                                    + "\n".join(f"#{r['id']} {r['text']}" for r in ideas[:10]))


@guarded
async def cmd_ai_roadmap(update, ctx):
    await _ailab_query(update, "architect",
                       "نقشه راهِ ارتقای معماریِ LANGAR در نسخه‌های بعدی (مرحله‌بندی‌شده)")


@guarded
async def cmd_ai_budget(update, ctx):
    if _BUDGET is None:
        await update.message.reply_text("BudgetManager فعال نیست.")
        return
    s = _BUDGET.status()
    rem_d = max(0.0, s["daily_limit"] - s["spent_today"])
    rem_m = max(0.0, s["monthly_limit"] - s["spent_month"])
    state = "✅ در بودجه" if s["ok"] else "⛔ بودجه تمام شده"
    await update.message.reply_text(
        f"💰 بودجه‌ی AI-Lab ({state})\n"
        f"امروز: ${s['spent_today']:.3f} از ${s['daily_limit']:.2f} (مانده ${rem_d:.3f})\n"
        f"این ماه: ${s['spent_month']:.3f} از ${s['monthly_limit']:.2f} (مانده ${rem_m:.3f})\n"
        "ℹ️ هزینه‌ها تخمینی‌اند.")


@guarded
async def cmd_ai_propose_update(update, ctx):
    if _AILAB is None:
        await update.message.reply_text("AI-Lab فعال نیست.")
        return
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "استفاده: /ai_propose_update <ailab|human|system> <توضیحِ تغییر>")
        return
    target = ctx.args[0].strip().lower()
    if target not in ("ailab", "human", "system"):
        await update.message.reply_text("target باید ailab یا human یا system باشد.")
        return
    issue = " ".join(ctx.args[1:])
    res = _AILAB.propose_update(target, issue)
    if not res.get("ok"):
        await update.message.reply_text(f"diff تولید نشد: {res.get('reason')}")
        return
    await update.message.reply_text(
        f"🧩 پیشنهادِ آپدیت برای «{target}» ساخته شد:\n{res.get('path')}\n"
        "خودت بازبینی و دستی اعمال کن. AI-Lab هرگز خودکار اعمال نمی‌کند.")


# ----------------------------------------------------------------------
# دستورِ ناشناخته — پیشنهادِ نزدیک‌ترین
# ----------------------------------------------------------------------

@owner_only
async def on_unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if db.is_halted():
        return
    await update.message.reply_text(menus.suggest_for_unknown())


# ----------------------------------------------------------------------
# CORE — /mind (مدلِ ذهنی) و /improve و /pending
# ----------------------------------------------------------------------

@guarded
async def cmd_mind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if _CORE is None:
        await update.message.reply_text("CORE فعال نیست (بات در حالتِ ساده اجرا شده).")
        return
    p = _CORE.mm.get_profile()
    st = _CORE.get_communication_style()
    await update.message.reply_text(
        "🧠 مدلِ ذهنیِ فعلی:\n"
        f"• استرس: {p.get('stress_level')}\n"
        f"• ترندِ خواب: {p.get('sleep_trend')}\n"
        f"• درگیری: {p.get('engagement')}\n"
        f"• لحنِ ترجیحی: {p.get('preferred_tone')}\n"
        f"• آخرین حوزه: {p.get('last_active_domain')}\n"
        f"لحنِ پیشنهادیِ الان: {st.tone} (حداکثر {st.max_length} خط)"
    )


@guarded
async def cmd_improve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if _CORE is None:
        await update.message.reply_text("CORE فعال نیست.")
        return
    rep = _CORE.reflect_and_improve()
    if not rep.get("ok"):
        await update.message.reply_text(f"بازتاب انجام نشد: {rep.get('reason')}")
        return
    sug = "\n".join(f"• {s}" for s in rep.get("suggestions", [])) or "بدونِ پیشنهاد."
    await update.message.reply_text(
        "🔧 بازتابِ خودبهبودی (وزن‌دهیِ امن اعمال شد؛ تغییرِ prompt فقط با تأیید):\n" + sug
    )


@guarded
async def cmd_pending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db.list_improvement_reports("pending")
    if not rows:
        await update.message.reply_text("پیشنهادِ در انتظارِ تأییدی نیست.")
        return
    import json as _j
    lines = []
    for r in rows[:5]:
        try:
            sug = _j.loads(r["suggestions_json"] or "[]")
        except Exception:
            sug = []
        lines.append(f"#{r['id']} ({r['date'][:10]}): " + ("؛ ".join(sug[:2]) or "—"))
    await update.message.reply_text("⏳ پیشنهادهای در انتظار:\n" + "\n".join(lines))


# ----------------------------------------------------------------------
# Phase 5 — privacy و حذفِ داده
# ----------------------------------------------------------------------

@guarded
async def cmd_privacy(update, ctx):
    await update.message.reply_text(
        "🔒 حریمِ خصوصی\n\n"
        "• همه‌ی داده‌ها محلی‌اند (SQLite کنارِ بات). جایی در ابر نمی‌رود.\n"
        "• فقط تو (OWNER_ID) به بات دسترسی داری.\n"
        "• پشتیبان: /export (یا /export_csv).\n"
        "• اگر CLAUDE_KEY گذاشته باشی، فقط برای ساختِ سؤالِ روزانه از Claude استفاده می‌شود؛ "
        "بدونِ کلید، کاملاً آفلاین.\n"
        "• حذفِ کاملِ داده: /delete_all_data (دومرحله‌ای، با archive)."
    )


@guarded
async def del_start(update, ctx):
    await update.message.reply_text(
        "⚠️ این همه‌ی داده‌ها را پاک می‌کند (اول یک archive گرفته می‌شود).\n"
        "برای تأیید، دقیقاً این عبارت را بفرست:\n\nDELETE LANGAR DATA\n\nیا /cancel"
    )
    return DEL_CONFIRM


async def del_confirm(update, ctx):
    if update.message.text.strip() != "DELETE LANGAR DATA":
        await update.message.reply_text("عبارت مطابقت نداشت. لغو شد.")
        return ConversationHandler.END
    import shutil
    archived = None
    try:
        src = str(db.DB_PATH)
        archived = src + "." + date.today().isoformat() + ".bak"
        shutil.copyfile(src, archived)
    except Exception:
        log.exception("archive failed")
    db.wipe_all_data()
    msg = "🗑 همه‌ی داده‌ها پاک شد."
    if archived:
        msg += " (یک archive کنارِ دیتابیس ذخیره شد.)"
    await update.message.reply_text(msg)
    return ConversationHandler.END


async def del_cancel(update, ctx):
    await update.message.reply_text("لغو شد. چیزی پاک نشد.")
    return ConversationHandler.END


# ----------------------------------------------------------------------
# /export — خروجی JSON
# ----------------------------------------------------------------------

@guarded
async def cmd_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import json
    import tempfile
    from datetime import datetime

    def rows_to_list(rows):
        return [dict(r) for r in rows]

    data = {
        "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "logs": rows_to_list(db.all_logs()),
        "insights": rows_to_list(db.all_insights()),
        "reflections": rows_to_list(db.all_reflections()),
        "daily_state": rows_to_list(db.all_daily_state()),
        "schema_version": db.schema_version(),
    }
    payload = json.dumps(data, ensure_ascii=False, indent=2)

    fname = f"langar_export_{date.today().isoformat()}.json"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write(payload)
        path = f.name
    with open(path, "rb") as fh:
        await update.message.reply_document(
            document=fh, filename=fname,
            caption=f"📤 خروجی LANGAR · {len(data['logs'])} log · {len(data['insights'])} بینش",
        )
    os.remove(path)
    db.mark_exported()


@guarded
async def cmd_export_csv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import csv as _csv
    import io
    import tempfile
    import zipfile

    tables = {
        "logs.csv": db.all_logs(),
        "insights.csv": db.all_insights(),
        "reflections.csv": db.all_reflections(),
        "daily_state.csv": db.all_daily_state(),
        "habits.csv": db.list_habits(active_only=False),
        "habit_logs.csv": db.all_habit_logs(),
        "experiments.csv": db.all_experiments(),
        "reviews.csv": db.all_reviews(),
    }
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        zpath = tf.name
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name, rows in tables.items():
            buf = io.StringIO()
            if rows:
                w = _csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
                w.writeheader()
                for r in rows:
                    w.writerow(dict(r))
            z.writestr(name, buf.getvalue())
    with open(zpath, "rb") as fh:
        await update.message.reply_document(
            document=fh, filename=f"langar_csv_{date.today().isoformat()}.zip",
            caption="📤 خروجی CSV (همه‌ی جدول‌ها)",
        )
    os.remove(zpath)
    db.mark_exported()


# ----------------------------------------------------------------------
# error handler + post_init (منوی دستورها)
# ----------------------------------------------------------------------

async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.exception("خطای مدیریت‌نشده", exc_info=ctx.error)


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("menu", "منوی اصلی"),
        BotCommand("log", "ثبت RMSSD و تگ‌های امروز"),
        BotCommand("checkin", "چک‌این سریع حال/انرژی/استرس"),
        BotCommand("streak", "پیوستگی روزهای ثبت"),
        BotCommand("today", "خلاصه امروز + streak"),
        BotCommand("ailab", "آزمایشگاه هوش مصنوعی"),
        BotCommand("rmssd", "محاسبه RMSSD از داده خام"),
        BotCommand("rmssd_help", "راهنمای اندازه‌گیری"),
        BotCommand("trend", "ترند N روز اخیر"),
        BotCommand("ask", "سؤال کارگاه امروز"),
        BotCommand("reflect", "ثبت بازتاب آزاد"),
        BotCommand("insight", "ثبت بینش با تگ E/S/P"),
        BotCommand("recheck", "داوری بینش‌های امروز"),
        BotCommand("insights", "فهرست بینش‌ها"),
        BotCommand("insight_stats", "آمار بینش‌ها"),
        BotCommand("habit", "ساخت عادت"),
        BotCommand("habits", "فهرست عادت‌ها"),
        BotCommand("done", "ثبت انجامِ عادت"),
        BotCommand("habit_report", "گزارش عادت‌ها"),
        BotCommand("review_daily", "مرور روزانه"),
        BotCommand("review_weekly", "مرور هفتگی"),
        BotCommand("review_monthly", "مرور ماهانه"),
        BotCommand("experiment", "ساخت آزمایش N-of-1"),
        BotCommand("experiments", "فهرست آزمایش‌ها"),
        BotCommand("experiment_report", "گزارش آزمایش"),
        BotCommand("experiment_stop", "توقف آزمایش"),
        BotCommand("coach", "پیشنهاد آرام داده‌محور"),
        BotCommand("mind", "مدل ذهنی فعلی"),
        BotCommand("improve", "بازتاب خودبهبودی"),
        BotCommand("research", "پژوهش وب + آزمایش"),
        BotCommand("architect", "طراحی معماری بر اساس اهداف"),
        BotCommand("goal", "افزودن هدف"),
        BotCommand("goals", "فهرست اهداف"),
        BotCommand("patch", "تولید diff بهبود (سطح ۲)"),
        BotCommand("muse_help", "راهنمای Muse"),
        BotCommand("import_muse", "ورود CSV موز"),
        BotCommand("export", "خروجی JSON"),
        BotCommand("export_csv", "خروجی CSV"),
        BotCommand("privacy", "حریم خصوصی"),
        BotCommand("status", "وضعیت و آخرین log"),
        BotCommand("halt", "توقف فوری"),
        BotCommand("resume", "ادامه"),
    ])


# ----------------------------------------------------------------------
# ثبت همه‌ی هندلرها
# ----------------------------------------------------------------------

def register(app: Application) -> None:
    conv = ConversationHandler(
        entry_points=[CommandHandler("log", log_start)],
        states={
            RMSSD: [
                CommandHandler("skip", log_rmssd_skip),
                MessageHandler(filters.TEXT & ~filters.COMMAND, log_rmssd),
            ],
            SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_sleep)],
            USED: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_used)],
            LOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_loc)],
            NOTE: [
                CommandHandler("skip", log_note_skip),
                MessageHandler(filters.TEXT & ~filters.COMMAND, log_note),
            ],
        },
        fallbacks=[CommandHandler("cancel", log_cancel)],
        name="log_conversation",
        persistent=True,   # وضعیتِ گفتگوی نیمه‌تمام پس از ری‌استارت حفظ می‌شود
    )

    ask_conv = ConversationHandler(
        entry_points=[CommandHandler("ask", cmd_ask)],
        states={
            ASK_ANSWER: [
                CommandHandler("skip", ask_skip),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_answer),
            ],
        },
        fallbacks=[CommandHandler("cancel", ask_skip)],
        name="ask_conversation",
        persistent=True,
    )

    checkin_conv = ConversationHandler(
        entry_points=[CommandHandler("checkin", checkin_start)],
        states={
            CK_MOOD: [CommandHandler("skip", ck_mood_skip),
                      MessageHandler(filters.TEXT & ~filters.COMMAND, ck_mood)],
            CK_ENERGY: [CommandHandler("skip", ck_energy_skip),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, ck_energy)],
            CK_STRESS: [CommandHandler("skip", ck_stress_skip),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, ck_stress)],
        },
        fallbacks=[CommandHandler("cancel", checkin_cancel)],
        name="checkin_conversation",
        persistent=True,
    )

    habit_conv = ConversationHandler(
        entry_points=[CommandHandler("habit", habit_start)],
        states={
            HABIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, habit_title)],
            HABIT_CUE: [CommandHandler("skip", habit_cue_skip),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, habit_cue)],
            HABIT_ACTION: [CommandHandler("skip", habit_action_skip),
                           MessageHandler(filters.TEXT & ~filters.COMMAND, habit_action)],
            HABIT_MIN: [CommandHandler("skip", habit_min_skip),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, habit_min)],
        },
        fallbacks=[CommandHandler("cancel", habit_cancel)],
        name="habit_conversation", persistent=True,
    )

    review_conv = ConversationHandler(
        entry_points=[
            CommandHandler("review_daily", review_daily),
            CommandHandler("review_weekly", review_weekly),
            CommandHandler("review_monthly", review_monthly),
        ],
        states={
            REVIEW_Q: [CommandHandler("skip", review_skip),
                       MessageHandler(filters.TEXT & ~filters.COMMAND, review_answer)],
        },
        fallbacks=[CommandHandler("cancel", review_cancel)],
        name="review_conversation", persistent=True,
    )

    exp_conv = ConversationHandler(
        entry_points=[CommandHandler("experiment", exp_start)],
        states={
            EXP_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, exp_title)],
            EXP_HYP: [MessageHandler(filters.TEXT & ~filters.COMMAND, exp_hyp)],
            EXP_INT: [MessageHandler(filters.TEXT & ~filters.COMMAND, exp_int)],
            EXP_DESIGN: [CallbackQueryHandler(exp_design, pattern=r"^expdes:")],
        },
        fallbacks=[CommandHandler("cancel", exp_cancel)],
        name="experiment_conversation", persistent=True,
    )

    muse_conv = ConversationHandler(
        entry_points=[CommandHandler("import_muse", muse_start)],
        states={
            MUSE_WAIT: [MessageHandler(filters.Document.ALL, muse_receive)],
        },
        fallbacks=[CommandHandler("cancel", muse_cancel)],
        name="muse_conversation", persistent=True,
    )

    del_conv = ConversationHandler(
        entry_points=[CommandHandler("delete_all_data", del_start)],
        states={
            DEL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_confirm)],
        },
        fallbacks=[CommandHandler("cancel", del_cancel)],
        name="delete_conversation", persistent=True,
    )

    for c in (conv, ask_conv, checkin_conv, habit_conv, review_conv, exp_conv, muse_conv, del_conv):
        app.add_handler(c)

    for name, fn in [
        ("start", cmd_start), ("menu", cmd_menu), ("help_all", cmd_start_full),
        ("streak", cmd_streak), ("today", cmd_today),
        ("ailab", cmd_ailab), ("ai_research", cmd_ai_research), ("ai_digest", cmd_ai_digest),
        ("ai_architect", cmd_ai_architect), ("ai_memory", cmd_ai_memory),
        ("ai_benchmark", cmd_ai_benchmark), ("ai_safety", cmd_ai_safety),
        ("ai_ideas", cmd_ai_ideas), ("ai_roadmap", cmd_ai_roadmap),
        ("ai_budget", cmd_ai_budget), ("ai_propose_update", cmd_ai_propose_update),
        ("rmssd", cmd_rmssd), ("rmssd_help", cmd_rmssd_help),
        ("trend", cmd_trend), ("reflect", cmd_reflect),
        ("insight", cmd_insight), ("recheck", cmd_recheck),
        ("insights", cmd_insights), ("insight_stats", cmd_insight_stats),
        ("habits", cmd_habits), ("done", cmd_done), ("habit_report", cmd_habit_report),
        ("coach", cmd_coach),
        ("experiments", cmd_experiments), ("experiment_stop", cmd_experiment_stop),
        ("experiment_report", cmd_experiment_report),
        ("muse_help", cmd_muse_help),
        ("mind", cmd_mind), ("improve", cmd_improve), ("pending", cmd_pending),
        ("research", cmd_research), ("architect", cmd_architect),
        ("research_verdict", cmd_research_verdict), ("contract", cmd_contract),
        ("goal", cmd_goal), ("goals", cmd_goals),
        ("patch", cmd_patch), ("events", cmd_events),
        ("export", cmd_export), ("export_csv", cmd_export_csv),
        ("privacy", cmd_privacy),
        ("status", cmd_status), ("halt", cmd_halt), ("resume", cmd_resume),
    ]:
        app.add_handler(CommandHandler(name, fn))

    app.add_handler(CallbackQueryHandler(on_tag, pattern=r"^tag:"))
    app.add_handler(CallbackQueryHandler(on_verdict, pattern=r"^verdict:"))
    app.add_handler(CallbackQueryHandler(on_done, pattern=r"^done:"))
    app.add_handler(CallbackQueryHandler(on_expstop, pattern=r"^expstop:"))
    app.add_handler(CallbackQueryHandler(on_exprep, pattern=r"^exprep:"))
    app.add_handler(CallbackQueryHandler(on_expday, pattern=r"^expday:"))
    app.add_handler(CallbackQueryHandler(on_muse, pattern=r"^muse:"))
    app.add_handler(CallbackQueryHandler(on_menu, pattern=r"^menu:"))
    # دستورِ ناشناخته — باید آخرین هندلر باشد تا فقط دستورهای بی‌مطابقت را بگیرد
    app.add_handler(MessageHandler(filters.COMMAND, on_unknown))
    app.add_error_handler(on_error)

    # پینگِ صبحگاهیِ خودکار (نیازمندِ نصبِ extra «job-queue»)
    jq = getattr(app, "job_queue", None)
    if jq is not None:
        try:
            hour = int(os.environ.get("LANGAR_PING_HOUR", "8"))
        except ValueError:
            hour = 8
        jq.run_daily(morning_ping, time=_dt.time(hour=hour, minute=0))
        log.info("پینگِ صبحگاهی ساعتِ %02d:00 تنظیم شد.", hour)
    else:
        log.info("JobQueue نصب نیست؛ پینگِ صبحگاهی غیرفعال است "
                 "(برای فعال‌سازی: python-telegram-bot[job-queue]).")
