from collections import Counter
from decimal import Decimal
import json

from game.actions.common import DIE_IDS

from .entities import Entities, NaturalResource, Resource, ResourceGeneric, ResourceType, Tech, Vyroba

LEVEL_SYMBOLS_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]

class EntityParser():
    entities = {}
    errors = []


    def __init__(self, fileName):
        with open(fileName) as file:
            self.data = json.load(file)        
        self.fileName = fileName


    def parseTypString(self, s):
        typId = s[:s.rfind("-")]
        typLevel = int(s[s.rfind("-")+1:])
        return (self.entities[typId], typLevel)


    def parseCostSingle(self, s):
        chunks = [x.strip() for x in s.strip().split(":")]
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


    def parseDieCost(self, s):
        assert s.split(":")[0] in DIE_IDS, "Unknown die id: " + s.split(":")[0]
        return (s.split(":")[0], int(s.split(":")[1]))


    def parseLineGeneric(self, c, line):
        e = c(id=line[0], name=line[1])
        self.entities[line[0]] = e


    def parseLineTyp(self, line):
        assert line[0][0:4] == "typ-", "Invalid id-prefix: \"" + line[0][0:4] + "\" (expected \"typ-\")"

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

        if line[2] == "":
            return

        id = "pro" + id[3:]
        pro = Resource(id=id, name=line[2], typ=typData, produces=mat)
        self.entities[id] = pro

    
    def parseLineTechStep1(self, line):
        cost = self.parseCost(line[4])
        cost[self.entities["res-prace"]] = Decimal(line[3])
        tech = Tech(id=line[0], name=line[1], diePoints=int(line[2]), cost=cost)
        self.entities[line[0]] = tech


    def parseLineTechStep2(self, line):
        if len(line[5]) <= 1:
            return

        tech = self.entities[line[0]]
        chunks = [x.strip().split(":") for x in line[5].split(",")]
        data = map(lambda x: (x[0].strip(), x[1].strip()), chunks)
        edges = {self.entities[x[0]]: x[1] for x in data}
        tech.edges = edges


    def parseLineVyroba(self, line):
        cost = self.parseCost(line[5])
        cost[self.entities["res-prace"]] = Decimal(line[3])
        cost[self.entities["res-obyvatel"]] = Decimal(line[4])
        reward = self.parseCostSingle(line[6])
        assert type(reward[0]) is not ResourceGeneric, "Vyroba cannot reward generic resource \"" + str(reward[0]) + "\""
        die = self.parseDieCost(line[2])

        techs = []
        for x in line[7].split(","):
            x = x.strip()
            tech = self.entities[x]
            assert tech != None, "Unknown unlocking tech " + x
            techs.append(tech)
        vyroba = Vyroba(id=line[0], name=line[1], die=die, cost=cost, reward=reward, techs=techs)
        self.entities[line[0]] = vyroba


    def parseSheet(self, sheetId, dataOffset, parser, prefixes, asserts=True):
        if (len(self.errors) > 0):
            print("Skipping " + sheetId + " parsing")
            return

        for lineId, line in enumerate(self.data[sheetId][dataOffset:], start = 1 + dataOffset):
            try:
                if asserts:
                    assert not line[0] in self.entities, "Id already exists: " + line[0]
                    assert line[0][3] == '-', "Id prefix must be 3 chars long, got \"" + line[0] + "\""
                    assert line[0][:3] in prefixes, "Invalid id prefix: \"" + line[0][:3] + "\" (allowed prefixes: " + prefixes + ")"
                parser(line)

            except Exception as e:
                message = sheetId + "." + str(lineId) + ": " + str(e.args[0])
                self.errors.append(message)
        for e in self.errors:
            print("  " + e)


    def parseTypes(self):
        self.parseSheet("type", 1, lambda x: self.parseLineTyp(x), ["typ"])

    def parseMaterials(self):
        self.parseSheet("material", 1, lambda x: self.parseLineMaterial(x), ["res", "mat"])

    def parseNaturalResources(self):
        self.parseSheet("naturalResource", 1, lambda x: self.parseLineGeneric(NaturalResource, x), ["nat"])

    def parseTechs(self):
        self.parseSheet("tech", 1, lambda x: self.parseLineTechStep1(x), ["tec"])
        self.parseSheet("tech", 1, lambda x: self.parseLineTechStep2(x), ["tec"], asserts=False)

    def parseVyrobas(self):
        self.parseSheet("vyroba", 2, lambda x: self.parseLineVyroba(x), ["vyr"])
    


    def parse(self) -> Entities:
        self.parseTypes()
        self.parseMaterials()
        self.parseNaturalResources()
        self.parseTechs()
        self.parseVyrobas()

        entities = Entities(self.entities.values())

        print()
        if (len(self.errors)) > 0:
            print("ERROR: Failed to parse file " + self.fileName + ". Errors are listed above")
            return None
        else:
            c = Counter([x[:3] for x in entities.keys()])
            for x in ["natuaral resources", "types of resourcesa", "materials", "resourses", "productions", "techs", "vyrobas"]:
                print("    " + x + ": " + str(c[x[:3]]))
            print("SUCCESS: Created " + str(len(entities)) + " entities from " + self.fileName)

        return entities