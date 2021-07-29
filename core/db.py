from app.models import Coin, Price, Currency, Vitex, Stellar, Pancake, Orderbook, Explorer, Network
from mining.models import PoolStats, PoolManager, BlockManager, Block, Pool
from pycoingecko import CoinGeckoAPI
from core.timer import Timer
from django.apps import apps
from decimal import Decimal
from copy import deepcopy
import datetime
import json

cg = CoinGeckoAPI()


@Timer(name='epic_chart_price')
def epic_chart_price():
    data = cg.get_coin_market_chart_by_id(id='epic', vs_currency="usd", days=1)
    return data


class DataBase:
    def __init__(self):
        try:
            self.data = self._data()
        except Exception as e:
            print(e)
            try:
                self.init_db()
                self.update()
                self.data = self._data()
            except Exception as e:
                print(e)
                pass

    @Timer('all_data')
    def _data(self):
        data = {
            'block': self._block(),
            'vitex': self._vitex(),
            'stellar': self._stellar(),
            'pancake': self._pancake(),
            'orderbook': self._orderbook(),
            'explorer': self._explorer(),
            'network': self._network(),
            'coins': deepcopy(Coin.objects.all()),
            'prices': deepcopy(Price.objects.all()),
            'currency': deepcopy(Currency.objects.all()),
            'pools': deepcopy(Pool.objects.all()),
            'pool_stats': deepcopy(PoolStats.objects.all()),
            'blocks': deepcopy(Block.objects.all()),
            }

        p = data['prices']

        data['price'] = {
            'epic_vs_usd': Price.objects.get(coin__symbol="EPIC", currency__symbol="USD").value,
            'epic_vs_btc': Price.objects.get(coin__symbol="EPIC", currency__symbol="BTC").value,
            'epic_vs_xlm': Price.objects.get(coin__symbol="EPIC", currency__symbol="XLM").value,
            'epic_vs_bnb': Price.objects.get(coin__symbol="EPIC", currency__symbol="BNB").value,
            'btc_vs_usd': Price.objects.get(coin__symbol="BTC", currency__symbol="USD").value,
            'xlm_vs_usd': Price.objects.get(coin__symbol="XLM", currency__symbol="USD").value,
            'bnb_vs_usd': Price.objects.get(coin__symbol="BNB", currency__symbol="USD").value,
            }

        data['mining_stats'] = {
            'pools': data['pools'].order_by('name'),
            'blocks': data['blocks'],
            'last_block': data['blocks'].order_by('height').last(),
            'last_100': data['blocks'].order_by('-height')[:100],
            'solo_blocks': BlockManager().get_solo_blocks(),
            'colors': ['#3984BC', '#812D86', '#CBB128', '#4B565F'],
            }
        return data

    @staticmethod
    def update_and_get(query):
        model = apps.get_model(app_label='app', model_name=query.capitalize())
        model()._data()
        return eval(f"self.{query}()")

    @staticmethod
    def _block():
        try:
            return Block.objects.order_by('height').last()
        except Exception as e:
            print(f'Block ERROR: \n{e}')
            try:
                BlockManager()._data()
                return Block.objects.order_by('height').last()
            except Exception as e:
                print(f'Block ERROR: \n{e}')
                pass
        return Block.objects.order_by('height').last()

    @staticmethod
    def _pool(pool):
        try:
            return PoolStats.objects.filter(pool=pool).order_by('updated').last()
        except Exception as e:
            print(f'PoolStats ERROR: \n{e}')
            try:
                PoolStats()._data()
                return PoolStats.objects.filter(pool=pool).order_by('updated').last()
            except Exception as e:
                print(f'PoolStats ERROR: \n{e}')
                pass

    @staticmethod
    def _vitex():
        try:
            return json.loads(Vitex.objects.order_by('updated').last().data)
        except Exception as e:
            print(f'Vitex ERROR: \n{e}')
            try:
                Vitex()._data()
                return json.loads(Vitex.objects.order_by('updated').last().data)
            except Exception as e:
                print(f'Vitex ERROR: \n{e}')
                pass

    @staticmethod
    def _stellar():
        try:
            return json.loads(Stellar.objects.order_by('updated').last().data)
        except Exception as e:
            print(f'Stellar ERROR: \n{e}')
            try:
                Stellar()._data()
                return json.loads(Stellar.objects.order_by('updated').last().data)
            except Exception as e:
                print(f'Stellar ERROR: \n{e}')
                pass

    @staticmethod
    def _pancake():
        try:
            return json.loads(Pancake.objects.order_by('updated').last().data)
        except Exception as e:
            print(f'PANCAKE ERROR: \n{e}')
            try:
                Pancake()._data()
                return json.loads(Pancake.objects.order_by('updated').last().data)
            except Exception as e:
                print(f'PANCAKE ERROR: \n{e}')
                pass

    @staticmethod
    def _orderbook():
        try:

            return json.loads(Orderbook.objects.order_by('updated').last().data)
        except Exception as e:
            print(f'Orderbook ERROR: \n{e}')
            try:
                Orderbook()._data()
                return json.loads(Orderbook.objects.order_by('updated').last().data)
            except Exception as e:
                print(f'Orderbook ERROR: \n{e}')
                pass

    @staticmethod
    def _explorer():
        try:
            return Explorer.objects.order_by('updated').last()
        except Exception as e:
            print(f'Explorer ERROR: \n{e}')
            try:
                Explorer()._data()
                return Explorer.objects.order_by('updated').last()
            except Exception as e:
                print(f'Explorer ERROR: \n{e}')
                pass

    @staticmethod
    def _network():
        try:
            return Network.objects.order_by('timestamp').last()
        except Exception as e:
            print(f'Network ERROR: \n{e}')
            try:
                Network()._data()
                return Network.objects.order_by('timestamp').last()
            except Exception as e:
                print(f'Network ERROR: \n{e}')
                pass

    def to_epic(self, currency):
        if currency in ['USD' or 'usd' or 'usdt']:
            return self.get_price('epic', 'usd')
        elif currency in ['BTC' or 'btc' or 'bitcoin']:
            return self.get_price('epic', 'btc')
        elif currency in ['XLM' or 'xlm' or 'lumen']:
            return self.get_price('epic', 'xlm')
        else:
            obj = db.data['currency'].filter(symbol=currency)
            if obj:
                curr_vs_usd = obj.value
                return db.data['price']['epic_vs_usd'] * curr_vs_usd

    def get_block(self, height):
        return self.data['blocks'].get(height=height)

    def get_price(self, coin, currency='USD'):
        if isinstance(coin, Coin):
            coin = coin.symbol

        name = f"{coin.lower()}_vs_{currency.lower()}"
        return self.data['price'][name]

    def epic_to(self, currency):
        obj = self.data['currency'].filter(symbol=currency)
        epic = self.data['currency'].filter(symbol='EPIC')[0]
        if obj:
            return obj[0].symbol, epic.value * (1 / obj[0].value)

    @staticmethod
    def _delete_all():
        Coin.objects.all().delete()
        Currency.objects.all().delete()
        Vitex.objects.all().delete()
        Stellar.objects.all().delete()
        Pancake.objects.all().delete()
        Orderbook.objects.all().delete()
        Explorer.objects.all().delete()
        Network.objects.all().delete()

    def init_db(self):
        PoolManager()._data()
        Coin().init_data()

    def update(self):
        PoolManager()._data()
        BlockManager()._data()
        Currency()._data()
        Vitex()._data()
        Stellar()._data()
        Pancake()._data()
        Orderbook()._data()
        Explorer()._data()
        Network()._data()


db = DataBase()
