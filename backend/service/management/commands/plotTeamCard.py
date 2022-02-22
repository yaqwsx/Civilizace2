from django.core.management import BaseCommand
import sys
import os
import subprocess

def cardHeader(teamColor):
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

        \definecolor{teamColor}{RGB}{""" + ", ".join([str(x) for x in teamColor]) + r"""}

        \renewcommand*{\arraystretch}{0}

        \newcommand\NameTag[1]{%
            \setlength\fboxsep{0.3cm}\setlength\fboxrule{0.0pt}% delete
            \fbox{% delete
                    \textcolor{teamColor}{{\vrule width 0.5cm}}\ \
                    \begin{minipage}[c][3cm][t]{9cm}%
                        {#1}
                    \end{minipage}%
            }% delete
        }
        """


class Command(BaseCommand):
    help = "Draw tech tree"

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str)
        parser.add_argument("--id", type=str, help="Team ID" )
        parser.add_argument("-r", type=int, default=0)
        parser.add_argument("-g", type=int, default=0)
        parser.add_argument("-b", type=int, default=0)

    def handle(self, *args, **kwargs):
        try:
            output = kwargs["output"]
            id = kwargs["id"]
            r, g, b = kwargs["r"], kwargs["g"], kwargs["b"]

            texSrc = output.replace(".pdf", ".tex")
            with open(texSrc, "w") as f:
                f.write(cardHeader((r, g, b)))
                f.write(r"""
                \begin{document}
                    \NameTag{\qrcode[version=1,height=3cm]{""" + id + r"""}}
                \end{document}
                """)
            buildCmd = ["texfot", "pdflatex", "-halt-on-error", "--output-directory", os.path.dirname(texSrc), texSrc]
            subprocess.run(buildCmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            cmd = " ".join(e.cmd)
            sys.stderr.write(f"Command '{cmd}' failed:\n")
            sys.stderr.write(e.stdout.decode("utf8"))
            sys.stderr.write(e.stderr.decode("utf8"))
            raise






