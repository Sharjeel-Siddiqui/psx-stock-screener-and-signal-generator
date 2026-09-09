# PSX EMA 7/21 Daily Signal Bot

A free, signal-only PSX scanner that reproduces the TradingView strategy
**"PSX EMA 7/21 - 2 Daily Candle Confirmation"**:

- Daily timeframe
- EMA 7 and EMA 21
- Golden Cross -> wait 2 complete daily candles -> BUY if EMA 7 > EMA 21
- Death Cross -> wait 2 complete daily candles -> SELL ALL if EMA 7 < EMA 21
- **Early alerts:** an `⚡ EARLY` heads-up on the cross candle itself, ~2 trading
  days before the confirmed signal (the confirmed BUY/SELL still matches the
  Pine strategy exactly)
- **Missed-run safety:** each run re-checks the last few candles, so a skipped
  or failed run never silently drops a signal
- **Reminder run:** a second, pre-market run re-sends the day's alerts once
- Full **KMI-30** Shariah-compliant index watchlist (+ a few extra names)
- ntfy.sh phone notifications
- Persistent duplicate-alert prevention
- GitHub Actions daily automation
- Never places broker orders

## 1. Set up ntfy notifications

This bot sends alerts through [ntfy.sh](https://ntfy.sh) — no account needed.

1. Install the **ntfy** app on your phone (Android / iOS) or open https://ntfy.sh.
2. **Subscribe** to a topic. Pick a long, hard-to-guess name (a public ntfy
   topic is readable by anyone who knows its name), e.g.
   `psx-alerts-9f3k2xq7`.
3. That topic name is your `NTFY_TOPIC`.

## 2. Test locally

Install Python 3.11+ (3.12 is recommended).

Create a virtual environment:

Windows:
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install:
```bash
pip install -r requirements.txt
```

Set the ntfy topic.

Windows PowerShell:
```powershell
$env:NTFY_TOPIC="your-topic-name"
```

macOS/Linux:
```bash
export NTFY_TOPIC="your-topic-name"
```

Run one scan (you should receive a notification if any symbol has a signal):
```bash
python scanner.py
```

## 3. Validate signals against TradingView

Example:
```bash
python backtest.py --symbol MEBL --years 3
```

Run this for each symbol and compare the dates with TradingView.

## 4. Run modes

The scanner has two modes, selected by the `RUN_MODE` environment variable:

- `RUN_MODE=main` (default) — scan for new signals.
- `RUN_MODE=reminder` — do **not** scan; re-send the alerts from the last main
  run once (so a notification you missed is surfaced again pre-market).

```bash
RUN_MODE=reminder python scanner.py
```

## 5. Run automatically for free

Put this project in a GitHub repository.

For a private repo, GitHub Free includes a monthly Actions allowance. Public
repositories using standard GitHub-hosted runners are free. See current GitHub
Actions billing docs.

In GitHub:
Settings -> Secrets and variables -> Actions -> New repository secret

Add:
- `NTFY_TOPIC`

The workflow runs Monday–Friday and can also be started manually from the
Actions tab (with a `main` / `reminder` mode selector):

| Run | Time (PKT) | UTC cron | Purpose |
|-----|-----------|----------|---------|
| Main scan | 16:30 | `30 11 * * 1-5` | Detect new signals |
| Reminder | 09:00 next day | `0 4 * * 1-5` | Re-send the day's alerts pre-market |

> **Note:** GitHub only runs scheduled (`cron`) workflows from the **default
> branch**. The automation goes live once this is merged into `main` — it will
> not fire on a feature branch.

## 6. Duplicate alerts

`state.json` stores a key such as:

`MEBL:BUY:2026-08-31`

The workflow commits state changes back to the repository. This prevents the
same signal from being sent again if the workflow runs twice on the same signal
date. Reminder runs mark each alert as reminded so it is never re-sent twice.

## 7. Safety

This project does not connect to a broker and cannot place orders.

If a data request fails, the scanner logs an error and does not invent a signal.

The `⚡ EARLY` alerts are a faster, **unconfirmed** heads-up and are **not part
of the backtested Pine strategy** — only the confirmed 🟢/🔴 signals match the
TradingView backtest.

Before using signals with real money, compare the historical Python signals
against TradingView and run the bot in alert-only/paper mode first.

## Data source

The project uses the open-source `psxdata` Python package for PSX historical
OHLCV data. It is MIT licensed and currently requires Python 3.11+.

Data-source availability and PSX redistribution/use terms can change. This
project is for personal signal generation; verify the applicable data terms
before redistributing market data.

## Symbols

Full **KMI-30** (KSE-Meezan 30) Shariah-compliant index, as re-composed
effective 25 May 2026 (PSX Notice N-610), plus a few extra watchlist names.
KMI-30 is re-composed ~twice a year (May & Nov) — review the list in
`config.py` after each recomposition.

**KMI-30 (30):**
AIRLINK, ATRL, CPHL, DGKC, EFERT, ENGROH, FCCL, FFC, FFL, GAL, GHNI, HCAR,
HUBC, LUCK, MARI, MEBL, MLCF, NML, NRL, OGDC, PAEL, PPL, PRL, PSO, SAZEW,
SEARL, SNGP, SSGC, SYS, TREET

**Extra (non-KMI-30):** BFBIO, DCR, FABL, GGL, NETSOL
