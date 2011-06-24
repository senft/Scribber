#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess
import markdown


class MarkdownExporter():
    def __init__(self):
        pass

    def to_pdf(self, text, filename):
        self._to_html(text, filename)

        return True

    def _to_html(self, text, filename):

        with open(filename, 'w+') as f:
            f.write(text)
        
