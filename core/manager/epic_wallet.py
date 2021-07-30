from pathlib import Path

from core.secrets import epic_wallet_api_secret, epic_wallet_password
# from wallet.tools import Command
from decimal import Decimal
import more_itertools
import requests
import json
import re

COMMANDS = ['info', 'txs', 'send', 'create']


class WalletManager:
    def __init__(self,
                 hostname="https://epicradar.tech",
                 port=3413,
                 api_secret=epic_wallet_api_secret,
                 password=epic_wallet_password):
        self.receive_address = f"{hostname}/wallet"
        self.blockchain_dir = '"/home/blacktyger/.epic/main/chain_data"'
        self.node = f"{hostname}/node"
        self.hostname = hostname
        self.port = port
        self.url = f"http://{self.hostname}:{self.port}"
        self.api_secret = api_secret
        self.password = password
        self.auth = ('epic', self.api_secret)

    def blockchain_size(self):
        try:
            return round(sum(file.stat().st_size for file in Path(self.blockchain_dir).rglob('*'))/10**9, 2)
        except:
            return 1.60

    def node_is_online(self):
        url = f"{self.node}/v1/status"
        try:
            r = json.loads(requests.get(url).content)
            # print(f"--> Node: Online")
            return True
        except:
            # print(f"--> Node: Offline")
            return False

    def node_data(self):
        if self.node_is_online():
            url = f"{self.node}/v1/status"
            # print(json.loads(requests.get(url).content))
            return json.loads(requests.get(url).content)
        else:
            return False

    # def get_balance(self):
    #     b = []
    #     try:
    #         if self.node_is_online():
    #             for line in self.command('info').split('\n'):
    #                 patter = r"\d+.\d+"
    #                 match = re.findall(patter, line)
    #                 if match:
    #                     b.append(match)
    #             b = [Decimal(n) for n in list(more_itertools.collapse(b))]
    #             balances = {
    #                 'total': b[1],
    #                 'wait_conf': float(b[2]),
    #                 'wait_final': float(b[3]),
    #                 'locked': float(b[4]),
    #                 'spendable': float(b[5])
    #                 }
    #             return balances
    #     except:
    #         balances = {
    #             'total': 0,
    #             'wait_conf': 0,
    #             'wait_final': 0,
    #             'locked': 0,
    #             'spendable': 0
    #             }
    #
    #         return balances
    #
    # def get_txs(self):
    #     transactions = []
    #     for line in self.command('txs').split('\n'):
    #         patter = r"^\s{1}\d+\s{3}\w"
    #         if re.search(patter, line):
    #             r = [x for x in line.split(' ') if x != ""]
    #             tx = {'confirmed': r[6], 'created at': r[4] + ' ' + r[5],
    #                   'type': r[1], 'tx_id': r[3], 'conf_time': r[7] + ' ' + r[8], 'credit': r[-5],
    #                   'debit': r[-4], 'fee': r[-3], 'amount': r[-2]}
    #             transactions.append(tx)
    #     transactions.reverse()
    #     return transactions


# x = WalletManager()

# print(x.blockchain_size())