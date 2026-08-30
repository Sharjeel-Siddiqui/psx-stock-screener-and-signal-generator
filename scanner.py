from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from config import SYMBOLS, NTFY_TOPIC
from data_provider import get_daily_history
from strategy import add_indicators
from state import load_state, save_state, signal_key
from ntfy import send_ntfy


TZ = ZoneInfo("Asia/Karachi")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# =====================================================
# FORMAT ALERT MESSAGE
# =====================================================

def format_message(
    symbol: str,
    row,
    action: str,
) -> str:

    if action == "BUY":

        return (
            "🟢 BUY SIGNAL\n\n"
            f"Symbol: {symbol}\n"
            f"Price: {float(row['close']):.2f}\n\n"
            f"EMA 7: {float(row['ema7']):.2f}\n"
            f"EMA 21: {float(row['ema21']):.2f}\n\n"
            "Reason:\n"
            "Golden Cross + 2 Daily Candle Confirmation\n\n"
            "Action: BUY"
        )

    return (
        "🔴 SELL SIGNAL\n\n"
        f"Symbol: {symbol}\n"
        f"Price: {float(row['close']):.2f}\n\n"
        f"EMA 7: {float(row['ema7']):.2f}\n"
        f"EMA 21: {float(row['ema21']):.2f}\n\n"
        "Reason:\n"
        "Death Cross + 2 Daily Candle Confirmation\n\n"
        "Action: SELL ALL"
    )


# =====================================================
# SCAN ONE STOCK
# =====================================================

def scan_symbol(
    symbol: str,
    state: dict,
) -> bool:

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
    # Latest CLOSED daily candle
    # -------------------------------------------------

    row = x.iloc[-1]

    signal_date = row["date"]

    # -------------------------------------------------
    # Signal detection
    # -------------------------------------------------

    action = None

    if bool(row["buy_signal"]):
        action = "BUY"

    elif bool(row["sell_signal"]):
        action = "SELL"

    # -------------------------------------------------
    # No signal
    # -------------------------------------------------

    if action is None:

        logging.info(
            "%s: no signal on %s",
            symbol,
            signal_date,
        )

        return False

    # -------------------------------------------------
    # Prevent duplicate alerts
    # -------------------------------------------------

    key = signal_key(
        symbol,
        action,
        signal_date,
    )

    if key in state["signals"]:

        logging.info(
            "%s: already sent %s on %s",
            symbol,
            action,
            signal_date,
        )

        return False

    # -------------------------------------------------
    # Create notification
    # -------------------------------------------------

    message = format_message(
        symbol,
        row,
        action,
    )

    # -------------------------------------------------
    # Send notification
    # -------------------------------------------------

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
        "SENT %s %s @ %s",
        action,
        symbol,
        row["close"],
    )

    return True


# =====================================================
# MAIN SCANNER
# =====================================================

def main() -> None:

    if not NTFY_TOPIC:

        raise RuntimeError(
            "NTFY_TOPIC is not configured"
        )

    state = load_state()

    sent = 0

    # -------------------------------------------------
    # Scan all stocks
    # -------------------------------------------------

    for symbol in SYMBOLS:

        try:

            if scan_symbol(
                symbol,
                state,
            ):

                sent += 1

        except Exception as exc:

            # IMPORTANT:
            # Never generate a signal from bad data.

            logging.exception(
                "%s: DATA ERROR / scan failed: %s",
                symbol,
                exc,
            )

    # -------------------------------------------------
    # Persist state
    # -------------------------------------------------

    save_state(state)

    logging.info(
        "Scan complete. Alerts sent: %d",
        sent,
    )


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":
    main()