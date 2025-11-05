from src.hashing import aes_hashing

# funkcija Merkle Root Hash apskaiciavimui

def calculate_merkle_root(transactions):
    tx_hashes = [tx.transaction_id for tx in transactions]
    if not tx_hashes:
        return None
    while len(tx_hashes) > 1:
        if len(tx_hashes) % 2 != 0:
            tx_hashes.append(tx_hashes[-1])
        new_level = []
        for i in range(0, len(tx_hashes), 2):
            left = bytes.fromhex(tx_hashes[i])
            right = bytes.fromhex(tx_hashes[i + 1])
            combined = left + right
            new_level.append(aes_hashing(combined).hex())
        tx_hashes = new_level
    return tx_hashes[0]
