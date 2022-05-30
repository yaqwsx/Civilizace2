from __future__ import annotations
import enum
from pydantic import BaseModel
from typing import List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal
from game.entities import *

class StateModel(BaseModel):
    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        for field in self.__fields__.values():
            if getattr(self, field.name) != getattr(other, field.name):
                return False
        return True

class ArmyState(enum.Enum):
    Idle = 0
    Marching = 1
    Occupying = 2

class ArmyGoal(enum.Enum):
    Occupy = 0
    Eliminate = 1
    Supply = 2
    Replace = 3


class ArmyId(StateModel):
    prestige: int
    team: Team

    def serialize(self):
        return (self.team.id, self.prestige)

    @classmethod
    def deserialize(cls, data, entities):
        return ArmyId(
            prestige=data[1],
            team=entities[data[0]])

    def __hash__(self):
        return self.team.__hash__() + self.prestige

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.team == other.team and self.prestige == other.prestige

class Army(StateModel):
    team: Team # duplicates: items in Team.armies
    prestige: int
    equipment: int=0 # number of weapons the army currently carries
    boost: int=-1 # boost added by die throw
    tile: Optional[MapTileEntity]=None
    state: ArmyState=ArmyState.Idle
    goal: Optional[ArmyGoal]=None

    @property
    def capacity(self) -> int:
        return self.prestige - BASE_ARMY_STRENGTH

    @property
    def id(self) -> ArmyId:
        return ArmyId(prestige=self.prestige, team=self.team)

    @property
    def strength(self) -> int:
        return self.equipment + BASE_ARMY_STRENGTH + max(0, self.boost)

    @property
    def isMarching(self) -> bool:
        return self.tile == None

    @property
    def isBoosted(self) -> bool:
        return self.boost >= 0

    def retreat(self, state: GameState) -> int:
        result = self.equipment
        tile = state.map.tiles[self.tile.index]
        if self.state == ArmyState.Occupying:
            assert tile.occupiedBy == self.id, "Army {} thinks its occupying a tile occupied by {}".format(self.id, tile.occupiedBy)
            tile.occupiedBy = None
        tile.inbound.discard(self.id)

        self.state = ArmyState.Idle
        self.equipment = 0
        self.boost = -1
        self.tile = None
        self.goal = None
        return result

    def occupy(self, tile: MapTile):
        if tile.occupiedBy == self.id: return
        assert tile.occupiedBy == None, "Nelze obsadit pole obsazené cizí armádou"
        tile.occupiedBy = self.id
        tile.inbound.discard(self.id)

        self.state = ArmyState.Occupying
        self.boost = -1
        self.tile = tile.entity
        self.goal = None

    def destroyEquipment(self, casualties: int) -> int:
        self.equipment = max(0, self.equipment - casualties)
        return BASE_ARMY_STRENGTH + self.equipment


class MapTile(StateModel): # Game state elemnent
    entity: MapTileEntity
    occupiedBy: Optional[ArmyId]=None
    buildings: Dict[Building, Optional[TeamId]]={} # TeamId is stored for stats purposes only
    inbound: Set[ArmyId]=set()

    # We have to provide extra serialization/deserialization as the model uses
    # polymorphism (MapTile/HomeTile)
    def serialize(self):
        vals = super().serialize()
        vals["tt"] = "M"
        return vals

    @classmethod
    def deserialize(cls, data, entities):
        deducedCls = {
            "H": HomeTile,
            "M": MapTile
        }[data["tt"]]

        source = {}
        for field in deducedCls.__fields__.values():
            source[field.name] = deducedCls._deserialize(data[field.name], field, entities)
        return deducedCls.parse_obj(source)

    @property
    def name(self) -> str:
        return self.entity.name

    @property
    def index(self) -> int:
        return self.entity.index

    @property
    def parcelCount(self) -> int:
        return self.entity.parcelCount

    @property
    def richness(self) -> int:
        return self.entity.richness

    @property
    def features(self) -> List[TileFeature]:
        return self.entity.naturalResources + self.buildings.keys()

    @property
    def id(self) -> EntityId:
        return self.entity.id

    @property
    def defenseBonus(self) -> int:
        return 0


class HomeTile(MapTile):
    team: Team
    roadsTo: List[MapTileEntity]=[]

    def serialize(self):
        vals = super().serialize()
        vals["tt"] = "H"
        return vals

    @classmethod
    def createInitial(cls, team: Team, tile: MapTileEntity, entities: Entities) -> HomeTile:
        return HomeTile(name="Domovské pole " + team.name,
                       index=tile.index,
                       parcelCount=3,
                       richness=0,
                       naturalResources = tile.naturalResources)


class MapState(StateModel):
    size: int=MAP_SIZE
    tiles: Dict[int, MapTile]
    homeTiles: Dict[Team, HomeTile]

    def _getRelativeIndex(self, team: Team, tile: MapTileEntity) -> int:
        home = self.homeTiles[team]
        assert home != None, "Team {} has no home tile".format(team.id)
        relIndex = tile.index - home.index
        relIndexOffset = relIndex + self.size/2
        return (relIndexOffset % self.size) - self.size/2

    def getRawDistance(self, team: Team, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        return TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE

    def getActualDistance(self, team: Team, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        distance = TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE
        home = self.homeTiles[team]
        if relativeIndex != tile.index - home.index:
            distance *= Decimal(0.8) # Tiles are around the map
        multiplier = 1
        if tile in home.roadsTo:
            multiplier -= 0.5
        tileState = self.tiles[tile.index]
        if tileState.occupiedBy != None and tileState.occupiedBy.team == team:
            multiplier -= 0.5
        return Decimal(float(distance) * multiplier)

    def getHomeTile(self, team: Team) -> HomeTile:
        return self.homeTiles.get(team)


    @classmethod
    def createInitial(cls, entities: Entities) -> MapState:
        return MapState(
            tiles = {tile.index: MapTile(entity=tile) for tile in entities.tiles.values() if tile.index % 4 != 1},
            homeTiles = {}
        )


class TeamState(StateModel):
    team: Team
    redCounter: Decimal
    blueCounter: Decimal

    techs: Set[Tech]
    researching: Set[Tech] = set()
    armies: Dict[ArmyId, Army]

    resources: Dict[Resource, Decimal]
    storage: Dict[Resource, Decimal]

    def getUnlockingDice(self, entity: EntityWithCost) -> Set[str]:
        dice = set()
        for unlock in entity.unlockedBy:
            if unlock[0] in self.techs:
                dice.add(unlock[1])
        return dice

    @property
    def work(self) -> Decimal:
        # TBA: Think of a better way...
        for r, a in self.resources.items():
            if r.id == "res-prace":
                return a
        return 0

    @classmethod
    def createInitial(cls, team: Team, entities: Entities) -> TeamState:
        armies = {ArmyId(prestige=x, team=team): Army(team=team, prestige=x) for x in STARTER_ARMY_PRESTIGES}
        return TeamState(
            team=team,
            redCounter=0,
            blueCounter=0,
            techs=[entities["tec-start"]],
            armies=armies,
            resources={
                entities["res-prace"]: Decimal(50),
                entities["pro-drevo"]: Decimal(20)
            },
            storage={
                entities["mat-drevo"]: Decimal(10)
            }
        )


class GameState(StateModel):
    turn: int
    teamStates: Dict[Team, TeamState]
    map: MapState

    def getArmy(self, id: ArmyId) -> Army:
        return self.teamStates[id.team].armies.get(id) if id != None else None

    @classmethod
    def createInitial(cls, entities: Entities) -> GameState:
        teamStates = {}
        for v in entities.teams.values():
            teamStates[v] = TeamState.createInitial(v, entities)

        return GameState(
            turn=0,
            teamStates={team: TeamState.createInitial(team, entities) for team in entities.teams.values()},
            map=MapState.createInitial(entities)
        )

