from json import JSONDecodeError
from .network_hashrate import *
from core.db import db
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

    def __init__(self, algo, rig_hashrate, currency='USD', power_consumption=0,
                 electricity_cost=0, pool_fee=0, period=1):
        self.network = NetworkCalculator(node_url="https://epicradar.tech/node/v1/status")
        self.model = db.network_data()
        self.currency_list = db.currency
        self.block_time = 60
        self.algo = algo
        self.rig_hashrate = rig_hashrate
        self.currency = self.currency_list[currency]
        self.power_consumption = power_consumption
        self.electricity_cost = electricity_cost
        self.pool_fee = pool_fee
        self.period = period
        self.usd_price = float(db.epic_vs_usd)
        self.btc_price = float(db.epic_vs_btc)
        self.rig_reward()
        self.rig_income()
        self.rig_cost()
        self.rig_profit()

    def height(self):
        return int(self.model['height'])

    def network_hash(self):
        return self.model['hash'][self.algo]

    def target_diff(self):
        return self.model['diff'][self.algo]

    def reward(self):
        height = self.height()
        if 698401 < height <= 1157760:
            return [8.0, 0.5328, 7.4672]
        elif 1157761 < height <= 1224000:
            return [4.0, 0.2664, 3.7336]
        elif 1224001 < height <= 1749600:
            return [4.0, 0.2220, 3.7780]
        elif 1749601 < height <= 2023200:
            return [4.0, 0.1776, 3.8224]
        elif 2023201 < height <= 2275200:
            return [2.0, 0.0888, 1.9112]

    def algo_percentage(self):
        if self.algo == "progpow":
            return 0.38
        if self.algo == "randomx":
            return 0.6
        if self.algo == "cuckoo":
            return 0.02

    def blocks_per_day(self):
        """
        Calculate number of blocks per 24h based on block_time and algorithm
        """
        blocks_day = 86400 / self.block_time

        if self.algo == "progpow":
            return blocks_day * self.algo_percentage()
        if self.algo == "randomx":
            return blocks_day * self.algo_percentage()
        if self.algo == "cuckoo":
            return blocks_day * self.algo_percentage()

    def currency_to_btc(self, value, currency=None):
        """
        Find bitcoin price based on currency
        """
        if currency is None:
            url = f'https://blockchain.info/tobtc?currency={self.currency["symbol"]}&value={value}'
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
        blocks_per_day = (self.rig_hashrate / self.network_hash()) * self.blocks_per_day()
        hours_for_one_block = 24 / blocks_per_day
        block_reward = self.reward()[2]
        block_value = float(self.currency['price']) * self.usd_price * block_reward

        return {'hours_for_one_block': hours_for_one_block, 'days': hours_for_one_block / 24,
                'block_reward': block_reward, 'block_value': block_value}

    def pool_cost(self):
        """
        Calculate pool mining software cost based on pool_fee
        """
        if self.pool_fee:
            print(f" yield - pool_fee: {self.pool_fee}")
            return self.mining_reward * (float(self.pool_fee) / 100)

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
            value += (self.pool_cost() * self.usd_price) * float(self.currency['price'])

        self.cost = {'value': value, 'btc_value': self.currency_to_btc(value=value)}

    def rig_profit(self):
        """
        Calculate rig profit based on rig_income and rig_cost
        """
        profit = self.income['value'] - self.cost['value']
        btc_profit = self.income['btc_value'] - self.cost['btc_value']
        self.profit = {'value': profit, 'btc_value': btc_profit}

    def rig_income(self):
        """
        Calculate rig income based on rig_reward and Epic price vs currency
        """
        amount = self.mining_reward
        value = float(self.currency['price']) * self.usd_price
        print(type(amount), type(value), type(self.btc_price))
        self.income = {'value': amount * value, 'btc_value': amount * self.btc_price}

    def rig_reward(self):
        """
        Calculate rig reward based on rig_hashrate and block algorithm
        """
        if self.rig_hashrate and self.algo:
            rig_vs_net = self.rig_hashrate / self.network_hash()
            epic_amount = rig_vs_net * self.blocks_per_day() * self.reward()[2] * self.period
        else:
            epic_amount = 0
        self.mining_reward = epic_amount
