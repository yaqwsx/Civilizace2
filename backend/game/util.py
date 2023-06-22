from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from pydantic import BaseModel

from game.entities import Entity, EntityBase, EntityId

T = TypeVar("T")
U = TypeVar("U")
TEntity = TypeVar("TEntity", bound=Entity)
TModel = TypeVar("TModel", bound=BaseModel)
TNumber = TypeVar("TNumber", int, Decimal)


class FileCache:
    def __init__(self, cacheDirectory, suffix):
        self.cacheDirectory = Path(cacheDirectory).resolve()
        self.cacheDirectory.mkdir(exist_ok=True, parents=True)
        self.suffix = suffix

    def path(self, ident: str, renderer: Callable[[str], None]) -> Path:
        """
        Given an identifier and renderer (function that will fill content in the
        give file) return path to a file populated with the content.
        """
        cFile = self._cacheFile(ident)
        if not cFile.exists():
            renderer(str(cFile))
        return cFile

    def content(self, ident, renderer: Callable[[str], None]) -> bytes:
        cFile = self.path(ident, renderer)
        with open(cFile, "wb") as f:
            return f.read()

    def _cacheFile(self, ident):
        return self.cacheDirectory / f"{ident}.{self.suffix}"


def unique(values: Iterable[Any]) -> bool:
    return all(count <= 1 for count in Counter(values).values())


@overload
def get_by_entity_id(entity_id: EntityId, mapping: Mapping[TEntity, T]) -> Optional[T]:
    ...


@overload
def get_by_entity_id(
    entity_id: EntityId, mapping: Mapping[TEntity, T], default: U
) -> Union[T, U]:
    ...


def get_by_entity_id(
    entity_id: EntityId, mapping: Mapping[TEntity, T], default: U = None
) -> Union[T, Optional[U]]:
    entity: TEntity = EntityBase(id=entity_id, name="")  # type: ignore used only for eq
    return mapping.get(entity, default)


def sum_dict(amounts: Iterable[Tuple[T, TNumber]]) -> dict[T, TNumber]:
    result: dict[T, TNumber] = {}
    for key, amount in amounts:
        if key in result:
            result[key] += amount
        else:
            result[key] = amount
    return result
