from __future__ import annotations

import pandas as pd


def pine_ema(series: pd.Series, length: int) -> pd.Series:
    """
    Pine-compatible recursive EMA approximation.

    TradingView ta.ema uses alpha = 2/(length+1). We seed the EMA
    with the first SMA(length) and then apply the recursive formula.
    """
    s = pd.to_numeric(series, errors="coerce").astype(float)
    out = pd.Series(float("nan"), index=s.index, dtype=float)

    valid = s.dropna()
    if len(valid) < length:
        return out

    first_pos = valid.index[length - 1]
    seed = valid.iloc[:length].mean()
    out.loc[first_pos] = seed

    alpha = 2.0 / (length + 1.0)
    prev = seed

    for idx in valid.index[length:]:
        prev = alpha * float(valid.loc[idx]) + (1.0 - alpha) * prev
        out.loc[idx] = prev

    return out


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["ema7"] = pine_ema(x["close"], 7)
    x["ema21"] = pine_ema(x["close"], 21)

    # ta.crossover(a,b): current a>b AND previous a<=b
    x["golden_cross"] = (
        (x["ema7"] > x["ema21"]) &
        (x["ema7"].shift(1) <= x["ema21"].shift(1))
    )

    # ta.crossunder(a,b): current a<b AND previous a>=b
    x["death_cross"] = (
        (x["ema7"] < x["ema21"]) &
        (x["ema7"].shift(1) >= x["ema21"].shift(1))
    )

    # Equivalent to ta.barssince(goldenCross) == 2:
    # a cross on t-2, with no newer cross in t-1 or t.
    x["golden_bars_2"] = (
        x["golden_cross"].shift(2).fillna(False) &
        ~x["golden_cross"].shift(1).fillna(False) &
        ~x["golden_cross"].fillna(False)
    )

    x["death_bars_2"] = (
        x["death_cross"].shift(2).fillna(False) &
        ~x["death_cross"].shift(1).fillna(False) &
        ~x["death_cross"].fillna(False)
    )

    x["buy_signal"] = x["golden_bars_2"] & (x["ema7"] > x["ema21"])
    x["sell_signal"] = x["death_bars_2"] & (x["ema7"] < x["ema21"])

    return x


def signals(df: pd.DataFrame) -> pd.DataFrame:
    x = add_indicators(df)
    return x.loc[x["buy_signal"] | x["sell_signal"],
                 ["date", "close", "ema7", "ema21", "buy_signal", "sell_signal"]].copy()
