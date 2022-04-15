from collections import Counter
from decimal import Decimal
import json
from msilib.schema import Error
from typing import List

from game.actions.common import DIE_IDS

from .entities import Building, Entities, MapTileEntity, NaturalResource, Resource, ResourceGeneric, ResourceType, Team, Tech, TileFeature, Vyroba

DICE_IDS = ["die-lesy", "die-plane", "die-hory"]
LEVEL_SYMBOLS_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]
GUARANTEED_IDS = ["tec-start", "nat-voda", "tym-zeleni", "res-prace", "res-obyvatel"]


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


    def getEdgesFromLine(self, line):
        if len(line[5]) < 4:
            return []

        chunks = [x.strip() for x in line[5].split(",")]
        result = []
        try:
            unlockedByList = [(chunk[0].strip(), chunk[1].strip()) for chunk in map(lambda x: [y.strip() for y in x.split(":")], chunks)]
        except Exception as e:
            raise RuntimeError("Failed to parse unlocking dice: " + line[5]) from e
        for chunk in chunks:
            split = chunk.split(":")
            assert len(split) == 2, "Invalid edge: " + chunk
            techId = split[0]
            die = split[1]
            assert die in DICE_IDS, "Unknown unlocking die id \"" + die + "\". Allowed dice are " + str(DICE_IDS)
            assert techId in self.entities, "Unknown unlocking tech id \"" + techId + ("\"" if techId[3] == "-" else "\": Id is not exactly 3 symbols long")
            tech = self.entities[techId]
            assert isinstance(tech, Tech), "Unlocking entity is not a tech: " + techId + ", but a " + type(tech).name
            result.append((tech, die))        
        return result


    def kwargsEntityWithCost(self, line, includeEdges = True):
        cost = self.parseCost(line[3])
        cost[self.entities["res-prace"]] = Decimal(line[2])
        return {'id': line[0], 
                'name':line[1], 
                'cost':cost, 
                'points': Decimal(line[4]), 
                "unlockedBy": self.getEdgesFromLine(line) if includeEdges else []}


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


    def parseLineTechStep1(self, line):
        tech = Tech(**self.kwargsEntityWithCost(line, includeEdges=False))
        self.entities[line[0]] = tech


    def parseLineTechStep2(self, line):
        tech = self.entities[line[0]]
        assert isinstance(tech, Tech)
        tech.unlockedBy = self.getEdgesFromLine(line)


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
        build = Building(requiredFeatures=self.getFeaturesFromField(line[6], onlyNaturals=True), **self.kwargsEntityWithCost(line))
        self.entities[line[0]] = build


    def parseLineVyroba(self, line):
        reward = self.parseCostSingle(line[7])
        assert not isinstance(reward[0], ResourceGeneric), "Vyroba cannot reward generic resource \"" + str(reward[0]) + "\""
        requiredFeatures = self.getFeaturesFromField(line[8])
        vyroba = Vyroba(reward=reward, requiredFeatures=requiredFeatures, **self.kwargsEntityWithCost(line))
        assert "res-obyvatel" not in vyroba.cost, "Cannot declare Obyvatel cost explicitly, use column cena-obyvatel instead"
        vyroba.cost[self.entities["res-obyvatel"]] = Decimal(line[6])
        self.entities[line[0]] = vyroba


    def parseLineTile(self, line, lineId):
        assert len(line[0]) == 1, "Map tiles should have single letter tag"
        id = "map-tile" + line[0].upper()
        assert not id in self.entities, "Id already exists: " + id
        index = lineId-2
        name = line[0].upper()
        resources = [self.entities[x.strip()] for x in line[1].split(",")]
        tile = MapTileEntity(id=id, name=name, index=index, naturalResources=resources,
                            parcelCount=int(line[2]), richness=int(line[3]))
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
                print(message)
                raise e
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

    def parseTechs(self):
        self.parseSheet("tech", 1, lambda x: self.parseLineTechStep1(x), ["tec"])
        self.parseSheet("tech", 1, lambda x: self.parseLineTechStep2(x), ["tec"], asserts=False)

    def parseBuildings(self):
        self.parseSheet("building", 1, lambda x: self.parseLineBuilding(x), ["bui"])

    def parseVyrobas(self):
        self.parseSheet("vyroba", 2, lambda x: self.parseLineVyroba(x), ["vyr"])

    def parseTiles(self):
        self.parseSheet("tile", 1, lambda x, y: self.parseLineTile(x, y), ["map"], asserts=False, includeIndex=True)



    def parse(self) -> Entities:
        self.entities = {}

        self.parseTeams()
        self.parseTypes()
        self.parseMaterials()
        self.parseNaturalResources()
        self.parseTechs()
        self.parseBuildings()
        self.parseTiles()
        self.parseVyrobas()

        for id in GUARANTEED_IDS:
            if not id in self.entities:
                self.errors.append("Missing required id \"" + id + "\"")

        entities = Entities(self.entities.values())

        print()
        if (len(self.errors)) > 0:
            print("ERROR: Failed to parse file " + self.fileName + ". Errors are listed above")
            return None
        else:
            c = Counter([x[:3] for x in entities.keys()])
            for x in ["tymy", "natuaral resources", "types of resources", "map tiles", "materials", "buildings", "resourses", "productions", "techs", "vyrobas"]:
                print("    " + x + ": " + str(c[x[:3]]))
            print("SUCCESS: Created " + str(len(entities)) + " entities from " + self.fileName)

        return entities
