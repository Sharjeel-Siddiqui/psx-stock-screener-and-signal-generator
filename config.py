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
# SCANNER LOOKBACK
# =====================================================
#
# How many of the most recent daily candles to re-check
# on every run. Looking back a few candles (instead of
# only the very last one) means a skipped or failed run
# can no longer silently drop a signal — the next
# successful run will still find and send it. Duplicate
# prevention (state.json) makes this safe.

LOOKBACK_CANDLES = 5


# =====================================================
# REMINDER RUN
# =====================================================
#
# The workflow runs a second time the next morning
# (09:00 PKT, pre-market). In "reminder" mode the scanner
# does NOT look for new signals — it simply re-sends the
# alerts fired in the last main run (previous 16:30 PKT),
# so a notification you missed overnight is surfaced again
# before the market opens.
#
# The main→reminder gap is ~16.5 h, so this window must be
# a bit wider than that to catch the alerts, yet under 24 h
# so it never re-sends the previous day's alerts. Only
# alerts sent within this many hours are re-sent, and each
# alert is reminded at most once (tracked in state).

REMINDER_MAX_AGE_HOURS = 20


# =====================================================
# NTFY
# =====================================================

NTFY_TOPIC = os.getenv(
    "NTFY_TOPIC",
    ""
)