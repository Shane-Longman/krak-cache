#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import json
import sys


def main():

    kraken_res = requests.get('https://api.kraken.com/0/public/AssetPairs')
    if kraken_res.status_code != 200:
        print('[Kraken] Bad status code. Aborting', file=sys.stderr)
        print(kraken_res.text, file=sys.stderr)
        return

    bina_res = requests.get('https://www.binance.com/bapi/asset/v2/public/asset-service/product/get-products?includeEtf=false')
    if bina_res.status_code != 200:
        print('[Binance] Bad status code. Aborting', file=sys.stderr)
        print(bina_res.text, file=sys.stderr)
        return

    kraken_json = kraken_res.json()
    kraken_markets = sorted([mkt['wsname'].replace('/', '-') for _, mkt in kraken_json['result'].items()])

    bina_json = bina_res.json()
    bina_markets = sorted([mkt['b'] + '-' + mkt['q'] for mkt in bina_json['data'] if mkt['st'] == 'TRADING'])
    # clone Binance USDT markets as USDC
    bina_markets.extend(m.replace('-USDT', '-USDC') for m in bina_markets if m.endswith('-USDT'))

    # clone Binance USDT markets as USD
    bina_markets.extend(m.replace('-USDT', '-USD') for m in bina_markets if m.endswith('-USDT'))

    # clone Binance BTC markets as XBT
    bina_markets.extend(m.replace('-BTC', '-XBT') for m in bina_markets if m.endswith('-BTC'))
    bina_markets.extend(m.replace('BTC-', 'XBT-') for m in bina_markets if m.startswith('BTC-'))

    bina_markets.extend(m.replace('DOGE-', 'XDG-') for m in bina_markets if m.startswith('DOGE-'))

    common = set.intersection(set(kraken_markets), set(bina_markets))

    common = sorted([m for m in common])
    common = [m for m in common
              if m.endswith('-USDT')
              or m.endswith('-USDC')
              or m.endswith('-BTC')
              or m.endswith('-XBT')
              or m.endswith('-ETH')
              or m.endswith('-EUR')
              or m.endswith('-USD')
             ]
    print(" ".join(common))


if __name__ == '__main__':
    main()
