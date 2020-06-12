from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pathlib import Path
import os
import json
import subprocess
import sys

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

def postProcessIcons(directory, report=print):
    try:
        report("SVG to PDF")
        conversionList = ""
        for file in os.listdir(directory):
            if file.endswith(".svg"):
                file = os.path.abspath(os.path.join(directory, file))
                output = file.replace(".svg", ".pdf")
                conversionList += f"{file} --export-pdf={output}\n"
        report(conversionList)
        converstionCmd = ["inkscape", "--shell"]
        subprocess.run(converstionCmd, capture_output=True, check=True, input=conversionList.encode("utf8"))
    except subprocess.CalledProcessError as e:
        cmd = " ".join(e.cmd)
        sys.stderr.write(f"Command '{cmd}' failed:\n")
        sys.stderr.write(e.stdout.decode("utf8"))
        sys.stderr.write(e.stderr.decode("utf8"))
        raise
