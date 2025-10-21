import random
import sys
from datetime import datetime  # realiam timestamp
from Crypto.Cipher import AES

# AES-hash parametrai
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

# Vartotojas su UTXO
class User:
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key
        self._utxos = []  # Private UTXO
        self._balance = 0  # Private balance

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

# Vartotojų generavimas (~1000 vartotojų)
def generate_users(num_users=1000, seed=None):
    if seed is not None:
        random.seed(seed)
    users = []
    for i in range(num_users):
        name = f"User_{i+1}"
        public_key = aes_hashing(f"{name}{random.randint(1, 10000)}".encode()).hex()
        user = User(name, public_key)
        # Atsitiktinai pridedame 10 UTXO kiekvienam vartotojui
        for _ in range(10):
            amount = random.randint(100, 1000)
            user.add_utxo(amount)
        users.append(user)
    return users

# Transakcija (UTXO modelis)
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

        # Išimame panaudotus UTXO
        self.sender.remove_utxos(used_utxos)

        # transaction_id (kitų laukų hash) – naudojame AES-hash
        tx_data = f"{self.sender.public_key}{self.receiver.public_key}{self.amount}".encode()
        self.transaction_id = aes_hashing(tx_data).hex()

# Transakcijų generavimas (~10 000)
def generate_transactions(users, num_transactions=10000, seed=None):
    if seed is not None:
        random.seed(seed + 1337)
    transactions = []
    for _ in range(num_transactions):
        sender = random.choice(users)
        receiver = random.choice(users)
        if receiver is sender:
            continue
        amount = random.randint(1, 1000)
        tx = Transaction(sender, receiver, amount)
        try:
            tx.generate_transaction()
            transactions.append(tx)
        except ValueError as e:
            print(f"Transakcija nepavyko: {e}")
    return transactions

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
            combined = (tx_hashes[i] + tx_hashes[i + 1]).encode()
            new_level.append(aes_hashing(combined).hex())
        tx_hashes = new_level
    return tx_hashes[0]

# Blokas
class Block:
    # konstruktorius
    def __init__(self, block_id, transactions, difficulty=3):
        self.block_id = block_id
        self.prev_block_hash = None
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")  # Laiko antspaudas (reali data/laikas)
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

# Blockchain
class Blockchain:
    # konstruktorius
    def __init__(self, difficulty=3):
        self.chain = []
        self.difficulty = difficulty

    # grazina paskutinio bloko hash'a
    def get_last_hash(self):
        if not self.chain:
            return "0" * 32  # AES 16 baitų -> 32 hex simboliai
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

# maininimo funkcija (Proof-of-Work)
def mine_blockchain(blockchain, transactions, block_size=100, difficulty=3,
                    block_out_path="block_output.txt", mining_log_path="mining_log.txt",
                    write_mode="overwrite"):
    # failų režimas
    file_mode = "w" if write_mode == "overwrite" else "a"

    # išvalome failus, jei perrašymas
    if file_mode == "w":
        with open(block_out_path, "w", encoding="utf-8") as _:
            pass
        with open(mining_log_path, "w", encoding="utf-8") as _:
            pass

    block_id = len(blockchain.chain) + 1

    while transactions:
        new_block, selected = create_new_block(
            transactions, block_id, blockchain.get_last_hash(), block_size=100, difficulty=difficulty
        )

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

        # pašaliname iš viso sąrašo būtent pasirinktas transakcijas
        for tx in selected:
            transactions.remove(tx)

        blockchain.add_block(new_block)

        mining_info = {
            "block_id": new_block.block_id,
            "nonce": new_block.nonce,
            "hash": new_block.hash,
            "difficulty": new_block.difficulty
        }
        write_to_file_mining(mining_info, mining_log=mining_log_path, mode=file_mode)
        write_block_to_file(new_block, filename=block_out_path, mode=file_mode)

        block_id += 1

# funkcija irasymui i faila
def write_block_to_file(block, filename="block_output.txt", mode="a"):
    with open(filename, mode, encoding="utf-8") as file:
        file.write(f"Block ID: {block.block_id}\n")
        file.write(f"Block Timestamp: {block.timestamp}\n")
        file.write(f"Block Previous Hash: {block.prev_block_hash}\n")
        file.write(f"Block Hash: {block.hash}\n")
        file.write(f"Merkle Root: {block.merkle_root}\n\n")

        for i, tx in enumerate(block.transactions):
            file.write(f"Transaction {i+1}:\n")
            file.write(f"  Sender: {tx.sender.name} -> Receiver: {tx.receiver.name}\n")
            file.write(f"  Amount: {tx.amount}\n")
            file.write(f"  Inputs: {tx.inputs}\n")
            file.write(f"  Outputs: {tx.outputs}\n")
            file.write(f"  TxID: {tx.transaction_id}\n\n")

        # konsolės išvedimas
        print(f"Block ID: {block.block_id}")
        print(f"Block Timestamp: {block.timestamp}")
        print(f"Block Previous Hash: {block.prev_block_hash}")
        print(f"Block Hash: {block.hash}")
        print(f"Merkle Root: {block.merkle_root}\n")

# funkcija irasanti i faila kasimo informacija
def write_to_file_mining(mining_info, mining_log="mining_log.txt", mode="a"):
    with open(mining_log, mode, encoding="utf-8") as file:
        file.write(f"{'=' * 60}\n")
        file.write(f"MINING REPORT — Block ID: {mining_info['block_id']}\n")
        file.write(f"Difficulty: {mining_info['difficulty']}\n")
        file.write(f"Nonce: {mining_info['nonce']}\n")
        file.write(f"Block Hash: {mining_info['hash']}\n")
        file.write(f"{'=' * 60}\n\n")

# flag'u parsinimas
def parse_flags(argv):
    params = {
        "users": 1000,
        "tx": 10000,
        "difficulty": 3,
        "block_size": 100,
        "write": "overwrite",  # overwrite | append
        "seed": None
    }

    if len(argv) <= 1:
        print("Nepateikti flag'ai — naudojamos numatytos reikšmės.")
        return params

    raw_args = argv[1:]
    flags = [a for a in raw_args if a.startswith("--")]
    rest = [a for a in raw_args if not a.startswith("--")]

    allowed = {"--users", "--tx", "--difficulty", "--block-size", "--write", "--seed"}
    unknown = [f for f in flags if f.split("=")[0] not in allowed]
    if unknown:
        print("Nežinomi flag'ai:", ", ".join(unknown))
        print("Bus ignoruojami. Galimi flag'ai: --users=N --tx=N --difficulty=N --block-size=N --write=append|overwrite --seed=N")

    for f in flags:
        key_val = f.split("=", 1)
        key = key_val[0]
        val = key_val[1] if len(key_val) == 2 else None
        if key == "--users":
            try: params["users"] = int(val)
            except: print("Bloga --users reikšmė, naudojama numatyta (1000).")
        elif key == "--tx":
            try: params["tx"] = int(val)
            except: print("Bloga --tx reikšmė, naudojama numatyta (10000).")
        elif key == "--difficulty":
            try: params["difficulty"] = int(val)
            except: print("Bloga --difficulty reikšmė, naudojama numatyta (3).")
        elif key == "--block-size":
            try: params["block_size"] = int(val)
            except: print("Bloga --block-size reikšmė, naudojama numatyta (100).")
        elif key == "--write":
            if val in ("append", "overwrite"):
                params["write"] = val
            else:
                print("Bloga --write reikšmė, naudokite: append | overwrite. Naudojama numatyta (overwrite).")
        elif key == "--seed":
            try: params["seed"] = int(val)
            except: print("Bloga --seed reikšmė, naudojama numatyta (None).")

    if rest:
        print("Nepanaudoti argumentai:", " ".join(rest))
    return params

def main():
    params = parse_flags(sys.argv)

    print("Generuojame vartotojus ir transakcijas...")
    users = generate_users(num_users=params["users"], seed=params["seed"])
    transactions = generate_transactions(users, num_transactions=params["tx"], seed=params["seed"])

    blockchain = Blockchain(difficulty=params["difficulty"])

    mine_blockchain(
        blockchain,
        transactions,
        block_size=params["block_size"],
        difficulty=params["difficulty"],
        block_out_path="block_output.txt",
        mining_log_path="mining_log.txt",
        write_mode=params["write"]
    )

    print("\nDarbas baigtas. Rezultatai: block_output.txt ir mining_log.txt")

if __name__ == "__main__":
    main()
