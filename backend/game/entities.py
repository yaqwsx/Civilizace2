from __future__ import annotations

import itertools
import os
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from functools import cached_property
from typing import Any, Iterable, Optional, Tuple, Type, Union

import boolean
from frozendict import frozendict
from pydantic import BaseModel

EntityId = str

STARTER_ARMY_PRESTIGES = [15, 20, 25]
BASE_ARMY_STRENGTH = 0
MAP_SIZE = 32
TILE_DISTANCES_RELATIVE = {
    0: Decimal(0),
    -9: Decimal(3),
    -3: Decimal(3),
    2: Decimal(3),
    7: Decimal(3),
    9: Decimal(3),
    -2: Decimal(2),
    -1: Decimal(2),
    1: Decimal(2),
    5: Decimal(2),
    6: Decimal(2),
}
TIME_PER_TILE_DISTANCE = (
    Decimal(300) if os.environ.get("CIV_SPEED_RUN", None) != "1" else Decimal(30)
)


TECHNOLOGY_START = "tec-start"
RESOURCE_VILLAGER = "res-obyvatel"
RESOURCE_WORK = "res-prace"
RESOURCE_CULTURE = "res-kultura"
RESOURCE_WITHDRAW_CAPACITY = "res-withdraw_cap"

GUARANTEED_IDS: dict[EntityId, Type[Entity]]  # Defined after Entity is defined


class EntityBase(BaseModel):
    class Config:
        arbitrary_types_allowed = True

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


@dataclass(init=False, repr=False, eq=False)
class Die(EntityBase):
    briefName: str


@dataclass(init=False, repr=False, eq=False)
class Resource(EntityBase):
    produces: Optional[Resource] = None
    nontradable: bool = False
    isGeneric: bool = False

    @property
    def tradable(self) -> bool:
        return not self.nontradable

    @property
    def isTradableProduction(self) -> bool:
        return self.tradable and self.produces is not None

    @property
    def isWithdrawable(self) -> bool:
        return self.tradable and self.produces is None


@dataclass(init=False, repr=False, eq=False)
class TileFeature(EntityBase):
    pass


@dataclass(init=False, repr=False, eq=False)
class NaturalResource(TileFeature):
    color: str


@dataclass(init=False, repr=False, eq=False)
class EntityWithCost(EntityBase):
    cost: dict[Resource, Decimal] = {}
    points: int
    requirements: Optional[boolean.Expression] = None

    def requirements_met(self, owned_entities: Iterable[EntityWithCost]) -> bool:
        if self.requirements is None:
            return True
        owned_entities_set = set(entity.id for entity in owned_entities)
        entity_id_map: dict[str, bool] = {
            entity_id: entity_id in owned_entities_set
            for entity_id in self.requirements.objects
        }
        return self.requirements(**entity_id_map)  # type: ignore


@dataclass(init=False, repr=False, eq=False)
class Tech(EntityWithCost):
    unlocks: list[EntityWithCost] = []
    requiresTask: bool
    flavor: str = ""

    @property
    def unlocksVyrobas(self) -> set[Vyroba]:
        return set(e for e in self.unlocks if isinstance(e, Vyroba))

    @property
    def unlocksTechs(self) -> set[Tech]:
        return set(e for e in self.unlocks if isinstance(e, Tech))

    @property
    def unlocksBuildings(self) -> set[Building]:
        return set(e for e in self.unlocks if isinstance(e, Building))

    @property
    def unlocksTeamAttributes(self) -> set[TeamAttribute]:
        return set(e for e in self.unlocks if isinstance(e, TeamAttribute))


@dataclass(init=False, repr=False, eq=False)
class Vyroba(EntityWithCost):
    reward: Tuple[Resource, Decimal]
    otherRewards: list[Tuple[Resource, Decimal]] = []
    requiredTileFeatures: list[TileFeature] = []
    flavor: str = ""

    def all_rewards(self) -> Iterable[Tuple[Resource, Decimal]]:
        return itertools.chain([self.reward], self.otherRewards)


@dataclass(init=False, repr=False, eq=False)
class TeamAttribute(EntityWithCost):
    flavor: str = ""


@dataclass(init=False, repr=False, eq=False)
class Building(EntityWithCost, TileFeature):
    requiredTileFeatures: list[NaturalResource] = []
    # duplicates: BuildingUpgrade.building
    upgrades: list[BuildingUpgrade] = []


@dataclass(init=False, repr=False, eq=False)
class BuildingUpgrade(EntityWithCost, TileFeature):
    building: Building


@dataclass(init=False, repr=False, eq=False)
class MapTileEntity(EntityBase):
    index: int
    naturalResources: list[NaturalResource]
    richness: int


@dataclass(init=False, repr=False, eq=False)
class TeamGroup(EntityBase):
    """Group of teams that can unlock techs, vyrobas, etc."""

    unlocks: list[EntityWithCost] = []
    # duplicates: TeamEntity.groups
    teams: list[TeamEntity] = []


@dataclass(init=False, repr=False, eq=False)
class UserEntity(EntityBase):
    # We use it to populate database
    username: Optional[str]
    password: Optional[str]


@dataclass(init=False, repr=False, eq=False)
class TeamEntity(UserEntity):
    color: str
    visible: bool
    homeTile: MapTileEntity
    hexColor: str = "#000000"
    groups: list[TeamGroup] = []


class OrgRole(Enum):
    ORG = 0
    SUPER = 1


@dataclass(init=False, repr=False, eq=False)
class OrgEntity(UserEntity):
    role: OrgRole


@dataclass(init=False, repr=False, eq=False)
class GameInitState(BaseModel):
    turn: int = 0


# Common type of all available entities
Entity = Union[
    Die,
    Resource,
    NaturalResource,
    Vyroba,
    Building,
    BuildingUpgrade,
    TeamAttribute,
    Tech,
    MapTileEntity,
    TeamEntity,
    OrgEntity,
    TeamGroup,
]

EntityWithCost.update_forward_refs()
Building.update_forward_refs()


GUARANTEED_IDS = {
    TECHNOLOGY_START: Tech,
    RESOURCE_VILLAGER: Resource,
    RESOURCE_WORK: Resource,
    RESOURCE_CULTURE: Resource,
    RESOURCE_WITHDRAW_CAPACITY: Resource,
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
    def work(self) -> Resource:
        return self.resources[RESOURCE_WORK]

    @property
    def obyvatel(self) -> Resource:
        return self.resources[RESOURCE_VILLAGER]

    @property
    def culture(self) -> Resource:
        return self.resources[RESOURCE_CULTURE]

    @property
    def withdraw_capacity(self) -> Resource:
        return self.resources[RESOURCE_WITHDRAW_CAPACITY]

    @property
    def zbrane(self) -> Resource:
        # TODO: remove
        return self.resources["mat-zbrane"]

    @property
    def all(self) -> frozendict[EntityId, Entity]:
        return self

    @cached_property
    def dice(self) -> frozendict[EntityId, Die]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, Die)})

    @cached_property
    def resources(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, Resource)})

    @cached_property
    def vyrobas(self) -> frozendict[EntityId, Vyroba]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, Vyroba)})

    @cached_property
    def buildings(self) -> frozendict[EntityId, Building]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, Building)})

    @cached_property
    def building_upgrades(self) -> frozendict[EntityId, BuildingUpgrade]:
        return frozendict(
            {k: v for k, v in self.items() if isinstance(v, BuildingUpgrade)}
        )

    @cached_property
    def team_attributes(self) -> frozendict[EntityId, TeamAttribute]:
        return frozendict(
            {k: v for k, v in self.items() if isinstance(v, TeamAttribute)}
        )

    @cached_property
    def techs(self) -> frozendict[EntityId, Tech]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, Tech)})

    @cached_property
    def tiles(self) -> frozendict[EntityId, MapTileEntity]:
        return frozendict(
            {k: v for k, v in self.items() if isinstance(v, MapTileEntity)}
        )

    @cached_property
    def team_groups(self) -> frozendict[EntityId, TeamGroup]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, TeamGroup)})

    @cached_property
    def teams(self) -> frozendict[EntityId, TeamEntity]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, TeamEntity)})

    @cached_property
    def orgs(self) -> frozendict[EntityId, OrgEntity]:
        return frozendict({k: v for k, v in self.items() if isinstance(v, OrgEntity)})

    @staticmethod
    def _gameOnlyView(entity: Entity) -> Entity:
        if isinstance(entity, UserEntity):
            e = entity.copy()
            e.username = None
            e.password = None
            return e
        return entity

    @property
    def gameOnlyEntities(self) -> Entities:
        return Entities([self._gameOnlyView(v) for v in self.values()])
