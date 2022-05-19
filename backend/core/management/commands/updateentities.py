from collections import Counter
from pathlib import Path
import json
import sys
from django.core.management import BaseCommand

from core.gsheets import getSheets
from core.management.commands.pullentities import setFilename
from game.entityParser import EntityParser, loadEntities
from django.conf import settings

from game.models import DbEntities



class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("setname")

    def handle(self, setname, *args, **kwargs):
        targetFile = settings.ENTITY_PATH / setFilename(setname)
        ent = loadEntities(targetFile)
        with open(targetFile) as f:
            data = json.load(f)
        DbEntities.objects.create(data=data)
