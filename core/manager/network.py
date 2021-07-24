from .stellar import StellarNetworkManager
from app.templatetags.math import get_ts
from datetime import datetime
from core.timer import Timer
from django.apps import apps
from decimal import Decimal
import hashlib
import time


def get_model_from_str(model, app='swapic'):
    return apps.get_model(app, model)


class TransactionManager:
    def __init__(self):
        self.stellar = StellarNetworkManager()

    def create_new_proforma(self, timestamp, epic_amount, xlm_amount,
                            receive_address, receive_method):
        """Create local transaction based on user input"""
        timestamp = get_ts(timestamp)

        if receive_method == "wallet":
            receive_address = receive_address
        if receive_method == "keybase":
            receive_address = f"keybaseid_{receive_address}"

        local_hash = hashlib.md5(f"{receive_address}{timestamp}"
                                 .encode('utf-8')).hexdigest()

        data = {
            'send_address': self.stellar.wallet['keys']['public'],
            'receive_address': receive_address,
            'destination_amount': epic_amount,
            'receive_method': receive_method,
            'destination_min': epic_amount,
            'memo': receive_address,
            'timestamp': timestamp,
            'amount': xlm_amount,
            'local_hash': local_hash,
            }
        return data

    @Timer("download_network_tx_history")
    def download_user_tx_history(self):
        """Download blockchain snapshot of transactions from Users to Swapic address"""

        transactions = self.stellar.server.transactions() \
            .for_account(account_id=self.stellar.wallet['keys']['public']) \
            .order(desc=True).limit(100).call()

        return [tx for tx in transactions['_embedded']['records']]

    @staticmethod
    def tx_timeout(tx):
        now = datetime.now()
        # Time string from server "2021-01-29T20:04:19Z"
        ts = datetime.strptime(tx.data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        delta = now - ts
        print(f"INFO: Time delta {delta}")

        if delta.seconds > 120 * 60:
            tx.status = "Archived"
            tx.save()
            print(f'INFO: Transaction {tx} is older than 120 minutes, status "{tx.status}"')

    def save_all_users_txs_to_db(self):
        user_tx = get_model_from_str('UserTransaction')
        """Append all transactions from User to Swapic account in to local database"""
        net_data = self.download_user_tx_history()

        for tx in net_data:
            obj, created = user_tx.objects.get_or_create(data=tx)
            if created:
                self.tx_timeout(obj)
                print(f"SAVED SwapicTransaction: {tx}")

    # @staticmethod
    # def save_user_tx_to_db(tx):
    #     user_tx = get_model_from_str('UserTransaction')
    #
    #     """Append transaction in to local database"""
    #     obj, created = user_tx.objects.get_or_create(data=tx)
    #     if created:
    #         print(f"SAVED SwapicTransaction: {tx}")
    #     else:
    #         print(f"FAILED to save SwapicTransaction: {tx}")

    def extract_transaction(self, tx):
        data = self.stellar.server.payments(). \
            for_transaction(transaction_hash=tx['hash']).call()
        return data

    def new_transactions_from_users(self):
        user_tx = get_model_from_str('UserTransaction')
        print(f"INFO: Listening for new transactions...")
        new_tx = [user_tx.objects.get_or_create(data=tx)[0]
                  for tx in self.download_user_tx_history()
                  if user_tx.objects.get_or_create(data=tx)[1]]
        print(f"INFO: New transactions {new_tx}:")
        return new_tx

    # TODO: Logic for transaction pool for hang transactions

    def run_listener(self, transaction):
        max_try = 10
        new_txs = []

        while max_try and not new_txs:
            time.sleep(5)
            max_try = max_try - 1
            print(f"INFO: Refresh network transactions || TRY LEFT: {max_try}...")
            new_txs = self.new_transactions_from_users()

        if new_txs:
            print(f"INFO: {len(new_txs)} new transactions")
            for i, tx in enumerate(new_txs):
                print(f"PROCESSING: Transaction [{i}] {tx.data['created_at']}")
                if self.validate_user_tx(local=transaction.proforma, network=tx.data):
                    return tx
                else:
                    if not self.tx_timeout(tx):
                        tx.status = "INVALID"
                        tx.save()
                        print(f"FAILED: Transaction [{i}] {tx.data['created_at']} status '{tx.status}'")
                    continue
        else:
            return False
        return False

    def validate_user_tx(self, network, local):
        """
        > USER TRANSACTION VALIDATION
            >> Compare local_hash from local and network transaction
            >> If local_hash is matching return True
            >> If XLM amount is different no more than 1% return True
            >> If local_hash and XLM amount do not match send XLM back to user address
        """
        print(f"confirmed_in_network START")

        n = self.extract_transaction(network)['_embedded']['records'][0]

        def is_amount_valid():
            print(f"is_amount_valid start")
            print(f"Network amount: {n['amount']} | Local amount: {local['amount']}")

            if Decimal(local['amount']) == Decimal(n['amount']):
                print(f"SUCCESS: Price match")
                return True
            else:
                v1 = Decimal(local['amount'])
                v2 = Decimal(n['amount'])
                try:
                    percentage = round(abs(v1 - v2) / max(v1, v2) * 100, 3)
                except ZeroDivisionError:
                    percentage = float('inf')

                print(f"PRICE DIFFERENCE: {percentage}%")
                if percentage < 1.1:
                    print(f"SUCCESS: Price match ({percentage}%)")
                    return True
                else:
                    print(f"FAILED: Price don't match")
                    # self.return_user_asset()
                    return False

        network_local_hash = hashlib.md5(
            f"{network['memo']}{local['timestamp']}".encode('utf-8')).hexdigest()

        if local['local_hash'] == network_local_hash:
            print(f"SUCCESS: local and network local_hash match")
            return is_amount_valid()
        else:
            # self.return_user_asset()
            print(f"FAILED: local and network local_hash don't match.")

