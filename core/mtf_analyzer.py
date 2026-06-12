# ============================================================
# HOPE OPTIONS — Multi-Timeframe Analyzer
# Checks 15min + 5min + 1min alignment before any signal
# All 3 timeframes must agree — no exceptions
# ============================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_fetcher import get_candles
from core.indicators import run_all_indicators
from core.regime_detector import detect_regime
from config import PRIMARY_TF, CONFIRM_TF, ENTRY_TF


def get_timeframe_bias(df) -> dict:
    """
    Determines the directional bias for a single timeframe.
    Returns: CALL, PUT, or NEUTRAL with score
    """
    if df.empty or len(df) < 30:
        return {"bias": "NEUTRAL", "score": 0, "reason": "Insufficient data"}

    indicators = run_all_indicators(df)

    call_count = 0
    put_count  = 0
    labels     = []

    for name, data in indicators.items():
        sig = data.get("signal", "NEUTRAL")
        if sig == "CALL":
            call_count += 1
        elif sig == "PUT":
            put_count += 1
        labels.append(data.get("label", ""))

    total = call_count + put_count
    if total == 0:
        return {"bias": "NEUTRAL", "score": 0, "reason": "All indicators neutral"}

    if call_count > put_count:
        score = round((call_count / 5) * 100)
        return {"bias": "CALL", "score": score,
                "reason": f"{call_count}/5 indicators bullish", "labels": labels}
    elif put_count > call_count:
        score = round((put_count / 5) * 100)
        return {"bias": "PUT", "score": score,
                "reason": f"{put_count}/5 indicators bearish", "labels": labels}
    else:
        return {"bias": "NEUTRAL", "score": 50,
                "reason": "Indicators split equally", "labels": labels}


def analyze_mtf(pair_name: str) -> dict:
    """
    Full multi-timeframe analysis for a pair.
    Returns final direction and whether signal is valid.
    """

    # Fetch all three timeframes
    df_confirm = get_candles(pair_name, CONFIRM_TF)  # 15m
    df_primary = get_candles(pair_name, PRIMARY_TF)  # 5m
    df_entry   = get_candles(pair_name, ENTRY_TF)    # 1m

    # Get bias for each timeframe
    bias_15m = get_timeframe_bias(df_confirm)
    bias_5m  = get_timeframe_bias(df_primary)
    bias_1m  = get_timeframe_bias(df_entry)

    # Get market regime from 5m
    regime = detect_regime(df_primary) if not df_primary.empty else {
        "regime": "UNKNOWN", "tradeable": False, "reason": "No data"
    }

    # ── MTF Confluence Check ──
    biases = [bias_15m["bias"], bias_5m["bias"], bias_1m["bias"]]

    call_tfs = biases.count("CALL")
    put_tfs  = biases.count("PUT")

    # All 3 must agree OR at minimum 2/3 with no opposing signal
    if call_tfs >= 2 and put_tfs == 0:
        direction = "CALL"
        aligned   = True
        mtf_reason = f"MTF Bullish {call_tfs}/3 timeframes agree ✅"
    elif put_tfs >= 2 and call_tfs == 0:
        direction = "PUT"
        aligned   = True
        mtf_reason = f"MTF Bearish {put_tfs}/3 timeframes agree ✅"
    else:
        direction = "NEUTRAL"
        aligned   = False
        mtf_reason = f"MTF Conflict — 15m:{bias_15m['bias']} 5m:{bias_5m['bias']} 1m:{bias_1m['bias']} ❌"

    # Final signal validity
    valid = aligned and regime["tradeable"]

    return {
        "pair":       pair_name,
        "direction":  direction,
        "valid":      valid,
        "regime":     regime,
        "bias_15m":   bias_15m,
        "bias_5m":    bias_5m,
        "bias_1m":    bias_1m,
        "mtf_reason": mtf_reason,
        "aligned":    aligned,
    }


def test_mtf_analyzer():
    print("Testing Multi-Timeframe Analyzer...\n")

    for pair in ["EURUSD", "GBPUSD"]:
        print(f"{'='*50}")
        print(f"Analyzing {pair}...")
        result = analyze_mtf(pair)

        print(f"Regime   : {result['regime']['reason']}")
        print(f"15m Bias : {result['bias_15m']['bias']:8} | {result['bias_15m']['reason']}")
        print(f"5m  Bias : {result['bias_5m']['bias']:8} | {result['bias_5m']['reason']}")
        print(f"1m  Bias : {result['bias_1m']['bias']:8} | {result['bias_1m']['reason']}")
        print(f"MTF      : {result['mtf_reason']}")
        valid = "✅ VALID SETUP" if result["valid"] else "❌ NO TRADE"
        print(f"Result   : {valid} — Direction: {result['direction']}")
        print()


if __name__ == "__main__":
    test_mtf_analyzer()