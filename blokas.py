import random
import sys
import os
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
def generate_users(num_users=1000):
    users = []
    for i in range(num_users):
        name = f"User_{i+1}"
        public_key = aes_hashing(f"{name}{random.randint(1, 10000)}".encode()).hex()
        user = User(name, public_key)
        # vietoje fiksuotu 10 mazu UTXO – parenkame tiksline pradine suma [100..1_000_000] ir suskaidome i kelis UTXO
        target_total = random.randint(100, 1000000)
        if target_total < 1000:
            user.add_utxo(target_total)
        else:
            # atsitiktinis UTXO kiekis (5–15), kad islaikyti realistiška „mozaika“
            n_utxos = random.randint(5, 15)
            remaining = target_total
            for _ in range(n_utxos - 1):
                # gabalas tarp ~1% ir ~20% likucio, bet ne maziau kaip 100
                low = max(100, remaining // 100)
                high = max(low, remaining // 5)
                chunk = random.randint(low, high)
                remaining -= chunk
                user.add_utxo(chunk)
                if remaining <= 100:
                    break
            if remaining > 0:
                user.add_utxo(remaining)
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
        # pridėtas tx_nonce, kad id būtų sunkiau koliduoti bei patogiau validacijai
        self.tx_nonce = random.randint(1, 1000000000)

    def _compute_tx_id(self):
        # skaičiuojame hash nuo VISKO: sender_pk, receiver_pk, amount, tx_nonce, surikiuoti inputs/outputs
        sender_pk = self.sender.public_key
        receiver_pk = self.receiver.public_key

        # surikiuojame inputs pagal UTXO id
        sorted_inputs = sorted(self.inputs, key=lambda x: x[0])  # (utxo_id, utxo_value)
        # surikiuojame outputs pagal (pk, amount)
        sorted_outputs = sorted(self.outputs, key=lambda x: (x[0], x[1]))  # (pk, amount)

        parts = []
        parts.append(f"sender={sender_pk}")
        parts.append(f"receiver={receiver_pk}")
        parts.append(f"amount={self.amount}")
        parts.append(f"tx_nonce={self.tx_nonce}")
        parts.append("inputs=[")
        for utxo_id, utxo_val in sorted_inputs:
            parts.append(f"{utxo_id}:{utxo_val}")
        parts.append("]")
        parts.append("outputs=[")
        for pk, val in sorted_outputs:
            parts.append(f"{pk}:{val}")
        parts.append("]")

        serialized = "|".join(parts).encode()
        return aes_hashing(serialized).hex()

    def generate_transaction(self):
        # pakeista logika: čia UTXO NEUŽRAŠOM – tik parenkame inputs ir suformuojame outputs (įskaitant grąžą)
        remaining_amount = self.amount
        available_utxos = self.sender.get_utxos()
        total_utxo_value = sum(value for _, value in available_utxos)

        if total_utxo_value < self.amount:
            print(f"Siuntėjas {self.sender.name} turi tik {total_utxo_value} pinigų, bet reikia {self.amount}.")
            raise ValueError("Siuntėjas neturi pakankamai pinigų.")

        used = []
        acc = 0
        for utxo, value in available_utxos:
            used.append((utxo, value))
            acc += value
            if acc >= remaining_amount:
                break

        if acc < remaining_amount:
            print(f"Siuntėjas {self.sender.name} turi tik {total_utxo_value} pinigų, bet reikia {self.amount}.")
            raise ValueError("Siuntėjas neturi pakankamai pinigų.")  # papildoma sauga

        # inputs = sunaudojame pilnus UTXO (klasikinis UTXO modelis)
        self.inputs = used[:]  # [(utxo_id, utxo_value), ...]

        # outputs = 1) gavėjui visa suma 2) siuntėjui grąža (jei liko)
        change = acc - remaining_amount
        self.outputs = [(self.receiver.public_key, self.amount)]
        if change > 0:
            self.outputs.append((self.sender.public_key, change))

        # transaction_id (pilna informacija)
        self.transaction_id = self._compute_tx_id()

# Transakcijų generavimas (~10 000)
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

# funkcija irasymui i faila
def write_block_to_file(block, filename="block_output.txt"):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"Block ID: {block.block_id}\n")
        file.write(f"Block Timestamp: {block.timestamp}\n")
        file.write(f"Block Hash: {block.hash}\n\n")
        for i, tx in enumerate(block.transactions):
            file.write(f"Transaction {i+1}:\n")
            file.write(f"  Sender: {tx.sender.name} -> Receiver: {tx.receiver.name}\n")
            file.write(f"  Amount: {tx.amount}\n")
            file.write(f"  Inputs: {tx.inputs}\n")
            file.write(f"  Outputs: {tx.outputs}\n\n")
        # konsolės išvedimas
        print(f"Block ID: {block.block_id}")
        print(f"Block Timestamp: {block.timestamp}")
        print(f"Block Hash: {block.hash}")

# funkcija irasanti i faila kasimo informacija
def write_to_file_mining(mining_info, mining_log="mining_log.txt"):
    with open(mining_log, "a", encoding="utf-8") as file:
        file.write(f"{'=' * 60}\n")
        file.write(f"MINING REPORT — Block ID: {mining_info['block_id']}\n")
        file.write(f"Difficulty: {mining_info['difficulty']}\n")
        file.write(f"Nonce: {mining_info['nonce']}\n")
        file.write(f"Block Hash: {mining_info['hash']}\n")
        file.write(f"{'=' * 60}\n\n")

# maininimo funkcija (Proof-of-Work)
def mine_blockchain(blockchain, transactions, users, block_size=100, difficulty=3,
                    block_file="block_output.txt", mining_file="mining_log.txt",
                    append_mode=False):
    if not append_mode:
        open(block_file, "w", encoding="utf-8").close()
        open(mining_file, "w", encoding="utf-8").close()

    # greitas žemėlapis: public_key -> User (kad outputs būtų galima priskirti adresatams)
    pk_index = {u.public_key: u for u in users}

    block_id = len(blockchain.chain) + 1

    while transactions:
        new_block, selected = create_new_block(
            transactions, block_id, blockchain.get_last_hash(),
            block_size=block_size, difficulty=difficulty
        )

        print(f"Kasamas blokas {new_block.block_id} su {len(new_block.transactions)} transakciju...")
        while True:
            block_hash = new_block.calculate_hash()
            if block_hash.startswith("0" * difficulty):
                new_block.hash = block_hash
                print(f"Blokas iskastas! Nonce={new_block.nonce} Hash={new_block.hash}\n")
                break
            new_block.nonce += 1

        # Atnaujiname UTXO tik PO kasimo
        for tx in new_block.transactions:
            # patikriname, kad visi inputs UTXO vis dar egzistuoja pas siuntėją
            sender = tx.sender
            sender_utxos = dict(sender.get_utxos())  # {utxo_id: value}
            input_ids = [u for (u, v) in tx.inputs]
            missing = [uid for uid in input_ids if uid not in sender_utxos]
            if missing:
                # jei UTXO nebeliko – praleidžiam šią TX be valstybės keitimo
                print(f"ĮSPĖJIMAS: TX praleista (nebėra input UTXO). Siuntėjas={sender.name}")
                continue

            # nuimame sunaudotus UTXO pilnai
            sender.remove_utxos(set(input_ids))

            # pridedame outputs kaip naujus UTXO adresatams (gavėjas + galimai grąža siuntėjui)
            for (pk, val) in tx.outputs:
                user = pk_index.get(pk, None)
                if user is not None:
                    user.add_utxo(val)
                else:
                    # neturėtume čia patekti (visi pk priklauso users), bet paliekame saugą
                    print("ĮSPĖJIMAS: nerastas user pagal public_key, praleidžiam output.")

        # Pašaliname iš viso sąrašo būtent tas 100 pasirinktu transakcijų (ne pirmas 100)
        for tx in selected:
            transactions.remove(tx)

        # Įtraukiame bloką į grandinę
        blockchain.add_block(new_block)

        # Išsaugome kasimo informaciją
        mining_info = {
            "block_id": new_block.block_id,
            "nonce": new_block.nonce,
            "hash": new_block.hash,
            "difficulty": new_block.difficulty
        }
        write_to_file_mining(mining_info, mining_log=mining_file)

        # Išrašome bloką į failą (kad matytųsi turinys)
        write_block_to_file(new_block, filename=block_file)

        # Einame prie kito ID
        block_id += 1

def parse_flags(argv):
    # Paprastas flag'ų parsinimas: --append, --overwrite, --users=N, --tx=N, --block-size=N, --difficulty=N
    flags = { "append": False, "overwrite": True, "users": 1000, "tx": 10000, "block_size": 100, "difficulty": 3 }
    for a in argv:
        al = a.lower()
        if al == "--append":
            flags["append"] = True
            flags["overwrite"] = False
        elif al == "--overwrite":
            flags["append"] = False
            flags["overwrite"] = True
        elif al.startswith("--users="):
            try:
                flags["users"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --users reikšmė, naudosime numatytą: 1000")
        elif al.startswith("--tx="):
            try:
                flags["tx"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --tx reikšmė, naudosime numatytą: 10000")
        elif al.startswith("--block-size="):
            try:
                flags["block_size"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --block-size reikšmė, naudosime numatytą: 100")
        elif al.startswith("--difficulty="):
            try:
                flags["difficulty"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --difficulty reikšmė, naudosime numatytą: 3")
        else:
            if al.startswith("--"):
                print(f"Nežinomas flag'as: {a} (ignoruojame)")
    return flags

def main():
    # Flag'ai
    flags = parse_flags(sys.argv[1:])
    append_mode = flags["append"]
    users_n = flags["users"]
    tx_n = flags["tx"]
    block_size = flags["block_size"]
    difficulty = flags["difficulty"]

    print("Generuojame vartotojus ir transakcijas...")
    users = generate_users(users_n)
    transactions = generate_transactions(users, tx_n)
    blockchain = Blockchain(difficulty=difficulty)

    # Visą srautą daro kasimo funkcija, kuri pati teisingai tvarko Block ID didėjimą.
    mine_blockchain(
        blockchain,
        transactions,
        users,  # perduodame users, kad outputs būtų galima priskirti pagal public_key
        block_size=block_size,
        difficulty=difficulty,
        block_file="block_output.txt",
        mining_file="mining_log.txt",
        append_mode=append_mode
    )

if __name__ == "__main__":
    main()
