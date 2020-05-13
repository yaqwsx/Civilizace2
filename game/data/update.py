from gspread import authorize as gspread_authorize
from oauth2client.service_account import ServiceAccountCredentials
import json

from django.db import transaction

from .entity import EntityModel, GameDataModel, DieModel
from .tech import TechModel
from .parser import Parser

class UpdateError(RuntimeError):
    def __init__(self, message, warnings):
        super().__init__(message)
        self.warnings = warnings

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

    def fileAsSource(self, filename="game/data/entities.json"):
        with open(filename, "r") as jsonFile:
            self.raw = json.load(jsonFile)

    def saveToFile(self, filename="game/data/entities.json"):
        with open(filename, "w") as jsonFile:
            json.dump(self.raw, jsonFile, indent=4)

    def googleAsSource(self):
        self.raw = self._download()

    @transaction.atomic
    def update(self):
        if self.raw is None:
            raise RuntimeError("No source was specified for updater")
        warnings = []

        parser = Parser()
        warnings.extend(parser.parse(self.raw))

        if len(warnings) > 0:
            raise UpdateError("Update error", warnings)

    def DEBUG(self):
        print("Running DEBUG")
        raw = self._download()
        parser = Parser()
        parser.parse()


if __name__ == "__main__":
    updater = Update()
    updater.googleAsSource()
    try:
        updater.update()
        print("Update done")
        updater.saveToFile()
        print("Saved to file")
    except UpdateError as e:
        print(e.warnings[0])
        for line in e.warnings[1:]:
            print("  " + line)
