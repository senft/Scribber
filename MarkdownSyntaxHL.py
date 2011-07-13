#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import pango
import re


class NoPatternFound(Exception):
    pass


class Pattern(object):
    """ Represents one markdown-pattern."""
    def __init__(self, tagn, start, length, end=None, flags=0):
        """ Keyword arguments:
        tagn -- the tagname of the tag that should be applied to the
                matched pattern
        start -- the start pattern of the whole pattern
        length -- the length of the start-pattern. We need this so we can
                  skip the start of the pattern to continue searching, and
                  not be stuck on matching the begining over and over
                  again.
        end -- if you want to match a specific end, independently from your
               start, define the pattern here
        flags -- RE.flags for the patterns (seperator multiple flags with a '|'
                 e.g. re.MULTILINE|re.IGNORECASE)
        """
        self.tagn = tagn
        self.start = re.compile(start, flags)
        if end:
            self.end = re.compile(end, flags)
        else:
            self.end = None
        self.length = length

patterns = [# atx headers
            Pattern('heading1', r"^\# .*$", 1, flags=re.MULTILINE),
            Pattern('heading2', r"^\#\# .*$", 1, flags=re.MULTILINE),
            Pattern('heading3', r"^\#{3} .*$", 1, flags=re.MULTILINE),
            Pattern('heading4', r"^\#{4} .*$", 1, flags=re.MULTILINE),
            Pattern('heading5', r"^\#{5} .*$", 1, flags=re.MULTILINE),
            Pattern('heading6', r"^\#{6} .*$", 1, flags=re.MULTILINE),
            # Setext headers
            Pattern('heading1', r"^(.+?)\n(=+)$", 1, flags=re.MULTILINE),
            Pattern('heading2', r"^(?![\!-\*\+])(.+?)\n(-+)$", 1,
                    flags=re.MULTILINE),

            # tables
            Pattern('table_default', r"^\* .*?$", 1, flags=re.MULTILINE),
            Pattern('table_default', r"^\+ .*?$", 1, flags=re.MULTILINE),
            Pattern('table_default', r"^\- .*?$", 1, flags=re.MULTILINE),
            Pattern('table_sorted', r"^\d+\. .*?$", 1, flags=re.MULTILINE),

            Pattern('blockquote', r"^>", 1, flags=re.MULTILINE, end=r"\n"),

            Pattern('image', r"\!\(\w*\)\[\w|.+\]", 1, end=r"\[\w|.+\]"),

            # basic inline formatting
            Pattern('underlined', r"_\w", 1, end=r"\w_"),
            Pattern('italic', r"(?<!\*)(\*\w)", 1, end=r"(\w\*)"),
            Pattern('bold', r"\*\*\w", 2, end=r"\w\*\*"),
            Pattern('bolditalic', r"\*\*\*\w", 3, end=r"\w\*\*\*")]


class MarkdownSyntaxHL(object):
    def __init__(self, buffer):
        self.buffer = buffer

        self.tags = buffer.tags

        self.buffer.connect_after("insert-text", self._on_insert_text)
        self.buffer.connect_after("delete-range", self._on_delete_range)
        self.buffer.connect('apply-tag', self._on_apply_tag)

        self.tags['heading1'] = self.buffer.create_tag("heading1",
            weight=pango.WEIGHT_BOLD, left_margin=30)
        self.tags['heading2'] = self.buffer.create_tag("heading2",
            weight=pango.WEIGHT_BOLD, left_margin=40)
        self.tags['heading3'] = self.buffer.create_tag("heading3",
            weight=pango.WEIGHT_BOLD, left_margin=50)
        self.tags['heading4'] = self.buffer.create_tag("heading4",
            weight=pango.WEIGHT_BOLD, left_margin=60)
        self.tags['heading5'] = self.buffer.create_tag("heading5",
            weight=pango.WEIGHT_BOLD, left_margin=70)
        self.tags['heading6'] = self.buffer.create_tag("heading6",
            weight=pango.WEIGHT_BOLD, left_margin=80)

        self.tags['table_default'] = self.buffer.create_tag("table_default",
            left_margin=110)
        self.tags['table_sorted'] = self.buffer.create_tag("table_sorted",
            left_margin=110)

        self.tags['blockquote'] = self.buffer.create_tag('blockquote',
                              left_margin=110, style=pango.STYLE_ITALIC)

        self.tags['image'] = self.buffer.create_tag('image',
                         style=pango.STYLE_ITALIC)

        self.tags['underlined'] = self.buffer.create_tag("underlined",
                              underline=pango.UNDERLINE_SINGLE)
        self.tags['bold'] = self.buffer.create_tag("bold",
                        weight=pango.WEIGHT_BOLD)
        self.tags['italic'] = self.buffer.create_tag("italic",
                                 style=pango.STYLE_ITALIC)
        self.tags['bolditalic'] = self.buffer.create_tag("bolditalic",
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
        if iter.has_tag(self.tags['table_default']) and text == '\n':
            start = iter.copy()
            start.backward_line()

            if start.get_text(iter) == '* \n':
                self.buffer.delete(start, iter)
            else:
                self.buffer.insert_at_cursor('* ')
        elif iter.has_tag(self.buffer.tags['table_sorted']) and text == '\n':
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
            used_iters = set()
            search_start = start.copy()

            while True:
                try:
                    match = self._find_pattern(pattern,
                            text[search_start.get_offset():end.get_offset()],
                            search_start, end)

                    if match['start'].get_offset() in used_iters:
                        search_start.forward_chars(pattern.length)
                        continue

                    used_iters.add(match['start'].get_offset())
                    if not match['end'].equal(end):
                        new_end = match['end'].copy()
                        # TODO WTF is this shit? Why do i need to go back?!
                        new_end.backward_chars(pattern.length)
                        used_iters.add(new_end.get_offset())

                    # Continue "next" search behind this match
                    search_start = match['start'].copy()
                    search_start.forward_chars(pattern.length)

                    yield match

                except NoPatternFound:
                    break

    def _find_pattern(self, pattern, text, start, end):
        """ Returns the first occurence of pattern in text.

            Keyword arguments:
            pattern -- the RE object to match
            text -- the text in which to search
            start -- the beginning of 'text' in the overlaying gtkTextBuffer
            end -- the end of 'text' in the overlaying gtkTextBuffer
        """

        # Match begining
        result_start = pattern.start.search(text)

        if result_start:
            # Forward until start of match
            start_index = result_start.start()
            mstart = start.copy()
            mstart.forward_chars(start_index)

            # Do we have a end pattern?
            if pattern.end:
                # Match end (start searching _after_ the matched start)
                result_end = pattern.end.search(text[start_index:])
                if result_end:
                    mend = mstart.copy()
                    mend.forward_chars(result_end.end())
                else:
                    # No pattern for end found -> match until end
                    mend = self.buffer.get_end_iter()
            else:
                # No end pattern specified -> use end of start-match as pattern
                # end
                mend = start.copy()
                mend.forward_chars(result_start.end())

            return dict(tagn=pattern.tagn, start=mstart, end=mend,
                        length=pattern.length)
        else:
            raise NoPatternFound("Pattern not found.")


