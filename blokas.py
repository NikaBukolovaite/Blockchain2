import random
import hashlib
import sys
from Crypto.Cipher import AES

BLOCK = 16
IV_LEFT = bytes.fromhex("0123456789abcdeffedcba9876543210")
IV_RIGHT = bytes.fromhex("fedcba98765432100123456789abcdef")
FINAL_CONST = bytes.fromhex('ffffffffffffffffffffffffffffffff')

def pad_message(message: bytes) -> bytes:
    L = len(message)
    message_in_bits = L * 8
    padded = message + b'\x80'
    num_of_zeros = (16 - (len(padded) + 8) % 16) % 16
    padded += b'\x00' * num_of_zeros
    padded += message_in_bits.to_bytes(8, 'big')
    return padded

def xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("Ilgiai turi sutapti")
    return bytes([x ^ y for x, y in zip(a, b)])

def aes_hashing(message: bytes) -> bytes:
    state_left = IV_LEFT
    state_right = IV_RIGHT
    padded_message = pad_message(message)

    for i in range(0, len(padded_message), BLOCK):
        Mi = padded_message[i:i + BLOCK]

        cipher = AES.new(state_left, AES.MODE_ECB)
        encrypted = cipher.encrypt(state_right)

        state_right = xor_bytes(encrypted, Mi)
        state_left, state_right = state_right, state_left

    cipher = AES.new(state_left, AES.MODE_ECB)
    final_enc = cipher.encrypt(FINAL_CONST)

    return final_enc

class User:
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key
        self._utxos = []  
        self._balance = 0 

    def add_utxo(self, amount):
        utxo = aes_hashing(f"{self.public_key}|{amount}|{random.randint(1, 10000)}".encode()).hex()
        self._utxos.append((utxo, amount))
        self._balance += amount

    def get_balance(self):
        return self._balance

    def get_utxos(self):
        return self._utxos

    def remove_utxos(self, used_utxos):
        self._utxos = [utxo for utxo in self._utxos if utxo[0] not in used_utxos]
        self._balance = sum([value for _, value in self._utxos])

def generate_users(num_users=1000):
    users = []
    for i in range(num_users):
        name = f"User_{i+1}"
        public_key = aes_hashing(f"{name}{random.randint(1, 10000)}".encode()).hex()
        user = User(name, public_key)
        
        for _ in range(10):
            amount = random.randint(100, 1000)
            user.add_utxo(amount)
        
        users.append(user)
    return users

class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.inputs = []
        self.outputs = []
        self.transaction_id = None

    def generate_transaction(self):
        remaining_amount = self.amount
        available_utxos = self.sender.get_utxos()
        total_utxo_value = sum(value for _, value in available_utxos)
        
        if total_utxo_value < self.amount:
            print(f"Siuntėjas {self.sender.name} turi tik {total_utxo_value} pinigų, bet reikia {self.amount}.")
            raise ValueError("Siuntėjas neturi pakankamai pinigų.")
        
        used_utxos = []
        for utxo, value in available_utxos:
            if remaining_amount <= 0:
                break
            if value >= remaining_amount:
                self.inputs.append((utxo, remaining_amount)) 
                self.outputs.append((self.receiver.public_key, remaining_amount))
                used_utxos.append(utxo)
                remaining_amount = 0
            else:
                self.inputs.append((utxo, value)) 
                self.outputs.append((self.receiver.public_key, value)) 
                used_utxos.append(utxo)
                remaining_amount -= value
        
        self.sender.remove_utxos(used_utxos)
        
        tx_data = f"{self.sender.public_key}{self.receiver.public_key}{self.amount}".encode()
        self.transaction_id = aes_hashing(tx_data).hex()

def generate_transactions(users, num_transactions=10000):
    transactions = []
    for _ in range(num_transactions):
        sender = random.choice(users)
        receiver = random.choice(users)
        amount = random.randint(1, 1000)
        tx = Transaction(sender, receiver, amount)
        try:
            tx.generate_transaction()
            transactions.append(tx)
        except ValueError as e:
            print(f"Transakcija nepavyko: {e}")
    return transactions

#funkcija Merkle Root Hash apskaiciavimui
def calculate_merkle_root(transactions):
    tx_hashes = [tx.transaction_id for tx in transactions]
    if not tx_hashes:
        return None
    while len(tx_hashes) > 1:
        if len(tx_hashes) % 2 != 0:
            tx_hashes.append(tx_hashes[-1])
        new_level = []
        for i in range(0, len(tx_hashes), 2):
            combined = (tx_hashes[i] + tx_hashes[i + 1]).encode()
            new_level.append(aes_hashing(combined).hex())
        tx_hashes = new_level

    return tx_hashes[0]


class Block:
    #konstruktorius
    def __init__(self, block_id, transactions, difficulty=3):
        self.block_id = block_id
        self.prev_block_hash = None
        self.timestamp = aes_hashing(str(random.randint(1, 100000)).encode()).hex()  # Laiko antspaudas
        self.nonce = 0
        self.version = 1
        self.difficulty = difficulty
        self.merkle_root = calculate_merkle_root(transactions)

        self.transactions = transactions
        self.hash = None

    #padaro hash is bloko header'io
    def calculate_hash(self):
        header = (
            f"{self.version}"
            f"{self.prev_block_hash}"
            f"{self.timestamp}"
            f"{self.nonce}"
            f"{self.difficulty}"
        )
        return aes_hashing(header.encode()).hex()



class Blockchain:
    #konstruktorius
    def __init__(self, difficulty=3):
        self.chain = []
        self.difficulty = difficulty
    #grazina paskutinio bloko hash'a
    def get_last_hash(self):
        if not self.chain:
            return "0" * 64
        return self.chain[-1].hash
    #prideda bloka i hasha
    def add_block(self, block):
        self.chain.append(block)

    def __repr__(self):
        return f"Block {self.block_id} - Hash: {self.calculate_hash()}"

#funkcija, sukurianti nauja bloka
def create_new_block(transactions, block_id, prev_block_hash):
    selected_transactions = random.sample(transactions, min(100, len(transactions)))
    
    new_block = Block(block_id, selected_transactions)
    new_block.prev_block_hash=prev_block_hash
    
    return new_block
 #maininimo funkcija
def mine_blockchain(blockchain, transactions, block_size=100, difficulty=3):
        block_id = len(blockchain.chain) + 1

        while transactions:
            new_block = create_new_block(transactions, block_id, blockchain.get_last_hash())

            print(f"Kasamas blokas {new_block.block_id} su {len(new_block.transactions)} transakciju...")
            while True:
                block_hash = new_block.calculate_hash()
                if block_hash.startswith("0" * difficulty):
                    new_block.hash = block_hash
                    print(f"Blokas iskastas! Nonce={new_block.nonce} Hash={new_block.hash}\n")
                    break
                new_block.nonce += 1

            for tx in new_block.transactions:
                tx.receiver.add_utxo(tx.amount)

            del transactions[:block_size]

            blockchain.add_block(new_block)

            block_id += 1
            mining_info = { "block_id": new_block.block_id,"nonce": new_block.nonce, "hash": new_block.hash, "difficulty": new_block.difficulty}
            write_to_file_mining(mining_info)

#funkcija irasymui i faila
def write_block_to_file(block, filename="block_output.txt"):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"Block ID: {block.block_id}\n")
        file.write(f"Block Timestamp: {block.timestamp}\n")
        file.write(f"Block Hash: {block.calculate_hash()}\n\n")
        
        for i, tx in enumerate(block.transactions):
            file.write(f"Transaction {i+1}:\n")
            file.write(f"  Sender: {tx.sender.name} -> Receiver: {tx.receiver.name}\n")
            file.write(f"  Amount: {tx.amount}\n")
            file.write(f"  Inputs: {tx.inputs}\n")
            file.write(f"  Outputs: {tx.outputs}\n\n")
            
            print(f"Transaction {i+1}:")
            print(f"  Sender: {tx.sender.name} -> Receiver: {tx.receiver.name}")
            print(f"  Amount: {tx.amount}")
            print(f"  Inputs: {tx.inputs}")
            print(f"  Outputs: {tx.outputs}\n")
        
        print(f"Block ID: {block.block_id}")
        print(f"Block Timestamp: {block.timestamp}")
        print(f"Block Hash: {block.calculate_hash()}")

#funkcija irasanti i faila kasimo informacija
def write_to_file_mining(mining_info, mining_log="mining_log.txt"):
    with open(mining_log, "a", encoding="utf-8") as file:
        file.write(f"{'=' * 60}\n")
        file.write(f"MINING REPORT — Block ID: {mining_info['block_id']}\n")
        file.write(f"Difficulty: {mining_info['difficulty']}\n")
        file.write(f"Nonce: {mining_info['nonce']}\n")
        file.write(f"Block Hash: {mining_info['hash']}\n")
        file.write(f"{'=' * 60}\n\n")

def main():
    print("Generuojame vartotojus ir transakcijas...")
    users = generate_users()
    transactions = generate_transactions(users)
    blockchain = Blockchain(difficulty=3)

    new_block = create_new_block(transactions=transactions, block_id=1, prev_block_hash=blockchain.get_last_hash())
    mine_blockchain(blockchain, transactions, block_size=100, difficulty=3)

    write_block_to_file(new_block)


if __name__ == "__main__":
    main()
