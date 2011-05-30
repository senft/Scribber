#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# TODO: Spellcheck when exporting (?) gtkspell

import sys
import pygtk
pygtk.require('2.0')
import gtk
import pango
#import gtkspell


DEBUG_FLAG = True


def _log_debug(msg):
    if not DEBUG_FLAG:
        return
    sys.stderr.write("DEBUG: ")
    sys.stderr.write(msg)
    sys.stderr.write("\n")


def _log_warn(msg):
    sys.stderr.write("WARN: ")
    sys.stderr.write(msg)
    sys.stderr.write("\n")


def _log_error(msg):
    sys.stderr.write("ERROR: ")
    sys.stderr.write(msg)
    sys.stderr.write("\n")


class ScribberView(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        gtk.rc_parse(".gtkrc")

        self.is_fullscreen = False

        self.set_title("Scribber")
        self.set_border_width(2)
        #self.set_decorated(False)
        self.resize(300, 100)

        # Callbacks
        self.connect("delete_event", self.delete_event)
        self.connect("destroy", self.destroy)
        self.connect("window-state-event", self.on_window_state_event)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        vbox = gtk.VBox(False, 0)
        self.add(vbox)

        # TextView
        self.view = ScribberTextView()
        vbox.pack_start(scrolled_window, True, True, 2)

        scrolled_window.add_with_viewport(self.view)

        #check = gtkspell.Spell(view)
        #check.set_language("de_DE")

        # Statusbar
        self.sbarbox = gtk.HBox(False, 0)

        self.button_focus = gtk.ToggleButton("Focus")
        self.button_focus.set_image(
            gtk.image_new_from_file("system-search.png"))
        self.button_focus.set_active(True)
        self.button_focus.connect("clicked", self.on_focus_click)
        self.button_fullscreen = gtk.ToggleButton("Fullscreen")
        self.button_fullscreen.set_image(
            gtk.image_new_from_file("view-fullscreen.png"))
        self.button_fullscreen.connect("clicked", self.on_fullscreen_click)

        sbar_wc = gtk.Statusbar()
        context_id = sbar_wc.get_context_id("main_window")

        sbar_wc.push(context_id, "wc")

        self.sbarbox.pack_start(self.button_focus, False, False, 2)
        self.sbarbox.pack_start(self.button_fullscreen, False, False, 2)
        self.sbarbox.pack_end(sbar_wc, True, True, 2)

        vbox.pack_end(self.sbarbox, False, False, 2)

        # Go!
        self.show_all()
        gtk.main()

    def on_fullscreen_click(self, widget, data=None):
        if self.is_fullscreen:
            self.unfullscreen()
            self.is_fullscreen = False
        else:
            self.fullscreen()
            self.is_fullscreen = True

    def on_focus_click(self, widget, data=None):
        self.view.get_buffer().focus = self.view.get_buffer().focus

    def on_window_state_event(self, event, data=None):
        if data.new_window_state == gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.button_fullscreen.set_active(True)
            self.is_fullscreen = True
            # TODO: Delete hide and show.. should be disposed seconds after
            # typing
            self.sbarbox.hide()
        else:
            self.button_fullscreen.set_active(False)
            self.is_fullscreen = False
            self.sbarbox.show()

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()


class ScribberTextView(gtk.TextView):
    def __init__(self):
        gtk.TextView.__init__(self)

        self.set_buffer(ScribberTextBuffer())

        # TODO: Catch all relevant events:
        # TODO: Event missing: When selecting text, and deselecting it again,
        # by clicking somehere in the text, the FocusMode doesnt hilight the
        # right sentence
        self.connect('key-press-event', self.on_key_event)
        self.connect('key-release-event', self.on_key_event)
        self.connect('button-press-event', self.on_button_event)
        self.connect('button-release-event', self.on_button_event)

        # http://www.tortall.net/mu/wiki/PyGTKCairoTutorial
        font = pango.FontDescription("envy code r 12")
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

    def on_key_event(self, widget, event, data=None):
        self.get_buffer().hilight_sentence()

    def on_button_event(self, widget, event, data=None):
        self.get_buffer().hilight_sentence()


class ScribberTextBuffer(gtk.TextBuffer):
    def __init__(self):
        gtk.TextBuffer.__init__(self)

        self.focus = True

        self.connect('changed', self.on_change)

        # Tags: http://www.bravegnu.org/gtktext/x113.html
        self.create_tag("default", foreground="#999999", left_margin=80,
            right_margin=80)

        self.tag_heading = self.create_tag("heading", weight=pango.WEIGHT_BOLD,
            left_margin=50, pixels_above_lines=15, pixels_below_lines=10)

        self.create_tag("mytable", left_margin=110, pixels_above_lines=20,
            pixels_below_lines=20)

        self.create_tag("bold", weight=pango.WEIGHT_BOLD,
            style=pango.STYLE_NORMAL)
        self.create_tag("italic", style=pango.STYLE_ITALIC)

        self.hilight_sentence()

    def on_change(self, buffer):
        self.markdown()

    def hilight_sentence(self):
        if self.focus:
            # TODO: get_start_iter().has_tag("table") -> hilight whole table
            start = self.get_start_iter()
            end = self.get_end_iter()

            sentence_start = self.get_iter_at_mark(self.get_insert())
            sentence_start.backward_sentence_start()

            sentence_end = self.get_iter_at_mark(self.get_insert())
            sentence_end.forward_sentence_end()

            # Set normal style for whole text
            self.apply_tag_by_name("default", start, end)

            # Remove from currently hilighted sentence
            self.remove_tag_by_name("default", sentence_start, sentence_end)

    def markdown(self):
        self.markdown_heading()
        self.markdown_emphasis('*', 'italic')
        self.markdown_emphasis('**', 'bold')

    def markdown_emphasis(self, needle, tag):
        start = self.get_start_iter()
        try:
            (start, end) = start.forward_search(needle,
                gtk.TEXT_SEARCH_VISIBLE_ONLY, None)

            if end.get_char() == " ":
                print 'DONT'

#            while(end.get_char() == " "):
#                (start, end) = start.forward_search(needle,
#                    gtk.TEXT_SEARCH_VISIBLE_ONLY, None)
        except:
            start = None

        while start is not None:
            eol = end.copy()
            try:
                # Find end of iter that marks the second occurence of needle
                eol = eol.forward_search(needle, 0, None)[1]
            except:
                eol = self.get_end_iter()

            self.apply_tag_by_name(tag, start, eol)

            eol.forward_char()
            try:
                (start, end) = eol.forward_search(needle,
                    gtk.TEXT_SEARCH_VISIBLE_ONLY, None)
            except:
                start = None

    def markdown_heading(self):
        start = self.get_start_iter()
        try:
            (start, end) = start.forward_search('#',
            gtk.TEXT_SEARCH_VISIBLE_ONLY, None)
        except:
            start = None

        while(start != None):
            eol = start.copy()
            eol.forward_line()

            if not start.begins_tag(self.tag_heading) \
            or not eol.ends_tag(self.tag_heading):
            # TODO: Bug! when inserting a line between 2 Heading-lines, the new
            # line is a heading, too
                self.apply_tag_by_name("heading", start, eol)

            try:
                (start, end) = end.forward_search('#',
                gtk.TEXT_SEARCH_VISIBLE_ONLY, None)
            except:
                start = None

if __name__ == '__main__':
    ScribberView()
