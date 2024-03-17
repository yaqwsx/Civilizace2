import dataclasses
import enum
import typing
from decimal import Decimal
from typing import Any, Callable, Iterable, Optional, Type, Union

import boolean
from pydantic import BaseModel
import pydantic
from pydantic.fields import FieldInfo

from game.actions.actionBase import ActionArgs
from game.entities import Entities, EntityBase
from game.state import StateModel
from game.util import T, TModel, U, unique


JsonSerializable = Union[
    str,
    int,
    bool,
    type(None),
    list["JsonSerializable"],
    tuple["JsonSerializable", ...],
    dict[str, "JsonSerializable"],
    dict["JsonSerializable", "JsonSerializable"],
]


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
            f"Unexpected value type '{type(value)}' for {expectedType} (allowed types: {', '.join(str(allowedTypes))})",
            *args,
            **kwargs,
        )
        self.value = value
        self.expectedType = expectedType
        self.allowedTypes = allowedTypes


class Serializer:
    def serialize_to_json(self, value: Any) -> JsonSerializable:
        if isinstance(value, EntityBase):
            return self.serialize_entity(value)
        return self.serialize_with_shallow_entities(value)

    def serialize(self, value: Any) -> JsonSerializable:
        if isinstance(value, EntityBase):
            return self.serialize_entity(value)
        return self.serialize_with_shallow_entities(value)

    def serialize_entity_with_extra(
        self, entity: EntityBase, extra_fields: dict[str, Any]
    ) -> dict[str, JsonSerializable]:
        """
        Args:
        - a serialization function that takes field name and field value and returns
          serialized field value. If none is returned, the value is not included in
          the result
        - a function that returns extra fields for the model

        Returns:
            a dictionary that represents the serialized entity
        """
        result = self.serialize_entity(entity)
        fields_count = len(result)
        result.update(
            {k: self.serialize_with_shallow_entities(v) for k, v in extra_fields}
        )
        assert len(result) == fields_count + len(extra_fields)
        return result

    def serialize_entity(self, entity: EntityBase) -> dict[str, JsonSerializable]:
        """Turn the entity into a dictionary representation"""
        return {k: self.serialize_with_shallow_entities(v) for k, v in entity}

    def serialize_with_shallow_entities(self, value: Any) -> JsonSerializable:
        if isinstance(value, EntityBase):
            return value.id
        return self._serialize_recursively(value, self.serialize_with_shallow_entities)

    def _serialize_recursively(
        self,
        value: Any,
        inner_serialize: Callable[[Any], JsonSerializable],
    ) -> JsonSerializable:
        """Calls `inner_serialize` on inner fields of structured types

        Example usage:
        ```{py}
        def my_serialize(value: Any) -> JsonSerializable:
            if isinstance(value, MySpecialType):
                return my_custom_serialize(value)
            return ser._serialize_recursively(value, my_serialize)
        ```
        """
        if isinstance(value, BaseModel):
            return {k: inner_serialize(v) for k, v in value}
        if dataclasses.is_dataclass(value):
            return {k: inner_serialize(v) for k, v in dataclasses.asdict(value)}
        if isinstance(value, list):
            return [inner_serialize(x) for x in value]
        if isinstance(value, set):
            return [inner_serialize(x) for x in sorted(value)]
        if isinstance(value, tuple):
            return tuple(inner_serialize(x) for x in value)
        if isinstance(value, dict):
            return {inner_serialize(k): inner_serialize(v) for k, v in value.items()}
        return self._value_to_serializable(value)

    def _value_to_serializable(self, value: Any) -> JsonSerializable:
        if isinstance(value, enum.Enum):
            return value.value
        if isinstance(value, Decimal):
            return str(value)
        assert isinstance(
            value, str | int | bool | type(None)
        ), f"Unexpected type {type(value)} during serialization"
        return value


class Deserializer:
    def __init__(self, entities: Optional[Entities]) -> None:
        self.entities = entities
        super()

    def deserialize(self, cls: type[T], data: Any) -> T:
        if issubclass(cls, EntityBase):
            return self.deserialize_entity(cls, data)
        return self.deserialize_with_shallow_entities(cls, data)

    def deserialize_entity(self, cls: type[TModel], data: dict[str, Any]) -> TModel:
        """Turn a dictionary representation into the model"""
        return cls(
            **{
                k: self._deserialize_model_field(
                    cls.model_fields.get(k), v, self.deserialize_with_shallow_entities
                )
                for k, v in data
            }
        )

    def _deserialize_entity_from_any(self, cls: type[TModel], data: Any) -> TModel:
        if not isinstance(data, dict):
            raise UnexpectedValueType(data, cls, [dict])
        if not all(isinstance(name, str) for name in data):
            raise RuntimeError(
                f"Unexpected type of field name (one of: {tuple(data.keys())!r})"
            )
        return self.deserialize_entity(cls, data)

    # Returns `data` if `field` is None
    def _deserialize_model_field(
        self,
        field: FieldInfo | None,
        data: Any,
        inner_deserialize: Callable[[type[T], Any], T],
    ) -> Any:
        if field is None:
            return data
        field_type: Any = field.annotation
        return inner_deserialize(field_type, data)

    def deserialize_with_shallow_entities(self, cls: type[T], data: Any) -> T:
        if isinstance(cls, type) and issubclass(cls, EntityBase):
            assert cls != EntityBase, "Don't deserialize EntityBase"
            if not isinstance(data, str):
                raise UnexpectedValueType(data, cls, [str])
            if self.entities is None:
                raise RuntimeError("Cannot deserialize shallow entity without entities")
            entity = self.entities.get(data)
            if entity is None:
                raise RuntimeError(f"Could not find entity with id {data!r}")
            if not isinstance(entity, cls):
                raise RuntimeError(f"Entity {entity!r} is not {cls}")
            return entity
        return self._deserialize_recursively(
            cls, data, self.deserialize_with_shallow_entities
        )

    def _deserialize_recursively(
        self,
        cls: type[T],
        data: Any,
        inner_deserialize: Callable[[type[U], Any], U],
    ) -> T:
        """Calls `inner_serialize` on inner fields of structured types

        Example usage:
        ```{py}
        def my_serialize(value: Any) -> JsonSerializable:
            if isinstance(value, MySpecialType):
                return my_custom_serialize(value)
            return ser._serialize_recursively(value, my_serialize)
        ```
        """
        if isinstance(cls, type) and issubclass(cls, BaseModel):
            if not isinstance(data, dict):
                raise UnexpectedValueType(data, cls, [dict[str, Any]])
            if not all(isinstance(name, str) for name in data):
                raise RuntimeError(
                    f"Unexpected type of field name (one of: {tuple(data.keys())!r})"
                )

            def deserialize_field(k: str, v: Any):
                return self._deserialize_model_field(
                    cls.model_fields.get(k), v, inner_deserialize
                )

            return cls(**{k: deserialize_field(k, v) for k, v in data.items()})

        if typing.get_origin(cls) is not None:
            return self._deserialize_generic(cls, data, inner_deserialize)
        return self._deserialize_value(cls, data)

    def _deserialize_generic(
        self,
        generic: type[T],
        data: Any,
        inner_deserialize: Callable[[type[U], Any], U],
    ) -> T:
        origin = typing.get_origin(generic)
        assert origin is not None
        if origin in (set, typing.Set):
            if not isinstance(data, (set, list)):
                raise UnexpectedValueType(data, generic, [set, list])
            if not isinstance(data, set) and not unique(data):
                raise RuntimeError(
                    f"Expected set for {generic}, but got list with duplicate elements ({', '.join(data)})"
                )
            (type_arg,) = typing.get_args(generic)
            return generic(set(inner_deserialize(type_arg, x) for x in data))
        if origin in (tuple, typing.Tuple):
            if not isinstance(data, (tuple, list)):
                raise UnexpectedValueType(data, generic, [tuple, list])
            type_args = typing.get_args(generic)
            if len(data) != len(type_args):
                raise RuntimeError(
                    f"Expected {len(type_args)} values, but got {len(data)} ({data!r})"
                )
            return generic(
                [inner_deserialize(t, x) for t, x in zip(type_args, data, strict=True)]
            )
        if origin in (list, typing.List):
            if not isinstance(data, list):
                raise UnexpectedValueType(data, generic, [list])
            (type_arg,) = typing.get_args(generic)
            return generic([inner_deserialize(type_arg, x) for x in data])
        if origin in (dict, typing.Dict):
            if not isinstance(data, dict):
                raise UnexpectedValueType(data, generic, [dict])
            (key_arg, value_arg) = typing.get_args(generic)
            return generic(
                {
                    inner_deserialize(key_arg, k): inner_deserialize(value_arg, v)
                    for k, v in data.items()
                }
            )

        if origin == typing.Union:
            type_args: tuple[Any, ...] = typing.get_args(generic)
            for type_arg in type_args:
                try:
                    return inner_deserialize(type_arg, data)  # type: ignore
                except UnexpectedValueType:
                    pass
            raise UnexpectedValueType(data, generic, type_args)
        assert False, f"Deserializing generic type {generic} not implemented"

    def _deserialize_value(self, cls: type[T], data: Any) -> T:
        if issubclass(cls, enum.Enum):
            if issubclass(cls, enum.IntEnum):
                if not isinstance(data, (str, int)):
                    raise UnexpectedValueType(data, cls, [str, int])
                if isinstance(data, int):
                    return cls(data)
                return cls(cls._member_map_[data])
            else:
                if not isinstance(data, str):
                    raise UnexpectedValueType(data, cls, [str])
                return cls(cls._member_map_[data])
        if issubclass(cls, Decimal):
            if not isinstance(data, (str, int)):
                raise UnexpectedValueType(data, cls, [str, int])
            return cls(data)

        if cls == type(None):
            if data is not None:
                raise UnexpectedValueType(data, cls, [type(None)])
            return cls()
        assert not issubclass(cls, float), "Don't use float, use Decimal instead"
        if not isinstance(data, cls):
            assert cls in (str, int, bool), f"Unexpected type {cls!r}"
            raise UnexpectedValueType(data, cls, [cls])
        return cls(data)
