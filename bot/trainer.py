"""
Bimonthly retraining: fetches 2 years of history from Alpaca
and retrains one BagLearner model per symbol.
"""
from bot.data_feed import fetch_closes
from bot.strategy_learner import train

SYMBOLS = ["NVDA", "MSFT", "SPY"]
LOOKBACK_DAYS = 730  # ~2 years


def retrain_all() -> None:
    print("[trainer] Starting bimonthly retraining...")
    for symbol in SYMBOLS:
        print(f"[trainer] Fetching {LOOKBACK_DAYS} days of data for {symbol}")
        prices = fetch_closes(symbol, lookback_days=LOOKBACK_DAYS)
        train(symbol, prices)
    print("[trainer] Retraining complete.")


if __name__ == "__main__":
    retrain_all()
