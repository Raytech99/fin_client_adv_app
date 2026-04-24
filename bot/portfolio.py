"""
Real Alpaca portfolio: buy-and-hold VGT with $1,700.

This is the only strategy that places actual orders. The 4 simulated
strategies run in parallel in simulator.py with their own virtual cash.
"""
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv

load_dotenv()

REAL_SYMBOL = "VGT"
STARTING_CAPITAL = 1700.0

_trading_client: TradingClient | None = None


def _tc() -> TradingClient:
    global _trading_client
    if _trading_client is None:
        _trading_client = TradingClient(
            api_key=os.environ["ALPACA_API_KEY"],
            secret_key=os.environ["ALPACA_SECRET_KEY"],
            paper=True,
        )
    return _trading_client


def get_account() -> dict:
    acct = _tc().get_account()
    return {
        "equity": float(acct.equity),
        "cash": float(acct.cash),
        "buying_power": float(acct.buying_power),
    }


def get_positions() -> dict[str, dict]:
    positions = {}
    for p in _tc().get_all_positions():
        positions[p.symbol] = {
            "side": p.side.value,
            "qty": float(p.qty),
            "market_value": float(p.market_value),
            "current_price": float(p.current_price),
            "unrealized_pl": float(p.unrealized_pl),
            "cost_basis": float(p.cost_basis),
        }
    return positions


def ensure_vgt_initialized() -> dict | None:
    """
    If we don't already hold VGT, place a one-time $1,700 fractional buy.
    Returns the order info if a buy was placed, None otherwise.
    """
    positions = get_positions()
    if REAL_SYMBOL in positions:
        return None

    req = MarketOrderRequest(
        symbol=REAL_SYMBOL,
        notional=round(STARTING_CAPITAL, 2),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )
    _tc().submit_order(req)
    print(f"[portfolio] Initial ${STARTING_CAPITAL} VGT buy submitted.")
    return {
        "action": "buy",
        "symbol": REAL_SYMBOL,
        "dollar_amount": STARTING_CAPITAL,
    }


def get_vgt_virtual_equity() -> float:
    """
    VGT-denominated virtual portfolio value.
    = cost basis + unrealized P&L on our VGT position.
    If we have no position yet, return STARTING_CAPITAL.
    """
    positions = get_positions()
    if REAL_SYMBOL not in positions:
        return STARTING_CAPITAL
    p = positions[REAL_SYMBOL]
    return p["cost_basis"] + p["unrealized_pl"]
