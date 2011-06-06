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

        self.connect_after('key-press-event', self._on_key_event)
        self.connect('key-release-event', self._on_key_event)
        self.connect_after('button-press-event', self._on_button_event)
        self.connect('button-release-event', self._on_button_event)
        self.connect('move-cursor', self._on_move_cursor)

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

        self._focus_current_sentence()

    def _on_move_cursor(self, widget, event, data=None, asd=None):
        self._focus_current_sentence()

    def _on_key_event(self, widget, event, data=None):
        self._focus_current_sentence()

    def _on_button_event(self, widget, event, data=None):
        self._focus_current_sentence()

    def _focus_current_sentence(self):
        # TODO: Scroll doesnt work
        sentence_start = self.get_buffer()._focus_current_sentence()
        self.scroll_to_iter(sentence_start, 0, True, 0.0, 0.0)


class ScribberTextBuffer(gtk.TextBuffer):

    patterns = [ ['heading1', re.compile('\#(?!\#) '), re.compile(''), 1],
                 ['heading2', re.compile('\#{2}(?!\#) '), re.compile(''), 1],
                 ['heading3', re.compile('\#{3}(?!\#) '), re.compile(''), 1],
                 ['heading4', re.compile('\#{4}(?!\#) '), re.compile(''), 1],
                 ['heading5', re.compile('\#{5}(?!\#) '), re.compile(''), 1],
                 ['heading6', re.compile('\#{6} '), re.compile(''), 1],
                 ['table_default', re.compile('\* '), re.compile(''), 1],
                 ['table_sorted', re.compile('\d+\. '), re.compile(''), 1],
                 ['italic', re.compile('(?<!\*)(\*\w)'),
                   re.compile('(\w\*)(?!\*)'), 1],
                 ['bold', re.compile('\*\*\w'), re.compile('\w\*\*'), 2] ]

    def __init__(self):
        gtk.TextBuffer.__init__(self)

        self.set_text("""
# Ab geht die Post
Lorem ipsum dolor sit amet, \
elit. Ut sit amet diam mauris. Fusce ac erat, ut ultrices ligula. \
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilisi. Morbi dignissim ultrices velit, posuere accumsan \
leo vehicula eget. Mauris at urna eget arcu vulputate feugiat nec id nunc. \
Nullam in faucibus ipsum. Maecenas rhoncus massa eu libero vestibulum \
sollicitudin. Morbi tempus sapien id magna molestie ut sodales lectus \
fringilla. In a quam nibh. Nullam vulputate nunc at velit ultricies at \
feugiat erat dignissim. Aliquam *tempus*, quam non suscipit varius, ligula quam \
elementum orci, vitae euismod lectus nulla non mauris. Proin rutrum massa \
feugiat sem scelerisque imperdiet laoreet vulputate. Quisque ullamcorper\
 justo et velit dapibus **vulputate** pharetra lorem lobortis. Phasellus eget \
tellus sed odio facilisis euismod. Mauris a elit libero.

* Numero One
* Zwei
* Drei

Nam elit. Ut sit amet diam mauris. Fusce ac erat, ut ultrices ligula. \
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilisi. Morbi *dignissim ultrices velit*, posuere accumsan \
leo vehicula eget. Mauris at urna eget arcu vulputate feugiat nec id nunc. \
Nullam in faucibus ipsum. Maecenas rhoncus massa eu libero vestibulum \
sollicitudin. Morbi tempus sapien id magna molestie ut sodales lectus \
fringilla. In a quam nibh. Nullam vulputate nunc at velit ultricies at \
feugiat erat dignissim. Aliquam tempus, quam non suscipit varius, ligula quam \
elementum orci, vitae *euismod lectus nulla non mauris. Proin rutrum massa \
feugiat sem scelerisque **imperdiet** laoreet vulputate. Quisque ullamcorper\
 justo et velit dapibus vulputate pharetra lorem lobortis. Phasellus eget \
tellus sed odio facilisis* euismod. Mauris a elit libero, a gravida ligula. Nam\
elit.

# Ich bin total aufgeregt
Ut sit amet diam mauris. Fusce ac erat \
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilisi. Morbi dignissim ultrices velit, posuere accumsan \
leo vehicula eget. Mauris at urna eget arcu vulputate feugiat nec id nunc. \
Nullam in faucibus ipsum. Maecenas rhoncus massa eu libero vestibulum.
## Level 2
### Level 3 
sollicitudin. Morbi tempus sapien id magna molestie ut sodales lectus \
fringilla. In a quam nibh. Nullam vulputate nunc at velit ultricies at \
feugiat erat dignissim. Aliquam tempus, quam non suscipit varius, ligula quam \
elementum orci, vitae euismod lectus nulla non mauris. Proin rutrum massa
### WHAAAAAT?
feugiat sem scelerisque imperdiet laoreet vulputate. Quisque ullamcorper\
 justo et velit dapibus vulputate pharetra lorem lobortis. Phasellus eget \
tellus sed odio facilisis euismod. Mauris a elit libero, a gravida ligula. Nam\
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilisi. Morbi dignissim ultrices velit, posuere accumsan \
leo vehicula eget. Mauris at urna eget arcu vulputate feugiat nec id nunc. \
Nullam in faucibus ipsum. Maecenas rhoncus massa eu libero vestibulum \
sollicitudin. Morbi tempus sapien id magna molestie ut sodales lectus \
fringilla. In a quam nibh. Nullam vulputate nunc at velit ultricies at \
feugiat erat dignissim. Aliquam tempus, quam non suscipit varius, ligula quam \
elementum orci, vitae euismod lectus nulla non mauris. Proin rutrum massa \
feugiat sem scelerisque imperdiet laoreet vulputate. Quisque ullamcorper\
 justo et velit dapibus vulputate pharetra lorem lobortis. Phasellus eget \
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilisi. Morbi dignissim ultrices velit, posuere accumsan \
leo vehicula eget. Mauris at urna eget arcu vulputate feugiat nec id nunc. \
 vel nisi eget tortor sodales dictum.""")

        self.focus = True

        self.connect_after("insert-text", self._on_insert_text)
        self.connect_after("delete-range", self._on_delete_range)
        self.connect('apply-tag', self._on_apply_tag)
        

        self.tag_default = self.create_tag("default", foreground="#888888")

        self.tag_focus = self.create_tag("focus", foreground="#000000")

        self.tag_heading1 = self.create_tag("heading1", weight=pango.WEIGHT_BOLD,
            left_margin=30)
        self.tag_heading2 = self.create_tag("heading2", weight=pango.WEIGHT_BOLD,
            left_margin=40)
        self.tag_heading3 = self.create_tag("heading3", weight=pango.WEIGHT_BOLD,
            left_margin=50)
        self.tag_heading4 = self.create_tag("heading4", weight=pango.WEIGHT_BOLD,
            left_margin=60)
        self.tag_heading5 = self.create_tag("heading5", weight=pango.WEIGHT_BOLD,
            left_margin=70)
        self.tag_heading6 = self.create_tag("heading6", weight=pango.WEIGHT_BOLD,
            left_margin=80)

        self.tag_table_default = self.create_tag("table_default", left_margin=110)
        self.tag_table_sorted = self.create_tag("table_sorted", left_margin=110)

        self.tag_bold = self.create_tag("bold", weight=pango.WEIGHT_BOLD)
        self.tag_italic = self.create_tag("italic", style=pango.STYLE_ITALIC)
        self.tag_bolditalic = self.create_tag("bolditalic",
            weight=pango.WEIGHT_BOLD, style=pango.STYLE_ITALIC)


        self._apply_tags = True
        self._update_markdown(self.get_start_iter())
        self._apply_tags = False

    def _on_apply_tag(self, buf, tag, start, end):
        # FIXME This is a hack! It allows apply-tag only while
        #       _on_insert_text() and _on_delete_range()
        if not self._apply_tags:
            self.emit_stop_by_name('apply-tag')
            return True

    def _on_insert_text(self, buf, iter, text, length):
        if iter.has_tag(self.tag_table_default) and text == "\n":
            self.insert_at_cursor("* ")
        if iter.has_tag(self.tag_table_sorted) and text == "\n":
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

        if end is None: end = self.get_end_iter()

        finished = False

        # Only remove markdown tags (no focus tags)
        for p in self.patterns:
            self.remove_tag_by_name(p[0], start, end) 

        while not finished:
            tagn, mstart, mend, length = self._get_first_pattern(start, end)

            if tagn:
                # Found a pattern
                # TODO: +1 universal?
                if mstart.get_offset() + 1 in used_iters or \
                    (mend.get_offset() in used_iters and not mend.equal(end)):
                    start = mstart
                    start.forward_chars(length)
                    continue

                #print "************** Apply tag ", tagn, "to: ",mstart.get_text(mend)
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
        """ Returns (tagname, start, end) of the first occurence of any
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

                if pattern_tagn.startswith('heading') or pattern_tagn == 'table_default':
                    # No need to search here. Just match 'til end
                    mend = mstart.copy()
                    mend.forward_line()
                    matches.append([result_start.start(), [pattern_tagn, mstart,
                    mend, pattern[3]]])
                    continue


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

        if len(matches) == 0: return (None, None, None, None)
        return min(matches)[1]


    def _focus_current_sentence(self):
        """ Applys a highlighting tag to the sentence the cursor is on """

        self._apply_tags = True

        if self.focus:# and not self.get_has_selection():
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
                    if not starts_sentence: mstart.backward_sentence_start()
                    if not ends_sentence: mend.forward_sentence_end()

                self.apply_tag_by_name("default", start, end)
                self.apply_tag_by_name("focus", mstart, mend)

            self._apply_tags = False
            return mstart


if __name__ == '__main__':
    ScribberView()
