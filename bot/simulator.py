"""
Virtual portfolio simulator — each strategy gets its own $1,700 account.

Reads yesterday's snapshot from Supabase, applies today's signals at
today's close prices, returns today's updated portfolio state.

Simulation conventions:
  - Each simulated strategy has full $1,700 starting capital.
  - Long positions use fractional shares (full dollar amount deployed).
  - Short positions use whole shares only (matches real Alpaca constraint).
  - Allocation per active position = capital / len(basket).
  - No commissions or slippage (Alpaca paper is idealized anyway).

The state of each strategy is persisted day-to-day in strategy_snapshots.
"""
import math
from datetime import date
from typing import Any

from bot import db

STARTING_CAPITAL = 1700.0


def _load_prev_snapshot(strategy: str) -> dict[str, Any] | None:
    """Return the most recent snapshot for this strategy, or None."""
    res = (
        db._db()
        .table("strategy_snapshots")
        .select("*")
        .eq("strategy", strategy)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _initial_state() -> dict[str, Any]:
    """Fresh strategy with no positions."""
    return {
        "cash": STARTING_CAPITAL,
        "positions": {},     # {symbol: {shares, entry_price, side}}
    }


def _compute_total_value(state: dict, current_prices: dict[str, float]) -> float:
    """
    total = cash + long market values − short liabilities.
    Short proceeds are already in `cash` from when the short was opened,
    so here we only subtract the current buy-back cost (the liability).
    """
    total = state["cash"]
    for symbol, pos in state["positions"].items():
        price = current_prices.get(symbol, pos["entry_price"])
        if pos["side"] == "long":
            total += pos["shares"] * price
        else:  # short — liability to buy back at current price
            total -= pos["shares"] * price
    return total


def _positions_market_value(state: dict, current_prices: dict[str, float]) -> dict:
    """For logging: human-readable position summary with marks."""
    out = {}
    for symbol, pos in state["positions"].items():
        price = current_prices.get(symbol, pos["entry_price"])
        if pos["side"] == "long":
            mv = pos["shares"] * price
            pnl = pos["shares"] * (price - pos["entry_price"])
        else:
            # short: MV is the buy-back liability (negative contribution to equity)
            mv = -(pos["shares"] * price)
            pnl = pos["shares"] * (pos["entry_price"] - price)
        out[symbol] = {
            "side": pos["side"],
            "shares": round(pos["shares"], 4),
            "entry_price": round(pos["entry_price"], 4),
            "current_price": round(price, 4),
            "market_value": round(mv, 2),
            "unrealized_pnl": round(pnl, 2),
        }
    return out


def _close_position(state: dict, symbol: str, current_price: float) -> None:
    """
    Close an open position at current price; update cash.
    Long: sell at current price, cash += shares * current_price.
    Short: buy back at current price, cash -= shares * current_price.
    Net cash change across open+close equals the trade's P&L.
    """
    if symbol not in state["positions"]:
        return
    pos = state["positions"].pop(symbol)
    if pos["side"] == "long":
        state["cash"] += pos["shares"] * current_price
    else:
        state["cash"] -= pos["shares"] * current_price


def _open_long(state: dict, symbol: str, allocation: float, current_price: float) -> None:
    """Open a long position with fractional shares for the given dollar amount."""
    shares = allocation / current_price
    state["cash"] -= allocation
    state["positions"][symbol] = {
        "side": "long",
        "shares": shares,
        "entry_price": current_price,
    }


def _open_short(state: dict, symbol: str, allocation: float, current_price: float) -> None:
    """Open a short position with whole shares (as close to allocation as fits)."""
    whole_shares = math.floor(allocation / current_price)
    if whole_shares < 1:
        # Can't short this stock with available allocation
        return
    proceeds = whole_shares * current_price
    state["cash"] += proceeds
    state["positions"][symbol] = {
        "side": "short",
        "shares": whole_shares,
        "entry_price": current_price,
    }


def _apply_signal(state: dict, symbol: str, target_signal: int,
                  current_price: float, allocation: float) -> None:
    """Reconcile one symbol's position with the target signal."""
    current_pos = state["positions"].get(symbol)
    current_sig = 0
    if current_pos:
        current_sig = 1 if current_pos["side"] == "long" else -1

    if current_sig == target_signal:
        return  # no change

    # Close whatever is open first
    if current_pos:
        _close_position(state, symbol, current_price)

    if target_signal == 1:
        _open_long(state, symbol, allocation, current_price)
    elif target_signal == -1:
        _open_short(state, symbol, allocation, current_price)


def run_simulated_day(
    strategy: str,
    today: date,
    signals: dict[str, int],
    prices: dict[str, float],
    signal_details: dict | None = None,
) -> dict[str, Any]:
    """
    Advance one simulated strategy by one day.

    Args:
      strategy: strategy name (e.g. 'manual', 'momentum', 'pairs', 'ml')
      today: today's date
      signals: {symbol: target_signal}
      prices: {symbol: current_price}
      signal_details: optional metadata to log alongside the snapshot

    Returns the written snapshot dict. Persists to Supabase.
    """
    prev = _load_prev_snapshot(strategy)
    if prev is None:
        state = _initial_state()
    else:
        state = {
            "cash": float(prev["cash"]),
            "positions": {
                s: {
                    "side": p["side"],
                    "shares": float(p["shares"]),
                    "entry_price": float(p["entry_price"]),
                }
                for s, p in (prev.get("positions") or {}).items()
            },
        }

    # Allocation per slot = fraction of STARTING_CAPITAL
    if signals:
        allocation_per_slot = STARTING_CAPITAL / len(signals)
    else:
        allocation_per_slot = STARTING_CAPITAL

    # Apply each signal
    for symbol, sig in signals.items():
        price = prices.get(symbol)
        if price is None:
            continue
        _apply_signal(state, symbol, sig, price, allocation_per_slot)

    total = _compute_total_value(state, prices)
    position_summary = _positions_market_value(state, prices)

    snapshot = {
        "date": str(today),
        "strategy": strategy,
        "total_value": round(total, 4),
        "cash": round(state["cash"], 4),
        "positions": position_summary,
        "signals": signal_details or {s: int(v) for s, v in signals.items()},
    }

    db._db().table("strategy_snapshots").upsert(
        snapshot, on_conflict="date,strategy"
    ).execute()

    return snapshot
