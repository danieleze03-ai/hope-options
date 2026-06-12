# ============================================================
# HOPE OPTIONS — Market Regime Detector
# Classifies market as TRENDING, RANGING, or CHOPPY
# Only RANGING and early TRENDING regimes get signals
# ============================================================

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def detect_regime(df: pd.DataFrame) -> dict:
    """
    Detects current market regime using ADX + price structure.

    Returns:
        regime: "TRENDING" | "RANGING" | "CHOPPY"
        tradeable: True/False
        reason: explanation string
        adx: ADX value
    """
    if len(df) < 30:
        return {
            "regime": "UNKNOWN",
            "tradeable": False,
            "reason": "Not enough candles",
            "adx": 0
        }

    high  = df["high"]
    low   = df["low"]
    close = df["close"]

    # ── ADX Calculation ──
    period = 14

    plus_dm  = high.diff()
    minus_dm = -low.diff()

    plus_dm  = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low  - close.shift()).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr       = tr.ewm(span=period, adjust=False).mean()
    plus_di   = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr
    minus_di  = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr
    dx        = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di))
    adx       = dx.ewm(span=period, adjust=False).mean()

    adx_val     = round(float(adx.iloc[-1]), 2)
    plus_di_val = round(float(plus_di.iloc[-1]), 2)
    minus_di_val= round(float(minus_di.iloc[-1]), 2)

    # ── Choppiness Index ──
    chop_period = 14
    atr_sum  = tr.rolling(chop_period).sum()
    hl_range = high.rolling(chop_period).max() - low.rolling(chop_period).min()
    chop     = 100 * np.log10(atr_sum / hl_range) / np.log10(chop_period)
    chop_val = round(float(chop.iloc[-1]), 2)

    # ── Regime Classification ──
    # ADX > 25 = trending, < 20 = ranging/choppy
    # Choppiness > 61.8 = choppy, < 38.2 = strong trend

    if chop_val > 61.8:
        regime    = "CHOPPY"
        tradeable = False
        reason    = f"Choppy market (Chop={chop_val}) — No trade ❌"

    elif adx_val >= 25 and chop_val < 55:
        regime    = "TRENDING"
        tradeable = True
        direction = "Bullish" if plus_di_val > minus_di_val else "Bearish"
        reason    = f"Trending {direction} (ADX={adx_val}) ✅"

    elif adx_val < 25 and chop_val < 61.8:
        regime    = "RANGING"
        tradeable = True
        reason    = f"Ranging market (ADX={adx_val}) — Good for reversals ✅"

    else:
        regime    = "CHOPPY"
        tradeable = False
        reason    = f"Uncertain conditions (ADX={adx_val}, Chop={chop_val}) ❌"

    return {
        "regime":     regime,
        "tradeable":  tradeable,
        "reason":     reason,
        "adx":        adx_val,
        "chop":       chop_val,
        "plus_di":    plus_di_val,
        "minus_di":   minus_di_val,
    }


def test_regime_detector():
    from core.data_fetcher import get_candles
    print("Testing regime detector...\n")

    for pair in ["EURUSD", "GBPUSD"]:
        df = get_candles(pair, "5m")
        if df.empty:
            print(f"❌ No data for {pair}")
            continue
        result = detect_regime(df)
        tradeable = "✅ TRADEABLE" if result["tradeable"] else "❌ SKIP"
        print(f"{pair} | {result['regime']:10} | ADX: {result['adx']:6} | Chop: {result['chop']:6} | {tradeable}")
        print(f"       {result['reason']}\n")


if __name__ == "__main__":
    test_regime_detector()