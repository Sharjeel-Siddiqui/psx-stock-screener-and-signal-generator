from __future__ import annotations

import pandas as pd
import psxdata


def get_daily_history(symbol: str, years: int = 3) -> pd.DataFrame:
    """
    Fetch PSX daily OHLCV history using the free/open-source psxdata package.
    """
    end = pd.Timestamp.now(tz="Asia/Karachi").date()
    start = (pd.Timestamp(end) - pd.DateOffset(years=years)).date()

    df = psxdata.stocks(
        symbol,
        start=str(start),
        end=str(end),
    )

    if df is None or len(df) == 0:
        raise ValueError(f"No data returned for {symbol}")

    df = df.copy()
    df.columns = [str(c).lower().strip() for c in df.columns]

    # Normalize common date/index layouts.
    if "date" not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            df.columns = [str(c).lower().strip() for c in df.columns]
        else:
            raise ValueError(f"Could not find a date column for {symbol}")

    required = {"date", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{symbol}: missing columns {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date", "close"]).sort_values("date")
    df = df.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)

    return df
