from datetime import datetime
from time import sleep, time

from django_extensions.management.jobs import MinutelyJob
from mining.network_hashrate import NetworkCalculator
from multiprocessing import Process
import sys
from core.db import DataBase


class Job(MinutelyJob):
    help = "UPDATE DB."

    def execute(self):
        sleep_time = 300
        p1 = Process(target=NetworkCalculator(node_url="https://epicradar.tech/node/v1/status").update)
        p1.start()

        while True:
            try: DataBase().update()
            except Exception as e: print(e)
            print(f'⌛️Waiting {sleep_time} seconds')
            sleep(sleep_time)
            print(f'⚙️Updating Database start at {datetime.now().strftime("%H:%M:%S")}')

