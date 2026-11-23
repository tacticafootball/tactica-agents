"""Compare tactica.'s chances with a market price you already have (Polymarket, an exchange, anywhere).

tactica. sells its own forecast, not prices. You bring the market's price; this script buys the
forecast (0.25 USDC) and shows the gap between our chance and the market's implied chance.

    pip install eth-account==0.13.7
    python compare.py <fixtureId> --home 0.52 --draw 0.27 --away 0.24 \
        --key-file ~/.config/my-agent-wallet.hex --max-usdc 0.25

--home / --draw / --away are the market's implied chances (0-1), for example a Polymarket share price.
For decimal odds, pass 1/odds. This is information, not betting or financial advice. 18+.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'python'))
import tactica_x402  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('fixture_id')
    for side in ('home', 'draw', 'away'):
        parser.add_argument('--' + side, type=float, required=True)
    parser.add_argument('--key-file', required=True)
    parser.add_argument('--max-usdc', type=float, required=True)
    args = parser.parse_args()

    with open(os.path.expanduser(args.key_file)) as handle:
        key = handle.read().strip()
    forecast, _ = tactica_x402.buy(tactica_x402.forecast_url(args.fixture_id), key, args.max_usdc)
    match = forecast['match']
    print(f"{match['homeTeam']['name']} v {match['awayTeam']['name']}  ({match.get('kickoffAt')})")
    print(f"{'':6} {'tactica.':>9} {'market':>8} {'gap':>7}")
    for side in ('home', 'draw', 'away'):
        ours = forecast['probabilities'][side] / 100      # tactica. gives whole percentages
        market = getattr(args, side)
        print(f'{side:6} {ours:9.1%} {market:8.1%} {ours - market:+7.1%}')
    xg = forecast['expectedGoals']
    print(f"expected goals: {xg['home']} - {xg['away']}   model {forecast.get('modelVersion')}")


if __name__ == '__main__':
    main()
