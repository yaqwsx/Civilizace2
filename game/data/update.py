from gspread import authorize as gspread_authorize
from oauth2client.service_account import ServiceAccountCredentials
import json

class Update():

    def _download(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name("game/google-sheet-key.json", scope)
        gc = gspread_authorize(credentials)

        wks = gc.open_by_url("https://docs.google.com/spreadsheets/d/1EcBVbrpLp3_ypbYTMWM9Cw1EGQq8ST44zQcV9KA-B_A/edit?usp=sharing")

        sheetMap = {
            "tech": 1,
            "mat": 2,
            "proc": 3,

        }

        result = {}
        for key, value in sheetMap.items():
            entitiesSheet = wks.get_worksheet(value)
            sheet = entitiesSheet.get_all_values()
            result[key] = sheet

        return result

    def _parseRaw(self, raw):
        return {}

    def _validate(self, parsed):
        warnings = []
        return warnings

    def _update(self, parsed):
        return True

    def download(self):
        raw = self._download()
        parsed = self._parseRaw(raw)
        warnings = self._validate(parsed)

        if not len(warnings):
            with open("game/data/entities.json", "w") as jsonFile:
                json.dump(raw, jsonFile, indent=4)
                print("Entities updated")
        else:
            warnings.insert(0, "Data obsahují chybu; entity nebyly aktualizovány")
        return warnings

    def update(self):
        with open("game/data/entities.json", "r") as jsonFile:
            raw = json.load(jsonFile)

        return False

if __name__ == "__main__":
    updater = Update()
    warnings = updater.download()
    if len(warnings):
        print(warnings[0])
        for line in warnings[1:]:
            print("  " + line)