import os
import pickle

FILE = 'blockchain.pickle'


def read_blockchain(instance):
    if not os.path.exists(FILE):
        bc = instance()
        with open(FILE, 'wb') as file:
            pickle.dump(bc, file, protocol=pickle.HIGHEST_PROTOCOL)

    with open(FILE, 'rb') as handle:
        bc = pickle.load(handle)
        print(bc)