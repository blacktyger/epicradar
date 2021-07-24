from core.bokeh_charts.mini_charts import stellar_mini_chart, pancake_mini_chart, vitex_mini_chart
from core.bokeh_charts.stellar_line_price import stellar_price
from core.manager.epic_wallet import WalletManager
from core.manager.language import text
from app.utils import change, liquidity, total_volumes
from core.db import db

wallet = WalletManager()

data = {
    'assets_table': {
        'vitex': {
            'chart': vitex_mini_chart(db.vitex['candles']),
            'chain_link': "https://vitex.net/",
            'trade_link': "https://x.vite.net/trade?symbol=EPIC-002_BTC-000",
            'change': change(db.vitex['candles'], 'vitex', db.epic_vs_btc),
            'price_quota': db.epic_vs_btc,
            'price_usd': db.epic_vs_btc * db.btc_price,
            'volume': db.vitex['ticker']['quantity'],
            'liquidity': liquidity('vitex')
            },
        'stellar': {
            'chart': stellar_mini_chart(db.stellar['sepic_xlm']['trades']),
            'chain_link': "https://www.stellar.org/",
            'trade_link': "https://www.stellarx.com/markets/EPIC:GD4YEDHMQK2HD7DMKAG554JK4TVOTQNPWTKR2KHL5UCSJ6ART2UA2E32",
            'change': change(db.stellar['sepic_xlm']['trades'], 'stellar', db.epic_vs_xlm),
            'price_quota': db.epic_vs_xlm,
            'price_usd': db.epic_vs_xlm * db.xlm_price,
            'volume': db.stellar['sepic_xlm']['vol_24h'],
            'liquidity': liquidity('stellar')
            },
        'pancake': {
            'chart': pancake_mini_chart(db.pancake['chart_data']),
            'chain_link': "https://www.binance.org/en",
            'trade_link': "https://exchange.pancakeswap.finance/#/swap?outputCurrency=0x2cca66321b8f275339e622af66059ef251b38893&inputCurrency=BNB",
            'change': change(db.pancake['chart_data'], 'pancake', db.epic_vs_bnb),
            'price_quota': db.epic_vs_bnb,
            'price_usd': db.epic_vs_bnb * db.bnb_price,
            'volume': db.pancake['volume_24']['total'],
            'liquidity': db.pancake['liquidity']
            },
        },

    # 'stellar_chart': stellar_price(db.stellar['sepic_xlm']['trades']),
    'total_volumes': total_volumes(),
    'currency_list': db.currency,
    'epic_prices': [db.epic_to(x) for x in ['GBP', 'CNY']],
    'epic_vs_usd': db.epic_vs_usd,
    'epic_vs_btc': db.epic_vs_btc,
    'xlm_price': db.epic_vs_xlm,
    'btc_price': db.btc_price,
    'explorer': db.explorer,
    'balances': wallet.get_balance(),
    'updated': db.updated,
    'network': db.network,
    'pancake': db.pancake,
    'segment': 'index',
    'vitex': db.vitex['ticker'],
    'text': text(kwargs={'updated': db.updated}),
    'node': {'blockchain_size': wallet.blockchain_size(),
             'is_online': wallet.node_is_online(),
             'data': wallet.node_data()}

    }


