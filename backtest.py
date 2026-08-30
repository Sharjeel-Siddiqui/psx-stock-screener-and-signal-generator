from __future__ import annotations

import argparse

from data_provider import get_daily_history
from strategy import signals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--years", type=int, default=3)
    args = parser.parse_args()

    df = get_daily_history(args.symbol, years=args.years)
    out = signals(df)

    if out.empty:
        print(f"{args.symbol}: no signals")
        return

    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
