from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from frozendict import frozendict
from functools import cached_property
from pydantic import BaseModel
from typing import Any, Optional, Set, Tuple, Type, TypeVar, Union, Iterable, Dict, List
from enum import Enum
import os

EntityId = str

STARTER_ARMY_PRESTIGES = [15, 20, 25]
BASE_ARMY_STRENGTH = 0
MAP_SIZE = 32
TILE_DISTANCES_RELATIVE = {0: Decimal(0),
                           -9: Decimal(3), -3: Decimal(3), 2: Decimal(3), 7: Decimal(3), 9: Decimal(3),
                           -2: Decimal(2), -1: Decimal(2), 1: Decimal(2), 5: Decimal(2), 6: Decimal(2)}
TIME_PER_TILE_DISTANCE = Decimal(300) if os.environ.get(
    "CIV_SPEED_RUN", None) != "1" else Decimal(30)


TECHNOLOGY_START = "tec-start"
RESOURCE_VILLAGER = "res-obyvatel"
RESOURCE_WORK = "res-prace"

GUARANTEED_IDS: Dict[EntityId, Type[Entity]]  # Defined after Entity is defined


class EntityBase(BaseModel):
    id: EntityId
    name: str
    icon: Optional[str] = None

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, EntityBase) and self.id == other.id

    def __hash__(self) -> int:
        return self.id.__hash__()

    def __str__(self) -> str:
        return "{}({})".format(self.id, self.name)

    def __repr__(self) -> str:
        return "{}({})".format(self.id, self.name)


def adHocEntitiy(id) -> EntityBase:
    return EntityBase(id=id, name="")


@dataclass(init=False, eq=False)
class Die(EntityBase):
    briefName: str


@dataclass(init=False, eq=False)
class ResourceType(EntityBase):
    productionName: str
    colorName: str
    colorHex: str = "0x000000"

@dataclass(init=False, eq=False)
class Resource(EntityBase):
    typ: Optional[ResourceType] = None
    produces: Optional[Resource] = None

    @property
    def isProduction(self) -> bool:
        return self.produces != None

    @property
    def isGeneric(self) -> bool:
        return self.id.startswith("pge-") or self.id.startswith("mge-")

    @property
    def isTracked(self) -> bool:
        return not self.id.startswith("mat-") and not self.id.startswith("mge-")


@dataclass(init=False, eq=False)
class TileFeature(EntityBase):
    pass

@dataclass(init=False, eq=False)
class NaturalResource(TileFeature):
    color: str


@dataclass(init=False, eq=False)
class EntityWithCost(EntityBase):
    cost: Dict[Resource, Decimal] = {}
    points: int
    # duplicates: items in Tech.unlocks
    unlockedBy: List[Tuple[Tech, Die]] = []

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

    @property
    def unlockingDice(self) -> Set[Die]:
        return set(d for e, d in self.unlockedBy)

@dataclass(init=False, eq=False)
class Vyroba(EntityWithCost):
    reward: Tuple[Resource, Decimal]
    requiredFeatures: List[TileFeature] = []
    flavor: str = ""

@dataclass(init=False, eq=False)
class Building(EntityWithCost, TileFeature):
    requiredFeatures: List[NaturalResource] = []

@dataclass(init=False, eq=False)
class Tech(EntityWithCost):
    unlocks: List[Tuple[EntityWithCost, Die]] = []
    flavor: str = ""

    @property
    def unlocksVyrobas(self) -> Set[Vyroba]:
        return set(x for x, _ in self.unlocks if isinstance(x, Vyroba))

    @property
    def unlocksTechs(self) -> Set[Tech]:
        return set(x for x, _ in self.unlocks if isinstance(x, Tech))

    @property
    def unlocksBuilding(self) -> Set[Building]:
        return set(x for x, _ in self.unlocks if isinstance(x, Building))

    def allowedDie(self, target: Entity) -> Set[Die]:
        return set(d for e, d in self.unlocks if e == target)


@dataclass(init=False, eq=False)
class MapTileEntity(EntityBase):
    index: int
    parcelCount: int
    naturalResources: List[NaturalResource]
    richness: int


@dataclass(init=False, eq=False)
class Team(EntityBase):
    color: str
    password: Optional[str]  # We use it to populate database
    visible: bool
    homeTile: MapTileEntity
    hexColor: str = "#000000"


class OrgRole(Enum):
    ORG = 0
    SUPER = 1

@dataclass(init=False, eq=False)
class Org(EntityBase):
    role: OrgRole
    password: Optional[str]


# Common type of all available entities
Entity = Union[Die,
               ResourceType,
               Resource,
               NaturalResource,
               Vyroba,
               Building,
               Tech,
               MapTileEntity,
               Team,
               Org,
               ]

Vyroba.update_forward_refs()

TEntity = TypeVar('TEntity', bound=Entity)


GUARANTEED_IDS = {
    TECHNOLOGY_START: Tech,
    RESOURCE_VILLAGER: Resource,
    RESOURCE_WORK: Resource,
}


class Entities(frozendict[EntityId, Entity]):
    """
    The entities are represented as immutable dictionary (frozendict) so
    you cannot alter them. They also give you some properties to quickly
    select relevant sub-entities
    """

    def __new__(cls, entities: Iterable[Entity]) -> Entities:
        return super().__new__(cls, {x.id: x for x in entities})  # type: ignore

    def __init__(self, entities: Iterable[Entity]):
        ...

    @property
    def all(self) -> frozendict[EntityId, Entity]:
        return self

    @property
    def work(self) -> Resource:
        return self.resources[RESOURCE_WORK]

    @property
    def obyvatel(self) -> Resource:
        return self.resources[RESOURCE_VILLAGER]

    @property
    def zbrane(self):
        # TODO: remove
        return self["mat-zbrane"]

    @cached_property
    def dice(self) -> frozendict[EntityId, Die]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Die)})

    @cached_property
    def resources(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Resource)})

    @cached_property
    def materials(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.resources.items()
                           if v.isTracked})

    @cached_property
    def productions(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.resources.items()
                           if v.isProduction})

    @cached_property
    def vyrobas(self) -> frozendict[EntityId, Vyroba]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Vyroba)})

    @cached_property
    def buildings(self) -> frozendict[EntityId, Building]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Building)})

    @cached_property
    def techs(self) -> frozendict[EntityId, Tech]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Tech)})

    @cached_property
    def tiles(self) -> frozendict[EntityId, MapTileEntity]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, MapTileEntity)})

    @cached_property
    def teams(self) -> frozendict[EntityId, Team]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Team)})

    @cached_property
    def orgs(self) -> frozendict[EntityId, Org]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Org)})

    @staticmethod
    def _gameOnlyView(entity: Entity) -> Entity:
        if isinstance(entity, Team) or isinstance(entity, Org):
            e = entity.copy()
            e.password = None
            return e
        return entity

    @property
    def gameOnlyEntities(self) -> Entities:
        return Entities([self._gameOnlyView(v) for v in self.values()])
