import random
import hashlib
import sys

class User:
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key
        self._utxos = []  # Private UTXO
        self._balance = 0  # Private balance

    def add_utxo(self, amount):
        utxo = hashlib.sha256(f"{self.public_key}|{amount}|{random.randint(1, 10000)}".encode()).hexdigest()
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
        public_key = hashlib.sha256(f"{name}{random.randint(1, 10000)}".encode()).hexdigest()
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

    def generate_transaction(self):
        remaining_amount = self.amount
        available_utxos = self.sender.get_utxos()
        total_utxo_value = sum(value for _, value in available_utxos)
        
        if total_utxo_value < self.amount:
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

def write_results_to_file_and_terminal(transactions, filename="transactions_output.txt"):
    with open(filename, "w") as file:
        for i, tx in enumerate(transactions[:5]):  
            file.write(f"Transaction {i+1}:\n")
            file.write(f"  Sender: {tx.sender.name} → Receiver: {tx.receiver.name}\n")
            file.write(f"  Amount: {tx.amount}\n")
            file.write(f"  Inputs: {tx.inputs}\n")
            file.write(f"  Outputs: {tx.outputs}\n\n")
            
            print(f"Transaction {i+1}:")
            print(f"  Sender: {tx.sender.name} → Receiver: {tx.receiver.name}")
            print(f"  Amount: {tx.amount}")
            print(f"  Inputs: {tx.inputs}")
            print(f"  Outputs: {tx.outputs}\n")

def main():
    if len(sys.argv) > 1:
        print("Programos argumentai:")
        print(sys.argv)

    print("Generuojame vartotojus ir transakcijas...")
    users = generate_users()
    transactions = generate_transactions(users)

    write_results_to_file_and_terminal(transactions)

if __name__ == "__main__":
    main()
