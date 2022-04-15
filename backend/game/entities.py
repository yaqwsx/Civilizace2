from __future__ import annotations
from decimal import Decimal
from frozendict import frozendict
from functools import cached_property
from pydantic import BaseModel
from typing import Optional, Tuple, Union, Iterable, Dict, List

# Type Aliases
EntityId = str
TeamId = str # intentionally left weak


class EntityBase(BaseModel):
    id: EntityId
    name: str

    def __hash__(self) -> int:
        return self.id.__hash__()

    def __repr__(self) -> str:
        return "{}({})".format(self.id, self.name)


class Team(EntityBase):
    None


class ResourceType(EntityBase):
    productionName: str
    colorName: str
    colorVal: int


class ResourceBase(EntityBase):
    ### Any resource, base class for Resource, GenericResource; 
    #   Do not instantiate 
    #   TODO: Is there a simple way to disable __init__ for this base class? ###
    typ: Optional[Tuple[ResourceType, int]]=None
    produces: Optional[Resource]=None

    @property
    def isResource(self) -> bool:
        return self.isMaterial or self.isProduction

    @property
    def isMaterial(self) -> bool:
        return self.id.startswith("mat-")

    @property
    def isProduction(self) -> bool:
        return self.produces != None


class Resource(ResourceBase):
    ### Represents a specific resource (e.g., mat-drevo) ###
    None

class ResourceGeneric(ResourceBase):
    ### Represents action cost using ResourceType rather than material itself (e.g., mat-palivo-3) ###
    None


class Tech(EntityBase):
    cost: Dict[ResourceBase, Decimal]
    diePoints: int
    edges: Dict[Tech, str]={} # tech -> dieId

    def __str__(self) -> str:
        return self.name + "("+ self.id + ")"


class Vyroba(EntityBase):
    cost: Dict[ResourceBase, Decimal]
    die: Tuple[str, int]
    reward: Tuple[Resource, Decimal]
    techs: List[Tech]=[]


class TileFeature(EntityBase):
    pass


class NaturalResource(TileFeature):
    pass


class Building(TileFeature):
    requiredFeatures: List[TileFeature]


class MapTileEntity(EntityBase): # used to import data for initial state
    index: int
    parcelCount: int
    naturalResources: List[NaturalResource]
    richness: int=0


# Common type of all available entities
Entity = Union[Resource, Tech, Vyroba, NaturalResource, Building, MapTileEntity, ResourceType]

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
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Resource) and v.isResource})

    @cached_property
    def materials(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Resource) and v.isMaterial})

    @cached_property
    def productions(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Resource) and v.isProduction})

    @cached_property
    def techs(self) -> frozendict[EntityId, Tech]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Tech)})


    @cached_property
    def teams(self) -> frozendict[EntityId, Team]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Team)})

    @cached_property
    def tiles(self) -> frozendict[EntityId, MapTileEntity]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, MapTileEntity)})
