# ============================================================
# HOPE OPTIONS — Main Loop
# Runs signal checks every 30 seconds, tracks results,
# sends daily report at end of day, runs Telegram bot
# FastAPI serves dashboard + API on the single public port
# ============================================================

import sys
import os
import asyncio
import time
from datetime import datetime, timezone
import uvicorn
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from signals.signal_engine import run_all_pairs
from communication.bot import send_signal, send_daily_report, build_app
from tracker.result_tracker import track_signal
from tracker.performance import get_today_stats
from api.api import app as fastapi_app
from fastapi.responses import PlainTextResponse

CHECK_INTERVAL = 30  # seconds
PORT = int(os.environ.get("PORT", 8080))

# Tracks the UTC date we last sent a daily report for
_last_report_date = None


# ── Add ping route to FastAPI (replaces aiohttp keep-alive) ──
@fastapi_app.get("/")
async def ping():
    return PlainTextResponse("Hope Options is alive ✅")


async def signal_loop():
    """Continuously checks for signals every CHECK_INTERVAL seconds."""
    global _last_report_date

    print("[Main] Hope Options signal loop started.")

    while True:
        try:
            signals = run_all_pairs()

            for signal in signals:
                print(f"[Main] SIGNAL: {signal['pair']} {signal['direction']} "
                      f"(score {signal['score']}/100)")

                await send_signal(signal)
                asyncio.create_task(track_signal(signal))

            await _check_daily_report()

        except Exception as e:
            print(f"[Main] ERROR in signal loop: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def _check_daily_report():
    """Send a daily report once per day, after 23:55 UTC."""
    global _last_report_date

    now = datetime.now(timezone.utc)
    today = now.date().isoformat()

    if now.hour == 23 and now.minute >= 55:
        if _last_report_date != today:
            stats = get_today_stats()
            await send_daily_report(stats)
            _last_report_date = today
            print(f"[Main] Daily report sent for {today}")


async def main():
    """Run Telegram bot, FastAPI server, and signal loop together."""
    app = build_app()

    # Start Telegram bot polling in the background
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("[Main] Telegram bot polling started.")

    # Start FastAPI on the single public port (replaces aiohttp server)
    cfg = uvicorn.Config(fastapi_app, host="0.0.0.0", port=PORT, log_level="warning")
    server = uvicorn.Server(cfg)
    asyncio.create_task(server.serve())
    print(f"[Main] FastAPI dashboard running on port {PORT}")

    try:
        await signal_loop()
    except Exception as e:
        print(f"[Main] FATAL error in main: {e}")
    finally:
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
        except Exception as e:
            print(f"[Main] Error during shutdown: {e}")


if __name__ == "__main__":
    while True:
        try:
            print("[Main] Starting Hope Options...")
            asyncio.run(main())
        except Exception as e:
            print(f"[Main] Process crashed: {e}. Restarting in 10 seconds...")
            time.sleep(10)