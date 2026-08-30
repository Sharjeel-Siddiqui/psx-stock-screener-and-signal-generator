from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from config import SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from data_provider import get_daily_history
from strategy import add_indicators
from state import load_state, save_state, signal_key
from telegram import send_telegram

TZ = ZoneInfo("Asia/Karachi")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def format_message(symbol: str, row, action: str) -> str:
    emoji = "🟢" if action == "BUY" else "🔴"
    reason = (
        "Golden Cross + 2 Daily Candle Confirmation"
        if action == "BUY"
        else "Death Cross + 2 Daily Candle Confirmation"
    )
    return (
        f"{emoji} {action} SIGNAL\n\n"
        f"Symbol: {symbol}\n"
        f"Price: {float(row['close']):.4f}\n"
        f"EMA 7: {float(row['ema7']):.4f}\n"
        f"EMA 21: {float(row['ema21']):.4f}\n\n"
        f"Reason: {reason}\n"
        f"Signal date: {row['date']}\n"
        f"Action: {'BUY' if action == 'BUY' else 'SELL ALL'}"
    )


def scan_symbol(symbol: str, state: dict) -> bool:
    logging.info("Scanning %s", symbol)
    df = get_daily_history(symbol, years=3)

    # Only evaluate a candle that is already present as an EOD bar.
    # The GitHub workflow runs after the PSX session. If the provider
    # ever returns a current/incomplete date, skip it.
    today_pk = datetime.now(TZ).date()
    df = df[df["date"] <= today_pk].copy()

    if len(df) < 30:
        raise ValueError(f"{symbol}: insufficient history")

    x = add_indicators(df)
    row = x.iloc[-1]

    # We only act on today's latest EOD row. If the provider's latest
    # row is not today's date, it may be a holiday/weekend or delayed.
    # In that case the latest row is still a closed candle, and can be
    # processed exactly once.
    signal_date = row["date"]

    action = None
    if bool(row["buy_signal"]):
        action = "BUY"
    elif bool(row["sell_signal"]):
        action = "SELL"

    if not action:
        logging.info("%s: no signal on %s", symbol, signal_date)
        return False

    key = signal_key(symbol, action, signal_date)
    if key in state["signals"]:
        logging.info("%s: already sent %s on %s", symbol, action, signal_date)
        return False

    message = format_message(symbol, row, action)
    send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

    state["signals"][key] = {
        "symbol": symbol,
        "action": action,
        "date": str(signal_date),
        "price": float(row["close"]),
        "ema7": float(row["ema7"]),
        "ema21": float(row["ema21"]),
        "sent_at": datetime.now(TZ).isoformat(),
    }
    logging.info("SENT %s %s @ %s", action, symbol, row["close"])
    return True


def main() -> None:
    state = load_state()
    sent = 0

    for symbol in SYMBOLS:
        try:
            if scan_symbol(symbol, state):
                sent += 1
        except Exception as exc:
            # Fail safely: never create a signal from bad/missing data.
            logging.exception("%s: DATA ERROR / scan failed: %s", symbol, exc)

    save_state(state)
    logging.info("Scan complete. Alerts sent: %d", sent)


if __name__ == "__main__":
    main()
