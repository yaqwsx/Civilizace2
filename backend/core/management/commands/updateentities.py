from collections import Counter
from pathlib import Path
import json
import sys
from django.core.management import BaseCommand

from core.gsheets import getSheets
from game.entityParser import EntityParser
from django.conf import settings



class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("setname")

    def handle(self, setname, *args, **kwargs):
        raise NotImplementedError()
