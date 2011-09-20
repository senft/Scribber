#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import gtk
import subprocess
import markdown
import mdx_latex

TEX_HEADER = r"""\documentclass[a4paper, 12pt, oneside, german]{scrreprt}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[ngerman]{babel}
\usepackage[left=3cm, right=3cm, top=3cm, bottom=3cm, includehead]{geometry}

\usepackage{listings, setspace, graphicx, color, hyperref, fancyhdr, amsmath,
            tabularx, dsfont, amsthm}

\setkomafont{disposition}{\normalcolor\bfseries}

\pagestyle{headings}

%Kopf- und Fußzeile
\pagestyle{fancy}
\fancyhf{}
\headheight 15pt

%Kopfzeile rechts oben mit Kapitelname in Kapitälchen
\fancyhead[R]{\textsc{\nouppercase{\leftmark}}}

%Fußzeile rechts mit Seitenzahl
\fancyfoot[R]{\thepage}
\begin{document}
"""


class ExportDialog(gtk.Dialog):
    """ TODO: Shows a dialog where one can specify how he wants to export.
              This returns a dict containing the options.
              e.g.
                return {'article' : 1, 'encoding' : 'utf-8',
                        size : 12pt, margins, ...  }
    """
    def __init__(self):
        gtk.Dialog.__init__(self)
        print dir(self)


class MarkdownExporter(object):
    def __init__(self):
        pass

    def to_pdf(self, text, filename):
        if self.to_latex(text, filename):
            # TODO Use gobject.child_watch_add() to wait for pdflatex to finish
            subprocess.Popen(''.join(['pdflatex ', filename, ' .tex']),
                shell=True)
        return True

    def to_latex(self, text, filename):
        md = markdown.Markdown(['tables'])
        mkdn2latex = mdx_latex.LaTeXExtension()
        mkdn2latex.extendMarkdown(md, markdown.__dict__)

        out = md.convert(text)
        # Cut leading and trailing <span>-Tags
        out = out[6:-7]

        # Add some headers and packages
        document = [TEX_HEADER, out, '\end{document}']

        out = ''.join(document)
        #print out

        return self._write_to_file(out, ''.join([filename, '.tex']))

    def to_plain_text(self, text, filename):
        return self._write_to_file(text, filename)

    def _write_to_file(self, text, filename):
        result = True
        try:
            with open(filename, 'w+') as f:
                f.write(text)
        except IOError:
            result = False

        return result
