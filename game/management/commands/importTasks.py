from django.core.management import BaseCommand
from game.models.state import State
from game.data.task import TaskModel, TaskMapping
from game.data.tech import TechModel
import json

class Command(BaseCommand):
    help = "Import tasks (merge them based on their name)"

    def add_arguments(self, parser):
        parser.add_argument("input", type=str, help="input JSON file")

    def handle(self, *args, **kwargs):
        with open(kwargs["input"]) as f:
            tasks = json.load(f)

        for t in tasks:
            tm, _ = TaskModel.objects.update_or_create(
                name=t["name"],
                defaults={
                    "teamDescription": t["teamDescription"],
                    "orgDescription": t["orgDescription"],
                    "capacity": t["capacity"]
                }
            )

            for m in t["belongsTo"]:
                if not TechModel.manager.latest().filter(id=m).exists():
                    print(f"Tech {m} does not exist. Ignoring")
                    continue
                TaskMapping.objects.update_or_create(
                    task=tm, techId=m, defaults={"active": True})