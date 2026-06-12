# ============================================================
# HOPE OPTIONS — News Filter
# Blocks signals during high-impact news events
# Uses ForexFactory calendar (free, no API key)
# ============================================================

import requests
import sys
import os
from datetime import datetime, timezone, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWS_BLOCK_MINUTES


# Pairs we care about — only block news for these currencies
WATCHED_CURRENCIES = ["USD", "EUR", "GBP", "JPY"]


def get_news_events() -> list:
    """
    Fetch today's high-impact forex news from ForexFactory.
    Returns list of events with time and currency.
    """
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"[NewsFilter] Failed to fetch news: {response.status_code}")
            return []

        events = response.json()

        # Filter only high impact events for our currencies
        high_impact = []
        for event in events:
            if (event.get("impact") == "High" and
                    event.get("currency") in WATCHED_CURRENCIES):
                high_impact.append(event)

        return high_impact

    except Exception as e:
        print(f"[NewsFilter] Error fetching news: {e}")
        return []


def is_news_blocked(pair_name: str) -> dict:
    """
    Check if a pair is blocked due to upcoming or recent news.
    Blocks NEWS_BLOCK_MINUTES before and after any high-impact event.
    """
    # Extract currencies from pair name
    pair_currencies = _get_pair_currencies(pair_name)

    events = get_news_events()
    now    = datetime.now(timezone.utc)

    for event in events:
        event_currency = event.get("currency", "")

        # Only check events affecting our pair's currencies
        if event_currency not in pair_currencies:
            continue

        event_time = _parse_event_time(event.get("date", ""))
        if not event_time:
            continue

        diff_minutes = (event_time - now).total_seconds() / 60

        # Block if within window
        if -NEWS_BLOCK_MINUTES <= diff_minutes <= NEWS_BLOCK_MINUTES:
            title = event.get("title", "Unknown event")
            if diff_minutes > 0:
                timing = f"in {int(diff_minutes)} min"
            else:
                timing = f"{int(abs(diff_minutes))} min ago"

            return {
                "blocked": True,
                "reason":  f"⚠️ High-impact news: {title} ({event_currency}) {timing} — Signal blocked ❌",
                "event":   title,
                "currency": event_currency,
            }

    return {
        "blocked": False,
        "reason":  "No high-impact news nearby ✅",
        "event":   None,
        "currency": None,
    }


def _get_pair_currencies(pair_name: str) -> list:
    """Extract currency codes from pair name e.g. EURUSD -> [EUR, USD]"""
    pair = pair_name.upper().replace("/", "").replace("=X", "")
    if len(pair) == 6:
        return [pair[:3], pair[3:]]
    return []


def _parse_event_time(date_str: str) -> datetime:
    """Parse ForexFactory date string to UTC datetime."""
    try:
        # ForexFactory format: "2024-01-15T08:30:00-05:00"
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def test_news_filter():
    print("Testing news filter...\n")

    events = get_news_events()
    print(f"High-impact events today/this week: {len(events)}")

    for pair in ["EURUSD", "GBPUSD", "USDJPY"]:
        result = is_news_blocked(pair)
        status = "🚫 BLOCKED" if result["blocked"] else "✅ CLEAR"
        print(f"{pair}: {status} — {result['reason']}")


if __name__ == "__main__":
    test_news_filter()