# ============================================================
# HOPE OPTIONS — FastAPI Dashboard API
# Thin HTTP bridge between the bot's internal state
# and the React dashboard frontend.
#
# Runs on port 8081 (main keep-alive server owns 8080)
# All imports are direct — no data duplication
# ============================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List

import config
from signals.signal_engine import _signal_log, get_daily_count
from core.mtf_analyzer import analyze_mtf
from tracker.performance import get_today_stats
from signals.session_filter import is_trading_session, get_wat_time

app = FastAPI(title="Hope Options Dashboard API")

# Allow the dashboard HTML (served from same origin) to call these endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models for POST body validation ──

class PairsUpdate(BaseModel):
    pairs: List[str]

class LimitUpdate(BaseModel):
    limit: int


# ================================================================
# GET /status
# Returns: bot alive, session info, WAT time, pairs, daily count
# ================================================================

@app.get("/status")
async def get_status():
    session = is_trading_session()
    return {
        "bot_alive":     True,
        "session_active": session["active"],
        "session_label":  session.get("session_label", "—"),
        "wat_time":       get_wat_time(),
        "active_pairs":   config.ACTIVE_PAIRS,
        "daily_count":    get_daily_count(),
        "daily_limit":    config.MAX_SIGNALS_PER_DAY,
    }


# ================================================================
# GET /confidence
# Calls analyze_mtf() on every active pair.
# Returns live score + direction per pair.
# ================================================================

@app.get("/confidence")
async def get_confidence():
    results = []
    for pair in config.ACTIVE_PAIRS:
        try:
            mtf = analyze_mtf(pair)
            # Build a clean score: average of the 3 timeframe scores
            score_15m = mtf["bias_15m"].get("score", 0)
            score_5m  = mtf["bias_5m"].get("score", 0)
            score_1m  = mtf["bias_1m"].get("score", 0)
            avg_score = round((score_15m + score_5m + score_1m) / 3)

            results.append({
                "pair":       pair,
                "direction":  mtf["direction"],
                "aligned":    mtf["aligned"],
                "score":      avg_score,
                "score_15m":  score_15m,
                "score_5m":   score_5m,
                "score_1m":   score_1m,
                "regime":     mtf["regime"]["reason"],
                "mtf_reason": mtf["mtf_reason"],
            })
        except Exception as e:
            results.append({
                "pair":      pair,
                "direction": "ERROR",
                "aligned":   False,
                "score":     0,
                "error":     str(e),
            })
    return results


# ================================================================
# GET /signals
# Returns today's signal log (all entries, including PENDING)
# ================================================================

@app.get("/signals")
async def get_signals():
    today = datetime.now(timezone.utc).date().isoformat()

    # Safety: if log is from a previous day, return empty
    if _signal_log.get("date") != today:
        return {
            "date":    today,
            "count":   0,
            "signals": []
        }

    return {
        "date":    _signal_log["date"],
        "count":   _signal_log["count"],
        "signals": _signal_log["signals"],
    }


# ================================================================
# GET /stats
# Returns today's win rate, pips, wins, losses, pending
# ================================================================

@app.get("/stats")
async def get_stats():
    return get_today_stats()


# ================================================================
# POST /pairs
# Body: { "pairs": ["EURUSD", "GBPJPY", ...] }
# Overwrites ACTIVE_PAIRS in memory until restart
# ================================================================

@app.post("/pairs")
async def update_pairs(body: PairsUpdate):
    if not body.pairs:
        return JSONResponse(
            status_code=400,
            content={"error": "pairs list cannot be empty"}
        )
    config.ACTIVE_PAIRS = body.pairs
    return {
        "success": True,
        "active_pairs": config.ACTIVE_PAIRS
    }


# ================================================================
# POST /limit
# Body: { "limit": 10 }
# Overwrites MAX_SIGNALS_PER_DAY in memory until restart
# ================================================================

@app.post("/limit")
async def update_limit(body: LimitUpdate):
    if body.limit < 1 or body.limit > 999:
        return JSONResponse(
            status_code=400,
            content={"error": "limit must be at least 1"}
        )
    config.MAX_SIGNALS_PER_DAY = body.limit
    return {
        "success": True,
        "daily_limit": config.MAX_SIGNALS_PER_DAY
    }


# ================================================================
# GET /dashboard  (serves the React UI)
# FastAPI will serve the HTML file here.
# We'll fill this in Phase 2 with the actual HTML.
# ================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    dashboard_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "dashboard", "index.html"
    )
    if not os.path.exists(dashboard_path):
        return HTMLResponse("<h2>Dashboard not built yet — Phase 2 pending</h2>")
    with open(dashboard_path, "r") as f:
        return HTMLResponse(f.read())