from __future__ import annotations

import json
from pathlib import Path

STATE_FILE = Path("state.json")


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
