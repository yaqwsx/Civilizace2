from service.plotting.dot import indent, escapeId, fromMm, digraphHeader, endGraph
import textwrap

from game.data.tech import TechModel

import os
import sys
import subprocess
from pathlib import Path

def fullLabel(tech):
    PADDING = 1
    WIDTH = fromMm(60)
    DESCRIPTION_HEIGHT = fromMm(20)
    DEPENDENCY_HEIGHT = 1
    SQUARE_WIDTH = DESCRIPTION_HEIGHT

    description = """
        <table cellspacing="0" cellpadding="{padding}" border="0" fixedsize="false"
               width="{tableWidth}" height="{tableHeight}">
            <tr>
                <td rowspan="3" border="1" fixedsize="true" width="{qrWidth}" height="{height}">QR</td>
                <td border="1" fixedsize="true" width="{labelWidth}"
                    valign="top" align="center">
                    <font point-size="10"><b>{label}</b></font>
                </td>
            </tr>
            <tr>
                <td border="1">
                    {flavour}
                </td>
            </tr>
            <tr>
                <td border="1">
                    Výroby
                </td>
            </tr>
        </table>
    """.format(
        label=tech.label,
        flavour=tech.flavour,
        tableWidth=WIDTH, tableHeight=DESCRIPTION_HEIGHT,
        height=DESCRIPTION_HEIGHT,
        padding=PADDING,
        qrWidth=SQUARE_WIDTH, labelWidth=WIDTH - SQUARE_WIDTH
    )

    dependencies = """
    <table cellspacing="0" cellpadding="0"  border="0" fixedsize="true"
           width="{width}" height="{height}">
        <tr>
            <td width="{depWidth}" height="{height}" port="dep1"></td>
            <td width="{depWidth}" height="{height}" port="dep2"></td>
            <td width="{depWidth}" height="{height}" port="dep3"></td>
        </tr>
    </table>
    """.format(
        width=WIDTH, height=DEPENDENCY_HEIGHT,
        depWidth=WIDTH/3
    )


    fullLabel = """
    <table cellborder="0" valign="middle">
        <tr><td>{description}</td></tr>
        <tr><td>{dependencies}</td></tr>
    </table>
    """
    return fullLabel.format(**locals())

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

def techNode(file, tech):
    """
    Generate LaTeX file with tech node
    """

    description = r"{\Large\textbf{" + tech.label + r"}}" + "\n\n"
    description += tech.flavour + "\n\n"
    vyrobas = tech.unlock_vyrobas.all()
    if vyrobas:
        if len(vyrobas) == 1:
            description += r"\textbf{Odemyká výrobu:}"
        else:
            description += r"\textbf{Odemyká výroby:}"
        description += r"\begin{itemize}[noitemsep,nolistsep,leftmargin=*]" + "\n"
        for vyroba in tech.unlock_vyrobas.all():
            description += r"\item " + vyroba.label + "\n"
        description += r"\end{itemize}" + "\n\n"

    unlocksTech = tech.unlocks_tech.all()
    unlocks = ""
    if unlocksTech:
        unlocks += r"\textbf{Navazující směry bádání:}\begin{itemize}[noitemsep,nolistsep,leftmargin=*]" + "\n"
        for ut in unlocksTech:
            resources = ["{}$\\times$ {} kostka".format(ut.dots, ut.die.label)]
            resources += ["{}$\\times$ {}".format(r.amount, r.resource.label) for r in ut.resources.all()]
            unlocks += r"\item " + ut.label + " (" + ", ".join(resources) + ")\n"
        unlocks += r"\end{itemize}" + "\n\n"


    file.write(r"""
    \documentclass{standalone}
    \usepackage{amsmath}
    \usepackage{txfonts}
    \usepackage{mdframed}
    \usepackage{qrcode}
    \usepackage{pbox}
    \usepackage{enumitem}

    \newcommand\TechCard[3]{%
        \setlength\fboxsep{0.3cm}\setlength\fboxrule{0.1pt}% delete
        \fbox{% delete
                \hspace{0.5cm}\vrule\ \
                \begin{minipage}[c][5cm][t]{7cm}%
                    \parbox[t][][t]{2.3cm}{\vspace{-10pt}\qrcode[version=1,height=2cm]{ #1 }}%
                    \parbox[t][][t]{4.7cm}{ #2 }

                    \vspace{4pt}

                    #3
                \end{minipage}%
        }% delete
    }

    \begin{document}
        \TechCard
            {""" + tech.id + r"""}
            {""" + description + r"""}
            {""" + unlocks + r"""}
    \end{document}
    """)

class TechBuilder:
    def __init__(self, buildDirectory):
        self.buildDirectory = os.path.abspath(buildDirectory)
        Path(self.buildDirectory).mkdir(parents=True, exist_ok=True)

    def generateTechLabels(self):
        for tech in TechModel.objects.all():
            texSrc = os.path.join(self.buildDirectory, tech.id + ".tex")
            with open(texSrc, "w") as f:
                techNode(f, tech)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                "--output-directory", self.buildDirectory, texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)

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