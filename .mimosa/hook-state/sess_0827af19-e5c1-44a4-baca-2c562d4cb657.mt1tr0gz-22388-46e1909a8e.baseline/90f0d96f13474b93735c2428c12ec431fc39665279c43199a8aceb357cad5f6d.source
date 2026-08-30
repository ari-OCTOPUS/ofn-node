"""
control-bot — Telegram bot for stackctl (infra-control)
Controls all projects on the VPS via inline keyboard buttons.

Security model:
- Only ALLOWED_CHAT_IDS (from env) can interact.
- Every action calls stackctl (no direct docker access from bot code).
- Every action is audit-logged by stackctl (hash-chained, INV-3).
- Logs tail is capped at 50 lines to avoid Telegram message limits.
"""

import asyncio
import logging
import os
import subprocess
import sys
import yaml
from pathlib import Path
from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ── Config ─────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["CONTROL_BOT_TOKEN"]
ALLOWED_CHAT_IDS = set(
    int(x.strip())
    for x in os.environ.get("ALLOWED_CHAT_IDS", "").split(",")
    if x.strip().lstrip("-").isdigit()
)
STACKCTL = os.environ.get("STACKCTL_PATH", "/opt/infra-control/stackctl")
PROJECTS_YAML = Path(STACKCTL).parent / "projects.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("control-bot")


# ── Auth decorator ─────────────────────────────────────────────────────────

def auth_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = (
            update.effective_chat.id if update.effective_chat else None
        )
        if chat_id not in ALLOWED_CHAT_IDS:
            logger.warning("Unauthorized access attempt from chat_id=%s", chat_id)
            if update.message:
                await update.message.reply_text("⛔ Unauthorized.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Unauthorized.", show_alert=True)
            return
        return await func(update, context)
    return wrapper


# ── Helpers ────────────────────────────────────────────────────────────────

def load_project_names() -> list[str]:
    if not PROJECTS_YAML.exists():
        return []
    with open(PROJECTS_YAML) as f:
        data = yaml.safe_load(f)
    return list(data.get("projects", {}).keys())


def run_stackctl(*args, timeout: int = 120) -> tuple[int, str]:
    """Run stackctl and return (returncode, output)."""
    try:
        r = subprocess.run(
            ["python3", STACKCTL] + list(args),
            capture_output=True, text=True, timeout=timeout
        )
        output = (r.stdout + r.stderr).strip()
        return r.returncode, output
    except subprocess.TimeoutExpired:
        return 1, "ERROR: command timed out"
    except Exception as e:
        return 1, f"ERROR: {e}"


def make_project_keyboard(action: str, projects: list[str]) -> InlineKeyboardMarkup:
    """Build inline keyboard with one button per project."""
    buttons = [
        [InlineKeyboardButton(p, callback_data=f"{action}:{p}")]
        for p in projects
    ]
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def truncate(text: str, max_len: int = 3500) -> str:
    if len(text) <= max_len:
        return text
    return "...(truncated)\n" + text[-max_len:]


# ── Command handlers ────────────────────────────────────────────────────────

@auth_required
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = load_project_names()
    text = (
        "🖥 *infra-control bot*\n\n"
        f"Projects: `{'`, `'.join(projects) if projects else 'none'}`\n\n"
        "Commands:\n"
        "/status — show all project status\n"
        "/up — start a project\n"
        "/down — stop a project\n"
        "/restart — restart a project\n"
        "/logs — tail logs\n"
        "/deploy — deploy latest image\n"
        "/kill — kill switch\n"
        "/list — list projects"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@auth_required
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Fetching status...")
    rc, out = run_stackctl("status")
    emoji = "✅" if rc == 0 else "❌"
    await update.message.reply_text(
        f"{emoji} Status:\n```\n{truncate(out)}\n```",
        parse_mode="Markdown"
    )


@auth_required
async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rc, out = run_stackctl("list")
    await update.message.reply_text(f"```\n{truncate(out)}\n```", parse_mode="Markdown")


@auth_required
async def cmd_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = load_project_names()
    await update.message.reply_text(
        "▶️ Start which project?",
        reply_markup=make_project_keyboard("up", projects)
    )


@auth_required
async def cmd_down(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = load_project_names()
    await update.message.reply_text(
        "⏹ Stop which project?",
        reply_markup=make_project_keyboard("down", projects)
    )


@auth_required
async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = load_project_names()
    await update.message.reply_text(
        "🔄 Restart which project?",
        reply_markup=make_project_keyboard("restart", projects)
    )


@auth_required
async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = load_project_names()
    await update.message.reply_text(
        "📋 Logs for which project?",
        reply_markup=make_project_keyboard("logs", projects)
    )


@auth_required
async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = load_project_names()
    await update.message.reply_text(
        "🚀 Deploy which project?",
        reply_markup=make_project_keyboard("deploy", projects)
    )


@auth_required
async def cmd_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = load_project_names()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 KILL ALL", callback_data="kill:--all")],
        *[[InlineKeyboardButton(f"Kill {p}", callback_data=f"kill:{p}")] for p in projects],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])
    await update.message.reply_text(
        "⚠️ *Kill switch — confirm action:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ── Callback handler ────────────────────────────────────────────────────────

@auth_required
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return

    parts = data.split(":", 1)
    if len(parts) != 2:
        await query.edit_message_text("⚠️ Unknown action.")
        return

    action, project = parts
    emoji_map = {
        "up": "▶️", "down": "⏹", "restart": "🔄",
        "logs": "📋", "deploy": "🚀", "kill": "🔴"
    }
    emoji = emoji_map.get(action, "🔧")

    await query.edit_message_text(f"{emoji} Running `{action} {project}`...", parse_mode="Markdown")

    if action == "logs":
        # logs: run stackctl logs --tail 50 (no follow in bot context)
        rc, out = run_stackctl("logs", project, timeout=30)
        # Trim to last 50 lines
        lines = out.split("\n")
        out = "\n".join(lines[-50:])
    else:
        rc, out = run_stackctl(action, project)

    ok = rc == 0
    status_emoji = "✅" if ok else "❌"
    result_text = (
        f"{status_emoji} `{action} {project}` {'done' if ok else 'FAILED'}:\n"
        f"```\n{truncate(out, 2000)}\n```"
    )
    await query.edit_message_text(result_text, parse_mode="Markdown")


# ── Error handler ───────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update caused error: %s", context.error, exc_info=context.error)


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not ALLOWED_CHAT_IDS:
        logger.error("ALLOWED_CHAT_IDS is empty — bot would accept no commands. Exiting.")
        sys.exit(1)

    logger.info("control-bot starting. Allowed chat IDs: %s", ALLOWED_CHAT_IDS)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("up", cmd_up))
    app.add_handler(CommandHandler("down", cmd_down))
    app.add_handler(CommandHandler("restart", cmd_restart))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("deploy", cmd_deploy))
    app.add_handler(CommandHandler("kill", cmd_kill))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    logger.info("Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
