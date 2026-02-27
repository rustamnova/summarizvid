#!/usr/bin/env python3
import os
import sys
import logging
import logging.handlers
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# ---------------------------
# Config / ENV
# ---------------------------
load_dotenv(override=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
USER_IDS  = set(int(x.strip()) for x in os.getenv("USER_IDS", "").split(",") if x.strip().isdigit())

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")

# ---------------------------
# Logging
# ---------------------------
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

_worklog_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "worklog.txt"), maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
_worklog_handler.setLevel(logging.INFO)
_worklog_handler.setFormatter(_fmt)

_error_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "errors.txt"), maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
_error_handler.setLevel(logging.ERROR)
_error_handler.setFormatter(_fmt)

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_fmt)

logging.root.handlers.clear()
logging.root.setLevel(logging.INFO)
logging.root.addHandler(_worklog_handler)
logging.root.addHandler(_error_handler)
logging.root.addHandler(_console_handler)

log = logging.getLogger(__name__)


# ---------------------------
# Helpers
# ---------------------------
def allowed(user_id: int) -> bool:
    return not USER_IDS or user_id in USER_IDS


# ---------------------------
# Handlers
# ---------------------------
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        return
    log.info(f"/start от {update.effective_user.id}")
    await update.message.reply_text("👋 Привет! Я бот.")


async def cmd_ping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        return
    await update.message.reply_text("🏓 Pong!")


# ---------------------------
# Main
# ---------------------------
def main():
    log.info("=== Запуск бота ===")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping",  cmd_ping))
    log.info("Бот запущен, ожидание обновлений...")
    app.run_polling(drop_pending_updates=True)
    log.info("=== Остановка бота ===")


if __name__ == "__main__":
    main()
