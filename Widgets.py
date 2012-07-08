#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Custom widgets used in Scribber.
    * ScribberTextView is a gtk.TextView with some basic formatting and
      mechanisms to focus the current sentence

    * ScribberTextBuffer is the underlying gtk.TextBuffer. It has automatic
      Markdown-Syntax-Hilighting and features simple hilighting for search and
      replace

    * ScribberFindBox is a simple gtk.HBox containing the usual widgets
      used in a Find-Windget

    * ScribberFindReplaceBox is the same as ScribberFindBox for find/replace

    * ScribberFadeHBox is a gtk.HBox that can hold 3 Widgets. A top-bar, and
      widget and a bottom-bar. The top and bottom bar can, give their space to
      the main widget with a nice sliding animation
"""

import collections
import gobject
import gtk
import pango
import pygtk
pygtk.require('2.0')
import re

from MarkdownSyntaxHL import MarkdownSyntaxHL


class ScribberTextView(gtk.TextView):
    def __init__(self, parent_window):
        gtk.TextView.__init__(self)

        self.focus = True

        self.parent_window = parent_window

        self.edit_region_width = 794

        self.connect_after('key-press-event', self._on_key_pressed)
        self.connect('key-release-event', self._on_key_released)
        self.connect_after('button-press-event', self._on_click_event)
        self.connect('button-release-event', self._on_click_event)
        self.connect('move-cursor', self._on_move_cursor)
        self.connect('size-allocate', self._on_size_allocate)

        self.set_accepts_tab(True)

        self.image_window = gtk.Window(gtk.WINDOW_POPUP)
        self.image_image = gtk.Image()
        self.image_window.set_decorated(False)
        self.image_window.set_default_size(200, 200)
        self.image_window.add(self.image_image)

        font = pango.FontDescription("Deja Vu Sans 11")
        self.modify_font(font)

        self.set_justification(gtk.JUSTIFY_FILL)

        #self.set_indent(20)

        # Wrap mode
        #self.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.set_wrap_mode(gtk.WRAP_WORD)

        # Paragraph spacing
        self.set_pixels_above_lines(3)
        self.set_pixels_below_lines(3)

        # Line spacing
        self.set_pixels_inside_wrap(6)

    def open_file(self, filename):
        try:
            with open(filename, 'r') as fileo:
                data = fileo.read()

            self.get_buffer().set_text(data)

            # TODO Memorize cursor position from last time editing this file
            self.get_buffer().place_cursor(self.get_buffer().get_start_iter())
            self.focus_current_sentence()
            self.get_buffer().set_modified(False)
        except IOError:
            raise

    def toggle_focus_mode(self):
        if self.focus:
            self.focus = False
            self.get_buffer().stop_focus()
        else:
            self.focus = True
            self.focus_current_sentence()

    def focus_current_sentence(self):
        """ Highlights the current sentence and scroll it to the middle of
            the gtkTextView. """
        if self.focus:
            self.get_buffer().focus_current_sentence()

            # TODO The scrolling is really obtrusive because it is so hard,
            # this can only work, if the scrolling was smooth.

            # Scroll cursor to middle of TextView
            #self.scroll_to_mark(self.get_buffer().get_insert(), 0.0, True,
            #    0.0, 0.5)

    def _on_key_pressed(self, widget, event, data=None):
        keyname = gtk.gdk.keyval_name(event.keyval)
        state = event.state

        #cursor = self.get_buffer().get_cursor_iter()
        #print cursor.get_line()

        #(start, end) = self.get_buffer().get_selection_bounds()
        #print (start.get_text(end))

        if state == gtk.gdk.CONTROL_MASK:  # CTRL
            if keyname == 'd':
                self.delete_current_line()
        elif state == gtk.gdk.MOD1_MASK:  # Alt
            if keyname == 'Up':
                self.move_line_up()
            elif keyname == 'Down':
                self.move_line_down()

        self.focus_current_sentence()
        self.toggle_image_window()

    def _on_key_released(self, widget, event, data=None):
        self.focus_current_sentence()
        self.toggle_image_window()

    def _on_move_cursor(self, widget, step_size, count, extend_selection,
                        data=None):
        self.focus_current_sentence()
        self.toggle_image_window()

    def _on_click_event(self, widget, event, data=None):
        self.focus_current_sentence()
        self.toggle_image_window()

    def _on_size_allocate(self, widget, event, data=None):
        """ Called when widget gets resized. This modifies the left/right
        margin so that we have a fixed line width. """

        x, y, width, height = self.get_allocation()
        if width > self.edit_region_width:
            margin = (width - self.edit_region_width) / 2
            self.set_left_margin(margin)
            self.set_right_margin(margin)

    def toggle_image_window(self):
        """ Checks if current cursor position is an image. If so, it displays a
        preview of that image."""

        tag_image = self.get_buffer().tags['image']
        #pattern_image = MarkdownSyntaxHL.PATTERNS['image']
        cursor = self.get_buffer().get_cursor_iter()
        if cursor.has_tag(tag_image):
            # Parse the filename
            start = cursor.copy()
            if not cursor.begins_tag(tag_image):
                start.backward_to_tag_toggle(tag_image)

            end = cursor.copy()
            if not cursor.ends_tag(tag_image):
                end.forward_to_tag_toggle(tag_image)

            image_pattern = start.get_text(end)
            print image_pattern

            self.show_image_window('system-search.png')
        else:
            self.image_window.hide()

    def show_image_window(self, image):
        """ Determines the current cursor position on the screen (x,y) and
        displays the image preview."""

        if not self.image_window.get_visible():
            buffer = self.get_buffer()
            self.image_image.set_from_file(image)

            window_x, window_y = self.parent_window.get_position()
            self_x, self_y, self_width, self_height = self.get_allocation()
            cursor = buffer.get_cursor_iter()
            x, y, width, height = self.get_iter_location(cursor)
            x, y = self.buffer_to_window_coords(gtk.TEXT_WINDOW_WIDGET, x, y)
            self.image_window.move(x + width + window_x + self_x,
                                   y + height + window_y + self_y)
            self.image_window.show_all()

    def move_line_up(self):
        # delete and buffer current line
        text = self.delete_current_line()

        buffer = self.get_buffer()
        cursor = buffer.get_cursor_iter()
        # insert deletet text again
        self.backward_display_line(cursor)
        self.backward_display_line(cursor)
        buffer.insert(cursor, '\n' + text)

        # and select the isertet text
        buffer.select_range(*self._get_line_iters(cursor))

    def move_line_down(self):
        # delete and buffer current line
        text = self.delete_current_line()

        buffer = self.get_buffer()
        cursor = buffer.get_cursor_iter()
        # insert deletet text again
        self.forward_display_line(cursor)
        buffer.insert(cursor, text + '\n')

        # and select the isertet text
        self.backward_display_line(cursor)
        buffer.select_range(*self._get_line_iters(cursor))

    def delete_current_line(self):
        buffer = self.get_buffer()
        start, end = self._get_line_iters()

        # Save deleted text
        text = buffer.get_text(start, end)
        buffer.delete(start, end)

        cursor = buffer.get_cursor_iter()
        # delete the empty line
        buffer.backspace(cursor, False, True)
        cursor.forward_line()
        buffer.place_cursor(cursor)
        return text

    def _get_line_iters(self, iter=None):
        """ Returns two iters, pointing at the start and the end of a
        visual line.

        Keyword arguments:
        iter -- the iter of the line (if none is given, use the current line
        """
        if iter is None:
            buffer = self.get_buffer()
            start = buffer.get_cursor_iter()
        else:
            start = iter.copy()

        end = start.copy()

        self.backward_display_line_start(start)
        self.forward_display_line_end(end)
        return (start, end)


class ScribberTextBuffer(gtk.TextBuffer):
    def __init__(self):
        gtk.TextBuffer.__init__(self)
        self.tags = {}
        self.tags['blurr_out'] = self.create_tag("blurr_out",
                                                 foreground="#c0c0c0")
        self.tags['match'] = self.create_tag('match', background='#FFFF00')

        self.syntax_hl = MarkdownSyntaxHL(self)

    def get_cursor_iter(self):
        return self.get_iter_at_mark(self.get_insert())

    def _find_all_matches(self, pattern, start=None, end=None):
        """ Returns a deque containg a tuple (start_iter, end_iter) for all
            matches of 'pattern'. In order of there occurence starting from
            current cursor position.

            Keyword arguments:
            pattern -- the pattern to match
            start -- a TextIter where to start the search. If None start at
                     buffer start
            end --  a TextIter where to end the search. If None end at buffer
                    end
        """
        #TODO: When I search for 'foo bar baz' it should also match
        # 'foo *bar* baz'

        matches = collections.deque()

        if not start:
            # No start given -> use buffer start
            search_start = self.get_iter_at_mark(self.get_insert())
        else:
            search_start = start

        if not end:
            # No end given -> use buffer end
            search_end = self.get_end_iter()
        else:
            search_end = end

        text = search_start.get_text(search_end)

        for match in pattern.finditer(text):
            mstart = search_start.copy()
            mend = search_start.copy()

            mstart.forward_chars(match.start())
            mend.forward_chars(match.end())

            matches.append((mstart, mend))

        # Now match from start to current cursor
        if not start and not end:
            matches_from_start = self._find_all_matches(pattern,
                                                        self.get_start_iter(),
                                                        start)

            matches.extend(matches_from_start)
        return matches

    def replace_pattern(self, pattern, repl, start=None, end=None,
                        replace_all=False):

        if not start:
            start = self.get_start_iter()

        if not end:
            end = self.get_end_iter()

        text = start.get_text(end)

        if replace_all:
            text = re.sub(pattern, repl, text)
            self.set_text(text)
        else:
            text = re.sub(pattern, repl, text, 1)
            self.delete_selection(True, True)
            self.insert_at_cursor(text)

    def hilight_pattern(self, pattern):
        """ Hilights all matches in buffer and selects the match next to
            current cursor position. """
        self.remove_tag_by_name('match', self.get_start_iter(),
                                self.get_end_iter())

        matches = self._find_all_matches(pattern)

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

    def focus_current_sentence(self):
        """ Applys a highlighting tag to the sentence the cursor is on. """

        self._apply_tags = True

        cursor = self.get_cursor_iter()

        start = self.get_start_iter()
        end = self.get_end_iter()
        mstart = cursor.copy()
        mend = cursor.copy()

        if not cursor.starts_sentence():
            mstart.backward_sentence_start()
        if not cursor.ends_sentence():
            mend.forward_sentence_end()

        self.remove_tag_by_name("blurr_out", mstart, mend)
        self.apply_tag_by_name("blurr_out", start, mstart)
        self.apply_tag_by_name("blurr_out", mend, end)

        self._apply_tags = False

    def stop_focus(self):
        """ Removes all highlighting tags from buffer."""
        start = self.get_start_iter()
        end = self.get_end_iter()
        self.remove_tag_by_name("blurr_out", start, end)


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
        text = re.escape(text)
        if self.chk_matchcase.get_active():
            pattern = re.compile(text)
        else:
            pattern = re.compile(text, re.IGNORECASE)

        self.matches = self.buffer.hilight_pattern(pattern)

    def _on_find_type(self, widget):
        """ Called when text in txt_find changes. """
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
            self.matches[0] because we rotate all matches in self.matches.
        """

        start, end = self.matches[0]
        self.buffer.replace_pattern(self.txt_find.get_text(),
                                    self.txt_replace.get_text(), start, end,
                                    self.chk_matchcase, replace_all=False)
        # When we replaced pattern somewhere, jump to next occurence of
        # pattern
        self.hilight_search(self.txt_find.get_text())

    def replace_all(self):
        self.buffer.replace_pattern(self.txt_find.get_text(),
                                    self.txt_replace.get_text(), start=None,
                                    end=None, replace_all=True)

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
    """ This is a HBox (based on a gtk.Fixed) that holds 3 children. A header,
        a main widget and a footer. The main widget consumes all space not
        needed by the header/footer. Also it is possible to fadeout the
        header/footer with a nice animation.
    """

    UP = 1
    DOWN = -1
    FADE_DELAY = 3

    def __init__(self):
        gtk.Fixed.__init__(self)
        self.connect('size-allocate', self._on_size_allocate)

        self.fading_widgets = dict(head=None, foot=None)
        self.main = None
        self.fading = False

    def add_header(self, widget):
        # To keep track of the widgets offset
        widget.offset = 0
        self.add(widget)
        self.fading_widgets['head'] = widget

    def add_footer(self, widget):
        # To keep track of the widgets offset
        widget.offset = 0
        self.add(widget)
        self.fading_widgets['foot'] = widget

    def add_main_widget(self, widget):
        self.main = widget
        self.add(self.main)

    def _resize_children(self):
        fixed_x, fixed_y, fixed_width, fixed_height = self.get_allocation()
        head = self.fading_widgets['head']
        foot = self.fading_widgets['foot']

        head_x, head_y, head_width, head_height = head.get_allocation()
        foot_x, foot_y, foot_width, foot_height = foot.get_allocation()

        new_main_y = head_height - head.offset
        new_main_height = fixed_height - head_height - foot_height + \
            head.offset + foot.offset

        self.main.size_allocate((0, new_main_y, fixed_width, new_main_height))

        if head.get_visible():
            head.size_allocate((0, 0 - head.offset, fixed_width, head_height))

        if foot.get_visible():
            new_footer_y = fixed_height - foot_height + foot.offset
            foot.size_allocate((0, new_footer_y, fixed_width, foot_height))

    def _on_size_allocate(self, widget, event, data=None):
        self._resize_children()

    def fadeout(self):
        self._fadeout()

    def _fadeout(self):
        """ Checks if we are currently fading, if not, starts a timer
            that calls a fadeout function until the widgets are completely
            faded out.  """
        # Make sure we only call this once
        if (self.fading_widgets['head'].get_visible() and not self.fading):
            self.fading = True

            gobject.timeout_add(ScribberFadeHBox.FADE_DELAY, self._fade,
                                self.__fadeout_check_widget,
                                ScribberFadeHBox.UP)

            while gtk.events_pending():
                gtk.main_iteration_do(block=False)

            for widget in self.fading_widgets.values():
                widget.hide()

    def fadein(self):
        if not self.fading_widgets['head'].get_visible() and not self.fading:
            self.fading = True
            self._fadein()

    def _fadein(self):
        """ Checks if we are currently fading, if not, starts a timer
            that calls a fadein function until the widgets are completely
            faded in.
        """
        for widget in self.fading_widgets.values():
            widget.show()

        gobject.timeout_add(ScribberFadeHBox.FADE_DELAY, self._fade,
                            self.__fadein_check_widget,
                            ScribberFadeHBox.DOWN)

    def _fade(self, check_widget, offset):
        """ Fades the header and footer in the right direction. Returns True
            if at least one widget has been moved.

            Keyword arguments:
            check_widget -- a function checking if a widget is fully faded
                            in/out
            offset -- 1 if the widget needs to be faded "up", -1 if "down"
        """

        modified_widget = False

        for widget in self.fading_widgets.values():
            if check_widget(widget):
                widget.offset += offset
                modified_widget = True

        self._resize_children()

        if not modified_widget:
            # We havent moved head nor foot -> fading finished
            self.fading = False

        return modified_widget

    def __fadeout_check_widget(self, widget):
        """ Returns True if the widget isn't fully faded out."""
        x, y, width, height = widget.get_allocation()
        return widget.offset < height

    def __fadein_check_widget(self, widget):
        """ Returns True if the widget isn't fully faded in."""
        return widget.offset > 0
