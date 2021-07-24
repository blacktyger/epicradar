from app.templatetags.math import t_s
from core.manager.stellar import StellarNetworkManager
from core.manager.pancake import PancakeAPI
from vitex_api_pkg import VitexRestApi
from pycoingecko import CoinGeckoAPI
from core.secrets import currency_api
from core.timer import Timer
import pandas as pd
import datetime
import requests
import pickle
import jsons
import json
import os

cg = CoinGeckoAPI()


class DataBase:
    def __init__(self):
        self.epic_vs_xlm = None
        self.epic_vs_usd = None
        self.epic_vs_btc = None
        self.epic_vs_bnb = None
        self.bnb_price = None
        self.btc_price = None
        self.orderbook = None
        self.xlm_price = None
        self.currency = None
        self.explorer = None
        self.stellar = None
        self.network = None
        self.pancake = None
        self.updated = None
        self.blocks = None
        self.vitex = None
        self.epic = None

    def run(self):
        """ Run all API queries and save to instance"""
        print("\n------- DATABASE REPORT ----------------")
        self.epic_vs_usd = cg.get_price(ids=['epic-cash'], vs_currencies=['USD'])['epic-cash']['usd']
        self.bnb_price = cg.get_price(ids=['binancecoin'], vs_currencies=['USD'])['binancecoin']['usd']
        self.xlm_price = cg.get_price(ids=['STELLAR'], vs_currencies=['USD'])['stellar']['usd']
        self.btc_price = float(json.loads(requests.get("https://blockchain.info/ticker").content)['USD']['last'])
        self.orderbook = self.get_orderbook()
        self.currency = self.currency_data()
        self.network = self.network_data()
        self.vitex = self.vitex_data()
        self.stellar = self.stellar_data()
        self.pancake = self.pancake_data()
        self.updated = datetime.datetime.now()
        self.explorer = self.explorer_data()
        self.epic_vs_xlm = float(self.stellar_data()['sepic_xlm']['price'])
        self.epic_vs_btc = float(self.vitex['ticker']['closePrice'])
        self.epic_vs_bnb = float(self.pancake['epic_vs_bnb'])

        print("-------- END REPORT --------------------\n")

    def call(self):
        """ Update data and return self instance as json object"""
        self.run()
        data = jsons.dump(self)
        data = dict(data)
        return data

    @Timer(name='epic_chart_price')
    def epic_chart_price(self):
        data = cg.get_coin_market_chart_by_id(id='epic', vs_currency="usd", days=1)
        return data

    @Timer(name='explorer_data')
    def explorer_data(self):
        url = "https://explorer.epic.tech/api?q="
        circulating = json.loads(requests.get(f"{url}circulating").content)
        blocktime = json.loads(requests.get(f"{url}average-blocktime").content)
        height = json.loads(requests.get(f"{url}height").content)

        return {'circulating': circulating,
                'blocktime': blocktime,
                'height': height}

    @Timer(name='stellar_data')
    def stellar_data(self):
        xlm = StellarNetworkManager()
        # usd = StellarNetworkManager()
        # usd.counter = usd.assets['usd']
        data = {}

        for pair in [xlm]:
            data[f"sepic_{pair.counter.code.lower()}"] = {
                'price': pair.last_trade()['price'],
                'vol_24h': pair.last_24h()['base_volume'],
                'orderbook': pair.orderbook(),
                'trades': pair.trades()
                }
        return data

    @Timer(name='vitex_data')
    def vitex_data(self):
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
        data = {'candles': resp['candles']['data'],
                'ticker': resp['ticker']['data'][0]}

        return data

    @Timer(name='pancake_data')
    def pancake_data(self):
        mgr = PancakeAPI()
        l = mgr.liquidity()
        volume_24 = mgr.pool_24_volume()
        epic_vs_bnb = l['wbnb']['WBNB'] / l['wbnb']['EPIC']
        epic_vs_bnb_usd = self.bnb_price * epic_vs_bnb
        l_bnb_usd = \
            l['wbnb']['WBNB'] * self.bnb_price \
            + l['wbnb']['EPIC'] * self.epic_vs_usd
        l_busd_usd = l['busd']['BUSD'] + l['busd']['EPIC'] \
                     * self.epic_vs_usd
        l_total = l_bnb_usd + l_busd_usd
        chart_data = mgr.chart_data()
        # print(chart_data)
        return {
            'liquidity': l_total,
            'volume_24': volume_24,
            'chart_data': chart_data,
            'epic_vs_bnb': epic_vs_bnb,
            'epic_vs_bnb_usd': epic_vs_bnb_usd
            }

    @Timer(name='network_data')
    def network_data(self):
        net_hash_file = "mining\\network_hashrate.csv"
        net_diff_file = "mining\\network_difficulty.csv"
        hash_df = pd.read_csv(net_hash_file)
        diff_df = pd.read_csv(net_diff_file)
        network_hashrate = hash_df.iloc[[-1]]
        network_difficulty = diff_df.iloc[[-1]]
        network_difficulty = network_difficulty.to_dict('records')[0]
        network_hashrate = network_hashrate.to_dict('records')[0]
        return {
            'timestamp': t_s(network_hashrate['timestamp']),
            'height': network_hashrate['height'],
            'diff': network_difficulty,
            'hash': network_hashrate
            }

    @Timer(name='currency_data')
    def currency_data(self):
        data = {}
        currencies = {'EU': 'EUR', 'GB': 'GBP', 'JP': 'JPY', 'CN': 'CNY',
                      'PL': 'PLN', 'RU': 'RUB', 'PH': 'PHP', 'VE': 'VES'}
        data['BTC'] = {'symbol': 'BTC', 'price': self.btc_price}
        data['USD'] = {'symbol': 'USD', 'price': 1}
        url = f'https://v6.exchangerate-api.com/v6/{currency_api}/latest/USD'
        rates = requests.get(url).json()['conversion_rates']

        for key, value in currencies.items():
            for currency, price in rates.items():
                if currency == value:
                    data[value] = {'symbol': value, 'price': price,
                                   'country': key}
        return data

    @Timer(name='get_orderbook')
    def get_orderbook(self):
        vitex_api = VitexRestApi()
        vitex_epic_btc_orderbook = vitex_api.get_order_book_depth(symbol="EPIC-002_BTC-000")
        stellar = self.stellar_data()
        # stellarx_sepic_usd_orderbook = stellar['sepic_usd']['orderbook']
        stellarx_sepic_xlm_orderbook = stellar['sepic_xlm']['orderbook']

        self.orderbook = {
            'stellarx': {
                # 'usd': stellarx_sepic_usd_orderbook,
                'xlm': stellarx_sepic_xlm_orderbook
                },
            'vitex': {
                'btc': {
                    'bids': vitex_epic_btc_orderbook['data']['asks'],
                    'asks': vitex_epic_btc_orderbook['data']['bids']
                    }},
            }
        return self.orderbook

    @staticmethod
    def to_epic(currency, base="EPIC"):
        if base == "EPIC":
            if currency == ('USD' or 'usd' or 'usdt'):
                return db.epic_vs_usd
            elif currency == ('BTC' or 'btc' or 'bitcoin'):
                return db.epic_vs_btc
            elif currency == ('XLM' or 'xlm' or 'lumen'):
                return db.epic_vs_xlm
            else:
                for k, v in db.currency.items():
                    if k == currency:
                        curr_vs_usd = float(v['price'])
                        return db.epic_vs_usd * curr_vs_usd
                else:
                    return 1

    @staticmethod
    def epic_to(currency):
        for k, v in db.currency.items():
            if k == currency:
                curr_vs_usd = float(v['price'])
                return [v['symbol'], float(db.epic_vs_usd) * curr_vs_usd]


db_file = 'db.pickle'

if not os.path.exists(db_file):
    db = DataBase()
    db.run()
    with open(db_file, 'wb') as file:
        pickle.dump(db, file, protocol=pickle.HIGHEST_PROTOCOL)

with open(db_file, 'rb') as handle:
    db = pickle.load(handle)
