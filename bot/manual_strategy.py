"""
Manual Strategy: 2-of-3 indicator voting system.
Ported from ML4T strategy_evaluation project.

Votes:
  BB%B  < -1.0  → +1 (oversold long),  > +1.0 → -1 (overbought short)
  Mom   < -0.05 → +1,                  > +0.05 → -1
  RSI   <  30   → +1,                  >  70   → -1

Signal fires only when sum >= +2 (go long) or <= -2 (go short).
"""
import pandas as pd
from bot.indicators import bollinger_bands, momentum, rsi


def compute_signal(prices: pd.Series) -> int:
    """
    Return today's signal for a single stock: +1, 0, or -1.
    Requires at least 20 days of price history.
    """
    bb = bollinger_bands(prices).iloc[-1]
    mom = momentum(prices).iloc[-1]
    rsi_val = rsi(prices).iloc[-1]

    vote_bb = 1 if bb < -1.0 else (-1 if bb > 1.0 else 0)
    vote_mom = 1 if mom < -0.05 else (-1 if mom > 0.05 else 0)
    vote_rsi = 1 if rsi_val < 30 else (-1 if rsi_val > 70 else 0)

    total = vote_bb + vote_mom + vote_rsi
    if total >= 2:
        return 1
    if total <= -2:
        return -1
    return 0


def compute_signals(prices_df: pd.DataFrame) -> dict[str, int]:
    """Return {symbol: signal} for every column in prices_df."""
    return {symbol: compute_signal(prices_df[symbol].dropna())
            for symbol in prices_df.columns}
