# ============================================================
# HOPE OPTIONS — Confluence Scorer
# Scores a setup from 0-100 before any signal is sent
# Minimum 75/100 required to generate a signal
# ============================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MIN_CONFLUENCE_SCORE, MIN_INDICATORS_AGREE


def calculate_score(mtf_result: dict, regime: dict, session: dict, news: dict) -> dict:
    """
    Scores a trade setup based on all filters combined.
    Returns score 0-100 and breakdown.
    """
    score    = 0
    breakdown = []

    # ── 1. Regime Score (25 points) ──
    if regime.get("tradeable"):
        regime_type = regime.get("regime", "")
        adx         = regime.get("adx", 0)

        if regime_type == "TRENDING" and adx >= 30:
            score += 25
            breakdown.append(f"Strong trend (ADX={adx}) +25")
        elif regime_type == "TRENDING":
            score += 20
            breakdown.append(f"Trending (ADX={adx}) +20")
        elif regime_type == "RANGING":
            score += 18
            breakdown.append(f"Ranging market +18")
    else:
        breakdown.append("Choppy/untradeable regime +0")

    # ── 2. MTF Alignment Score (25 points) ──
    bias_15m = mtf_result.get("bias_15m", {}).get("bias", "NEUTRAL")
    bias_5m  = mtf_result.get("bias_5m",  {}).get("bias", "NEUTRAL")
    bias_1m  = mtf_result.get("bias_1m",  {}).get("bias", "NEUTRAL")
    direction = mtf_result.get("direction", "NEUTRAL")

    if direction != "NEUTRAL":
        aligned_count = [bias_15m, bias_5m, bias_1m].count(direction)
        if aligned_count == 3:
            score += 25
            breakdown.append("All 3 timeframes aligned +25")
        elif aligned_count == 2:
            score += 18
            breakdown.append("2/3 timeframes aligned +18")
        else:
            breakdown.append("MTF not aligned +0")
    else:
        breakdown.append("No MTF direction +0")

    # ── 3. Indicator Agreement Score (30 points) ──
    bias_5m_data   = mtf_result.get("bias_5m", {})
    indicators_5m  = bias_5m_data.get("labels", [])
    direction       = mtf_result.get("direction", "NEUTRAL")

    # Count how many indicator labels contain ✅
    confirmed = sum(1 for label in indicators_5m if "✅" in label)

    if confirmed >= 5:
        score += 30
        breakdown.append(f"5/5 indicators agree +30")
    elif confirmed == 4:
        score += 25
        breakdown.append(f"4/5 indicators agree +25")
    elif confirmed == 3:
        score += 15
        breakdown.append(f"3/5 indicators agree +15")
    elif confirmed == 2:
        score += 8
        breakdown.append(f"2/5 indicators agree +8")
    else:
        breakdown.append(f"<2 indicators agree +0")

    # ── 4. Session Score (10 points) ──
    if session.get("active"):
        session_name = session.get("session", "")
        if session_name == "ny_overlap":
            score += 10
            breakdown.append("NY/London Overlap (best session) +10")
        elif session_name in ["london_open", "ny_open"]:
            score += 8
            breakdown.append(f"{session.get('session_label')} session +8")
        else:
            score += 5
            breakdown.append("Active session +5")
    else:
        breakdown.append("Outside session +0")

    # ── 5. News Clear Bonus (10 points) ──
    if not news.get("blocked"):
        score += 10
        breakdown.append("No news nearby +10")
    else:
        score -= 20
        breakdown.append("News blocking signal -20")

    # ── Final Verdict ──
    score = max(0, min(100, score))  # Clamp 0-100

    signal_valid = (
        score >= MIN_CONFLUENCE_SCORE and
        mtf_result.get("direction") != "NEUTRAL" and
        not news.get("blocked") and
        session.get("active") and
        regime.get("tradeable")
    )

    return {
        "score":        score,
        "signal_valid": signal_valid,
        "direction":    mtf_result.get("direction", "NEUTRAL"),
        "breakdown":    breakdown,
        "verdict":      f"Score {score}/100 — {'✅ SIGNAL' if signal_valid else '❌ NO SIGNAL'}"
    }


def test_scorer():
    from core.mtf_analyzer import analyze_mtf
    from signals.session_filter import is_trading_session
    from signals.news_filter import is_news_blocked

    print("Testing confluence scorer...\n")

    for pair in ["EURUSD", "GBPUSD"]:
        print(f"{'='*50}")
        print(f"Scoring {pair}...")

        mtf     = analyze_mtf(pair)
        regime  = mtf["regime"]
        session = is_trading_session()
        news    = is_news_blocked(pair)
        result  = calculate_score(mtf, regime, session, news)

        print(f"Direction : {result['direction']}")
        print(f"Score     : {result['score']}/100")
        print(f"Verdict   : {result['verdict']}")
        print(f"\nBreakdown:")
        for item in result["breakdown"]:
            print(f"  {item}")
        print()


if __name__ == "__main__":
    test_scorer()