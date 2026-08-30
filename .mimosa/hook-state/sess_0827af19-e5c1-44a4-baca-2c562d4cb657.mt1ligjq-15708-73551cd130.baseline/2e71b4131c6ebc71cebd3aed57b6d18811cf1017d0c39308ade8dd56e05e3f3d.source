#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
silabi_bot.py — رباتِ خود-شناسیِ کم‌اصطکاکِ تلگرام برای یک ذهنِ پرورودی و کم‌فیلتر («سیلابی»).

دو سیگنالِ به‌هم‌پیوسته را دنبال می‌کند — انرژی و ایده — و الگوها را به تو بازمی‌تاباند تا:
خودت را بشناسی، بهتر عمل کنی، و نسوزی.

اصلِ طراحی: ثبت باید چند ثانیه طول بکشد، نه چند دقیقه.
یک عددِ تنها = ثبتِ انرژی. هر متنِ دیگر = ثبتِ ایده، که خودکار با انرژیِ همان لحظه برچسب می‌خورد.

----------------------------------------------------------------------
لایه‌ی «بازتابِ تطبیقی» (همان خودبهبوددهندگی):
ربات با جمع‌شدنِ داده، مدلی شخصی از تو می‌سازد و آن را به‌مرور به‌روزرسانی می‌کند:
  • پنجره‌ی اوجِ انرژیِ تو در شبانه‌روز
  • سطحِ انرژی‌ای که ایده‌های «درستِ» تو در آن می‌آیند
  • آستانه‌ی شخصیِ سوختنِ تو (نه یک عددِ ثابت برای همه)
نِی‌زدن‌ها (nudges) بر اساسِ همین مدلِ یادگرفته‌شده شخصی می‌شوند، نه قاعده‌های ثابت.
مدل با هر ثبت، آرام واسنجی می‌شود. این «خودبهبوددهندگیِ» امن است:
ربات از دادهٔ تو یاد می‌گیرد، ولی هرگز کدِ خودش را بازنویسی نمی‌کند.
----------------------------------------------------------------------

نصب:
  ۱. در تلگرام با @BotFather حرف بزن → /newbot → توکن را کپی کن.
  ۲. pip install "python-telegram-bot>=20" --break-system-packages
  ۳. export TELEGRAM_TOKEN="توکنِ تو"
  ۴. python3 silabi_bot.py

روی Orange Pi هم خوب اجرا می‌شود. داده در یک فایلِ محلیِ SQLite می‌ماند (silabi.db).

دستورها:
  <عدد ۱ تا ۵>     ثبتِ انرژی/تمرکزِ همین حالا
  <هر متنِ دیگر>   ثبتِ ایده/شهود (خودکار با انرژیِ فعلی برچسب می‌خورد)
  /done            آخرین ایده‌ات «درست از آب درآمد»
  /noise           آخرین ایده‌ات «نویز بود»
  /eat <چی>        ثبتِ یک نوبتِ خوردن + محرکش (نه کالری — فقط الگو)
  /now             آیا الانْ وقتِ خوبی برای کارِ عمیق است؟ (بر اساسِ مدلِ تو)
  /today           خلاصه‌ی امروز
  /mirror          آینه‌ی هفتگی: انرژی، ایده، دقتِ شهود، پیوندِ غذا-فکر
  /learned         ربات تا حالا چه از تو یاد گرفته است
  /help            همین راهنما

نکته درباره‌ی /eat: این عمداً «الگو» را دنبال می‌کند (کِی و چرا موقعِ فکرِ عمیق می‌خوری)،
نه شمارشِ کالری یا هدفِ وزن. هدف، بینش به پیوندِ غذا↔فکر است، نه محدودیت.
برای هدف‌های دقیقِ تغذیه، یک متخصص.
"""

import os
import sqlite3
import datetime as dt
import statistics

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# پیش‌فرض: فایلِ پایگاه‌داده کنارِ خودِ کد ذخیره شود
# (تا داده در پوشه‌ی پروژه بماند و Claude در گفت‌وگوهای بعد بتواند بخواندش)
_HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("SILABI_DB", os.path.join(_HERE, "silabi.db"))
TOKEN = os.environ.get("<REDACTED-TELEGRAM-TOKEN>")

# حداقل دادهٔ لازم پیش از آنکه ربات به یافته‌هایش اعتماد کند (تا نِی‌زدنِ زودهنگام نزند)
MIN_ENERGY_POINTS = 8
MIN_JUDGED_IDEAS = 4


# --------------------------------------------------------------------------- #
#  پایگاه‌داده
# --------------------------------------------------------------------------- #
def db():
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS energy(
            id INTEGER PRIMARY KEY, user INTEGER, level INTEGER, ts TEXT)"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS ideas(
            id INTEGER PRIMARY KEY, user INTEGER, text TEXT, energy_at INTEGER,
            ts TEXT, verdict TEXT)"""  # verdict: NULL | 'right' | 'noise'
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS food(
            id INTEGER PRIMARY KEY, user INTEGER, what TEXT, trigger TEXT,
            energy_at INTEGER, ts TEXT)"""
    )
    return con


def latest_energy(con, user):
    row = con.execute(
        "SELECT level FROM energy WHERE user=? ORDER BY id DESC LIMIT 1", (user,)
    ).fetchone()
    return row[0] if row else None


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
#  لایه‌ی بازتابِ تطبیقی — مدلِ یادگیرنده از روی همه‌ی داده‌ی کاربر
# --------------------------------------------------------------------------- #
def learn_profile(con, user):
    """
    یک مدلِ شخصی از روی *همه‌ی* داده‌ی کاربر می‌سازد و برمی‌گرداند.
    هیچ‌چیز را در دیسک نمی‌نویسد؛ هر بار تازه محاسبه می‌شود تا همیشه به‌روز باشد.

    خروجی یک dict است؛ کلیدهایی که داده‌ی کافی ندارند None می‌مانند.
    """
    profile = {
        "n_energy": 0,
        "energy_mean": None,
        "energy_sd": None,
        "burnout_threshold": 2,   # پیش‌فرضِ ثابت تا وقتی داده‌ی کافی بیاید
        "peak_hour": None,
        "peak_hour_avg": None,
        "low_hour": None,
        "best_idea_energy": None,  # انرژی‌ای که ایده‌های درست در آن می‌آیند
        "intuition_acc": None,
        "n_judged": 0,
    }

    # ---- انرژی ----
    en = con.execute(
        "SELECT level, ts FROM energy WHERE user=?", (user,)
    ).fetchall()
    profile["n_energy"] = len(en)

    if len(en) >= 2:
        levels = [r[0] for r in en]
        profile["energy_mean"] = statistics.mean(levels)
        profile["energy_sd"] = statistics.pstdev(levels)

    if len(en) >= MIN_ENERGY_POINTS:
        # آستانه‌ی شخصیِ سوختن: یک انحرافِ معیار زیرِ میانگینِ خودِ کاربر
        # (محدود بین ۱ و ۳ تا منطقی بماند)
        thr = profile["energy_mean"] - profile["energy_sd"]
        profile["burnout_threshold"] = max(1, min(3, round(thr)))

        # پنجره‌ی اوج/افتِ انرژی بر حسبِ ساعتِ شبانه‌روز
        by_hour = {}
        for lvl, ts in en:
            try:
                h = dt.datetime.fromisoformat(ts).hour
            except ValueError:
                continue
            by_hour.setdefault(h, []).append(lvl)
        # فقط ساعت‌هایی که دستِ‌کم ۲ نمونه دارند قابل‌اعتمادند
        hour_avg = {h: statistics.mean(v) for h, v in by_hour.items() if len(v) >= 2}
        if hour_avg:
            profile["peak_hour"] = max(hour_avg, key=hour_avg.get)
            profile["peak_hour_avg"] = hour_avg[profile["peak_hour"]]
            profile["low_hour"] = min(hour_avg, key=hour_avg.get)

    # ---- ایده‌ها و دقتِ شهود ----
    ideas = con.execute(
        "SELECT energy_at, verdict FROM ideas WHERE user=?", (user,)
    ).fetchall()
    judged = [i for i in ideas if i[1] in ("right", "noise")]
    right = [i for i in judged if i[1] == "right"]
    profile["n_judged"] = len(judged)

    if len(judged) >= MIN_JUDGED_IDEAS:
        profile["intuition_acc"] = len(right) / len(judged)
        right_e = [i[0] for i in right if i[0]]
        if right_e:
            profile["best_idea_energy"] = statistics.mean(right_e)

    return profile


# --------------------------------------------------------------------------- #
#  متن‌ها
# --------------------------------------------------------------------------- #
HELP = (
    "🌊 *رباتِ سیلابی*\n\n"
    "• یک عدد ۱ تا ۵ بفرست → انرژی/تمرکزِ الان ثبت می‌شود\n"
    "• هر متنِ دیگر → یک ایده/شهود ثبت می‌شود (با انرژیِ همان لحظه)\n\n"
    "`/done` ـ آخرین ایده‌ات درست از آب درآمد\n"
    "`/noise` ـ آخرین ایده‌ات نویز بود\n"
    "`/eat چی خوردی` ـ ثبتِ الگوی غذا (نه کالری — فقط الگو و محرک)\n"
    "`/now` ـ آیا الان وقتِ خوبی برای کارِ عمیق است؟\n"
    "`/today` ـ خلاصه‌ی امروز\n"
    "`/mirror` ـ آینه‌ی هفتگی (الگوهایت)\n"
    "`/learned` ـ ربات تا حالا چه از تو یاد گرفته\n\n"
    "_هرچه بیشتر ثبت کنی، آینه دقیق‌تر می‌شود. ربات از دادهٔ تو یاد می‌گیرد._"
)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP, parse_mode="Markdown")


# --------------------------------------------------------------------------- #
#  ثبتِ متن (انرژی یا ایده)
# --------------------------------------------------------------------------- #
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    text = update.message.text.strip()
    con = db()

    # عددِ تنهای ۱ تا ۵ ⇒ ثبتِ انرژی
    if text.isdigit() and 1 <= int(text) <= 5:
        lvl = int(text)
        con.execute(
            "INSERT INTO energy(user,level,ts) VALUES(?,?,?)", (user, lvl, now())
        )
        con.commit()
        bar = "▁▃▅▇█"[lvl - 1]
        msg = f"⚡ انرژی ثبت شد: {lvl}/5 {bar}"

        # نِی‌زدنِ سوختن — تطبیقی: آستانه از مدلِ خودِ کاربر می‌آید
        prof = learn_profile(con, user)
        thr = prof["burnout_threshold"]
        lows = con.execute(
            "SELECT level FROM energy WHERE user=? ORDER BY id DESC LIMIT 3", (user,)
        ).fetchall()
        if len(lows) == 3 and all(l[0] <= thr for l in lows):
            personal = ""
            if prof["n_energy"] >= MIN_ENERGY_POINTS:
                personal = f" (آستانه‌ی شخصیِ تو: {thr}/5)"
            msg += (
                f"\n\n🛑 سه ثبتِ پایینِ پشت‌سرهم{personal}. این الگوی سوختن است.\n"
                "وقتِ بازیابیِ واقعی است — خواب، طبیعت، تنهاییِ کم‌محرک. "
                "سیل را امروز هدایت نکن، فقط بگذار فروکش کند."
            )
        await update.message.reply_text(msg)
        con.close()
        return

    # وگرنه ⇒ ایده، خودکار با انرژیِ فعلی برچسب می‌خورد
    e = latest_energy(con, user)
    con.execute(
        "INSERT INTO ideas(user,text,energy_at,ts,verdict) VALUES(?,?,?,?,NULL)",
        (user, text, e, now()),
    )
    con.commit()

    tag = f" (انرژی الان: {e}/5)" if e else " (انرژی هنوز ثبت نشده — یک عدد بفرست)"
    reply = f"💡 ایده ثبت شد{tag}\nذهنت سبک شد. ادامه بده."

    # بازتابِ تطبیقی: اگر مدل می‌داند ایده‌های درستِ تو در چه انرژی‌ای می‌آیند،
    # و انرژیِ الان خیلی پایین‌تر است، آرام یادآوری کن.
    prof = learn_profile(con, user)
    if e and prof["best_idea_energy"] is not None:
        best = prof["best_idea_energy"]
        if e <= best - 1.5:
            reply += (
                f"\n\n🪞 ایده‌های درستِ تو معمولاً حولِ انرژیِ ~{best:.1f}/5 می‌آیند، "
                f"و الان {e}/5 هستی. شاید این بیشتر نشخوار باشد تا شهود — "
                "بنویسش و فعلاً رهایش کن."
            )
    con.close()
    await update.message.reply_text(reply)


# --------------------------------------------------------------------------- #
#  داوریِ ایده‌ها
# --------------------------------------------------------------------------- #
async def verdict(update, ctx, value):
    user = update.effective_user.id
    con = db()
    row = con.execute(
        "SELECT id FROM ideas WHERE user=? AND verdict IS NULL ORDER BY id DESC LIMIT 1",
        (user,),
    ).fetchone()
    if not row:
        await update.message.reply_text("ایده‌ای برای علامت‌زدن پیدا نشد.")
        con.close()
        return
    con.execute("UPDATE ideas SET verdict=? WHERE id=?", (value, row[0]))
    con.commit()
    con.close()
    label = "درست ✅" if value == "right" else "نویز ⚪"
    await update.message.reply_text(f"آخرین ایده علامت خورد: {label}")


async def done(update, ctx):
    await verdict(update, ctx, "right")


async def noise(update, ctx):
    await verdict(update, ctx, "noise")


# --------------------------------------------------------------------------- #
#  ثبتِ غذا (الگو، نه کالری)
# --------------------------------------------------------------------------- #
async def eat(update, ctx):
    user = update.effective_user.id
    what = " ".join(ctx.args).strip() if ctx.args else ""
    if not what:
        await update.message.reply_text(
            "چی خوردی را بعد از دستور بنویس. مثال:\n`/eat آجیل موقعِ کارِ فکری`",
            parse_mode="Markdown",
        )
        return
    con = db()
    e = latest_energy(con, user)
    con.execute(
        "INSERT INTO food(user,what,trigger,energy_at,ts) VALUES(?,?,?,?,?)",
        (user, what, None, e, now()),
    )
    con.commit()
    con.close()
    tag = f" (انرژی الان: {e}/5)" if e else ""
    await update.message.reply_text(
        f"🍽 ثبت شد{tag}\n"
        "بدونِ قضاوت. این فقط برای دیدنِ الگوست — کِی و چرا، نه چقدر."
    )


# --------------------------------------------------------------------------- #
#  /now — آیا الان وقتِ خوبی برای کارِ عمیق است؟ (تطبیقی)
# --------------------------------------------------------------------------- #
async def now_cmd(update, ctx):
    user = update.effective_user.id
    con = db()
    prof = learn_profile(con, user)
    e = latest_energy(con, user)
    con.close()

    if prof["peak_hour"] is None:
        await update.message.reply_text(
            "هنوز داده‌ی کافی ندارم تا پنجره‌ی اوجت را بشناسم.\n"
            "چند روز انرژی ثبت کن (یک عدد ۱ تا ۵ در ساعت‌های مختلف)، بعد می‌توانم بگویم."
        )
        return

    cur_h = dt.datetime.now().hour
    peak = prof["peak_hour"]
    # فاصله‌ی دایره‌ای تا پنجره‌ی اوج (ساعت)
    dist = min((cur_h - peak) % 24, (peak - cur_h) % 24)

    lines = [f"⏰ ساعتِ {cur_h}:00"]
    if e:
        lines.append(f"انرژیِ ثبت‌شده‌ی فعلی: {e}/5")

    if dist <= 1:
        lines.append(
            f"\n✅ این نزدیکِ پنجره‌ی اوجِ توست (~{peak}:00). "
            "اگر کارِ عمیق یا تصمیمِ مهم داری، حالا بهترین زمان است."
        )
    elif prof["low_hour"] is not None and abs(cur_h - prof["low_hour"]) <= 1:
        lines.append(
            f"\n⚪ این نزدیکِ افتِ معمولِ توست (~{prof['low_hour']}:00). "
            "کارِ سبک یا بازیابی بهتر است تا تصمیمِ سنگین."
        )
    else:
        lines.append(
            f"\nپنجره‌ی اوجِ تو حولِ ~{peak}:00 است. "
            f"اگر می‌توانی، کارِ مهم را به آن ساعت موکول کن."
        )
    await update.message.reply_text("\n".join(lines))


# --------------------------------------------------------------------------- #
#  /today — خلاصه‌ی امروز
# --------------------------------------------------------------------------- #
async def today(update, ctx):
    user = update.effective_user.id
    con = db()
    d = dt.date.today().isoformat()
    en = con.execute(
        "SELECT level FROM energy WHERE user=? AND ts LIKE ?", (user, d + "%")
    ).fetchall()
    ideas = con.execute(
        "SELECT text, energy_at FROM ideas WHERE user=? AND ts LIKE ?", (user, d + "%")
    ).fetchall()
    con.close()

    levels = [r[0] for r in en]
    avg = sum(levels) / len(levels) if levels else None
    lines = [
        "📅 *امروز*",
        f"انرژی: {len(levels)} ثبت" + (f"، میانگین {avg:.1f}/5" if avg else ""),
        f"ایده‌ها: {len(ideas)}",
    ]
    for t, e in ideas[:8]:
        lines.append(f"  • {t[:50]}" + (f" (⚡{e})" if e else ""))
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# --------------------------------------------------------------------------- #
#  /mirror — آینه‌ی هفتگی
# --------------------------------------------------------------------------- #
async def mirror(update, ctx):
    user = update.effective_user.id
    con = db()
    week_ago = (dt.datetime.now() - dt.timedelta(days=7)).isoformat()

    # انرژی بر حسبِ ساعتِ شبانه‌روز ⇒ پنجره‌ی اوج
    rows = con.execute(
        "SELECT level, ts FROM energy WHERE user=? AND ts>=?", (user, week_ago)
    ).fetchall()
    by_hour = {}
    for lvl, ts in rows:
        try:
            h = dt.datetime.fromisoformat(ts).hour
        except ValueError:
            continue
        by_hour.setdefault(h, []).append(lvl)
    peak_line = "داده‌ی کافی نیست"
    if by_hour:
        hour_avg = {h: sum(v) / len(v) for h, v in by_hour.items()}
        peak_h = max(hour_avg, key=hour_avg.get)
        low_h = min(hour_avg, key=hour_avg.get)
        peak_line = (
            f"اوجِ انرژی حولِ ساعت {peak_h}:00 ({hour_avg[peak_h]:.1f}/5)\n"
            f"افتِ انرژی حولِ ساعت {low_h}:00 ({hour_avg[low_h]:.1f}/5)"
        )

    # ایده‌ها + دقتِ شهود
    ideas = con.execute(
        "SELECT energy_at, verdict FROM ideas WHERE user=? AND ts>=?", (user, week_ago)
    ).fetchall()
    n_ideas = len(ideas)
    judged = [i for i in ideas if i[1] in ("right", "noise")]
    right = [i for i in judged if i[1] == "right"]
    acc = len(right) / len(judged) if judged else None

    # ایده‌های درست در چه انرژی‌ای می‌آیند؟
    right_e = [i[0] for i in right if i[0]]
    best_e = sum(right_e) / len(right_e) if right_e else None

    # پیوندِ غذا↔فکر: خوردن‌ها در چه انرژی‌ای خوشه می‌شوند؟
    foods = con.execute(
        "SELECT energy_at FROM food WHERE user=? AND ts>=?", (user, week_ago)
    ).fetchall()
    food_e = [f[0] for f in foods if f[0]]
    food_line = None
    if len(food_e) >= 3:
        avg_food_e = sum(food_e) / len(food_e)
        high = sum(1 for x in food_e if x >= 4)
        share_high = high / len(food_e)
        food_line = (
            f"🍽 خوردن‌ها: {len(foods)} بار، میانگینِ انرژیِ لحظه‌ی خوردن "
            f"{avg_food_e:.1f}/5"
        )
        if share_high >= 0.5:
            food_line += (
                f"\n   {share_high*100:.0f}% موقعِ انرژیِ بالا خوردی — یعنی الگویت با "
                "کارِ فکری/شهود گره خورده، نه با گرسنگیِ واقعی."
            )
            food_line += (
                "\n   این خودآگاهی است، نه ایراد. حالا که دیدی‌اش، می‌توانی موقعِ اوجِ "
                "فکری یک گزینه‌ی سبک و آماده کنارت بگذاری."
            )

    con.close()

    lines = ["🪞 *آینه‌ی هفتگی*\n", peak_line, "", f"ایده‌های ثبت‌شده: {n_ideas}"]
    if acc is not None:
        lines.append(f"دقتِ شهود: {acc*100:.0f}% ({len(right)} از {len(judged)} درست)")
        if acc < 0.5:
            lines.append(
                "⚠️ بیشترِ شهودت این هفته نویز بود — عادی است، با ثبتِ بیشتر واسنجی می‌شود."
            )
    if best_e is not None:
        lines.append(f"\n✨ بهترین ایده‌هایت در انرژیِ ~{best_e:.1f}/5 آمدند.")
        lines.append("کارِ خلاقانه را بگذار روی همین سطحِ انرژی، نه پایین‌تر.")
    if food_line:
        lines.append("\n" + food_line)
    lines.append("\nاین لحظه‌ی بازنگری است — همان چیزی که سیلابیِ موفق مقدس می‌شمارد.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# --------------------------------------------------------------------------- #
#  /learned — مدلی که ربات تا حالا از تو ساخته
# --------------------------------------------------------------------------- #
async def learned(update, ctx):
    user = update.effective_user.id
    con = db()
    prof = learn_profile(con, user)
    con.close()

    lines = ["🧠 *آنچه تا حالا از تو یاد گرفته‌ام*\n"]

    if prof["n_energy"] < MIN_ENERGY_POINTS:
        lines.append(
            f"هنوز در حالِ یادگیری‌ام — {prof['n_energy']} ثبتِ انرژی دارم، "
            f"به {MIN_ENERGY_POINTS} که برسد مدلم قابل‌اعتماد می‌شود."
        )
    else:
        if prof["energy_mean"] is not None:
            lines.append(f"• انرژیِ پایه‌ات: میانگین {prof['energy_mean']:.1f}/5")
        if prof["peak_hour"] is not None:
            lines.append(
                f"• اوجِ انرژی: حولِ ساعت {prof['peak_hour']}:00 "
                f"({prof['peak_hour_avg']:.1f}/5) — وقتِ کارِ عمیق"
            )
        if prof["low_hour"] is not None:
            lines.append(f"• افتِ انرژی: حولِ ساعت {prof['low_hour']}:00 — وقتِ بازیابی")
        lines.append(f"• آستانه‌ی شخصیِ سوختنِ تو: {prof['burnout_threshold']}/5")

    if prof["n_judged"] >= MIN_JUDGED_IDEAS:
        lines.append("")
        lines.append(f"• دقتِ شهود: {prof['intuition_acc']*100:.0f}%")
        if prof["best_idea_energy"] is not None:
            lines.append(
                f"• ایده‌های درستت در انرژیِ ~{prof['best_idea_energy']:.1f}/5 می‌آیند"
            )
    else:
        lines.append(
            f"\nبرای شناختِ شهودت، چند ایده‌ی دیگر را با /done یا /noise داوری کن "
            f"(تا حالا {prof['n_judged']} از {MIN_JUDGED_IDEAS})."
        )

    lines.append("\n_این مدل با هر ثبت، آرام به‌روز می‌شود._")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# --------------------------------------------------------------------------- #
#  راه‌اندازی
# --------------------------------------------------------------------------- #
def main():
    if not TOKEN:
        raise SystemExit("متغیرِ TELEGRAM_TOKEN را تنظیم کن (از @BotFather بگیر).")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("noise", noise))
    app.add_handler(CommandHandler("eat", eat))
    app.add_handler(CommandHandler("now", now_cmd))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("mirror", mirror))
    app.add_handler(CommandHandler("learned", learned))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Silabi bot running. Press Ctrl-C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
