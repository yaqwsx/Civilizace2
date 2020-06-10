from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pathlib import Path
import os
import json

def downloadIcons(directory, report=print):
    Path(directory).mkdir(parents=True, exist_ok=True)

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)

    fileList = drive.ListFile({'q': "'1JgPxJFb1tKqhYRf3YsO5ZZwptjk4WdKY' in parents and trashed=false"}).GetList()
    for file in fileList:
        report(f"Downloading {file['title']}")
        fPath = os.path.join(directory, file["title"])
        file.GetContentFile(fPath)