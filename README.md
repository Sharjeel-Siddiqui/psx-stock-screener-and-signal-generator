# PSX EMA 7/21 Daily Signal Bot

A free, signal-only PSX scanner that reproduces the current TradingView strategy:

- Daily timeframe
- EMA 7 and EMA 21
- Golden Cross -> wait 2 complete daily candles -> BUY if EMA 7 > EMA 21
- Death Cross -> wait 2 complete daily candles -> SELL ALL if EMA 7 < EMA 21
- No green/red candle requirement
- 16 initial PSX symbols
- Telegram phone notifications
- Persistent duplicate-alert prevention
- GitHub Actions daily automation
- Never places broker orders

## 1. Create a Telegram bot

Open Telegram and talk to `@BotFather`.

Use `/newbot`, choose a name and username, and copy the bot token.

Then send a message such as `test` to your new bot.

To obtain your chat ID, open:

`https://api.telegram.org/botYOUR_TOKEN/getUpdates`

Look for:

`"chat":{"id": ... }`

Do not publish your token.

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

Set environment variables.

Windows PowerShell:
```powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
$env:TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
```

macOS/Linux:
```bash
export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
```

Test Telegram:
```bash
python test_telegram.py
```

## 3. Validate signals against TradingView

Example:
```bash
python backtest.py --symbol MEBL --years 3
```

Run this for each symbol and compare the dates with TradingView.

## 4. Run one scan locally

```bash
python scanner.py
```

## 5. Run automatically for free

Put this project in a GitHub repository.

For a private repo, GitHub Free includes a monthly Actions allowance. Public repositories using standard GitHub-hosted runners are free. See current GitHub Actions billing docs.

In GitHub:
Settings -> Secrets and variables -> Actions -> New repository secret

Add:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

The workflow runs Monday-Friday at 16:30 Pakistan time (11:30 UTC) and can also be started manually from the Actions tab.

## 6. Duplicate alerts

`state.json` stores a key such as:

`MEBL:BUY:2026-08-31`

The workflow commits state changes back to the repository. This prevents the same signal from being sent again if the workflow runs twice on the same signal date.

## 7. Safety

This project does not connect to a broker and cannot place orders.

If a data request fails, the scanner logs an error and does not invent a signal.

Before using signals with real money, compare the historical Python signals against TradingView and run the bot in alert-only/paper mode first.

## Data source

The project uses the open-source `psxdata` Python package for PSX historical OHLCV data. It is MIT licensed and currently requires Python 3.11+.

Data-source availability and PSX redistribution/use terms can change. This project is for personal signal generation; verify the applicable data terms before redistributing market data.

## Initial symbols

BFBIO, DCR, EFERT, ENGROH, FABL, FFC, GAL, GGL,
HCAR, HUBC, MEBL, MLCF, NETSOL, OGDC, PSO, SYS
