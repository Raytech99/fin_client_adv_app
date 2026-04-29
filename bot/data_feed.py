"""Fetch historical daily OHLCV from Alpaca and return closing price Series."""
import os
import time
from datetime import date, timedelta
from functools import wraps

import pandas as pd
import requests
import urllib3
import httpx
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

TRANSIENT_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    urllib3.exceptions.ProtocolError,
    ConnectionError,
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadTimeout,
)


def _with_retry(max_attempts: int = 4, backoff: float = 3.0):
    """Retry on transient network errors with exponential backoff."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            delay = backoff
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except TRANSIENT_ERRORS as e:
                    if attempt == max_attempts:
                        raise
                    print(f"[data_feed] {fn.__name__} failed ({type(e).__name__}), "
                          f"retry {attempt}/{max_attempts - 1} in {delay:.0f}s")
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

_client = None


def _get_client() -> StockHistoricalDataClient:
    global _client
    if _client is None:
        _client = StockHistoricalDataClient(
            api_key=os.environ["ALPACA_API_KEY"],
            secret_key=os.environ["ALPACA_SECRET_KEY"],
        )
    return _client


@_with_retry()
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
