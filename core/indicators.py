# ============================================================
# HOPE OPTIONS — Indicators Engine
# All 5 indicators calculated manually from OHLCV data
# ============================================================

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT,
    EMA_FAST, EMA_MID, EMA_SLOW,
    BB_PERIOD, BB_STD,
    STOCH_K, STOCH_D,
    MACD_FAST, MACD_SLOW, MACD_SIGNAL
)


# ─────────────────────────────────────────
# RSI
# ─────────────────────────────────────────
def calculate_rsi(df: pd.DataFrame) -> dict:
    close = df["close"]
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(com=RSI_PERIOD - 1, min_periods=RSI_PERIOD).mean()
    avg_loss = loss.ewm(com=RSI_PERIOD - 1, min_periods=RSI_PERIOD).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    value = round(float(rsi.iloc[-1]), 2)

    if value <= RSI_OVERSOLD:
        signal = "CALL"
        label  = f"RSI {value} — Oversold ✅"
    elif value >= RSI_OVERBOUGHT:
        signal = "PUT"
        label  = f"RSI {value} — Overbought ✅"
    else:
        signal = "NEUTRAL"
        label  = f"RSI {value} — Neutral ❌"

    return {"value": value, "signal": signal, "label": label}


# ─────────────────────────────────────────
# MACD
# ─────────────────────────────────────────
def calculate_macd(df: pd.DataFrame) -> dict:
    close = df["close"]
    ema_fast   = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow   = close.ewm(span=MACD_SLOW, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
    histogram  = macd_line - signal_line

    macd_val  = round(float(macd_line.iloc[-1]), 6)
    sig_val   = round(float(signal_line.iloc[-1]), 6)
    hist_val  = round(float(histogram.iloc[-1]), 6)
    hist_prev = round(float(histogram.iloc[-2]), 6)

    # Bullish cross: histogram flipped positive
    if hist_val > 0 and hist_prev <= 0:
        signal = "CALL"
        label  = f"MACD Bullish crossover ✅"
    elif hist_val < 0 and hist_prev >= 0:
        signal = "PUT"
        label  = f"MACD Bearish crossover ✅"
    elif hist_val > 0:
        signal = "CALL"
        label  = f"MACD Bullish momentum ✅"
    elif hist_val < 0:
        signal = "PUT"
        label  = f"MACD Bearish momentum ✅"
    else:
        signal = "NEUTRAL"
        label  = f"MACD Neutral ❌"

    return {"macd": macd_val, "signal_line": sig_val,
            "histogram": hist_val, "signal": signal, "label": label}


# ─────────────────────────────────────────
# Bollinger Bands
# ─────────────────────────────────────────
def calculate_bollinger(df: pd.DataFrame) -> dict:
    close  = df["close"]
    mid    = close.rolling(BB_PERIOD).mean()
    std    = close.rolling(BB_PERIOD).std()
    upper  = mid + BB_STD * std
    lower  = mid - BB_STD * std

    price     = round(float(close.iloc[-1]), 5)
    upper_val = round(float(upper.iloc[-1]), 5)
    lower_val = round(float(lower.iloc[-1]), 5)
    mid_val   = round(float(mid.iloc[-1]), 5)
    bandwidth = round(float(((upper - lower) / mid).iloc[-1] * 100), 4)

    if price <= lower_val:
        signal = "CALL"
        label  = f"BB Price at lower band ✅"
    elif price >= upper_val:
        signal = "PUT"
        label  = f"BB Price at upper band ✅"
    else:
        signal = "NEUTRAL"
        label  = f"BB Price inside bands ❌"

    return {
        "price": price, "upper": upper_val,
        "lower": lower_val, "mid": mid_val,
        "bandwidth": bandwidth, "signal": signal, "label": label
    }


# ─────────────────────────────────────────
# EMA Stack
# ─────────────────────────────────────────
def calculate_ema_stack(df: pd.DataFrame) -> dict:
    close    = df["close"]
    ema_fast = close.ewm(span=EMA_FAST, adjust=False).mean()
    ema_mid  = close.ewm(span=EMA_MID,  adjust=False).mean()
    ema_slow = close.ewm(span=EMA_SLOW, adjust=False).mean()

    fast = round(float(ema_fast.iloc[-1]), 5)
    mid  = round(float(ema_mid.iloc[-1]),  5)
    slow = round(float(ema_slow.iloc[-1]), 5)
    price = round(float(close.iloc[-1]),   5)

    # Bullish stack: price > fast > mid > slow
    if price > fast > mid > slow:
        signal = "CALL"
        label  = f"EMA Stack Bullish aligned ✅"
    elif price < fast < mid < slow:
        signal = "PUT"
        label  = f"EMA Stack Bearish aligned ✅"
    else:
        signal = "NEUTRAL"
        label  = f"EMA Stack Mixed ❌"

    return {
        "fast": fast, "mid": mid, "slow": slow,
        "signal": signal, "label": label
    }


# ─────────────────────────────────────────
# Stochastic Oscillator
# ─────────────────────────────────────────
def calculate_stochastic(df: pd.DataFrame) -> dict:
    high  = df["high"]
    low   = df["low"]
    close = df["close"]

    lowest_low   = low.rolling(STOCH_K).min()
    highest_high = high.rolling(STOCH_K).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(STOCH_D).mean()

    k_val = round(float(k.iloc[-1]), 2)
    d_val = round(float(d.iloc[-1]), 2)

    if k_val < 20 and d_val < 20:
        signal = "CALL"
        label  = f"Stoch {k_val}/{d_val} — Oversold ✅"
    elif k_val > 80 and d_val > 80:
        signal = "PUT"
        label  = f"Stoch {k_val}/{d_val} — Overbought ✅"
    else:
        signal = "NEUTRAL"
        label  = f"Stoch {k_val}/{d_val} — Neutral ❌"

    return {"k": k_val, "d": d_val, "signal": signal, "label": label}


# ─────────────────────────────────────────
# Run All Indicators
# ─────────────────────────────────────────
def run_all_indicators(df: pd.DataFrame) -> dict:
    return {
        "rsi":        calculate_rsi(df),
        "macd":       calculate_macd(df),
        "bollinger":  calculate_bollinger(df),
        "ema_stack":  calculate_ema_stack(df),
        "stochastic": calculate_stochastic(df),
    }


# ─────────────────────────────────────────
# Test
# ─────────────────────────────────────────
def test_indicators():
    from core.data_fetcher import get_candles
    print("Testing indicators on EURUSD 5m...\n")
    df = get_candles("EURUSD", "5m")
    if df.empty:
        print("❌ No data to test indicators")
        return

    results = run_all_indicators(df)
    for name, data in results.items():
        print(f"{name.upper():12} | Signal: {data['signal']:8} | {data['label']}")


if __name__ == "__main__":
    test_indicators()