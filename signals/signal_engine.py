# ============================================================
# HOPE OPTIONS — Signal Engine
# Final decision: CALL, PUT, or NO TRADE
# This is the last gate before a signal is sent
# ============================================================

import sys
import os
import json
from datetime import datetime, timezone, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mtf_analyzer import analyze_mtf
from core.data_fetcher import get_current_price
from signals.scorer import calculate_score
from signals.session_filter import is_trading_session, get_wat_time
from signals.news_filter import is_news_blocked
from config import ACTIVE_PAIRS, MAX_SIGNALS_PER_DAY, EXPIRY_MINUTES


# In-memory daily signal counter (resets at midnight UTC)
_signal_log = {
    "date":    None,
    "count":   0,
    "signals": []
}


def _reset_if_new_day():
    today = datetime.now(timezone.utc).date().isoformat()
    if _signal_log["date"] != today:
        _signal_log["date"]    = today
        _signal_log["count"]   = 0
        _signal_log["signals"] = []


def get_daily_count() -> int:
    _reset_if_new_day()
    return _signal_log["count"]


def already_signalled_pair(pair_name: str) -> bool:
    """Prevent signalling same pair twice within 2 candles (10 minutes)."""
    _reset_if_new_day()
    now = datetime.now(timezone.utc)
    for sig in _signal_log["signals"]:
        if sig["pair"] == pair_name:
            sent_at = datetime.fromisoformat(sig["time"])
            if (now - sent_at).total_seconds() < 600:
                return True
    return False


def run_signal_check(pair_name: str) -> dict:
    """
    Full signal check for one pair.
    Returns signal dict or NO TRADE dict.
    """
    _reset_if_new_day()

    # ── Gate 1: Daily limit ──
    if _signal_log["count"] >= MAX_SIGNALS_PER_DAY:
        return _no_trade(pair_name, f"Daily limit reached ({MAX_SIGNALS_PER_DAY} signals) ❌")

    # ── Gate 2: Session check ──
    session = is_trading_session()
    if not session["active"]:
        return _no_trade(pair_name, session["reason"])

    # ── Gate 3: Recent signal on same pair ──
    if already_signalled_pair(pair_name):
        return _no_trade(pair_name, f"Too soon after last {pair_name} signal ❌")

    # ── Gate 4: News check ──
    news = is_news_blocked(pair_name)
    if news["blocked"]:
        return _no_trade(pair_name, news["reason"])

    # ── Gate 5: MTF Analysis ──
    mtf    = analyze_mtf(pair_name)
    regime = mtf["regime"]

    if not regime["tradeable"]:
        return _no_trade(pair_name, regime["reason"])

    if not mtf["aligned"]:
        return _no_trade(pair_name, mtf["mtf_reason"])

    # ── Gate 6: Confluence Score ──
    score_result = calculate_score(mtf, regime, session, news)

    if not score_result["signal_valid"]:
        return _no_trade(pair_name, score_result["verdict"])

    # ── All gates passed — Generate signal ──
    direction = score_result["direction"]
    price     = get_current_price(pair_name)
    now_utc   = datetime.now(timezone.utc)
    expiry    = now_utc + timedelta(minutes=EXPIRY_MINUTES)

    signal = {
        "type":        "SIGNAL",
        "pair":        pair_name,
        "direction":   direction,
        "score":       score_result["score"],
        "price":       price,
        "entry_time":  now_utc.isoformat(),
        "expiry_time": expiry.isoformat(),
        "expiry_min":  EXPIRY_MINUTES,
        "wat_time":    get_wat_time(),
        "session":     session["session_label"],
        "regime":      regime["reason"],
        "mtf":         mtf["mtf_reason"],
        "breakdown":   score_result["breakdown"],
        "bias_15m":    mtf["bias_15m"]["reason"],
        "bias_5m":     mtf["bias_5m"]["reason"],
        "bias_1m":     mtf["bias_1m"]["reason"],
    }

    # Record in daily log
    _signal_log["count"] += 1
    _signal_log["signals"].append({
        "pair":   pair_name,
        "time":   now_utc.isoformat(),
        "direction": direction,
        "score":  score_result["score"],
        "price":  price,
        "result": "PENDING"
    })

    return signal


def run_all_pairs() -> list:
    """Run signal check on all active pairs. Returns list of valid signals."""
    signals = []
    for pair in ACTIVE_PAIRS:
        result = run_signal_check(pair)
        if result.get("type") == "SIGNAL":
            signals.append(result)
    return signals


def _no_trade(pair_name: str, reason: str) -> dict:
    return {
        "type":   "NO_TRADE",
        "pair":   pair_name,
        "reason": reason
    }


def test_signal_engine():
    print("Testing signal engine...\n")
    for pair in ACTIVE_PAIRS:
        print(f"{'='*50}")
        result = run_signal_check(pair)
        if result["type"] == "SIGNAL":
            print(f"🟢 SIGNAL FOUND!")
            print(f"   Pair      : {result['pair']}")
            print(f"   Direction : {result['direction']}")
            print(f"   Score     : {result['score']}/100")
            print(f"   Price     : {result['price']}")
            print(f"   Time      : {result['wat_time']}")
            print(f"   Session   : {result['session']}")
        else:
            print(f"⏸  NO TRADE — {result['pair']}")
            print(f"   Reason: {result['reason']}")
        print()


if __name__ == "__main__":
    test_signal_engine()