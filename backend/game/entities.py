from __future__ import annotations
from decimal import Decimal
from frozendict import frozendict
from functools import cached_property
from pydantic import BaseModel
from typing import Any, Optional, Set, Tuple, Union, Iterable, Dict, List
from enum import Enum
import os

EntityId = str
TeamId = str  # intentionally left weak
DieId = str

STARTER_ARMY_PRESTIGES = [15, 20, 25]
BASE_ARMY_STRENGTH = 0
MAP_SIZE = 32
TILE_DISTANCES_RELATIVE = {0: Decimal(0),
                           -9: Decimal(3), -3: Decimal(3), 2: Decimal(3), 7: Decimal(3), 9: Decimal(3),
                           -2: Decimal(2), -1: Decimal(2), 1: Decimal(2), 5: Decimal(2), 6: Decimal(2)}
TIME_PER_TILE_DISTANCE = Decimal(300) if os.environ.get(
    "CIV_SPEED_RUN", None) != "1" else Decimal(30)
DIE_IDS = [DieId("die-lesy"), DieId("die-plane"), DieId("die-hory")]
TECH_BONUS_TOKENS = ["cheapDie", "star", "obyvatel20",
                     "obyvatel40", "kultura5", "kultura10!"]


def dieName(id: DieId) -> str:
    # Why isn't this in entities?
    return {
        "die-lesy": "Lesní kostka",
        "die-plane": "Planinná kostka",
        "die-hory": "Horská kostka"
    }[id]


def briefDieName(id: DieId) -> str:
    # Why isn't this in entities?
    return {
        "die-lesy": "Lesní",
        "die-plane": "Planinná",
        "die-hory": "Horská"
    }[id]

# Type Aliases


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


class Team(EntityBase):
    color: str
    password: Optional[str]  # We use it to populate database
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
    # Any resource, base class for Resource, GenericResource;
    #   Do not instantiate
    #   TODO: Is there a simple way to disable __init__ for this base class? ###
    typ: Optional[Tuple[ResourceType, int]] = None
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


class EntityWithCost(EntityBase):
    cost: Dict[Resource, Decimal]
    points: int
    # duplicates: items in Tech.unlocks
    unlockedBy: List[Tuple[EntityWithCost, DieId]] = []

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
    def unlockingDice(self) -> Set[dieId]:
        return set(d for e, d in self.unlockedBy)


class Tech(EntityWithCost):
    unlocks: List[Tuple[Entity, DieId]] = []
    bonuses: List[str]
    flavor: str

    @property
    def unlocksVyrobas(self) -> Set[Vyroba]:
        return set(x for x, _ in self.unlocks if isinstance(x, Vyroba))

    @property
    def unlocksTechs(self) -> Set[Vyroba]:
        return set(x for x, _ in self.unlocks if isinstance(x, Tech))

    @property
    def unlocksBuilding(self) -> Set[Building]:
        return set(x for x, _ in self.unlocks if isinstance(x, Building))

    @property
    def hasStar(self) -> bool:
        return "star" in self.bonuses

    def allowedDie(self, target: Entity) -> Set[DieId]:
        return set(d for e, d in self.unlocks if e == target)


class TileFeature(EntityBase):
    pass


class Vyroba(EntityWithCost):
    reward: Tuple[Resource, Decimal]
    requiredFeatures: List[TileFeature]
    flavor: str


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

    def __new__(cls, entities: Iterable[Entity], plague: Optional["PlagueData"] = None) -> Entities:
        x = super().__new__(cls, {x.id: x for x in entities})
        x.plague = plague
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

    @property
    def basicFoodProduction(self) -> Resource:
        return self["pro-bobule"]

    @cached_property
    def resources(self) -> frozendict[EntityId, Resource]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Resource)})

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
    def buildings(self) -> frozendict[EntityId, Building]:
        return frozendict({k: v for k, v in self.items()
                           if isinstance(v, Building)})

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
        return Entities([self._gameOnlyView(v) for v in self.values()], self.plague)
