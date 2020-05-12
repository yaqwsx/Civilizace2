from .entity import EntityModel, GameDataModel
from .resource import ResourceTypeModel, ResourceModel

class Parser():
    SHEET_MAP= {
        "type": 4,
        "res": 3,
        "tech": 1,
        "edge": 2,
        "vyr": 5
    }

    warnings = None

    def _logWarning(self, message):
        self.warnings.append(message)
        print(message)

    def _addResourceTypes(self):
        print("Parsing resource types")
        myRaw = self.raw[self.SHEET_MAP["type"]]

        for n, line in enumerate(myRaw[1:], start=1):
            print("Parsing type " + str(line))
            if len(line) < 3:
                self._logWarning("Typy." + str(n) +": Málo parametrů (" + len(line) + "/3)")
                continue
            label = line[0]
            id = line[1]
            color = line[2]
            type = ResourceTypeModel.objects.create(id=id, label=label, color=color, data=self.data)
            type.save()

    def _addResources(self):
        print("Parsing resources")
        myRaw = self.raw[self.SHEET_MAP["res"]]

        for n, line in enumerate(myRaw[1:], start=1):
            print("Parsing resource " + str(line))
            if len(line) < 4:
                self._logWarning(message = "Zdroje." + str(n) +": Málo parametrů (" + len(line) + "/4)")
                continue

            label = line[0]
            id = line[1]
            typeRaw = line[2]
            icon = line[3]
            if typeRaw == "-":
                res = ResourceModel.objects.create(id=id, label=label, type=None, level=1, icon=icon, data=self.data)
                res.save()
            else:
                chunks = typeRaw.split("-")
                if len(chunks) < 2:
                    self._logWarning("Zdroje." + str(n) +": Typ neobsahuje level")
                    continue
                try:
                    level = int(chunks[1])
                except ValueError:
                    self._logWarning("Zdroje." + str(n) +": Neznamy level " + chunks[1])
                    continue
                try:
                    type = chunks[0]
                    typeId = "type-" + type
                    typeRef = ResourceTypeModel.objects.get(id="type-"+type)
                except Exception: # TODO: Look up the correct error
                    self._logWarning("Zdroje." + str(n) +": Neznamy typ " + chunks[0])
                    continue

                mat = ResourceModel.objects.create(
                    id=id, label=label, type=typeRef,
                    level=level, icon=icon, data=self.data)
                mat.save()

                prodId = "prod" + id[3:]
                prodLabel = "Produkce: " + label
                prod = ResourceModel.objects.create(
                    id=prodId, label=prodLabel, type=typeRef,
                    level=level, icon=icon, isProduction=True,
                    data=self.data)
                prod.save()


    def _addTechs(self):
        pass

    def _addEdges(self):
        pass

    def _addVyrobas(self):
        pass


    def parse(self, rawData):
        # clear all entities
        self.warnings = []

        for data in GameDataModel.objects.all():
            data.delete()

        # create data entity
        self.data = GameDataModel.objects.create()
        self.raw = rawData

        # parse each entity type
        self._addResourceTypes()
        self._addResources()

        warnings = self.warnings
        self.warnings = None
        return warnings