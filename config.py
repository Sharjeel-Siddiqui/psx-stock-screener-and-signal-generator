from __future__ import annotations

import os


# =====================================================
# PSX STOCKS
# =====================================================

SYMBOLS = [
    "BFBIO",
    "DCR",
    "EFERT",
    "ENGROH",
    "FABL",
    "FFC",
    "GAL",
    "GGL",
    "HCAR",
    "HUBC",
    "MEBL",
    "MLCF",
    "NETSOL",
    "OGDC",
    "PSO",
    "SYS",
]


# =====================================================
# BACKTEST CAPITAL
# =====================================================

INITIAL_CAPITAL = 100_000


# =====================================================
# NTFY
# =====================================================

NTFY_TOPIC = os.getenv(
    "NTFY_TOPIC",
    ""
)