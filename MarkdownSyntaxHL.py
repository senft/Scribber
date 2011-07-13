#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import pango
import re


class Pattern(object):
    """ Represents one markdown-pattern."""
    def __init__(self, tagn, start, end, length):
        """ Keyword arguments:
        tagn -- the tagname of the tag that should be applied to the
                matched pattern
        start -- the start pattern of the whole pattern
        end -- the end pattern of the whole pattern
        length -- the length of the start-pattern. We need this so we can
                  skip the start of the pattern to continue searching, and
                  not be stuck on matching the begining over and over
                  again.
        """
        self.tagn = tagn
        self.start = start
        self.end = end
        self.length = length


patterns = [Pattern('heading1', re.compile(r"^\#(?!\#) ", re.MULTILINE),
                re.compile(r"\n"), 1),
            Pattern('heading1', re.compile(r"^(.+)\n(=+)$", re.MULTILINE),
                re.compile(r"=+"), 1),
            Pattern('heading2', re.compile(r"^\#{2}(?!\#) ",
                re.MULTILINE), re.compile(r"\n"), 1),
            Pattern('heading2', re.compile(r"^(.+)\n(-+)$", re.MULTILINE),
                re.compile(r"-+"), 1),
            Pattern('heading3', re.compile(r"^\#{3}(?!\#) ",
                re.MULTILINE), re.compile(r"\n"), 1),
            Pattern('heading4', re.compile(r"^\#{4}(?!\#) ",
                re.MULTILINE), re.compile(r"\n"), 1),
            Pattern('heading5', re.compile(r"^\#{5}(?!\#) ",
                re.MULTILINE), re.compile(r"\n"), 1),
            Pattern('heading6', re.compile(r"^\#{6} ",
                re.MULTILINE), re.compile(r"\n"), 1),

            Pattern('table_default', re.compile(r"^\* ", re.MULTILINE),
                re.compile(r"\n"), 1),
            Pattern('table_default', re.compile(r"^\+ ", re.MULTILINE),
                re.compile(r"\n"), 1),
            Pattern('table_default', re.compile(r"^\- ", re.MULTILINE),
                re.compile(r"\n"), 1),

            Pattern('table_sorted', re.compile(r"^\d+\. ", re.MULTILINE),
                re.compile(r"\n"), 1),

            Pattern('blockquote', re.compile(r"^>", re.MULTILINE),
                re.compile(r"\n"), 1),

            Pattern('image', re.compile(r"\!\(\w*\)\[\w|.+\]"),
                    re.compile(r"\[\w|.+\]"), 1),

            Pattern('underlined', re.compile(r"_\w"), re.compile(r"\w_"),
                1),
            Pattern('italic', re.compile(r"(?<!\*)(\*\w)"),
                re.compile(r"(\w\*)"), 1),
            Pattern('bold', re.compile(r"\*\*\w"), re.compile(r"\w\*\*"),
                2),
            Pattern('bolditalic', re.compile(r"\*\*\*\w"),
                re.compile(r"\w\*\*\*"), 3)]


class MarkdownSyntaxHL(object):
    def __init__(self, buffer):
        self.buffer = buffer

        self.buffer.connect_after("insert-text", self._on_insert_text)
        self.buffer.connect_after("delete-range", self._on_delete_range)
        self.buffer.connect('apply-tag', self._on_apply_tag)

        self.tag_heading1 = self.buffer.create_tag("heading1",
            weight=pango.WEIGHT_BOLD, left_margin=30)
        self.tag_heading2 = self.buffer.create_tag("heading2",
            weight=pango.WEIGHT_BOLD, left_margin=40)
        self.tag_heading3 = self.buffer.create_tag("heading3",
            weight=pango.WEIGHT_BOLD, left_margin=50)
        self.tag_heading4 = self.buffer.create_tag("heading4",
            weight=pango.WEIGHT_BOLD, left_margin=60)
        self.tag_heading5 = self.buffer.create_tag("heading5",
            weight=pango.WEIGHT_BOLD, left_margin=70)
        self.tag_heading6 = self.buffer.create_tag("heading6",
            weight=pango.WEIGHT_BOLD, left_margin=80)

        self.tag_table_default = self.buffer.create_tag("table_default",
            left_margin=110)
        self.tag_table_sorted = self.buffer.create_tag("table_sorted",
            left_margin=110)

        self.tag_blockquote = self.buffer.create_tag('blockquote',
                              left_margin=110, style=pango.STYLE_ITALIC)

        self.tag_image = self.buffer.create_tag('image',
                         style=pango.STYLE_ITALIC)

        self.tag_underlined = self.buffer.create_tag("underlined",
                              underline=pango.UNDERLINE_SINGLE)
        self.tag_bold = self.buffer.create_tag("bold",
                        weight=pango.WEIGHT_BOLD)
        self.buffer.tag_italic = self.buffer.create_tag("italic",
                                 style=pango.STYLE_ITALIC)
        self.buffer.tag_bolditalic = self.buffer.create_tag("bolditalic",
            weight=pango.WEIGHT_BOLD, style=pango.STYLE_ITALIC)

    def _on_apply_tag(self, buffer, tag, start, end):
        # FIXME This is a hack! It allows apply-tag only while
        #       _on_insert_text() and _on_delete_range() so we dont paste
        #       tagged text
        if not self.buffer._apply_tags:
            self.buffer.emit_stop_by_name('apply-tag')
            return True

    def _on_insert_text(self, buffer, iter, text, length):
        # Continue a table if we got one
        if iter.has_tag(self.buffer.tag_table_default) and text == '\n':
            start = iter.copy()
            start.backward_line()

            if start.get_text(iter) == '* \n':
                self.buffer.delete(start, iter)
            else:
                self.buffer.insert_at_cursor('* ')
        elif iter.has_tag(self.buffer.tag_table_sorted) and text == '\n':
            # Same
            self.buffer.insert_at_cursor('\d ')

        self.buffer._apply_tags = True
        self._update_markdown()
        self.buffer._apply_tags = False

    def _on_delete_range(self, buffer, start, end):
        self.buffer._apply_tags = True
        self._update_markdown()
        self.buffer._apply_tags = False

    def get_cursor_iter(self):
        return self.buffer.get_iter_at_mark(self.buffer.get_insert())

    def _update_markdown(self, start=None, end=None):
        """ Removes all tags from whole buffer and renews markdown syntax
            highlighting from "bottom to top".
        """
        if not start:
            start = self.buffer.get_start_iter()

        if not end:
            end = self.buffer.get_end_iter()

        # Only remove markdown tags (no focus tags)
        for pattern in patterns:
            self.buffer.remove_tag_by_name(pattern.tagn, start, end)

        for pattern in self._get_markdown_patterns(start, end):
            self.buffer.apply_tag_by_name(pattern['tagn'], pattern['start'],
                                   pattern['end'])

    def _get_markdown_patterns(self, start, end):
        """ Returns all found markdown patterns in this buffer."""
        text = start.get_text(end)
        for pattern in patterns:
            used_iters = []
            search_start = start.copy()

            while True:
                try:
                    iter_already_used = False
                    match = self.buffer._find_pattern(pattern,
                            text[search_start.get_offset():end.get_offset()],
                            search_start, end)

                    for iter in used_iters:
                        if iter.equal(match['start']):
                            search_start.forward_chars(pattern.length)
                            iter_already_used = True
                    if iter_already_used:
                        continue

                    used_iters.append(match['start'])
                    if not match['end'].equal(end):
                        new_end = match['end'].copy()
                        # TODO WTF is this shit? Why do i need to go back?!
                        new_end.backward_chars(pattern.length)
                        used_iters.append(new_end)

                    # Continue "next" search behind this match
                    search_start = match['start'].copy()
                    search_start.forward_chars(pattern.length)

                    yield match

                except self.buffer.NoPatternFound:
                    break
