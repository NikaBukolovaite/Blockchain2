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

        print_block_txs_to_console(
            new_block,
            print_all=print_txs,
            preview_count=tx_preview
        )

        # Einame prie kito ID
        block_id += 1
