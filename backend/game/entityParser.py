from decimal import Decimal
import json
from typing import (Callable,
                    Dict,
                    List,
                    Optional,
                    Protocol,
                    Tuple,
                    TypedDict)

from .entities import (DIE_IDS,
                       Building,
                       DieId,
                       Entities,
                       Entity,
                       EntityWithCost,
                       MapTileEntity,
                       NaturalResource,
                       Org,
                       OrgRole,
                       Resource,
                       ResourceType,
                       Team,
                       Tech,
                       TileFeature,
                       Vyroba)

DICE_IDS = ["die-lesy", "die-plane", "die-hory"]
DIE_ALIASES = {"die-les": "die-lesy", "les": "die-lesy", "lesy": "die-lesy",
               "hory": "die-hory", "hora": "die-hory",
               "plan": "die-plane", "plane": "die-plane",
               "any": "die-any"}
LEVEL_SYMBOLS_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]
GUARANTEED_IDS = ["tec-start", "nat-voda", "tym-zeleni",
                  "res-prace", "res-obyvatel", "mat-zbrane"]


def readRole(s: str) -> OrgRole:
    s = s.lower()
    if s == "org":
        return OrgRole.ORG
    if s == "super":
        return OrgRole.SUPER
    raise RuntimeError(f"{s} is not a valid role")


class EntityParser():
    class _EntityWithCost(TypedDict):
        id: str
        name: str
        cost: Dict[Resource, Decimal]
        points: int

    def __init__(self,
                 data: Dict[str, List[List[str]]],
                 reportError: Optional[Callable[[str], None]] = None) -> None:
        self.errors: List[str] = []
        self.data = data

        if reportError:
            self.reportError = reportError
        else:
            self.reportError = self._reportError

    def _reportError(self, error: str) -> None:
        print(error)

    def parseTypString(self, s: str) -> Tuple[ResourceType, int]:
        assert len(s.split("-")) == 3, "Invalid resourceType id: " + s
        typId = s[:s.rfind("-")]
        typLevel = int(s[s.rfind("-")+1:])
        return (self.entities[typId], typLevel)

    def parseCostSingle(self, s: str) -> Tuple[Resource, Decimal]:
        chunks = [x.strip() for x in s.strip().split(":")]
        assert len(chunks) == 2, "Invalid cost property \"" + \
            s + "\" (expecting \"resourceId:amount\")"
        assert chunks[0][3] == "-", "Invalid entity id: " + chunks[0]
        assert self.entities.get(
            chunks[0], None), f"Neznámý zdroj: {chunks[0]}"
        return (self.entities[chunks[0]], Decimal(chunks[1]))

    def parseCost(self, s: str) -> Dict[Resource, Decimal]:
        if len(s) <= 2:
            return {}
        return {x[0]: x[1] for x in map(self.parseCostSingle, s.split(","))}

    def getEdgesFromField(self,
                          field: str
                          ) -> List[Tuple[Entity, str]]:
        if len(field) < 4:
            return []

        chunks = [x.strip() for x in field.split(",")]
        result = []
        for chunk in chunks:
            split = chunk.split(":")
            assert len(split) == 2, "Invalid edge: " + chunk
            targetId = split[0]
            assert targetId in self.entities, "Unknown unlocking tech id \""\
                + targetId \
                + ("\"" if targetId[3] ==
                   "-" else "\": Id is not exactly 3 symbols long")
            targetEntity = self.entities[targetId]

            die = split[1].strip()
            if die in DIE_ALIASES:
                die = DIE_ALIASES[die]
            if die == "die-any":
                for die in DICE_IDS:
                    result.append((targetEntity, die))
                continue
            assert die in DICE_IDS, "Unknown unlocking die id \"" + \
                die + "\". Allowed dice are " + str(DICE_IDS)
            result.append((targetEntity, die))
        return result

    def kwargsEntityWithCost(self,
                             line: List[str],
                             includeEdges: bool = True
                             ) -> _EntityWithCost:
        cost = self.parseCost(line[3])
        cost[self.entities["res-prace"]] = Decimal(line[2])
        return {'id': line[0],
                'name': line[1],
                'cost': cost,
                'points': int(line[4])}

    def parseDieCost(self, s: str) -> Tuple[DieId, int]:
        assert s.split(":")[0] in DIE_IDS, "Unknown die id: " + s.split(":")[0]
        return (s.split(":")[0], int(s.split(":")[1]))

    class _LineParser(Protocol):
        def __call__(self, id: str, name: str) -> Entity:
            ...

    def parseLineGeneric(self, c: _LineParser, line: List[str]) -> None:
        e = c(id=line[0], name=line[1])
        self.entities[line[0]] = e

    def parseLineTeam(self, line: List[str]) -> None:
        if len(line) != 6:
            raise RuntimeError(f"Team line {line} doesn't look like team line")
        tiles = [tile for tile in self.entities.values() if isinstance(
            tile, MapTileEntity) and tile.name == line[5]]
        assert len(tiles) == 1, f"Invalid set of team starting tiles: {tiles}"
        assert line[4] in ["TRUE", "FALSE"], \
            f"Invalid team visibility: {line[4]}"

        team = Team(
            id=line[0],
            name=line[1],
            color=line[2],
            password=line[3],
            visible=bool(line[4]),
            homeTileId=tiles[0].id
        )
        self.entities[team.id] = team

    def parseLineOrg(self, line: List[str]) -> None:
        if len(line) != 4:
            raise RuntimeError(f"Invalid org line: {line}")
        org = Org(
            id=line[0],
            name=line[1],
            role=readRole(line[2]),
            password=line[3])
        self.entities[org.id] = org

    def parseLineTyp(self, line: List[str]) -> None:
        typ = ResourceType(id=line[0], name=line[1], productionName=line[2],
                           colorName=line[3], colorVal=int(line[4], 0))
        self.entities[line[0]] = typ

    def parseLineMaterial(self, line: List[str]) -> None:
        id = line[0]
        if id[:3] == "res":
            self.entities[id] = Resource(id=id, name=line[1], icon=line[4])
            return

        icon = line[4]
        assert len(icon) >= 8, f"Příliš krátký název ikony: \"{line[4]}\""

        typData = self.parseTypString(line[3])
        mat = Resource(id=id, name=line[1], typ=typData, icon=icon)
        self.entities[id] = mat

        assert len(line[2]) > 0, "Name of production cannot be empty"

        id = "pro" + id[3:]
        pro = Resource(
            id=id,
            name=line[2],
            typ=typData,
            produces=mat,
            icon=icon[:-5]+"b.svg")
        self.entities[id] = pro

    def parseLineTechCreateEntity(self, line: List[str]) -> None:
        tech = Tech(
            flavor=line[7],
            **self.kwargsEntityWithCost(line, includeEdges=False))
        self.entities[line[0]] = tech

    def parseLineTechAddUnlocks(self, line: List[str]) -> None:
        tech = self.entities[line[0]]
        assert isinstance(tech, Tech)
        unlocks = self.getEdgesFromField(
            line[5]) + self.getEdgesFromField(line[6])
        for unlock in unlocks:
            target = unlock[0]
            if not isinstance(target, EntityWithCost):
                print(target)
                print(unlock)
            assert isinstance(target, EntityWithCost), \
                f"Cannot unlock entity without a cost: {target}"
            target.unlockedBy.append((tech, unlock[1]))
        tech.unlocks += unlocks

    def getFeaturesFromField(self,
                             field: str,
                             onlyNaturals: bool = False) -> List[TileFeature]:
        if len(field) < 2:
            return []
        result = []
        for x in [x.strip() for x in field.split(",")]:
            assert x in self.entities, "Unknown entity: " + x
            feature = self.entities[x]
            assert isinstance(feature, TileFeature), \
                f"Entity is not a tile feature: {x}({type(feature).__name__ })"
            if onlyNaturals:
                assert isinstance(feature, NaturalResource), \
                    f'Feature "{x}" is not a natural resource, \
                        but a {type(x).__name__}'
            result.append(feature)
        return result

    def parseLineBuilding(self, line: List[str]) -> None:
        build = Building(
            requiredFeatures=self.getFeaturesFromField(
                line[5],
                onlyNaturals=True),

            **self.kwargsEntityWithCost(line),
            icon=line[6])

        self.entities[line[0]] = build

    def parseLineVyroba(self, line: List[str]) -> None:
        reward = self.parseCostSingle(line[6])
        assert not reward[0].isGeneric, \
            f'Vyroba cannot reward generic resource "{reward[0]}"'
        requiredFeatures = self.getFeaturesFromField(line[7])
        flavor = line[8]
        vyroba = Vyroba(reward=reward, requiredFeatures=requiredFeatures,
                        flavor=flavor, **self.kwargsEntityWithCost(line))
        assert "res-obyvatel" not in vyroba.cost, \
            "Cannot declare Obyvatel cost explicitly, \
            use column cena-obyvatel instead"

        obyvatelCost = Decimal(line[5] if len(line[5]) > 0 else 0)
        if obyvatelCost != 0:
            vyroba.cost[self.entities["res-obyvatel"]] = obyvatelCost

        edges = self.getEdgesFromField(line[9] if len(line) > 9 else "")
        for edge in edges:
            tech = edge[0]
            assert isinstance(tech, Tech), f"Neznámý tech k odemčení: {tech}"
            assert isinstance(edge[1], Decimal), \
                f"Neznámá cena odemčení: {edge[1]}"
            vyroba.unlockedBy.append(edge)
            tech.unlocks.append((vyroba, edge[1]))
        self.entities[line[0]] = vyroba

    def parseLineTile(self, line: List[str]) -> None:
        id = "map-tile" + line[1].rjust(2, "0")
        name = line[0].upper()
        assert id not in self.entities, f"Id already exists: {id}"
        index = int(line[1])
        resources = [self.entities[x.strip()] for x in line[2].split(",")]
        tile = MapTileEntity(
            id=id,
            name=name,
            index=index,
            naturalResources=resources,
            parcelCount=int(line[3]), richness=int(line[4]))
        self.entities[id] = tile

    def parseSheet(self,
                   sheetId: str,
                   dataOffset: int,
                   parser: Callable[[List[str]], None],
                   prefixes: List[str],
                   asserts: bool = True) -> None:
        if (len(self.errors) > 0):
            return

        for lineId, line in enumerate(
                self.data[sheetId][dataOffset:],
                start=1 + dataOffset):
            try:
                if asserts:
                    assert not line[0] in self.entities, \
                        f"Id already exists: {line[0]}"
                    assert line[0][3] == '-', \
                        f'Id {line[0]} prefix must be 3 chars long, \
                            got "{line[0]}"'
                    assert line[0][:3] in prefixes, \
                        f'Invalid id prefix: {line[0][:3]} \
                            (allowed prefixes: {prefixes})'
                    assert len(line[1]) >= 3, "Entity name cannot be empty"

                parser(line)

            except Exception as e:
                message = sheetId + "." + str(lineId) + ": " + str(e.args[0])
                self.errors.append(message)

        for err in self.errors:
            self.reportError("  " + err)

    def parseTeams(self) -> None:
        self.parseSheet("teams", 1, self.parseLineTeam, ["tym"])

    def parseOrgs(self) -> None:
        self.parseSheet("orgs", 1, self.parseLineOrg, ["org"])

    def parseTypes(self) -> None:
        self.parseSheet("type", 1, lambda x: self.parseLineTyp(x), ["typ"])

    def parseMaterials(self) -> None:
        self.parseSheet(
            "material", 1, lambda x: self.parseLineMaterial(x), ["res", "mat"])

    def parseNaturalResources(self) -> None:
        self.parseSheet("naturalResource",
                        1,
                        lambda x: self.parseLineGeneric(
                            lambda id, name: NaturalResource(id=id, name=name),
                            x),
                        ["nat"])

    def parseBuildings(self) -> None:
        self.parseSheet(
            "building", 1, lambda x: self.parseLineBuilding(x), ["bui"])

    def parseVyrobas(self) -> None:
        self.parseSheet(
            "vyroba", 1, lambda x: self.parseLineVyroba(x), ["vyr"])

    def parseTiles(self) -> None:
        self.parseSheet("tile",
                        1,
                        lambda x: self.parseLineTile(
                            x),
                        ["map"],
                        asserts=False)

    def parseTechsEmpty(self) -> None:
        self.parseSheet(
            "tech", 1, lambda x: self.parseLineTechCreateEntity(x), ["tec"])

    def parseTechsFill(self) -> None:
        self.parseSheet("tech", 1, lambda x: self.parseLineTechAddUnlocks(x), [
                        "tec"], asserts=False)

    def checkMap(self, entities: Entities) -> None:
        if len(entities.teams) * 4 != len(entities.tiles):
            self.errors.append("World size is wrong: \
                There are {} tiles and {} teams \
                    (expecting 4 tiles per team)".format(
                len(entities.tiles),
                len(entities.teams)))
            return

        tiles = entities.tiles
        for i in range(len(tiles)):
            count = sum(1 for x in tiles.values() if x.index == i)
            if count > 1:
                self.errors.append(
                    "Tile index {} occured {} times".format(i, count))
            if count < 1:
                self.errors.append("Tile index {} missing".format(i))

    def buildGenericResources(self) -> None:
        newResources = []
        for e in self.entities.values():
            if not isinstance(e, ResourceType):
                continue
            for i in range(1, 7):
                newResources.append(Resource(
                    id=f"mge-{e.id[4:]}-{i}",
                    name=f"{e.name} {i}",
                    typ=(e, i),
                    icon=None
                ))
                newResources.append(Resource(
                    id=f"pge-{e.id[4:]}-{i}",
                    name=f"{e.productionName} {i}",
                    typ=(e, i),
                    produces=newResources[-1],
                    icon=None
                ))
        for r in newResources:
            self.entities[r.id] = r

    def hardcodeValues(self) -> None:
        work = self.entities["res-prace"]
        obyvatel = self.entities["res-obyvatel"]
        culture = self.entities["res-kultura"]

        obyvatel.produces = work
        culture.produces = obyvatel

    def checkUnlockedBy(self) -> None:
        if len(self.errors) > 0:
            return
        checked = 0
        for id, entity in self.entities.items():
            if not isinstance(entity, EntityWithCost):
                continue
            checked += 1
            if id == "tec-start" or id == "tec-epoch":
                continue
            if len(entity.unlockedBy) == 0:
                self.errors.append(
                    f"{id} ({entity.name}) nemá odemykající hranu")

    def parse(self) -> Entities:
        self.entities: Entities

        self.parseTypes()
        self.buildGenericResources()
        self.parseMaterials()
        self.parseNaturalResources()
        self.parseTechsEmpty()
        self.parseBuildings()
        self.parseTiles()
        self.parseVyrobas()
        self.parseTechsFill()

        self.parseTeams()
        self.parseOrgs()

        self.hardcodeValues()

        self.checkUnlockedBy()

        if len(self.errors) == 0:
            for id in GUARANTEED_IDS:
                if id not in self.entities:
                    message = f"Missing required id \"{id}\""
                    self.errors.append(message)
                    print(message)
            if len(self.errors) == 0:
                entities = Entities(self.entities.values())
                self.checkMap(entities)
                return entities
        for message in self.errors:
            print(message)
        raise RuntimeError(
            f"Found {len(self.errors)} errors. Entities are not complete")


def parseEntities(data: Dict[str, List[List[str]]],
                  reportError: Callable[[str], None]) -> Entities:
    parser = EntityParser(data, reportError)
    baseEntities = parser.parse()
    return Entities(baseEntities.values())


def loadEntities(fileName: str) -> Entities:
    with open(fileName) as file:
        data = json.load(file)

    parser = EntityParser(data)
    entities = parser.parse()
    return Entities(entities.values())
