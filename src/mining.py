import os
from concurrent.futures import ProcessPoolExecutor, FIRST_COMPLETED, wait

from src.chain import create_new_block

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

# transakcijų išvedimas į konsolę (pilnas arba „preview“)
def print_block_txs_to_console(block, print_all: bool = False, preview_count: int = 3):

    if not block.transactions:
        print("  (Šiame bloke nėra transakcijų)")
        return

    if print_all:
        print(f"  Transakcijos (viso: {len(block.transactions)}):")
        for i, tx in enumerate(block.transactions, 1):
            print(f"  TX#{i}: {tx.sender.name} -> {tx.receiver.name}, amount={tx.amount}")
            print(f"    Inputs:  {tx.inputs}")
            print(f"    Outputs: {tx.outputs}")
        return

    # preview režimas
    count = min(preview_count, len(block.transactions))
    print(f"  Transakcijų peržiūra (pirmos {count} iš {len(block.transactions)}):")
    for i in range(count):
        tx = block.transactions[i]
        print(f"  TX#{i+1}: {tx.sender.name} -> {tx.receiver.name}, amount={tx.amount}")
        print(f"    Inputs:  {tx.inputs}")
        print(f"    Outputs: {tx.outputs}")
    if len(block.transactions) > count:
        print(f"  … ir dar {len(block.transactions) - count} transakcijų (pilna versija: block_output.txt)")

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
                    append_mode=False,
                    print_txs=False,            # jei True – spausdina visas TX į konsolę
                    tx_preview=3):              # jei print_txs=False – spausdina tiek pirmų TX
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

        # Atnaujiname UTXO tik PO KASIMO
        included = 0
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
            included += 1

        # Pašaliname iš viso sąrašo būtent tas 100 pasirinktu transakcijų (ne pirmas 100)
        for tx in selected:
            if tx in transactions:
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

        # Konsolės „preview“ – vienodas UX
        print_block_txs_to_console(
            new_block,
            print_all=print_txs,
            preview_count=tx_preview
        )

        # SUMMARY: aiški santrauka dėstytojui
        print(f"[SUMMARY] Block #{new_block.block_id} mined at difficulty={new_block.difficulty}")
        print(f"[SUMMARY] Hash={new_block.hash}, nonce={new_block.nonce}")
        print(f"[SUMMARY] Included TXs: {included}, mempool left: {len(transactions)}")
        print(f"[SUMMARY] Chain length: {len(blockchain.chain)}\n")

        # Einame prie kito ID
        block_id += 1

def _mine_candidate_worker(prev_hash: str, timestamp: str, version: int,
                           merkle_root: str, difficulty: int,
                           start_nonce: int, max_attempts: int):
    from src.hashing import aes_hashing
    nonce = start_nonce
    for attempts in range(1, max_attempts + 1):
        header = f"{prev_hash}{timestamp}{version}{merkle_root}{nonce}{difficulty}"
        h = aes_hashing(header.encode()).hex()
        if h.startswith("0" * difficulty):
            return True, nonce, attempts, h
        nonce += 1
    return False, None, max_attempts, None

def distributed_mining(blockchain, transactions, users, block_size=100, difficulty=3,
                         num_candidates=5, max_attempts=10000,
                         block_file="block_output.txt", mining_file="mining_log.txt",
                         workers=None,
                         print_txs=False,            # preview/vistos TX konsolėje
                         tx_preview=3):              # kiek rodyti per preview
    if not transactions:
        print("nera transakciju kasimui")
        return

    if workers is None:
        workers = max(1, min(num_candidates, (os.cpu_count() or 1)))

    pk_index = {u.public_key: u for u in users}

    # VIENODAS block_id VISIEMS KANDIDATAMS
    block_id = len(blockchain.chain) + 1

    candidate_blocks = []
    for _ in range(num_candidates):
        candidate, selected = create_new_block(
            transactions, block_id, blockchain.get_last_hash(),
            block_size=block_size, difficulty=difficulty
        )
        candidate_blocks.append((candidate, selected))

    print(f"Sukurta {num_candidates} kandidatinių blokų, pradedamas LYGIAGRETUS kasimas ({workers} proc.)...")
    winner = None
    winner_selected = None

    futures = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for candidate, _ in candidate_blocks:
            futures.append(
                ex.submit(
                    _mine_candidate_worker,
                    candidate.prev_block_hash,
                    candidate.timestamp,
                    getattr(candidate, "version", 1),
                    candidate.merkle_root,
                    candidate.difficulty,
                    0,
                    max_attempts
                )
            )

        done, _ = wait(futures, return_when=FIRST_COMPLETED)
        found_any = False
        for fut in done:
            try:
                found, nonce, attempts, h = fut.result()
            except Exception:
                continue
            if found:
                idx = futures.index(fut)
                candidate, selected = candidate_blocks[idx]
                candidate.nonce = nonce
                candidate.hash = h
                winner = candidate
                winner_selected = selected
                print(f"Block #{winner.block_id} mined. Attempts = {attempts}. Nonce = {winner.nonce}")
                found_any = True
                break

        if not found_any:
            print("No block was mined, trying to increase attempts")
            return distributed_mining(
                blockchain, transactions, users,
                block_size=block_size,
                difficulty=difficulty,
                num_candidates=num_candidates,
                max_attempts=max_attempts * 2,
                block_file=block_file,
                mining_file=mining_file,
                workers=workers,
                print_txs=print_txs,
                tx_preview=tx_preview
            )

    if winner:
        blockchain.add_block(winner)
    else:
        print("No block was mined, trying to increase attempts")
        return distributed_mining(
            blockchain, transactions, users,
            block_size=block_size,
            difficulty=difficulty,
            num_candidates=num_candidates,
            max_attempts=max_attempts * 2,
            block_file=block_file,
            mining_file=mining_file,
            workers=workers,
            print_txs=print_txs,
            tx_preview=tx_preview
        )

    # UTXO atnaujinimas + pašalinimas iš mempool (tik laimėtojo bloko TX)
    included = 0
    if winner_selected:
        for tx in winner_selected:
            sender = tx.sender
            input_ids = [u for (u, v) in tx.inputs]
            sender.remove_utxos(set(input_ids))

            for (pk, val) in tx.outputs:
                user = pk_index.get(pk, None)
                if user:
                    user.add_utxo(val)
            included += 1

        for tx in winner_selected:
            if tx in transactions:
                transactions.remove(tx)

    # įrašai į failus — kaip v0.1
    mining_info = {
        "block_id": winner.block_id,
        "nonce": winner.nonce,
        "hash": winner.hash,
        "difficulty": winner.difficulty
    }
    write_to_file_mining(mining_info, mining_log=mining_file)
    write_block_to_file(winner, filename=block_file)

    # vienodas UX — preview ir čia
    print_block_txs_to_console(
        winner,
        print_all=print_txs,
        preview_count=tx_preview
    )

    # vienas aiškus SUMMARY blokas (be perteklinių dubliavimų)
    print(f"[SUMMARY] Block #{winner.block_id} mined at difficulty={winner.difficulty}")
    print(f"[SUMMARY] Hash={winner.hash}, nonce={winner.nonce}")
    print(f"[SUMMARY] Included TXs: {included}, mempool left: {len(transactions)}")
    print(f"[SUMMARY] Chain length: {len(blockchain.chain)}")
    print("Block added. Current chain length =", len(blockchain.chain))
