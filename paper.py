from __future__ import annotations

import math


# =====================================================
# PAPER-PORTFOLIO SIMULATION
# =====================================================
#
# For a single symbol, simulate the Pine strategy on a
# fixed starting capital (default 100,000 PKR):
#
#   - trade CONFIRMED signals only (buy_signal / sell_signal),
#     never the early-cross alerts
#   - BUY when flat: buy the maximum WHOLE shares the cash
#     allows, then compound
#   - SELL when holding: sell the entire position
#
# This is stateless — it is recomputed from the full price
# history on every run, so it always matches the backtest
# and can never drift. It is a SIMULATION for illustration,
# not a record of real trades.


def simulate(
    symbol: str,
    x,
    capital: float = 100_000.0,
) -> dict:

    cash = float(capital)
    units = 0
    cost = 0.0
    entry_price = None
    entry_date = None

    trades = []

    for row in x.itertuples():

        price = float(row.close)

        # Skip bad prices defensively.
        if price != price or price <= 0:  # NaN or non-positive
            continue

        buy = bool(getattr(row, "buy_signal", False))
        sell = bool(getattr(row, "sell_signal", False))

        # -------- ENTRY: buy max whole shares --------
        if units == 0 and buy:

            u = int(math.floor(cash / price))

            if u > 0:
                cost = u * price
                cash -= cost
                units = u
                entry_price = price
                entry_date = row.date

                trades.append({
                    "action": "BUY",
                    "date": str(row.date),
                    "units": u,
                    "price": round(price, 2),
                    "cost": round(cost, 2),
                })

        # -------- EXIT: sell the whole position --------
        elif units > 0 and sell:

            proceeds = units * price
            pnl = proceeds - cost
            pnl_pct = (pnl / cost * 100.0) if cost else 0.0
            cash += proceeds

            trades.append({
                "action": "SELL",
                "date": str(row.date),
                "units": units,
                "price": round(price, 2),
                "proceeds": round(proceeds, 2),
                "buy_price": round(entry_price, 2) if entry_price else None,
                "buy_date": str(entry_date) if entry_date else None,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
            })

            units = 0
            cost = 0.0
            entry_price = None
            entry_date = None

    # -------------------------------------------------
    # Final state (as of the latest candle)
    # -------------------------------------------------

    last_price = float(x.iloc[-1]["close"])
    holding = units > 0

    market_value = units * last_price if holding else 0.0
    equity = cash + market_value

    position = None
    if holding:
        unreal = market_value - cost
        position = {
            "symbol": symbol,
            "units": units,
            "buy_price": round(entry_price, 2) if entry_price else None,
            "buy_date": str(entry_date) if entry_date else None,
            "cost": round(cost, 2),
            "last_price": round(last_price, 2),
            "market_value": round(market_value, 2),
            "unrealized_pnl": round(unreal, 2),
            "unrealized_pct": round(unreal / cost * 100.0, 2) if cost else 0.0,
        }

    realized_pnl = sum(
        t["pnl"] for t in trades if t["action"] == "SELL"
    )

    return {
        "symbol": symbol,
        "capital_start": capital,
        "cash": round(cash, 2),
        "equity": round(equity, 2),
        "total_return_pct": round((equity - capital) / capital * 100.0, 2),
        "realized_pnl": round(realized_pnl, 2),
        "in_position": holding,
        "position": position,
        "trades_count": len(trades),
        "trades": trades,
    }
