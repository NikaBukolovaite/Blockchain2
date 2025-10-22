import random
from block import Block

# Blockchain
class Blockchain:
    # konstruktorius
    def __init__(self, difficulty=3):
        self.chain = []
        self.difficulty = difficulty

    # grazina paskutinio bloko hash'a
    def get_last_hash(self):
        if not self.chain:
            return "0" * 64
        return self.chain[-1].hash

    # prideda bloka i grandine
    def add_block(self, block):
        self.chain.append(block)

    def __repr__(self):
        return f"Blockchain(len={len(self.chain)})"

# funkcija, sukurianti nauja bloka (parenka 100 tx)
def create_new_block(transactions, block_id, prev_block_hash, block_size=100, difficulty=3):
    selected_transactions = random.sample(transactions, min(block_size, len(transactions)))
    new_block = Block(block_id, selected_transactions, difficulty=difficulty)
    new_block.prev_block_hash = prev_block_hash
    return new_block, selected_transactions
