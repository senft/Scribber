#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Scribber, a text editor that focuses on minimalism.

Icons provided by the Tango Desktop Project (http://tango.freedesktop.org/)
"""

import pygtk
pygtk.require('2.0')
import gtk
import os
import pango
import re
import ReSTExporter


class ScribberView(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        gtk.rc_parse(".gtkrc")

        self.view = ScribberTextView()
        self.is_fullscreen = False
        self.filename = None
        self.exporter = ReSTExporter.ReSTExporter(self.view.get_buffer())

        self.set_title("Scribber")
        self.set_border_width(2)
        #self.set_decorated(False)
        self.resize(300, 100)

        # Callbacks
        self.connect("delete_event", self._delete_event)
        self.connect("destroy", self.destroy)
        self.connect("window-state-event", self._on_window_state_event)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.view)

        vbox = gtk.VBox(False, 2)

        self.menu_bar = self.create_menu_bar()
        vbox.pack_start(self.menu_bar, False, False, 0)
        vbox.pack_start(scrolled_window, True, True, 0)

        #check = gtkspell.Spell(view)
        #check.set_language("de_DE")

        self.status_bar = self.create_status_bar()
        vbox.pack_end(self.status_bar, False, False, 0)

        self.add(vbox)
        # Go!
        self.show_all()
        gtk.main()

    def _fadeout_widget(self, widget, time=10):
        a = widget.get_snapshot()
        print dir(a)
        # copy the current widget style
        style = widget.get_style().copy()
        new_style = style.copy()
        # change the style attributes
        new_style.bg[gtk.STATE_NORMAL] = gtk.gdk.Color(50000, 255, 255)
        new_style.bg_pixmap[gtk.STATE_NORMAL] = widget.get_snapshot()
        # fill out the new style by attaching it to the widget
        widget.set_style(new_style)

    def save(self):
        self._fadeout_widget(self.menu_bar)
    
        if not self.filename:
            self.save_as()
        else:
            self.exporter.to_plan_text(self.filename)

    def save_as(self):
        chooser = gtk.FileChooserDialog(title='Save...',
                action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        response = chooser.run()

        if response == gtk.RESPONSE_OK:
            print 'Save as: ', chooser.get_filename()
            self.filename = chooser.get_filename()
            self.exporter.to_plain_text(chooser.get_filename())
        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no file selected'

        chooser.destroy()

    def export(self):
        chooser = gtk.FileChooserDialog(title='Export...',
            action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        filter_pdf = gtk.FileFilter()
        filter_pdf.set_name('PDF-Document')
        filter_pdf.add_pattern('*.pdf')
        chooser.add_filter(filter_pdf)

        filter_odt = gtk.FileFilter()
        filter_odt.set_name('Open-Office-Document')
        filter_odt.add_pattern('*.odt')
        chooser.add_filter(filter_odt)

        response = chooser.run()

        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            print 'Export to: ', filename

            file, ext = os.path.splitext(filename)
            
            if chooser.get_filter().get_name() == 'PDF-Document':
               self.exporter.to_pdf(file)
            elif chooser.get_filter().get_name() == 'Open-Office-Document':
               self.exporter.to_odt(file)

        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no file selected'

        chooser.destroy()

    def open(self):
        chooser = gtk.FileChooserDialog(title='Open...',
                action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        response = chooser.run()

        if response == gtk.RESPONSE_OK:
            print 'Open: ', chooser.get_filename()
        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no file selected'

        chooser.destroy()

    def create_menu_bar(self):
        menu_bar = gtk.MenuBar()

        agr = gtk.AccelGroup()
        self.add_accel_group(agr)

        # File menu
        filemenu = gtk.Menu()
        filem = gtk.MenuItem("_File")
        filem.set_submenu(filemenu)

        newi = gtk.ImageMenuItem(gtk.STOCK_NEW, agr)
        filemenu.append(newi)

        openm = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        filemenu.append(openm)

        filemenu.append(gtk.SeparatorMenuItem())

        savem = gtk.ImageMenuItem(gtk.STOCK_SAVE)
        key, mod = gtk.accelerator_parse("<Control>S")
        savem.add_accelerator("activate", agr, key,
            mod, gtk.ACCEL_VISIBLE)
        savem.connect('activate', self._on_savem)
        filemenu.append(savem)

        saveasm = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS)
        key, mod = gtk.accelerator_parse("<Control><Shift>S")
        saveasm.add_accelerator("activate", agr, key,
            mod, gtk.ACCEL_VISIBLE)
        saveasm.connect('activate', self._on_saveasm)
        filemenu.append(saveasm)

        filemenu.append(gtk.SeparatorMenuItem())

        exportm = gtk.MenuItem("Expor_t...", True)
        exportm.connect('activate', self._on_exportm)
        filemenu.append(exportm)

        filemenu.append(gtk.SeparatorMenuItem())

        exit = gtk.ImageMenuItem(gtk.STOCK_QUIT, agr)
        exit.connect("activate", gtk.main_quit)
        filemenu.append(exit)

        # Edit menu
        editmenu = gtk.Menu()
        editm = gtk.MenuItem("_Edit")
        editm.set_submenu(editmenu)

        undom = gtk.ImageMenuItem(gtk.STOCK_UNDO, agr)
        key, mod = gtk.accelerator_parse("<Control>Z")
        undom.add_accelerator("activate", agr, key,
            mod, gtk.ACCEL_VISIBLE)
        editmenu.append(undom)

        redom = gtk.ImageMenuItem(gtk.STOCK_REDO, agr)
        key, mod = gtk.accelerator_parse("<Control>Y")
        redom.add_accelerator("activate", agr, key,
            mod, gtk.ACCEL_VISIBLE)
        editmenu.append(redom)

        editmenu.append(gtk.SeparatorMenuItem())

        cutm = gtk.ImageMenuItem(gtk.STOCK_CUT, agr)
        editmenu.append(cutm)

        copym = gtk.ImageMenuItem(gtk.STOCK_COPY, agr)
        editmenu.append(copym)

        pastem = gtk.ImageMenuItem(gtk.STOCK_PASTE, agr)
        editmenu.append(pastem)

        deletem = gtk.ImageMenuItem(gtk.STOCK_DELETE, agr)
        editmenu.append(deletem)

        editmenu.append(gtk.SeparatorMenuItem())

        findm = gtk.ImageMenuItem(gtk.STOCK_FIND, agr)
        editmenu.append(findm)

        findreplacem = gtk.ImageMenuItem(gtk.STOCK_FIND_AND_REPLACE, agr)
        editmenu.append(findreplacem)

        # Help menu
        qmenu = gtk.Menu()
        qm = gtk.MenuItem("_Help")
        qm.set_submenu(qmenu)

        helpm = gtk.ImageMenuItem(gtk.STOCK_HELP, agr)
        qmenu.append(helpm)

        aboutm = gtk.ImageMenuItem(gtk.STOCK_ABOUT, agr)
        qmenu.append(aboutm)

        # Add stuff
        menu_bar.append(filem)
        menu_bar.append(editm)
        menu_bar.append(qm)

        return menu_bar

    def create_status_bar(self):
        sbarbox = gtk.HBox(False, 0)

        # Buttons
        self.button_focus = gtk.ToggleButton("Focus")
        self.button_focus.set_image(
            gtk.image_new_from_file("system-search.png"))
        self.button_focus.set_active(True)
        self.button_focus.connect("clicked", self._on_focus_click)
        self.button_fullscreen = gtk.ToggleButton("Fullscreen")
        self.button_fullscreen.set_image(
                gtk.image_new_from_file("view-fullscreen.png"))
        self.button_fullscreen.connect("clicked", self._on_fullscreen_click)

        sbar_wc = gtk.Statusbar()
        context_id = sbar_wc.get_context_id("main_window")
        #sbar_wc.push(context_id, "wc")

        sbarbox.pack_start(self.button_focus, False, False, 0)
        sbarbox.pack_start(self.button_fullscreen, False, False, 0)
        sbarbox.pack_end(sbar_wc, True, True, 0)

        return sbarbox

    def _on_savem(self, data=None):
        self.save()

    def _on_saveasm(self, data=None):
        self.save_as()

    def _on_exportm(self, data=None):
        self.export()

    def _on_focus_click(self, widget, data=None):
        if self.view.focus:
            self.view.get_buffer().stop_focus()
        else:
            self.view.get_buffer().focus_current_sentence()
        self.view.focus = not self.view.focus

    def _on_fullscreen_click(self, widget, data=None):
        if self.is_fullscreen:
            self.unfullscreen()
            # Gtk doesnt provied a way to check a windows state, so we have to
            # keep track ourselves
            self.menu_bar.show()
            self.status_bar.show()
            self.is_fullscreen = False
        else:
            self.fullscreen()
            self.menu_bar.hide()
            self.status_bar.hide()
            self.is_fullscreen = True

    def _on_window_state_event(self, event, data=None):
        if data.new_window_state == gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.button_fullscreen.set_active(True)
            self.is_fullscreen = True
        else:
            self.button_fullscreen.set_active(False)
            self.is_fullscreen = False

    def _delete_event(self, widget, event, data=None):
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

        self.connect('size-request', self._on_resize)

        # http://www.tortall.net/mu/wiki/PyGTKCairoTutorial
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

        self.focus = True

        self._focus_current_sentence()

    def _on_move_cursor(self, widget, event, data=None, asd=None):
        self._focus_current_sentence()

    def _on_key_event(self, widget, event, data=None):
        self._focus_current_sentence()

    def _on_button_event(self, widget, event, data=None):
        self._focus_current_sentence()

    def _on_resize(self, requisition, data=None):
        #print self.get_allocation()
        pass

    def _focus_current_sentence(self):
        if self.focus:
            cursor_iter = self.get_buffer().focus_current_sentence()
            self.scroll_to_iter(cursor_iter, 0.0, True, 0.0, 0.5)


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

        self.set_text("""
# Ab geht die Post
Lorem ipsum dolor sit amet, \
elit. Ut sit a*me*t d**iam ma**uris. Fusce ac ***erat par*** ut ultrices. \
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilis. Morbi di**gn**is*si*m ultric velit, poser accumsan \
leo vehicu eget. Maris at urna e***ge***t arcu vultate feugiat nec id nunc. \
Nullam in faucibus ipsum. Maecenas rhoncus massa eu libero vestibulum \
sollicitudin. Morbi tempus sapien id magna molestie ut sodales lectus \
fringilla. In a quam nibh. Nullam vulputate nunc at velit ultricies at \
feugiat erat dignissim. Aliquam *tempus*, quam non suspit varius, ligula quam \
elementum orci, vitae euismod lectus nulla non mauris. Proin rutrum massa \
feugiat sem scelerisque imperdiet laoreet vulputate. Quisque ullamcorper\
 justo et velit dapibus **vulputate** pharetra lorem lobortis. Phasellus eget \
tellus sed odio facilisis euismod. Mauris a elit libero.

* Numero One
* Zwei
* Drei

Nam elit. Ut sit amet diam mauris. Fusce ac erat, ut ultrices ligula. \
Vestibulum adipiscing mi libero. Suspendisse potenti. Fusce eu dui nunc, at \
tempus leo. Nulla facilis. Morbi *dignissim ultrices velit*, posuere accumsan \
leo vehicula eget. Mauris at urna eget arcu vulputate feugiat nec id nunc. \
Nullam in faucibus ipsum. Maecenas rhoncus massa eu libero vestibulum \
sollicitudin. Morbi tempus sapien id magna molestie ut sodales lectus \
fringilla. In a quam nibh. Nullam vulputate nunc at velit ultricies at \
feugiat erat dignissim. Aliquam tempus, quam non suscipit varius, ligula quam \
elementum orci, vitae *euismod lectus nulla non mauris. Proin rutrum massa \
feugiat sem scelerisque **imperdiet** laoreet vulputate. Quisque ullamcorper\
 justo et velit dapibus vulputate pharetra lorem lobortis. Phasellus eget \
tellus sed odio facilsis* euismod. Mauris a elit libero, a gravida ligula. Nam\
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

        #self.set_text('ha***ll***o asd*hall ooo*asd ***megakrass***')

        self.connect_after("insert-text", self._on_insert_text)
        self.connect_after("delete-range", self._on_delete_range)
        self.connect('apply-tag', self._on_apply_tag)

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

        self._apply_tags = True
        self._update_markdown(self.get_start_iter())
        self._apply_tags = False

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
        """ Applys a highlighting tag to the sentence the cursor is on """

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
        return cursor_iter

    def stop_focus(self):
        start = self.get_start_iter()
        end = self.get_end_iter()
        self.remove_tag_by_name("default", start, end)
        self.apply_tag_by_name("focus", start, end)

if __name__ == '__main__':
    ScribberView()
