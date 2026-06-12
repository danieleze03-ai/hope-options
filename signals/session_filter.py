# ============================================================
# HOPE OPTIONS — Session Filter
# Only signals during London, NY Overlap, NY Open
# Outside these windows — bot stays silent
# ============================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, time
from config import SESSIONS


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_trading_session() -> dict:
    """
    Check if current UTC time is within any active trading session.
    Returns session name, whether active, and time info.
    """
    now     = get_utc_now()
    current = now.time()

    for session_name, window in SESSIONS.items():
        start = time(*map(int, window["start"].split(":")))
        end   = time(*map(int, window["end"].split(":")))

        if start <= current <= end:
            return {
                "active":       True,
                "session":      session_name,
                "session_label": _format_session_name(session_name),
                "utc_time":     now.strftime("%H:%M UTC"),
                "reason":       f"{_format_session_name(session_name)} session active ✅"
            }

    # Not in any session
    next_session = _get_next_session(current)
    return {
        "active":       False,
        "session":      None,
        "session_label": None,
        "utc_time":     now.strftime("%H:%M UTC"),
        "reason":       f"Outside trading sessions — Next: {next_session} ❌"
    }


def _format_session_name(name: str) -> str:
    mapping = {
        "london_open": "London Open",
        "ny_overlap":  "NY/London Overlap",
        "ny_open":     "New York Open",
    }
    return mapping.get(name, name.replace("_", " ").title())


def _get_next_session(current_time: time) -> str:
    """Returns name of the next upcoming session."""
    upcoming = []
    for name, window in SESSIONS.items():
        start = time(*map(int, window["start"].split(":")))
        if start > current_time:
            upcoming.append((start, _format_session_name(name)))

    if upcoming:
        upcoming.sort(key=lambda x: x[0])
        return f"{upcoming[0][1]} at {upcoming[0][0].strftime('%H:%M')} UTC"

    # All sessions passed today — next is tomorrow's London Open
    return "London Open at 07:00 UTC (tomorrow)"


def get_wat_time() -> str:
    """Returns current West Africa Time (UTC+1) for signal messages."""
    from datetime import timedelta
    wat = get_utc_now() + timedelta(hours=1)
    return wat.strftime("%H:%M WAT")


def test_session_filter():
    print("Testing session filter...\n")
    result = is_trading_session()
    print(f"UTC Time : {result['utc_time']}")
    print(f"WAT Time : {get_wat_time()}")
    print(f"Active   : {result['active']}")
    print(f"Session  : {result.get('session_label', 'None')}")
    print(f"Reason   : {result['reason']}")


if __name__ == "__main__":
    test_session_filter()