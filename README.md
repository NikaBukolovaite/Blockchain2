# 💻 Blockchain

Supaprastinta **blokų grandinė**, imituojanti UTXO modelį, transakcijų atranką į blokus, Merkle šaknį ir Proof‑of‑Work (PoW) kasimą. Visos maišos daromos su užduotyje pateikta **AES pagrindu sukurta maišos funkcija**.

---

# Blockchain v1.0

## Turinys

- [Apžvalga](#apžvalga)
- [Funkcijos](#funkcijos)
- [Ekrano nuotraukos ir demonstracija](#ekrano-nuotraukos-ir-demonstracija)
- [Architektūra](#architektūra)
- [Programos diegimas](#programos-diegimas)
- [Paleidimas](#paleidimas)
- [Neteisingų flag'ų atvejai](#neteisingų-flagų-atvejai)
- [Konfigūracija (CLI flag'ai)](#konfigūracija-cli-flagai)
- [Rezultatai ir log'ai](#rezultatai-ir-logai)
- [Kaip tai veikia?](#kaip-tai-veikia)

---

## Apžvalga

Programa generuoja vartotojus (UTXO mozaika), kuria atsitiktines transakcijas, formuoja blokus, apskaičiuoja **Merkle root** ir kasa blokus pagal **PoW**: kol bloko antraštės maiša prasideda `difficulty` nuliais. Patvirtinus bloką atnaujinamos UTXO būsenos.

---

## Programos struktūra

projekto_aplankas/
├─ hashing.py # AES pagrindu hash funkcija ir helper'iai
├─ models.py # User, Transaction; generate_users(), generate_transactions()
├─ merkle.py # calculate_merkle_root()
├─ block.py # Block klasė, bloko hash skaičiavimas
├─ chain.py # Blockchain klasė, create_new_block()
├─ mining.py # mine_blockchain(), žurnalų rašymas
└─ cli.py # įėjimo taškas: flag'ai ir main()

---

## Funkcijos

- **UTXO modelis** su grąža siuntėjui.
- **Transakcijų ID** iš kanonizuotos reprezentacijos per `aes_hashing()`.
- **Merkle root** su poravimu ir dubliavimu nelyginiam kiekiui.
- **PoW kasimas** su `difficulty` nuliais hash pradžioje.
- **Dviginės panaudos prevencija** kasimo metu (tikrinami įėjimo UTXO egzistavimai).
- **Žurnalai**: konsolėje ir tekstiniuose failuose.
- Pasirenkamas transakcijų „dump'as“ į failą (jei įjungta).

---

## Ekrano nuotraukos ir demonstracija

**Konsolės eiga (kasimas):**

<p align="center">
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/6b4b44aab9c552a3966e6cb2fa18f3faee8469dc/imagines/konsole.png" alt="Kasimo eiga – konsolė" width="780" />
</p>

**Failų išvestys:**

<p align="center">
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/6b4b44aab9c552a3966e6cb2fa18f3faee8469dc/imagines/mininglog.png" alt="mining_log.txt ištrauka" width="380" />
</p>

<p align="center">
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/6b4b44aab9c552a3966e6cb2fa18f3faee8469dc/imagines/blokas.png" alt="block_output.txt ištrauka" width="380" />
</p>

---

## Architektūra

- **User** – vardas, `public_key` (iš `aes_hashing`), privatūs UTXO ir balansas.
- **Transaction** – `sender`, `receiver`, `amount`, `inputs`, `outputs`, `tx_nonce`, `transaction_id`.
- **Block** – `block_id`, `prev_block_hash`, `timestamp`, `version`, `merkle_root`, `nonce`, `difficulty`, transakcijų sąrašas.
- **Blockchain** – blokų seka ir pagalbinės funkcijos (`get_last_hash`, `add_block`).
- **Merkle** – poruojami TX ID (`hex` → `bytes`), dubliuojamas paskutinis, kol lieka šaknis.
- **PoW** – `calculate_hash()` virš 6 antraštės laukų; ieškoma `0...` prefikso.

---

## Programos diegimas

**Reikalavimai:**

## Paleidimas

Paleisti programą su default nustatymais galima į konsolę įvedus:

```bash
python src/cli.py
```

Norint paleisti programą su pasirinktu(ais) parametrais:

```bash
python src/cli.py --users=1000 --tx=10000 --block-size=100 --difficulty=3 --overwrite
```

> Pastaba: nebūtina nurodyti visų flagų — galite pasirinkti tik reikiamus, o likusieji bus pritaikyti pagal numatytąsias reikšmes.
> Pastaba: flag'ai nurodyti skiltyje - [Konfigūracija (CLI flag'ai)](#konfigūracija-cli-flagai)

## Neteisingų flag’ų atvejai

- **Neatpažintas flag’as** (pvz., `--usres=10`, `--users` be `=`)  
  → Išvedamas pranešimas _„Nežinomas flag'as: … (ignoruojame)”_, flag’as **ignoruojamas**, taikomos **numatytosios** reikšmės.

- **Teisingas flag’as, bet bloga reikšmė** (pvz., `--users=abc`, `--tx=10k`, `--difficulty=low`)  
  → Išvedamas pranešimas _„Neteisinga --<pavadinimas> reikšmė, naudosime numatytą: …”_, o reikšmė nustatoma į **default** (`users=1000`, `tx=10000`, `block_size=100`, `difficulty=3`).

- **Mišinys: keli teisingi + keli klaidingi**  
  → Teisingi pritaikomi, klaidingi **ignoruojami** arba **nustatomi į default**. Programa **tęsia darbą** (klaidos nefatalinės).

- **Dublikatai** (tą patį parametrą nurodei kelis kartus)  
  → „Laimi“ **paskutinis** paminėjimas eilėje.  
  Pvz.: `--users=500 --users=2000` ⇒ galutinis `users=2000`.

- **`--append` ir `--overwrite` kartu**  
  → „Laimi“ **paskutinis**:  
  `--append --overwrite` ⇒ **perrašys** failus;  
  `--overwrite --append` ⇒ **pridės** prie esamų failų.

> Pastaba: loginės ribos šiuo metu netikrinamos (tik ar reikšmė paverčiama į `int`).  
> Pvz., `--block-size=0` ar `--difficulty=-1` gali turėti nepageidaujamų pasekmių (ar net sukelti klaidą formuojant bloką). Jei reikia, pridėkite ribų tikrinimą (pvz., `>= 1`).

### Pavyzdžiai

```bash
# Klaidinga reikšmė ir neatpažintas flag'as:
python src/cli.py --users=abc --tx=5000 --foo=bar
# Rezultatas: users → 1000 (default), tx → 5000; --foo ignoruotas.

# Dublikatai:
python src/cli.py --users=500 --users=2000
# Rezultatas: users → 2000

# Abu režimai paminėti:
python src/cli.py --append --overwrite
# Rezultatas: rašys per naują (overwrite), nes paskutinis nugalėjo.
```

---

## Konfigūracija (CLI flag'ai)

| Flag               | Reikšmė                                  |  Numatytoji | Pastabos                                       |
| ------------------ | ---------------------------------------- | ----------: | ---------------------------------------------- |
| `--users=INT`      | Sugeneruojamų vartotojų skaičius         |      `1000` | Didesnės reikšmės – daugiau RAM/CPU            |
| `--tx=INT`         | Sugeneruojamų transakcijų skaičius       |     `10000` |                                                |
| `--block-size=INT` | Transakcijų sk. viename bloke            |       `100` | Parenkama iki `block-size` **atsitiktinių** TX |
| `--difficulty=INT` | PoW sudėtingumas (nuliai hash pradžioje) |         `3` | `3` → `000…` prefiksas                         |
| `--append`         | Rašyti **pridedant** prie failų          |           — | Jei nenurodyta – veikia kaip `--overwrite`     |
| `--overwrite`      | Failus **perrašyti** nuo tuščio          | **įjungta** |                                                |

---

## Rezultatai ir log'ai

- **`mining_log.txt`** – kasimo ataskaitos (Block ID, Difficulty, Nonce, Block Hash).
- **`block_output.txt`** – blokų santrauka (ID, Timestamp, Hash) ir – jei įjungta – transakcijų detalės.
- **Konsolė** – eiga („Kasamas blokas…“, „Blokas iškastas!“) + perspėjimai (pvz., dėl dvigubų panaudų).

**Greitas pavyzdys:**

```bash
Kasamas blokas 1 su 100 transakciju...
Blokas iskastas! Nonce=48217 Hash=000a4f2c...e19
```

---

## Kaip tai veikia?

Žemiau pateiktas pilnas duomenų srautas nuo atsitiktinių duomenų generavimo iki bloko įtraukimo į grandinę ir žurnalų išrašymo.

### 1) Duomenų generavimas

- `generate_users(N)`:
  - Sukuria ~N vartotojų su `name` ir `public_key` (pastarasis gaunamas iš `aes_hashing()`).
  - Kiekvienam vartotojui parenkama tikslinė suma `[100 .. 1_000_000]` ir suskaidoma į kelis UTXO (5–15 vnt., jei suma didesnė), kad gautųsi realistiškesnė „mozaika“.
- `generate_transactions(M)`:
  - Atsitiktinai parenka siuntėją ir gavėją, parenka sumą `[1 .. 1000]`.
  - `Transaction.generate_transaction()` **NEKEIČIA** bendros UTXO būsenos: tik **parenka** įėjimus (pilnus UTXO), apskaičiuoja grąžą ir suformuoja `outputs`.
  - `transaction_id` skaičiuojamas deterministiškai (`_compute_tx_id()`): `sender_pk`, `receiver_pk`, `amount`, `tx_nonce`, bei **surikiuoti** `inputs` ir `outputs` → `aes_hashing()`.

> Pastaba: šiame etape UTXO **dar nenuimami** — jie lieka pas siuntėją iki sėkmingo kasimo.

---

### 2) Bloko kandidatūra

- `create_new_block(transactions, block_id, prev_block_hash, block_size, difficulty)`:
  - Iš didesnio transakcijų sąrašo atsitiktinai paima iki `block_size` **kandidatų**.
  - Sukuria `Block`:
    - `prev_block_hash` gaunamas iš `Blockchain.get_last_hash()`:
      - jei grandinė tuščia → `00..00` (64 nuliai),
      - kitaip → paskutinio bloko `hash`.
    - `timestamp` (`YYYY-MM-DD HH:MM:SS`), `version=1`, `difficulty`, `nonce=0`.
    - `merkle_root = calculate_merkle_root(kandidatai)`.

> Pasirinktų transakcijų turinys (ir jų hash’ai) įeina į `merkle_root`, todėl **kasimas visada vyksta virš konkretaus kandidatų rinkinio**.

---

### 3) Merkle root (`calculate_merkle_root()`)

- Paimami visų kandidatinių transakcijų `transaction_id` (hex).
- Poravimas atliekamas baitų lygmeniu (`bytes.fromhex(h1) + bytes.fromhex(h2)`), rez. maišoma per `aes_hashing()`.
- Jei lygyje transakcijų nelyginis skaičius — paskutinė **dubliuojama**.
- Procesas kartojamas, kol lieka viena šaknis → tai ir yra `merkle_root`.

---

### 4) Kasimas (Proof-of-Work)

- `Block.calculate_hash()` sudeda **6 antraštės laukus**:
  - `prev_block_hash`, `timestamp`, `version`, `merkle_root`, `nonce`, `difficulty`.
- Kol `hash` **neprasideda** `difficulty` skaičiumi nulių:
  - didinamas `nonce` (`0, 1, 2, …`) ir vėl skaičiuojamas `calculate_hash()`.
- Radus tinkamą `hash`:
  - `new_block.hash = hash`,
  - baigiamas kasimas ir pereinama prie būsenos atnaujinimo.

> Intuityviai: kuo didesnis `difficulty`, tuo rečiau sutinkami „teisingi“ hash’ai → ilgiau kasama.

---

### 5) Patvirtinimas ir UTXO atnaujinimas

Po sėkmingo kasimo — **tik tada** — pritaikomi kandidatiniai pakeitimai:

1. **Input UTXO tikrinimas:**

   - Kiekvienai transakcijai paimamas siuntėjas ir jo dabartinis UTXO sąrašas.
   - Jei nors vienas `input` UTXO **nebėra** pas siuntėją (pvz., kitoje transakcijoje jau sunaudotas):
     - transakcija **praleidžiama** (nekeičiant būsenos), o apie tai išvedamas įspėjimas.

2. **Input UTXO nuėmimas:**

   - Jei `input` UTXO egzistuoja — `sender.remove_utxos(input_ids)` sunaudoja pilnus UTXO.

3. **Output UTXO sukūrimas:**

   - Kiekvienam `output (pk, amount)` sukuriamas naujas UTXO **gavėjui** (arba grąža siuntėjui): `user.add_utxo(amount)`.

4. **Transakcijų pašalinimas iš bendro sąrašo:**

   - Tik tos `selected` transakcijos, kurios dalyvavo bloke, pašalinamos iš „mempool“ sąrašo.

5. **Bloko įtraukimas į grandinę:**

   - `blockchain.add_block(new_block)`.

6. **Išvestis**
   - `mining_log.txt` — `Block ID`, `Difficulty`, `Nonce`, `Block Hash`.
   - `block_output.txt` — bloko santrauka ir (pasirinktinai) detali transakcijų informacija.

---

### 6) Santrauka (pseudokodas)

```

```
