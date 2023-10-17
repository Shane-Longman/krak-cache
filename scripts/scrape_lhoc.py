#!/usr/bin/python3
# -*- coding: utf-8 -*-

import plac
import requests
import datetime as dt
from typing import List
from collections import defaultdict
from decimal import Decimal as D
import time


# example usage:
#
# ./scrape_lhoc.py 2021-06-03 XDG-USDT


def parse_date(s):
    if len(s) == len("YYYY-MM-DD"):
        return dt.datetime.strptime(s, "%Y-%m-%d")
    elif len(s) == len('2021-05-19T11:00:00'):
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    elif s[19] == 'Z':
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    else:
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")


def main(
        ofname : ("Output file name", 'positional', None, str),
        begin : ("Starting date, YYYY-MM-DD[THH::MM::SS]", 'positional', None, str),
        market : ("Market to download", 'positional', None, str),
    ):

    begin: dt.datetime = parse_date(begin)
    end: dt.datetime = begin + dt.timedelta(hours=24)

    UTC0: dt.datetime = dt.datetime(1970, 1, 1)

    # https://api.kraken.com/0/public/Trades?pair=XBTUSD&since=1688669597&count=1000
    # https://api.kraken.com/0/public/Trades?pair=XBTUSD&since=1688669597

    end_ts: float = (end - UTC0).total_seconds()

    try:
        market = market.replace('-', '')
        trades = defaultdict(lambda: []) # key = minute-resolution date string
        lhoc = []
        now: dt.datetime = begin
        now_ts: float = (now - UTC0).total_seconds()

        request_no = 0

        while now < end:
            print(f'>>> {market} at {now.strftime("%Y-%m-%d %H:%M:%S")}')

            request_no += 1

            MAX_RETRIES = 5
            retries = MAX_RETRIES
            while retries > 0:
                retries -= 1
                if request_no % 5 == 0:
                    time.sleep(2)
                url = f'https://api.kraken.com/0/public/Trades?pair={market}&since={now_ts}'
                res = requests.get(url, headers={'Accept-Encoding': 'gzip, deflate, br'})
                if not res.status_code == 200:
                    print(res)
                assert res.status_code == 200

                js: dict = res.json()
                js_error = js['error']
                if not js_error:
                    break
                elif 'EGeneral:Internal error' in js_error:
                    print(f'[w] [EGeneral:Internal error] Try {MAX_RETRIES - retries} of {MAX_RETRIES}')
                    assert retries != 0, "[!] [EGeneral:Internal error] Maximum number of retries exceeded."
                    time.sleep(10)
                else:
                    assert not js_error, str(js['error'])

            result: dict = js['result']

            js_trades = result.get(market, None) or result[next(iter(result.keys()))]
            js_trade: list
            for js_trade in js_trades:
                price: str = js_trade[0]
                vol: str = js_trade[1]
                ts: float = float(js_trade[2])
                iso = dt.datetime.utcfromtimestamp(ts).isoformat()[:16]
                if ts < end_ts:
                    trades[iso].append((float(price), price, vol))
                else:
                    break
                #trade = '{},{},{},{},{},{}\n'.format(iso, js_trade['T'], int(js_trade['m']), js_trade['a'], js_trade['p'], js_trade['q'])
                #trades.append(trade)

            if not js_trades:
                print("[i] Empty trades list in response.")
                break
            # update `now` for printing
            now = UTC0 + dt.timedelta(seconds=js_trades[-1][2])

            new_now_ts = float(result['last']) / 1e9
            if now_ts == new_now_ts:
                print('[i] End of trades')
                break
            now_ts = new_now_ts

        for iso, minute_trades in trades.items():
            if minute_trades:
                iso += ':00'
                # output I want (LHOC): 2021-01-01T00:36:00,1609461360,340.51,340.91,340.51,340.58,9.93893384
                lo: str = min(minute_trades)[1]
                hi: str = max(minute_trades)[1]
                op: str = minute_trades[0][1]
                cl: str = minute_trades[-1][1]
                tv = sum(D(tup[2]) for tup in minute_trades)
                lhoc.append(
                    f"{iso},{round((parse_date(iso) - UTC0).total_seconds())},{lo},{hi},{op},{cl},{tv}\n"
                )

        with open(ofname, 'wt') as ofile:
            ofile.writelines(lhoc)

    except KeyboardInterrupt:
        #with open(ofname, 'wt') as ofile:
        #    ofile.writelines(trades)
        return

    pass


if __name__ == '__main__':
    plac.call(main)
