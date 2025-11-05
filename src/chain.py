import random
from src.block import Block

# Blockchain
class Blockchain:
    # konstruktorius
    def __init__(self, difficulty=3):
        self.chain = []
        self.difficulty = difficulty

    # grazina paskutinio bloko hash'a
    def get_last_hash(self):
        if not self.chain:
            # AES-hash yra 16 baitų -> 32 heks simboliai
            return "0" * 32
        return self.chain[-1].hash

    # prideda bloka i grandine
    def add_block(self, block):
        self.chain.append(block)

    # paieška pagal block_id (arba eilės nr.)
    def find_block_by_id(self, block_id: int):
        for b in self.chain:
            if b.block_id == block_id:
                return b
        return None

    # paieška transakcijos pagal txid (hex)
    def find_tx_by_id(self, txid: str):
        for b in self.chain:
            for tx in b.transactions:
                if tx.transaction_id == txid:
                    return tx
        return None

    def __repr__(self):
        return f"Blockchain(len={len(self.chain)})"

# funkcija, sukurianti nauja bloka (parenka 100 tx)
def create_new_block(transactions, block_id, prev_block_hash, block_size=100, difficulty=3):
    selected_transactions = random.sample(transactions, min(block_size, len(transactions)))
    new_block = Block(block_id, selected_transactions, difficulty=difficulty)
    new_block.prev_block_hash = prev_block_hash
    return new_block, selected_transactions
