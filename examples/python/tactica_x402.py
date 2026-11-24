"""Buy a tactica. forecast with x402, step by step, using nothing but eth-account.

    pip install eth-account==0.13.7

    python tactica_x402.py fixtures                      # free: upcoming fixtures and their ids
    python tactica_x402.py free                          # free: this round's free forecast, no wallet needed
    python tactica_x402.py offer  <fixtureId>            # free: show the x402 payment request, pay nothing
    python tactica_x402.py buy    <fixtureId> --key-file ~/.config/my-agent-wallet.hex --max-usdc 0.25

The wallet key is read from a file, never from the command line. Use a wallet that holds only what you
are happy to spend. The script refuses any price above --max-usdc. Gas is paid by the facilitator, so
the wallet needs USDC on Base and nothing else.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request

ORIGIN = 'https://app.tacticafootball.co.uk'
MCP_URL = ORIGIN + '/x402/mcp'
CHAIN_IDS = {'eip155:8453': 8453, 'eip155:84532': 84532}


def _b64(value):
    return base64.b64encode(json.dumps(value, separators=(',', ':')).encode()).decode()


def _unb64(text):
    return json.loads(base64.b64decode(text))


def _request(url, *, data=None, headers=None):
    req = urllib.request.Request(url, data=data, method='POST' if data is not None else 'GET',
                                 headers=dict({'Accept': 'application/json'}, **(headers or {})))
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read()


def list_fixtures():
    """Free MCP tool: upcoming fixtures, earliest kick-off first."""
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                       'params': {'name': 'list_fixtures', 'arguments': {}}}).encode()
    _, _, raw = _request(MCP_URL, data=body, headers={'Content-Type': 'application/json',
                                                      'Accept': 'application/json, text/event-stream',
                                                      'MCP-Protocol-Version': '2025-11-25'})
    return json.loads(raw)['result']['structuredContent']['fixtures']


def free_forecast():
    """The round's free sample: find the fixture marked freeSample and fetch it without paying."""
    sample = next((f for f in list_fixtures() if f.get('freeSample')), None)
    if sample is None:
        raise RuntimeError('no free sample this round')
    status, _, raw = _request(forecast_url(sample['fixtureId']))
    if status != 200:
        raise RuntimeError(f'HTTP {status}: {raw.decode()[:300]}')
    return sample, json.loads(raw)


def forecast_url(fixture_id):
    return f'{ORIGIN}/x402/v1/forecast/{fixture_id}'


def offer(url):
    """Ask without paying. Returns (status, payment request or None, body)."""
    status, headers, body = _request(url)
    required = headers.get('payment-required')
    return status, (_unb64(required) if status == 402 and required else None), body


def _sign(key, requirement):
    """The x402 v2 'exact' EVM payload: a USDC EIP-3009 TransferWithAuthorization."""
    from eth_account import Account
    from eth_account.messages import encode_typed_data
    account = Account.from_key(key)
    now = int(time.time())
    auth = {'from': account.address, 'to': requirement['payTo'], 'value': requirement['amount'],
            'validAfter': str(now - 600), 'validBefore': str(now + int(requirement['maxTimeoutSeconds'])),
            'nonce': '0x' + secrets.token_hex(32)}
    typed = {
        'types': {'EIP712Domain': [{'name': 'name', 'type': 'string'}, {'name': 'version', 'type': 'string'},
                                   {'name': 'chainId', 'type': 'uint256'}, {'name': 'verifyingContract', 'type': 'address'}],
                  'TransferWithAuthorization': [{'name': 'from', 'type': 'address'}, {'name': 'to', 'type': 'address'},
                                                {'name': 'value', 'type': 'uint256'}, {'name': 'validAfter', 'type': 'uint256'},
                                                {'name': 'validBefore', 'type': 'uint256'}, {'name': 'nonce', 'type': 'bytes32'}]},
        'primaryType': 'TransferWithAuthorization',
        'domain': {'name': requirement['extra']['name'], 'version': requirement['extra']['version'],
                   'chainId': CHAIN_IDS[requirement['network']], 'verifyingContract': requirement['asset']},
        'message': {'from': auth['from'], 'to': auth['to'], 'value': int(auth['value']),
                    'validAfter': int(auth['validAfter']), 'validBefore': int(auth['validBefore']),
                    'nonce': bytes.fromhex(auth['nonce'][2:])},
    }
    signed = account.sign_message(encode_typed_data(full_message=typed))
    return {'signature': '0x' + signed.signature.hex().removeprefix('0x'), 'authorization': auth}


def buy(url, key, max_usdc):
    """Pay for one paid route and return its JSON. Nothing is signed above max_usdc."""
    status, request, body = offer(url)
    if request is None:
        raise RuntimeError(f'no payment request (HTTP {status}): {body[:300]!r}')
    requirement = request['accepts'][0]
    price = int(requirement['amount']) / 1_000_000
    if requirement['network'] not in CHAIN_IDS:
        raise RuntimeError(f"unsupported network {requirement['network']}")
    if price > max_usdc:
        raise RuntimeError(f'price {price:.2f} USDC is above your limit of {max_usdc:.2f}')
    payment = {'x402Version': 2, 'resource': request['resource'], 'accepted': requirement,
               'payload': _sign(key, requirement)}
    if 'extensions' in request:
        payment['extensions'] = request['extensions']
    status, headers, body = _request(url, headers={'PAYMENT-SIGNATURE': _b64(payment)})
    if status != 200:
        try:
            reason = json.loads(body).get('error') or 'no reason given'
        except ValueError:
            reason = body[:300]
        raise RuntimeError(f'payment not accepted (HTTP {status}): {reason}')
    receipt = headers.get('payment-response')
    return json.loads(body), (_unb64(receipt) if receipt else None)


def _key(path):
    with open(os.path.expanduser(path)) as handle:
        return handle.read().strip()


def main():
    parser = argparse.ArgumentParser(description='tactica. x402 example')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('fixtures')
    sub.add_parser('free')
    sub.add_parser('offer').add_argument('fixture_id')
    paid = sub.add_parser('buy')
    paid.add_argument('fixture_id')
    paid.add_argument('--key-file', required=True)
    paid.add_argument('--max-usdc', type=float, required=True)
    args = parser.parse_args()

    if args.command == 'fixtures':
        for f in list_fixtures():
            free = '  FREE' if f.get('freeSample') else ''
            print(f"{f['kickoffAt']}  {f['league']:<24} {f['homeTeam']} v {f['awayTeam']}  {f['fixtureId']}{free}")
    elif args.command == 'free':
        sample, data = free_forecast()
        print(f"{sample['homeTeam']} v {sample['awayTeam']} ({sample['kickoffAt']}): free this round")
        print(json.dumps(data, indent=2))
    elif args.command == 'offer':
        status, request, body = offer(forecast_url(args.fixture_id))
        if request is None:
            sys.exit(f'HTTP {status}: {body.decode()[:300]}')
        req = request['accepts'][0]
        print(f"{request['resource']['description']}\nprice: {int(req['amount']) / 1e6:.2f} USDC on {req['network']}")
    else:
        data, receipt = buy(forecast_url(args.fixture_id), _key(args.key_file), args.max_usdc)
        print(json.dumps(data, indent=2))
        if receipt:
            print('transaction:', receipt.get('transaction'))


if __name__ == '__main__':
    main()
