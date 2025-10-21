# 💻 Blockchain (v1.0 / v0.1)

Supaprastinta **blokų grandinė**, imituojanti UTXO modelį, transakcijų atranką į blokus, Merkle šaknį ir Proof‑of‑Work (PoW) kasimą. Visos maišos daromos su užduotyje pateikta **AES pagrindu sukurta maišos funkcija**.

---

## 🧭 Turinys

- [Apžvalga](#apžvalga)
- [Funkcijos](#funkcijos)
- [Ekrano nuotraukos ir demonstracija](#ekrano-nuotraukos-ir-demonstracija)
- [Architektūra](#architektūra)
- [Diegimas ir paleidimas](#diegimas-ir-paleidimas)
- [Konfigūracija (CLI flag'ai)](#konfigūracija-cli-flagai)
- [Rezultatai ir log'ai](#rezultatai-ir-logai)
- [Kaip tai veikia](#kaip-tai-veikia)

---

## Apžvalga

Programa generuoja vartotojus (UTXO mozaika), kuria atsitiktines transakcijas, formuoja blokus, apskaičiuoja **Merkle root** ir kasa blokus pagal **PoW**: kol bloko antraštės maiša prasideda `difficulty` nuliais. Patvirtinus bloką atnaujinamos UTXO būsenos.

---

## Funkcijos

- ✅ **UTXO modelis** su grąža siuntėjui.
- ✅ **Transakcijų ID** iš kanonizuotos reprezentacijos per `aes_hashing()`.
- ✅ **Merkle root** su poravimu ir dubliavimu nelyginiam kiekiui.
- ✅ **PoW kasimas** su `difficulty` nuliais hash pradžioje.
- ✅ **Dviginės panaudos prevencija** kasimo metu (tikrinami įėjimo UTXO egzistavimai).
- ✅ **Žurnalai**: konsolėje ir tekstiniuose failuose.
- ➕ Pasirenkamas transakcijų „dump'as“ į failą (jei įjungta).

---

## Ekrano nuotraukos ir demonstracija

**Konsolės eiga (kasimas):**

<p align="center">
  <img src="docs/images/mining_console.png" alt="Kasimo eiga – konsolė" width="780" />
</p>

**Failų išvestys:**

<div align="center">
  <img src="docs/images/mining_log_excerpt.png" alt="mining_log.txt ištrauka" width="380" />
  <img src="docs/images/block_output_excerpt.png" alt="block_output.txt ištrauka" width="380" />
</div>

---

## Architektūra

- **User** – vardas, `public_key` (iš `aes_hashing`), privatūs UTXO ir balansas.
- **Transaction** – `sender`, `receiver`, `amount`, `inputs`, `outputs`, `tx_nonce`, `transaction_id`.
- **Block** – `block_id`, `prev_block_hash`, `timestamp`, `version`, `merkle_root`, `nonce`, `difficulty`, transakcijų sąrašas.
- **Blockchain** – blokų seka ir pagalbinės funkcijos (`get_last_hash`, `add_block`).
- **Merkle** – poruojami TX ID (`hex` → `bytes`), dubliuojamas paskutinis, kol lieka šaknis.
- **PoW** – `calculate_hash()` virš 6 antraštės laukų; ieškoma `0...` prefikso.

---

## Diegimas ir paleidimas

**Reikalavimai:**

> Pastaba: išvesties failai perrašomi su `--overwrite`, o su `--append` – pildomi toliau.

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

```
Kasamas blokas 1 su 100 transakciju...
Blokas iskastas! Nonce=48217 Hash=000a4f2c...e19
```

---

## Kaip tai veikia

1. **Duomenų generavimas:** `generate_users()` ir `generate_transactions()`.
2. **Bloko kandidatūra:** `create_new_block()` parenka iki `block-size` transakcijų.
3. **Merkle root:** `calculate_merkle_root()`.
4. **Kasimas:** `calculate_hash()` per 6 header laukus; didinamas `nonce`.
5. **Patvirtinimas:** tikrinami input UTXO, atnaujinami UTXO pagal outputs, blokas pridedamas į grandinę.
