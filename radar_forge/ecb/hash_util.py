import hashlib as hl
import json
from collections import OrderedDict
from django.core.serializers.json import DjangoJSONEncoder
import time

__all__ = ['hash_string_256', 'hash_block']


def hash_string_256(string):
    return hl.sha256(string).hexdigest()


def hash_block(block):
    hashable_block = block.hashable_info()
    hashable_txs = [tx.hashable_info() for tx in block.transactions()]
    data = f"{hashable_txs}{hashable_block}"
    return hash_string_256(json.dumps(data, sort_keys=True).encode())
