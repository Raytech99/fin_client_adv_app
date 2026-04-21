"""Supabase client and insert helpers."""
import os
from datetime import date

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def _db() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_KEY"],
        )
    return _client


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
