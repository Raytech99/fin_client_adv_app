"""
Momentum strategy: 10/30 SMA crossover, long-only.

When the fast moving average (10-day) crosses ABOVE the slow (30-day),
the trend is up -> go LONG.
When it crosses BELOW, trend is gone -> go FLAT (no shorts).

Applied to trending tech stocks where mean reversion fails.
"""
import pandas as pd

SYMBOLS = ["MSFT", "AAPL", "NVDA"]
FAST_WINDOW = 10
SLOW_WINDOW = 30


def compute_signal(prices: pd.Series) -> int:
    """Return 1 (long) if fast SMA > slow SMA today, else 0 (flat)."""
    fast = prices.rolling(FAST_WINDOW).mean().iloc[-1]
    slow = prices.rolling(SLOW_WINDOW).mean().iloc[-1]
    if pd.isna(fast) or pd.isna(slow):
        return 0
    return 1 if fast > slow else 0


def compute_signal_details(prices: pd.Series) -> dict:
    """Return {signal, fast_sma, slow_sma} for logging."""
    fast = float(prices.rolling(FAST_WINDOW).mean().iloc[-1])
    slow = float(prices.rolling(SLOW_WINDOW).mean().iloc[-1])
    return {
        "signal": 1 if fast > slow else 0,
        "fast_sma": round(fast, 4),
        "slow_sma": round(slow, 4),
    }


def compute_signals(prices_df: pd.DataFrame) -> dict[str, int]:
    return {s: compute_signal(prices_df[s].dropna()) for s in SYMBOLS}
