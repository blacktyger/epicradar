from django.utils import timezone
from django.db import models
from core.db import DataBase
import jsonfield
import uuid

from core.manager.network import TransactionManager
from core.manager.stellar import StellarNetworkManager


"""
Django Models:
    - Swapic: 
        > main class to manage whole swap process
    
    - NetworkTransaction: 
        > model to store each swapic transaction in Stellar network
    
    - LocalTransaction
        > model to store each local user transaction
"""


class Transaction(models.Model):
    """Container model for all steps (transactions) needed to process SWAPIC

    Transaction types
        > Proforma: this is only record in local database,
          collects user inputs and.

        > UserTransaction: transaction from Stellar network
          sent by user to Swapic Stellar wallet, values are checked
          against Proforma instance to confirm data.
          It is middleman between User and EPIC-XLM gateway.

        > SwapicTransaction: last transaction in process,
          based on values from UserTransaction new transaction
          is build and send to EPIC-XLM gateway on Stellar network.

    Transactions statuses:
        > "Created", "Pending", "Canceled", "Accepted", "Archived"
    """

    timestamp = models.DateTimeField(default=timezone.now)
    proforma = jsonfield.JSONField()
    status = models.CharField(max_length=20, default="Created")
    data = jsonfield.JSONField()
    id = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Transaction: {self.id} {self.timestamp}"


class UserTransaction(models.Model):
    id = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, default="Saved")
    timestamp = models.DateTimeField(default=timezone.now)
    data = jsonfield.JSONField()

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"User Tx: {self.id}"


class SwapicTransaction(models.Model):
    id = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    data = jsonfield.JSONField()

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"User Tx: {self.id}"


class Swapic:
    model = Transaction

    def __init__(self):
        self.stellar = StellarNetworkManager()
        self.manager = TransactionManager()

    def create_proforma(self, timestamp, epic_amount, xlm_amount,
                        receive_address, receive_method):
        tx = self.manager.create_new_proforma(
            timestamp, epic_amount, xlm_amount, receive_address, receive_method)

        instance, created = self.model.objects.\
            get_or_create(proforma=tx, status="Building")
        print(instance)
        if created:
            instance.status = "Pending"
            instance.save()
            print(f"SUCCESS: Transaction: {instance.id} status '{instance.status}'")
            return instance
        else:
            print(f"FAILED: Transaction: {instance.id} already exists or something else :D.")
            return False

    def transaction_accepted(self, transaction):
        matching_tx = self.manager.run_listener(transaction)

        if matching_tx:
            matching_tx.transaction = transaction
            matching_tx.save()
            transaction.status = "Accepted"
            transaction.save()
            print(f"SUCCESS: Transaction {transaction.id} status '{transaction.status}'")
            return True
        else:
            transaction.status = "Canceled"
            transaction.save()
            print(f"FAILED: Transaction {transaction.id} status '{transaction.status}'")
            return False

    def create_swapic_tx(self, kwargs):
        return self.stellar.build_transaction(kwargs)

    # TODO: ERROR WITH BAD SEQ - MAY BE ACCOUNT STUFF

    def send_swapic_tx(self, transaction, tx_build):
        tx_build.sign(self.stellar.wallet['keys']['pair'])
        response = self.stellar.server.submit_transaction(tx_build)
        print(tx_build.to_xdr())
        print(f'RESPONSE: {response}')
        swapic_tx = SwapicTransaction.objects.create(
            data=tx_build.to_xdr(), transaction=transaction)
        transaction.status = "Done"
        transaction.save()
        print(f'SUCCESS: Transaction {transaction.id} with network hash: {tx_build.hash_hex()} sent.')
        return response