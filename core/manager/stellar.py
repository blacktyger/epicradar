import time

from stellar_sdk import Server, Keypair, TransactionBuilder, Network
from stellar_sdk import Asset as asset_
from operator import itemgetter
from decimal import Decimal
import requests
import datetime
import json


def get_ts(date):
    """ Convert datetime object to timestamp in milliseconds """
    if not isinstance(date, str):
        date = str(date).split(" ")[0]
    else:
        date = date
    return int(time.mktime(time.strptime(date, "%Y-%m-%d"))) * 1000


# !! ENV VARIABLE FOR PRIVATE KEYS
VARIABLES = {
    'HORIZON_URL': "https://horizon.stellar.org",
    'wallet': {
        'keys': {
            'pair': None,
            'public': "GBYB6Y6SXU2Y7RXGAPWQIXO5IULILZLBLWTRHI6QSWAUGHM3BLF33A3C",
            'private': "SCS4OCUNPOBW3E7MPKYQG7Z3PZC7ZSUF2CITUI3LB3CE7MHABZ2FASXH"
            }
        },
    'epic_gateway_addr': "GCXAJPJNTN7UQSQW6ZGEUE2Z7JNC2R2CGW4VXGITWFE6OWBPQZ5I2M57",
    'epic_gateway_addr_2': "GD6W7XRMXCH6WCET65AMOZK5BABG3M53VKUVIQNIFMW2EVUEV4NCM6K7",
    }


class StellarNetworkManager:
    """Manage Stellar API, help build and listen for network transactions"""

    def __init__(self, variables=None):
        if variables is None:
            variables = VARIABLES
        self.vars = variables
        self.wallet = self.vars['wallet']
        self.server = Server(horizon_url=self.vars['HORIZON_URL'])
        self.init_source_account()
        self.assets = {}
        self.init_assets()
        self.base = self.assets['sepic']
        self.counter = self.assets['xlm']
        self.epic_gateway_addr = self.vars["epic_gateway_addr"]
        self.epic_gateway_addr_2 = self.vars["epic_gateway_addr_2"]
        self.destination_asset = self.assets['sepic']

    def init_source_account(self):
        try:
            self.wallet['keys']['pair'] = Keypair.from_secret(self.wallet['keys']['private'])
            self.source_account = self.server.load_account(account_id=self.wallet['keys']['pair'].public_key)
            # print(f"INITIALIZE KEYS AND SOURCE ACCOUNT: {self.wallet['keys']['pair'].public_key}")
        except:
            self.source_account = self.wallet['keys']['public']

    def listen_for_transaction(self):
        """
        >> Get network transaction history for source account
        >> Compare local transaction history with network
        >> while there is no new transaction in network
            >> read_local_history every x sec
            >> if no new tx after x times return True and
                prompt TIME OUT / FAILED
        >> if new transaction's loop over them
            >> check if it was checked before
            >> check if confirmed_in_network
            >> if yes return True
            >> else continue through new_tx list and repeat
    """

    def get_send_paths(self, **kwargs):
        def get_path_asset(record):
            path = record['path'][0]
            asset = asset_(code=path['asset_code'], issuer=path['asset_issuer'])
            print(f'PATH ASSET: {asset.code}')
            return [asset]

        def get_best_path(paths):
            sorted_by_amount = sorted(paths, key=itemgetter('destination_amount'), reverse=True)
            direct = None
            direct_amount = 0
            best_amount = Decimal(sorted_by_amount[0]['destination_amount'])

            for path in sorted_by_amount:
                if not path['path']:
                    direct = path
                    direct_amount = Decimal(path['destination_amount'])

            print(f"{direct_amount} {best_amount}")
            try:
                percentage = abs(direct_amount - best_amount) / max(direct_amount, best_amount) * 100
            except ZeroDivisionError:
                percentage = float('inf')

            if percentage < 0.5:
                sorted_by_amount.insert(0, direct)
                print(f"SUCCESS PATH: Direct")
            else:
                print(f"PATHS PERCENTAGE DIFFERENCE {round(percentage, 3)}%")

            return sorted_by_amount

        records = self.server.strict_send_paths(**kwargs).call()
        paths = []

        for r in records['_embedded']['records']:
            if 'destination_asset_code' in r.keys():
                if r['destination_asset_code'] == self.destination_asset.code:
                    paths.append(r)

        paths = get_best_path(paths)

        if paths[0]['path']:
            paths[0]['path'] = get_path_asset(paths[0])
            print(f"NO DIRECT PATH - BRIDGE ASSET: {paths[0]['path']}")

        return paths[0]

    def build_transaction(self, kwargs):
        """Build Swapic transaction on stellar network and save to """
        if 'source_asset' not in kwargs.keys():
            kwargs['source_asset'] = self.assets['xlm']

        base_fee = 100
        source_account = self.source_account
        destination = self.epic_gateway_addr
        destination_asset = kwargs['destination_asset']
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        send_amount = kwargs['send_amount']
        send_code = kwargs['send_code']
        set_timeout = kwargs['set_timeout']
        text_memo = kwargs['text_memo']

        path = self.get_send_paths(
            source_asset=kwargs['source_asset'],
            source_amount=kwargs['send_amount'],
            destination=self.epic_gateway_addr,
            )
        print("SUCCESS PATH: ", path)

        dest_min = path['destination_amount']

        print('')
        print("---------------------------------------------")
        print(f"TRADE {send_amount} {send_code} FOR {dest_min} {destination_asset.code}")
        print("----------------------------------------------")
        print('')

        transaction = TransactionBuilder(
            source_account=source_account,
            network_passphrase=network_passphrase,
            base_fee=base_fee) \
            .append_path_payment_strict_send_op(
            send_code=send_code, send_issuer=None,
            dest_code=destination_asset.code,
            dest_issuer=destination_asset.issuer, send_amount=send_amount,
            dest_min=dest_min, destination=destination,
            path=path['path']) \
            .set_timeout(set_timeout) \
            .add_text_memo(text_memo) \
            .build()
        print(f"SUCCESS Swapic transaction build")

        return transaction

    def init_assets(self):
        self.assets = {
            'xlm': asset_("XLM"),
            'sepic': asset_(code='EPIC', issuer='GD4YEDHMQK2HD7DMKAG554JK4TVOTQNPWTKR2KHL5UCSJ6ART2UA2E32'),
            'usd': asset_(code='USD', issuer='GDUKMGUGDZQK6YHYA5Z6AY2G4XDSZPSZ3SW5UN3ARVMO6QSRDWP5YLEX')
            }

    def add_asset(self, name, code, issuer):
        self.assets[name] = asset_(code=code, issuer=issuer)

    def last_trade(self):
        return self.trades(limit=1)[0]

    @staticmethod
    def xlm_sepic_send_path(amount):
        full_url = f"https://horizon.stellar.org/paths/strict-send?destination_assets=EPIC%3AGD4YEDHMQK2HD7DMKAG554JK4TVOTQNPWTKR2KHL5UCSJ6ART2UA2E32&source_asset_type=native&source_amount={amount}"
        # print(requests.Request('GET', full_url).prepare().url)
        return json.loads(requests.get(full_url).content)

    @staticmethod
    def xlm_sepic_receive_path(amount):
        full_url = f"https://horizon.stellar.org/paths/strict-receive?&destination_asset_type=credit_alphanum4&destination_asset_code=EPIC&destination_asset_issuer=GD4YEDHMQK2HD7DMKAG554JK4TVOTQNPWTKR2KHL5UCSJ6ART2UA2E32&source_assets=native&destination_amount={amount}"
        # print(requests.get(full_url).content)
        return json.loads(requests.get(full_url).content)

    def find_tx(self, amount, address=None):
        pass

    def last_24h(self):
        end_today = datetime.datetime.today() + datetime.timedelta(days=1)
        start_today = datetime.datetime.today()
        try:
            return self.trades(start=get_ts(start_today), end=get_ts(end_today),
                               resolution=86400000)[0]
        except IndexError:
            return self.trades(end=get_ts(end_today), resolution=86400000)[0]

    def orderbook(self):
        """
        Return orderbook dict with :bids and :asks with amount and price
        for given trading pair (:base, :counter) EXAMPLE: EPIC/XLM
        """
        data = self.server.orderbook(self.base, self.counter).call()
        asks = [[float(x['price']),
                 float(x['amount']) / float(x['price'])] for x in data['bids']]

        bids = [[float(x['price']), float(x['amount'])] for x in data['asks']]

        return {'bids': bids, 'asks': asks}

    def trades(self, start=None, end=None, resolution=1000*60*60, limit=164):
        """
        Return dict with last trades on given pair
        :base :counter - assets
        :start :end - date range (datetime obj or string 'year-month-day' format)
        :resolution - time interval in milliseconds
        :limit - number of records to show
        """
        data = self.server.trade_aggregations(self.base, self.counter, resolution=resolution,
                                              start_time=start, end_time=end
                                              ).limit(limit).order('dec').call()
        data = [{'time': x['timestamp'], 'trade_count': x['trade_count'],
                 'base_volume': x['base_volume'], 'counter_volume': x['counter_volume'],
                 'price': x['avg'], 'high': x['high'], 'low': x['low'],
                 'open': x['open'], 'close': x['close']} for x in data['_embedded']['records']]

        return data
