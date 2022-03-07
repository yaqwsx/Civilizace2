import enum


class Translations(enum.Enum):
    # TODO: Proc se nedaji pouzit v enumech?
    TECH_UNKNOWN = "Neznámý"
    TECH_VIDIBLE = "Viditelný"
    TECH_RESEARCHING = "Zkoumá se"
    TECH_OWNED = "Vyzkoumaný"
