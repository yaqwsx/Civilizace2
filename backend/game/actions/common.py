from __future__ import annotations

import contextlib
from decimal import Decimal
from typing import Any, Callable, Generator, Iterable, Mapping, Union

import boolean
from pydantic import BaseModel

from game.entities import Entity, EntityWithCost, Resource
from game.util import requirements_str


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

    def __init__(self, *msgs: Union[str, MessageBuilder]):
        super().__init__()
        for msg in msgs:
            self += msg

    def __iadd__(self, other: Union[str, MessageBuilder]) -> MessageBuilder:
        if isinstance(other, MessageBuilder):
            self.add(other.message)
        else:
            self.add(other)
        return self

    def add(self, message: str) -> None:
        if len(message) == 0:
            return
        if not self.empty:
            self.message += "\n\n"
        self.message += message

    @contextlib.contextmanager
    def startList(
        self, header: str = ""
    ) -> Generator[Callable[[str], None], None, None]:
        lines = []
        try:
            yield lambda x: lines.append(x)
        finally:
            if len(lines) > 0:
                if header != "":
                    self.add(header)
                self.addList(lines)

    def addList(self, items: list[str]) -> None:
        self.add("\n".join(["- " + x for x in items]))

    def addEntityDict(
        self, header: str, items: dict[Entity, Union[int, float, Decimal]]
    ):
        with self.startList(header) as addLine:
            for entity, amount in items.items():
                addLine(f"[[{entity.id}|{amount}]]")

    @property
    def empty(self) -> bool:
        return len(self.message) == 0


def printResourceListForMarkdown(
    resources: Mapping[Resource, Union[Decimal, int]],
    roundFunction: Callable[[Decimal], Any] = lambda x: x,
    *,
    header: str = "",
    emptyHeader: str = "",
) -> str:
    if len(resources) == 0:
        return emptyHeader
    message = MessageBuilder()
    with message.startList(header=header) as addLine:
        for resource, amount in resources.items():
            addLine(f"[[{resource.id}|{roundFunction(Decimal(amount))}]]")
    return message.message


def print_missing_requirements(
    entity: EntityWithCost, owned_entities: Iterable[EntityWithCost]
) -> str:
    if entity.requirements is None:
        return "Nemá požadavky"

    owned_ids = set(e.id for e in owned_entities)
    missing_req: boolean.Expression = entity.requirements.subs(
        {
            symbol: entity.requirements.TRUE
            for symbol in entity.requirements.get_symbols()
            if symbol.obj in owned_ids
        },
        simplify=True,
    )  # type: ignore

    if missing_req == missing_req.FALSE:
        return "Nelze splnit"

    if missing_req == missing_req.TRUE:
        return "Splněno"

    return requirements_str(missing_req, lambda id: f"[[{id}]]")
