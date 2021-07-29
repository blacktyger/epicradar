from django.core.serializers.json import DjangoJSONEncoder
from vitex_api_pkg import VitexRestApi
from pycoingecko import CoinGeckoAPI
from jsonfield import JSONField
from django.db import models
from decimal import Decimal
import pandas as pd
import requests
import json

from core.manager.stellar import StellarNetworkManager
from core.manager.pancake import PancakeAPI
from core.secrets import currency_api
from core.timer import Timer

cg = CoinGeckoAPI()

SYMBOLS = ['USD', 'BTC', 'XLM', 'BNB', 'EPIC', 'ETH']

COINS = {'EPIC-CASH': 'EPIC', 'BITCOIN': 'BTC', 'stellar': 'XLM',
         'ethereum': 'ETH', 'MONERO': 'XMR', 'binancecoin': 'BNB'}

CURRENCIES = {'USD': 'USD', 'EU': 'EUR', 'GB': 'GBP', 'JP': 'JPY', 'CN': 'CNY',
              'PL': 'PLN', 'RU': 'RUB', 'PH': 'PHP', 'XLM': 'XLM', 'VE': 'VES',
              'EPIC': 'EPIC', 'BTC': 'BTC', 'ETH': 'ETH', 'BNB': 'BNB'}


class Coin(models.Model):
    name = models.CharField(max_length=20)
    symbol = models.CharField(max_length=20)

    @Timer(name='coin_data')
    def init_data(self):
        for name, symbol in COINS.items():
            Coin.objects.get_or_create(name=name, symbol=symbol)

    def __str__(self):
        return f"{str(self.name).upper()} ({self.symbol.upper()})"


class Currency(models.Model):
    most_recent = models.BooleanField(default=True)
    country = models.CharField(max_length=5)
    symbol = models.CharField(max_length=5)
    value = models.DecimalField(decimal_places=8, max_digits=32, default=1)

    data = models.JSONField(null=True)

    @Timer(name='currency_data')
    def _data(self):
        def download():
            url = f'https://v6.exchangerate-api.com/v6/{currency_api}/latest/USD'
            return requests.get(url).json()['conversion_rates']

        try:
            btc_vs_usd = Decimal(json.loads(requests.get('https://blockchain.info/ticker').content)['USD']['last'])
        except Exception as e:
            print(e)
            btc_vs_usd = cg.get_price(ids=['bitcoin'], vs_currencies=['USD'])['bitcoin']['usd']
            btc_vs_usd = Decimal(btc_vs_usd)

        data, created = Currency.objects.get_or_create(symbol='XXX', country='XXX')
        if not created:
            try:
                rates = data.data
                # print('RATES ALREADY SAVED')
            except Exception as e:
                print(e)
                rates = download()
                data.data = json.dumps(rates)
                data.save()
        else:
            print('NO SAVED RATES, MAKING NEW QUERY')
            rates = download()
            data.data = json.dumps(rates)
            data.save()

        for country, symbol in CURRENCIES.items():
            if symbol in SYMBOLS:
                obj, created = Currency.objects.get_or_create(
                    symbol=symbol, country=country)
                if symbol == 'BTC':
                    obj.value = btc_vs_usd
                    obj.save()
                    price, created = Price.objects.creaget(coin=symbol, currency='USD')
                    price.value = btc_vs_usd
                    price.save()

                elif symbol == 'USD':
                    obj.value = 1
                    obj.save()

                else:
                    coin_obj = Coin.objects.filter(symbol=symbol)
                    if coin_obj:
                        obj.value = cg.get_price(ids=[coin_obj[0].name.lower()], vs_currencies=[
                            'USD'])[coin_obj[0].name.lower()]['usd']
                        obj.save()
                        price, created = Price.objects.creaget(coin=coin_obj[0], currency='USD')
                        price.value = obj.value
                        price.save()
                    else:
                        print(f'{symbol} not found')
            else:
                # print(rates)
                try: rates = json.loads(rates)
                except Exception: rates = dict(rates)

                for currency, value in rates.items():
                    if currency == symbol:
                        obj, created = Currency.objects.get_or_create(
                            symbol=symbol, country=country)
                        obj.value = 1 / value
                        obj.save()

    def __str__(self):
        return f"{self.symbol.upper()}"


class PriceQuerySet(models.QuerySet):
    def creaget(self, **kwargs):
        try:
            if isinstance(kwargs['coin'], str):
                kwargs['coin'] = Coin.objects.get(symbol=kwargs['coin'].upper())
            if isinstance(kwargs['currency'], str):
                kwargs['currency'] = Currency.objects.get(symbol=kwargs['currency'].upper())
        except self.model.DoesNotExist:
            print(f"{kwargs['coin']} or {kwargs['currency']} not exists")
        return self.get_or_create(coin=kwargs['coin'], currency=kwargs['currency'])


class Price(models.Model):
    most_recent = models.BooleanField(default=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True)
    value = models.DecimalField(decimal_places=8, max_digits=32, default=-1)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)

    objects = PriceQuerySet.as_manager()

    @staticmethod
    def get_cg_price(coin):
        if isinstance(coin, str):
            coin = Coin.objects.get(symbol=coin)

        return Decimal(cg.get_price(ids=[coin.name.lower()],
                                    vs_currencies=['USD'])[coin.name.lower()]['usd'])

    def __str__(self):
        return f"1 {self.coin.symbol.upper()} = {round(self.value, 4)} {self.currency.symbol}"


class Explorer(models.Model):
    most_recent = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    circulating = models.IntegerField()
    blocktime = models.IntegerField()
    height = models.IntegerField()

    @Timer(name='explorer_data')
    def _data(self):
        url = "https://explorer.epic.tech/api?q="
        circulating = json.loads(requests.get(f"{url}circulating").content)
        blocktime = json.loads(requests.get(f"{url}average-blocktime").content)
        height = json.loads(requests.get(f"{url}getblockcount").content)

        Explorer.objects.create(
            circulating=circulating,
            blocktime=blocktime,
            height=height)

    def __str__(self):
        return f"EXPLORE HEIGHT: {self.height}"


class Network(models.Model):
    most_recent = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now=True)
    height = models.IntegerField()
    diff = JSONField()
    hash = JSONField()

    @Timer(name='network_data')
    def _data(self):
        net_hash_file = "network_hashrate.csv"
        net_diff_file = "network_difficulty.csv"
        hash_df = pd.read_csv(net_hash_file)
        diff_df = pd.read_csv(net_diff_file)
        network_hashrate = hash_df.iloc[[-1]]
        network_difficulty = diff_df.iloc[[-1]]
        network_difficulty = network_difficulty.to_dict('records')[0]
        network_hashrate = network_hashrate.to_dict('records')[0]

        Network.objects.create(**{
            'timestamp': network_hashrate['timestamp'],
            'height': network_hashrate['height'],
            'diff': network_difficulty,
            'hash': network_hashrate
            })

    def __str__(self):
        return f"NETWORK HEIGHT: {self.height}"


class Vitex(models.Model):
    most_recent = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    data = JSONField()

    @Timer(name='vitex_data')
    def _data(self):
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

        Vitex.objects.create(data=json.dumps(data, cls=DjangoJSONEncoder))
        obj, created = Price.objects.creaget(coin='epic', currency='btc')
        obj.value = Decimal(data['ticker']['closePrice'])
        obj.save()

    def __str__(self):
        return f"VITEX, {self.updated}"


class Stellar(models.Model):
    most_recent = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    data = JSONField()

    @Timer(name='stellar_data')
    def _data(self):
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

        Stellar.objects.create(data=json.dumps(data, cls=DjangoJSONEncoder))
        obj, created = Price.objects.creaget(coin='epic', currency='xlm')
        obj.value = data['sepic_xlm']['price']
        obj.save()

    def __str__(self):
        return f"STELLAR, {self.updated}"


class Pancake(models.Model):
    most_recent = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    data = JSONField()

    @Timer(name='pancake_data')
    def _data(self):
        mgr = PancakeAPI()
        l = mgr.liquidity()
        try:
            volume_24 = mgr.pool_24_volume()
        except TypeError as er:
            print(er)
            volume_24 = {}
        try:
            bnb_vs_usd = Price.objects.get(coin__symbol="BNB", currency__symbol="USD").value
            epic_vs_usd = Price.objects.get(coin__symbol="EPIC", currency__symbol="USD").value
        except Exception as e:
            print(e)
            bnb_vs_usd = Price.get_cg_price('BNB')
            epic_vs_usd = Price.get_cg_price('EPIC')

        epic_vs_bnb = Decimal(l['wbnb']['WBNB']) / Decimal(l['wbnb']['EPIC'])

        epic_vs_bnb_usd = bnb_vs_usd * epic_vs_bnb
        l_bnb_usd = Decimal(l['wbnb']['WBNB']) * bnb_vs_usd \
                    + Decimal(l['wbnb']['EPIC']) * epic_vs_usd
        l_busd_usd = Decimal(l['busd']['BUSD']) + Decimal(l['busd']['EPIC']) * epic_vs_usd
        l_total = l_bnb_usd + l_busd_usd
        chart_data = mgr.chart_data()

        data = {
            'liquidity': l_total,
            'volume_24': volume_24,
            'chart_data': chart_data,
            'epic_vs_bnb': epic_vs_bnb,
            'epic_vs_bnb_usd': epic_vs_bnb_usd
            }

        Pancake.objects.create(data=json.dumps(data, cls=DjangoJSONEncoder))
        obj, created = Price.objects.creaget(coin='epic', currency='bnb')
        obj.value = epic_vs_bnb
        obj.save()

    def __str__(self):
        return f"PANCAKE, {self.updated}"


class Orderbook(models.Model):
    most_recent = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    data = JSONField()

    @Timer(name='get_orderbook')
    def _data(self):
        vitex_api = VitexRestApi()
        vitex_epic_btc_orderbook = vitex_api.get_order_book_depth(symbol="EPIC-002_BTC-000")
        stellar = Stellar.objects.last()
        # stellarx_sepic_usd_orderbook = stellar['sepic_usd']['orderbook']

        try:
            stellarx_sepic_xlm_orderbook = json.loads(json.loads(stellar.data))['sepic_xlm']['orderbook']
        except Exception as e:
            stellarx_sepic_xlm_orderbook = json.loads(stellar.data['sepic_xlm']['orderbook'])

        data = {
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
        Orderbook.objects.create(data=json.dumps(data, cls=DjangoJSONEncoder))

    def __str__(self):
        return f"ORDERBOOK, {self.updated}"
