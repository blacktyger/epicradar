import json

import requests


def vitex_data():
    queries = {'candles': 'klines?symbol=', 'ticker': 'ticker/24hr?symbols='}
    symbol = 'EPIC-002_BTC-000'

    def vitex_api(query, extra='&interval=hour&limit=168'):
        start_url = "https://api.vitex.net/api/v2/"
        if query == "klines?symbol=":
            url = start_url + query + symbol + extra
        else:
            url = start_url + query + symbol
        # print(f"{url}...")
        return json.loads(requests.get(url).content)

    resp = {query: vitex_api(queries[query]) for query in queries}

    d = {'candles': resp['candles']['data'],
         'ticker': resp['ticker']['data'][0]}

    data = {'time': d['candles']['t'], 'price': d['candles']['c']}

    return data

vitex_data()