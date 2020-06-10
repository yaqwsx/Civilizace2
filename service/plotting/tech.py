from service.plotting.dot import indent, escapeId, fromMm, digraphHeader, endGraph
import textwrap

from game.data.tech import TechModel

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
    styles.append('penwidth="50"')
    for i, edge in enumerate(tech.unlocks_tech.all()):
        file.write(indent(indentLevel) + "{}:dep{} -> {}[{}];\n".format(
            escapeId(edge.src.id),
            i + 1,
            escapeId(edge.dst.id),
            ", ".join(styles)
        ))

class TechBuilder:
    def __init__(self, buildDirectory, iconDirectory):
        self.iconDirectory = os.path.abspath(iconDirectory)
        self.buildDirectory = os.path.abspath(buildDirectory)
        Path(self.buildDirectory).mkdir(parents=True, exist_ok=True)

    def generateTechLabel(self, tech):
        try:
            texSrc = os.path.join(self.buildDirectory, tech.id + ".tex")
            with open(texSrc, "w") as f:
                self.techNode(f, tech)
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

    def fullGraphFile(self):
        return os.path.join(self.buildDirectory, "fullGraph.pdf")

    def generateFullGraph(self):
        try:
            dotFile = os.path.join(self.buildDirectory, "fullGraph.dot")
            texFile = os.path.join(self.buildDirectory, "fullGraph.tex")
            techs = TechModel.objects.all()
            with open(dotFile, "w") as f:
                digraphHeader(f)
                for t in techs:
                    declareTech(f, t, self.labelFor(t))
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

    def techNode(self, file, tech):
        """
        Generate LaTeX file with tech node
        """

        description = r"{\Large\textbf{" + tech.label + r"}}" + "\n\n"
        description += tech.flavour + "\n\n"
        vyrobas = tech.unlock_vyrobas.all()
        anyList = False
        if vyrobas and True:
            anyList = True
            if len(vyrobas) == 1:
                description += r"\textbf{Odemyká výrobu:}"
            else:
                description += r"\textbf{Odemyká výroby:}"
            description += r"\begin{itemize}[noitemsep,nolistsep,leftmargin=*,topsep=0pt,partopsep=0pt,parsep=0pt]" + "\n"
            for vyroba in vyrobas:
                description += r"\item " + vyroba.label + "\n"
            description += r"\end{itemize}" + "\n\n"
        enhancers = tech.unlock_enhancers.all()
        if enhancers:
            anyList = True
            description += r"\textbf{Odemyká vylepšení:}"
            description += r"\begin{itemize}[noitemsep,nolistsep,leftmargin=*]" + "\n"
            for enhancer in enhancers:
                description += r"\item " + enhancer.label + "\n"
            description += r"\end{itemize}" + "\n\n"

        # description += "Done"

        unlocksTech = tech.unlocks_tech.all()
        unlocks = ""
        if anyList:
            unlocks += r"\vspace{-2\fontcharht\font`X}" + "\n\n"
        if unlocksTech:
            unlocks += r"\textbf{Navazující směry bádání:}\begin{itemize}[noitemsep,nolistsep,leftmargin=*]" + "\n"
            for ut in unlocksTech:
                resources = ["{}$\\times$ {}".format(ut.dots, ut.die.label)]
                resources += ["{}$\\times$ {}".format(r.amount, self.formatResource(r.resource)) for r in ut.resources.all()]
                unlocks += r"\item " + ut.label + " (" + ", ".join(resources) + ")\n"
            unlocks += r"\end{itemize}" + "\n\n"

        if tech.image and tech.image != "-":
            icon = r"\includegraphics[width=3cm, height=3cm, keepaspectratio]{" + os.path.join(self.iconDirectory, tech.image) + r"}"
        else:
            icon = ""


        file.write(r"""
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

        \newcommand\crule[3][black]{\textcolor{#1}{\rule{#2}{#3}}}

        \newcommand\icon[1]{%
            \begingroup\normalfont
                \raisebox{-.25\height}{\includegraphics[height=3\fontcharht\font`\B]{{#1}}}
            \endgroup
        }

        \newcommand\TechCard[4]{%
            \setlength\fboxsep{0.3cm}\setlength\fboxrule{0.0pt}% delete
            \fbox{% delete
                    {\vrule width 0.3cm}\ \
                    \begin{minipage}[c][5cm][t]{9cm}%
                        \begin{tabularx}{\textwidth}{lXr}
                            \raisebox{-\height+\fontcharht\font`X}{\qrcode[version=1,height=2cm]{ #1 }} & { #2 } & \raisebox{-\height+\fontcharht\font`X}{{#3}}
                        \end{tabularx}
                        {#4}
                    \end{minipage}%
            }% delete
        }

        \begin{document}
            \TechCard
                {""" + tech.id + r"""}
                {""" + description + r"""}
                {""" + icon + r"""}
                {""" + unlocks + r"""
                    \vspace*{\fill}
                    \begin{center} (""" + tech.nodeTag + r""")\end{center}
                }

        \end{document}
        """)