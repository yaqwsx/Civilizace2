from gspread import authorize as gspread_authorize
from oauth2client.service_account import ServiceAccountCredentials
import json

def download(keyFilePath):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name(keyFilePath, scope)
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

def parseRaw(raw):
    return {}

def validate(data):
    return []

if __name__ == "__main__":
    raw = download("game /google-sheet-key.json")
    data = parseRaw(raw)
    warnings = validate(data)

    print(json.dumps(raw, sort_keys=True, indent=4))
    if len(warnings) == 0:
        None
        # save into data.json
        # popup
    else:
        None
        # popup warnings
