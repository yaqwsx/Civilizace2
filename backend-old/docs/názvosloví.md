# Názvosloví

- `Action` je databázový model reprezentující herní akci zadanou týmem (např.
  Červení krmí)
- Každá instance `Action` má k sobě přidružené modely `ActionEvent`, které
  symbolizují to, že "tým akci započal", "tým akci zrušil", "tým akci dokončil"
  atd. Nejsou relevantní pro hru, jsou relevantní pro přehrávání historie.
- `ActionType` je enum definující, které všechny herní akce známe (např. Krmení,
  Zkoumání).
- Herní akce definované v `ActionType` jsou implementovány pomocí tříd v
  `game.models.actions`