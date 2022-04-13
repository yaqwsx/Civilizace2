import json

from .entities import Entities, ResourceType

class EntityParser():
    entities = {}
    errors = []


    def __init__(self, fileName):
        with open(fileName) as file:
            self.data = json.load(file)        
        self.fileName = fileName


    def parseLineType(self, line):
        assert len(line) > 4, "Line incomplete"
        assert not line[0] in self.entities, "Id already exists: " + line[0]

        typ = ResourceType(id=line[0], name=line[1], productionName=line[2],
            colorName=line[3], colorVal=int(line[4], 0))

        self.entities[line[0]] = typ


    def parseSheet(self, sheetId, dataOffset, parser):
        if (len(self.errors) > 0):
            print("Skipping " + sheetId + " parsing")
            return

        for lineId, line in enumerate(self.data[sheetId][dataOffset:], start = 1 + dataOffset):
            try:
                parser(line)
            except Exception as e:
                message = sheetId + "." + str(lineId) + ": " + str(e.args[0])
                self.errors.append(message)
        for e in self.errors:
            print("  " + e)


    def parseTypes(self):
        self.parseSheet("types", 1, (lambda x: self.parseLineType(x)))


    def parse(self) -> Entities:
        self.parseTypes()

        entities = Entities(self.entities.values())

        print()
        if (len(self.errors)) > 0:
            print("ERROR: Failed to parse file " + self.fileName + ". Errors are listed above")
        else:
            print("SUCCESS: File " + self.fileName + ": parsed successfully")

        return entities