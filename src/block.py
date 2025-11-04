import hashlib
from datetime import datetime  # realiam timestamp
from src.hashing import aes_hashing
from src.merkle import calculate_merkle_root

# Blokas
class Block:
    # konstruktorius
    def __init__(self, block_id, transactions, difficulty=3):
        self.block_id = block_id
        self.prev_block_hash = None
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Laiko antspaudas (reali data/laikas)
        self.nonce = 0
        self.version = 1
        self.difficulty = difficulty
        self.merkle_root = calculate_merkle_root(transactions)

        self.transactions = transactions
        self.hash = None

    # padaro hash is bloko header'io
    def calculate_hash(self):
        header = (
            f"{self.prev_block_hash}"
            f"{self.timestamp}"
            f"{self.version}"
            f"{self.merkle_root}"
            f"{self.nonce}"
            f"{self.difficulty}"
        )
        return aes_hashing(header.encode()).hex()

