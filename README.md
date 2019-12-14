# Civilizace2

Herní systém pro druhý ročník Civilizace

# Jak to rozběhnout?

- mít nainstalovaný Python 3
- nainstalovat závislosti: v adresáři projektu zavolej `pip install -r
  requirements.txt` nebo `pip3 install -r requirements.txt` (záleží, jaký alias
  máš pro Python 3)
- zmigruj databázi: v adresáři projektu zavolej `python manage.py migrate` nebo
  `python3 manage.py migrate`
- nakrm databázi výchozími daty: v adresáři projektu zavolej `python manage.py
  create groups users state` nebo `python3 manage.py create groups users state`
- spusť vývojový server: v adresáři projektu zavolej `python manage.py
  runserver` nebo `python3 manage.py runserver`
- otevři v prohlížeči [http://localhost:8000](http://localhost:8000)
- seznam uživatelů najdeš v `game/management/commands/create.py`, všichni mají
  heslo "password"

# Jak vyvíjet

## Udělal jsem změny v databázových modelech

- zavolej `python manage.py makemigrations` a pak `python manage.py migrate`

## Pullnul jsem novou verzi

- ta mohla změnit DB modely, zavolej `python manage.py migrate`

## Chci resetovat hru

- zavolej `python manage.py create state`

## Něco jsem pokazil a chci kompletně resetovat databázi

- smaž soubor `db.sqlite3` a postupuj podle "Jak to rozběhnout?"