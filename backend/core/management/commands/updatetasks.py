from collections import Counter
from pathlib import Path
import json
import sys
from django.core.management import BaseCommand

from core.gsheets import getSheets
from core.management.commands.pullentities import setFilename
from game.entityParser import EntityParser, loadEntities
from django.conf import settings

from game.models import DbTask, DbTaskPreference

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("setname")

    def handle(self, setname, *args, **kwargs):
        targetFile = settings.TASK_PATH / setFilename(setname)
        with open(targetFile, "r") as f:
            tasks = json.load(f)["úkoly"]
        for tLine in tasks[1:]:
            task, _ = DbTask.objects.update_or_create(id=tLine[0], defaults={
                "name": tLine[1],
                "capacity": tLine[2],
                "orgDescription": tLine[3],
                "teamDescription": tLine[4]})
            DbTaskPreference.objects.filter(task=tLine[0]).delete()
            for tech in tLine[5].split(","):
                tech = tech.strip()
                DbTaskPreference.objects.get_or_create(task=task, techId=tech)
