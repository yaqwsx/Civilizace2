# Jak spustit backend civilizace?

- vytvoř virtuální prostředí (`python3 -m venv venv`)
- spusť virtuální prostřed (na UNIX systémech `. venv/bin/activate`)
- nainstaluj závislosti: `pip install -r requirements.txt`
- opatři si soubor `gauth.json` z našeho drivu - obsahuje přístupové klíče ke
  Google tabulkám. Umísti ho do kořenového adresáře backendu.
    - pokud chceš, můžeš soubor umístit kamkoliv a nastavit proměnnou prostředí
      `CIVILIZACE_GAUTH_FILE` na cestu k němu.
- zresetuj hru pomocí `scripts/resetGame.sh` - to vytvoří databázi a aplikuje
  migrace.
- funguj úplně normálně jako s Djangem.

## Jak se to má s migracemi

Django spravuje migrace, ale při vývoji se pohybujeme velmi rychle a hlavně s
sebou netáhneme produkční databázi. V rámci jednoduchosti a rychlosti existuje
skprit `scripts/resetGameHard.sh`, který zruší aktuální migrace, vygeneruje nové
a zinicializuje hru.

