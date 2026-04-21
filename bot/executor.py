"""
Main daily execution logic.
Called by the scheduler at 3:50 PM ET on market days.
"""
from datetime import date

from bot.data_feed import fetch_closes_multi
from bot.indicators import bollinger_bands, momentum, rsi
from bot.manual_strategy import compute_signals as manual_signals
from bot.strategy_learner import predict_all as ml_signals
from bot.portfolio import (
    get_account, get_positions, get_virtual_equity,
    current_signal_from_position, place_order, SYMBOLS,
)
from bot import db
from bot.reporter import send_daily_report


def run_daily() -> None:
    today = date.today()
    print(f"\n[executor] Running daily cycle for {today}")

    # --- 1. Fetch price data ---
    print("[executor] Fetching price history...")
    prices_df = fetch_closes_multi(SYMBOLS, lookback_days=120)

    # --- 2. Compute signals from both strategies ---
    manual = manual_signals(prices_df)
    ml = ml_signals(SYMBOLS, prices_df)
    print(f"[executor] Manual signals: {manual}")
    print(f"[executor] ML signals (shadow): {ml}")

    # --- 3. Get current account state ---
    positions = get_positions()
    virtual_equity = get_virtual_equity(positions)
    print(f"[executor] Virtual equity: ${virtual_equity:,.2f}")

    # --- 4. Log signals to Supabase ---
    signals_for_email = {}
    for symbol in SYMBOLS:
        prices = prices_df[symbol].dropna()
        bb_val = float(bollinger_bands(prices).iloc[-1])
        mom_val = float(momentum(prices).iloc[-1])
        rsi_val = float(rsi(prices).iloc[-1])

        db.upsert_signal(
            trade_date=today,
            symbol=symbol,
            bb=bb_val,
            mom=mom_val,
            rsi_val=rsi_val,
            manual_signal=manual[symbol],
            ml_signal=ml[symbol],
        )
        signals_for_email[symbol] = {
            "manual": manual[symbol],
            "ml": ml[symbol],
            "bb": bb_val,
            "momentum": mom_val,
            "rsi": rsi_val,
        }

    # --- 5. Execute trades based on Manual Strategy ---
    trades_placed = []
    for symbol in SYMBOLS:
        target = manual[symbol]
        current = current_signal_from_position(symbol, positions)
        current_price = (
            positions[symbol]["current_price"]
            if symbol in positions
            else float(prices_df[symbol].dropna().iloc[-1])
        )
        order = place_order(symbol, target, current, current_price)
        if order:
            print(f"[executor] Order placed: {order}")
            trades_placed.append(order)
            db.insert_trade(
                trade_date=today,
                symbol=symbol,
                action=order["action"],
                shares=order["shares"],
                dollar_amount=order["dollar"],
                price=current_price,
                strategy="manual",
            )

    # --- 6. Snapshot portfolio using virtual $1,700 accounting ---
    positions_after = get_positions()
    virtual_equity_after = get_virtual_equity(positions_after)
    db.upsert_snapshot(
        snap_date=today,
        total_value=virtual_equity_after,
        cash=0.0,  # all undeployed capital is implicit in STARTING_CAPITAL
        positions={s: positions_after.get(s, {}) for s in SYMBOLS},
    )

    # --- 7. Send email ---
    send_daily_report(
        snap_date=today,
        virtual_equity=virtual_equity_after,
        positions=positions_after,
        signals=signals_for_email,
        trades_placed=trades_placed,
    )

    print(f"[executor] Daily cycle complete for {today}\n")


if __name__ == "__main__":
    run_daily()
