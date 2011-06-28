#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Scribber, a simple text editor that focuses on minimalism. It has basic
text editor features, Markdown-Syntax-Hilighting, Export to PDF/ODT.

Some icons provided by the Tango Desktop Project
(http://tango.freedesktop.org/)
"""

import pygtk
pygtk.require('2.0')
import gtk
import os
import sys

from MarkdownExporter import MarkdownExporter
from MarkdownExporter import ExportDialog
from ScribberWidgets import ScribberTextView
from ScribberWidgets import ScribberFindBox
from ScribberWidgets import ScribberFindReplaceBox
from ScribberWidgets import ScribberFadeHBox


__author__ = 'Julian Wulfheide'
__copyright__ = 'Copyright 2011, Julian Wulfheide'
__credits__ = ['Julian Wulfheide', ]
__license__ = 'MIT'
__maintainer__ = 'Julian Wulfheide'
__version__ = '0.1'
__email__ = 'ju.wulfheide@gmail.com'
__status__ = 'Development'


class ScribberView():
    def __init__(self, filename=None):
        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)

        # Parse own .gtkrc for colored cursor
        gtk.rc_parse(".gtkrc")

        self.view = ScribberTextView()

        # GTK doesnt provide a way to check wether a window is fullscreen or
        # no. So we have to keep track ourselves.
        self.is_fullscreen = False

        self.filename = filename
        self.exporter = MarkdownExporter()

        self.win.set_title("Scribber - Untitled")
        self.win.set_destroy_with_parent(False)

        # Callbacks
        self.win.connect('delete_event', self._delete_event)
        self.win.connect('destroy', self.destroy)
        self.win.connect('window-state-event', self._on_window_state_event)
        self.win.connect('size-request', self._on_window_resize)
        self.win.connect('motion-notify-event', self._on_mouse_motion)

        # To keep track of wether the document is modified or not.
        self.view.get_buffer().connect('modified-changed',
            self._on_buffer_modified_change)

        # To hide or show the bars
        self.view.get_buffer().connect("insert-text", self._on_buffer_changed)
        self.view.get_buffer().connect("delete-range", self._on_buffer_changed)

        scrolled_window = gtk.ScrolledWindow()
        #scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        scrolled_window.add(self.view)

        self.find_box = ScribberFindBox(self.view.get_buffer())

        self.fix_find = gtk.Fixed()
        self.fix_find.add(self.find_box)

        self.find_replace_box = ScribberFindReplaceBox(self.view.get_buffer())
        self.fix_find_replace = gtk.Fixed()
        self.fix_find_replace.add(self.find_replace_box)

        vbox = gtk.VBox(False, 2)
        # Chill.. otherwise, fade_box calls on_size_allocate infinitly
        vbox.set_resize_mode(gtk.RESIZE_QUEUE)

        self.menu_bar = self.create_menu_bar()
        self.status_bar = self.create_status_bar()

        vbox.pack_start(scrolled_window, True, True, 0)
        vbox.pack_end(self.fix_find, False, False, 0)
        vbox.pack_end(self.fix_find_replace, False, False, 0)

        self.fade_box = ScribberFadeHBox()
        self.fade_box.add_main(vbox)
        self.fade_box.add_header(self.menu_bar)
        self.fade_box.add_footer(self.status_bar)

        self.win.add(self.fade_box)

        if self.filename:
            self.open(filename)

    def go(self):
        """ Show Scribber instance. """
        # Go!
        self.win.show_all()
        self.fix_find.hide()
        self.fix_find_replace.hide()
        gtk.main()

    def new(self):
        new = ScribberView()
        new.go()

    def save(self):
        if not self.filename:
            # Never saved before (no filename known) -> show SaveAs dialog
            if self.save_as():
                self.view.get_buffer().set_modified(False)
        else:
            # Filename is know
            result = self.exporter.to_plain_text(
                self.view.get_buffer().get_start_iter().get_text(
                self.view.get_buffer().get_end_iter()),
                self.filename)

            if result:
                self.view.get_buffer().set_modified(False)

        # If we saved in one of the branches above, get_modified should be
        # to false now -> save() was successfull
        return not self.view.get_buffer().get_modified()

    def save_as(self):
        success = False

        dialog = gtk.FileChooserDialog(parent=self.win, title='Save...',
                action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            # User picked a file
            self.filename = dialog.get_filename()
            success = self.save()

        dialog.destroy()
        return success

    def export(self):
        #exportdialog = ExportDialog()
        #exportdialog.show()

        filedialog = gtk.FileChooserDialog(parent=self.win, title='Export...',
            action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        filter_pdf = gtk.FileFilter()
        filter_pdf.set_name('PDF-Document')
        filter_pdf.add_pattern('*.pdf')
        filedialog.add_filter(filter_pdf)

        filter_odt = gtk.FileFilter()
        filter_odt.set_name('Open-Office-Document')
        filter_odt.add_pattern('*.odt')
        filedialog.add_filter(filter_odt)

        response = filedialog.run()

        if response == gtk.RESPONSE_OK:
            filename = filedialog.get_filename()
            print 'Export to: ', filename

            file, ext = os.path.splitext(filename)

            if filedialog.get_filter().get_name() == 'PDF-Document':
                # TODO Ugly text retreavel
                self.exporter.to_pdf(
                    self.view.get_buffer().get_start_iter().get_text(
                    self.view.get_buffer().get_end_iter()), file)
            elif filedialog.get_filter().get_name() == 'Open-Office-Document':
                self.exporter.to_odt(file)

        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no file selected'

        filedialog.destroy()

    def open(self, filename=None):
        response = None
        if self.view.get_buffer().get_modified():
            response = self.show_ask_save_dialog()

        if filename is None:
            if not response == gtk.RESPONSE_CANCEL:

                dialog = gtk.FileChooserDialog(parent=self.win,
                        title='Open...', action=gtk.FILE_CHOOSER_ACTION_OPEN,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))

                response = dialog.run()

                if response == gtk.RESPONSE_OK:
                    filename = dialog.get_filename()
                    self.view.open_file(filename)
                    self.win.set_title('Scribber - ' + filename)
                    self.filename = filename
                elif response == gtk.RESPONSE_CANCEL:
                    print 'Closed, no file selected'

                dialog.destroy()
        else:
            self.view.open_file(filename)
            self.win.set_title('Scribber - ' + filename)
            self.filename = filename

    def delete(self):
        self.view.get_buffer().delete_selection(True, True)

    def copy(self):
        try:
            clipboard = gtk.clipboard_get()
            (start, end) = self.view.get_buffer().get_selection_bounds()
            clipboard.set_text(start.get_text(end))
        except:
            # No selection
            pass

    def cut(self):
        self.copy()
        self.view.get_buffer().delete_selection(True, True)

    def paste(self):
        # If text is selected delete it first
        self.delete()

        clipboard = gtk.clipboard_get()
        text = clipboard.wait_for_text()
        if text:
            self.view.get_buffer().insert_at_cursor(text)

    def toggle_find_box(self):
        self.fix_find_replace.hide()

        print 'toggle'
        if self.fix_find.get_visible():
            self.fix_find.hide()
            self.view.get_buffer().stop_hilight_pattern()
            self.win.set_focus(self.view)
        else:
            self.fix_find.show()
            self.win.set_focus(self.find_box.txt_find)
            print 'show'

    def toggle_find_replace_box(self):
        self.fix_find.hide()

        if self.fix_find_replace.get_visible():
            self.fix_find_replace.hide()
            self.view.get_buffer().stop_hilight_pattern()
            self.win.set_focus(self.view)
        else:
            self.fix_find_replace.show()
            self.win.set_focus(self.find_replace_box.txt_find)

    def show_about(self):
        dialog = gtk.AboutDialog()
        dialog.set_name('Scribber')
        dialog.set_version(__version__)
        dialog.set_copyright(__copyright__)
        dialog.set_license(__license__)
        dialog.set_comments("Scribber is a simple text editor.")
        dialog.set_website("website")
        dialog.connect("response", lambda d, r: d.destroy())

        dialog.run()

    def show_help(self):
        """ Start a not-editable Scribber instance showing a help document. """
        help = ScribberView('help.txt')
        help.view.set_editable(False)
        help.go()

    def show_ask_save_dialog(self):
        """ Pops up a "Quit w/o saving"-Dialog and saves if user wants to
            save."""

        dialog = gtk.MessageDialog(parent=self.win, flags=0,
                type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
                message_format='The document has been modified. Do you want '
                               'to save your changes?')

        dialog.add_button('Cancel', gtk.RESPONSE_CANCEL)
        response = dialog.run()

        if response == gtk.RESPONSE_YES:
            self.save()

        dialog.destroy()
        # Return the responso so we can react on a REPONSE_CANCEL elsewere
        return response

    def create_menu_bar(self):
        menu_bar = gtk.MenuBar()

        agr = gtk.AccelGroup()
        self.win.add_accel_group(agr)

        # File menu
        filemenu = gtk.Menu()
        filem = gtk.MenuItem("_File")
        filem.set_submenu(filemenu)

        newm = gtk.ImageMenuItem(gtk.STOCK_NEW, agr)
        newm.connect('activate', self._on_menu_click)
        filemenu.append(newm)

        openm = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        openm.connect('activate', self._on_menu_click)
        filemenu.append(openm)

        filemenu.append(gtk.SeparatorMenuItem())

        savem = gtk.ImageMenuItem(gtk.STOCK_SAVE)
        key, mod = gtk.accelerator_parse("<Control>S")
        savem.add_accelerator('activate', agr, key,
            mod, gtk.ACCEL_VISIBLE)
        savem.connect('activate', self._on_menu_click)
        filemenu.append(savem)

        saveasm = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS)
        key, mod = gtk.accelerator_parse("<Control><Shift>S")
        saveasm.add_accelerator('activate', agr, key,
            mod, gtk.ACCEL_VISIBLE)
        saveasm.connect('activate', self._on_menu_click)
        filemenu.append(saveasm)

        filemenu.append(gtk.SeparatorMenuItem())

        exportm = gtk.MenuItem("Expor_t...")
        exportm.connect('activate', self._on_menu_click)
        filemenu.append(exportm)

        filemenu.append(gtk.SeparatorMenuItem())

        quitm = gtk.ImageMenuItem(gtk.STOCK_QUIT, agr)
        quitm.connect('activate', self._on_menu_click)
        filemenu.append(quitm)

        # Edit menu
        editmenu = gtk.Menu()
        editm = gtk.MenuItem("_Edit")
        editm.set_submenu(editmenu)

        undom = gtk.ImageMenuItem(gtk.STOCK_UNDO, agr)
        key, mod = gtk.accelerator_parse("<Control>Z")
        undom.add_accelerator('activate', agr, key,
            mod, gtk.ACCEL_VISIBLE)
        editmenu.append(undom)

        redom = gtk.ImageMenuItem(gtk.STOCK_REDO, agr)
        key, mod = gtk.accelerator_parse("<Control>Y")
        redom.add_accelerator('activate', agr, key,
            mod, gtk.ACCEL_VISIBLE)
        editmenu.append(redom)

        editmenu.append(gtk.SeparatorMenuItem())

        cutm = gtk.ImageMenuItem(gtk.STOCK_CUT, agr)
        cutm.connect('activate', self._on_menu_click)
        editmenu.append(cutm)

        copym = gtk.ImageMenuItem(gtk.STOCK_COPY, agr)
        copym.connect('activate', self._on_menu_click)
        editmenu.append(copym)

        pastem = gtk.ImageMenuItem(gtk.STOCK_PASTE, agr)
        pastem.connect('activate', self._on_menu_click)
        editmenu.append(pastem)

        deletem = gtk.ImageMenuItem(gtk.STOCK_DELETE, agr)
        deletem.connect('activate', self._on_menu_click)
        editmenu.append(deletem)

        editmenu.append(gtk.SeparatorMenuItem())

        findm = gtk.ImageMenuItem(gtk.STOCK_FIND, agr)
        findm.connect('activate', self._on_menu_click)
        editmenu.append(findm)

        findreplacem = gtk.ImageMenuItem(gtk.STOCK_FIND_AND_REPLACE, agr)
        findreplacem.connect('activate', self._on_menu_click)
        editmenu.append(findreplacem)

        # Help menu
        qmenu = gtk.Menu()
        qm = gtk.MenuItem("_Help")
        qm.set_submenu(qmenu)

        helpm = gtk.ImageMenuItem(gtk.STOCK_HELP, agr)
        helpm.connect('activate', self._on_menu_click)
        qmenu.append(helpm)

        aboutm = gtk.ImageMenuItem(gtk.STOCK_ABOUT, agr)
        aboutm.connect('activate', self._on_menu_click)
        qmenu.append(aboutm)

        # Add stuff
        menu_bar.append(filem)
        menu_bar.append(editm)
        menu_bar.append(qm)

        self.menu_actions = {}

        self.menu_actions[newm] = self.new
        self.menu_actions[savem] = self.save
        self.menu_actions[saveasm] = self.save_as
        self.menu_actions[exportm] = self.export
        self.menu_actions[openm] = self.open
        self.menu_actions[quitm] = self.new

        self.menu_actions[copym] = self.copy
        self.menu_actions[cutm] = self.cut
        self.menu_actions[pastem] = self.paste
        self.menu_actions[deletem] = self.delete

        self.menu_actions[findm] = self.toggle_find_box
        self.menu_actions[findreplacem] = self.toggle_find_replace_box

        self.menu_actions[aboutm] = self.show_about
        self.menu_actions[helpm] = self.show_help

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
        sbar_wc.push(context_id, "wc")

        sbarbox.pack_start(self.button_focus, False, False, 0)
        sbarbox.pack_start(self.button_fullscreen, False, False, 0)
        sbarbox.pack_end(sbar_wc, True, True, 0)

        return sbarbox

    def _on_menu_click(self, widget, data=None):
        """ Called when clicked on a menu item. """
        self.menu_actions[widget]()

    def _on_mouse_motion(self, widget, event, data=None):
        self.win.set_decorated(True)
        self.fade_box.fadein()

    def _on_buffer_changed(self, buf, iter, text, length=None):
        self.win.set_decorated(False)
        self.fade_box.fadeout()

    def _on_buffer_modified_change(self, widget, data=None):
        """ Called when the TextBuffer of our TextView gets modified.
            Only used to set the right window title (* when Buffer is
            modified)."""
        if self.filename:
            filename = self.filename
        else:
            filename = 'Untitled'

        if self.view.get_buffer().get_modified():
            if not self.win.get_title().endswith('*'):
                self.win.set_title('Scribber - ' + filename + '*')
        else:
            if self.win.get_title().endswith('*'):
                self.win.set_title('Scribber - ' + filename)

    def _on_focus_click(self, widget, data=None):
        if self.view.focus:
            self.view.get_buffer().stop_focus()
        else:
            self.view.get_buffer().focus_current_sentence()
        self.view.focus = not self.view.focus

    def _on_fullscreen_click(self, widget, data=None):
        # Gtk doesnt provied a way to check a windows state, so we have to
        # keep track ourselves
        if self.is_fullscreen:
            self.win.unfullscreen()
            self.is_fullscreen = False
        else:
            self.win.fullscreen()
            self.is_fullscreen = True

    def _on_window_state_event(self, widget, event, data=None):
        """ Called when the window state changes (e.g.
            Fullscreen/Unfullscreen). Needed to determine the correct state
            for the fullscreen button, because fullscreen can be set
            externally."""
        if event.new_window_state == gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.button_fullscreen.set_active(True)
            self.is_fullscreen = True
        else:
            self.button_fullscreen.set_active(False)
            self.is_fullscreen = False

    def _on_window_resize(self, requisition, data=None):
        self.view.focus_current_sentence()

    def _delete_event(self, widget, event, data=None):
        # When this returns True we dont quit
        response = None
        if self.view.get_buffer().get_modified():
            response = self.show_ask_save_dialog()

        return response == gtk.RESPONSE_CANCEL

    def destroy(self, widget, data=None):
        gtk.main_quit()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        scribber = ScribberView(sys.argv[1])
    else:
        scribber = ScribberView()

    scribber.go()
