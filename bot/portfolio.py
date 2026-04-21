"""
Position sizing and portfolio state from Alpaca.
Each symbol gets an equal share of total equity.
Long  → dollar order (fractional shares supported).
Short → whole shares only (Alpaca restriction).
"""
import os
import math

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    ClosePositionRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv

load_dotenv()

SYMBOLS = ["NVDA", "MSFT", "SPY"]
STARTING_CAPITAL = 1700.0
ALLOCATION_PER_STOCK = STARTING_CAPITAL / len(SYMBOLS)  # ~$567

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
    """Return {symbol: {side, qty, market_value, current_price}}."""
    positions = {}
    for p in _tc().get_all_positions():
        positions[p.symbol] = {
            "side": p.side.value,
            "qty": float(p.qty),
            "market_value": float(p.market_value),
            "current_price": float(p.current_price),
            "unrealized_pl": float(p.unrealized_pl),
        }
    return positions


def get_virtual_equity(positions: dict) -> float:
    """
    Virtual portfolio value = $1,700 starting capital + unrealized P&L
    across our 3 managed positions. Ignores the $98k+ Alpaca paper cash
    we never touch — keeps accounting comparable to a real $1,700 account.
    """
    unrealized = sum(
        positions[s]["unrealized_pl"]
        for s in SYMBOLS
        if s in positions
    )
    return STARTING_CAPITAL + unrealized


def current_signal_from_position(symbol: str, positions: dict) -> int:
    """Infer current held signal from open position: +1, 0, or -1."""
    if symbol not in positions:
        return 0
    side = positions[symbol]["side"]
    return 1 if side == "long" else -1


def place_order(
    symbol: str,
    target_signal: int,
    current_signal: int,
    current_price: float,
) -> dict | None:
    """
    Reconcile current position with target signal.
    Returns order info dict or None if no trade needed.
    """
    if target_signal == current_signal:
        return None

    allocation = ALLOCATION_PER_STOCK

    # Close existing position first if we're flipping sides
    if current_signal != 0:
        _tc().close_position(symbol)

    if target_signal == 0:
        return {"action": "close", "symbol": symbol, "shares": 0, "dollar": 0}

    if target_signal == 1:
        req = MarketOrderRequest(
            symbol=symbol,
            notional=round(allocation, 2),
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        _tc().submit_order(req)
        return {
            "action": "buy",
            "symbol": symbol,
            "shares": allocation / current_price,
            "dollar": allocation,
        }

    if target_signal == -1:
        whole_shares = math.floor(allocation / current_price)
        if whole_shares < 1:
            print(f"[portfolio] Insufficient allocation to short {symbol} "
                  f"(need ≥${current_price:.2f}, have ${allocation:.2f})")
            return None
        req = MarketOrderRequest(
            symbol=symbol,
            qty=whole_shares,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        _tc().submit_order(req)
        return {
            "action": "short",
            "symbol": symbol,
            "shares": whole_shares,
            "dollar": whole_shares * current_price,
        }
