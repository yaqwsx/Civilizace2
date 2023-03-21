from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json
from django.core.management import BaseCommand

from core.gsheets import getSheets
from core.management.commands.pullentities import setFilename
from game.entityParser import EntityParser
from django.conf import settings

from game.models import DbEntities



class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("setname")

    def handle(self, setname: str, *args, **kwargs) -> None:
        targetFile = settings.ENTITY_PATH / setFilename(setname)
        ent = EntityParser.load(targetFile)
        with open(targetFile) as f:
            data = json.load(f)
        DbEntities.objects.create(data=data)
