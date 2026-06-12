# ============================================================
# HOPE OPTIONS — Performance Tracker
# Calculates daily/overall stats from signals_log.csv
# ============================================================

import os
import csv
from datetime import datetime, timezone
from collections import defaultdict

LOG_PATH = "data/signals_log.csv"


def _read_rows():
    """Read all rows from CSV (excluding header). Returns []."""
    if not os.path.exists(LOG_PATH):
        return []

    with open(LOG_PATH, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    return rows[1:] if len(rows) > 1 else []


def get_stats(date_filter: str = None):
    """
    Calculate performance stats.

    date_filter: "YYYY-MM-DD" string to filter to a specific day,
                 or None for all-time stats.

    Returns a dict with overall stats and per-pair breakdown.
    """
    rows = _read_rows()

    total = wins = losses = pending = 0
    total_pips = 0.0
    per_pair = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "pips": 0.0})

    for row in rows:
        if len(row) < 9:
            continue

        date, time_, pair, direction, score, entry, exit_, result, pips = row[:9]

        if date_filter and date != date_filter:
            continue

        total += 1
        per_pair[pair]["total"] += 1

        if result == "WIN":
            wins += 1
            per_pair[pair]["wins"] += 1
        elif result == "LOSS":
            losses += 1
            per_pair[pair]["losses"] += 1
        elif result == "PENDING":
            pending += 1
            continue  # skip pip counting for pending

        try:
            pip_val = float(pips)
            total_pips += pip_val
            per_pair[pair]["pips"] += pip_val
        except ValueError:
            pass

    decided = wins + losses
    win_rate = round((wins / decided) * 100, 1) if decided > 0 else 0.0

    pair_stats = {}
    for pair, stats in per_pair.items():
        p_decided = stats["wins"] + stats["losses"]
        p_win_rate = round((stats["wins"] / p_decided) * 100, 1) if p_decided > 0 else 0.0
        pair_stats[pair] = {
            "total": stats["total"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "win_rate": p_win_rate,
            "pips": round(stats["pips"], 1)
        }

    return {
        "date_filter": date_filter or "ALL TIME",
        "total_signals": total,
        "wins": wins,
        "losses": losses,
        "pending": pending,
        "win_rate": win_rate,
        "total_pips": round(total_pips, 1),
        "per_pair": pair_stats
    }


def get_today_stats():
    """Stats for today (UTC date, matches how result_tracker logs)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return get_stats(date_filter=today)


def format_stats_message(stats: dict) -> str:
    """Format stats dict into a Telegram-friendly message."""
    lines = []
    lines.append(f"📊 HOPE OPTIONS — STATS ({stats['date_filter']})")
    lines.append("────────────────────────────")
    lines.append(f"Total Signals : {stats['total_signals']}")
    lines.append(f"Wins          : {stats['wins']} ✅")
    lines.append(f"Losses        : {stats['losses']} ❌")
    if stats['pending']:
        lines.append(f"Pending       : {stats['pending']} ⏳")
    lines.append(f"Win Rate      : {stats['win_rate']}%")
    lines.append(f"Total Pips    : {stats['total_pips']}")

    if stats['per_pair']:
        lines.append("────────────────────────────")
        lines.append("By Pair:")
        for pair, p in stats['per_pair'].items():
            lines.append(f"  {pair}: {p['wins']}W/{p['losses']}L "
                          f"({p['win_rate']}%) | {p['pips']} pips")

    return "\n".join(lines)


def test_performance():
    """Test stats calculation against current CSV."""
    print("=== TODAY ===")
    today_stats = get_today_stats()
    print(format_stats_message(today_stats))

    print("\n=== ALL TIME ===")
    all_stats = get_stats()
    print(format_stats_message(all_stats))


if __name__ == "__main__":
    test_performance()