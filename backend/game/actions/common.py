from __future__ import annotations
from argparse import ArgumentError

from decimal import Decimal
from game.state import TeamId
from game.entities import EntityId
from typing import Dict, List, Any, Union, Generator, Callable
from pydantic import BaseModel
import contextlib

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
    def __init__(self, msg: Union[str, MessageBuilder]) -> None:
        if isinstance(msg, MessageBuilder):
            super().__init__(msg.message)
        else:
            super().__init__(msg)


class ActionCost(BaseModel):
    allowedDice: set[str] = set()
    requiredDots: int = 0
    postpone: int = 0
    resources: Dict[EntityId, Decimal]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.validate()

    def validate(self) -> None:
        if (self.requiredDots == 0) != (len(self.allowedDice) == 0):
            raise ArgumentError("Requiring " + self.requiredDots + " dots on dice " + self.allowedDice)
        


class GlobalActionArgs(BaseModel):
    pass

class TeamActionArgs(BaseModel):
    teamId: TeamId

