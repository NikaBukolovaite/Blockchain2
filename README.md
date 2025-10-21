# 💻 Blockchain

Šioje programoje realizuota supaprastinta **blokų grandinė\***, imituojanti jos veikimą realiomis sąlygomis.

Ši programa sugeneruoja vartotojus ir transakcijas, iš pasirinktų transakcijų formuoja blokus, apskaičiuoja jų Merkle šaknį ir kasa blokus Proof-of-Work principu, kol bloko antraštės maiša atitinka nustatytą sudėtingumą. Visi maišavimai (vartotojų UTXO, transakcijų ID, Merkle sujungimai ir bloko antraštės hash) atliekami naudojant užduotyje pateiktą AES pagrindu sukurtą maišos funkciją. Iškasus bloką, transakcijos įrašomos į Body, atnaujinami UTXO gavėjams, o blokas su savo Header (version, previous hash, timestamp, merkle root, nonce, difficulty) prijungiamas prie grandinės. Rezultatai išvedami į konsolę ir į tekstinius žurnalus (blokų turinys ir kasimo ataskaitos).

**\*Blokų grandinė** yra nuoseklus blokų sąrašas, kuriame kiekvienas blokas susietas su ankstesnio bloko maišos reikšme (hash).

# 📃 Naudojimo instrukcijos

## Programos paleidimas

```bash
python blokas.py [FLAGAI...]
```

## Galimi flag'ai

| Flag               | Reikšmė                                  | Numatytoji reikšmė | Pastabos                                                                |
| ------------------ | ---------------------------------------- | ------------------ | ----------------------------------------------------------------------- |
| `--users=INT`      | Sugeneruojamų vartotojų skaičius         | `1000`             | Labai didelės reikšmės (pvz., 1 000 000) naudos daug RAM/CPU.           |
| `--tx=INT`         | Sugeneruojamų transakcijų skaičius       | `10000`            |                                                                         |
| `--block-size=INT` | Transakcijų sk. viename bloke            | `100`              | Kiekvienam blokui imama iki `block-size` **atsitiktinių** transakcijų.  |
| `--difficulty=INT` | PoW sudėtingumas (nuliai hash pradžioje) | `3`                | Pvz., `3` → bloko hash prasideda bent `000…`. Didesnė reikšmė – lėčiau. |
| `--append`         | Rašymo režimas: **pridėti** prie failų   | —                  | Jei nenurodoma nieko – veikia kaip `overwrite` (perrašo).               |
| `--overwrite`      | Rašymo režimas: **perrašyti** failus     | **įjungta**        | Pagal nutylėjimą prieš startą failai išvalomi.                          |
