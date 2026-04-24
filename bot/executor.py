"""
Daily execution — runs all 5 strategies.

Real trades: VGT buy-and-hold only (one-time purchase, then just marked to market).
Simulated:  Manual (mean-rev), ML shadow, Momentum, Pairs — each with own $1,700.

Fires at 3:50 PM ET Mon-Fri via launchd.
"""
import time
from datetime import date

from bot.data_feed import fetch_closes_multi
from bot.indicators import bollinger_bands, momentum as ind_momentum, rsi
from bot.manual_strategy import compute_signals as manual_signals
from bot.strategy_learner import predict_all as ml_signals
from bot.momentum_strategy import (
    compute_signals as momentum_signals,
    compute_signal_details as momentum_details,
    SYMBOLS as MOMENTUM_SYMBOLS,
)
from bot.pairs_strategy import (
    compute_pair_signal,
    SYMBOL_A as PAIR_A,
    SYMBOL_B as PAIR_B,
)
from bot.portfolio import (
    ensure_vgt_initialized,
    get_vgt_virtual_equity,
    get_positions,
    REAL_SYMBOL,
)
from bot import db
from bot.simulator import run_simulated_day, _load_prev_snapshot
from bot.reporter import send_daily_report

MEAN_REV_SYMBOLS = ["JPM", "KO", "XOM"]
ALL_DATA_SYMBOLS = list(set(MEAN_REV_SYMBOLS + MOMENTUM_SYMBOLS + [PAIR_A, PAIR_B, REAL_SYMBOL]))


def run_daily() -> None:
    today = date.today()
    print(f"\n[executor] Running daily cycle for {today}")
    print("[executor] Waiting 15s for network to settle...")
    time.sleep(15)

    # ── 1. Fetch price history for every symbol we care about ─────────────────
    print("[executor] Fetching price history...")
    prices_df = fetch_closes_multi(ALL_DATA_SYMBOLS, lookback_days=120)
    current_prices = {s: float(prices_df[s].dropna().iloc[-1]) for s in ALL_DATA_SYMBOLS}

    # ── 2. One-time: make sure VGT is bought with $1,700 ─────────────────────
    vgt_order = ensure_vgt_initialized()
    if vgt_order:
        db.insert_trade(
            trade_date=today,
            symbol=REAL_SYMBOL,
            action="buy",
            shares=vgt_order["dollar_amount"] / current_prices[REAL_SYMBOL],
            dollar_amount=vgt_order["dollar_amount"],
            price=current_prices[REAL_SYMBOL],
            strategy="vgt_real",
        )

    # ── 3. Manual Strategy (simulated on mean-rev stocks) ────────────────────
    mean_rev_prices = prices_df[MEAN_REV_SYMBOLS]
    manual = manual_signals(mean_rev_prices)
    print(f"[executor] Manual signals: {manual}")

    # Log indicator values into the existing signals table for transparency
    signal_details_manual = {}
    for sym in MEAN_REV_SYMBOLS:
        p = mean_rev_prices[sym].dropna()
        bb = float(bollinger_bands(p).iloc[-1])
        mom = float(ind_momentum(p).iloc[-1])
        rsi_val = float(rsi(p).iloc[-1])
        signal_details_manual[sym] = {
            "signal": manual[sym],
            "bb": bb,
            "momentum": mom,
            "rsi": rsi_val,
        }

    run_simulated_day(
        strategy="manual",
        today=today,
        signals=manual,
        prices={s: current_prices[s] for s in MEAN_REV_SYMBOLS},
        signal_details=signal_details_manual,
    )

    # ── 4. ML Shadow (same universe as Manual) ────────────────────────────────
    ml = ml_signals(MEAN_REV_SYMBOLS, mean_rev_prices)
    print(f"[executor] ML signals: {ml}")

    run_simulated_day(
        strategy="ml",
        today=today,
        signals=ml,
        prices={s: current_prices[s] for s in MEAN_REV_SYMBOLS},
        signal_details={s: {"signal": ml[s]} for s in MEAN_REV_SYMBOLS},
    )

    # ── 5. Momentum Strategy ─────────────────────────────────────────────────
    mom_prices = prices_df[MOMENTUM_SYMBOLS]
    mom_sigs = momentum_signals(mom_prices)
    print(f"[executor] Momentum signals: {mom_sigs}")

    mom_details = {
        s: momentum_details(mom_prices[s].dropna()) for s in MOMENTUM_SYMBOLS
    }

    run_simulated_day(
        strategy="momentum",
        today=today,
        signals=mom_sigs,
        prices={s: current_prices[s] for s in MOMENTUM_SYMBOLS},
        signal_details=mom_details,
    )

    # ── 6. Pairs Trading (AMD / NVDA) ────────────────────────────────────────
    prev_pair_snap = _load_prev_snapshot("pairs")
    prev_sig_a = 0
    if prev_pair_snap and prev_pair_snap.get("positions"):
        a_pos = prev_pair_snap["positions"].get(PAIR_A)
        if a_pos:
            prev_sig_a = 1 if a_pos["side"] == "long" else -1

    pair_info = compute_pair_signal(
        prices_df[PAIR_A].dropna(),
        prices_df[PAIR_B].dropna(),
        prev_signal_a=prev_sig_a,
    )
    print(f"[executor] Pair signal: z={pair_info['z_score']} "
          f"-> {PAIR_A}={pair_info['signal_a']}, {PAIR_B}={pair_info['signal_b']}")

    run_simulated_day(
        strategy="pairs",
        today=today,
        signals={PAIR_A: pair_info["signal_a"], PAIR_B: pair_info["signal_b"]},
        prices={PAIR_A: current_prices[PAIR_A], PAIR_B: current_prices[PAIR_B]},
        signal_details=pair_info,
    )

    # ── 7. VGT real portfolio — just snapshot mark-to-market ────────────────
    vgt_equity = get_vgt_virtual_equity()
    vgt_positions = get_positions()
    db._db().table("strategy_snapshots").upsert({
        "date": str(today),
        "strategy": "vgt_real",
        "total_value": round(vgt_equity, 4),
        "cash": 0.0,
        "positions": {
            REAL_SYMBOL: {
                "side": "long",
                "shares": vgt_positions.get(REAL_SYMBOL, {}).get("qty", 0),
                "current_price": current_prices[REAL_SYMBOL],
                "market_value": vgt_positions.get(REAL_SYMBOL, {}).get("market_value", 0),
                "unrealized_pnl": vgt_positions.get(REAL_SYMBOL, {}).get("unrealized_pl", 0),
            }
        },
        "signals": {"action": "buy_and_hold"},
    }, on_conflict="date,strategy").execute()

    # ── 8. Keep portfolio_snapshots in sync (dashboard compatibility) ───────
    db.upsert_snapshot(
        snap_date=today,
        total_value=vgt_equity,
        cash=0.0,
        positions={REAL_SYMBOL: vgt_positions.get(REAL_SYMBOL, {})},
    )

    # ── 9. Send daily email ──────────────────────────────────────────────────
    send_daily_report(snap_date=today)

    print(f"[executor] Daily cycle complete for {today}\n")


if __name__ == "__main__":
    run_daily()
