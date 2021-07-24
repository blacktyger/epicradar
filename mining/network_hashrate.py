from datetime import datetime
import pandas as pd
import requests
import json
import time


class NetworkCalculator:
    """
    Get data from epicradar.tech/node or explorer.epic.tech as backup
    to calculate current difficulty on each algo within Epic network.
    """
    def __init__(self, node_url):
        self.explorer_url = "https://explorer.epic.tech/api?q="
        self.diff_file = 'network_difficulty.csv'
        self.hash_file = 'network_hashrate.csv'
        self.node_url = node_url
        self.block_target_time = 60
        self.network_hashrate = {}
        self.last_total_diffs = {}
        self.prev_total_diffs = {}
        self.current_diffs = {}
        self.height = None

    def get_node_data(self):
        data = json.loads(requests.get(self.node_url).content)
        d = data['tip']['total_difficulty']
        diffs = {
            'randomx': d['randomx'],
            'progpow': d['progpow'],
            'cuckatoo': d['cuckatoo']
            }
        node = {'height': data['tip']['height'], 'diffs': diffs}
        return node

    def get_explorer_data(self):
        q_list = {'randomx': 'getdifficulty-randomx',
                  'progpow': 'getdifficulty-progpow',
                  'cuckatoo': 'getdifficulty-cuckoo'}
        explorer = {'height': json.loads(requests.get(f"{self.explorer_url}getblockcount").content),
                    'diffs': {}}

        for algo, query in q_list.items():
            url = f"{self.explorer_url}{query}"
            explorer['diffs'][algo] = json.loads(requests.get(url).content)
        return explorer

    def calculate_current_network_diff(self):
        """
        current_diff = last_block_total_diff - previous_block_total_diff
        """
        new = self.last_total_diffs
        old = self.prev_total_diffs
        diff = {algo: int(new['diffs'][algo] - old['diffs'][algo]) for algo in new['diffs']}
        diff['height'] = self.height
        diff['timestamp'] = int(datetime.timestamp(datetime.now()))
        return diff

    def calculate_current_network_hashrate(self):
        """
        net_hashrate = current_diff / block_target_time
        """
        net_hashrate = {algo: int(self.current_diffs[algo] / self.block_target_time)
                        for algo in self.current_diffs}
        net_hashrate['height'] = self.height
        net_hashrate['timestamp'] = int(datetime.timestamp(datetime.now()))
        return net_hashrate

    def save_to_csv(self):
        df_hash = pd.DataFrame([self.network_hashrate])
        df_diff = pd.DataFrame([self.current_diffs])

        with open(self.hash_file, 'a') as f:
            df_hash.to_csv(f, header=f.tell() == 0, line_terminator='\n')
        with open(self.diff_file, 'a') as f:
            df_diff.to_csv(f, header=f.tell() == 0, line_terminator='\n')

    def update(self):
        """
        Start listening for new blocks, calculate
        network difficulty and hashrate for each algo
        and save to CSV files. Local node is a main
        source, explorer.epic.tech API is a backup
        """
        while True:
            try:
                data = self.get_node_data()
            except:
                data = self.get_explorer_data()

            # If not previous data is present, save current values (normal)
            if not self.height or not self.last_total_diffs:
                self.last_total_diffs = data
                self.prev_total_diffs = data
                self.height = data['height']
                print(f"No stored data in script, saving from source")
                print(self.last_total_diffs)

            # If script height is same as network height (normal)
            if self.height == data['height']:
                # print(f"No new blocks, height: {self.height}")
                time.sleep(3)

            # If script height is higher than network height (error)
            elif self.height > data['height']:
                self.last_total_diffs = data
                self.prev_total_diffs = data
                print(f"Stored height ({self.height}) is greater than network ({data['height']}), restart")

            # If script height is lower than network height by 1 block (normal)
            if self.height == data['height'] - 1:
                self.height = data['height']
                self.prev_total_diffs = self.last_total_diffs
                self.last_total_diffs = data
                # try:
                self.current_diffs = self.calculate_current_network_diff()
                self.network_hashrate = self.calculate_current_network_hashrate()
                self.save_to_csv()
                print(f"{self.height} saved to db!")
                # except:
                #     print(f"{self.height} errors, NOT saved to db!")
                #     continue

                print(f"---- DIFFICULTY ----")
                print(self.current_diffs)
                print(f"---- HASHRATE ----")
                print(self.network_hashrate)

            # If script height is lower than network more than 1 (problem)
            elif self.height < data['height'] - 1:
                # self.last_total_diffs = data
                self.prev_total_diffs = data
                self.height = data['height']
                print(f"Stored height is way behind network - restart at height: {self.height}")

#
# x = NetworkCalculator(node_url="https://epicradar.tech/node/v1/status")
#
# x.update()
