import json

from django.apps import apps

from core.bokeh_charts.mini_charts import stellar_mini_chart, pancake_mini_chart, vitex_mini_chart
from app.utils import change
from core.bokeh_charts.vitex_line_price import vitex_price
from core.manager.epic_wallet import WalletManager
from mining.mining_calculator import Calculator
from core.manager.language import text
from decimal import Decimal
import datetime

wallet = WalletManager()


def data(db):
    updated = datetime.datetime.now()
    vitex = json.loads(db.data['vitex'])
    stellar = json.loads(db.data['stellar'])
    pancake = json.loads(db.data['pancake'])
    orderbook = json.loads(db.data['orderbook'])
    explorer = db.data['explorer']
    network = db.data['network']

    vitex_total = Decimal(vitex['ticker']['quantity'])
    stellar_total = Decimal(stellar['sepic_xlm']['vol_24h'])
    pancake_total = Decimal(pancake['volume_24']['total'])

    def daily_mined():
        from mining.mining_calculator import Calculator
        mining = Calculator(algo='randomx', rig_hashrate=1, currency='USD')
        block_time = explorer.blocktime
        block_reward = mining.reward()[0]
        return {'coins': (86400 / block_time) * block_reward,
                'blocks': 86400 / block_time}

    def halving():
        """
        Calculate time of next halving based on block height and average block time.
        """
        from mining.mining_calculator import Calculator
        mining = Calculator(algo='randomx', rig_hashrate=1, currency='USD')
        block_time = explorer.blocktime
        block_height = explorer.height
        time_left = ((mining.reward()[3] - block_height) * block_time)
        date = datetime.datetime.now() + datetime.timedelta(seconds=int(time_left))
        return {'date': date, 'height': mining.reward()[3]}

    def liquidity(chain):
        if chain == "stellar":
            stellar = orderbook['stellarx']['xlm']
            s_bids = sum(x[1] for x in stellar['bids'])
            s_asks = sum(x[1] for x in stellar['asks'])
            stellar_l = Decimal(s_bids + s_asks)
            return stellar_l * db.get_price('epic')

        elif chain == 'vitex':
            vitex = orderbook['vitex']['btc']
            v_bids = sum(float(x[1]) for x in vitex['bids'])
            v_asks = sum(float(x[1]) for x in vitex['asks'])
            vitex_l = Decimal(v_bids + v_asks)
            return vitex_l * db.get_price('epic')

    return {
        'assets_table': {
            'vitex': {
                'chart': vitex_mini_chart(vitex['candles']),
                'chain_link': "https://vitex.net/",
                'trade_link': "https://x.vite.net/trade?symbol=EPIC-002_BTC-000",
                'change': change(vitex['candles'], 'vitex', db.get_price('epic', 'btc')),
                'price_quota': db.get_price('epic', 'btc'),
                'price_usd': db.get_price('epic', 'btc') * db.get_price('btc'),
                'volume': vitex['ticker']['quantity'],
                'liquidity': liquidity('vitex')
                },
            'stellar': {
                'chart': stellar_mini_chart(stellar['sepic_xlm']['trades']),
                'chain_link': "https://www.stellar.org/",
                'trade_link': "https://www.stellarx.com/markets/EPIC:GD4YEDHMQK2HD7DMKAG554JK4TVOTQNPWTKR2KHL5UCSJ6ART2UA2E32",
                'change': change(stellar['sepic_xlm']['trades'], 'stellar', db.get_price('epic', 'xlm')),
                'price_quota': db.get_price('epic', 'xlm'),
                'price_usd': db.get_price('epic', 'xlm') * db.get_price('xlm'),
                'volume': stellar['sepic_xlm']['vol_24h'],
                'liquidity': liquidity('stellar')
                },
            'pancake': {
                # 'chart': pancake_mini_chart(pancake['chart_data']),
                'chain_link': "https://www.binance.org/en",
                'trade_link': "https://exchange.pancakeswap.finance/#/swap?outputCurrency=0x2cca66321b8f275339e622af66059ef251b38893&inputCurrency=BNB",
                'change': change(pancake['chart_data'], 'pancake', db.get_price('epic', 'bnb')),
                'price_quota': db.get_price('epic', 'bnb'),
                'price_usd': db.get_price('epic', 'bnb') * db.get_price('bnb'),
                'volume': pancake['volume_24']['total'],
                'liquidity': pancake['liquidity']
                },
            },
        'mining_info': {
            'circulating': explorer.circulating,
            'mined_': (explorer.circulating / 21_000_000) * 100,
            'mined_24h': daily_mined(),
            'block_reward': Calculator(algo='randomx', rig_hashrate=1,
                                       currency='USD').reward()[2],
            'block_value': Decimal(Calculator(algo='randomx', rig_hashrate=1,
                                              currency='USD').reward()[2]) * db.get_price('epic'),
            'halving': halving(),
            },
        'mining_stats': db.data['mining_stats'],
        'vitex_price': vitex_price(vitex['candles']),
        'total_volumes': vitex_total + stellar_total + pancake_total,
        'currency_list': db.data['currency'],
        'epic_prices': [db.epic_to(x) for x in ['GBP', 'CNY']],
        'epic_vs_usd': db.get_price('epic'),
        'epic_vs_btc': db.get_price('epic', 'btc'),
        'xlm_price': db.get_price('epic', 'xlm'),
        'btc_price': db.get_price('btc'),
        'explorer': explorer,
        # 'balances': wallet.get_balance(),
        'updated': updated,
        'network': network,
        'network_hash': json.loads(network.hash),
        'pancake': pancake,
        'segment': 'index',
        'vitex': vitex['ticker'],
        'text': text(kwargs={'updated': updated}),
        'node': {'blockchain_size': wallet.blockchain_size(),
                 'is_online': wallet.node_is_online(),
                 'data': wallet.node_data()}
        }
