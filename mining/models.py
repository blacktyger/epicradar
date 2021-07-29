from django.utils.timezone import make_aware
from jsonfield import JSONField
from django.db import models
from core.timer import Timer
from dateutil import tz
import pandas as pd
import requests
import datetime
import socket
import json
import time


def ping_address(host, timeout=2):
    if ':' in host:
        old_host = host.split(':')
        host = old_host[0]
        port = int(old_host[1])
    else:
        port = 3415
    s = socket.socket()
    s.settimeout(timeout)
    result = False
    start = time.time()
    try:
        s.connect((host, port))
        s.close()
        result = True
        end = time.time()
        ms = 1000 * (end - start)
        # print(f"{host}:{port}  {result}, {int(ms)}")
        return [result, int(ms)]
    except (socket.gaierror, socket.timeout) as e:
        print(e)

    return [result, 0]


class Pool(models.Model):
    name = models.CharField(max_length=32, unique=True)
    url = models.URLField()
    api_url = models.URLField(null=True)
    stratum_urls = models.CharField(max_length=256)

    def last_found(self):
        obj = PoolStats.objects.filter(pool=self).last().data
        return json.loads(obj)['stats']['block_stats']['last']

    def blocks_in_last100(self):
        last = Block.objects.first().height
        qs = Block.objects.filter(height__range=(last - 100, last+1), pool=self)
        return qs.count()

    def workers_count(self):
        obj = Pool.objects.get(id=self.id).stats.last()
        obj_data = json.loads(obj.data)['stats']['stats']
        workers_count = 0
        if obj.pool.name == 'icemining':
            workers_count += int(obj_data['workers'])
        else:
            workers_count += int(obj_data['onlineRandomX'])
            workers_count += int(obj_data['onlineProgPow'])
            try: workers_count += int(obj_data['onlineCuckoo'])
            except Exception: workers_count += 0
        return workers_count

    def total_hashrate(self):
        obj = Pool.objects.get(id=self.id).stats.last()
        obj_data = json.loads(obj.data)['stats']['stats']

        hashrate = 0
        if obj.pool.name == 'icemining':
            hashrate += int(obj_data['hashrate'])
        else:
            hashrate += int(str(obj_data['hashrateRandomX']).split('.')[0])
            hashrate += int(str(obj_data['hashrateProgPow']).split('.')[0])
            hashrate += int(str(obj_data['hashrateCuckoo']).split('.')[0])
        return hashrate

    def is_online(self):
        ping = PoolManager().ping_pool(pool=self)
        return ping['pool_online']

    def __str__(self):
        return f"{self.name}"


class PoolStats(models.Model):
    updated = models.DateTimeField(auto_now=True)
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name='stats')
    data = JSONField()

    def __str__(self):
        return f"{self.pool.name.upper()} STATS [{self.updated}]"


class Block(models.Model):
    height = models.IntegerField(unique=True)
    timestamp = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField(null=True)
    network_hashrate = JSONField()
    network_diff = JSONField()
    algorithm = models.CharField(max_length=32, null=True, blank=True)
    hash = models.CharField(max_length=256, null=True, blank=True)
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE,
                             related_name='block', null=True)

    class Meta:
        ordering = ['-height']

    @staticmethod
    def get_block(height):
        obj = Block.objects.filter(height=int(height))
        if obj:
            return obj[0]

    def __str__(self):
        return f"BLOCK {self.height} [{self.algorithm} | {self.pool}]"


class BlockManager:
    def get_solo_blocks(self):
        return Block.objects.filter(pool__isnull=True)

    def add_block(self, **kwargs):
        block, created = Block.objects.get_or_create(height=int(kwargs['height']))

        for k, v in kwargs.items():
            if getattr(block, k) != v:
                setattr(block, k, v)
                block.save()

    @Timer('blocks_data')
    def _data(self):
        block_limit = -100
        net_hash_file = "network_hashrate.csv"
        net_diff_file = "network_difficulty.csv"
        hash_df = pd.read_csv(net_hash_file, index_col=0)[block_limit:-1].to_dict('records')
        diff_df = pd.read_csv(net_diff_file, index_col=0)[block_limit:-1].to_dict('records')

        for i, h in enumerate(hash_df):
            kwargs = {
                'height': h['height'],
                'network_hashrate': h,
                'network_diff': diff_df[i],
                'timestamp': h['timestamp'],
                'date': make_aware(datetime.datetime.utcfromtimestamp(int(h['timestamp'])), timezone=tz.gettz('GMT'))
                }

            self.add_block(**kwargs)


class PoolManager:
    def __init__(self):
        self.pools = Pool.objects.all()
        if self.pools.count() < 1:
            self.init_data()

    @Timer('pool_data')
    def _data(self):
        kwargs = {'pool': Pool, 'data': {}}

        for pool in self.pools:
            kwargs['pool'] = pool
            kwargs['data']['ping'] = self.ping_pool(pool.name)
            try:
                kwargs['data']['stats'] = self.stats_parser(pool.name)
                PoolStats.objects.create(**kwargs)
            except requests.exceptions.ReadTimeout as er:
                print(er)
                continue

    def ping_pool(self, pool):
        if isinstance(pool, str):
            pool = self.pools.get(name=pool)

        data = {'pool_online': False, 'stratums': {}}

        for stratum in eval(pool.stratum_urls):
            ping = ping_address(stratum)
            if ping[0]:
                data['pool_online'] = True
                data['stratums'][stratum] = {'online': ping[0],
                                             'latency': ping[1]}
            else:
                data['stratums'][stratum] = {'online': False,
                                             'latency': 0}
        return data

    def stats_parser(self, pool):
        if isinstance(pool, str):
            pool = self.pools.get(name=pool)

        data = {'stats': {}, 'blocks': [], 'block_stats': {}}

        if pool.name == 'icemining':
            r = eval(f"self.get_{pool.name.lower()}()")
            data['stats'] = r[0]
            data['blocks'] = [block for block in r[1] if block['sym'] == 'EPIC']
            data['block_stats']['last'] = r[0]['lastblock']
            data['block_stats']['24h'] = r[0]['24h_blocks']

            for block in data['blocks']:
                kwargs = {
                    'height': block['height'],
                    'algorithm': block['algo'].lower(),
                    'timestamp': block['t'],
                    'date': make_aware(datetime.datetime.utcfromtimestamp(int(block['t'])), timezone=tz.gettz('GMT')),
                    'hash': block['hash'],
                    'pool': pool
                    }
                BlockManager().add_block(**kwargs)
        else:
            r = eval(f"self.get_{pool.name.lower()}()")['data']
            data['stats'] = r['poolStats']
            data['blocks'] = r['poolBlocks']['latest']
            data['block_stats']['total'] = r['poolBlocks']['total']
            data['block_stats']['last'] = r['poolBlocks']['lastFound']

            for block in data['blocks']:
                kwargs = {
                    'height': block['blockHeight'],
                    'algorithm': block['algo'].lower(),
                    'timestamp': block['time'],

                    'date': make_aware(datetime.datetime.utcfromtimestamp(int(block['time'])), timezone=tz.gettz('GMT')),

                    'hash': block['hash'],
                    'pool': pool
                    }
                BlockManager().add_block(**kwargs)

        return data

    @staticmethod
    def init_data():
        for pool in POOLS:
            Pool.objects.get_or_create(
                name=pool[0], url=pool[1], api_url=pool[2], stratum_urls=pool[3])
        print(f'{len(POOLS)} NEW POOLS CREATED')

    def get_51pool(self):
        pool = self.pools.get(name='51pool')
        stats_api = json.loads(requests.get(f"{pool.api_url}", timeout=10).content)
        # block_api = json.loads(requests.get(f"{pool.api_url}blocks", timeout=5).content)[0]
        return stats_api

    def get_icemining(self):
        pool = self.pools.get(name='icemining')
        stats_api = json.loads(requests.get(f"{pool.api_url}currencies", timeout=10).content)['EPIC']
        block_api = json.loads(requests.get(f"{pool.api_url}blocks", timeout=10).content)
        return stats_api, block_api

    def get_epicmine(self):
        pool = self.pools.get(name='epicmine')
        stats_api = json.loads(requests.get(f"{pool.api_url}", timeout=10).content)
        return stats_api

    def get_fastepic(self):
        pool = self.pools.get(name='fastepic')



POOLS = [
    ['51pool', 'https://51pool.online', 'https://51pool.online/api/', "['51pool.online:3416', '51pool.online:4416']"],
    ['icemining', 'https://icemining.ca', 'https://icemining.ca/api/', "['epic.hashrate.to:4000']"],
    # ['fastepic', 'https://fastepic.eu/pool', 'https://fastepic.eu/api/', "['fastepic.eu:3300']"],
    ['epicmine', 'https://epicmine.org', 'https://epicmine.org/api/',
     "['eu.epicmine.org:3333', 'us.epicmine.org:3333', 'hk.epicmine.org:3333']"]
    ]
