from __future__ import annotations
from functools import cached_property
import math
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

from game.state import PlagueStats

class PlagueWord(BaseModel):
    word: str
    slug: Optional[str]
    alias: Optional[str]

    def __eq__(self, other):
        return isinstance(other, PlagueWord) and self.word == other.word

class PlagueSheet(BaseModel):
    name: str
    sentences: List[str]
    words: List[PlagueWord]
    map: str

class PlagueSentence(BaseModel):
    name: str
    words: List[PlagueWord]
    recoveryDiff: float
    mortalityDiff: float
    infectiousnessDiff: float


class PlagueData(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    words: Dict[str, PlagueWord]
    sheets: List[PlagueSheet]
    sentences: List[PlagueSentence]

    @cached_property
    def slugToWordMapping(self):
        mapping = {}
        for word in self.words.values():
            if word.slug is not None:
                mapping[word.slug] = word
            if word.alias is not None:
                mapping[word.alias] = word
        return mapping

    def getMatchingSentence(self, words: List[str]) -> PlagueSentence:
        try:
            words = [self.slugToWordMapping(w) for w in words]
        except KeyError:
            return None
        for s in self.sentences:
            if s.words == words:
                return s
        return None


def readPlagueFromEntities(sheets) -> PlagueData:
    words = readPlagueWords(sheets["mezihra-slova"])
    sentences = readPlagueSentences(sheets["mezihra-vety"], words)
    sheets = readPlagueSheets(sheets["mezihra-listy"], words)

    return PlagueData(words=words, sentences=sentences, sheets=sheets)

def readPlagueWords(sheet) -> Dict[str, PlagueWord]:
    words = {}
    for row in sheet[1:]:
        if len(row) == 0 or len(row[0]) == 0:
            continue
        word = row[0].upper()
        slug = None if len(row[1]) == 0 else row[1].upper()
        alias = None if len(row[2]) == 0 else row[2]
        words[word] = PlagueWord(word=word, slug=slug, alias=alias)
    return words

def readPlagueSentences(sheet, words) -> List[PlagueSentence]:
    sentences = []
    for row in sheet[1:]:
        if len(row) == 0 or len(row[4]) == 0:
            continue
        name = row[4]
        wordString = "".join([x for x in name if x.isupper() or x.isspace()])
        try:
            sWords = [words[x.strip()] for x in wordString.split(" ") if len(x.strip()) != 0]
        except KeyError as e:
            raise RuntimeError(f"Nemůžu nalézt slovo moru {e} z věty {name}") from None
        recoveryDiff = float(row[5])
        mortalityDiff = float(row[6])
        infectiousnessDiff = float(row[7])
        sentences.append(PlagueSentence(name=name, words=sWords,
            recoveryDiff=recoveryDiff, mortalityDiff=mortalityDiff, infectiousnessDiff=infectiousnessDiff))
    return sentences

def readPlagueSheets(sheet, words) -> List[PlagueSheet]:
    sheets = []
    for row in sheet[1:]:
        if len(row) == 0 or len(row[0]) == 0:
            continue
        try:
            sheets.append(PlagueSheet(
                name=row[0],
                sentences=row[1:4],
                words=[words[w.strip()] for w in row[4:6]],
                map=row[6]
            ))
        except KeyError as e:
            raise RuntimeError(f"Nemůžu nalézt slovo moru {e} z listu {row}") from None
    return sheets


def simulatePlague(stats: PlagueStats, population: int) -> Tuple[PlagueStats, int]:
    """
    Given the state of the plague and total population, compute a new state and
    return the number of newly dead people.
    """
    contacts = math.ceil(stats.sick * stats.infectiousness)
    newlyInfected = round(contacts * (population - stats.immune - stats.sick) / population)

    cured = math.floor((stats.sick + newlyInfected) * stats.recovery)
    dead = math.floor((stats.sick + newlyInfected) * stats.mortality)

    return PlagueStats(
        sick=stats.sick + newlyInfected - cured - dead,
        immune=stats.immune + cured,
        recovery=stats.recovery,
        mortality=stats.mortality,
        infectiousness=stats.infectiousness
    ), dead

def getDeathToll(stats: PlagueStats, population: int) -> int:
    """
    Given current statistics, compute how much people will die
    """
    deadTotal = 0
    for i in range(80):
        nextstats, dead = simulatePlague(stats, population)
        deadTotal += dead
        population = max(0, population - dead)
        stats = nextstats
    return deadTotal
