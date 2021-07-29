from mining.network_hashrate import NetworkCalculator

x = NetworkCalculator(node_url="https://epicradar.tech/node/v1/status")

if __name__ == '__main__':
    x.update()