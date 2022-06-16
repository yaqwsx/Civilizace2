import os
from django.core.management import BaseCommand
from pathlib import Path
import shutil
import subprocess

from game.models import DbEntities

TEMPLATE = Path("../graphics/plague").resolve()

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("outputdir", type=str)

    def handle(self, outputdir, *args, **kwargs):
        outputdir = Path(outputdir)
        outputdir.mkdir(exist_ok=True, parents=True)
        _, entities = DbEntities.objects.get_revision()
        plague = entities.plague
        teams = list(entities.teams.values())
        CHUNK_SIZE = 2

        teamChunks = [teams[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE] for i in range((len(teams) + CHUNK_SIZE - 1) // CHUNK_SIZE )]
        for pList in plague.sheets:
            for chunk in teamChunks:
                self.generate(pList, chunk[0], chunk[1], outputdir)

    def generate(self, pList, lTeam, rTeam, outputdir):
        with open(TEMPLATE / "index.html") as f:
            content = f.read()

        content = content \
            .replace("SHEET_NAME", pList.name) \
            .replace("LEFT_TEAM", lTeam.name) \
            .replace("RIGHT_TEAM", rTeam.name)
        for i in range(2):
            content = content \
                .replace(f"LEFT_WORD{i+1}", f"{pList.words[i].word} pro {lTeam.name}") \
                .replace(f"RIGHT_WORD{i+1}", f"{pList.words[i].word} pro {rTeam.name}") \
                .replace(f"LEFT_QR{i+1}", f"mor-{pList.words[i].slug} {lTeam.id}") \
                .replace(f"RIGHT_QR{i+1}", f"mor-{pList.words[i].slug} {rTeam.id}")
        for i in range(3):
            content = content \
                .replace(f"LEFT_SENTENCE{i+1}", pList.sentences[i]) \
                .replace(f"RIGHT_SENTENCE{i+1}", pList.sentences[i])
        content = content \
            .replace("MAP_LEFT", pList.map) \
            .replace("MAP_RIGHT", pList.map)

        with open(TEMPLATE / "subs.html", "w") as f:
            f.write(content)

        outfile = outputdir / f"{pList.name}_{lTeam.name}_{rTeam.name}.pdf"

        subprocess.run(["google-chrome", "--headless", "--disable-gpu",
                        f"--print-to-pdf=tmp.pdf", str(TEMPLATE / "subs.html")],
                        check=True, cwd=str(TEMPLATE))

        subprocess.run(["pdftk", "tmp.pdf", "cat", "1", "output", str(outfile)],
                        check=True, cwd=str(TEMPLATE))

        os.unlink(TEMPLATE / "subs.html")
        os.unlink(TEMPLATE / "tmp.pdf")












