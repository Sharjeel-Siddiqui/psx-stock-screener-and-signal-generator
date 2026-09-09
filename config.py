from __future__ import annotations

import os


# =====================================================
# PSX STOCKS
# =====================================================
#
# Full KMI-30 (KSE-Meezan 30) Shariah-compliant index as
# re-composed effective 25 May 2026 — PSX Notice N-610,
# accounts as of 31 Dec 2025 — plus a few extra names that
# were on the original watchlist but are NOT KMI-30
# members (BFBIO, DCR, FABL, GGL, NETSOL).
#
# NOTE: KMI-30 is re-composed twice a year (~May & Nov),
# so review this list after each recomposition.

SYMBOLS = [
    # ----- KMI-30 constituents (30) -----
    "AIRLINK",
    "ATRL",
    "CPHL",
    "DGKC",
    "EFERT",
    "ENGROH",
    "FCCL",
    "FFC",
    "FFL",
    "GAL",
    "GHNI",
    "HCAR",
    "HUBC",
    "LUCK",
    "MARI",
    "MEBL",
    "MLCF",
    "NML",
    "NRL",
    "OGDC",
    "PAEL",
    "PPL",
    "PRL",
    "PSO",
    "SAZEW",
    "SEARL",
    "SNGP",
    "SSGC",
    "SYS",
    "TREET",

    # ----- Extra (non-KMI-30) watchlist -----
    "BFBIO",
    "DCR",
    "FABL",
    "GGL",
    "NETSOL",
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