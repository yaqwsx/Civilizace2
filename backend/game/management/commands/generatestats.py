from decimal import Decimal
from typing import Any
from django.core.management import BaseCommand

from pathlib import Path
from game.entities import Entities, TeamEntity
from game.state import GameState

import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from game.models import DbAction, DbEntities, DbState, DbSticker, StickerType


pio.templates["civilizace"] = go.layout.Template(
    layout={
        "xaxis": {
            "automargin": True,
            "gridcolor": "black",
            "linecolor": "black",
            "ticks": "",
            "title": {"standoff": 15},
            "zerolinecolor": "black",
            "zerolinewidth": 2,
        },
        "yaxis": {
            "automargin": True,
            "gridcolor": "black",
            "linecolor": "black",
            "ticks": "",
            "title": {"standoff": 15},
            "zerolinecolor": "black",
            "zerolinewidth": 2,
        },
    }
)


pio.templates.default = "none+civilizace"


def isRoundEnd(prevState, state):
    return prevState.world.turn != state.world.turn


def teamStat(team: TeamEntity, states: list[GameState], entities: Entities):
    stat: list[dict[str, Decimal | int]] = []
    prodSum = 0
    weightedSum = 0
    for prevState, state in zip(states, states[1:]):
        if isRoundEnd(prevState, state):
            tState = state.teamStates[team]
            prod = 0
            for resource, amount in tState.resources.items():
                if resource.isTradableProduction:
                    prod += amount
            prodSum += prod
            stat.append(
                {
                    "obyvatele": tState.resources.get(entities.obyvatel, Decimal(0)),
                    "populace": tState.population,
                    "techy": len(tState.techs),
                    "productions": prod,
                    "prodSum": prodSum,
                }
            )
    return stat


def plotTeamGraph(team, overview, outputdir):
    l = overview["stat"]
    turns = [x + 1 for x in range(len(l))]

    mSize = 5

    populace = go.Scatter(
        x=turns,
        y=[x["populace"] for x in l],
        mode="lines+markers",
        name="Populace",
        # marker_symbol=134,
        marker_size=mSize,
        line=dict(color="black", dash="solid", width=0.5),
        legendgroup="1",
    )
    obyvatele = go.Scatter(
        x=turns,
        y=[x["obyvatele"] for x in l],
        mode="lines+markers",
        name="Obyvatele",
        # marker_symbol=135,
        marker_size=mSize,
        line=dict(color="black", dash="solid"),
        legendgroup="1",
    )
    techs = go.Scatter(
        x=turns,
        y=[x["techy"] for x in l],
        mode="lines+markers",
        name="Počet vyzkoumaných technologíí",
        marker_size=mSize,
        line=dict(color="black", dash="solid"),
        legendgroup="2",
    )
    prods = go.Scatter(
        x=turns,
        y=[x["productions"] for x in l],
        mode="lines+markers",
        name="Aktivní produkce",
        # marker_symbol=134,
        marker_size=mSize,
        line=dict(color="black", dash="solid", width=0.5),
        legendgroup="3",
    )
    prodSum = go.Scatter(
        x=turns,
        y=[x["prodSum"] for x in l],
        mode="lines+markers",
        name="Vyprodukované materiály",
        # marker_symbol=135,
        marker_size=mSize,
        line=dict(color="black", dash="solid"),
        legendgroup="3",
    )

    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=(
            "Vývoj populace",
            "Počet vyzkoumaných technologií",
            "Aktivní produkce (vlevo) a \nkumulativní počet vyprodukovaných materiálů (vpravo)",
        ),
        horizontal_spacing=0.1,
        vertical_spacing=0.1,
        specs=[[{}], [{}], [{"secondary_y": True}]],
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        legend_tracegroupgap=180,
    )

    fig.add_trace(populace, row=1, col=1)
    fig.add_trace(obyvatele, row=1, col=1)

    fig.add_trace(techs, row=2, col=1)

    fig.add_trace(prods, row=3, col=1)
    fig.add_trace(prodSum, row=3, col=1, secondary_y=True)

    for row in [1, 2, 3]:
        fig.update_xaxes(
            tickmode="linear",
            tick0=0,
            dtick=1,
            title_text="Kolo",
            range=[turns[0], turns[-1]],
            row=row,
            col=1,
        )

    # odir = Path("stats")
    # odir.mkdir(exist_ok=True, parents=True)
    with open(outputdir / (team.id + ".html"), "w") as f:
        f.write(
            f"""
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
                    height: 22cm;
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
                        <td>Celkem útoků</td>
                        <td>{overview["attacks"]}</td>
                    </tr>
                    <tr>
                        <td>Postaveno budov</td>
                        <td>{overview.get("buildings", 0)}</td>
                    </tr>
                    <tr>
                        <td>Technologií vyzkoumáno jako první</td>
                        <td>{max(0, overview.get("techsFirst", 0) - 7)}</td>
                    </tr>
                </table>
                <br>

                <div class="graph">
        """
        )
        f.write(fig.to_html(full_html=False, include_plotlyjs=True))
        f.write(
            f"""
                </div>
            </div>
            </body>
        """
        )


def plotSummary(overview, outdir):
    pio.templates.default = "plotly"
    fig = make_subplots(
        rows=6,
        cols=1,
        subplot_titles=(
            "Vývoj populace",
            "Procento nespecializovaných",
            "Počet vyzkoumaných technologií",
            "Aktivní produkce",
            "Kumulativní počet vyprodukovaných materiálů",
            "Kumulativní počet vyprodukovaných materiálů vážený úrovní materiálu",
        ),
        horizontal_spacing=0.025,
        vertical_spacing=0.025,
    )

    for t, o in overview.items():
        if t.id == "tym-protinozci":
            continue
        l = o["stat"]
        turns = [x + 1 for x in range(len(l))]

        populace = go.Scatter(
            x=turns,
            y=[x["populace"] for x in l],
            mode="lines+markers",
            name=f"Populace {t.name}",
            line=dict(color=t.hexColor, dash="solid"),
            legendgroup="1",
        )
        obyvatele = go.Scatter(
            x=turns,
            y=[int(x["obyvatele"] / x["populace"] * 100) for x in l],
            mode="lines+markers",
            name=f"Procento nespecializovaných {t.name}",
            line=dict(color=t.hexColor, dash="solid"),
            legendgroup="2",
        )
        techs = go.Scatter(
            x=turns,
            y=[x["techy"] for x in l],
            mode="lines+markers",
            name=f"Počet vyzkoumaných technologíí {t.name}",
            line=dict(color=t.hexColor, dash="solid"),
            legendgroup="3",
        )
        prods = go.Scatter(
            x=turns,
            y=[x["productions"] for x in l],
            mode="lines+markers",
            name=f"Aktivní produkce {t.name}",
            line=dict(color=t.hexColor, dash="solid"),
            legendgroup="4",
        )
        prodSum = go.Scatter(
            x=turns,
            y=[x["prodSum"] for x in l],
            mode="lines+markers",
            name=f"Vyprodukované materiály {t.name}",
            line=dict(color=t.hexColor, dash="solid"),
            legendgroup="5",
        )

        wprodSum = go.Scatter(
            x=turns,
            y=[x["weightedSum"] for x in l],
            mode="lines+markers",
            name=f"Vyprodukovaný potenciál materiálů {t.name}",
            line=dict(color=t.hexColor, dash="solid"),
            legendgroup="6",
        )

        fig.add_trace(populace, row=1, col=1)
        fig.add_trace(obyvatele, row=2, col=1)

        fig.add_trace(techs, row=3, col=1)

        fig.add_trace(prods, row=4, col=1)
        fig.add_trace(prodSum, row=5, col=1)

        fig.add_trace(wprodSum, row=6, col=1)

    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        legend_tracegroupgap=180,
        height=5000,
    )

    for row in range(6):
        fig.update_xaxes(
            tickmode="linear",
            tick0=0,
            dtick=1,
            title_text="Kolo",
            range=[turns[0], turns[-1]],
            row=row + 1,
            col=1,
        )

    fig.write_html(outdir / "summary.html")


class Command(BaseCommand):
    help = "Dump base per-team stat into several CSV files"

    def add_arguments(self, parser):
        parser.add_argument("output", type=str)

    def handle(self, output, *args, **kwargs):
        outputDir = Path(output)
        outputDir.mkdir(exist_ok=True, parents=True)

        states = [s.toIr() for s in DbState.objects.all().order_by("id")]
        revision, entities = DbEntities.objects.get_revision()

        overview = {t: {"attacks": 0} for t in entities.teams.values()}

        for team in entities.teams.values():
            print(f"Statistiky pro tým {team.name}")
            fname = outputDir / f"{team.name}.csv"
            print(fname)
            with open(fname, "w") as f:
                stat = teamStat(team, states, entities)
                f.write("populace, obvyatele, techy, produkce, materialy\n")
                for l in stat:
                    f.write(
                        f'{l["populace"]}, {l["obyvatele"]}, {l["techy"]}, {l["productions"]}, {l["prodSum"]}\n'
                    )
                overview[team]["stat"] = stat

        for action in DbAction.objects.all():
            if "team" not in action.args:
                continue
            tId = action.args["team"]
            t = entities[tId]
            overview[t]["interactions"] = overview[t].get("interactions", 0) + 1
            if action.actionType == "ArmyDeployAction":
                overview[t]["attacks"] = overview[t].get("attacks", 0) + 1
            if action.actionType == "BuildAction":
                overview[t]["buildings"] = overview[t].get("buildings", 0) + 1

        techStickers = list(DbSticker.objects.filter(type=StickerType.techFirst))
        for t, o in overview.items():
            ts = [x.id for x in techStickers if x.team.id == t.id]
            o["techsFirst"] = len(ts)

        for t, o in overview.items():
            o["stat"] = o["stat"][:3] + o["stat"][7:9] + o["stat"][17:]

        plotSummary(overview, outputDir)

        for t, overview in overview.items():
            if "stat" not in overview:
                continue
            plotTeamGraph(t, overview, outputDir)

        print("Počet interakcí systémem: ", DbAction.objects.all().count())
