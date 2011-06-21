#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import docutils.core
import docutils.nodes as nodes
import docutils.utils as utils
from docutils.parsers.rst import roles
import subprocess
import re


class ReSTExporter():
    def __init__(self, buffer):
        self.buffer = buffer

    def role_bolditalic(name, rawtext, text, lineno, inliner, options={},
        content=[]):

        node = nodes.emphasis('', '', **options)
        node.append(nodes.strong(rawtext, utils.unescape(text), **options))
        return [node], []

    roles.register_canonical_role('bolditalic', role_bolditalic)

    def extend_rst(self, text):
        # Convert ***foo*** to :bolditalic:`foo`
        text = re.sub(r'(?<!\w)\*\*\*(.+?)\*\*\*', ':bolditalic:`\\1`', text)

        # Convert foo***bar***baz to foo\ ***bar***\ baz, because ReST does not
        # allow hilight chars in a word
        text = re.sub(r'(\w)\*\*\*(.+?)\*\*\*(\w)',
            '\\1\ :bolditalic:`\\2`\ \\3', text)

        # Convert foo**bar**baz to foo\ **bar**\ baz, because ReST does not
        # allow hilight chars in a word
        # TODO: What if a pattern starts (ends) with "foo*as" but ends (starts)
        # with "bar* foo"
        text = re.sub(r'([\w*])\*\*(.+?)\*\*([\w*])', '\\1\ **\\2**\ \\3', text)

        # Convert foo*bar*baz to foo\ *bar*\ baz, because ReST does not allow
        # emphazising chars in a word
        text = re.sub('r(\w)\*(?!\*)(.+?)\*(\w)', '\\1\ *\\2*\ \\3', text)

        return text

    def to_plain_text(self, filename):
        text = self.buffer.get_start_iter().get_text( \
            self.buffer.get_end_iter())

        with open(filename, 'w+') as f:
            f.write(text)

        # TODO Check if was succesfull
        return True

    def to_pdf(self, filename):
        text = self.buffer.get_start_iter().get_text( \
            self.buffer.get_end_iter())

        #text = self.extend_rst(text)

        with open(filename + '.rst', 'w+') as f:
            f.write(text)

        docutils.core.publish_file(source=file(filename + '.rst', 'r'),
            writer_name='LaTeX2e', destination=file(filename + '.tex', 'w+'))
        subprocess.Popen('pdflatex ' + filename + ' .tex', shell=True)

    def to_odt(self, filename):
        text = self.buffer.get_start_iter().get_text( \
            self.buffer.get_end_iter())

        text = self.extend_rst(text)

        with open(filename + '.rst', 'w+') as f:
            f.write(text)

        docutils.core.publish_file(source=file(filename + '.rst', 'r'),
            writer_name='odf_odt', destination=file(filename + '.odt', 'w+'))

    def to_html(self, filename):
        pass
