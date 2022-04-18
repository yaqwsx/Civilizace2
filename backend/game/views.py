from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponseNotFound


from typing import Dict, Any, Callable
import json
import decimal
from pydantic import BaseModel

from game.entities import Resource, Tech, Vyroba, Entity, EntityBase
from game.entities import ResourceBase, Tech, Vyroba, Entity

# This is only a mock of proposed API for the game frontend. Therefore, we use
# simple views, often with constant data or driven by static variables. No fancy
# stuff like ViewSets. There is also no auth

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

def shallowEntity(e: Any) -> Any:
    """
    Given an entity, or a tuple of entities, make them shalow - represent them
    only by ID
    """
    if isinstance(e, EntityBase):
        return e.id
    if isinstance(e, tuple):
        return tuple(map(shallowEntity, e))
    if isinstance(e, list):
        return list(map(shallowEntity, e))
    if isinstance(e, dict):
        return {shallowEntity(k): shallowEntity(v) for k, v in e.items()}
    return e

def entityFieldSerializer(e: Entity, field: str, value: Any) -> Any:
    if field == "typ":
        if value is None:
            return None
        t, l = value
        return {
            "level": l,
            "name": t.name,
            "prodName": t.productionName
        }
    return shallowEntity(value)

class EntityEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.dict()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def typeFilter(typespec, x):
    return (typespec is None) or \
           (typespec == "resource" and isinstance(x, ResourceBase)) or \
           (typespec == "tech" and isinstance(x, Tech)) or \
           (typespec == "vyroba" and isinstance(x, Vyroba))


# We expect this endpoint to serve entities with several filters available via
# get parameters:
# - type: resource | tech | vyroba
class EntityView(View):
    def get(self, request):
        from game.tests.actions.common import TEST_ENTITIES
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
        from game.tests.actions.common import TEST_ENTITIES
        typespec = request.GET.get("type", None)
        data = {
            id: serialize(val, entityFieldSerializer, lambda x: self.enrich(teamId, x))
            for id, val in TEST_ENTITIES.items()
            if typeFilter(typespec, val)
        }
        return JsonResponse(data, encoder=EntityEncoder)

    @staticmethod
    def enrich(teamId, entity):
        if isinstance(entity, Resource):
            return {
                "available": 5
            }
        if isinstance(entity, Tech):
            s = "available"
            if entity.id == "tec-start":
                s = "owned"
            if entity.id == "tec-a":
                s = "researching"

            extra = {"status": s}
            if  s == "researching":
                extra.update({"assignedTask": {
                    "id": "task_42",
                    "name": "Hezký úkol",
                    "teamDescription": "Řekni a!",
                    "orgDescription": "Zadej jim to!",
                    "capacity": 4,
                    "occupiedCount": 3,
                }})
            return extra
        return {}

MOCK_TASKS = [
    {
        "id": "task_42",
        "name": "Hezký úkol",
        "teamDescription": "Řekni a!",
        "orgDescription": "Zadej jim to!",
        "capacity": 4,
        "occupiedCount": 3,
        "techs": ["tec-a", "tec-b", "tec-c"]
    },
    {
        "id": "task_43",
        "name": "Další hezký úkol",
        "teamDescription": "# Tohle\n\n má:\n\n-markdown\n\n-jakože fakt\n\n",
        "orgDescription": "Zadej jim to!",
        "capacity": 4,
        "occupiedCount": 3,
        "techs": ["tec-b", "tec-c"]
    },
]

# Handle listing all tasks and creating a new one.
class TasksView(View):
    def get(self, request):
        return JsonResponse(MOCK_TASKS, safe=False)

    def post(self, request):
        # We should return something rest compatible...
        return JsonResponse({"status": "ok"})

# Handle task based on ID:
class TaskView(View):
    def get(self, request, taskId):
        for t in MOCK_TASKS:
            if t["id"] == taskId:
                return JsonResponse(t)
        return HttpResponseNotFound({"status": "error"})

    def put(self, request, taskId):
        for t in MOCK_TASKS:
            if t["id"] == taskId:
                return JsonResponse({"status": "ok"})
        return HttpResponseNotFound({"status": "error"})

    def put(self, request, taskId):
        for t in MOCK_TASKS:
            if t["id"] == taskId:
                return JsonResponse({"status": "ok"})
        return HttpResponseNotFound({"status": "error"})
