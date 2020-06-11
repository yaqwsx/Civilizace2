from service.plotting.dot import indent, escapeId, fromMm, digraphHeader, endGraph
import textwrap

from game.data.vyroba import VyrobaModel

import os
import sys
import subprocess
from pathlib import Path

class VyrobaBuilder:
    def __init__(self, buildDirectory, iconDirectory):
        self.iconDirectory = os.path.abspath(iconDirectory)
        self.buildDirectory = os.path.abspath(buildDirectory)
        Path(self.buildDirectory).mkdir(parents=True, exist_ok=True)

    def generateVyrobaLabel(self, vyroba):
        try:
            texSrc = os.path.join(self.buildDirectory, vyroba.id + ".tex")
            with open(texSrc, "w") as f:
                self.vyrobaCard(f, vyroba)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                "--output-directory", self.buildDirectory, texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            cmd = " ".join(e.cmd)
            sys.stderr.write(f"Command '{cmd}' failed:\n")
            sys.stderr.write(e.stdout.decode("utf8"))
            sys.stderr.write(e.stderr.decode("utf8"))
            raise

    def generateTechLabels(self):
        for tech in TechModel.objects.all():
            self.generateTechLabel(tech)

    def labelFor(self, tech):
        """Get absolute file path for given tech label"""
        return os.path.join(self.buildDirectory, tech.id + ".pdf")

    def emptyLabelFor(self, tech):
        """Get absolute file path for given tech label"""
        return os.path.join(self.buildDirectory, "empty-" + tech.id + ".pdf")

    def fullGraphFile(self):
        return os.path.join(self.buildDirectory, "fullGraph.pdf")

    def emptyFullGraphFile(self):
        return os.path.join(self.buildDirectory, "emptyFullGraph.pdf")

    def generateFullGraph(self):
        return self.generateFullGraphImpl(self.fullGraphFile(), lambda x: self.labelFor(x))

    def generateEmptyFullGraph(self):
        return self.generateFullGraphImpl(self.emptyFullGraphFile(), lambda x: self.emptyLabelFor(x))

    def generateFullGraphImpl(self, fullGraphFile, techLabler):
        try:
            dotFile = os.path.join(self.buildDirectory, fullGraphFile.replace(".pdf", ".dot"))
            texFile = os.path.join(self.buildDirectory, fullGraphFile.replace(".pdf", ".tex"))
            techs = TechModel.objects.all()
            with open(dotFile, "w") as f:
                digraphHeader(f)
                for t in techs:
                    declareTech(f, t, techLabler(t))
                for t in techs:
                    declareTechEdges(f, t)
                endGraph(f)
            buildCmd = ["dot2tex", "--autosize", "--usepdflatex", "-ftikz",
                "--template", "service/plotting/graphTemplate.tex",
                "-o", texFile, dotFile]
            subprocess.run(buildCmd, capture_output=True, check=True)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                    "--output-directory", self.buildDirectory, texFile]
            subprocess.run(buildCmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            cmd = " ".join(e.cmd)
            sys.stderr.write(f"Command '{cmd}' failed:\n")
            sys.stderr.write(e.stdout.decode("utf8"))
            sys.stderr.write(e.stderr.decode("utf8"))
            raise

    def formatResource(self, resource):
        return resource.label
        # if resource.icon:
        #     return r"\icon{" + os.path.join(self.iconDirectory, resource.icon) + "} " + resource.label
        # return resource.label

    def vyrobaHeader(self):
        return r"""
        \documentclass{standalone}
        \usepackage[czech]{babel}
        \usepackage[utf8]{inputenc}
        \usepackage[T1]{fontenc}
        \usepackage{tabularx}
        \usepackage{amsmath}
        \usepackage{txfonts}
        \usepackage{mdframed}
        \usepackage{qrcode}
        \usepackage{pbox}
        \usepackage{enumitem}
        \usepackage{graphicx}

        \renewcommand*{\arraystretch}{0}

        \newcommand\VyrobaCard[4]{%
            \setlength\fboxsep{0.3cm}\setlength\fboxrule{0.0pt}% delete
            \fbox{% delete
                    \begin{minipage}[c][5cm][t]{9cm}%
                        \begin{tabularx}{\textwidth}{lXr}
                            \raisebox{-\height+\fontcharht\font`X}{#1} \vspace{0.2cm} & #2 & \raisebox{-\height+\fontcharht\font`X}{{#3}}
                        \end{tabularx}
                        {#4}
                    \end{minipage}%
            }% delete
        }
        """

    def vyrobaCard(self, file, vyroba):
        """
        Generate LaTeX file with tech node
        """

        description = r"{\Large\textbf{" + tech.label + r"}}" + "\n\n"
        description += tech.flavour + "\n\n"
        vyrobas = tech.unlock_vyrobas.all()
        if vyrobas and True:
            if len(vyrobas) == 1:
                description += r"\textbf{Odemyká výrobu:}"
            else:
                description += r"\textbf{Odemyká výroby:}"
            description += r"\begin{itemize}[noitemsep,nolistsep,leftmargin=*,after=\vspace*{-\dimexpr\baselineskip - 3pt}]" + "\n"
            for vyroba in vyrobas:
                description += r"\item " + vyroba.label + "\n"
            description += r"\end{itemize}" + "\n\n"
        enhancers = tech.unlock_enhancers.all()
        if enhancers:
            description += r"\textbf{Odemyká vylepšení:}"
            description += r"\begin{itemize}[noitemsep,nolistsep,leftmargin=*,after=\vspace*{-\dimexpr\baselineskip - 3pt}]" + "\n"
            for enhancer in enhancers:
                description += r"\item " + enhancer.label + "\n"
            description += r"\end{itemize}" + "\n\n"

        unlocksTech = tech.unlocks_tech.all()
        unlocks = ""
        if unlocksTech:
            unlocks += r"\textbf{Navazující směry bádání:}\begin{itemize}[noitemsep,nolistsep,leftmargin=*]" + "\n"
            for ut in unlocksTech:
                resources = ["{}$\\times$ {}".format(ut.dots, ut.die.label)]
                resources += ["{}$\\times$ {}".format(r.amount, self.formatResource(r.resource)) for r in ut.resources.all()]
                unlocks += r"\item " + ut.label + " (" + ", ".join(resources) + ")\n"
            unlocks += r"\end{itemize}" + "\n\n"

        if tech.image and tech.image != "-":
            icon = r"\includegraphics[width=2.5cm, height=2.5cm, keepaspectratio]{" + os.path.join(self.iconDirectory, tech.image) + r"}"
        else:
            icon = ""

        file.write(self.cardHeader(self.teamColor))
        file.write(r"""
        \begin{document}
            \VyrobaCard
                {\qrcode[version=1,height=2cm]{""" + tech.id + r"""}}
                {""" + description + r"""}
                {""" + icon + r"""}
                {""" + unlocks + r"""
                    \vspace*{\fill}
                    \begin{center} (""" + tech.nodeTag + r""")\end{center}
                }

        \end{document})
        """)