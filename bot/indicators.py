import pandas as pd


def bollinger_bands(prices: pd.Series, window: int = 20) -> pd.Series:
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    return (prices - sma) / (2.0 * std)


def momentum(prices: pd.Series, window: int = 14) -> pd.Series:
    return (prices / prices.shift(window)) - 1.0


def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    delta = prices.diff()
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)
    avg_gain = gains.rolling(window=window).mean()
    avg_loss = losses.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_all(prices: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "bb": bollinger_bands(prices),
        "momentum": momentum(prices),
        "rsi": rsi(prices),
    })
