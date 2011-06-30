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

import collections
import gobject
import gtk
import pango
import pygtk
pygtk.require('2.0')
import re


class ScribberTextView(gtk.TextView):
    def __init__(self):
        gtk.TextView.__init__(self)

        self.focus = True

        self.connect_after('key-press-event', self._on_key_event)
        self.connect('key-release-event', self._on_key_event)
        self.connect_after('button-press-event', self._on_button_event)
        self.connect('button-release-event', self._on_button_event)
        self.connect('move-cursor', self._on_move_cursor)

        font = pango.FontDescription("Deja Vu Sans Mono  11")
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

    def open_file(self, filename):
        result = True
        try:
            with open(filename, 'r') as f:
                data = f.read()

            self.get_buffer().set_text(data)

            # TODO Maybe memorize cursor position from last time editing
            # this file
            self.get_buffer().place_cursor(self.get_buffer().get_start_iter())
            self.focus_current_sentence()
            self.get_buffer().set_modified(False)
        except IOError:
            result = False

        return result

    def focus_current_sentence(self):
        if self.focus:
            self.get_buffer().focus_current_sentence()
            # Scroll cursor to middle of TextView
            self.scroll_to_mark(self.get_buffer().get_insert(), 0.0, True,
                0.0, 0.5)

    def _on_move_cursor(self, widet, step_size, count, xtnd_slctn, data=None):
        self.focus_current_sentence()

    def _on_key_event(self, widget, event, data=None):
        self.focus_current_sentence()

    def _on_button_event(self, widget, event, data=None):
        self.focus_current_sentence()


class ScribberTextBuffer(gtk.TextBuffer):
    class NoPatternFound(Exception):
        pass

    class Pattern:
        def __init__(self, tagn, start, end, length):
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

                Pattern('underlined', re.compile(r"_\w"), re.compile(r"\w_"),
                    1),
                Pattern('italic', re.compile(r"(?<!\*)(\*\w)"),
                    re.compile(r"(\w\*)(?!\*)"), 1),
                Pattern('bold', re.compile(r"\*\*\w"), re.compile(r"\w\*\*"),
                    2),
                Pattern('bolditalic', re.compile(r"\*\*\*\w"),
                    re.compile(r"\w\*\*\*"), 3)]

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
            self.remove_tag_by_name(p.tagn, start, end)

        while not finished:
            try:
                tagn, mstart, mend, length = self._get_first_pattern(start,
                    end)

                if (mstart.get_offset() + length) in used_iters or \
                    (mend.get_offset() in used_iters and not mend.equal(end)):
                    # Iterators have been used -> skip match.
                    # End-iterator can be used multiple times, though.
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
            except self.NoPatternFound:
                # No pattern found
                finished = True

    def _get_first_pattern(self, start, end):
        """ Returns (tagname, start, end, length) of the first occurence of any
            known pattern in this buffer. """
        matches = []

        for p in self.patterns:
            mstart = start.copy()

            # Match begining
            result_start = p.start.search(mstart.get_text(end))
            if result_start:
                # Forward until start of match
                mstart.forward_chars(result_start.start())

                # Match end
                result_end = p.end.search(mstart.get_text(end))
                if result_end:
                    mend = mstart.copy()
                    mend.forward_chars(result_end.end())
                else:
                    # No pattern for end found -> match until end
                    mend = self.get_end_iter()

                if mstart.equal(start):
                    # Our first match is at the start of the range we are
                    # looking at -> We wont find a match before this ->
                    # Return this match
                    #print 'Shortcut'
                    return [p.tagn, mstart, mend, p.length]

                matches.append([result_start.start(), [p.tagn, mstart,
                    mend, p.length]])

        if not matches:
            raise self.NoPatternFound('Found no matchting pattern in buffer')

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
    # TODO: When this gets shown and has a text in txt_find -> hilight that
    def __init__(self, buffer):
        gtk.HBox.__init__(self, False, 4)
        self.matches = collections.deque()
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
                # Pressed <Return> in txt_find
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
                # Pressed <Return> in txt_find
                self.next()
            elif widget == self.txt_replace:
                # Pressed <Return> in txt_replace
                self.replace()

    def _on_replace_click(self, widget, data=None):
        self.replace()

    def _on_replace_all_click(self, widget, data=None):
        self.replace_all()

    def _on_toggle_match_case(self, widget):
        # Search again if match_case changed
        self.hilight_search(self.txt_find.get_text())


class ScribberFadeHBox(gtk.Fixed):
    """ This is a VBox (based on a gtk.Fixed) that holds 3 children. A head,
        a main widget and a foot. The main widget consumes all space not
        needed by the head/foot. Also it is possible to fadeout the
        head/foot with a nice animation. """

    def __init__(self):
        gtk.Fixed.__init__(self)
        self.connect('size-allocate', self.on_size_allocate)

        self.main = None
        self.head = None
        self.foot = None

        self.fading = False

    def add_header(self, widget):
        self.head = widget
        # To keep track of the widgets offset
        self.head.offset = 0
        self.add(self.head)

    def add_footer(self, widget):
        self.foot = widget
        # To keep track of the widgets offset
        self.foot.offset = 0
        self.add(self.foot)

    def add_main_widget(self, widget):
        self.main = widget
        self.add(self.main)

    def _resize_children(self):
        fixed_x, fixed_y, fixed_width, fixed_height = self.get_allocation()

        head_x, head_y, head_width, head_height = \
            self.head.get_allocation()

        foot_x, foot_y, foot_width, foot_height = \
            self.foot.get_allocation()

        self.main.size_allocate((0, head_height - self.head.offset,
            fixed_width, fixed_height - head_height - foot_height +
            self.head.offset + self.foot.offset))

        if self.head.get_visible():
            self.head.size_allocate((0, 0 - self.head.offset, fixed_width,
                head_height))

        if self.foot.get_visible():
            self.foot.size_allocate((0, fixed_height - foot_height +
                self.foot.offset, fixed_width, foot_height))

    def on_size_allocate(self, widget, event, data=None):
        self._resize_children()

    def fadeout(self):
        # Make sure we only call this once, especially not while we are already
        # fading in/out
        if (self.head.get_visible() and not self.fading):

            self.fading = True
            gobject.timeout_add(5, self._fade, self.__fadeout_check_widget, 1)

            while self.fading:
                # While widgets are still fading out, dont let this block
                # the fading-process
                gtk.main_iteration()

            self.head.hide()
            self.foot.hide()

    def fadein(self):
        # Make sure we only call this once, especially not while we are already
        # fading in/out
        if (not self.head.get_visible() and not self.fading):
            self.fading = True
            self.head.show()
            self.foot.show()
            gobject.timeout_add(5, self._fade, self.__fadein_check_widget, -1)

    def __fadeout_check_widget(self, widget):
        """Returns True if the widget isn't fully faded out."""
        x, y, width, height = widget.get_allocation()
        return widget.offset < height

    def __fadein_check_widget(self, widget):
        """Returns True if the widget isn't fully faded in."""
        return widget.offset > 0

    def _fade(self, check_widget, offset):
        """ Fades the header and footer in the right direction. Returns True
            if at least one widget has been moved.

            Keyword arguments:
            check_widget -- a function checking if a widget is fully faded
                            in/out
            offset -- 1 if the widget needs to be faded "up", -1 if "down"
        """
        mod_head = False
        mod_foot = False

        head_x, head_y, head_width, head_height = self.head.get_allocation()
        foot_x, foot_y, foot_width, foot_height = self.foot.get_allocation()

        if check_widget(self.head):
            self.head.offset += offset
            mod_head = True

        if check_widget(self.foot):
            self.foot.offset += offset
            mod_foot = True

        self._resize_children()

        if not mod_head and not mod_foot:
            # We havent moved head nor foot -> fading finished
            self.fading = False

        return mod_head or mod_foot
