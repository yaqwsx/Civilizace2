import json

from .entities import Entities, Resource, ResourceType

    

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


    def parseSheet(self, sheetId, dataOffset, parser, prefixes):
        if (len(self.errors) > 0):
            print("Skipping " + sheetId + " parsing")
            return

        for lineId, line in enumerate(self.data[sheetId][dataOffset:], start = 1 + dataOffset):
            try:
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
        self.parseSheet("types", 1, lambda x: self.parseLineTyp(x), ["typ"])

    def parseMaterials(self):
        self.parseSheet("material", 1, lambda x: self.parseLineMaterial(x), ["res", "mat"])


    def parse(self) -> Entities:
        self.parseTypes()
        self.parseMaterials()

        entities = Entities(self.entities.values())

        print()
        if (len(self.errors)) > 0:
            print("ERROR: Failed to parse file " + self.fileName + ". Errors are listed above")
        else:
            print("SUCCESS: Created " + str(len(entities)) + " entities from " + self.fileName)

        return entities