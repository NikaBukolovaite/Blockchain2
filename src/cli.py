import sys
from models import generate_users, generate_transactions
from chain import Blockchain
from mining import mine_blockchain

def parse_flags(argv):
    # Paprastas flag'ų parsinimas: --append, --overwrite, --users=N, --tx=N, --block-size=N, --difficulty=N, --print-txs, --tx-preview=N
    flags = {
        "append": False,
        "overwrite": True,
        "users": 1000,
        "tx": 10000,
        "block_size": 100,
        "difficulty": 3,
        "print_txs": False,  # jei True – visos TX bus spausdinamos konsolėje
        "tx_preview": 3      # jei print_txs=False – tiek pirmų TX spausdinti
    }
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
        elif al == "--print-txs":
            flags["print_txs"] = True
        elif al.startswith("--tx-preview="):
            try:
                flags["tx_preview"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --tx-preview reikšmė, naudosime numatytą: 3")
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
        append_mode=append_mode,
        print_txs=flags["print_txs"],
        tx_preview=flags["tx_preview"]
    )

if __name__ == "__main__":
    main()
