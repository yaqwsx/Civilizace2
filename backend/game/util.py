from decimal import Decimal
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, TypeVar, Union, overload
from entities import EntityBase, EntityId, Entity, Resource

T = TypeVar("T")
U = TypeVar("U")
TEntity = TypeVar("TEntity", bound=Entity)


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
