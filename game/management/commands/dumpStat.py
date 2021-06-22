from django.core.management import BaseCommand

from pathlib import Path
import os
from game.models.state import State
from game.models.actionBase import ActionPhase, ActionEvent, Action
from game.models.actionTypeList import ActionType
from game.models.users import Team

import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots


pio.templates["civilizace"] = go.layout.Template(
    layout={
        "xaxis": {
            'automargin': True,
            'gridcolor': 'black',
            'linecolor': 'black',
            'ticks': '',
            'title': {'standoff': 15},
            'zerolinecolor': 'black',
            'zerolinewidth': 2
        },
        "yaxis": {
            'automargin': True,
            'gridcolor': 'black',
            'linecolor': 'black',
            'ticks': '',
            'title': {'standoff': 15},
            'zerolinecolor': 'black',
            'zerolinewidth': 2
        },
    })


pio.templates.default = "none+civilizace"

def isRoundEnd(state, team):
    return state.action.action.team == team and state.action.action.move == ActionType.nextTurn

def teamStat(team, states):
    stat = []
    prodSum = 0
    for state in states:
        print(f"Walking state {state.id}")
        if isRoundEnd(state, team):
            if state.context is None:
                state.setContext(state.action.action.context)
            tState = state.teamState(team)
            prod = 0
            for resource, amount in tState.resources.asMap().items():
                if resource.isProduction:
                    prod += amount
            for resource, amount  in tState.foodSupply.asMap().items():
                if resource.isProduction:
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

def plotTeamGraph(team, overview):
    l = overview["stat"]
    turns = [x + 1 for x in range(len(l))]

    mSize = 5

    populace = go.Scatter(
        x=turns,
        y=[x["populace"] for x in l],
        mode='lines+markers',
        name='Populace',
        # marker_symbol=134,
        marker_size=mSize,
        line=dict(color='black', dash='solid', width=0.5),
        legendgroup="1")
    obyvatele = go.Scatter(
        x=turns,
        y=[x["obyvatele"] for x in l],
        mode='lines+markers',
        name='Obyvatele',
        # marker_symbol=135,
        marker_size=mSize,
        line=dict(color='black', dash='solid'),
        legendgroup="1")
    techs = go.Scatter(
        x=turns,
        y=[x["techy"] for x in l],
        mode="lines+markers",
        name="Počet vyzkoumaných technologíí",
        marker_size=mSize,
        line=dict(color='black', dash='solid'),
        legendgroup="2"
    )
    prods = go.Scatter(
        x=turns,
        y=[x["productions"] for x in l],
        mode="lines+markers",
        name="Aktivní produkce",
        # marker_symbol=134,
        marker_size=mSize,
        line=dict(color='black', dash='solid', width=0.5),
        legendgroup="3"
    )
    prodSum = go.Scatter(
        x=turns,
        y=[x["prodSum"] for x in l],
        mode="lines+markers",
        name="Vyprodukované materiály",
        # marker_symbol=135,
        marker_size=mSize,
        line=dict(color='black', dash='solid'),
        legendgroup="3"
    )

    fig = make_subplots(rows=3, cols=1,
        subplot_titles=(
            "Vývoj populace",
            "Počet vyzkoumaných technologií",
            "Aktivní produkce (vlevo) a \nkumulativní počet vyprodukovaných materiálů (vpravo)"),
        horizontal_spacing=0.1,
        vertical_spacing=0.1,
        specs=[[{}], [{}], [{"secondary_y": True}]])

    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        legend_tracegroupgap = 180,
    )

    fig.add_trace(populace, row=1, col=1)
    fig.add_trace(obyvatele, row=1, col=1)

    fig.add_trace(techs, row=2, col=1)

    fig.add_trace(prods, row=3, col=1)
    fig.add_trace(prodSum, row=3, col=1, secondary_y=True)

    for row in [1, 2, 3]:
        fig.update_xaxes(
            tickmode='linear', tick0=0, dtick=1,
            title_text="Kolo",
            range=[turns[0], turns[-1]],
            row=row, col=1)

    odir = Path("stats")
    odir.mkdir(exist_ok=True, parents=True)
    with open(odir / (team.id + ".html"), "w") as f:
        f.write(f"""
        <html>
            <head>
            <head>

            <style>
                body {{
                    font-family: "Artegra Sans Alt Medium", sans-serif;
                }}
                .page {{
                    width: 21cm;
                    height: 29cm;
                    margin-left: auto;
                    margin-right: auto;
                    overflow: hidden;
                }}

                .graph {{
                    height: 23cm;
                }}

                table {{
                    width: 100%;
                }}
            </style>

            <body>
            <div class="page">
                <h1>{team.name} — statistiky Civilizace 2021</h1>

                <table>
                    <tr>
                        <td>Celkový počet interakcí se systémem</td>
                        <td>{overview["interactions"]}</td>
                    </tr>
                    <tr>
                        <td>Celková populace</td>
                        <td>{l[-1]["populace"]}</td>
                    </tr>
                    <tr>
                        <td>Celkový počet technologíí</td>
                        <td>{l[-1]["techy"]}</td>
                    </tr>
                    <tr>
                        <td>Celkem vyprodukováno</td>
                        <td>{l[-1]["prodSum"]}</td>
                    </tr>
                    <tr>
                        <td>Celkem útoků na ostrovy</td>
                        <td>{overview["attacks"]}</td>
                    </tr>
                </table>
                <br>

                <div class="graph">
        """)
        f.write(fig.to_html(full_html=False, include_plotlyjs=True))
        f.write(f"""
                </div>
            </div>
            </body>
        """)

class Command(BaseCommand):
    help = "Dump base per-team stat into several CSV files"

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, required=False)

    def handle(self, *args, **kwargs):
        # outputDir = kwargs.get("output", "stats")
        outputDir = "stats"
        states = list(State.objects.all())

        overview = {t: {"attacks": 0} for t in Team.objects.all()}

        for team in Team.objects.all():
            print(f"Statistiky pro tým {team.name}")
            fname = os.path.join(outputDir, team.name + ".csv")
            print(fname)
            with open(fname, "w") as f:
                stat = teamStat(team, states)
                f.write("populace, obvyatele, techy, produkce, materialy\n")
                for l in stat:
                    f.write(f'{l["populace"]}, {l["obyvatele"]}, {l["techy"]}, {l["productions"]}, {l["prodSum"]}\n')
                overview[team]["stat"] = stat

        for action in Action.objects.all():
            if action.team is None:
                continue
            overview[action.team]["interactions"] = overview[action.team].get("interactions", 0) + 1
            if action.move == ActionType.attackIsland:
                overview[action.team]["attacks"] = overview[action.team].get("attacks", 0) + 1

        for t, overview in overview.items():
            if "stat" not in overview:
                continue
            if t.id == "tym-protinozci":
                continue
            plotTeamGraph(t, overview)

        print(len(Action.objects.all()))
