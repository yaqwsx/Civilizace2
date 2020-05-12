from gspread import authorize as gspread_authorize
from oauth2client.service_account import ServiceAccountCredentials
import json

from .entities import EntityModel, GameDataModel, DieModel
from .tech import TechModel

class Update():

    def _download(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name("game/google-sheet-key.json", scope)
        gc = gspread_authorize(credentials)

        wks = gc.open_by_url("https://docs.google.com/spreadsheets/d/1EcBVbrpLp3_ypbYTMWM9Cw1EGQq8ST44zQcV9KA-B_A/edit?usp=sharing")

        result = []
        for sheet in wks.worksheets():
            data = sheet.get_all_values()
            result.append(data)

        return result

    def _createEntities(self, raw, warnings):
        entities = GameDataModel.objects.create()

        return {}

    def _validateEntities(self, entities):
        warnings = []
        return warnings

    def _update(self, parsed):
        return True

    def _cleanup(self):
        entitiesSets = GameDataModel.objects.all()
        for entity in entitiesSets:
            entity.delete()
        dice = DieModel.objects.all()
        for die in dice:
            die.delete()

    def download(self):
        raw = self._download()

        warnings = self.update(raw=raw)

        if not len(warnings):
            with open("game/data/entities.json", "w") as jsonFile:
                json.dump(raw, jsonFile, indent=4)
                print("Entities updated")
        else:
            warnings.insert(0, "Data obsahují chybu; entity nebyly aktualizovány")
            self.update() # restore previous entity tables
        return warnings

    def update(self, raw=None):
        if not raw:
            with open("game/data/entities.json", "r") as jsonFile:
                raw = json.load(jsonFile)

        warnings = []

        return warnings

    def DEBUG(self):
        print("Running DEBUG")
        self._cleanup()
        data = GameDataModel.objects.create()
        techA = TechModel.objects.create(id="tech-A", label="Tech A", data=data)
        techA.save()
        data2 = GameDataModel.objects.create()
        techB = TechModel.objects.create(id="tech-B", label="Tech B", data=data2)
        techB.save()

        datas = GameDataModel.objects.all()
        for data in datas:
            print("Data: " + str(data))
            for tech in data.techmodel_set.all():
                print("  Tech: " + str(tech))
        print("DEBUG ended")



if __name__ == "__main__":
    updater = Update()
    warnings = updater.download()
    if len(warnings):
        print(warnings[0])
        for line in warnings[1:]:
            print("  " + line)