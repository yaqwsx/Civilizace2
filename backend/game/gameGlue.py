import enum
import typing
from decimal import Decimal
from typing import Any, Iterable, Optional, Type

import boolean
from pydantic import BaseModel
from pydantic.fields import (
    MAPPING_LIKE_SHAPES,
    SHAPE_LIST,
    SHAPE_SET,
    SHAPE_SINGLETON,
    ModelField,
)

from game.actions.actionBase import ActionArgs
from game.entities import Entities, EntityBase
from game.state import StateModel
from game.util import TModel, unique


class UnexpectedValueType(Exception):
    def __init__(
        self,
        value: Any,
        expectedType: Type,
        allowedTypes: Iterable[Type],
        *args,
        **kwargs,
    ):
        super().__init__(
            f"Unexpected value type '{type(value)}' for {expectedType} (allowed types: {', '.join(allowedTypes)})",
            *args,
            **kwargs,
        )
        self.value = value
        self.expectedType = expectedType
        self.allowedTypes = allowedTypes


def stateSerialize(model: BaseModel) -> dict[str, Any]:
    """
    Turn the model into a dictionary representation
    """
    return {
        field.name: _serialize_any(getattr(model, field.name))
        for field in model.__fields__.values()
    }


def _serialize_any(what: Any):
    if isinstance(what, EntityBase):
        return what.id
    if isinstance(what, StateModel) or isinstance(what, ActionArgs):
        return stateSerialize(what)
    if isinstance(what, enum.Enum):
        return what.value
    if isinstance(what, Decimal):
        return str(what)
    if isinstance(what, list):
        return [_serialize_any(x) for x in what]
    if isinstance(what, set):
        items = [_serialize_any(x) for x in what]
        items.sort()
        return items
    if isinstance(what, tuple):
        return tuple(_serialize_any(x) for x in what)
    if isinstance(what, dict):
        return {_serialize_any(k): _serialize_any(v) for k, v in what.items()}
    assert isinstance(
        what, str | int | type(None)
    ), f"Unexpected type {type(what)} during serialization"
    return what


def stateDeserialize(
    cls: Type[TModel], data: dict[str, Any], entities: Entities
) -> TModel:
    """
    Turn dictionary representation into a model
    """
    source: dict[str, Any] = {}
    for field in cls.__fields__.values():
        if field.name in data:
            source[field.name] = _deserialize_any(data[field.name], field, entities)
        elif field.required:
            raise RuntimeError(f"Field {field.name} required, but not provided")
    # TODO: check impact of `cls.validate(source)` on performance (would be the prefered way)
    return cls.construct(**source)


def _deserialize_any(data: Any, field: ModelField, entities: Entities) -> Any:
    if not field.required and data is None:
        return None
    if field.shape == SHAPE_SINGLETON:
        return _deserialize_singleton(data, field.type_, entities)
    if field.shape in MAPPING_LIKE_SHAPES:
        assert field.key_field is not None

        if not isinstance(data, dict):
            raise UnexpectedValueType(data, field.outer_type_, [dict], field=field)
        return {
            _deserialize_any(k, field.key_field, entities): _deserialize_singleton(
                v, field.type_, entities
            )
            for k, v in data.items()
        }
    if field.shape == SHAPE_LIST:
        if not isinstance(data, list):
            raise UnexpectedValueType(data, field.outer_type_, [list], field=field)
        return [_deserialize_singleton(x, field.type_, entities) for x in data]
    if field.shape == SHAPE_SET:
        if not isinstance(data, (set, list)):
            raise UnexpectedValueType(data, field.outer_type_, [set, list], field=field)
        if not isinstance(data, set) and not unique(data):
            raise RuntimeError(
                f"Expected set for {field.outer_type_}, but got list with duplicate elements ({', '.join(data)})"
            )
        return set(_deserialize_singleton(x, field.type_, entities) for x in data)
    assert (
        False
    ), f"Deserializing shape type {field.shape} not implemented (field={field})"


def _deserialize_generic(data: Any, generic: Type, entities: Entities) -> Any:
    origin = typing.get_origin(generic)
    assert origin is not None
    if issubclass(origin, set):
        if not isinstance(data, (set, list)):
            raise UnexpectedValueType(data, generic, [set, list])
        if not isinstance(data, set) and not unique(data):
            raise RuntimeError(
                f"Expected set for {generic}, but got list with duplicate elements ({', '.join(data)})"
            )
        (type_arg,) = typing.get_args(generic)
        return set(_deserialize_singleton(x, type_arg, entities) for x in data)
    if issubclass(origin, list):
        if not isinstance(data, list):
            raise UnexpectedValueType(data, generic, [list])
        (type_arg,) = typing.get_args(generic)
        return [_deserialize_singleton(x, type_arg, entities) for x in data]
    if issubclass(origin, dict):
        if not isinstance(data, dict):
            raise UnexpectedValueType(data, generic, [dict])
        (key_arg, value_arg) = typing.get_args(generic)
        return {
            _deserialize_singleton(k, key_arg, entities): _deserialize_singleton(
                v, value_arg, entities
            )
            for k, v in data.items()
        }
    assert False, f"Deserializing generic type {generic} not implemented"


def _deserialize_singleton(
    data: Optional[Any], expectedType: Type, entities: Entities
) -> Any:
    if typing.get_origin(expectedType) is not None:
        return _deserialize_generic(data, expectedType, entities)
    assert isinstance(expectedType, type), "expectedType has to be type or generic type"
    if issubclass(expectedType, StateModel) or issubclass(expectedType, ActionArgs):
        if not isinstance(data, dict):
            raise UnexpectedValueType(data, expectedType, [dict])
        if not all(isinstance(name, str) for name in data):
            raise RuntimeError("Unexpected type of field name")
        return stateDeserialize(expectedType, data, entities)
    if issubclass(expectedType, EntityBase):
        assert expectedType != EntityBase, "Don't deserialize EntityBase"
        if not isinstance(data, str):
            raise UnexpectedValueType(data, expectedType, [str])
        if data in entities:
            entity = entities[data]
        else:
            raise RuntimeError(f"Could not find entity with id '{data}'")
        if not isinstance(entity, expectedType):
            raise RuntimeError(f"Entity {entity} is not {expectedType}")
        return entity
    if issubclass(expectedType, enum.Enum):
        if not isinstance(data, (str, int)):
            raise UnexpectedValueType(data, expectedType, [str, int])
        if isinstance(data, str):
            return expectedType._member_map_[data]
        return expectedType(data)
    if issubclass(expectedType, bool):
        if isinstance(data, str):
            raise RuntimeError("Type bool can't be deserialized from str")
        if not isinstance(data, int):
            raise UnexpectedValueType(data, expectedType, [int])
        return expectedType(data)
    assert not issubclass(expectedType, float), "Don't use float, use Decimal instead"
    assert issubclass(
        expectedType, (int, Decimal, str)
    ), f"Unexpected type {expectedType}"

    if not isinstance(data, (str, int)):
        raise UnexpectedValueType(data, expectedType, [str, int])
    return expectedType(data)


def serializeEntity(
    entity: EntityBase, extraFields: dict[str, Any] = {}
) -> dict[str, Any]:
    """
    Args:
    - a serialization function that takes field name and field value and returns
      serialized field value. If none is returned, the value is not included in
      the result
    - a function that returns extra fields for the model

    Returns:
        a dictionary that represents the serialized entity
    """
    result: dict[str, Any] = {}
    for field, value in entity:
        if field not in ["role", "password", "visible"]:
            result[field] = _shallow_entity(value)
    fields_count = len(result)
    result.update(extraFields)
    assert len(result) == fields_count + len(extraFields)
    return result


def _shallow_entity(e: Any) -> Any:
    """
    Given an entity, or a tuple of entities, make them shalow - represent them
    only by ID
    """
    if isinstance(e, EntityBase):
        return e.id
    if isinstance(e, tuple):
        return tuple(map(_shallow_entity, e))
    if isinstance(e, list):
        return list(map(_shallow_entity, e))
    if isinstance(e, set):
        return set(map(_shallow_entity, e))
    if isinstance(e, dict):
        return {_shallow_entity(k): _shallow_entity(v) for k, v in e.items()}
    if isinstance(e, boolean.Expression):
        return str(e.simplify())
    assert isinstance(e, str | int | Decimal | type(None))
    if isinstance(e, Decimal):
        return str(e)
    return e
