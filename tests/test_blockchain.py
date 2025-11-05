import unittest
import sys
import os
import random
import io

from src.hashing import aes_hashing
from src.models import User, Transaction, generate_users, generate_transactions
from src.merkle import calculate_merkle_root
from src.mining import distributed_mining
from src.chain import Block, Blockchain

# Deterministiškumas visiems testams
random.seed(0)

# Nutildyti stdout/stderr testų metu
class BaseTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._stdout_orig = sys.stdout
        self._stderr_orig = sys.stderr
        self._stdout_buf = io.StringIO()
        self._stderr_buf = io.StringIO()
        sys.stdout = self._stdout_buf
        sys.stderr = self._stderr_buf

    def tearDown(self):
        sys.stdout = self._stdout_orig
        sys.stderr = self._stderr_orig
        super().tearDown()


class TestUser(BaseTest):
    def test_utxo_balance_add_remove(self):
        user = User("Alice", aes_hashing(b"Alice").hex())
        user.add_utxo(100)
        user.add_utxo(200)
        self.assertEqual(user.get_balance(), 300)
        first_utxo_id = user.get_utxos()[0][0]
        user.remove_utxos({first_utxo_id})
        self.assertEqual(user.get_balance(), 200)


class TestTransaction(BaseTest):
    def setUp(self):
        super().setUp()  # svarbu: kad veiktų stdout/stderr nutildymas
        self.users = generate_users(2)
        self.sender = self.users[0]
        self.receiver = self.users[1]

    def test_valid_transaction(self):
        tx = Transaction(self.sender, self.receiver, 50)
        tx.generate_transaction()
        self.assertIsNotNone(tx.transaction_id)
        self.assertTrue(tx.validate_transaction_id())

    def test_invalid_transaction_id_after_modification(self):
        tx = Transaction(self.sender, self.receiver, 50)
        tx.generate_transaction()
        tx.amount = 9999
        self.assertFalse(tx.validate_transaction_id())

    def test_balance_check_raises_valueerror(self):
        poor_sender = self.sender
        poor_sender._utxos.clear()
        poor_sender._balance = 10
        tx = Transaction(poor_sender, self.receiver, 1000)
        with self.assertRaises(ValueError):
            tx.generate_transaction()


class TestMerkleTree(BaseTest):
    def test_merkle_root_consistency(self):
        users = generate_users(4)
        txs = []
        for i in range(4):
            t = Transaction(users[0], users[1], 10 + i)
            t.generate_transaction()
            txs.append(t)

        root1 = calculate_merkle_root(txs)
        root2 = calculate_merkle_root(txs)
        self.assertEqual(root1, root2)

    def test_merkle_root_changes_if_data_changes(self):
        users = generate_users(4)
        txs = []
        for i in range(4):
            t = Transaction(users[0], users[1], 10 + i)
            t.generate_transaction()
            txs.append(t)

        root1 = calculate_merkle_root(txs)

        # Pakeičiame pirmą transakciją nauja, kad tikrai pasikeistų transaction_id
        new_tx = Transaction(users[0], users[1], 42)
        new_tx.generate_transaction()
        txs[0] = new_tx

        root2 = calculate_merkle_root(txs)
        self.assertNotEqual(root1, root2)


class TestProofOfWorkLogic(BaseTest):
    def test_pow_logic_changes_with_nonce(self):
        users = generate_users(5)
        txs = generate_transactions(users, num_transactions=5)
        difficulty = 2
        blockchain = Blockchain(difficulty=difficulty)
        block = Block(1, txs, difficulty=difficulty)
        block.prev_block_hash = blockchain.get_last_hash()

        first_hash = block.calculate_hash()
        block.nonce += 1
        second_hash = block.calculate_hash()
        self.assertNotEqual(first_hash, second_hash, "Hash turi keistis keičiant nonce")

        start_nonce = block.nonce
        iterations = 0
        max_iterations = 5000

        while True:
            block.hash = block.calculate_hash()
            iterations += 1
            if block.hash.startswith("0" * block.difficulty):
                break
            block.nonce += 1
            if iterations > max_iterations:
                self.fail("Proof-of-Work ciklas per ilgas (greičiausiai logikos klaida)")

        self.assertTrue(block.hash.startswith("0" * block.difficulty) or block.difficulty < 2)
        self.assertGreater(block.nonce, start_nonce)
        self.assertIsNotNone(block.merkle_root)

        self.assertEqual(len(blockchain.chain), 0, "Blokas dar nepridėtas prie grandinės")
        blockchain.add_block(block)
        self.assertEqual(len(blockchain.chain), 1)
        self.assertEqual(blockchain.chain[0].hash, block.hash)


class TestMiningCandidates(BaseTest):
    def setUp(self):
        super().setUp()  # svarbu: kad veiktų stdout/stderr nutildymas
        self.users = generate_users(10)
        self.transactions = generate_transactions(self.users, num_transactions=50)
        self.blockchain = Blockchain(difficulty=1)

    def test_candidate_generation_and_mining(self):
        start_len = len(self.blockchain.chain)
        distributed_mining(
            blockchain=self.blockchain,
            transactions=self.transactions,
            users=self.users,
            block_size=10,
            difficulty=1,
            num_candidates=5,
            max_attempts=500
        )
        end_len = len(self.blockchain.chain)
        self.assertGreater(end_len, start_len, "Po kasimo grandinė turėtų pailgėti bent 1 bloku")
        last_block = self.blockchain.chain[-1]
        self.assertIsNotNone(last_block.hash)
        self.assertEqual(len(last_block.hash), 32)
        self.assertIsNotNone(last_block.merkle_root)


if __name__ == '__main__':
    unittest.main()
