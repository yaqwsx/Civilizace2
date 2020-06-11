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

    def generateVyrobaLabels(self):
        for vyroba in VyrobaModel.objects.all():
            self.generateVyrobaLabel(vyroba)

    def labelFor(self, vyroba):
        """Get absolute file path for given vyroba label"""
        return os.path.join(self.buildDirectory, vyroba.id + ".pdf")

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
                    \begin{minipage}[c][3.2cm][t]{9cm}%
                        \begin{tabularx}{\textwidth}{lXr}
                            \raisebox{-\height+\fontcharht\font`X}{#1} \vspace{0.2cm} & #2 & \raisebox{-\height+\fontcharht\font`X}{{#3}}
                        \end{tabularx}
                        {#4}
                    \end{minipage}%
            }% delete
        }
        """

    def enhancementHeader(self):
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

        \newcommand\EnhancementCard[1]{%
            \setlength\fboxsep{0.3cm}\setlength\fboxrule{0.0pt}% delete
            \fbox{% delete
                    \begin{minipage}[c][3cm][t]{3cm}%
                        #1
                    \end{minipage}%
            }% delete
        }
        """

    def vyrobaCard(self, file, vyroba):
        """
        Generate LaTeX file with tech node
        """

        description = r"{\Large\textbf{" + vyroba.label + r"}}" + "\n\n"
        description += vyroba.flavour + "\n\n"
        description += r"\textbf{Probíhá v: }" + vyroba.build.label + "\n\n"

        longDescription = ""
        longDescription += r"\textbf{Výstup: }" + f"{vyroba.amount} $\\times$ {self.formatResource(vyroba.output)} \n\n"
        longDescription += r"\textbf{Vstupy: }"
        resources = ["{}$\\times$ {}".format(vyroba.dots, vyroba.die.label)]
        resources += ["{}$\\times$ {}".format(r.amount, self.formatResource(r.resource)) for r in vyroba.inputs.all()]
        longDescription += ", ".join(resources) + "\n\n"

        description += longDescription

        if vyroba.output.icon and vyroba.output.icon != "-":
            icon = r"\includegraphics[width=1.5cm, height=1.5cm, keepaspectratio]{" + os.path.join(self.iconDirectory, vyroba.output.icon) + r"}"
        else:
            icon = ""

        file.write(self.vyrobaHeader())
        file.write(r"""
        \begin{document}
            \VyrobaCard
                {\qrcode[version=1,height=2cm]{""" + vyroba.id + r"""}}
                {""" + description + r"""}
                {""" + icon + r"""}
                {""" + "" + r"""}
        \end{document})
        """)

    def enhancementCard(self, file, enh):
        description = r"{\Large\textbf{" + enh.label + r"}}" + "\n\n"
        description += vyroba.flavour + "\n\n"
        description += r"\textbf{Zlepšuje v: }" + enh.vyroba.label + "\n\n"
        description += r"\textbf{Přidává: }" + f"{enh.amount} $\\times$ {self.formatResource(vyroba.output)} \n\n"
        description += r"\textbf{Vstupy: }"
        resources = ["{}$\\times$ {}".format(r.amount, self.formatResource(r.resource)) for r in enh.inputs.all()]
        description += ", ".join(resources) + "\n\n"

        file.write(self.enhancementHeader())
        file.write(r"""
        \begin{document}
            \EnhancementCard{""" + description + r"""}
        \end{document})
        """)
