# Chci implementovat hru, co pro to musím udělat?

- je vhodné načíst si něco o [Djangu](https://www.djangoproject.com/) - mají
  skvělý tutoriál pro začátečníky
- umět trochu HTML a přečíst si něco o [Tailwindu](https://tailwindcss.com/)
- a hlavně si přečíst texty níže

# Co je to hra?

Hra je definována pomocí akcí a stavu. Akce je tah (např. hřáčí krmí své lidi),
který ovlivní stav. Celá hra je tedy jen posloupnost akcí, kterou když postupně
aplikujeme na iniciální stav, tak dostaneme koncový stav. Když chceme zobrazit
uživateli hru, vyrobí nejnovější stav a ten nějak zobrazíme pomocí tzv. pohledů
(terminologie Djanga). Když chceme zadat akci

# O modelech v Djangu

Modelem je třída, jejíž instance můžeme ukládat do databáze. Dědí od
`django.models.Model` nebo podobné a obsahuje pole (fields). Poje jsou ty
položky, které za nás Django ukládá do databáze a umí je znovu načíst. Model je
také to, co se předává v pohledech do šablon. Model by měl implementovat
veškerou bussiness logiku celé aplikace. Model může mít extra metody a atributy,
které použijeme v šablonách (např. pro model obsahující pole s počtem mužů a žen
můžeme mít metodu, která nám vrátí počet lidí a tu zavolat v šabloně).

Třída modelu má v sobě položku `object`, která je tzv. managerem pro modely.
Umožňuje je vytahovat z databáze a vyrábět nové instance. Když modifikuji model,
změna se nepropaguje okamžitě do databáze. Je třeba model explicitně uložit
pomocí metody `save()`.

Pro účely Civilizace je implementována třída `ImmutableModel`, která má tu
vlastnost, že pokud v ní byly provedeny změny a byla zavolána metoda `save`, tak
ta neaktualizuje původní hodnoty v databázi, ale vytvoří nové. Tzn. jakmile se
položka jednou uloží do databáze, už ji není možné změnit (a smazat). To je
užitečné např. při ukládání historie stavů.

## Důležité postřehy

- pokud změníš nějaký model, je třeba vyrobit migraci `python manage.py
  makemigration` a spustit ji `python manage.py migrate`

# O pohledech v Djangu

Pohled v Djangu je třída (dědící od `django.view.View`), která má za úkol
připravit HTML stránku a předat ji uživateli. Definuje metody `get` a `post`,
které jsou zavolány, kdy uživatel k danému pohledu přistupuje (`get`) nebo do
něj posílá data (`post`).

Co zpravidla pohled udělá? Pomocí managerů vytáhne z databáze potřebná data,
nastrká je do kontextu (slovník) a pomocí `render_template` vykreslí šablonu a
výsledek vrátí. Případně může uživatele přesměrovat na jiný pohled pomocí
`redirect`

A jak uživatel může přistoupit k pohledu? Je třeba se podívat do souboru
`urls.py`, která definuje URL naší aplikace a přiřazuje k nim pohledy. V URL
můžou být nějaké paramety, které se předají jako argumenty funkcím `get` a
`post`.

## Důležité postřehy

- všechny pohledy v civilizaci musí dostat v kontextu aktuální požadavek jako
  klíč `requiest` a aktuální zprávy uživateli jako klíč `messages`. Pro detaily
  se podívej na existující pohledy.
-

# O formulářích v Djangu

V Djangu je možné vyrobit třídu formuláře, která má políčka s nějakými
vlastnostmi (zjednodušeno). Django poté automaticky umí:

- vykreslit formulář jako HTML včetně validace vstupu u uživatele
- zvalidovat formulář na základě POST data a vyrobit tzv. vyčitěné hodnoty

Více detailů v [dokumentaci](https://docs.djangoproject.com/en/3.0/topics/forms/).

# Co je to herní stav a jak ho rozšířit?

Stav je model, který si pamatuje odkazy na "podstavy" (stav světa a stav pro
každý tým) + akci, která ho vyrobila. Zpravidla bude struktura vypadat tak, že:

- Stav
    - akce
    - stav světa
        - modul světa 1
            - JSON s daty
        - modul světa 2
            - JSON s daty
    - [stav týmu] - "pole"
        - odkaz na model týmu
        - modul týmu 1
            - JSON s daty
        - modul týmu 2
            - JSON s daty

Když vytváříš nový modul, poděd od `ImmutableModel` a implementuje veškerou
funkcionalitu, kterou potřebuješ. Např. obchodní modul by měl implementovat
metodu, která realizuje obchod mezi dvěma týmy. Zároveň pokud budeme chtít
prezentovat v šabloně např. seznam posledních 5 obchodů, vyrobíme metodu, která
**nebere žádné argumenty** (kromě self) a vrací seznam těchto 5 ochodů.

## Důležité postřehy

- všechny stavy musí dědit od `ImmutableModel`
- pokud potřebuješ ukládat různě strukturovaná data, použij `JSONField`
- na svém stavu implementuj metodu `sane`, která vrací dvojici `(bool, str)`,
  kde první prvek je true pokud je stav v pořádku (včetně podstavů) a druhý
  prvek obsahuje dodatečný komentář (zejména to **proč** stav není v pořádku).
  Metoda sane by měla rekurzivně volat sane na podstavech. Je dobré, aby vracela
  chyby ze všech podstavů.

# Co je to akce a jak ji vyrobit?

