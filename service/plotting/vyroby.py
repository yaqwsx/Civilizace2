from service.plotting.dot import indent, escapeId, fromMm, digraphHeader, endGraph
import textwrap

from game.data.vyroba import VyrobaModel, EnhancementModel

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

    def generateEnhancementLabel(self, enh):
        try:
            texSrc = os.path.join(self.buildDirectory, enh.id + ".tex")
            with open(texSrc, "w") as f:
                self.enhancementCard(f, enh)
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

    def generateEnhancementLabels(self):
        for enh in EnhancementModel.objects.all():
            self.generateEnhancementLabel(enh)

    def labelFor(self, vyroba):
        """Get absolute file path for given vyroba label"""
        return os.path.join(self.buildDirectory, vyroba.id + ".pdf")

    def formatResource(self, resource):
        if resource.isProduction:
            return r"\uline{" + resource.label.replace("Produkce: ", "") + "}"
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
        \usepackage{ragged2e}
        \usepackage{ulem}
        \renewcommand{\ULdepth}{1pt}

        \renewcommand*{\arraystretch}{0}
        \setlength\parskip{0pt}

        \newcommand\VyrobaCard[4]{%
            \setlength\fboxsep{0.3cm}\setlength\fboxrule{0.0pt}% delete
            \fbox{% delete
                    \begin{minipage}[c][3.8cm][t]{8.6cm}%
                        \begin{tabularx}{\textwidth}{lXr}
                            \raisebox{-\height+\fontcharht\font`X}{#1} \vspace{0.2cm} & \raggedright #2 & \raisebox{-\height+\fontcharht\font`X}{{#3}}
                        \end{tabularx}
                        \vspace{-6mm}
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
        \usepackage{ragged2e}
        \usepackage{ulem}
        \renewcommand{\ULdepth}{1pt}

        \renewcommand*{\arraystretch}{0}

        \newcommand\EnhancementCard[1]{%
            \setlength\fboxsep{0.2cm}\setlength\fboxrule{0.0pt}% delete
            \fbox{% delete
                    \begin{minipage}[c][1cm][t]{8.6cm}%
                       \raggedright #1
                    \end{minipage}%
            }% delete
        }
        """

    def icon(self, icon):
        return os.path.join(self.iconDirectory, icon).replace(".svg", ".pdf")

    def shortCutBuildName(self, vyroba):
        return vyroba.build.label.replace("Alchymistická dílna", "Alch. dílna")

    def vyrobaCard(self, file, vyroba):
        """
        Generate LaTeX file with tech node
        """

        description = r"{\Large\textbf{" + vyroba.label.replace("Materiál", "Mat") + r"}}" + "\n\n"
        description += r"\textbf{Probíhá v: }" + self.shortCutBuildName(vyroba) + "\n\n"

        longDescription = ""
        output = r"\textbf{Výstup: }" + f"{vyroba.amount} $\\times$ {self.formatResource(vyroba.output)} \n\n"
        longDescription += r"\textbf{Vstupy: }"
        resources = ["{}$\\times$\ {}".format(vyroba.dots, vyroba.die.label)]
        resources += ["{}$\\times$\ {}".format(r.amount, self.formatResource(r.resource)) for r in vyroba.inputs.all()]
        longDescription += ", ".join(resources) + "\n\n"

        description += longDescription
        description += vyroba.flavour

        if vyroba.output.icon and vyroba.output.icon != "-":
            icon = r"\includegraphics[width=1.5cm, height=1.5cm, keepaspectratio]{" + self.icon(vyroba.output.icon) + r"}"
        else:
            icon = ""

        file.write(self.vyrobaHeader())
        file.write(r"""
        \begin{document}
            \VyrobaCard
                {\qrcode[version=1,height=2cm]{""" + vyroba.id + r"""}}
                {""" + description + r"""}
                {""" + icon + r"""}
                { \begin{flushright}\vspace*{\fill}""" + output + r"""\end{flushright}}
        \end{document}
        """)

    def emptyVyrobaCard(self, file):
        file.write(self.vyrobaHeader())
        file.write(r"""
        \begin{document}
            \VyrobaCard
                {}
                {}
                {}
                {}
        \end{document}
        """)

    def enhancementCard(self, file, enh):
        description = r"{\Large\textbf{" + enh.label + r"}}" + r"\hspace*{\fill}"
        description += r"\textbf{Zlepšuje: }" + enh.vyroba.label + "\n\n"
        description += r"\textbf{Vstupy: }"
        resources = ["{}$\\times$\ {}".format(r.amount, self.formatResource(r.resource)) for r in enh.inputs.all()]
        description += ", ".join(resources) + r"\hspace*{\fill}"
        description += r"\textbf{Efekt: }" + f" {'+' if enh.amount >= 0 else '-'}{enh.amount} {self.formatResource(enh.vyroba.output)}\n\n"

        file.write(self.enhancementHeader())
        file.write(r"""
        \begin{document}
            \EnhancementCard{""" + description + r"""}
        \end{document}
        """)

    def emptyEnhancementCard(self, file):
        file.write(self.enhancementHeader())
        file.write(r"""
        \begin{document}
            \EnhancementCard{\ }
        \end{document}
        """)

    def allSheetHeader(self):
        return r"""
        \documentclass{article}
        \usepackage[a4paper, total={18cm, 28cm}]{geometry}
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
        \setlength{\tabcolsep}{0pt}
        \pagenumbering{gobble}

        \newcommand\VyrBox[4]{%
            \begin{tabular}{|c|}
                \hline
                #1 \\ \hline
                #2 \\ \hline
                #3 \\ \hline
                #4 \\ \hline
            \end{tabular}
            \vspace{0.15cm}
        }
        """

    def fullSheet(self):
        try:
            texSrc = os.path.join(self.buildDirectory, "empty-vyroba.tex")
            with open(texSrc, "w") as f:
                self.emptyVyrobaCard(f)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                "--output-directory", self.buildDirectory, texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)

            texSrc = os.path.join(self.buildDirectory, "empty-enhancement.tex")
            with open(texSrc, "w") as f:
                self.emptyEnhancementCard(f)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                "--output-directory", self.buildDirectory, texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)

            texSrc = os.path.join(self.buildDirectory, "fullSheet.tex")
            with open(texSrc, "w") as f:
                f.write(self.allSheetHeader())
                f.write(r"""
                \begin{document}
                \noindent""")
                for vyroba in VyrobaModel.objects.all():
                    enhancementList = list([enh.id for enh in vyroba.enhancers.all()])
                    while len(enhancementList) < 3:
                        enhancementList.append("empty-enhancement")
                    f.write(r"""\VyrBox
                        {\includegraphics{""" + os.path.join(self.buildDirectory, vyroba.id) + r""".pdf}}
                        {\includegraphics{""" + os.path.join(self.buildDirectory, enhancementList[0]) + r""".pdf}}
                        {\includegraphics{""" + os.path.join(self.buildDirectory, enhancementList[1]) + r""".pdf}}
                        {\includegraphics{""" + os.path.join(self.buildDirectory, enhancementList[2]) + r""".pdf}}
                    """)
                f.write(r"""
                \end{document}
                """)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                "--output-directory", self.buildDirectory, texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            cmd = " ".join(e.cmd)
            sys.stderr.write(f"Command '{cmd}' failed:\n")
            sys.stderr.write(e.stdout.decode("utf8"))
            sys.stderr.write(e.stderr.decode("utf8"))
            raise

    def emptySheet(self):
        try:
            texSrc = os.path.join(self.buildDirectory, "emptySheet.tex")
            with open(texSrc, "w") as f:
                f.write(self.allSheetHeader())
                f.write(r"""
                \begin{document}
                \noindent""")
                for i in range(6):
                    f.write(r"""\VyrBox
                    {\includegraphics{""" + os.path.join(self.buildDirectory, "empty-vyroba") + r""".pdf}}
                    {\includegraphics{""" + os.path.join(self.buildDirectory, "empty-enhancement") + r""".pdf}}
                    {\includegraphics{""" + os.path.join(self.buildDirectory, "empty-enhancement") + r""".pdf}}
                    {\includegraphics{""" + os.path.join(self.buildDirectory, "empty-enhancement") + r""".pdf}}
                    """)
                f.write(r"""
                \end{document}
                """)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error",
                "--output-directory", self.buildDirectory, texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            cmd = " ".join(e.cmd)
            sys.stderr.write(f"Command '{cmd}' failed:\n")
            sys.stderr.write(e.stdout.decode("utf8"))
            sys.stderr.write(e.stderr.decode("utf8"))
            raise
