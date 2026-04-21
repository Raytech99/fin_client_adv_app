"""
Strategy Learner: BagLearner(RTLearner) trained on BB%B, Momentum, RSI.
Labels are generated from 5-day forward returns with impact cost baked in.
One model per symbol, persisted to models/<SYMBOL>_model.pkl.
"""
import os
import joblib
import numpy as np
import pandas as pd

from bot.indicators import bollinger_bands, momentum, rsi
from bot.learners.RTLearner import RTLearner
from bot.learners.BagLearner import BagLearner

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

YBUY = 0.02
YSELL = -0.02
IMPACT = 0.005
FORWARD_DAYS = 5


def _model_path(symbol: str) -> str:
    return os.path.join(MODELS_DIR, f"{symbol}_model.pkl")


def _build_features(prices: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "bb": bollinger_bands(prices),
        "momentum": momentum(prices),
        "rsi": rsi(prices),
    }).dropna()


def _build_labels(prices: pd.Series, features_index) -> pd.Series:
    labels = []
    prices = prices.reindex(features_index)
    for i in range(len(prices) - FORWARD_DAYS):
        ret = (prices.iloc[i + FORWARD_DAYS] / prices.iloc[i]) - 1.0
        if ret > YBUY + IMPACT:
            labels.append(1)
        elif ret < YSELL - IMPACT:
            labels.append(-1)
        else:
            labels.append(0)
    return pd.Series(labels, index=features_index[:-FORWARD_DAYS])


def train(symbol: str, prices: pd.Series) -> None:
    """Train and save a model for the given symbol."""
    features = _build_features(prices)
    labels = _build_labels(prices, features.index)
    common = features.index.intersection(labels.index)
    X = features.loc[common].values.astype(float)
    y = labels.loc[common].values.astype(float)

    model = BagLearner(learner=RTLearner, kwargs={"leaf_size": 5}, bags=20)
    model.add_evidence(X, y)
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, _model_path(symbol))
    print(f"[StrategyLearner] Trained and saved model for {symbol} "
          f"({len(y)} samples)")


def predict(symbol: str, prices: pd.Series) -> int:
    """
    Load saved model and return today's signal: +1, 0, or -1.
    Returns 0 (hold) if no model file exists yet.
    """
    path = _model_path(symbol)
    if not os.path.exists(path):
        print(f"[StrategyLearner] No model found for {symbol}, returning 0")
        return 0

    model = joblib.load(path)
    features = _build_features(prices)
    if features.empty:
        return 0

    today_features = features.iloc[[-1]].values.astype(float)
    raw = model.query(today_features)[0]
    return int(np.round(raw))


def predict_all(symbols: list[str], prices_df: pd.DataFrame) -> dict[str, int]:
    return {s: predict(s, prices_df[s].dropna()) for s in symbols}
