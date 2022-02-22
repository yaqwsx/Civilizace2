from django.core.management import BaseCommand
from game.models.state import State
from game.data.task import TaskModel, TaskMapping
import json

class Command(BaseCommand):
    help = "Dump tasks into JSON file"

    def add_arguments(self, parser):
        parser.add_argument("output", type=str, help="output file name")

    def handle(self, *args, **kwargs):
        outputFilename = kwargs["output"]

        tasks = []
        for t in TaskModel.objects.all():
            tasks.append({
                "name": t.name,
                "teamDescription": t.teamDescription,
                "orgDescription": t.orgDescription,
                "capacity": t.capacity,
                "belongsTo": [m.tech.id for m in TaskMapping.objects.filter(active=True, task=t)]
            })

        with open(outputFilename, "w") as f:
            f.write(json.dumps(tasks, indent=4))
