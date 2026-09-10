from __future__ import annotations

import json
from pathlib import Path

STATE_FILE = Path("state.json")
PORTFOLIO_FILE = Path("portfolio.json")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"signals": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"signals": {}}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def signal_key(symbol: str, signal: str, date_value) -> str:
    return f"{symbol}:{signal}:{date_value}"


def save_portfolio(portfolio: dict) -> None:
    """
    Persist the simulated 100k paper-portfolio scenarios
    (per symbol) so the mobile app can render them.
    """
    PORTFOLIO_FILE.write_text(
        json.dumps(portfolio, indent=2, sort_keys=True),
        encoding="utf-8",
    )
