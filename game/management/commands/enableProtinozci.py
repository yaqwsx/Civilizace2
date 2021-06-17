from django.core.management import BaseCommand

from pathlib import Path
import os
from game.models.state import State
from game.models.actionBase import ActionPhase, ActionEvent, Action
from game.models.actionTypeList import ActionType
from game.models.users import Team


class Command(BaseCommand):
    help = "Enable protinozci"


    def handle(self, *args, **kwargs):
        t = Team.objects.get(id="tym-protinozci")
        t.visible = True
        t.save()