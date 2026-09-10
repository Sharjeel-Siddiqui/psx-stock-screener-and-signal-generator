from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from config import (
    SYMBOLS,
    NTFY_TOPIC,
    LOOKBACK_CANDLES,
    REMINDER_MAX_AGE_HOURS,
)
from data_provider import get_daily_history
from strategy import add_indicators
from state import load_state, save_state, load_portfolio, save_portfolio, signal_key
from ntfy import send_ntfy
from paper import simulate


TZ = ZoneInfo("Asia/Karachi")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# =====================================================
# ACTION PRESENTATION
# =====================================================
#
# Four alert types now exist:
#
#   EARLY_BUY  - golden cross just formed (day T), NOT yet
#                confirmed by the 2-candle rule
#   BUY        - golden cross confirmed 2 candles later
#   EARLY_SELL - death cross just formed (day T)
#   SELL       - death cross confirmed 2 candles later
#
# The EARLY_* alerts give you the signal ~2 trading days
# sooner; the confirmed alerts are the original behaviour.

ACTION_META = {
    "EARLY_BUY": {
        "title": "⚡ EARLY BUY (UNCONFIRMED)",
        "reason": (
            "Golden Cross just formed.\n"
            "Not yet confirmed by the 2-candle rule."
        ),
        "action": "Action: Watch / early entry",
    },
    "BUY": {
        "title": "🟢 BUY SIGNAL",
        "reason": (
            "Golden Cross + 2 Daily Candle Confirmation"
        ),
        "action": "Action: BUY",
    },
    "EARLY_SELL": {
        "title": "⚡ EARLY SELL (UNCONFIRMED)",
        "reason": (
            "Death Cross just formed.\n"
            "Not yet confirmed by the 2-candle rule."
        ),
        "action": "Action: Watch / consider exit",
    },
    "SELL": {
        "title": "🔴 SELL SIGNAL",
        "reason": (
            "Death Cross + 2 Daily Candle Confirmation"
        ),
        "action": "Action: SELL ALL",
    },
}


# =====================================================
# RUN MODE
# =====================================================
#
#   main     - scan for new signals (default)
#   reminder - re-send the last main run's alerts
#
# Selected by the workflow via the RUN_MODE env var.

def get_run_mode() -> str:
    mode = os.getenv("RUN_MODE", "main").strip().lower()
    return "reminder" if mode == "reminder" else "main"


# =====================================================
# FORMAT ALERT MESSAGE (from a live dataframe row)
# =====================================================

def format_message(
    symbol: str,
    row,
    action: str,
) -> str:

    meta = ACTION_META[action]

    return (
        f"{meta['title']}\n\n"
        f"Symbol: {symbol}\n"
        f"Date: {row['date']}\n"
        f"Price: {float(row['close']):.2f}\n\n"
        f"EMA 7: {float(row['ema7']):.2f}\n"
        f"EMA 21: {float(row['ema21']):.2f}\n\n"
        "Reason:\n"
        f"{meta['reason']}\n\n"
        f"{meta['action']}"
    )


# =====================================================
# FORMAT REMINDER MESSAGE (from stored state)
# =====================================================

def format_reminder(signal: dict) -> str:

    meta = ACTION_META.get(
        signal["action"],
        {
            "title": signal["action"],
            "reason": "",
            "action": "",
        },
    )

    return (
        "⏰ REMINDER\n"
        f"{meta['title']}\n\n"
        f"Symbol: {signal['symbol']}\n"
        f"Date: {signal['date']}\n"
        f"Price: {float(signal['price']):.2f}\n\n"
        f"EMA 7: {float(signal['ema7']):.2f}\n"
        f"EMA 21: {float(signal['ema21']):.2f}\n\n"
        f"{meta['action']}"
    )


# =====================================================
# DETECT ACTIONS ON A SINGLE CANDLE
# =====================================================

def detect_actions(row) -> list[str]:
    """
    Return every alert type present on this candle.

    A single candle never carries both an early and a
    confirmed signal of the same direction, but the early
    one fires on the cross candle and the confirmed one
    fires 2 candles later, so across the lookback window
    both can be sent.
    """

    actions = []

    if bool(row.get("golden_cross", False)):
        actions.append("EARLY_BUY")

    if bool(row.get("buy_signal", False)):
        actions.append("BUY")

    if bool(row.get("death_cross", False)):
        actions.append("EARLY_SELL")

    if bool(row.get("sell_signal", False)):
        actions.append("SELL")

    return actions


# =====================================================
# EMIT ONE SIGNAL (dedupe + send + record)
# =====================================================

def emit_signal(
    symbol: str,
    row,
    action: str,
    state: dict,
) -> bool:

    signal_date = row["date"]

    key = signal_key(
        symbol,
        action,
        signal_date,
    )

    # -------------------------------------------------
    # Prevent duplicate alerts
    # -------------------------------------------------

    if key in state["signals"]:

        logging.info(
            "%s: already sent %s on %s",
            symbol,
            action,
            signal_date,
        )

        return False

    # -------------------------------------------------
    # Send notification
    # -------------------------------------------------

    message = format_message(
        symbol,
        row,
        action,
    )

    send_ntfy(
        NTFY_TOPIC,
        message,
    )

    # -------------------------------------------------
    # Save signal state
    # -------------------------------------------------

    state["signals"][key] = {
        "symbol": symbol,
        "action": action,
        "date": str(signal_date),
        "price": float(row["close"]),
        "ema7": float(row["ema7"]),
        "ema21": float(row["ema21"]),
        "sent_at": datetime.now(TZ).isoformat(),
    }

    logging.info(
        "SENT %s %s @ %s (%s)",
        action,
        symbol,
        row["close"],
        signal_date,
    )

    return True


# =====================================================
# SCAN ONE STOCK
# =====================================================

def scan_symbol(
    symbol: str,
    state: dict,
    portfolio: dict | None = None,
) -> int:
    """
    Scan a single symbol and return how many NEW alerts
    were sent. If a `portfolio` dict is given, also store
    this symbol's simulated 100k paper scenario in it.
    """

    logging.info(
        "Scanning %s",
        symbol
    )

    # -------------------------------------------------
    # Download 3 years of daily data
    # -------------------------------------------------

    df = get_daily_history(
        symbol,
        years=3,
    )

    if df.empty:
        raise ValueError(
            f"{symbol}: empty dataset"
        )

    # -------------------------------------------------
    # Make absolutely sure data is chronological
    # -------------------------------------------------

    df = (
        df
        .sort_values("date")
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # -------------------------------------------------
    # Minimum data requirement
    # -------------------------------------------------

    if len(df) < 30:
        raise ValueError(
            f"{symbol}: insufficient history"
        )

    # -------------------------------------------------
    # Calculate indicators
    # -------------------------------------------------

    x = add_indicators(df)

    # -------------------------------------------------
    # Simulated 100k paper scenario (for the app)
    # -------------------------------------------------

    if portfolio is not None:
        portfolio[symbol] = simulate(symbol, x)

    # -------------------------------------------------
    # Re-check the last N closed candles, oldest first,
    # so a previously-missed signal is still caught and
    # alerts arrive in chronological order.
    # -------------------------------------------------

    recent = x.tail(LOOKBACK_CANDLES)

    sent = 0
    saw_signal = False

    for _, row in recent.iterrows():

        for action in detect_actions(row):

            saw_signal = True

            if emit_signal(
                symbol,
                row,
                action,
                state,
            ):
                sent += 1

    if not saw_signal:

        logging.info(
            "%s: no signal in last %d candles (as of %s)",
            symbol,
            LOOKBACK_CANDLES,
            x.iloc[-1]["date"],
        )

    return sent


# =====================================================
# MAIN SCAN (mode = main)
# =====================================================

def run_scan(state: dict, portfolio: dict) -> int:

    sent = 0

    for symbol in SYMBOLS:

        try:

            sent += scan_symbol(
                symbol,
                state,
                portfolio,
            )

        except Exception as exc:

            # IMPORTANT:
            # Never generate a signal from bad data.

            logging.exception(
                "%s: DATA ERROR / scan failed: %s",
                symbol,
                exc,
            )

    return sent


# =====================================================
# REMINDER RUN (mode = reminder)
# =====================================================
#
# Re-send the alerts fired by the last main run. No market
# data is fetched. Only alerts sent within the last
# REMINDER_MAX_AGE_HOURS are re-sent, and each is reminded
# at most once.

def run_reminder(state: dict) -> int:

    now = datetime.now(TZ)
    reminded = 0

    for signal in state["signals"].values():

        # Already reminded once — skip.
        if signal.get("reminded_at"):
            continue

        sent_at_raw = signal.get("sent_at")

        if not sent_at_raw:
            continue

        try:
            sent_at = datetime.fromisoformat(sent_at_raw)
        except Exception:
            continue

        age_hours = (now - sent_at).total_seconds() / 3600.0

        # Too old — not part of the last main run.
        if age_hours > REMINDER_MAX_AGE_HOURS:
            continue

        send_ntfy(
            NTFY_TOPIC,
            format_reminder(signal),
        )

        signal["reminded_at"] = now.isoformat()
        reminded += 1

        logging.info(
            "REMINDED %s %s (%s)",
            signal["action"],
            signal["symbol"],
            signal["date"],
        )

    return reminded


# =====================================================
# ENTRY POINT
# =====================================================

def main() -> None:

    if not NTFY_TOPIC:

        raise RuntimeError(
            "NTFY_TOPIC is not configured"
        )

    mode = get_run_mode()
    state = load_state()

    logging.info("Run mode: %s", mode)

    portfolio: dict = {}

    if mode == "reminder":
        count = run_reminder(state)
    else:
        count = run_scan(state, portfolio)
        # Only the main scan recomputes the paper scenarios. IMPORTANT:
        # never wipe good data when PSX was unreachable — if we got some
        # symbols, merge them over the last-saved file; if we got nothing,
        # leave the existing portfolio.json untouched.
        if portfolio:
            merged = load_portfolio()
            merged.update(portfolio)
            save_portfolio(merged)
        else:
            logging.warning(
                "No portfolio data this run (PSX unreachable?); "
                "keeping the previous portfolio.json."
            )

    # -------------------------------------------------
    # Persist state
    # -------------------------------------------------

    save_state(state)

    logging.info(
        "%s complete. Notifications sent: %d",
        mode.capitalize(),
        count,
    )


if __name__ == "__main__":
    main()
