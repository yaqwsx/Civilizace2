from service.plotting.dot import indent, escapeId, fromMm, digraphHeader, endGraph
import textwrap

from game.data.tech import TechModel
from game.data.vyroba import VyrobaModel

import os
import sys
import subprocess
from pathlib import Path


def declareTech(file, tech, nodeLabelImg, indentLevel=1):
    styles = []
    styles.append('shape=box')
    styles.append('margin="0"')
    # styles.append(f'label=""')
    styles.append(r'texlbl="\includegraphics{' + nodeLabelImg + r'}"')
    file.write(indent(indentLevel) + "{} [{}];\n".format(
        escapeId(tech.id),
        ", ".join(styles)))

def declareTechEdges(file, tech, indentLevel=1):
    styles = []
    for i, edge in enumerate(tech.unlocks_tech.all()):
        file.write(indent(indentLevel) + "{} -> {}[{}];\n".format(
            escapeId(edge.src.id),
            escapeId(edge.dst.id),
            ", ".join(styles)
        ))

class TechBuilder:
    def __init__(self, buildDirectory, iconDirectory, teamColor):
        self.iconDirectory = os.path.abspath(iconDirectory)
        self.buildDirectory = os.path.abspath(buildDirectory)
        self.teamColor = teamColor
        Path(self.buildDirectory).mkdir(parents=True, exist_ok=True)

    def generateTechLabel(self, tech):
        try:
            texSrc = os.path.join(self.buildDirectory, tech.id + ".tex")
            with open(texSrc, "w") as f:
                self.techNode(f, tech)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                "--output-directory", self.buildDirectory, texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)

            texSrc = os.path.join(self.buildDirectory, "empty-" + tech.id + ".tex")
            with open(texSrc, "w") as f:
                self.emptyTechNode(f, tech)
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
            if tech.id.startswith("div-"):
                continue
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
                f.write('graph [center=true, margin=0.2, nodesep=0.1, ranksep=0.3, pad=0.3];\n')
                f.write('ratio="0.5";\n')
                f.write("rankdir=LR;\n")
                f.write("{\n")
                for t in techs:
                    if t.id.startswith("div-"):
                        continue
                    declareTech(f, t, techLabler(t))
                for t in techs:
                    declareTechEdges(f, t)
                f.write("}\n")
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
        if resource.isProduction:
            return r"\uline{" + resource.label.replace("Produkce: ", "") + "}"
        return resource.label
        # if resource.icon:
        #     return r"\icon{" + os.path.join(self.iconDirectory, resource.icon) + "} " + resource.label
        # return resource.label

    def cardHeader(self,teamColor):
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
        \usepackage{ulem}
        \renewcommand{\ULdepth}{1pt}

        \definecolor{teamColor}{RGB}{""" + ", ".join([str(x) for x in teamColor]) + r"""}

        \renewcommand*{\arraystretch}{0}

        \newcommand\TechCard[4]{%
            \setlength\fboxsep{0.3cm}\setlength\fboxrule{0.0pt}% delete
            \fbox{% delete
                    \textcolor{teamColor}{{\vrule width 0.3cm}}\ \
                    \begin{minipage}[c][5cm][t]{9cm}%
                        \begin{tabularx}{\textwidth}{lXr}
                            \raisebox{-\height+\fontcharht\font`X}{#1} \vspace{0.2cm} & #2 & \raisebox{-\height+\fontcharht\font`X}{{#3}}
                        \end{tabularx}
                        \vspace{-2mm}

                        {#4}
                    \end{minipage}%
            }% delete
        }
        """

    def emptyTechNode(self, file, tech):
        unlocks = ""
        file.write(self.cardHeader((255, 255, 255)))
        file.write(r"""
        \begin{document}
            \TechCard
                {}
                {}
                {}
                {\begin{center}\huge\vspace{1cm} """ + tech.nodeTag + r"""\end{center}}
        \end{document})
        """)

    def formatVyroba(self, vyroba):
        if vyroba.output.isProduction:
            label = r"\uline{" + vyroba.label + "}"
            if VyrobaModel.objects.filter(id=vyroba.id + "-material"):
                label += " +M"
            return label
        return vyroba.label

    def techNode(self, file, tech):
        """
        Generate LaTeX file with tech node
        """

        description = r"{\Large\textbf{" + tech.label + r"}}" + "\n\n"
        vyrobas = tech.unlock_vyrobas.all()
        previous = False
        if vyrobas and True:
            if len(vyrobas) == 1:
                description += r"\textbf{Odemyká výrobu:}"
            else:
                description += r"\textbf{Odemyká výroby:}"
            description += r"\begin{itemize}[noitemsep,nolistsep,leftmargin=*,after=\vspace*{-\dimexpr\baselineskip - 3pt}]" + "\n"
            for vyroba in vyrobas:
                if vyroba.id.endswith("-material"):
                    continue
                description += r"\item " + self.formatVyroba(vyroba) + "\n"
            description += r"\end{itemize}" + "\n\n"
            previous = True
        enhancers = tech.unlock_enhancers.all()
        if enhancers:
            if previous:
                description += r"\vspace{\dimexpr\baselineskip - 2pt }"
            description += r"\textbf{Odemyká vylepšení:}"
            description += r"\begin{itemize}[noitemsep,nolistsep,leftmargin=*,after=\vspace*{-\dimexpr\baselineskip - 3pt}]" + "\n"
            for enhancer in enhancers:
                description += r"\item " + enhancer.label + "\n"
            description += r"\end{itemize}" + "\n\n"

        unlocksTech = tech.unlocks_tech.all()
        unlocks = ""
        if unlocksTech:
            if tech.id in ["build-pristav"]:
                unlocks += r"""\vspace{-4mm}"""
            if tech.id not in ["tech-matematika", "tech-alchymie"]:
                unlocks += r"""\textbf{Navazující směry bádání:}"""
            unlocks += r"""\begin{itemize}[noitemsep,nolistsep,leftmargin=*,after=\vspace*{-\dimexpr\baselineskip}]""" + "\n"
            for ut in unlocksTech:
                resources = ["{}$\\times$\ {}".format(ut.dots, ut.die.label)]
                resources += ["{}$\\times$\ {}".format(r.amount, self.formatResource(r.resource)) for r in ut.resources.all()]
                unlocks += r"\item " + ut.label + " (" + ", ".join(resources) + ")\n"
            unlocks += r"\end{itemize}" + "\n\n"
        if tech.flavour:
            unlocks += r"\vspace*{\dimexpr\baselineskip + 3pt}"
            unlocks += r"\textit{" + tech.flavour + "}\n\n"

        if tech.image and tech.image != "-":
            icon = r"\includegraphics[width=2.5cm, height=2.5cm, keepaspectratio]{" + os.path.join(self.iconDirectory, tech.image) + r"}"
        else:
            icon = ""

        file.write(self.cardHeader(self.teamColor))
        file.write(r"""
        \begin{document}
            \TechCard
                {\qrcode[version=1,height=2cm]{""" + tech.id + r"""}}
                {""" + description + r"""}
                {""" + icon + r"""}
                {""" + unlocks + r"""

                    \vspace{-3mm}
                    \vspace*{\fill}
                    \begin{center} (""" + tech.nodeTag + r""")\end{center}
                }

        \end{document})
        """)