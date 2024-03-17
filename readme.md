![Backend: Build & Test Badge](https://github.com/Ondraceq/civilizace3/actions/workflows/backend-build-test.yml/badge.svg)
![Backend: Coverage Badge](https://img.shields.io/badge/Backend:_Coverage-0-red.svg)

# Civilizační informační systém

Tento repozitář obsahuje vše relevantní k informačnímu systému pohánějící
instruktorskou akci Příběh civilizace.

## Příprava prostředí

```
$ conda env create -f conda-env.yml
$ conda activate civilizace
```

## Aktualizace prostředí (po změně conda-env.yml)

```
$ conda env update --file conda-env.yml --prune
```

## Jak to spustit:

### Jak spustit backend civilizace?

- pracovní adresář `backend`
- opatři si soubor `gauth.json` z našeho drivu - obsahuje přístupové klíče ke
  Google tabulkám. Umísti ho do kořenového adresáře backendu.
  - pokud chceš, můžeš soubor umístit kamkoliv a nastavit proměnnou prostředí
    `CIVILIZACE_GAUTH_FILE` na cestu k němu.
- stáhni si entity `python manage.py pullentities`. Entity jsou uloženy v
  `data/entities`
- zresetuj hru pomocí `scripts/resetGame.sh TEST` (na Windows `scripts/resetGame.bat TEST`)

  - to vytvoří databázi a aplikuje migrace. TEST je název sady entit

- funguj úplně normálně jako s Djangem
  - tj. zejména chceš `python manage.py runserver`

### Jak spustit frontend

- pracovní adresář `frontend`
- spusť `npm install`
- spusť `npm run start`

## Jak se to má s migracemi databází na backendu

Django spravuje migrace, ale při vývoji se pohybujeme velmi rychle a hlavně s
sebou netáhneme produkční databázi. V rámci jednoduchosti a rychlosti existuje
skript `scripts/resetGameHard.sh` (na Windows `scripts/resetGameHard.bat`),
který zruší aktuální migrace, vygeneruje nové a zinicializuje hru.
