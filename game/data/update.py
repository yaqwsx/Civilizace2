from gspread import authorize as gspread_authorize
from oauth2client.service_account import ServiceAccountCredentials
import json

from .entity import EntityModel, GameDataModel, DieModel
from .tech import TechModel
from .parser import Parser

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

        parser = Parser()
        warnings.extend(parser.parse(raw))

        return warnings

    def DEBUG(self):
        print("Running DEBUG")
        raw = self._download()
        parser = Parser()
        parser.parse()


if __name__ == "__main__":
    updater = Update()
    warnings = updater.download()
    if len(warnings):
        print(warnings[0])
        for line in warnings[1:]:
            print("  " + line)