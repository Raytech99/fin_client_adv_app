"""Fetch historical daily OHLCV from Alpaca and return closing price Series."""
import os
from datetime import date, timedelta

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client() -> StockHistoricalDataClient:
    global _client
    if _client is None:
        _client = StockHistoricalDataClient(
            api_key=os.environ["ALPACA_API_KEY"],
            secret_key=os.environ["ALPACA_SECRET_KEY"],
        )
    return _client


def fetch_closes(symbol: str, lookback_days: int = 500) -> pd.Series:
    """Return a Series of adjusted closing prices indexed by date."""
    end = date.today()
    start = end - timedelta(days=lookback_days)

    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        adjustment="all",
    )
    bars = _get_client().get_stock_bars(req).df

    if bars.empty:
        raise ValueError(f"No data returned for {symbol}")

    # Multi-index (symbol, timestamp) → drop symbol level
    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.xs(symbol, level="symbol")

    closes = bars["close"].copy()
    closes.index = pd.to_datetime(closes.index).date
    closes.name = symbol
    return closes.sort_index()


def fetch_closes_multi(symbols: list[str], lookback_days: int = 500) -> pd.DataFrame:
    """Return DataFrame of closing prices, one column per symbol."""
    return pd.DataFrame({s: fetch_closes(s, lookback_days) for s in symbols})
