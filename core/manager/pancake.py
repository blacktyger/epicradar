
from gql.transport.exceptions import TransportServerError, TransportQueryError
from core.manager.gql_queries import pool_volume, liquidity, ohlc
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta
from json import JSONDecodeError
from gql import gql, Client
from time import sleep
import ciso8601
import time
import json


def str_to_ts(ts):
    return int(time.mktime(ciso8601.parse_datetime(ts).timetuple()))


def last_24h():
    now = datetime.now()
    day_ago = timedelta(hours=24)
    return now - day_ago


class PancakeAPI:
    def __init__(self):
        self.contracts = self.contracts_book()

    @staticmethod
    def contracts_book():
        data = {
            "pools": {
                "wbnb": "0x81c1f3a45bc47ef476189b695f73ac1d0d5f1c0a",
                "busd": "0x8d1e574ba87f34f2faab5a3d1db6c97312ca721c"
                },
            "tokens": {
                "epic": "0x2CCa66321B8f275339E622Af66059Ef251b38893",
                "wbnb": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                "busd": "0xe9e7cea3dedca5984780bafc599bd69add087d56"
                }
            }
        return data

    @staticmethod
    def _call(query, vars):
        success = False
        data = dict
        tries = 4
        while not success and tries:
            try:
                transport = RequestsHTTPTransport(url="https://graphql.bitquery.io",
                                                  headers={'X-API-KEY': 'BQYWuYgUbfAGHOXhETM9WeQonACWuhIH'})
                client = Client(transport=transport, fetch_schema_from_transport=True)
                query = gql(query)
                # print("PancakeAPI: Starting query...")
                data = client.execute(query, variable_values=vars)
                success = True
                return data
            except (JSONDecodeError, TransportServerError, TransportQueryError, TypeError) as er:
                print(f"PancakeAPI: {er}")
                print(f"PancakeAPI: response error, trying again... ({tries} left)")
                tries -= 1
                sleep(3)
        return data

    def pool_24_volume(self):
        query = pool_volume
        resp = {}
        data = {'total': 0}
        vars = {"date_start": last_24h().strftime("%Y-%m-%d"),
                "date_stop": datetime.now().strftime("%Y-%m-%d")}

        for token, address in self.contracts["pools"].items():
            vars["pool_address"] = address
            resp[token] = self._call(query=query, vars=json.dumps(vars))
            # print(f"{token} = { resp[token]}")
            r = resp[token]['ethereum']['dexTrades'][0]
            data['total'] += r['tradeAmount']
            data[token] = r
        return data

    def liquidity(self):
        query = liquidity
        vars = {}
        resp = {}
        data = {}

        for token, address in self.contracts["pools"].items():
            temp = {}
            vars["pool_address"] = address
            resp[token] = self._call(query=query, vars=json.dumps(vars))
            r = resp[token]['ethereum']['address'][0]['balances']
            data[token] = r

            for x in data[token]:
                temp[x['currency']['symbol']] = x['value']
            data[token] = temp
        # print(data)
        return data

    def chart_data(self):
        query = ohlc
        data = {'time': [], 'price': []}
        vars = {"base": self.contracts['tokens']['epic'],
                "quote": self.contracts['tokens']['wbnb']}
        resp = self._call(query=query, vars=json.dumps(vars))
        r = resp['ethereum']['dexTrades']

        for x in r:
            data['time'].append(str_to_ts(x['timeInterval']['minute']))
            data['price'].append(float(x['close_price']))
        return data

# x = PancakeAPI()
# x.liquidity()