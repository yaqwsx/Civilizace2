import gspread
import os


def getService():
    """
    Return a service, reading the auth information from a file specified
    by env variable CIVILIZACE_GAUTH_FILE or file gauth.json
    """
    credentialPath = os.environ.get("CIVILIZACE_GAUTH_FILE", "gauth.json")
    if not os.path.exists(credentialPath):
        raise RuntimeError(
            f"Nebyl nalezen soubor s autentizačními informacemi"
            + f" pro Google Sheets: '{os.path.realpath(credentialPath)}'."
        )
    return gspread.service_account(filename=credentialPath)


def getSheets(id: str):
    return getService().open_by_key(id)
