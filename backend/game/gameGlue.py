from decimal import Decimal
import decimal
import enum
import json
from typing import Dict, Any, Callable, Optional
import typing
from pydantic import BaseModel
from pydantic.fields import SHAPE_SINGLETON, MAPPING_LIKE_SHAPES, SHAPE_LIST, SHAPE_SET
from game.actions.actionBase import ActionArgs

from game.entities import EntityBase, Entity
from game.state import MapTile, StateModel

def _stateSerialize(what):
    if isinstance(what, StateModel) or isinstance(what, ActionArgs):
        return stateSerialize(what)
    if isinstance(what, EntityBase):
        return what.id
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
        return tuple([_stateSerialize(x) for x in what])
    if isinstance(what, dict):
        return {_stateSerialize(k): _stateSerialize(v) for k, v in what.items()}
    return what

def stateSerialize(object: BaseModel) -> Dict[Any, Any]:
    """
    Turn the model into a dictionary representation
    """
    value = {}
    for field in object.__fields__.values():
        value[field.name] = _stateSerialize(getattr(object, field.name))
    # # There is polymorphism on MapTile, reflect it: //Not anymore, can be refactored out
    # if isinstance(object, MapTile):
    #     value["tt"] = "M"
    return value

def stateDeserialize(cls, data, entities):
    """
    Turn dictionary representation into a model
    """
    source = {}
    # if issubclass(cls, MapTile):
    #     cls = {
    #         "M": MapTile
    #     }[data["tt"]]
    for field in cls.__fields__.values():
        if not field.required:
            d = data.get(field.name, None)
        else:
            d = data[field.name]
        source[field.name] = _stateDeserialize(d, field, entities)
    # Parse OBJ is exceptionally slow. This construct object instead
    # x = cls.parse_obj(source)
    x = cls.construct(**source)
    return x

def _stateDeserialize(data, field, entities):
    if field.shape == SHAPE_SINGLETON:
        return _stateDeserializeSingleton(data, field.type_, field.required, entities)
    if field.shape in MAPPING_LIKE_SHAPES:
        return {
            _stateDeserialize(k, field.key_field, entities): _stateDeserializeSingleton(v, field.type_, field.required, entities)
            for k, v in data.items()}
    if field.shape == SHAPE_LIST:
        return [_stateDeserializeSingleton(x, field.type_, field.required, entities)
            for x in data]
    if field.shape == SHAPE_SET:
        return set([_stateDeserializeSingleton(x, field.type_, field.required, entities)
            for x in data])
    raise NotImplementedError(f"Shape type {field.shape} not implemented")

def _stateDeserializeGeneric(generic, data, entities):
    if issubclass(generic.__origin__, set):
        return set([_stateDeserializeSingleton(x, generic.__args__[0], True, entities)
            for x in data])
    if issubclass(generic.__origin__, list):
        return [_stateDeserializeSingleton(x, generic.__args__[0], True, entities)
            for x in data]
    if issubclass(generic.__origin__, dict):
        return {
            _stateDeserializeSingleton(k, generic.__args__[0], True, entities): _stateDeserializeSingleton(v, generic.__args__[1], True, entities)
            for k, v in data.items()}
    assert(False)

def _stateDeserializeSingleton(data, expectedType, required, entities):
    if not required and data is None:
        return None
    if hasattr(expectedType, "__origin__"):
        return _stateDeserializeGeneric(expectedType, data, entities)
    if issubclass(expectedType, StateModel) or issubclass(expectedType, ActionArgs):
        return stateDeserialize(expectedType, data, entities)
    if issubclass(expectedType, EntityBase):
        return entities[data]
    if issubclass(expectedType, Decimal):
        return Decimal(data)
    if issubclass(expectedType, enum.Enum):
        return expectedType(data)
    return expectedType(data)

def _serializeEntity(r: Entity,
              serializeField: Callable[[Entity, str, Any], Any],
              enrichEntity: Callable[[Entity], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given:
    - a serialization function that takes field name and field value and returns
      serialize field value. If none is returned, the value is not included in
      the result
    - a function that returns extra field for the model
    returns a dictionary that represents the serialized entity
    """
    res = {}
    for field, value in r:
        sValue = serializeField(r, field, value)
        if sValue is not None:
            res[field] = sValue
    res.update(enrichEntity(r))
    return res

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
    if isinstance(e, dict):
        return {_shallowEntity(k): _shallowEntity(v) for k, v in e.items()}
    return e

def _entityFieldSerializer(e: Entity, field: str, value: Any) -> Any:
    if field in ["role", "password", "visible"]:
        return None
    if field == "typ":
        if value is None:
            return None
        t, l = value
        return {
            "level": l,
            "id": t.id
        }
    return _shallowEntity(value)

def serializeEntity(entity: Entity,
                    enrichEntity: Optional[Callable[[Entity], Dict[str, Any]]]=None) \
                        -> Dict[str, Any]:
    enrich = (lambda x: {}) if (enrichEntity is None) else enrichEntity
    return _serializeEntity(entity, _entityFieldSerializer, enrich)

class EntityEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.dict()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)
