"""
Pairs trading: z-score of the AMD/NVDA price ratio.

The idea: AMD and NVDA are both semiconductors — historically correlated.
When the ratio AMD/NVDA deviates far from its recent mean, bet on convergence.

  z >  entry: ratio is stretched high -> short AMD, long NVDA
  z < -entry: ratio is stretched low  -> long AMD,  short NVDA
  |z| < exit: positions close (spread converged)

Market-neutral: total exposure is ~zero, so we profit only from spread
convergence, not overall market direction.
"""
import pandas as pd

SYMBOL_A = "AMD"
SYMBOL_B = "NVDA"
LOOKBACK = 30           # rolling window for ratio statistics
ENTRY_Z = 2.0           # enter when |z| > 2
EXIT_Z = 0.5            # close when |z| < 0.5


def compute_pair_signal(prices_a: pd.Series, prices_b: pd.Series,
                        prev_signal_a: int = 0) -> dict:
    """
    Return {signal_a, signal_b, z_score, ratio, ratio_mean}.

    signal_a/b in {-1, 0, 1}. They will always be opposites when active
    (pair trade) or both 0 when flat.

    prev_signal_a is passed in so we can apply the hysteresis band: once
    we're in a position we hold until |z| < EXIT_Z, not until z flips.
    """
    ratio = prices_a / prices_b
    rolling = ratio.rolling(LOOKBACK)
    mean = rolling.mean().iloc[-1]
    std = rolling.std().iloc[-1]
    current_ratio = ratio.iloc[-1]
    z = (current_ratio - mean) / std if std > 0 else 0.0

    # Hysteresis: if already in a position, only exit when z inside exit band
    if prev_signal_a != 0:
        if abs(z) < EXIT_Z:
            new_signal_a = 0
        else:
            new_signal_a = prev_signal_a
    else:
        if z > ENTRY_Z:
            new_signal_a = -1    # short AMD, long NVDA
        elif z < -ENTRY_Z:
            new_signal_a = 1     # long AMD, short NVDA
        else:
            new_signal_a = 0

    return {
        "signal_a": new_signal_a,
        "signal_b": -new_signal_a,
        "z_score": round(float(z), 4),
        "ratio": round(float(current_ratio), 6),
        "ratio_mean": round(float(mean), 6) if not pd.isna(mean) else None,
    }
