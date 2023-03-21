from __future__ import annotations
from ctypes import Union

from decimal import Decimal
from game.entities import Entity, EntityId, Resource, Team
from typing import Dict, List, Any, Generator, Callable, Set, Iterable
from pydantic import BaseModel, root_validator, validator
import contextlib

class ActionFailed(Exception):
    """
    Expects a pretty (markdown-formatted) message. This message will be seen
    by the user. That is raise ActionFailed(message)
    """
    def __init__(self, message):
        if isinstance(message, MessageBuilder):
            super().__init__(message.message)
        super().__init__(message)

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
                if header != "":
                     self.add(header)
                self.addList(lines)


    def addList(self, items: List[str]) -> None:
        self.add("\n".join(["- " + x for x in items]))

    def addEntityDict(self, header: str, items: Dict[Entity, Union[int, float, Decimal]]):
        with self.startList(header) as addLine:
            for e, a in items.items():
                addLine(f"[[{e.id}|{a}]]")

    def addListItem(self, item: str) -> None:
        self.message += "\n- " + item

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
    resources: Dict[Resource, Decimal] = {}

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

    @property
    def productions(self):
        return {r: a for r, a in self.resources.items() if r.isProduction}

    @property
    def materials(self):
        return {r: a for r, a in self.resources.items() if r.isMaterial}

    def formatDice(self):
        # Why isn't this in entities?
        names = {
            "die-lesy": "Lesní kostka",
            "die-plane": "Planina kostka",
            "die-hory": "Horská kostka"
        }
        if self.requiredDots == 0:
            return "Akce nevyžaduje házení kostkou"
        builder = MessageBuilder()
        with builder.startList(f"Je třeba hodit {self.requiredDots} na jedné z:") as addDice:
            for d in self.allowedDice:
                addDice(names[d])
        return builder.message
