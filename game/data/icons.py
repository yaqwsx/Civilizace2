from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import httplib2
import json

def downloadIcons():
    scope = ['https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name("game/google-sheet-key.json", scope)
    credentials.authorize(httplib2.Http())
    gauth = GoogleAuth()
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name("game/google-sheet-key.json", scope)
    gauth.ServiceAuth()
    # gauth.credentials = credentials

    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': "'1JgPxJFb1tKqhYRf3YsO5ZZwptjk4WdKY' in parents"}).GetList()
    print(len(file_list))
    for file1 in file_list:
        print('title: %s, id: %s' % (file1['title'], file1['id']))