from .entity import EntityModel, GameDataModel, DieModel
from .resource import ResourceTypeModel, ResourceModel
from .tech import TaskModel, TechModel, TechEdgeModel, TechEdgeInputModel

class Parser():
    SHEET_MAP= {
        "die": 7,
        "task": 6,
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

    def _addDice(self):
        print("Parsing dice")
        myRaw = self.raw[self.SHEET_MAP["die"]]

        for n, line in enumerate(myRaw[1:], start=1):
            print("Parsing die " + str(line))
            if len(line) < 2:
                self._logWarning("Kostky." + str(n) + ": Málo parametrů (" + len(line) + "/2)")
                continue
            label = line[0]
            id = line[1]
            die = DieModel.objects.create(id=id, label=label, data=self.data)
            die.save()

    def _addTasks(self):
        print("Parsing tasks")
        myRaw = self.raw[self.SHEET_MAP["task"]]

        for n, line in enumerate(myRaw[1:], start=1):
            print("Parsing task " + str(line))
            if len(line) < 3:
                self._logWarning("Ukoly." + str(n) + ": Málo parametrů (" + len(line) + "/3)")
                continue
            label = line[0]
            id = line[1]
            text = line[2]
            task = TaskModel.objects.create(id=id, label=label, text=text, data=self.data)
            task.save()

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

            for i in range(2,7):
                mat = ResourceModel.objects.create(
                    id="mat-"+id[5:]+"-"+str(i),
                    label=label+" "+str(i),
                    type=type,
                    icon="images/placeholder.png",
                    level=i,
                    isProduction=False,
                    data=self.data
                )
                mat.save()
                prod = ResourceModel.objects.create(
                    id="prod-"+id[5:]+"-"+str(i),
                    label="Produkce: "+label+" "+str(i),
                    type=type,
                    icon="images/placeholder.png",
                    level=i,
                    isProduction=True,
                    data=self.data
                )
                prod.save()

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
        print("Parsing techs")
        myRaw = self.raw[self.SHEET_MAP["tech"]]

        for n, line in enumerate(myRaw[1:], start=1):
            line = line[:7]
            if line[1] == "":
                continue
            print("Parsing tech " + str(line))
            if len(line) < 7:
                self._logWarning("Tech." + str(n) +": Málo parametrů (" + str(len(line)) + "/7)")
                continue
            label = line[0]
            id = line[1]
            flavour = line[5]
            notes = line[4]
            image = line[3]

            try:
                culture = int(line[6])
            except Exception:
                self._logWarning("Tech." + str(n) + ": Kultura není číslo (" + str(line[6]) + ")")
                continue

            try:
                task = TaskModel.objects.get(id=line[2])
            except Exception:
                self._logWarning("Tech." + str(n) + ": Nezname ID ukolu (" + str(line[2]) + ")")
                continue

            tech = TechModel.objects.create(id=id, label=label, task=task, image=image, notes=notes, flavour=flavour, culture=culture, data=self.data)
            tech.save()

    def _addEdges(self):
        print("Parsing edges")
        myRaw = self.raw[self.SHEET_MAP["edge"]]

        for n, line in enumerate(myRaw[1:], start=1):
            line = line[:8]
            if line[1] == "":
                continue
            print("Parsing edge " + str(line))
            if len(line) < 8:
                self._logWarning("Edge." + str(n) +": Málo parametrů (" + str(len(line)) + "/8)")
                continue
            label = line[0]
            id = line[1]
            try:
                src = TechModel.objects.get(id=line[2])
            except TechModel.DoesNotExist:
                self._logWarning("Edge." + str(n) +": Nezname zdrojove ID (" + line[2] + ")")
                continue
            try:
                dst = TechModel.objects.get(id=line[3])
            except TechModel.DoesNotExist:
                self._logWarning("Edge." + str(n) +": Nezname cilove ID (" + line[3] + ")")
                continue

            try:
                chunks = line[4].split(":")
                die = DieModel.objects.get(id=chunks[0])
                dots = int(chunks[1])
            except:
                self._logWarning("Edge." + str(n) +": Nepodarilo se zpracovat udaje o kostce (" + line[4] + ")")
                continue

            edge = TechEdgeModel.objects.create(id=id, label=label, src=src, dst=dst, die=die, dots=dots, data=self.data)
            edge.save()

            def addInput(entry):
                chunks = entry.split(":")

                if len(chunks) < 2:
                    self._logWarning("Edge." + str(n) + ".vstup: Nepodarilo se zpracovat vstup (" + entry + ")")
                    return None

                try:
                    res = ResourceModel.objects.get(id=chunks[0])
                except ResourceModel.DoesNotExist:
                    self._logWarning("Edge." + str(n) + ".vstup: Nezname ID vstupu (" + entry + ")")
                    return None

                try:
                    amount = int(chunks[1])
                except Exception:
                    self._logWarning("Edge." + str(n) + ".vstup: Spatne formatovany pocet jednotek (" + entry + ")")
                    return None

                input = TechEdgeInputModel.objects.create(parent=edge, resource=res, amount=amount)
                input.save()
                return input

            try:
                prace = int(line[5])
                if prace:
                    addInput("res-prace:" + str(prace))
            except ValueError:
                pass

            try:
                obyvatel = int(line[6])
                if obyvatel:
                    addInput("res-obyvatel:" + str(obyvatel))
            except ValueError:
                pass

            if line[7] != "" and line[7] != "-":
                chunks = line[7].split(",")
                for chunk in chunks:
                    addInput(chunk.strip())

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
        self._addDice()
        self._addTasks()
        self._addResourceTypes()
        self._addResources()
        self._addTechs()
        self._addEdges()
        self._addVyrobas()

        warnings = self.warnings
        self.warnings = None
        return warnings