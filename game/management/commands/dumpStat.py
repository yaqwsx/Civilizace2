from django.core.management import BaseCommand

from pathlib import Path
import os
from game.models.state import State
from game.models.actionBase import ActionPhase, ActionEvent, Action
from game.models.actionTypeList import ActionType
from game.models.users import Team

def isRoundEnd(state):
    return state.action.action.move == ActionType.nextTurn

def teamStat(team, states):
    stat = []
    prodSum = 0
    for state in states:
        print(f"Walking state {state.id}")
        if isRoundEnd(state):
            if state.context is None:
                state.setContext(state.action.action.context)
            tState = state.teamState(team)
            prod = 0
            for resource, amount in tState.resources.asMap().items():
                if resource.isProduction:
                    prod += amount
            for resource, amount  in tState.foodSupply.asMap().items():
                prod += amount
            prodSum += prod
            stat.append({
                "obyvatele": tState.resources.get("res-obyvatel"),
                "populace": tState.resources.get("res-populace"),
                "techy": len(tState.techs.getOwnedTechs()),
                "productions": prod,
                "prodSum": prodSum
            })
    return stat

class Command(BaseCommand):
    help = "Dump base per-team stat into several CSV files"

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, required=False)

    def handle(self, *args, **kwargs):
        # outputDir = kwargs.get("output", "stats")
        outputDir = "stats"
        states = list(State.objects.all())

        for team in Team.objects.all():
            print(f"Statistiky pro tým {team.name}")
            fname = os.path.join(outputDir, team.name + ".csv")
            print(fname)
            with open(fname, "w") as f:
                stat = teamStat(team, states)
                f.write("populace, obvyatele, techy, produkce, materialy\n")
                for l in stat:
                    f.write(f'{l["populace"]}, {l["obyvatele"]}, {l["techy"]}, {l["productions"]}, {l["prodSum"]}\n')

        interactions = {}
        for action in Action.objects.all():
            if action.team is None:
                continue
            interactions[action.team.name] = interactions.get(action.team.name, 0) + 1
        print(interactions)
