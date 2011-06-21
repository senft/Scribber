#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
All custom widgets used in Scribber.
* ScribberTextView is a gtk.TextView with some basic formatting and
mechanisms to focus the current sentence
* ScribberTextBuffer is the underlying gtk.TextBuffer. It has automatic
Markdown-Syntax-Hilighting and features simple hilighting for find and
replace
* ScribberFindBox is a simple gtk.HBox containing the usual widgets
used in a Find-Windget
* ScribberFindReplaceBox is the same as ScribberFindBox for find/replace
"""

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import re
import pango
import collections


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
        self.set_wrap_mode(gtk.WRAP_WORD)

        # Paragraph spacing
        self.set_pixels_above_lines(3)
        self.set_pixels_below_lines(3)

        self.set_right_margin(80)
        self.set_left_margin(80)

        # Line spacing
        self.set_pixels_inside_wrap(7)

        self.focus_current_sentence()

    def open_file(self, filename):
        with open(filename, 'r') as f:
            data = f.read()

        self.get_buffer().set_text(data)

        self.get_buffer().emit('insert-text',
            self.get_buffer().get_start_iter(), '', 0)

        self.get_buffer().place_cursor(self.get_buffer().get_start_iter())
        self.focus_current_sentence()
        self.get_buffer().set_modified(False)

        # Success?
        return True

    def focus_current_sentence(self):
        if self.focus:
            self.get_buffer().focus_current_sentence()
            self.scroll_to_mark(self.get_buffer().get_insert(), 0.0, True,
                0.0, 0.5)

    def _on_move_cursor(self, widet, step_size, count, extend_selection,
        data=None):

        self.focus_current_sentence()

    def _on_key_event(self, widget, event, data=None):
        self.focus_current_sentence()

    def _on_button_event(self, widget, event, data=None):
        self.focus_current_sentence()


class ScribberTextBuffer(gtk.TextBuffer):

    patterns = [['heading1', re.compile(r'^\#(?!\#) ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['heading1', re.compile(r'^(.+)\n(=+)', re.MULTILINE),
                    re.compile(r'(=+)'), 1],
                ['heading2', re.compile(r'^\#{2}(?!\#) ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['heading2', re.compile(r'^(.+)\n(-+)', re.MULTILINE),
                    re.compile(r'(-+)'), 1],
                ['heading3', re.compile(r'^\#{3}(?!\#) ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['heading4', re.compile(r'^\#{4}(?!\#) ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['heading5', re.compile(r'^\#{5}(?!\#) ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['heading6', re.compile(r'^\#{6} ', re.MULTILINE),
                    re.compile(r'\n'), 1],

                ['table_default', re.compile(r'^\* ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['table_default', re.compile(r'^\+ ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['table_default', re.compile(r'^\- ', re.MULTILINE),
                    re.compile(r'\n'), 1],
                ['table_sorted', re.compile(r'^\d+\. ', re.MULTILINE),
                    re.compile(r'\n'), 1],

                ['blockquote', re.compile(r'^>', re.MULTILINE),
                    re.compile(r'\n'), 1],

                ['underlined', re.compile(r'_\w'), re.compile(r'\w_'), 1],
                ['italic', re.compile(r'(?<!\*)(\*\w)'),
                  re.compile(r'(\w\*)(?!\*)'), 1],
                ['bold', re.compile(r'\*\*\w'), re.compile(r'\w\*\*'), 2],
                ['bolditalic', re.compile(r'\*\*\*\w'),
                   re.compile(r'\w\*\*\*'), 3]]

    def __init__(self):
        gtk.TextBuffer.__init__(self)

        self.connect_after("insert-text", self._on_insert_text)
        self.connect_after("delete-range", self._on_delete_range)
        self.connect('apply-tag', self._on_apply_tag)

        self.tag_default = self.create_tag("default", foreground="#888888")
        self.tag_focus = self.create_tag("focus", foreground="#000000")
        self.tag_match = self.create_tag('match', background='#FFFF00')

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

        self.tag_blockquote = self.create_tag('blockquote', left_margin=110,
            style=pango.STYLE_ITALIC)

        self.tag_underlined = self.create_tag("underlined",
            underline=pango.UNDERLINE_SINGLE)
        self.tag_bold = self.create_tag("bold", weight=pango.WEIGHT_BOLD)
        self.tag_italic = self.create_tag("italic", style=pango.STYLE_ITALIC)
        self.tag_bolditalic = self.create_tag("bolditalic",
            weight=pango.WEIGHT_BOLD, style=pango.STYLE_ITALIC)

    def _on_apply_tag(self, buf, tag, start, end):
        # FIXME This is a hack! It allows apply-tag only while
        #       _on_insert_text() and _on_delete_range() so we dont paste
        #       tagged text
        if not self._apply_tags:
            self.emit_stop_by_name('apply-tag')
            return True

    def _on_insert_text(self, buf, iter, text, length):
        # Continue a table if we got one
        if iter.has_tag(self.tag_table_default) and text == '\n':
            start = iter.copy()
            start.backward_line()

            if start.get_text(iter) == '* \n':
                self.delete(start, iter)
            else:
                self.insert_at_cursor('* ')
        elif iter.has_tag(self.tag_table_sorted) and text == '\n':
            # Same
            self.insert_at_cursor('\d ')

        self._apply_tags = True
        self._update_markdown(self.get_start_iter())
        self._apply_tags = False

    def _on_delete_range(self, buf, start, end):
        self._apply_tags = True
        self._update_markdown(self.get_start_iter())
        self._apply_tags = False

    def _find_all_matches(self, pattern, match_case=False, start=None,
        end=None):
        """ Returns a deque containg a tuple (start_iter, end_iter) for all
            matches of 'pattern'. In order of there occurence starting from
            current cursor position."""
        #TODO: When I search for 'foo bar baz' it should also match
        # 'foo *bar* baz'

        if start is None:
            # Use current cursor position as start
            search_start = self.get_iter_at_mark(self.get_insert())
        else:
            search_start = start

        if end is None:
            search_end = self.get_end_iter()
        else:
            search_end = end

        text = search_start.get_text(search_end)

        # Used to buffer out current matches (for next/back buttons). Using a
        # a deque for easy wrap-around
        matches = collections.deque()

        if match_case:
            needle_re = re.compile(pattern)
        else:
            needle_re = re.compile(pattern, re.IGNORECASE)

        for match in needle_re.finditer(text):
            mstart = search_start.copy()
            mend = search_start.copy()

            mstart.forward_chars(match.start())
            mend.forward_chars(match.end())

            matches.append((mstart, mend))

        # Now match from start to current cursor
        if start is None and end is None:
            matches_from_start = self._find_all_matches(pattern, match_case,
                self.get_start_iter(), start)

            matches.extend(matches_from_start)
        return matches

    def replace_pattern(self, pattern, repl, start, end, match_case=False,
        replace_all=False):

        if start is None:
            start = self.get_start_iter()

        if end is None:
            end = self.get_end_iter()

        text = start.get_text(end)

        if replace_all:
            text = re.sub(pattern, repl, text)
            self.set_text(text)
        else:
            text = re.sub(pattern, repl, text, 1)
            self.delete_selection(True, True)
            self.insert_at_cursor(text)

    def hilight_pattern(self, pattern, match_case=False):
        """ Hilights all matches in buffer and selects the match next to
            current cursor position. """
        self.remove_tag_by_name('match', self.get_start_iter(),
            self.get_end_iter())

        matches = self._find_all_matches(pattern, match_case)

        if matches:
            # If we have matches, we want to make the first match selected
            self.select_range(*matches[0])

        for mstart, mend in matches:
            self._apply_tags = True
            self.apply_tag_by_name('match', mstart, mend)
            self._apply_tags = False

        return matches

    def stop_hilight_pattern(self):
        start = self.get_start_iter()
        end = self.get_end_iter()
        self.remove_tag_by_name('match', start, end)

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


class ScribberFindBox(gtk.HBox):
    def __init__(self, buffer):
        gtk.HBox.__init__(self, False, 4)
        self.matches = None
        self.buffer = buffer
        self.init_gui()

    def init_gui(self):
        self.lbl_find = gtk.Label('Find: ')
        self.txt_find = gtk.Entry()
        self.txt_find.connect('changed', self._on_find_type)
        self.txt_find.connect('key-press-event', self._on_key_press)

        self.btn_next = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.btn_next.connect('clicked', self.next)

        self.btn_back = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.btn_back.connect('clicked', self.back)

        self.chk_matchcase = gtk.CheckButton('Match case')
        self.chk_matchcase.connect('toggled', self._on_toggle_match_case)

        self.add(self.lbl_find)
        self.add(self.txt_find)
        self.add(self.btn_back)
        self.add(self.btn_next)
        self.add(self.chk_matchcase)

    def hilight_search(self, text):
        self.matches = self.buffer.hilight_pattern(text,
            match_case=self.chk_matchcase.get_active())

    def _on_find_type(self, widget):
        """ Called when text in txt_find changes """
        self.hilight_search(widget.get_text())

    def _on_key_press(self, widget, event, data=None):
        if widget == self.txt_find:
            if gtk.gdk.keyval_name(event.keyval) == 'Return':
                # <Return> in txt_find
                self.next()

    def _on_toggle_match_case(self, widget):
        # Search again if match_case changed, because results can be very
        # different
        self.hilight_search(self.txt_find.get_text())

    def next(self, data=None):
        """ Selects next match """
        if self.matches:
            self.matches.rotate(-1)
            start, end = self.matches[0]
            self.buffer.select_range(start, end)

    def back(self, data=None):
        """ Selects last match """
        if self.matches:
            self.matches.rotate()
            start, end = self.matches[0]
            self.buffer.select_range(start, end)


class ScribberFindReplaceBox(ScribberFindBox):
    def init_gui(self):
        self.lbl_find = gtk.Label('Find: ')
        self.txt_find = gtk.Entry()
        self.txt_find.connect('changed', self._on_find_type)
        self.txt_find.connect('key-press-event', self._on_key_press)

        self.lbl_replace = gtk.Label('Replace: ')
        self.txt_replace = gtk.Entry()
        self.txt_replace.connect('key-press-event', self._on_key_press)

        self.btn_replace = gtk.Button('_Replace')
        self.btn_replace.connect('clicked', self._on_replace_click)

        self.btn_replace_all = gtk.Button('Replace a_ll')
        self.btn_replace_all.connect('clicked', self._on_replace_all_click)

        self.chk_matchcase = gtk.CheckButton('Match case')
        self.chk_matchcase.connect('toggled', self._on_toggle_match_case)

        self.btn_next = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.btn_next.connect('clicked', self.next)

        self.btn_back = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.btn_back.connect('clicked', self.back)

        self.add(self.lbl_find)
        self.add(self.txt_find)

        self.add(self.btn_back)
        self.add(self.btn_next)

        self.add(self.lbl_replace)
        self.add(self.txt_replace)

        self.add(self.btn_replace)
        self.add(self.btn_replace_all)

        self.add(self.chk_matchcase)

    def replace(self):
        """ Replaces current match. Out current match is always
            self.matches[0] because we rotate all matches in self.matches."""

        start, end = self.matches[0]
        self.buffer.replace_pattern(self.txt_find.get_text(),
            self.txt_replace.get_text(), start, end, self.chk_matchcase,
                replace_all=False)
        # When we replaced pattern somewhere, jump to next occurence of
        # pattern
        self.hilight_search(self.txt_find.get_text())

    def replace_all(self):
        self.buffer.replace_pattern(self.txt_find.get_text(),
            self.txt_replace.get_text(), start=None, end=None,
                match_case=self.chk_matchcase, replace_all=True)

    def _on_key_press(self, widget, event, data=None):
        if gtk.gdk.keyval_name(event.keyval) == 'Return':
            if widget == self.txt_find:
                # <Return> in txt_find
                self.next()
            elif widget == self.txt_replace:
                # <Return> in txt_replace
                self.replace()

    def _on_replace_click(self, widget, data=None):
        self.replace()

    def _on_replace_all_click(self, widget, data=None):
        self.replace_all()

    def _on_toggle_match_case(self, widget):
        # Search again if match_case changed
        self.hilight_search(self.txt_find.get_text())


class ScribberFadeHBox(gtk.Fixed):
    def __init__(self):
        gtk.Fixed.__init__(self)
        self.connect('size-allocate', self.on_size_allocate)
        self.header_offset = 0
        self.footer_offset = 0

        self.main = None
        self.header = None
        self.footer = None

        self.fading_out = False
        self.fading_in = False

    def add_header(self, widget):
        self.header = widget
        self.add(self.header)

    def add_footer(self, widget):
        self.footer = widget
        self.add(self.footer)

    def add_main(self, widget):
        self.main = widget
        self.add(self.main)

    def on_size_allocate(self, widget, event, data=None):
        fixed_x, fixed_y, fixed_width, fixed_height = self.get_allocation()

        header_x, header_y, header_width, header_height = \
            self.header.get_allocation()

        footer_x, footer_y, footer_width, footer_height = \
            self.footer.get_allocation()

        self.main.size_allocate((0, header_height - self.header_offset,
            fixed_width, fixed_height - header_height - footer_height +
            self.header_offset + self.footer_offset))

        if self.header.get_visible():
            self.header.size_allocate((0, 0 - self.header_offset, fixed_width,
                header_height))

        if self.footer.get_visible():
            self.footer.size_allocate((0, fixed_height - footer_height +
                self.footer_offset, fixed_width, footer_height))

    def fadeout(self):
        # Make sure we only call this once
        if self.header.get_visible() and not self.fading_in:
            gobject.timeout_add(5, self._fadeout)

    def fadein(self):
        # Make sure we only call this once
        if not self.header.get_visible() and not self.fading_out:
            self.header.show()
            self.footer.show()
            gobject.timeout_add(5, self._fadein)

    def _fadeout(self):
        mod_mb = False
        mod_sb = False

        self.fading_out = True

        header_x, header_y, header_width, header_height = \
            self.header.get_allocation()
        footer_x, footer_y, footer_width, footer_height = \
            self.footer.get_allocation()
        if header_height > self.header_offset:
            self.header_offset += 1
            mod_mb = True

        if footer_height > self.footer_offset:
            self.footer_offset += 1
            mod_sb = True

        self.on_size_allocate(None, None, None)

        if not mod_sb and not mod_mb:
            # We havent moved header nor footer -> fading finished
            self.fading_out = False
            self.header.hide()
            self.footer.hide()

        return mod_mb or mod_sb

    def _fadein(self):
        mod_mb = False
        mod_sb = False

        self.fading_in = True

        header_x, header_y, header_width, header_height = \
            self.header.get_allocation()
        footer_x, footer_y, footer_width, footer_height = \
            self.footer.get_allocation()

        if self.header_offset > 0:
            self.header_offset -= 1
            mod_mb = True

        if self.footer_offset > 0:
            self.footer_offset -= 1
            mod_sb = True

        self.on_size_allocate(None, None, None)

        if not mod_sb and not mod_mb:
            # We havent moved header nor footer -> fading finished
            self.fading_in = False

        return mod_mb or mod_sb
