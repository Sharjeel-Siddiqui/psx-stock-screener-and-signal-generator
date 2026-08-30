from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from telegram import send_telegram

send_telegram(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    "✅ PSX Alert Bot test message\nTelegram connection is working."
)

print("Test message sent.")
