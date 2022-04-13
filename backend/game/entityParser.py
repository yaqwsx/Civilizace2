import json

from game.entities import Entities, ResourceType

class EntityParser():
    entities = {}
    errors = []

    def __init__(self, fileName):
        with open(fileName) as file:
            self.data = json.load(file)        

    def parseType(self, line):
        print("  Parsing type " + str(line))
        assert len(line) > 4, "Line incomplete"
        assert not line[0] in self.entities, "Id already exists: " + line[0]

        typ = ResourceType(id=line[0], name=line[1], productionName=line[2],
            colorName=line[3], colorVal=line[4])

        self.entities[line[0]] = typ
        raise AssertionError("Failed to fail")

    def parseTypes(self):
        for lineId, line in enumerate(self.data["types"][1:], start=2):
            try:
                self.parseType(line)
            except Exception as e:
                message = "types:" + str(lineId) + ": " + str(e.args[0])
                self.errors.append(message)

    def parse(self) -> Entities:
        self.parseTypes()

        for e in self.errors:
            print(e)

        return None