import os

SYMBOLS = [
    "BFBIO", "DCR", "EFERT", "ENGROH",
    "FABL", "FFC", "GAL", "GGL",
    "HCAR", "HUBC", "MEBL", "MLCF",
    "NETSOL", "OGDC", "PSO", "SYS",
]

INITIAL_CAPITAL = 100_000

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# The scanner is intentionally signal-only. It never places broker orders.
