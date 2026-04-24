"""Supabase client and insert helpers with retry on transient network errors."""
import os
import time
from datetime import date
from functools import wraps

import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None

TRANSIENT_ERRORS = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
)


def _with_retry(max_attempts: int = 4, backoff: float = 2.0):
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
                    print(f"[db] {fn.__name__} failed ({type(e).__name__}), "
                          f"retry {attempt}/{max_attempts - 1} in {delay:.0f}s")
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator


def _db() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_KEY"],
        )
    return _client


@_with_retry()
def upsert_signal(
    trade_date: date,
    symbol: str,
    bb: float,
    mom: float,
    rsi_val: float,
    manual_signal: int,
    ml_signal: int,
) -> None:
    _db().table("signals").upsert({
        "date": str(trade_date),
        "symbol": symbol,
        "bb_pct_b": round(bb, 6),
        "momentum": round(mom, 6),
        "rsi": round(rsi_val, 4),
        "manual_signal": manual_signal,
        "ml_signal": ml_signal,
    }, on_conflict="date,symbol").execute()


@_with_retry()
def insert_trade(
    trade_date: date,
    symbol: str,
    action: str,
    shares: float,
    dollar_amount: float,
    price: float,
    strategy: str = "manual",
) -> None:
    _db().table("trades").insert({
        "date": str(trade_date),
        "symbol": symbol,
        "action": action,
        "shares": shares,
        "dollar_amount": round(dollar_amount, 4),
        "price": round(price, 4),
        "strategy": strategy,
    }).execute()


@_with_retry()
def upsert_snapshot(
    snap_date: date,
    total_value: float,
    cash: float,
    positions: dict,
) -> None:
    _db().table("portfolio_snapshots").upsert({
        "date": str(snap_date),
        "total_value": round(total_value, 4),
        "cash": round(cash, 4),
        "positions": positions,
    }, on_conflict="date").execute()


@_with_retry()
def upsert_performance(
    perf_date: date,
    symbol: str,
    daily_pnl: float,
    cumulative_return_pct: float,
) -> None:
    _db().table("daily_performance").upsert({
        "date": str(perf_date),
        "symbol": symbol,
        "daily_pnl": round(daily_pnl, 4),
        "cumulative_return_pct": round(cumulative_return_pct, 6),
    }, on_conflict="date,symbol").execute()
