import json
from django.core.management import BaseCommand
from game.models import DbState
from pathlib import Path


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("outputdir", type=str)

    def handle(self, outputdir, *args, **kwargs):
        outputdir = Path(outputdir)
        outputdir.mkdir(exist_ok=True, parents=True)
        states = DbState.objects.all().order_by("id")

        for s in states:
            intact = s.interaction
            if intact is None:
                continue
            name = f"{intact.created}_{intact.action.actionType}_{intact.phase}"

            dump = {
                "actionType": s.interaction.action.actionType,
                "actionType": s.interaction.action.description,
                "state": {
                    "map": s.mapState.data,
                    "world": s.worldState.data,
                    "teamNum": s.teamStates.all().count(),
                    "teams": {ts.team.id: ts.data for ts in s.teamStates.all()}
                }
            }
            with open(outputdir / f"{name}.json", "w") as f:
                json.dump(dump, f, indent=4)

        for s in states:
            dump = {
                "map": s.mapState.data,
                "world": s.worldState.data,
                "teamNum": s.teamStates.all().count(),
                "teams": {ts.team.id: ts.data for ts in s.teamStates.all()}
            }
            with open(outputdir / f"raw_{s.id}.json", "w") as f:
                json.dump(dump, f, indent=4)
