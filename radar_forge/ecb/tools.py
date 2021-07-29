import queue
from collections import OrderedDict
from itertools import chain
from queue import Queue


class IterableQueue:
    def __init__(self, source_queue):
        self.source_queue = source_queue

    def __iter__(self):
        while True:
            try:
                yield self.source_queue.get_nowait()
            except queue.Empty:
                return


def to_ordered_dict(instance):
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        data[f.name] = f.value_from_object(instance)
    for f in opts.many_to_many:
        data[f.name] = [i.id for i in f.value_from_object(instance)]
    return OrderedDict(data)
