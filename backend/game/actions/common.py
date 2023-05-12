from __future__ import annotations

import contextlib
from decimal import Decimal
from typing import Any, Callable, Dict, Generator, List, Set, Union

from pydantic import BaseModel, root_validator

from game.entities import Die, Entity, Resource


class ActionFailed(Exception):
    """
    Expects a pretty (markdown-formatted) message. This message will be seen
    by the user. That is raise ActionFailed(message)
    """

    def __init__(self, message: Union[str, MessageBuilder]):
        if isinstance(message, MessageBuilder):
            message = message.message
        super().__init__(message)


class MessageBuilder(BaseModel):
    """
    The goal is to simplify building markdown messages and not thinking about
    the whitespace. Adding to this creates new paragraph automatically.
    """
    message: str = ""

    def __iadd__(self, other: Any) -> MessageBuilder:
        if isinstance(other, MessageBuilder):
            other = other.message
        self.add(str(other))
        return self

    def add(self, message: str) -> None:
        if len(message) == 0:
            return
        if not self.empty:
            self.message += "\n\n"
        self.message += message

    @contextlib.contextmanager
    def startList(self, header: str = "") -> Generator[Callable[[str], None], None, None]:
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
            for entity, amount in items.items():
                addLine(f"[[{entity.id}|{amount}]]")

    @property
    def empty(self) -> bool:
        return len(self.message) == 0
