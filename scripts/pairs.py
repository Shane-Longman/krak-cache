#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, List, Set, Tuple, Union, Any, Optional, Mapping
import logging
import brotli

def requests_retry_session(
    retries: int=3,
    backoff_factor: float=0.3,
    status_forcelist: Tuple[int]=(500, 502, 503, 504),
    session: Optional[requests.Session]=None,
) -> requests.Session:
    session: requests.Session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def download(
    session: requests.Session,
    verb: str,
    url: str,
    *,
    retries: int,
    timeout: int,
    delay: int,
    params: Optional[Dict]=None,
    headers: Optional[Dict]=None,
    data: Optional[str]=None,
    auth: Optional[tuple]=None,
) -> Optional[requests.Response]:
    on_exception_retries: int = retries
    while on_exception_retries > 0:
        on_exception_retries -= 1
        try:
            res = session.request(verb, url, timeout=timeout, params=params, headers=headers, data=data, auth=auth)
        except requests.HTTPError as e:
            if on_exception_retries == 0:
                logging.error(f"Http failure: {str(e)}")
                return None
            else:
                logging.warning(f"Http failure: {str(e)}")
                time.sleep(delay)
                continue
        except requests.ConnectionError as e:
            if on_exception_retries == 0:
                logging.error(f"Connection failure: {str(e)}")
                return None
            else:
                logging.warning(f"Connection failure: {str(e)}")
                time.sleep(delay)
                continue
        except requests.Timeout as e:
            if on_exception_retries == 0:
                logging.error(f"Network timeout failure: {str(e)}")
                return None
            else:
                logging.warning(f"Network timeout failure: {str(e)}")
                time.sleep(delay)
                continue
        except requests.RequestException as e:
            if on_exception_retries == 0:
                logging.error(f"Core requests failure: {str(e)}")
                return None
            else:
                logging.warning(f"Core requests failure: {str(e)}")
                time.sleep(delay)
                continue
        break
                
    #if res.status_code < 200 or 300 <= res.status_code:
    #    logging.error(f'Http error: status={res.status_code}')
    #    return None
        
    return res


def main():

    kraken_res = requests.get('https://api.kraken.com/0/public/AssetPairs')
    if kraken_res.status_code != 200:
        print('[Kraken] Bad status code. Aborting', file=sys.stderr)
        print(kraken_res.text, file=sys.stderr)
        return

    retries = 3
    timeout = 15
    delay = 5
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }

    session: requests.Session = requests_retry_session(retries=retries)
    bina_res = download(
        session, 'GET', 'http://www.binance.com/bapi/asset/v2/public/asset-service/product/get-products?includeEtf=false',
        retries=retries,
        timeout=timeout,
        delay=delay,
    )
    #bina_res = requests.get('http://www.binance.com/bapi/asset/v2/public/asset-service/product/get-products?includeEtf=false')
    if bina_res.status_code != 200:
        print(f'[Binance] Bad status code {bina_res.status_code}. Aborting', file=sys.stderr)
        print(bina_res.text, file=sys.stderr)
        #return
        with open("bina_fallback.json", "rt") as ifile:
            bina_json = json.loads(ifile.read())
    else:
        bina_json = bina_res.json()

    kraken_json = kraken_res.json()
    kraken_markets = sorted([mkt['wsname'].replace('/', '-') for _, mkt in kraken_json['result'].items()])

    #bina_json = bina_res.json()
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
