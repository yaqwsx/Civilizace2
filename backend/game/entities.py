from __future__ import annotations
from frozendict import frozendict
from functools import cached_property
from pydantic import BaseModel
from typing import Union, Iterable, Dict

EntityId = str

class EntityBase(BaseModel):
    id: EntityId
    name: str

    def __hash__(self) -> int:
        return self.id.__hash__()

class Resource(EntityBase):
    @property
    def isResource(self) -> bool:
        return self.isMaterial or self.isProduction

    @property
    def isMaterial(self) -> bool:
        return self.id.startswith("mat-")

    @property
    def isProduction(self) -> bool:
        return self.id.startswith("prod-")

class Tech(EntityBase):
    cost: Dict[str, int]
    diePoints: int
    edges: Dict[Tech, str] # tech -> dieId

    def __str__(self) -> str:
        return self.name + "("+ self.id + ")"

# Common type of all available entities
Entity = Union[Resource, Tech]

class Entities(frozendict):
    """
    The entities are represented as immutable dictionary (frozendict) so
    you can alter them. They also give you some properties to quickly
    select relevant sub-entities
    """

    def __new__(cls, entities: Iterable[Entity]) -> Entities:
        x = super().__new__(cls, { x.id: x for x in entities })
        return x

    @property
    def work(self) -> Resource:
        return self["res-prace"]

    @cached_property
    def resources(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self
            if isinstance(v, Resource) and v.isResource})

    @cached_property
    def materials(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self
            if isinstance(v, Resource) and v.isMaterial})

    @cached_property
    def productions(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self
            if isinstance(v, Resource) and v.isProduction})

    @cached_property
    def techs(self) -> frozendict[EntityId, Tech]:
        return frozendict({k: v for k, v in self if isinstance(v, Tech)})
