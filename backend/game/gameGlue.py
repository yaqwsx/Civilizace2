from decimal import Decimal
import decimal
import enum
import json
import typing
from typing import Dict, Any, Callable, Optional, Tuple, Type, TypeVar, Union
from pydantic import BaseModel
from pydantic.fields import SHAPE_SINGLETON, MAPPING_LIKE_SHAPES, SHAPE_LIST, SHAPE_SET, ModelField
from game.actions.actionBase import ActionArgs

from game.entities import EntityBase, Entity, Entities
from game.state import MapTile, StateModel

TModel = TypeVar('TModel', bound=BaseModel)

def _stateSerialize(what: Any) -> Any:
    if isinstance(what, EntityBase):
        return what.id
    if isinstance(what, StateModel) or isinstance(what, ActionArgs):
        return stateSerialize(what)
    if isinstance(what, enum.Enum):
        return what.value
    if isinstance(what, Decimal):
        return str(what)
    if isinstance(what, list):
        return [_stateSerialize(x) for x in what]
    if isinstance(what, set):
        items = [_stateSerialize(x) for x in what]
        items.sort()
        return items
    if isinstance(what, tuple):
        return tuple(_stateSerialize(x) for x in what)
    if isinstance(what, dict):
        return {_stateSerialize(k): _stateSerialize(v) for k, v in what.items()}
    if isinstance(what, float):  # TODO: check float type
        print('Unexpected float type during serialization')
        return what
    assert isinstance(what, str | int | type(None)), f'Unexpected type {type(what)} during serialization'
    return what

def stateSerialize(model: BaseModel) -> Dict[str, Any]:
    """
    Turn the model into a dictionary representation
    """
    return {field.name: _stateSerialize(getattr(model, field.name))
                for field in model.__fields__.values()}

def stateDeserialize(cls: Type[TModel], data: Dict[str, Any], entities: Entities) -> TModel:
    """
    Turn dictionary representation into a model
    """
    source: Dict[str, Any] = {}
    for field in cls.__fields__.values():
        if field.name in data:
            source[field.name] = _stateDeserialize(data[field.name], field, entities)
        elif field.required:
            raise RuntimeError(f"Field {field.name} required, but not provided")
    # TODO: check impact of `cls.validate(source)` on performance (would be the prefered way)
    return cls.construct(**source)

def _stateDeserialize(data: Any, field: ModelField, entities: Entities) -> Any:
    required = field.required == True
    if field.shape == SHAPE_SINGLETON:
        return _stateDeserializeSingleton(data, field.type_, required, entities)
    if field.shape in MAPPING_LIKE_SHAPES:
        assert field.key_field is not None
        assert isinstance(data, dict), f"Expected {dict}, but got {type(data)} (field: {field})"
        return {_stateDeserialize(k, field.key_field, entities):
                    _stateDeserializeSingleton(v, field.type_, required, entities)
                for k, v in data.items()}
    if field.shape == SHAPE_LIST:
        assert isinstance(data, list), f"Expected {list}, but got {type(data)} (field: {field})"
        return [_stateDeserializeSingleton(x, field.type_, required, entities)
                for x in data]
    if field.shape == SHAPE_SET:
        # TODO: check if list in following condition is ok
        assert isinstance(data, set | list), f"Expected {set}, but got {type(data)} (field: {field})"
        return set(_stateDeserializeSingleton(x, field.type_, required, entities)
                for x in data)
    raise NotImplementedError(f"Shape type {field.shape} not implemented")

def _stateDeserializeGeneric(data: Any, generic: Type, entities: Entities) -> Any:
    origin = typing.get_origin(generic)
    assert origin is not None
    if issubclass(origin, set):
        assert isinstance(data, set)
        type_args, = generic.__args__
        return set([_stateDeserializeSingleton(x, generic.__args__[0], True, entities)
                for x in data])
    if issubclass(origin, list):
        assert isinstance(data, list)
        return [_stateDeserializeSingleton(x, generic.__args__[0], True, entities)
                for x in data]
    if issubclass(origin, dict):
        assert isinstance(data, dict)
        return {_stateDeserializeSingleton(k, generic.__args__[0], True, entities):
                    _stateDeserializeSingleton(v, generic.__args__[1], True, entities)
                for k, v in data.items()}
    assert False

def _stateDeserializeSingleton(data: Optional[Any], expectedType: Type, required: bool, entities: Entities) -> Any:
    if not required and data is None:
        return None
    if typing.get_origin(expectedType) is not None:
        return _stateDeserializeGeneric(data, expectedType, entities)
    assert isinstance(expectedType, type), 'expectedType has to be type or generic type'
    if issubclass(expectedType, StateModel) or issubclass(expectedType, ActionArgs):
        assert isinstance(data, dict), f"Expected dict for {expectedType}, but got {type(data)}"
        assert all(isinstance(name, str) for name in data)
        return stateDeserialize(expectedType, data, entities)
    if issubclass(expectedType, EntityBase):
        assert isinstance(data, str), f"Expected str for {expectedType}, but got {type(data)}"
        if data in entities:
            entity = entities[data]
        else:
            raise RuntimeError(f"Could not find entity with id '{data}'")
        if not isinstance(entity, expectedType):
            raise RuntimeError(f"Entity {entity} is not {expectedType.__name__}")
        return entity
    if issubclass(expectedType, enum.Enum):
        assert isinstance(data, str | int), f"Expected str or int for Enum {expectedType}, but got {type(data)}"
        if isinstance(data, str):
            return expectedType._member_map_[data]
        return expectedType(data)
    if issubclass(expectedType, bool):
        assert not isinstance(data, str), "Don't construct bool from str"
        assert isinstance(data, int), f"Expected int for {expectedType}, but got {type(data)}"
        return expectedType(data)
    # TODO: check if float is ok
    assert issubclass(expectedType, int | float | Decimal | str), f"Unexpected type {expectedType}"
    assert isinstance(data, str | int | float), f"Data of unexpected type {type(data)}"
    return expectedType(data)

def serializeEntity(entity: EntityBase, extraFields: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Args:
    - a serialization function that takes field name and field value and returns
      serialized field value. If none is returned, the value is not included in
      the result
    - a function that returns extra fields for the model

    Returns:
        a dictionary that represents the serialized entity
    """
    result = {}
    for field, value in entity:
        sValue = _entityFieldSerializer(field, value)
        if sValue is not None:
            assert field not in result
            result[field] = sValue
    fields_count = len(result)
    result.update(extraFields)
    assert len(result) == fields_count + len(extraFields)
    return result

def _shallowEntity(e: Any) -> Any:
    """
    Given an entity, or a tuple of entities, make them shalow - represent them
    only by ID
    """
    if isinstance(e, EntityBase):
        return e.id
    if isinstance(e, tuple):
        return tuple(map(_shallowEntity, e))
    if isinstance(e, list):
        return list(map(_shallowEntity, e))
    if isinstance(e, set):
        return set(map(_shallowEntity, e))
    if isinstance(e, dict):
        return {_shallowEntity(k): _shallowEntity(v) for k, v in e.items()}
    assert isinstance(e, str | int | Decimal | type(None))
    return e

def _entityFieldSerializer(field: str, value: Any) -> Optional[Any]:
    if field in ["role", "password", "visible"]:
        return None
    return _shallowEntity(value)

class EntityEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            return obj.dict()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)
