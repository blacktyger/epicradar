from django.contrib.auth.models import User
from Crypto.Signature import PKCS1_v1_5
from django.utils.deconstruct import deconstructible
from rest_framework import serializers
from .verification import Verification
from .tools import to_ordered_dict
from multiprocessing import Queue
from .hash_util import hash_block
from django.utils import timezone
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from django.db import models
from simhash import Simhash
from functools import reduce
import Crypto.Random
import jsonfield
import binascii
import uuid


# metrics of mining epic cash fake rig / real data stream


class Mempool:
    for color in colors:
        print('item no: ', cnt, ' ', color)
        queue.put(color)
        cnt += 1

    print('\npopping items from queue:')
    cnt = 0
    while not queue.empty():
        print('item no: ', cnt, ' ', queue.get())
        cnt += 1


class Wallet(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    name = models.CharField(max_length=70, blank=False, default='Default')
    private_key = models.CharField(max_length=2048, blank=False, default='none', editable=False)
    public_key = models.CharField(max_length=1024, blank=False, default='none')
    address = models.CharField(max_length=128, blank=False, default='none')
    pin = models.IntegerField(default=1111)
    balance = models.DecimalField(max_digits=32, decimal_places=8, blank=True, default=0)
    telegram_user = models.CharField(max_length=70, blank=True, null=True)
    creation_time = models.DateTimeField(auto_now=True)
    extra_data = jsonfield.JSONField(default={})

    def save(self, *args, **kwargs):
        if self.private_key and self.public_key == 'none':
            self.private_key, self.public_key = self.create_keys()
            self.address = Simhash(self.public_key).value
        super(Wallet, self).save(*args, **kwargs)

    @classmethod
    def get_new(cls):
        return cls.objects.create().id

    @staticmethod
    def create_keys():
        """Create a new pair of private and public keys."""
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (binascii.hexlify(private_key.exportKey()).decode('ascii'),
                binascii.hexlify(public_key.exportKey()).decode('ascii'))

    @staticmethod
    def verify_transaction(transaction):
        """Verify the signature of a transaction.
        Arguments:
            :transaction: The transaction that should be verified.
        """
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new((str(transaction.sender) + str(transaction.recipient) +
                        str(transaction.amount)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))

    def ordered_dict(self):
        return to_ordered_dict(self)

    def __str__(self):
        return f"{self.owner.username}: {self.address}"


class Transaction(models.Model):
    class Status(models.TextChoices):
        open = '0', "open"
        completed = '1', "completed"
        canceled = '2', "canceled"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    time = models.DateTimeField(auto_now=True)
    block = models.ForeignKey('Block', blank=True, on_delete=models.CASCADE, related_name='block', db_constraint=False)
    amount = models.DecimalField(decimal_places=8, max_digits=32, blank=False, default=0)
    sender = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='sender')
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.open)
    recipient = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='recipient')
    signature = models.CharField(max_length=256, blank=False, default='none')
    extra_data = jsonfield.JSONField(default={})

    def save(self, *args, **kwargs):
        if self.signature == 'none':
            self.signature = self.sign_transaction()
        super(Transaction, self).save(*args, **kwargs)

    @staticmethod
    def get_last_block():
        """ Get last block in the chain, in this case last mined block """
        return Block.objects.order_by('id').last()

    def sign_transaction(self):
        """Sign a transaction and return the signature"""
        signer = PKCS1_v1_5.new(RSA.importKey(
            binascii.unhexlify(self.sender.private_key)))
        h = SHA256.new(f"{self.sender}{self.recipient}{self.amount}".encode('utf8'))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode('ascii')

    def ordered_dict(self):
        return to_ordered_dict(self)

    def __str__(self):
        return f"{self.amount} from {self.sender} -> {self.recipient}"


class Blockchain(models.Model):
    name = models.CharField(max_length=64, blank=False, default='Blockchain instance')
    created = models.DateTimeField(auto_now=True)
    wallet_address = models.CharField(max_length=128, blank=False, default='none')
    extra_data = jsonfield.JSONField(default={})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.wallet_address == 'none':
            self._create_wallet()
            self.wallet_address = Wallet.objects.get(name='blockchain_wallet').address
            self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_block = Block(
            proof=54,
            id=0,
            timestamp=timezone.now(),
            previous_hash='If you reading this, talk via telegram to @blacktyg3r with code "5445", 3 epics reward ;)'
            )

        genesis_transaction = Transaction(
            block=genesis_block,
            sender=self.wallet(),
            recipient=self.wallet(),
            amount=10000,
            )

        genesis_transaction.save()
        genesis_block.save()
        genesis_block.transactions.add(genesis_transaction)

        print(f"GENESIS BLOCK CREATED!\n{genesis_block.ordered_dict()}")

    @staticmethod
    def _create_wallet():
        wallet = Wallet(
            owner=User.objects.first(),
            name='blockchain_wallet',
            pin='5432',
            balance=1000
            )
        wallet.save()
        return wallet

    def wallet(self):
        return Wallet.objects.get(address=self.wallet_address)

    @staticmethod
    def _get_open_transactions():
        return Transaction.objects.filter(status="open")

    def _chain(self):
        return Block.objects.filter()

    def _get_last_block(self):
        if self._chain().count() < 1:
            return None
        return self._chain().last()

    def _proof_of_work(self):
        """Generate a proof of work for the open transactions, the hash of the
        previous block and a random number (which is guessed until it fits)."""
        last_hash = hash_block(self._get_last_block(), Transaction)
        proof = 0
        # Try different PoW numbers and return the first valid one
        while not Verification.valid_proof(
            self._get_open_transactions(),
            last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, wallet):
        """Calculate and return the balance for a wallet"""

        tx_sender = [[tx.amount for tx in block.transactions.all()
                      if tx.sender.address == wallet.address]
                     for block in self._chain()]

        open_tx_sender = [
            tx.amount for tx in self._get_open_transactions()
            if tx.sender == wallet]

        tx_sender.append(open_tx_sender)
        print(tx_sender)

        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
        if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)

        tx_recipient = [
            [tx.amount for tx in block.transactions.all()
             if tx.recipient == wallet]
            for block in self._chain()]

        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
        if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)
        return amount_received - amount_sent

    @staticmethod
    def _update_balance(**params):
        sender = params['sender']
        recipient = params['recipient']
        amount = params['amount']

        sender.balance -= amount
        sender.save()
        recipient.balance += amount
        recipient.save()

    def _add_transaction(self, **params):
        sender = params['sender']
        transaction = Transaction.objects.create(
            sender=sender,
            recipient=params['recipient'],
            amount=params['amount'],
            )

        if Verification.verify_transaction(
            balance=self.get_balance(sender),
            transaction=transaction, sender=sender):
            self._get_last_block().transactions.add(transaction)
            self._update_balance(**params)
            return True
        else:
            return False

    def mine_block(self):
        """Create a new block and add open transactions to it."""
        hashed_block = hash_block(self._get_last_block(), Transaction)
        proof = self._proof_of_work()

        block = Block(
            proof=proof,
            timestamp=timezone.now(),  # CHANGED
            blockchain=Blockchain.objects.last().name,
            previous_hash=hashed_block
            )
        block.save()

        block.transactions.set(self._get_open_transactions())

        proof_is_valid = Verification.valid_proof(
            self._get_open_transactions(), block.previous_hash, block.proof)
        hashes_match = hashed_block == block.previous_hash

        if hashes_match and proof_is_valid:
            for tx in block.transactions.all():
                tx.open = False
                tx.completed = True
                tx.save()

            if self._get_open_transactions().count() != 0:  # CHANGED
                for tx in block.transactions.all():
                    if tx in (self._get_open_transactions()):
                        print('PROBLEM WITH OPENED TRANSACTION:')
                        # print(tx)
                        return False
                print('BLOCK ADDED')
                # print(block)
                return True

        else:
            print(f'PROBLEM WITH [proof_is_valid: {proof_is_valid} | hashes_match: {hashes_match}]')


class Block(models.Model):
    id = models.AutoField(primary_key=True)
    proof = models.CharField(max_length=256, blank=False, default='none')
    timestamp = models.DateTimeField(auto_now=True)
    # blockchain = models.CharField(max_length=256, blank=True, default='none')
    transactions = models.ManyToManyField(Transaction, blank=True, related_name='transactions')
    previous_hash = models.CharField(max_length=256, blank=True, default='none')

    # extra_data = jsonfield.JSONField(default={})

    def ordered_dict(self):
        return to_ordered_dict(self)

    def __str__(self):
        return f"{self.id} | {self.timestamp}"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['sender', 'receiver', 'amount', 'signature']


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'


# ----------------------16.03.2021-----------------------------------------

from django.contrib.auth.models import User
from Crypto.Signature import PKCS1_v1_5
from .verification import Verification
from rest_framework import serializers
from django.utils import timezone
from .hash_util import hash_block
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from django.db import models
from simhash import Simhash
from decimal import Decimal
import Crypto.Random
from .tools import *
import jsonfield
import binascii
import logging
import random
import uuid

# metrics of mining epic cash fake rig / real data stream
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger('')

BLOCKCHAIN_NAME = "TEST"
BLOCK_MAX_SIZE = 300
COINBASE_BALANCE = 1000
BLOCKCHAIN_SUPPLY = 100_000


class Mempool(models.Model):
    """Class for managing transactions before pushing to blockchain"""
    name = models.CharField(max_length=70, blank=False, default='none')
    queue = Queue()
    pending = jsonfield.JSONField(default={'txs': []})
    block_size = models.IntegerField(blank=False, null=True, default=100)

    @staticmethod
    def get_tx_by_id(id):
        return Transaction.objects.get(id=id)

    def add_tx(self, tx):
        self.queue.put(tx)
        self.pending['txs'].append(str(tx.id))
        self.save()
        logger.debug(f"TXS IN QUEUE: {self.queue.qsize()}")

    def add_txs_to_block(self):
        temp_block = []

        for tx in IterableQueue(self.queue):
            logging.debug(f"TX IN QUEUE: [{tx}]")
            if len(temp_block) == self.block_size:
                logger.debug("BLOCK FULL")
                return temp_block

            temp_block.append(tx)

            logging.debug(f"QUEUE THINGY")
            self.queue.get

            if tx in self.pending['txs']:
                self.pending['txs'].remove(str(tx.id))
                self.save()

            logger.debug(f"TXS FROM QUEUE: [{self.queue.qsize()}] | TX IN BLOCK: [{len(temp_block)}]")

            if len(self.pending['txs']) > 0:
                for tx_id in self.pending['txs']:
                    logger.debug(f"TXS FROM PENDING: [{len(self.pending['txs'])}] | TX IN BLOCK: [{len(temp_block)}]")
                    tx = Transaction.objects.get(id=tx_id)
                    temp_block.append(tx)
                    self.pending['txs'].remove(str(tx.id))
                    self.save()

        return temp_block

    def __str__(self):
        return f"MEMPOOL: {self.name}"


class Wallet(models.Model):
    """Class to manage blockchain funds"""
    pin = models.IntegerField(default=1111)
    name = models.CharField(max_length=70, blank=False, default='Default')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    locked = models.DecimalField(max_digits=32, decimal_places=8, blank=True, default=0)
    balance = models.DecimalField(max_digits=32, decimal_places=8, blank=True, default=0)
    address = models.CharField(max_length=128, blank=False, default='none')
    blockchain = models.ForeignKey('Blockchain', on_delete=models.CASCADE, blank=True,
                                   null=True, related_name="%(class)s_blockchain")
    public_key = models.CharField(max_length=1024, blank=False, default='none')
    private_key = models.CharField(max_length=2048, blank=False, default='none', editable=False)
    creation_time = models.DateTimeField(auto_now=True)
    telegram_user = models.CharField(max_length=70, blank=True, null=True)
    extra_data = jsonfield.JSONField(default={})

    def save(self, *args, **kwargs):
        """Override save method when new instance, generate keys and address """
        if self.private_key and self.public_key == 'none':
            self.private_key, self.public_key = self.create_keys()
            self.address = Simhash(self.public_key).value
        super(Wallet, self).save(*args, **kwargs)

    @staticmethod
    def create_keys():
        """Create a new pair of private and public keys."""
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (binascii.hexlify(private_key.exportKey()).decode('ascii'),
                binascii.hexlify(public_key.exportKey()).decode('ascii'))

    @staticmethod
    def verify_key(tx):
        """Verify the signature of a transaction."""
        public_key = RSA.importKey(binascii.unhexlify(tx.sender.public_key))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new(f"{tx.sender}{tx.recipient}{tx.amount}".encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(tx.signature))

    def sign_transaction(self, tx):
        """Sign a transaction and return the signature"""
        signer = PKCS1_v1_5.new(RSA.importKey(
            binascii.unhexlify(self.private_key)))
        h = SHA256.new(f"{self}{tx.recipient}{tx.amount}".encode('utf8'))
        signature = signer.sign(h)
        return binascii.hexlify(signature)

    @classmethod
    def get(cls, index):
        return cls.objects.get(id=index)

    @classmethod
    def get_all(cls):
        return [logging.debug(x, f"[{x.balance}]") for x in cls.objects.all()]

    def send(self, recipient, amount):
        """
        Create new transaction object, verify balances and signatures,
        update sender balance, push tx to mempool.
        """

        amount = Decimal(amount)
        if Verification.verify_balance(sender=self, amount=amount):
            new_tx = Transaction.objects.create(
                sender=self,
                recipient=recipient,
                amount=amount
                )

            if Verification.verify_transaction(tx=new_tx):
                self.locked += amount
                self.balance -= amount
                self.save()
                logging.debug(f"BALANCE: {self.balance} [{self.locked} LOCKED]")
                new_tx.status = 'mempool'
                new_tx.save()
                self.blockchain.mempool.add_tx(new_tx)
                return new_tx

            else:
                logging.debug(f"TX NOT ADDED TO MEMPOOL \n {new_tx}"
                              f"SIGNATURE NOT CORRECT")
                logging.debug(f"BALANCE: {self.balance} [{self.locked} LOCKED]")
                new_tx.status = 'canceled'
                new_tx.save()
                return False
        else:
            logging.debug(f"NOT ENOUGH BALANCE TO SEND: [{amount}]")
            logging.debug(f"BALANCE: {self.balance} [{self.locked} LOCKED]")
            return False

    def cancel_tx(self, tx):
        if tx.sender == self.owner:
            if not tx.block and tx.status in ['pending', 'mempool']:
                tx.sender.locked -= tx.amount
                tx.sender.save()
                tx.status = 'canceled'
                tx.save()
                logging.debug(f"TRANSACTION CANCELED: [{tx}]")
                return True
        return False

    def ordered_dict(self):
        """Return model instance as OrderedDict object (for hashing)"""
        return to_ordered_dict(self)

    def __str__(self):
        return f"{self.owner.username}: {self.address}"


class Transaction(models.Model):
    class Status(models.TextChoices):
        genesis = 'genesis', "genesis"
        pending = 'pending', "pending"
        mempool = 'mempool', 'mempool'
        canceled = 'canceled', 'canceled'
        completed = 'completed', "completed"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    time = models.DateTimeField(auto_now=True)
    block = models.ForeignKey('Block', on_delete=models.CASCADE, blank=True,
                              null=True, related_name='block')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.pending)
    amount = models.DecimalField(decimal_places=8, max_digits=32, default=0)
    sender = models.ForeignKey(Wallet, on_delete=models.CASCADE, blank=True,
                               null=True, related_name='sender')
    recipient = models.ForeignKey(Wallet, on_delete=models.CASCADE, blank=True,
                                  null=True, related_name='recipient')
    signature = models.CharField(max_length=256, blank=False, default='none')
    extra_data = jsonfield.JSONField(default={}, blank=True)

    class Meta:
        ordering = ['-time']

    def save(self, *args, **kwargs):
        if self.signature == 'none':
            self.signature = self.sender.sign_transaction(self)
        super(Transaction, self).save(*args, **kwargs)

    def ordered_dict(self):
        return to_ordered_dict(self)

    def hashable_info(self):
        return OrderedDict({
            'sender': self.sender.address,
            'recipient': self.recipient.address,
            'amount': self.amount}
            )

    def repr(self):
        data = {'sender': self.sender, 'time': self.time,
                'recipient': self.recipient,
                'amount': self.amount.normalize()}
        return data

    def __str__(self):
        return f"[{self.block}] {self.amount} from {self.sender} -> {self.recipient}"


class Block(models.Model):
    id = models.IntegerField(primary_key=True)
    proof = models.CharField(max_length=256, blank=False, default='none')
    timestamp = models.DateTimeField(auto_now=True)
    blockchain = models.ForeignKey('Blockchain', on_delete=models.CASCADE, blank=True,
                                   null=True, related_name="%(class)s_blockchain")
    previous_hash = models.CharField(max_length=256, blank=True, default='none')
    extra_data = jsonfield.JSONField(default={})

    def ordered_dict(self):
        return to_ordered_dict(self)

    def hashable_info(self):
        return OrderedDict({
            'proof': self.proof,
            'previous_hash': self.previous_hash})

    def transactions(self):
        return Transaction.objects.filter(block=self)

    def __str__(self):
        return f"{self.id}"


class Blockchain(models.Model):
    """
    Model class to manage whole blockchain,
    """
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=256, blank=False, default=BLOCKCHAIN_NAME)
    node = models.OneToOneField(User, on_delete=models.CASCADE, blank=True,
                                null=True, related_name='node')
    mempool = models.OneToOneField(Mempool, on_delete=models.CASCADE, blank=True,
                                   null=True, related_name="mempool")
    timestamp = models.DateTimeField(auto_now=True)
    total_supply = models.IntegerField(default=BLOCKCHAIN_SUPPLY)
    extra_data = jsonfield.JSONField(default={})

    @staticmethod
    def get_txs(status):
        if status == 'all':
            return Transaction.objects.all()
        else:
            return Transaction.objects.filter(status=status)

    @staticmethod
    def set(model, param, value):
        setattr(model, param, value)
        model.save()

    def chain(self):
        return Block.objects.filter(blockchain=self)

    def get_block(self, index):
        if index == "last":
            return self.chain().order_by('id').last()
        else:
            return self.chain()[index]

    def coinbase(self):
        return Wallet.objects.filter(blockchain=self)[0]

    def _proof_of_work(self):
        """Generate a proof of work for the pending transactions, the hash of the
        previous block and a random number (which is guessed until it fits)."""

        last_block_hash = hash_block(self.get_block('last'))
        proof = 0
        print(self.get_txs(status='mempool').filter(block=None))
        while not Verification.valid_proof(
            transactions=self.get_txs(status='mempool').filter(block=None),
            previous_hash=last_block_hash, proof=proof):
            proof += 1
        return proof

    @staticmethod
    def get_balance(wallet):
        """Calculate and return the balance for a wallet"""

        spend = sum([tx.amount for tx in Transaction.objects.filter(status='completed') if tx.sender == wallet])
        logging.debug(f"SPEND SUM: {spend}")

        received = sum([tx.amount for tx in Transaction.objects.filter(status='completed') if tx.recipient == wallet])
        logging.debug(f"RECEIVED SUM: {received}")

        return Decimal(received - spend)

    def _create_block(self):
        """Create a new empty block instance"""
        hashed_last_block = hash_block(self.get_block('last'))
        print(f"LAST BLOCK [{self.get_block('last').id}] HASH: {hashed_last_block}")

        proof = self._proof_of_work()
        id = self.get_block('last').id + 1
        print(f"NEW BLOCK ID [{id}]")

        new_block = Block.objects.create(
            id=id,
            proof=proof,
            timestamp=timezone.now(),
            blockchain=self,
            previous_hash=hashed_last_block
            )
        return new_block

    def mine_block(self):
        # Create new empty block
        new_block = self._create_block()
        logging.debug('NEW BLOCK CREATED')

        # Get pending transactions from mempool up to max block size
        pending = self.mempool.add_txs_to_block()
        logging.debug(f"PENDING TXS: [{len(pending)}]")

        for tx in pending:
            self.set(tx, 'block', new_block)
        logging.debug(new_block.transactions())

        print(self.get_txs(status='mempool').filter(block=new_block))

        # Validate PoW proofs and block hashes
        if Verification.valid_proof(
            transactions=self.get_txs(status='mempool').filter(block=new_block),
            previous_hash=new_block.previous_hash, proof=new_block.proof):

            # Add transactions to block, update status and participants balances
            for tx in new_block.transactions():
                self.set(tx, 'status', 'completed')
                tx.sender.locked -= tx.amount
                tx.sender.save()
                tx.recipient.balance += tx.amount
                tx.recipient.save()
                tx.save()
                logging.debug(f"------------------------------------------------")

            logging.debug('BLOCK ADDED')
            return True
        else:
            logging.debug(f"VERIFICATION FAILED, BLOCK NOT ADDED")
            logging.debug(f"TRANSACTIONS GOING BACK TO MEMPOOL")

            # Update transactions status and send them back to mempool
            for tx in pending:
                self.set(tx, 'status', 'mempool')
                self.set(tx, 'block', None)
                self.mempool.add_tx(tx)
            self.mempool.save()
            return False

    def __str__(self):
        return f"BLOCKCHAIN: {self.name} HEIGHT: {self.chain().count()}"


# TESTING STUFF

# bc = Blockchain()


def test():
    names = "Open and transparent Epic-Cash wallet for funding micro initiatives, events and ideas. " \
            "Project where everyone can contribute and show love to active community members - " \
            "faucets, tips or aidrops - it's just the beginning!".split(" ")
    for x in range(10):
        user = User.objects.get_or_create(username=f'{random.choice(names)}_user')[0]
        wallet = Wallet.objects.get_or_create(owner=user)[0]
        bc.coinbase.send(wallet, random.randint(0, 50))

    logging.debug(f"MINING BLOCK ----------------------")
    bc.mine_block()


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['sender', 'receiver', 'amount', 'signature']


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'
