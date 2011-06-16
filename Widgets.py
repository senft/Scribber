#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Widgets for Scribber
"""

import pygtk
pygtk.require('2.0')
import gtk
import re
import pango


class ScribberTextView(gtk.TextView):
    def __init__(self):
        gtk.TextView.__init__(self)

        self.focus = True

        self.set_buffer(ScribberTextBuffer())

        self.connect_after('key-press-event', self._on_key_event)
        self.connect('key-release-event', self._on_key_event)
        self.connect_after('button-press-event', self._on_button_event)
        self.connect('button-release-event', self._on_button_event)
        self.connect('move-cursor', self._on_move_cursor)

        font = pango.FontDescription("Bitstream 12")
        self.modify_font(font)

        # Wrap mode
        self.set_wrap_mode(gtk.WRAP_WORD_CHAR)

        # Paragraph spacing
        self.set_pixels_above_lines(3)
        self.set_pixels_below_lines(3)

        self.set_right_margin(80)
        self.set_left_margin(80)

        # Line spacing
        self.set_pixels_inside_wrap(7)

        self._focus_current_sentence()

    def open_file(self, filename):
        with open(filename, 'r') as f:
            data = f.read()

        self.get_buffer().set_text(data)

        self.get_buffer().emit('insert-text',
            self.get_buffer().get_start_iter(), '', 0)

        self.get_buffer().place_cursor(self.get_buffer().get_start_iter())
        self._focus_current_sentence()

        self.set_text_not_modified()

        # Success?
        return True


    def is_text_modified(self):
        return self.get_buffer().is_modified

    def set_text_not_modified(self):
        self.get_buffer().is_modified = False

    def _on_move_cursor(self, step_size, count, extend_selection, data=None):
        self._focus_current_sentence()

    def _on_key_event(self, event, data=None):
        self._focus_current_sentence()

    def _on_button_event(self, event, data=None):
        self._focus_current_sentence()

    def _focus_current_sentence(self):
        if self.focus:
            self.get_buffer().focus_current_sentence()
            self.scroll_to_mark(self.get_buffer().get_insert(), 0.0, True,
                0.0, 0.5)


class ScribberTextBuffer(gtk.TextBuffer):

    patterns = [['heading1', re.compile('\#(?!\#) '), re.compile('\n'), 1],
                ['heading2', re.compile('\#{2}(?!\#) '), re.compile('\n'), 1],
                ['heading3', re.compile('\#{3}(?!\#) '), re.compile('\n'), 1],
                ['heading4', re.compile('\#{4}(?!\#) '), re.compile('\n'), 1],
                ['heading5', re.compile('\#{5}(?!\#) '), re.compile('\n'), 1],
                ['heading6', re.compile('\#{6} '), re.compile('\n'), 1],
                ['table_default', re.compile('\* '), re.compile('\n'), 1],
                ['table_sorted', re.compile('\d+\. '), re.compile('\n'), 1],
                ['italic', re.compile('(?<!\*)(\*\w)'),
                  re.compile('(\w\*)(?!\*)'), 1],
                ['bold', re.compile('\*\*\w'), re.compile('\w\*\*'), 2],
                ['bolditalic', re.compile('\*\*\*\w'),
                   re.compile('\w\*\*\*'), 3]]

    def __init__(self):
        gtk.TextBuffer.__init__(self)
        
        self.connect_after("insert-text", self._on_insert_text)
        self.connect_after("delete-range", self._on_delete_range)
        self.connect('apply-tag', self._on_apply_tag)
        self.connect('changed', self._on_changed)

        self.tag_default = self.create_tag("default", foreground="#888888")

        self.tag_focus = self.create_tag("focus", foreground="#000000")

        self.tag_heading1 = self.create_tag("heading1",
            weight=pango.WEIGHT_BOLD, left_margin=30)
        self.tag_heading2 = self.create_tag("heading2",
            weight=pango.WEIGHT_BOLD, left_margin=40)
        self.tag_heading3 = self.create_tag("heading3",
            weight=pango.WEIGHT_BOLD, left_margin=50)
        self.tag_heading4 = self.create_tag("heading4",
            weight=pango.WEIGHT_BOLD, left_margin=60)
        self.tag_heading5 = self.create_tag("heading5",
            weight=pango.WEIGHT_BOLD, left_margin=70)
        self.tag_heading6 = self.create_tag("heading6",
            weight=pango.WEIGHT_BOLD, left_margin=80)

        self.tag_table_default = self.create_tag("table_default",
            left_margin=110)
        self.tag_table_sorted = self.create_tag("table_sorted",
            left_margin=110)

        self.tag_bold = self.create_tag("bold", weight=pango.WEIGHT_BOLD)
        self.tag_italic = self.create_tag("italic", style=pango.STYLE_ITALIC)
        self.tag_bolditalic = self.create_tag("bolditalic",
            weight=pango.WEIGHT_BOLD, style=pango.STYLE_ITALIC)

        self.is_modified = False

    def _on_changed(self, buf, data=None):
        self.is_modified = True

    def _on_apply_tag(self, buf, tag, start, end):
        # FIXME This is a hack! It allows apply-tag only while
        #       _on_insert_text() and _on_delete_range() so we dont paste
        #       tagged text
        if not self._apply_tags:
            self.emit_stop_by_name('apply-tag')
            return True

    def _on_insert_text(self, buf, iter, text, length):
        if iter.has_tag(self.tag_table_default) and text == "\n":
            # If line is not empty
            self.insert_at_cursor("* ")
            # else
            #   clear line
        if iter.has_tag(self.tag_table_sorted) and text == "\n":
            # Same
            self.insert_at_cursor("\d ")

        self._apply_tags = True
        self._update_markdown(self.get_start_iter())
        self._apply_tags = False

    def _on_delete_range(self, buf, start, end):
        self._apply_tags = True
        self._update_markdown(self.get_start_iter())
        self._apply_tags = False

    def _update_markdown(self, start, end=None):
        # Used to save which iters we already used as start or end of a pattern
        used_iters = []

        if end is None:
            end = self.get_end_iter()

        finished = False

        # Only remove markdown tags (no focus tags)
        for p in self.patterns:
            self.remove_tag_by_name(p[0], start, end)

        while not finished:
            tagn, mstart, mend, length = self._get_first_pattern(start, end)

            if tagn:
                # Found a pattern
                if mstart.get_offset() + length in used_iters or \
                    (mend.get_offset() in used_iters and not mend.equal(end)):
                    start = mstart
                    start.forward_chars(length)
                    continue

                self.apply_tag_by_name(tagn, mstart, mend)

                used_iters.append(mstart.get_offset())
                used_iters.append(mend.get_offset())

                start = mstart
                start.forward_chars(length)

                if start == end:
                    finished = True
            else:
                # No pattern found
                finished = True

    def _get_first_pattern(self, start, end):
        """ Returns (tagname, start, end, length) of the first occurence of any
            known pattern in this buffer. """
        matches = []

        for pattern in self.patterns:
            mstart = start.copy()

            pattern_tagn, pattern_start, pattern_end, pattern_length = pattern

            # Match begining
            result_start = pattern_start.search(mstart.get_text(end))
            if result_start:
                # TODO: Maybe: Shortcut here, if we found a match at
                # mstart.get_offset() == 0, because no match will be before
                # that one

                # Forward until start of match
                mstart.forward_chars(result_start.start())

                # Match end
                result_end = pattern_end.search(mstart.get_text(end))
                if result_end:
                    mend = mstart.copy()
                    mend.forward_chars(result_end.end())
                else:
                    # No pattern for end found -> match until end
                    mend = self.get_end_iter()

                matches.append([result_start.start(), [pattern_tagn, mstart,
                    mend, pattern[3]]])

        if len(matches) == 0:
            return (None, None, None, None)
        return min(matches)[1]

    def focus_current_sentence(self):
        """ Applys a highlighting tag to the sentence the cursor is on."""

        self._apply_tags = True

        cursor_iter = self.get_iter_at_mark(self.get_insert())

        starts_sentence = cursor_iter.starts_sentence()
        inside_sentence = cursor_iter.inside_sentence()
        ends_sentence = cursor_iter.ends_sentence()

        start = self.get_start_iter()
        end = self.get_end_iter()

        mstart = cursor_iter.copy()
        mend = cursor_iter.copy()

        self.remove_tag_by_name("focus", start, end)

        if starts_sentence or inside_sentence or ends_sentence:
            if cursor_iter.has_tag(self.tag_table_default):
                # Hilight current table
                mstart.backward_to_tag_toggle(self.tag_table_default)
                mend.forward_to_tag_toggle(self.tag_table_default)
            else:
                # Hilight current sentence
                if not starts_sentence:
                    mstart.backward_sentence_start()
                if not ends_sentence:
                    mend.forward_sentence_end()

            self.apply_tag_by_name("default", start, end)
            self.apply_tag_by_name("focus", mstart, mend)

        self._apply_tags = False

    def stop_focus(self):
        start = self.get_start_iter()
        end = self.get_end_iter()
        self.remove_tag_by_name("default", start, end)
        self.apply_tag_by_name("focus", start, end)

