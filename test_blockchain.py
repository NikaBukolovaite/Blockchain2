import unittest
import sys
import os

import random
from src.hashing import aes_hashing
from src.models import User, Transaction, generate_users, generate_transactions
from src.merkle import calculate_merkle_root
from src.chain import Block, Blockchain

class TestUser(unittest.TestCase):
    def test_utxo_balance_add_remove(self):
        user = User("Alice", aes_hashing(b"Alice").hex())
        user.add_utxo(100)
        user.add_utxo(200)
        self.assertEqual(user.get_balance(), 300)
        first_utxo_id = user.get_utxos()[0][0]
        user.remove_utxos({first_utxo_id})
        self.assertEqual(user.get_balance(), 200)

class TestTransaction(unittest.TestCase):
    def setUp(self):
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

    class TestMerkleTree(unittest.TestCase):
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
            txs[0].amount = 9999
            root2 = calculate_merkle_root(txs)
            self.assertNotEqual(root1, root2)
class TestBlockAndBlockchain(unittest.TestCase):
    def test_block_integration(self):
        users = generate_users(10)
        txs = generate_transactions(users, num_transactions=10)
        blockchain = Blockchain(difficulty=1)
        block = Block(1, txs, difficulty=1)
        block.prev_block_hash = blockchain.get_last_hash()
        block.hash = block.calculate_hash()
        blockchain.add_block(block)

        self.assertEqual(len(blockchain.chain), 1)
        self.assertIsNotNone(block.merkle_root)
        self.assertTrue(block.hash.startswith("0" * block.difficulty))



if __name__ == '__main__':
    unittest.main()
