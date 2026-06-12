# ============================================================
# HOPE OPTIONS — Telegram Bot
# Sends signals, results, and responds to commands
# ============================================================

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import telegram
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

from communication.messages import format_signal_message, format_result_message
from communication.messages import format_daily_report, format_status_message
from signals.signal_engine import get_daily_count, ACTIVE_PAIRS

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")


async def send_message(text: str):
    """Send a message to your Telegram chat."""
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        parse_mode="Markdown"
    )


async def send_signal(signal: dict):
    """Send a formatted signal message."""
    msg = format_signal_message(signal)
    await send_message(msg)


async def send_result(signal: dict, result: str, entry: float, exit_price: float):
    """Send a win/loss result message."""
    msg = format_result_message(signal, result, entry, exit_price)
    await send_message(msg)


async def send_daily_report(stats: dict):
    """Send end of day report."""
    msg = format_daily_report(stats)
    await send_message(msg)


# ── Bot Commands ──

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Hope Options Bot is running!*\n\n"
        "Commands:\n"
        "/status — Check bot status\n"
        "/accuracy — Today's win rate\n"
        "/pairs — Active pairs\n",
        parse_mode="Markdown"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs_status = [{"pair": p, "status": "Monitoring 👁"} for p in ACTIVE_PAIRS]
    msg = format_status_message(pairs_status, get_daily_count())
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_accuracy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from tracker.performance import get_today_stats
    stats = get_today_stats()
    msg   = format_daily_report(stats)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs_text = "\n".join([f"• {p}" for p in ACTIVE_PAIRS])
    await update.message.reply_text(
        f"📊 *Active Pairs:*\n{pairs_text}",
        parse_mode="Markdown"
    )


def build_app():
    """Build and return the Telegram application."""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("accuracy", cmd_accuracy))
    app.add_handler(CommandHandler("pairs",    cmd_pairs))
    return app


async def test_telegram():
    """Send a test message to verify connection."""
    print("Testing Telegram connection...")
    try:
        await send_message(
            "🤖 *Hope Options Bot*\n"
            "✅ Connection successful!\n"
            "_Bot is online and ready._"
        )
        print("✅ Telegram message sent successfully")
    except Exception as e:
        print(f"❌ Telegram error: {e}")


if __name__ == "__main__":
    asyncio.run(test_telegram())