from game.data.vyroba import VyrobaModel, VyrobaInputModel, EnhancementInputModel, EnhancementModel
from .entity import EntityModel, EntitiesVersion, DieModel, AchievementModel, IslandModel, Direction
from .resource import ResourceTypeModel, ResourceModel
from .tech import TechModel, TechEdgeModel, TechEdgeInputModel

class Parser():
    SHEET_MAP = {
        "die": 7,
        "island": 6,
        "type": 4,
        "res": 3,
        "tech": 1,
        "edge": 2,
        "vyr": 5,
        "ach": 8,
        "enh": 9
    }

    warnings = None

    def _logWarning(self, message):
        self.warnings.append(message)
        print(message)

    def _addDice(self):
        print("Parsing dice")
        myRaw = self.raw[self.SHEET_MAP["die"]]

        for n, line in enumerate(myRaw[1:], start=1):
            if len(line) < 2:
                self._logWarning("Kostky." + str(n) + ": Málo parametrů (" + len(line) + "/2)")
                continue
            label = line[0]
            id = line[1]
            die = DieModel.manager.create(id=id, label=label, version=self.entitiesVersion)

    @staticmethod
    def romeLevel(number):
        return ["0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"][number]

    def _addResourceTypes(self):
        print("Parsing resource types")
        myRaw = self.raw[self.SHEET_MAP["type"]]

        for n, line in enumerate(myRaw[1:], start=1):
            if len(line) < 3:
                self._logWarning("Typy." + str(n) + ": Málo parametrů (" + len(line) + "/3)")
                continue
            label = line[0]
            id = line[1]
            color = line[2]
            type = ResourceTypeModel.manager.create(id=id, label=label,
                color=color, version=self.entitiesVersion)

            for i in range(2, 7):
                mat = ResourceModel.manager.create(
                    id="mat-" + id[5:] + "-" + str(i),
                    label=label + " " + Parser.romeLevel(i),
                    type=type,
                    icon="placeholder.png",
                    level=i,
                    version=self.entitiesVersion
                )
                prod = ResourceModel.manager.create(
                    id="prod-" + id[5:] + "-" + str(i),
                    label="Produkce: " + label + " " + Parser.romeLevel(i),
                    type=type,
                    icon="placeholder.png",
                    level=i,
                    version=self.entitiesVersion
                    )

    def _addResources(self):
        print("Parsing resources")
        myRaw = self.raw[self.SHEET_MAP["res"]]

        for n, line in enumerate(myRaw[1:], start=1):
            if len(line) < 4:
                self._logWarning(message="Zdroje." + str(n) + ": Málo parametrů (" + len(line) + "/4)")
                continue

            label = line[0]
            id = line[1]
            typeRaw = line[2]
            icon = line[3]
            if typeRaw == "-":
                res = ResourceModel.manager.create(id=id, label=label,
                    type=None, level=1, icon=icon, version=self.entitiesVersion)
            else:
                chunks = typeRaw.split("-")
                if len(chunks) < 2:
                    self._logWarning("Zdroje." + str(n) + ": Typ neobsahuje level")
                    continue
                try:
                    level = int(chunks[1])
                except ValueError:
                    self._logWarning("Zdroje." + str(n) + ": Neznamy level " + chunks[1])
                    continue
                try:
                    type = chunks[0]
                    typeId = "type-" + type
                    typeRef = ResourceTypeModel.manager.get(id="type-" + type, version=self.entitiesVersion)
                except Exception:  # TODO: Look up the correct error
                    self._logWarning("Zdroje." + str(n) + ": Neznamy typ " + chunks[0])
                    continue

                mat = ResourceModel.manager.create(id=id,
                    label=label,
                    type=typeRef,
                    level=level,
                    icon=icon,
                    version=self.entitiesVersion)

                prodId = "prod" + id[3:]
                prodLabel = "Produkce: " + label
                prod = ResourceModel.manager.create(id=prodId,
                    label=prodLabel,
                    type=typeRef,
                    level=level,
                    icon=icon.replace("a.png", "b.png"),
                    version=self.entitiesVersion)

    def _addTechs(self):
        print("Parsing techs")
        myRaw = self.raw[self.SHEET_MAP["tech"]]
        count = 0

        for n, line in enumerate(myRaw[1:], start=1):
            line = line[:12]
            if line[1] == "":
                continue
            if len(line) < 8:
                self._logWarning("Tech." + str(n) + ": Málo parametrů (" + str(len(line)) + "/8)")
                continue
            label = line[0]
            id = line[1]
            flavour = line[5]
            notes = line[4]
            image = line[3]
            nodeTag = line[7]
            defenseBonus = line[11]

            try:
                culture = int(line[6])
            except Exception:
                self._logWarning(f"Tech." + str(n) + ": Kultura není číslo (" + str(line[6]) + ")")
                continue

            try:
                epocha = int(line[10])
            except Exception:
                epocha = -1

            tech = TechModel.manager.create(id=id,
                label=label, image=image, notes=notes,
                flavour=flavour, culture=culture, nodeTag=nodeTag,
                epocha=epocha, version=self.entitiesVersion,
                defenseBonus=defenseBonus)
            count += 1
        print(f"   added {count} technologies")

    def _addEdges(self):
        print("Parsing edges")
        myRaw = self.raw[self.SHEET_MAP["edge"]]
        count = 0

        for n, line in enumerate(myRaw[1:], start=1):
            line = line[:8]
            if line[1] == "":
                continue
            if len(line) < 8:
                self._logWarning("Edge." + str(n) + ": Málo parametrů (" + str(len(line)) + "/8)")
                continue
            label = line[0]
            id = line[1]
            try:
                src = TechModel.manager.get(id=line[2], version=self.entitiesVersion)
            except TechModel.DoesNotExist:
                self._logWarning("Edge." + str(n) + ": Nezname zdrojove ID (" + line[2] + ")")
                continue
            try:
                dst = TechModel.manager.get(id=line[3], version=self.entitiesVersion)
            except TechModel.DoesNotExist:
                self._logWarning("Edge." + str(n) + ": Nezname cilove ID (" + line[3] + ")")
                continue

            try:
                chunks = line[4].split(":")
                die = DieModel.manager.get(id=chunks[0], version=self.entitiesVersion)
                dots = int(chunks[1])
            except:
                self._logWarning("Edge." + str(n) + ": Nepodarilo se zpracovat udaje o kostce (" + line[4] + ")")
                continue
            print(f"Creating {id}, {self.entitiesVersion}")
            edge = TechEdgeModel.manager.create(id=id, label=label, src=src,
                dst=dst, die=die, dots=dots, version=self.entitiesVersion)
            count += 1

            def addInput(entry):
                chunks = entry.split(":")

                if len(chunks) < 2:
                    self._logWarning("Edge." + str(n) + ".vstup: Nepodarilo se zpracovat vstup (" + entry + ")")
                    return None

                try:
                    res = ResourceModel.manager.get(id=chunks[0], version=self.entitiesVersion)
                except ResourceModel.DoesNotExist:
                    self._logWarning("Edge." + str(n) + ".vstup: Nezname ID vstupu (" + entry + ")")
                    return None

                try:
                    amount = int(chunks[1])
                except Exception:
                    self._logWarning("Edge." + str(n) + ".vstup: Spatne formatovany pocet jednotek (" + entry + ")")
                    return None

                input = TechEdgeInputModel.objects.create(
                    parent=edge, resource=res, amount=amount)
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
        print(f"  added {count} tech edges")

    def _addVyrobas(self):
        print("Parsing vyrobas")
        myRaw = self.raw[self.SHEET_MAP["vyr"]]
        centrum = TechModel.manager.get(id="build-centrum", version=self.entitiesVersion)

        for n, line in enumerate(myRaw[2:], start=2):
            line = line[:15]
            if line[1] == "":
                continue

            id = line[1]
            label = line[0]

            flavour = line[14] if len(line) >= 15 else ""

            try:
                chunks = line[2].split(":")
                die = DieModel.manager.get(id=chunks[0], version=self.entitiesVersion)
                dots = int(chunks[1])
            except DieModel.DoesNotExist:
                self._logWarning("Vyroba." + str(n) + ": Neznámé ID kostky (" + line[2] + ")")
                continue
            except ValueError:
                self._logWarning("Vyroba." + str(n) + ": Chyba v počtu bodů na kostce (" + line[2] + ")")
                continue

            try:
                chunks = line[6].split(":")
                output = ResourceModel.manager.get(id=chunks[0], version=self.entitiesVersion)
                amount = int(chunks[1])
            except ResourceModel.DoesNotExist:
                self._logWarning("Vyroba." + str(n) + ": Neznámé ID materiálu (" + line[6] + ")")
                continue
            except ValueError:
                self._logWarning("Vyroba." + str(n) + ": Chyba v počtu získaných zdrojů (" + line[6] + ")")
                continue

            try:
                tech = TechModel.manager.get(id=line[7], version=self.entitiesVersion)
            except TechModel.DoesNotExist:
                self._logWarning("Vyroba." + str(n) + ": Neznámé ID technologie (" + line[7] + ")")
                continue

            try:
                if line[8][:5] == "land-":
                    build = None
                else:
                    build = TechModel.manager.get(id=line[8], version=self.entitiesVersion)
            except TechModel.DoesNotExist:
                self._logWarning("Vyroba." + str(n) + ": Neznámé ID budovy (" + line[8] + ")")
                continue

            vyr = VyrobaModel.manager.create(id=id,
                label=label, flavour=flavour, tech=tech, build=build,
                output=output, amount=amount, die=die, dots=dots, version=self.entitiesVersion)

            def addInput(entry):
                chunks = entry.split(":")

                if len(chunks) < 2:
                    self._logWarning("Vyroba." + str(n) + ".vstup: Nepodarilo se zpracovat vstup (" + entry + ")")
                    return None

                try:
                    res = ResourceModel.manager.get(id=chunks[0], version=self.entitiesVersion)
                except ResourceModel.DoesNotExist:
                    self._logWarning("Vyroba." + str(n) + ".vstup: Nezname ID vstupu (" + entry + ")")
                    return None

                try:
                    amount = int(chunks[1])
                except Exception:
                    self._logWarning("Vyroba." + str(n) + ".vstup: Spatne formatovany pocet jednotek (" + entry + ")")
                    return None

                input = VyrobaInputModel.objects.create(
                    parent=vyr, resource=res,
                    amount=amount)
                return input

            try:
                prace = int(line[3])
                if prace:
                    addInput("res-prace:" + str(prace))
            except ValueError:
                pass

            try:
                obyvatel = int(line[4])
                if obyvatel:
                    addInput("res-obyvatel:" + str(obyvatel))
            except ValueError:
                pass

            if line[5] != "" and line[5] != "-":
                chunks = line[5].split(",")
                for chunk in chunks:
                    addInput(chunk.strip())

            # ==========================================================
            # Adding material vyrobas version
            if line[9] != "TRUE":
                continue
            if not line[6].startswith("prod-"):
                continue

            try:
                chunks = line[6].split(":")
                output = ResourceModel.manager.get(id="mat-" + chunks[0][5:], version=self.entitiesVersion)
            except ResourceModel.DoesNotExist:
                self._logWarning("Vyroba." + str(n) + ": Nepodarilo se prevést ID na materiál (" + line[6] + ")")
                continue


            id = id + "-material"
            label = "Materiál: " + label

            vyr = VyrobaModel.manager.create(id=id,
                label=label, flavour=flavour, tech=tech, build=centrum,
                output=output, amount=amount, die=die, dots=dots, version=self.entitiesVersion)

            def addMatInput(entry):
                chunks = entry.split(":")

                if len(chunks) < 2:
                    self._logWarning("Vyroba." + str(n) + ".vstup: Nepodarilo se zpracovat vstup (" + entry + ")")
                    return None

                inputId = "mat-" + chunks[0][5:] if chunks[0][:5] == "prod-" else chunks[0]

                try:
                    res = ResourceModel.manager.get(id=inputId, version=self.entitiesVersion)
                except ResourceModel.DoesNotExist:
                    self._logWarning("Vyroba." + str(n) + ".vstup: Nezname ID vstupu (" + entry + ")")
                    return None

                try:
                    amount = int(chunks[1])
                except Exception:
                    self._logWarning("Vyroba." + str(n) + ".vstup: Spatne formatovany pocet jednotek (" + entry + ")")
                    return None

                input = VyrobaInputModel.objects.create(
                    parent=vyr, resource=res, amount=amount)

                return input

            try:
                prace = int(line[3])
                if prace:
                    addInput("res-prace:" + str(prace))
            except ValueError:
                pass

            if line[5] != "" and line[5] != "-":
                chunks = line[5].split(",")
                for chunk in chunks:
                    addMatInput(chunk.strip())


    def _addEnhancements(self):
        print("Parsing enhancements")
        myRaw = self.raw[self.SHEET_MAP["enh"]]

        for n, line in enumerate(myRaw[2:], start=2):
            line = line[:10]
            if line[1] == "":
                continue

            id = line[1]
            label = line[0]

            try:
                vyroba = VyrobaModel.manager.get(id=line[2], version=self.entitiesVersion)
            except VyrobaModel.DoesNotExist:
                self._logWarning("Vylepšení ." + str(n) + ": Neznámé ID výroby (" + line[2] + ")")
                continue

            try:
                tech = TechModel.manager.get(id=line[3], version=self.entitiesVersion)
            except TechModel.DoesNotExist:
                self._logWarning("Vylepšení ." + str(n) + ": Neznámé ID technologie (" + line[3] + ")")
                continue

            try:
                amount = int(line[5])
            except Exception:
                self._logWarning("Vylepšení ." + str(n) + ".: Bonus musí být číslo (" + line[5] + ")")
                return None

            enhancement = EnhancementModel.manager.create(id=id,
                label=label, tech=tech, vyroba=vyroba, amount=amount, version=self.entitiesVersion)

            def addInput(entry):
                chunks = entry.split(":")

                if len(chunks) < 2:
                    self._logWarning("Vylepšení." + str(n) + ".vstup: Nepodarilo se zpracovat vstup (" + entry + ")")
                    return None

                try:
                    res = ResourceModel.manager.get(id=chunks[0], version=self.entitiesVersion)
                except ResourceModel.DoesNotExist:
                    self._logWarning("Vylepšení." + str(n) + ".vstup: Nezname ID vstupu (" + entry + ")")
                    return None

                try:
                    amount = int(chunks[1])
                except Exception:
                    self._logWarning("Vylepšení." + str(n) + ".vstup: Spatne formatovany pocet jednotek (" + entry + ")")
                    return None

                input = EnhancementInputModel.objects.create(
                    parent=enhancement, resource=res, amount=amount)
                return input

            if line[4] != "" and line[4] != "-":
                chunks = line[4].split(",")
                for chunk in chunks:
                    addInput(chunk.strip())


    def _addAchievements(self):
        print("Parsing achievements")
        myRaw = self.raw[self.SHEET_MAP["ach"]]

        for n, line in enumerate(myRaw[1:], start=1):
            label, id, implementation, icon, orgMessage = line[:5]
            if id:
                AchievementModel.manager.create(id=id,
                    label=label, implementation=implementation,
                    icon=icon, orgMessage=orgMessage, version=self.entitiesVersion)

    def _cloneIslandTechTree(self, island, suffix, root):
        """
        Assuming a tree, clone it and add island properties
        """
        edges = root.unlocks_tech.all()
        root.pk = None
        root.syntheticId = None
        root.id = root.id + suffix
        root.island = island
        root.save()

        for edge in edges:
            newDst = self._cloneIslandTechTree(island, suffix, edge.dst)
            edge.pk = None
            edge.syntheticId = None
            edge.id = edge.id + suffix
            edge.src = root
            edge.dst = newDst
            edge.save()

        return root

    def _addIslands(self):
        print("Parsing islands")
        myRaw = self.raw[self.SHEET_MAP["island"]]
        count = 0

        for n, line in enumerate(myRaw[1:], start=1):
            line = line[:12]
            if line[1] == "":
                continue
            label = line[0]
            id = line[1]
            try:
                direction = {
                        "N": Direction.North,
                        "W": Direction.West,
                        "S": Direction.South,
                        "E": Direction.East
                    }[line[2]]
            except KeyError:
                raise RuntimeError(f"Unknown direction '{line[2]}'")
            distance = int(line[3])

            island = IslandModel.manager.create(id=id,
                label=label, direction=direction, distance=distance,
                root=None, version=self.entitiesVersion)
            rootTech = TechModel.manager.get(id=line[4], version=self.entitiesVersion)
            island.root = self._cloneIslandTechTree(island, f"-{id[4:]}", rootTech)
            island.save()
            count += 1
        print(f"   added {count} islands")


    def parse(self, rawData):
        # clear all entities

        # TODO: This is a hack to overcome UnicodeEncodeError: 'charmap' codec can't encode character '\u011b' in position 515: character maps to <undefined>
        # TODO: Fix and remove
        # Wrapped in try/except block as virtual terminals do not support encoding
        try:
            import sys, codecs
            print("sys.stdout.encoding: " + str(sys.stdout.encoding))
            sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')
        except:
            pass

        self.warnings = []

        # create a fresh entity version
        self.entitiesVersion = EntitiesVersion.objects.create()
        self.raw = rawData

        # parse each entity type
        self._addDice()
        self._addResourceTypes()
        self._addResources()
        self._addTechs()
        self._addEdges()
        self._addVyrobas()
        self._addIslands()
        # self._addEnhancements() # TODO: Update enhancement mechanics
        self._addAchievements()

        warnings = self.warnings
        self.warnings = None
        return warnings