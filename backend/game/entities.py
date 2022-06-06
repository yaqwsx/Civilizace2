from __future__ import annotations
from decimal import Decimal
from frozendict import frozendict
from functools import cached_property
from pydantic import BaseModel
from typing import Any, Optional, Set, Tuple, Union, Iterable, Dict, List
from enum import Enum

EntityId = str
TeamId = str # intentionally left weak
DieId = str

STARTER_ARMY_PRESTIGES = [15,20,25]
BASE_ARMY_STRENGTH = 5
MAP_SIZE = 32
TILE_DISTANCES_RELATIVE = {0: Decimal(0),
    -9: Decimal(3), -3: Decimal(3), 2: Decimal(3), 7: Decimal(3), 9: Decimal(3),
    -2: Decimal(2), -1: Decimal(2), 1: Decimal(2), 5: Decimal(2), 6: Decimal(2)}
TIME_PER_TILE_DISTANCE = Decimal(300)
DIE_IDS = [DieId("die-lesy"), DieId("die-plane"), DieId("die-hory")]
THROW_COST = 5


# Type Aliases

class EntityBase(BaseModel):
    id: EntityId
    name: str

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, EntityBase) and self.id == other.id

    def __hash__(self) -> int:
        return self.id.__hash__()

    def __str__(self) -> str:
        return "{}({})".format(self.id, self.name)


    def __repr__(self) -> str:
        return "{}({})".format(self.id, self.name)


class Team(EntityBase):
    color: str
    password: Optional[str] # We use it to populate database
    visible: bool
    homeTileId: EntityId

class OrgRole(Enum):
    ORG = 0
    SUPER = 1

class Org(EntityBase):
    role: OrgRole
    password: Optional[str]

class ResourceType(EntityBase):
    productionName: str
    colorName: str
    colorVal: int


class Resource(EntityBase):
    ### Any resource, base class for Resource, GenericResource;
    #   Do not instantiate
    #   TODO: Is there a simple way to disable __init__ for this base class? ###
    typ: Optional[Tuple[ResourceType, int]]=None
    produces: Optional[Resource]=None

    @property
    def isResource(self) -> bool:
        return self.isTracked or self.isProduction

    @property
    def isTracked(self) -> bool:
        return self.id.startswith("mat-") or self.id.startswith("mge-")

    @property
    def isProduction(self) -> bool:
        return self.produces != None

    @property
    def isGeneric(self) -> bool:
        return self.id.startswith("pge-") or self.id.startswith("mge-")

    @property
    def isTracked(self) -> bool:
        return not self.id.startswith("mat-")


class EntityWithCost(EntityBase):
    cost: Dict[Resource, Decimal]
    points: int
    unlockedBy: List[Tuple[EntityWithCost, DieId]]=[] # duplicates: items in Tech.unlocks

    # The default deduced equality is a strong-value based one. However, since
    # there are loops in fields (via unlockedBy), the equality check never ends.
    # Therefore, we have to break the loop - here we will just check that the
    # unlockedBy are the same objects.
    #
    # The ultimate solution would to be to keep a set of already checked objects
    # for equality, however, that requires changes to BaseModel which is out of
    # our control.
    #
    # Equality based on ID is enough, thus this code is no longer needed
    # def __eq__(self, other: Any) -> bool:
    #     if not isinstance(other, EntityWithCost):
    #         return False
    #     return self.cost == other.cost and \
    #            self.points == other.points and \
    #            [(id(e), d) for e, d in self.unlockedBy] == [(id(e), d) for e, d in other.unlockedBy]


class Tech(EntityWithCost):
    unlocks: List[Tuple[Entity, DieId]]=[]

    @property
    def unlocksVyrobas(self) -> Set[Vyroba]:
        return set(x for x, _ in self.unlocks if isinstance(x, Vyroba))

    @property
    def unlocksTechs(self) -> Set[Vyroba]:
        return set(x for x, _ in self.unlocks if isinstance(x, Tech))


class TileFeature(EntityBase):
    pass

class Vyroba(EntityWithCost):
    reward: Tuple[Resource, Decimal]
    requiredFeatures: List[TileFeature]


class NaturalResource(TileFeature):
    pass


class Building(EntityWithCost, TileFeature):
    requiredFeatures: List[TileFeature]


class MapTileEntity(EntityBase):
    index: int
    parcelCount: int
    naturalResources: List[NaturalResource]
    richness: int        


# Common type of all available entities
Entity = Union[Resource, Tech, Vyroba, NaturalResource, Building, MapTileEntity,
               ResourceType, Team, Org]

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
    def all(self) -> frozendict[EntityId, Entity]:
        return self

    @property
    def work(self) -> Resource:
        return self["res-prace"]

    @property
    def obyvatel(self) -> Resource:
        return self["res-obyvatel"]

    @property
    def zbrane(self) -> Resource:
        return self["mat-zbrane"]

    @cached_property
    def resources(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Resource) and v.isResource})

    @cached_property
    def materials(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Resource) and v.isTracked})

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

    @cached_property
    def orgs(self) -> frozendict[EntityId, Org]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Org)})

    @cached_property
    def teams(self) -> frozendict[EntityId, Team]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Team)})

    @cached_property
    def vyrobas(self) -> frozendict[EntityId, Vyroba]:
        return frozendict({k: v for k, v in self.items()
            if isinstance(v, Vyroba)})

    @staticmethod
    def _gameOnlyView(entity):
        if isinstance(entity, Team):
            t = entity.copy()
            t.password = None
            return t
        if isinstance(entity, Org):
            o = entity.copy()
            o.password = None
            return o
        return entity

    @property
    def gameOnlyEntities(self) -> Entities:
        return Entities([self._gameOnlyView(v) for v in self.values()])

