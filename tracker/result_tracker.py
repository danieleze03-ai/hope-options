# ============================================================
# HOPE OPTIONS — Result Tracker
# Waits for expiry then checks if signal was WIN or LOSS
# Sends result back to Telegram automatically
# ============================================================

import sys
import os
import asyncio
import csv
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_fetcher import get_current_price
from config import EXPIRY_MINUTES

# Path to signals log
LOG_PATH = "data/signals_log.csv"


def ensure_log_exists():
    """Create CSV log file if it doesn't exist."""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "date", "time", "pair", "direction",
                "score", "entry_price", "exit_price",
                "result", "pips"
            ])


def log_signal(signal: dict):
    """Log a new signal to CSV when it is first sent."""
    ensure_log_exists()
    now = datetime.now(timezone.utc)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            signal["pair"],
            signal["direction"],
            signal["score"],
            signal["price"],
            "",        # exit_price — filled later
            "PENDING", # result — filled later
            ""         # pips — filled later
        ])


def update_result(pair: str, entry_price: float, direction: str, exit_price: float):
    """Update the most recent PENDING signal for this pair with result."""
    ensure_log_exists()

    rows = []
    updated = False

    with open(LOG_PATH, "r", newline="") as f:
        reader = csv.reader(f)
        rows   = list(reader)

    # Find last PENDING row for this pair and update it
    for i in reversed(range(1, len(rows))):
        row = rows[i]
        if len(row) >= 8 and row[2] == pair and row[7] == "PENDING":
            exit_p = round(exit_price, 5)
            pips   = round(abs(exit_price - entry_price) * 10000, 1)

            if direction == "CALL":
                result = "WIN" if exit_price > entry_price else "LOSS"
            else:
                result = "WIN" if exit_price < entry_price else "LOSS"

            rows[i][5] = str(round(entry_price, 5))
            rows[i][6] = str(exit_p)
            rows[i][7] = result
            rows[i][8] = str(pips)
            updated = True
            break

    if updated:
        with open(LOG_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    return result if updated else "UNKNOWN"


async def track_signal(signal: dict):
    """
    Wait for expiry then fetch exit price and send result.
    Runs as async task — does not block main loop.
    """
    from communication.bot import send_result

    pair      = signal["pair"]
    entry     = signal["price"]
    direction = signal["direction"]
    expiry    = EXPIRY_MINUTES * 60  # Convert to seconds

    print(f"[Tracker] Tracking {pair} {direction} — result in {EXPIRY_MINUTES} min")

    # Log the signal immediately
    log_signal(signal)

    # Wait for expiry
    await asyncio.sleep(expiry)

    # Fetch exit price
    exit_price = get_current_price(pair)

    if exit_price == 0.0:
        print(f"[Tracker] Could not fetch exit price for {pair}")
        return

    # Determine result
    if direction == "CALL":
        result = "WIN" if exit_price > entry else "LOSS"
    else:
        result = "WIN" if exit_price < entry else "LOSS"

    # Update CSV
    update_result(pair, entry, direction, exit_price)

    # Send result to Telegram
    await send_result(signal, result, entry, exit_price)

    pips = round(abs(exit_price - entry) * 10000, 1)
    print(f"[Tracker] {pair} {direction} — {result} | Entry: {entry:.5f} Exit: {exit_price:.5f} ({pips} pips)")


def test_result_tracker():
    """Test logging a dummy signal."""
    ensure_log_exists()

    dummy_signal = {
        "pair":      "EURUSD",
        "direction": "CALL",
        "score":     82,
        "price":     1.08500,
        "wat_time":  "10:00 WAT"
    }

    log_signal(dummy_signal)
    print("✅ Signal logged to data/signals_log.csv")

    result = update_result("EURUSD", 1.08500, "CALL", 1.08620)
    print(f"✅ Result updated: {result}")

    # Show CSV contents
    with open(LOG_PATH, "r") as f:
        print("\nCSV Contents:")
        print(f.read())


if __name__ == "__main__":
    test_result_tracker()