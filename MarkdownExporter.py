#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import markdown
import mdx_latex
import subprocess
import gtk


class ExportDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self)
        print dir(self)


class MarkdownExporter():
    def __init__(self):
        pass

    def to_pdf(self, text, filename):
        self.to_latex(text, filename)

        subprocess.Popen(''.join['pdflatex ', filename, ' .tex'], shell=True)
        return True

    def to_latex(self, text, filename):
        md = markdown.Markdown(['tables'])
        mkdn2latex = mdx_latex.LaTeXExtension()
        mkdn2latex.extendMarkdown(md, markdown.__dict__)

        out = md.convert(text)
        # Cut leading and trailing <span>-Tags
        out = out[6:-7]

        print out

        # Add some headers and packages
        document = ["""
\\documentclass{article}
\\usepackage{graphicx}
\\begin{document}""", out,
            '\end{document}']

        out = ''.join(document)
        #print out

        with open(''.join[filename, '.tex'], 'w+') as f:
            f.write(out)

    def to_plain_text(self, text, filename):
        with open(filename, 'w+') as f:
            f.write(text)

        # TODO: Success?
        return True
