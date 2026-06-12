# ============================================================
# HOPE OPTIONS — Message Formatter
# Formats signal and result messages for Telegram
# ============================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXPIRY_MINUTES, RISK_PER_TRADE_PCT


def format_signal_message(signal: dict) -> str:
    """Formats a signal dict into a clean Telegram message."""

    direction = signal["direction"]
    arrow     = "⬆️" if direction == "CALL" else "⬇️"
    emoji     = "🟢" if direction == "CALL" else "🔴"
    score     = signal["score"]

    # Score bar visual
    filled = int(score / 10)
    bar    = "█" * filled + "░" * (10 - filled)

    # Confidence label
    if score >= 90:
        conf_label = "VERY HIGH 🔥"
    elif score >= 80:
        conf_label = "HIGH ✅"
    elif score >= 75:
        conf_label = "GOOD 👍"
    else:
        conf_label = "MODERATE ⚠️"

    msg = (
        f"{emoji} *HOPE OPTIONS SIGNAL*\n"
        f"{'─' * 28}\n"
        f"📊 *Pair:* `{signal['pair']}`\n"
        f"📍 *Direction:* *{direction}* {arrow}\n"
        f"⏱ *Expiry:* {EXPIRY_MINUTES} minutes\n"
        f"💰 *Entry Price:* `{signal['price']:.5f}`\n"
        f"🕐 *Time:* {signal['wat_time']}\n"
        f"{'─' * 28}\n"
        f"📈 *Confidence: {score}/100* — {conf_label}\n"
        f"`[{bar}]`\n"
        f"{'─' * 28}\n"
        f"🔍 *Analysis:*\n"
        f"• {signal['regime']}\n"
        f"• {signal['mtf']}\n"
        f"• 15m: {signal['bias_15m']}\n"
        f"• 5m:  {signal['bias_5m']}\n"
        f"• 1m:  {signal['bias_1m']}\n"
        f"• Session: {signal['session']}\n"
        f"{'─' * 28}\n"
        f"⚠️ *Risk {RISK_PER_TRADE_PCT}% of balance only*\n"
        f"_Hope Options — Trade smart, trade safe_"
    )
    return msg


def format_result_message(signal: dict, result: str, entry: float, exit_price: float) -> str:
    """Formats a win/loss result message."""

    direction  = signal["direction"]
    pair       = signal["pair"]
    pips       = round(abs(exit_price - entry) * 10000, 1)

    if result == "WIN":
        emoji  = "✅"
        label  = "WIN"
        detail = f"+{pips} pips in your favour"
    else:
        emoji  = "❌"
        label  = "LOSS"
        detail = f"{pips} pips against"

    msg = (
        f"{emoji} *SIGNAL RESULT*\n"
        f"{'─' * 28}\n"
        f"📊 *Pair:* `{pair}`\n"
        f"📍 *Direction:* {direction}\n"
        f"💰 *Entry:*  `{entry:.5f}`\n"
        f"🏁 *Exit:*   `{exit_price:.5f}`\n"
        f"📏 *Move:*   {detail}\n"
        f"{'─' * 28}\n"
        f"🏆 *Result: {label}*\n"
        f"_Hope Options_"
    )
    return msg


def format_daily_report(stats: dict) -> str:
    """Formats end of day performance report."""

    wins   = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total  = wins + losses
    rate   = round((wins / total * 100), 1) if total > 0 else 0

    if rate >= 70:
        verdict = "Excellent day! 🔥"
    elif rate >= 60:
        verdict = "Good performance 👍"
    elif rate >= 50:
        verdict = "Breakeven range ⚠️"
    else:
        verdict = "Tough day — review setups 📉"

    msg = (
        f"📊 *HOPE OPTIONS — DAILY REPORT*\n"
        f"{'─' * 28}\n"
        f"✅ Wins:       {wins}\n"
        f"❌ Losses:     {losses}\n"
        f"📈 Total:      {total}\n"
        f"🎯 Win Rate:   {rate}%\n"
        f"{'─' * 28}\n"
        f"_{verdict}_\n"
        f"_Hope Options_"
    )
    return msg


def format_status_message(pairs_status: list, daily_count: int) -> str:
    """Formats /status command response."""
    from signals.session_filter import is_trading_session, get_wat_time
    session = is_trading_session()

    lines = [
        f"🤖 *HOPE OPTIONS STATUS*",
        f"{'─' * 28}",
        f"🕐 Time: {get_wat_time()}",
        f"📡 Session: {session.get('session_label') or 'Outside sessions'}",
        f"📊 Signals today: {daily_count}/4",
        f"{'─' * 28}",
        f"*Pairs:*"
    ]

    for p in pairs_status:
        lines.append(f"• {p['pair']}: {p['status']}")

    lines.append(f"{'─' * 28}")
    lines.append(f"_Hope Options is {'active ✅' if session['active'] else 'standing by 🌙'}_")

    return "\n".join(lines)