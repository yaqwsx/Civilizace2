from __future__ import annotations

from decimal import Decimal
from game.entities import EntityId, ResourceBase
from typing import Dict, List, Any, Generator, Callable, Set, Iterable
from pydantic import BaseModel, root_validator, validator
import contextlib

from game.entityParser import DICE_IDS

class MessageBuilder(BaseModel):
    """
    The goal is to simplify building markdown messages and not thinking about
    the whitespace. Adding to this creates new paragraph automatically.
    """
    message: str=""

    def __iadd__(self, other: Any) -> MessageBuilder:
        self.add(str(other))
        return self

    def add(self, message: str) -> None:
        if message == None:
            return
        if len(self.message) > 0:
            self.message += "\n\n"
        self.message += message

    @contextlib.contextmanager
    def startList(self, header: str) -> Generator[Callable[[str], None], None, None]:
        lines = []
        try:
            yield lambda x: lines.append(x)
        finally:
            if len(lines) > 0:
                self.add(header)
                self.addList(lines)


    def addList(self, items: List[str]) -> None:
        self.add("\n".join(["- " + x for x in items]))

    def addListItem(self, item: str) -> None:
        self.message += "\n" + item

    @property
    def empty(self) -> bool:
        return len(self.message) == 0

class ActionException(Exception):
    pass

class DebugException(Exception):
    pass

class ActionCost(BaseModel):
    allowedDice: Set[str] = set()
    requiredDots: int = 0
    postpone: int = 0
    resources: Dict[ResourceBase, Decimal] = {}
    
    @validator("allowedDice")
    def validateDice(cls, v: Iterable[str]) -> Set[str]:
        ALLOWED_DICE = DICE_IDS
        dice = set(v)
        for d in dice:
            if d not in ALLOWED_DICE:
                raise ValueError(f"Kostka {d} není dovolena. Dovolené kostky: {','.join(ALLOWED_DICE)}")
        return dice


    @root_validator
    def validate(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        allowedDice = values.get("allowedDice", [])
        requiredDots = values.get("requiredDots", 0)
        if requiredDots < 0:
            raise ValueError("Nemůžu chtít záporně mnoho puntíků")
        if requiredDots == 0 and len(allowedDice) > 0:
            raise ValueError("Nemůžu mít povolené kostky a chtít 0 puntíků")
        if requiredDots > 0 and len(allowedDice) == 0:
            raise ValueError("Nemůžu chtít puntíky a nespecifikovat kostky")
        return values


