from __future__ import annotations

import logging
import random
import time

import pandas as pd
import psxdata


logger = logging.getLogger(__name__)


# How many times to retry a single symbol's fetch, and the base
# backoff (seconds). PSX (dps.psx.com.pk) is occasionally unreachable
# from GitHub's runners; a few spaced-out retries ride out brief blips.
_FETCH_ATTEMPTS = 4
_FETCH_BACKOFF = 4.0


def _fetch_stocks(symbol: str, start, end):
    """Call psxdata.stocks with retries + exponential backoff."""
    last_err = None
    for attempt in range(1, _FETCH_ATTEMPTS + 1):
        try:
            return psxdata.stocks(symbol, start=str(start), end=str(end))
        except Exception as exc:  # noqa: BLE001 - PSX/network flakiness
            last_err = exc
            if attempt < _FETCH_ATTEMPTS:
                wait = _FETCH_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 2)
                logger.warning(
                    "%s: fetch attempt %d/%d failed (%s); retrying in %.1fs",
                    symbol, attempt, _FETCH_ATTEMPTS, exc, wait,
                )
                time.sleep(wait)
    raise last_err


def get_daily_history(symbol: str, years: int = 3) -> pd.DataFrame:
    """
    Fetch PSX daily OHLCV history using psxdata.

    The returned dataframe is normalized and guaranteed to be:
        - chronological
        - duplicate-date free
        - numeric
        - free of invalid/missing dates
        - free of missing close prices

    We do NOT silently invent or modify prices.
    """

    end = pd.Timestamp.now(tz="Asia/Karachi").date()
    start = (pd.Timestamp(end) - pd.DateOffset(years=years)).date()

    logger.info(
        "%s: requesting data from %s to %s",
        symbol,
        start,
        end,
    )

    # -------------------------------------------------
    # FETCH DATA
    # -------------------------------------------------

    df = _fetch_stocks(symbol, start, end)

    if df is None or len(df) == 0:
        raise ValueError(f"No data returned for {symbol}")

    df = df.copy()

    # -------------------------------------------------
    # NORMALIZE COLUMN NAMES
    # -------------------------------------------------

    df.columns = [
        str(column).lower().strip()
        for column in df.columns
    ]

    # -------------------------------------------------
    # NORMALIZE DATE
    # -------------------------------------------------

    if "date" not in df.columns:

        if isinstance(df.index, pd.DatetimeIndex):

            df = df.reset_index()

            df.columns = [
                str(column).lower().strip()
                for column in df.columns
            ]

        else:
            raise ValueError(
                f"{symbol}: could not find a date column"
            )

    # Sometimes reset_index can produce a column called
    # "index" instead of "date".
    if "date" not in df.columns:

        possible_date_columns = [
            column
            for column in df.columns
            if "date" in str(column).lower()
        ]

        if len(possible_date_columns) == 1:
            df = df.rename(
                columns={
                    possible_date_columns[0]: "date"
                }
            )

    # -------------------------------------------------
    # REQUIRED COLUMNS
    # -------------------------------------------------

    required = {"date", "close"}

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{symbol}: missing columns {sorted(missing)}"
        )

    # -------------------------------------------------
    # DATE CONVERSION
    # -------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    invalid_dates = int(df["date"].isna().sum())

    if invalid_dates:
        logger.warning(
            "%s: removing %d rows with invalid dates",
            symbol,
            invalid_dates,
        )

    df = df.dropna(
        subset=["date"]
    )

    # Convert to timezone-naive calendar dates.
    df["date"] = df["date"].dt.date

    # -------------------------------------------------
    # NUMERIC OHLCV
    # -------------------------------------------------

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # -------------------------------------------------
    # REMOVE MISSING CLOSE
    # -------------------------------------------------

    missing_close = int(df["close"].isna().sum())

    if missing_close:
        logger.warning(
            "%s: removing %d rows with missing close",
            symbol,
            missing_close,
        )

    df = df.dropna(
        subset=["close"]
    )

    # -------------------------------------------------
    # REMOVE DUPLICATE DATES
    # -------------------------------------------------

    duplicate_count = int(
        df.duplicated(
            subset=["date"],
            keep=False,
        ).sum()
    )

    if duplicate_count:
        logger.warning(
            "%s: found %d duplicate-date rows; "
            "keeping the last record for each date",
            symbol,
            duplicate_count,
        )

    df = (
        df
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
    )

    # -------------------------------------------------
    # SORT CHRONOLOGICALLY
    # -------------------------------------------------

    df = (
        df
        .sort_values(
            by="date",
            ascending=True,
            kind="stable",
        )
        .reset_index(drop=True)
    )

    # -------------------------------------------------
    # FINAL DATE RANGE FILTER
    # -------------------------------------------------

    df = df[
        (df["date"] >= start) &
        (df["date"] <= end)
    ].copy()

    # -------------------------------------------------
    # FINAL VALIDATION
    # -------------------------------------------------

    if df.empty:
        raise ValueError(
            f"{symbol}: no valid data remains after cleaning"
        )

    if not df["date"].is_monotonic_increasing:
        raise ValueError(
            f"{symbol}: data is still not chronological "
            "after cleaning"
        )

    if df["date"].duplicated().any():
        raise ValueError(
            f"{symbol}: duplicate dates remain after cleaning"
        )

    if df["close"].isna().any():
        raise ValueError(
            f"{symbol}: missing close values remain"
        )

    # -------------------------------------------------
    # OPTIONAL OHLC VALIDATION
    # -------------------------------------------------
    #
    # We FLAG suspicious OHLC rows rather than deleting
    # them automatically. The close series is still kept
    # intact because EMA is based on CLOSE.
    #
    # This prevents us from accidentally changing the
    # historical price series and producing signals that
    # differ from TradingView.
    # -------------------------------------------------

    if all(
        column in df.columns
        for column in ["open", "high", "low", "close"]
    ):

        valid_ohlc = (
            (df["high"] >= df["low"]) &
            (df["high"] >= df["open"]) &
            (df["high"] >= df["close"]) &
            (df["low"] <= df["open"]) &
            (df["low"] <= df["close"])
        )

        invalid_ohlc = ~valid_ohlc

        invalid_count = int(
            invalid_ohlc.sum()
        )

        if invalid_count:

            logger.warning(
                "%s: %d suspicious OHLC rows detected; "
                "rows retained for close/EMA calculations",
                symbol,
                invalid_count,
            )

    # -------------------------------------------------
    # RESULT
    # -------------------------------------------------

    logger.info(
        "%s: %d valid daily candles loaded "
        "(%s → %s)",
        symbol,
        len(df),
        df.iloc[0]["date"],
        df.iloc[-1]["date"],
    )

    return df
