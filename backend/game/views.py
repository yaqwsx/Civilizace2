from django.shortcuts import render
from django.views import View
from django.http import JsonResponse

from typing import Dict, Any, Callable
import json
import decimal
from pydantic import BaseModel

from game.entities import Resource, Tech, Vyroba, Entity

# This is only a mock of proposed API for the game frontend. Therefore, we use
# simple views, often with constant data or driven by static variables. No fancy
# stuff like ViewSets. There is also no auth

try:
    from game.tests.actions.common import TEST_ENTITIES
    from game.entities import Entity
except FileNotFoundError as e:
    if "testEntities.json" not in str(e):
        raise e from None
    import sys
    sys.stderr.write("WARNING: Missing testEntities.json, silently ignoring\n")
    TEST_ENTITIES = {}


def serialize(r: Entity,
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

def entityFieldSerializer(e: Entity, field: str, value: Any) -> Any:
    if field == "produces":
        return value.id if value is not None else None
    if field == "reward":
        return (value[0].id, value[1])
    if field == "typ":
        if value is None:
            return None
        t, l = value
        return {
            "level": l,
            "name": t.name,
            "prodName": t.productionName
        }
    if field == "cost":
        return {r.id: v for r, v in value.items()}
    if field == "edges":
        return {t.id: v for t, v in value.items()}
    if field == "techs":
        return [t.id for t in value]
    return value

class EntityEncoder(json.JSONEncoder):
    def default(self, obj):
        print(obj)
        if isinstance(obj, BaseModel):
            return obj.dict()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def typeFilter(typespec, x):
    return (typespec is None) or \
           (typespec == "resource" and isinstance(x, Resource)) or \
           (typespec == "tech" and isinstance(x, Tech)) or \
           (typespec == "vyroba" and isinstance(x, Vyroba))


# We expect this endpoint to serve entities with several filters available via
# get parameters:
# - type: resource | tech | vyroba
class EntityView(View):
    def get(self, request):
        typespec = request.GET.get("type", None)
        return JsonResponse({
            id: serialize(val, entityFieldSerializer, lambda x: {})
            for id, val in TEST_ENTITIES.items()
            if typeFilter(typespec, val)
        }, encoder=EntityEncoder)

# We expect this endpoint to serve entities from team perspective (e.g., the
# entities are enriched with flags; techs have research state, resources have
# available amount).
# - type: resource | tech | vyroba
class TeamEntityView(View):
    def get(self, request, teamId):
        # TBA filter
        typespec = request.GET.get("type", None)
        return JsonResponse({
            id: serialize(val, entityFieldSerializer, lambda x: self.enrich(teamId, x))
            for id, val in TEST_ENTITIES.items()
            if typeFilter(typespec, val)
        }, encoder=EntityEncoder)

    @staticmethod
    def enrich(teamId, entity):
        if isinstance(entity, Resource):
            return {
                "available": 5
            }
        return {}
