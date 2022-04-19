from collections import Counter
from decimal import Decimal
import json
from typing import List

from game.actions.common import DIE_IDS

from .entities import Building, Entities, EntityWithCost, MapTileEntity, NaturalResource, Resource, ResourceGeneric, ResourceType, Team, Tech, TileFeature, Vyroba

DICE_IDS = ["die-lesy", "die-plane", "die-hory"]
LEVEL_SYMBOLS_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]
GUARANTEED_IDS = ["tec-start", "nat-voda", "tym-zeleni", "res-prace", "res-obyvatel", "mat-zbrane"]


class EntityParser():
    def __init__(self, fileName):
        self.errors = []
        with open(fileName) as file:
            self.data = json.load(file)
        self.fileName = fileName


    def parseTypString(self, s):
        assert len(s.split("-")) == 3, "Invalid resourceType id: " + s
        typId = s[:s.rfind("-")]
        typLevel = int(s[s.rfind("-")+1:])
        return (self.entities[typId], typLevel)


    def parseCostSingle(self, s):
        chunks = [x.strip() for x in s.strip().split(":")]
        assert len(chunks) == 2, "Invalid cost property \"" + s + "\" (expecting \"resourceId:amount\")"
        assert chunks[0][3] == "-", "Invalid entity id: " + chunks[0]
        if chunks[0].count("-") == 1:
            return (self.entities[chunks[0]], Decimal(chunks[1]))

        id = chunks[0]
        typData = self.parseTypString("typ" + id[3:])
        typ = typData[0]

        name = typ.productionName if id.startswith("pro") else typ.name
        name += " " + LEVEL_SYMBOLS_ROMAN[typData[1]]

        res = ResourceGeneric(id=chunks[0], name=name, typ=typData)
        return (res, Decimal(chunks[1]))


    def parseCost(self, s):
        if s.find(":") < 0:
            return {}
        return {x[0]: x[1] for x in map(self.parseCostSingle, s.split(","))}


    def getEdgesFromField(self, field, checkTypes = None):
        if len(field) < 4:
            return []

        chunks = [x.strip() for x in field.split(",")]
        result = []
        for chunk in chunks:
            split = chunk.split(":")
            assert len(split) == 2, "Invalid edge: " + chunk
            targetId = split[0]
            die = split[1]
            assert die in DICE_IDS, "Unknown unlocking die id \"" + die + "\". Allowed dice are " + str(DICE_IDS)
            assert targetId in self.entities, "Unknown unlocking tech id \"" + targetId + ("\"" if targetId[3] == "-" else "\": Id is not exactly 3 symbols long")
            targetEntity = self.entities[targetId]
            result.append((targetEntity, die))        
        return result


    def kwargsEntityWithCost(self, line, includeEdges = True):
        cost = self.parseCost(line[3])
        cost[self.entities["res-prace"]] = Decimal(line[2])
        return {'id': line[0], 
                'name':line[1], 
                'cost':cost, 
                'points': Decimal(line[4])}


    def parseDieCost(self, s):
        assert s.split(":")[0] in DIE_IDS, "Unknown die id: " + s.split(":")[0]
        return (s.split(":")[0], int(s.split(":")[1]))


    def parseLineGeneric(self, c, line):
        e = c(id=line[0], name=line[1])
        self.entities[line[0]] = e


    def parseLineTyp(self, line):
        typ = ResourceType(id=line[0], name=line[1], productionName=line[2],
            colorName=line[3], colorVal=int(line[4], 0))
        self.entities[line[0]] = typ


    def parseLineMaterial(self, line):
        id = line[0]
        if id[:3] == "res":
            self.entities[id] = Resource(id=id, name=line[1])
            return

        typData = self.parseTypString(line[3])
        mat = Resource(id=id, name=line[1], typ=typData)
        self.entities[id] = mat

        assert len(line[2]) > 0, "Name of production cannot be empty"

        id = "pro" + id[3:]
        pro = Resource(id=id, name=line[2], typ=typData, produces=mat)
        self.entities[id] = pro


    def parseLineTechCreateEntity(self, line):
        tech = Tech(**self.kwargsEntityWithCost(line, includeEdges=False))
        self.entities[line[0]] = tech


    def parseLineTechAddUnlocks(self, line):
        tech = self.entities[line[0]]
        assert isinstance(tech, Tech)
        unlocks = self.getEdgesFromField(line[5]) + self.getEdgesFromField(line[6])
        for unlock in unlocks:
            target = unlock[0]
            assert isinstance(target, EntityWithCost), "Cannot unlock entity without a cost: " + target
            target.unlockedBy.append((tech, unlock[1]))
        tech.unlocks = unlocks


    def getFeaturesFromField(self, field, onlyNaturals = False):
        if len(field) < 2:
            return []
        result = []
        for x in [x.strip() for x in field.split(",")]:
            assert x in self.entities, "Unknown entity: " + x
            feature = self.entities[x]
            assert isinstance(feature, TileFeature), "Entity is not a tile feature: " + x + " (" + type(feature).__name__ + ")"
            if onlyNaturals:
                assert isinstance(feature, NaturalResource), "Feature \"" + x + "\" is not a natural resource, but a " + type(x).name
            result.append(feature)
        return result


    def parseLineBuilding(self, line):
        build = Building(requiredFeatures=self.getFeaturesFromField(line[5], onlyNaturals=True), **self.kwargsEntityWithCost(line))
        self.entities[line[0]] = build


    def parseLineVyroba(self, line):
        reward = self.parseCostSingle(line[6])
        assert not isinstance(reward[0], ResourceGeneric), "Vyroba cannot reward generic resource \"" + str(reward[0]) + "\""
        requiredFeatures = self.getFeaturesFromField(line[7])
        vyroba = Vyroba(reward=reward, requiredFeatures=requiredFeatures, **self.kwargsEntityWithCost(line))
        assert "res-obyvatel" not in vyroba.cost, "Cannot declare Obyvatel cost explicitly, use column cena-obyvatel instead"
        vyroba.cost[self.entities["res-obyvatel"]] = Decimal(line[5]) if len(line[5]) > 0 else 0
        self.entities[line[0]] = vyroba


    def parseLineTile(self, line, lineId):
        assert len(line[0]) == 1, "Map tiles should have single letter tag"
        id = "map-tile" + line[1].rjust(2,"0")
        team=None
        name = line[0].upper()
        if line[5] != "":
            team = self.entities[line[5]]
            id="hom-tile"+team.id[4:]
        assert not id in self.entities, "Id already exists: " + id
        index = int(line[1])
        resources = [self.entities[x.strip()] for x in line[2].split(",")]
        tile = MapTileEntity(id=id, name=name, index=index, naturalResources=resources,
                            parcelCount=int(line[3]), richness=int(line[4]), homeTeam=team)
        self.entities[id] = tile


    def parseSheet(self, sheetId, dataOffset, parser, prefixes, asserts=True, includeIndex=False):
        if (len(self.errors) > 0):
            return

        for lineId, line in enumerate(self.data[sheetId][dataOffset:], start = 1 + dataOffset):
            try:
                if asserts:
                    assert not line[0] in self.entities, "Id already exists: " + line[0]
                    assert line[0][3] == '-', "Id prefix must be 3 chars long, got \"" + line[0] + "\""
                    assert line[0][:3] in prefixes, "Invalid id prefix: \"" + line[0][:3] + "\" (allowed prefixes: " + prefixes + ")"
                    assert len(line[1]) >= 3, "Entity name cannot be empty"
                parser(line, lineId) if includeIndex else parser(line)

            except Exception as e:
                message = sheetId + "." + str(lineId) + ": " + str(e.args[0])
                self.errors.append(message)
        for e in self.errors:
            print("  " + e)


    def parseTeams(self):
        self.parseSheet("teams", 1, lambda x: self.parseLineGeneric(Team, x), ["tym"])

    def parseTypes(self):
        self.parseSheet("type", 1, lambda x: self.parseLineTyp(x), ["typ"])

    def parseMaterials(self):
        self.parseSheet("material", 1, lambda x: self.parseLineMaterial(x), ["res", "mat"])

    def parseNaturalResources(self):
        self.parseSheet("naturalResource", 1, lambda x: self.parseLineGeneric(NaturalResource, x), ["nat"])

    def parseBuildings(self):
        self.parseSheet("building", 1, lambda x: self.parseLineBuilding(x), ["bui"])

    def parseVyrobas(self):
        self.parseSheet("vyroba", 1, lambda x: self.parseLineVyroba(x), ["vyr"])

    def parseTiles(self):
        self.parseSheet("tile", 1, lambda x, y: self.parseLineTile(x, y), ["map"], asserts=False, includeIndex=True)

    def parseTechs(self):
        self.parseSheet("tech", 1, lambda x: self.parseLineTechCreateEntity(x), ["tec"])
        self.parseSheet("tech", 1, lambda x: self.parseLineTechAddUnlocks(x), ["tec"], asserts=False)


    def checkMap(self, entities):
        if len(entities.teams) * 4 != len(entities.tiles):
            self.errors.append("World size is wrong: There are {} tiles and {} teams (expecting 4 tiles per team)".format(
                    len(entities.tiles), 
                    len(entities.teams)))
            return

        tiles = entities.tiles
        for i in range(len(tiles)):
            count = sum(1 for x in tiles.values() if x.index == i)
            if count > 1:
                self.errors.append("Tile index {} occured {} times".format(i, count))
            if count < 1:
                self.errors.append("Tile index {} missing".format(i))


    def parse(self) -> Entities:
        self.entities = {}

        self.parseTeams()
        self.parseTypes()
        self.parseMaterials()
        self.parseNaturalResources()
        self.parseBuildings()
        self.parseTiles()
        self.parseVyrobas()
        self.parseTechs()

        for id in GUARANTEED_IDS:
            if not id in self.entities:
                self.errors.append("Missing required id \"" + id + "\"")

        entities = Entities(self.entities.values())
        self.checkMap(entities)

        if (len(self.errors)) > 0:
            for message in self.errors:
                print("  " + message)
            print("ERROR: Failed to parse file " + self.fileName + ". Errors are listed above")
            return None
        else:
            print()
            c = Counter([x[:3] for x in entities.keys()])
            for x in ["tymy", "natuaral resources", "types of resources", "map tiles", "buildings", "resourses", "materials", "productions", "techs", "vyrobas"]:
                print("    " + x + ": " + str(c[x[:3]]))
            print("SUCCESS: Created " + str(len(entities)) + " entities from " + self.fileName)

        return entities
