from json import JSONDecodeError
from .network_hashrate import *
from decimal import Decimal
import requests
import json


class Calculator:
    """
## TASK ##
    - receive input from user
    - do calculations
    - send data to views and display

## DATA ##
- data from explorer
    - network_hashrate
    - target_diff

- data to calculate prices
    - epic price
    - currency rates

- data from user
    - rig hashrate
    - currency
    - power consumption
    - power rate cost
    """

    algos = ['randomx', 'progpow']
    halvings = [1157760, 1224000, 2275200]

    def __init__(self, algo, rig_hashrate, currency='USD', power_consumption=0,
                 electricity_cost=0, pool_fee=0, period=1):
        from core.db import db
        self.network = NetworkCalculator(node_url="https://epicradar.tech/node/v1/status")
        self.db = db
        self.model = self.db.data['network']
        self.currency_list = self.db.data['currency']
        self.block_time = Decimal(60)
        self.algo = algo
        self.rig_hashrate = rig_hashrate
        try:
            self.currency = self.currency_list.get(symbol=currency)
        except:
            self.currency = self.currency_list.get(symbol='USD')

        self.power_consumption = Decimal(power_consumption or 0)
        self.electricity_cost = Decimal(electricity_cost or 0)
        self.pool_fee = Decimal(pool_fee or 0)
        self.period = Decimal(period)
        self.usd_price = self.db.get_price('epic')
        self.btc_price = self.db.get_price('epic', 'btc')
        self.rig_reward()
        self.rig_income()
        self.rig_cost()
        self.rig_profit()

    def height(self):
        return int(self.model.height)

    def network_hash(self):
        return json.loads(self.model.hash)[self.algo]

    def target_diff(self):
        return json.loads(self.model.diff)[self.algo]

    def reward(self):
        height = self.height()
        if 698401 < height <= 1157760:
            return [8.0, 0.5328, 7.4672, 1157760]
        elif 1157761 < height <= 1224000:
            return [4.0, 0.2664, 3.7336, 2275200]
        elif 1224001 < height <= 1749600:
            return [4.0, 0.2220, 3.7780, 2275200]
        elif 1749601 < height <= 2023200:
            return [4.0, 0.1776, 3.8224, 2275200]
        elif 2023201 < height <= 2275200:
            return [2.0, 0.0888, 1.9112]

    def algo_percentage(self):
        if self.algo == "progpow":
            return Decimal(0.38)
        if self.algo == "randomx":
            return Decimal(0.6)
        if self.algo == "cuckoo":
            return Decimal(0.02)

    def blocks_per_day(self):
        """
        Calculate number of blocks per 24h based on block_time and algorithm
        """
        blocks_day = 86400 / self.block_time

        if self.algo == "progpow":
            return Decimal(blocks_day * self.algo_percentage())
        if self.algo == "randomx":
            return Decimal(blocks_day * self.algo_percentage())
        if self.algo == "cuckoo":
            return Decimal(blocks_day * self.algo_percentage())

    def currency_to_btc(self, value, currency=None):
        """
        Find bitcoin price based on currency
        """
        if currency is None:
            url = f'https://blockchain.info/tobtc?currency={self.currency.symbol}&value={value}'
        else:
            url = f'https://blockchain.info/tobtc?currency={currency}&value={value}'
        try:
            return json.loads(requests.get(url).content)
        except JSONDecodeError as er:
            print(er)
            return 0

    def solo_block(self):
        """
        Calculate time needed to mine block solo based on rig_hashrate and block algorithm
        network_hashrate() / rig_hashrate * blocks_per_day
        """
        print(self.rig_hashrate, self.network_hash(), self.blocks_per_day())
        blocks_per_day = Decimal(self.rig_hashrate / self.network_hash()) * self.blocks_per_day()
        hours_for_one_block = 24 / blocks_per_day
        block_reward = self.reward()[2]
        
        block_value = self.currency.value * self.usd_price * Decimal(block_reward)

        return {'hours_for_one_block': float(hours_for_one_block), 'days': float(hours_for_one_block / 24),
                'block_reward': block_reward, 'block_value': float(block_value)}

    def pool_cost(self):
        """
        Calculate pool mining software cost based on pool_fee
        """
        if self.pool_fee:
            print(f" yield - pool_fee: {self.pool_fee}")
            return self.mining_reward * (self.pool_fee / 100)

    def rig_cost(self):
        """
        Calculate rig cost based on electricity_cost, power_consumption and currency
        """
        if self.electricity_cost and self.power_consumption is not None:
            mining_time = 24 * self.period * self.algo_percentage()
            mining_cost = (self.power_consumption / 1000) * self.electricity_cost
            value = mining_time * mining_cost
        else:
            value = 0

        if self.pool_fee:
            value += self.pool_cost() * self.usd_price * self.currency.value

        self.cost = {'value': Decimal(value), 'btc_value': Decimal(self.currency_to_btc(value=value))}

    def rig_profit(self):
        """
        Calculate rig profit based on rig_income and rig_cost
        """
        profit = self.income['value'] - self.cost['value']
        btc_profit = self.income['btc_value'] - self.cost['btc_value']
        self.profit = {'value': Decimal(profit), 'btc_value': Decimal(btc_profit)}

    def rig_income(self):
        """
        Calculate rig income based on rig_reward and Epic price vs currency
        """
        amount = self.mining_reward
        value = self.currency.value * self.usd_price
        # print(type(amount), type(value), type(self.btc_price))
        self.income = {'value': Decimal(amount * value), 'btc_value': Decimal(amount * self.btc_price)}

    def rig_reward(self):
        """
        Calculate rig reward based on rig_hashrate and block algorithm
        """
        try:
            if self.rig_hashrate and self.algo:
                rig_vs_net = Decimal(self.rig_hashrate / self.network_hash())
                epic_amount = rig_vs_net * self.blocks_per_day() * Decimal(self.reward()[2]) * self.period
            else:
                epic_amount = 0
            self.mining_reward = Decimal(epic_amount)
        except Exception as e:
            print(e)
            self.mining_reward = Decimal(0)
