# ============================================================
# HOPE OPTIONS — Configuration
# ============================================================

# Pairs to analyse — yfinance format
PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "EURJPY": "EURJPY=X",
}

# Active pairs to trade (start with just 2)
ACTIVE_PAIRS = ["EURUSD", "GBPUSD"]

# Timeframes — yfinance format
PRIMARY_TF  = "5m"
CONFIRM_TF  = "15m"
ENTRY_TF    = "1m"

# Signal settings
MIN_CONFLUENCE_SCORE  = 75
MIN_INDICATORS_AGREE  = 4
MAX_SIGNALS_PER_DAY   = 999
EXPIRY_MINUTES        = 5

# Risk reminder
RISK_PER_TRADE_PCT = 5

# Trading sessions (UTC times)
SESSIONS = {
    "london_open": {"start": "07:00", "end": "11:00"},
    "ny_overlap":  {"start": "12:00", "end": "15:00"},
    "ny_open":     {"start": "13:00", "end": "16:00"},
}

# News filter
NEWS_BLOCK_MINUTES = 15

# Indicator settings
RSI_PERIOD      = 14
RSI_OVERSOLD    = 35
RSI_OVERBOUGHT  = 65
EMA_FAST        = 9
EMA_MID         = 21
EMA_SLOW        = 50
BB_PERIOD       = 20
BB_STD          = 2
STOCH_K         = 14
STOCH_D         = 3
MACD_FAST       = 12
MACD_SLOW       = 26
MACD_SIGNAL     = 9

# Data settings
CANDLE_LOOKBACK = 100    # How many candles to fetch for analysis