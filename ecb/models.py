from django.contrib.auth.models import User
from Crypto.Signature import PKCS1_v1_5
from .hash_util import hash_string_256
from rest_framework import serializers
from django.utils import timezone
from .hash_util import hash_block
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from django.db.models import Q
from core.timer import Timer
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


class Wallet(models.Model):
    """Class to manage blockchain funds"""
    pin = models.IntegerField(default=1111)
    name = models.CharField(max_length=70, blank=False, default='Default')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    locked = models.DecimalField(max_digits=32, decimal_places=8, blank=True, default=0)
    pending = models.DecimalField(max_digits=32, decimal_places=8, blank=True, default=0)
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

    def sign_transaction(self, tx):
        """Sign a transaction and return the signature"""
        signer = PKCS1_v1_5.new(RSA.importKey(
            binascii.unhexlify(self.private_key)))
        h = SHA256.new(f"{self}{tx.recipient}{tx.amount}".encode('utf8'))
        signature = signer.sign(h)
        return binascii.hexlify(signature)

    @staticmethod
    def verify_key(tx):
        """Verify the signature of a transaction."""
        public_key = RSA.importKey(binascii.unhexlify(tx.sender.public_key))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new(f"{tx.sender}{tx.recipient}{tx.amount}".encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(tx.signature))

    @staticmethod
    def db_balance_vs_chain_balance(wallet):
        """Check wallet balance on both local database and chain history, return matching bool"""

        # Do not check balances on COINBASE wallet
        if wallet == Wallet.objects.first():
            return True

        # Sum all transaction amounts where wallet was a sender
        spend = sum([tx.amount for tx in Transaction.objects.filter(
            status='completed') if tx.sender == wallet])
        logging.debug(f"SPEND SUM: {spend}")

        # Sum all transaction amounts where wallet was a receiver
        received = sum([tx.amount for tx in Transaction.objects.filter(
            status='completed') if tx.recipient == wallet])
        logging.debug(f"RECEIVED SUM: {received}")

        # Save chain wallet balance (difference between sent and received coins)
        chain_balance = Decimal(received - spend)

        # Validate whether local database balance is same as blockchain and return bool
        if (wallet.balance + wallet.locked - wallet.pending) == chain_balance:
            logging.debug(f"DB BALANCE VS CHAIN BALANCE: MATCH")
            return True
        else:
            logging.debug(f"DB BALANCE:{wallet.balance + wallet.locked - wallet.pending}")
            logging.debug(f"CHAIN BALANCE:{chain_balance}")
            return False

    @classmethod
    def get(cls, index):
        return cls.objects.get(id=index)

    @classmethod
    def get_all(cls):
        return [logging.debug(x, f"[{x.balance}]") for x in cls.objects.all()]

    def transactions(self):
        return Transaction.objects.filter(Q(sender=self) | Q(recipient=self)).order_by('-time')

    def send(self, recipient, amount):
        """
        Create new transaction object, verify balances and signatures,
        update sender balance, push tx to mempool.
        """
        amount = Decimal(amount)

        # Compare balance from blockchain and local database
        if self.db_balance_vs_chain_balance(self):

            # Create new transaction object
            new_tx = Transaction.objects.create(
                sender=self,
                recipient=recipient,
                amount=amount
                )

            # Verify transaction signature before sending and return bool
            if self.verify_key(tx=new_tx):

                # Update participants balances
                self.locked += amount
                self.balance -= amount

                # Extra check if sender balance after transaction is not less than 0
                if self.balance < 0:
                    logging.debug(f"SENDER BALANCE: {self.balance} - FAILED")
                    return False

                self.save()
                recipient.pending += amount
                recipient.save()
                logging.debug(f"SENDER BALANCE: {self.balance} [{self.locked} LOCKED]")
                logging.debug(f"RECIPIENT BALANCE: {recipient.balance} [{recipient.pending} PENDING]")
                new_tx.status = 'mempool'
                new_tx.save()
                return new_tx
            else:
                logging.debug(f"TX NOT ADDED TO MEMPOOL \n {new_tx}"
                              f"SIGNATURE NOT CORRECT")
                logging.debug(f"BALANCE: {self.balance} [{self.locked} LOCKED]")
                new_tx.status = 'canceled'
                new_tx.save()
        else:
            logging.debug(f"NOT ENOUGH BALANCE TO SEND: [{amount}]")
            logging.debug(f"BALANCE: {self.balance} [{self.locked} LOCKED]")
            return False

    @staticmethod
    def cancel_tx(tx):
        """ Cancel transactions not added to block - status 'pending' or 'mempool'"""

        if not tx.block and tx.status in ['pending', 'mempool']:
            tx.sender.locked -= tx.amount
            tx.sender.save()
            tx.recipient.pending -= tx.amount
            tx.recipient.save()
            tx.status = 'canceled'
            tx.save()
            logging.debug(f"TRANSACTION CANCELED: [{tx}]")
            return True

        logging.debug(f"CAN'T CANCEL: [{tx}]")
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
        ordering = ['time']

    def save(self, *args, **kwargs):

        # When saved to db for first time, create signature
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
    timestamp = models.DateTimeField(auto_now=True)
    block_size = models.IntegerField(default=BLOCK_MAX_SIZE)
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
        """Initial wallet instance with total supply of blockchain"""
        return Wallet.objects.filter(blockchain=self)[0]

    @staticmethod
    def valid_proof(block, proof):
        guess = f"{[tx.hashable_info() for tx in block.transactions()]}{block.previous_hash}{proof}".encode()
        guess_hash = hash_string_256(guess)
        return guess_hash[0:2] == '00'

    @Timer(name='proof_of_work')
    def _proof_of_work(self, block):
        """Proof is a number of attempts to find number with leading x zeros
           based on hashed block object, it's random factor"""

        # Return random number (actual computing aka mining is needed), based on block values
        logging.debug(f"PROOF OF WORK START")
        proof = 0
        while not self.valid_proof(block, proof=proof):
            proof += 1
        return proof

    def _create_block(self):
        # Prepare pending transactions for new block, append only up to block_size value
        pending = self.get_txs(status='mempool').filter(block=None)
        if pending.count() > self.block_size:
            pending = pending[:self.block_size]

        # Validate PoW proofs of last block (except genesis)
        last_block = self.get_block('last')
        if last_block.id == 0:
            valid = True
        else:
            valid = self.valid_proof(last_block, proof=last_block.proof)

        if valid:
            # Make sure that id (height) of new_block is last_block_id + 1
            id = self.get_block('last').id + 1
            logging.debug(f"NEW BLOCK ID [{id}]")

            # Create new_block object in Block model
            new_block = Block.objects.create(
                id=id,
                timestamp=timezone.now(),
                blockchain=self,
                previous_hash=hash_block(last_block)
                )

            # Append pending transactions to new_block
            for tx in pending:
                self.set(tx, 'block', new_block)
            return True

        else:
            logging.debug(f"LAST BLOCK VALIDATION FAILED")
            return False

    def mine_block(self):
        # Create new_block
        if self._create_block():
            new_block = self.get_block('last')
            logging.debug(f'NEW BLOCK CREATED | TXS: {len(new_block.transactions())}')

            # Solve 'mining' puzzle and save proof to new_block
            new_block.proof = self._proof_of_work(new_block)
            new_block.save()

            # Update transactions status and participants balances
            for tx in new_block.transactions():
                self.set(tx, 'status', 'completed')
                tx.sender.locked -= tx.amount
                tx.sender.save()
                tx.recipient.balance += tx.amount
                tx.recipient.pending -= tx.amount
                tx.recipient.save()
                tx.save()

            logging.debug(f'BLOCK [{new_block.id}] ADDED TO BLOCKCHAIN')
            return True

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
