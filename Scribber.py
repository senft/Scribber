#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""

    Scribber, a text editor that focuses on minimalism

    Icons provided by the Tango Desktop Project (http://tango.freedesktop.org/)

"""

# TODO: Spellcheck when exporting (?) gtkspell

import pygtk
pygtk.require('2.0')
import gtk
import pango
import re


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

        # Buttons
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

    def on_focus_click(self, widget, data=None):
        self.view.get_buffer().focus = self.view.get_buffer().focus

    def on_fullscreen_click(self, widget, data=None):
        if self.is_fullscreen:
            self.unfullscreen()
            # Gtk doesnt provied a way to check a windows state, so we have to
            # keep track ourselves
            self.is_fullscreen = False
        else:
            self.fullscreen()
            self.is_fullscreen = True

    def on_window_state_event(self, event, data=None):
        if data.new_window_state == gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.button_fullscreen.set_active(True)
            self.is_fullscreen = True
        else:
            self.button_fullscreen.set_active(False)
            self.is_fullscreen = False

    def delete_event(self, widget, event, data=None):
        # Really quit?
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()


class ScribberTextView(gtk.TextView):
    def __init__(self):
        gtk.TextView.__init__(self)

        self.set_buffer(ScribberTextBuffer())

        self.connect_after('key-press-event', self.on_key_event)
        self.connect('key-release-event', self.on_key_event)
        self.connect_after('button-press-event', self.on_button_event)
        self.connect('button-release-event', self.on_button_event)
        self.connect('move-cursor', self.on_move_cursor)

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

    def on_move_cursor(self, widget, event, data=None, asd=None):
        # TODO: argument names
        #self.get_buffer()._focus_sentence()
        pass

    def on_key_event(self, widget, event, data=None):
        #self.get_buffer()._focus_sentence()
        pass

    def on_button_event(self, widget, event, data=None):
        #self.get_buffer()._focus_sentence()
        pass


class ScribberTextBuffer(gtk.TextBuffer):
    def __init__(self):
        gtk.TextBuffer.__init__(self)

        self.set_text("""Lorem ipsum dolor sit amet, consectetur adipiscing \
elit. Ut sit amet diam mauris. Fusce ac erat justo, ut ultrices ligula. \
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilisi. Morbi dignissim ultrices velit, posuere accumsan \
leo vehicula eget. Mauris at urna eget arcu vulputate feugiat nec id nunc. \
Nullam in faucibus ipsum. Maecenas rhoncus massa eu libero vestibulum \
sollicitudin. Morbi tempus sapien id magna molestie ut sodales lectus \
fringilla. In a quam nibh. Nullam vulputate nunc at velit ultricies at \
feugiat erat dignissim. Aliquam tempus, quam non suscipit varius, ligula quam \
elementum orci, vitae euismod lectus nulla non mauris. Proin rutrum massa \
feugiat sem scelerisque imperdiet laoreet justo vulputate. Quisque ullamcorper\
 justo et velit dapibus vulputate pharetra lorem lobortis. Phasellus eget \
tellus sed odio facilisis euismod. Mauris a elit libero, a gravida ligula. Nam\
 vel nisi eget tortor sodales dictum.""")

        self.focus = True

        self.connect_after("insert-text", self._on_insert_text)
        self.connect_after("delete-range", self._on_delete_range)

        # Tags: http://www.bravegnu.org/gtktext/x113.html
        self.tag_default = self.create_tag("default", foreground="#999999")

        self.tag_focus = self.create_tag("focus", foreground="#000000")

        self.tag_heading = self.create_tag("heading", weight=pango.WEIGHT_BOLD,
            left_margin=50, pixels_above_lines=15, pixels_below_lines=10)

        self.tag_mytable = self.create_tag("mytable", left_margin=110,
            pixels_above_lines=20, pixels_below_lines=20)

        self.tag_bold = self.create_tag("bold", weight=pango.WEIGHT_BOLD)
        self.tag_italic = self.create_tag("italic", style=pango.STYLE_ITALIC)
        self.tag_bolditalic = self.create_tag("bolditalic",
            weight=pango.WEIGHT_BOLD, style=pango.STYLE_ITALIC)

    def _on_insert_text(self, buf, iter, text, length):
        iter.backward_chars(length)
        if not iter.begins_tag():
            iter.backward_to_tag_toggle(None)

        # Maybe we just found the beginning of a "hilight-tag"
        # TODO: Check in a loop for all tags
        if not (iter.begins_tag(self.tag_bold) or
            iter.begins_tag(self.tag_italic)):

            iter.backward_to_tag_toggle(None)

        self._update_markdown(iter)

    def _on_delete_range(self, buf, start, end):
        pass

    patterns = [ ["heading", re.compile("\#"), re.compile("$")],
                 ["italic", re.compile("(?<!\*)(\*\w)"),
                    re.compile("(\w\*)(?!\*)")],
                 ["bold", re.compile("\*\*\w"), re.compile("\w\*\*")] ]

    def _update_markdown(self, start, end=None):
        # Used to save which iters we already used as start or end of a pattern
        used_iters = {}

        if end is None: end = self.get_end_iter()

        finished = False
        while not finished:
            
            tag, mstart, mend = self._get_first_pattern(start, end)

            print "\n---------------------------------------------------------"
            print "Searching in: ", start.get_text(end)

            if not tag:
                # Found no pattern
                finished = True
                continue
            else:
                # Found a pattern
                if mstart.get_offset() in used_iters:
                    # Iter already was used as a end-iter -> skip it
                    start = mstart
                    start.forward_char()
                    continue
                if mend.get_offset() in used_iters:
                    start = mend
                    start.forward_char()
                    continue

                print "Found pattern: ", start.get_text(end)
                # Instead of self.remove_all_tags(start, end) only remove
                # tags that dont alter color (only markdown tags)
                for p in self.patterns:
                    #TODO: Really from start to end?
                    # This is wrong!
                    self.remove_tag_by_name(p[0], start, end) 

                print "Apply tag to: ", mstart.get_text(mend)
                self.apply_tag_by_name(tag, mstart, mend)
                used_iters[mstart.get_offset()] = mstart.get_char()
                used_iters[mend.get_offset()] = mend.get_char()

            #start = mstart
            #start.forward_char()
            start = mend

            if start == end:
                finished = True

    def _get_first_pattern(self, start, end):
        """ Returns (tagname, start, end) of the first occurence of any
            known pattern in this buffer. """
        # TODO: Refactor, plx

        list = []

        for pattern in self.patterns:
            mstart = start.copy()

            # Match begining
            result_start = pattern[1].search(mstart.get_text(end))
            if result_start:
                #print "Matched: ", result_start.groups()
                # Skip the already matched start
                mstart.forward_chars(result_start.start())

                # Match end
                result_end = pattern[2].search(mstart.get_text(end))
                if result_end:
                    #print "Matched: ", result_end.groups()
                    mend = mstart.copy()
                    mend.forward_chars(result_end.end()-1)
                else:
                    mend = self.get_end_iter()

                list.append([result_start.start(), [pattern[0], mstart, mend]])

        #print list
        if len(list) == 0: return (None, None, None)

        pattern = list[0]
        for p in list:
            if p[0] < pattern[0]:
                pattern = p

        #print "return: ", pattern[1]
        return pattern[1]


    def _focus_sentence(self):
        """ Applys a highlighting tag to the sentence the cursor is in """
        if self.focus:# and not self.get_has_selection():
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

if __name__ == '__main__':
    ScribberView()
