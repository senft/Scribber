#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Scribber, a simple text editor that focuses on minimalism. It has basic
text editor features, Markdown-Syntax-Hilighting, Export to PDF/ODT.
"""

import gtk
import pygtk
pygtk.require('2.0')
import sys

from Widgets import (ScribberFadeHBox, ScribberFindBox, ScribberFindReplaceBox,
                     ScribberTextBuffer, ScribberTextView)

__author__ = 'Julian Wulfheide'
__copyright__ = 'Copyright 2011, Julian Wulfheide'
__credits__ = ['Julian Wulfheide', ]
__license__ = 'MIT'
__maintainer__ = 'Julian Wulfheide'
__version__ = 'dev'
__email__ = 'ju.wulfheide@gmail.com'
__status__ = 'Development'


class ScribberGUI(object):
    def __init__(self):
        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win.set_title('Untitled* - Scribber')

        # Parse own .gtkrc for colored cursor
        gtk.rc_parse(".gtkrc")

        self.buffer = ScribberTextBuffer()
        self.view = ScribberTextView(self.win)
        self.view.set_buffer(self.buffer)

        # GTK doesnt provide a way to check wether a window is fullscreen or
        # no. So we have to keep track ourselves.
        self.is_fullscreen = False

        self.filename = None

        self.win.set_destroy_with_parent(False)

        # Callbacks
        self.win.connect('delete_event', self._delete_event)
        self.win.connect('window-state-event', self._on_window_state_event)
        self.win.connect('size-request', self._on_window_resize)
        self.win.connect('motion-notify-event', self._on_mouse_motion)

        # To keep track of wether the document is modified or not.
        self.buffer.connect('modified-changed',
                            self._on_buffer_modified_change)

        # To hide and show the bars (menu and statusbar)
        self.buffer.connect("insert-text", self._on_buffer_changed)
        self.buffer.connect("delete-range", self._on_buffer_changed)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        scrolled_window.add(self.view)

        self.find_box = ScribberFindBox(self.buffer)

        self.fix_find = gtk.Fixed()
        self.fix_find.add(self.find_box)

        self.find_replace_box = ScribberFindReplaceBox(self.buffer)
        self.fix_find_replace = gtk.Fixed()
        self.fix_find_replace.add(self.find_replace_box)

        self.menu_bar = self.create_menu_bar()
        self.status_bar = self.create_status_bar()

        main_vbox = gtk.VBox(False, 2)
        main_vbox.pack_start(scrolled_window, True, True, 0)
        main_vbox.pack_end(self.fix_find, False, False, 0)
        main_vbox.pack_end(self.fix_find_replace, False, False, 0)

        self.fade_box = ScribberFadeHBox()
        self.fade_box.add_main_widget(main_vbox)
        self.fade_box.add_header(self.menu_bar)
        self.fade_box.add_footer(self.status_bar)

        self.win.add(self.fade_box)
        self.win.resize(600, 600)

    def run(self):
        """ Show Scribber instance. """
        self.win.show_all()
        self.fix_find.hide()
        self.fix_find_replace.hide()
        gtk.main()

    def save(self):
        """ If the current file was previously saved, it just writes all
        changes to the same file. If it never was saved before, call
        save_as(). """
        if not self.filename:
            # Never saved before (no filename known) -> show saveAs dialog
            if self.save_as():
                self.buffer.set_modified(False)
        else:
            # Filename is know
            text = self.buffer.get_start_iter().get_text(
                self.buffer.get_end_iter())
            try:
                with open(self.filename, 'w+') as f:
                    f.write(text)
                self.buffer.set_modified(False)

            except IOError as ioe:
                dialog = \
                    gtk.MessageDialog(parent=self.win,
                                      message_format='Could write to file.',
                                      buttons=gtk.BUTTONS_OK,
                                      type=gtk.MESSAGE_ERROR)
                dialog.format_secondary_text(str(ioe))
                dialog.connect("response", lambda d, r: d.destroy())
                dialog.run()



        # If we saved above, self.get_modified() should be false now, so the
        # save was successfull
        return not self.buffer.get_modified()

    def save_as(self):
        """ Shows a FileChooserDialog and if the user selected a file saves to
        it (returns True if a file was written). """
        success = False
        dialog = gtk.FileChooserDialog(parent=self.win, title='Save...',
                                       action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                       buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                       gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            # User picked a file
            self.filename = dialog.get_filename()
            success = self.save()

        dialog.destroy()
        return success

    def open(self, filename=None):
        response = None
        if self.buffer.get_modified():
            # Ask if file should be saved if it has been modified
            response = self.show_ask_save_dialog()

        # If save-dialog has been canceled, cancel open, too
        if (not response == gtk.RESPONSE_CANCEL or
                not response == gtk.RESPONSE_DELETE_EVENT):
            if not filename:
                # No filename passed, so show a open-dialog
                dialog = \
                    gtk.FileChooserDialog(parent=self.win,
                                          title='Open...',
                                          action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                          buttons=(gtk.STOCK_CANCEL,
                                                   gtk.RESPONSE_CANCEL,
                                                   gtk.STOCK_OPEN,
                                                   gtk.RESPONSE_OK))
                response = dialog.run()
                if response == gtk.RESPONSE_OK:
                    # A file has been selected
                    filename = dialog.get_filename()

                dialog.destroy()

            # Open-dialog might have been canceled, so check for
            # filename != None again
            if filename:
                # Finally open the file
                try:
                    self.view.open_file(filename)
                    self.filename = filename
                    self.set_window_title()
                except IOError as ioe:
                    dialog = \
                        gtk.MessageDialog(parent=self.win,
                                          message_format='Could not open '
                                                         'file.',
                                          buttons=gtk.BUTTONS_OK,
                                          type=gtk.MESSAGE_ERROR)
                    dialog.format_secondary_text(str(ioe))
                    dialog.connect("response", lambda d, r: d.destroy())
                    dialog.run()

    def delete(self):
        """ Deletes the currently selected text in out TextBuffer."""
        self.buffer.delete_selection(True, True)

    def copy(self):
        """ Pushes the currently selected text into the clipboard."""
        try:
            clipboard = gtk.clipboard_get()
            (start, end) = self.buffer.get_selection_bounds()
            clipboard.set_text(start.get_text(end))
        except ValueError:
            # No selection
            pass

    def cut(self):
        """ Pushes the currently selected text into the clipboard and deletes
            it in our TextBuffer."""
        self.copy()
        self.buffer.delete_selection(True, True)

    def paste(self):
        """ Pushes the clipboard in our TextBuffer."""
        # If text is selected delete it first
        self.delete()

        clipboard = gtk.clipboard_get()
        text = clipboard.wait_for_text()
        if text:
            self.buffer.insert_at_cursor(text)

    def toggle_find_box(self):
        self.fix_find_replace.hide()

        if self.fix_find.get_visible():
            self.fix_find.hide()
            self.buffer.stop_hilight_pattern()
            self.win.set_focus(self.view)
        else:
            self.fix_find.show()
            self.win.set_focus(self.find_box.txt_find)

    def toggle_find_replace_box(self):
        self.fix_find.hide()

        if self.fix_find_replace.get_visible():
            self.fix_find_replace.hide()
            self.buffer.stop_hilight_pattern()
            self.win.set_focus(self.view)
        else:
            self.fix_find_replace.show()
            self.win.set_focus(self.find_replace_box.txt_find)

    def show_about(self):
        dialog = gtk.AboutDialog()
        dialog.set_name('Scribber')
        dialog.set_version(__version__)
        dialog.set_copyright(__copyright__)
        with open('LICENSE', 'r') as fhandle:
            license = fhandle.read()
        dialog.set_license(license)
        dialog.set_comments("Scribber is a simple text editor.")
        dialog.set_website("website")
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.run()

    def show_help(self):
        """ Start a not-editable Scribber instance showing a help document. """
        help_win = ScribberGUI()
        help_win.open('help.txt')
        help_win.view.set_editable(False)
        help_win.focus()
        help_win.run()

    def show_ask_save_dialog(self):
        """ Pops up a "Quit w/o saving"-Dialog and saves if user wants to. """
        dialog = gtk.MessageDialog(parent=self.win, flags=0,
                                   type=gtk.MESSAGE_QUESTION,
                                   buttons=gtk.BUTTONS_YES_NO,
                                   message_format='The document has been '
                                                  'modified. Do you want '
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

        self.menu_actions[newm] = new_instance
        self.menu_actions[savem] = self.save
        self.menu_actions[saveasm] = self.save_as
        self.menu_actions[exportm] = None
        self.menu_actions[openm] = self.open
        self.menu_actions[quitm] = self.quit

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
        button_focus = gtk.ToggleButton("Focus")
        ico_focus = gtk.image_new_from_file("icons/system-search.png")
        button_focus.set_image(ico_focus)
        button_focus.set_active(True)
        button_focus.connect("clicked", self._on_button_click)

        self.button_fullscreen = gtk.ToggleButton("Fullscreen")
        ico_fullscreen = gtk.image_new_from_file("icons/view-fullscreen.png")
        self.button_fullscreen.set_image(ico_fullscreen)
        self.button_fullscreen.connect("clicked", self._on_button_click)

        self.button_actions = {}
        self.button_actions[button_focus] = self.focus
        self.button_actions[self.button_fullscreen] = self.fullscreen

        sbar_wc = gtk.Statusbar()
        context_id = sbar_wc.get_context_id("main_window")
        sbar_wc.push(context_id, "wc")

        sbarbox.pack_start(button_focus, False, False, 0)
        sbarbox.pack_start(self.button_fullscreen, False, False, 0)
        sbarbox.pack_end(sbar_wc, True, True, 0)

        return sbarbox

    def focus(self):
        self.view.toggle_focus_mode()
        # Focus TextView
        self.win.set_focus(self.view)

    def fullscreen(self):
        # Gtk doesnt provied a way to check a windows state, so we have to
        # keep track ourselves
        if self.is_fullscreen:
            self.win.unfullscreen()
            self.is_fullscreen = False
        else:
            self.win.fullscreen()
            self.is_fullscreen = True

        # Focus TextView
        self.win.set_focus(self.view)

    def set_window_title(self):
        if self.filename:
            filename = self.filename
        else:
            filename = 'Untitled'

        if self.buffer.get_modified():
            self.win.set_title(filename + '*' + ' - Scribber')
        else:
            self.win.set_title(filename + ' - Scribber')

    def _on_menu_click(self, widget, data=None):
        """ Called when clicked on a menu item. """
        if widget in self.menu_actions:
            self.menu_actions[widget]()

    def _on_button_click(self, widget, data=None):
        """ Called when clicked on a button. """
        if widget in self.button_actions:
            self.button_actions[widget]()

    def _on_mouse_motion(self, widget, event, data=None):
        # TODO Toggling decoration is a hard "break"
        #self.win.set_decorated(True)
        self.fade_box.fadein()

    def _on_buffer_changed(self, buffer, iter, text, length=None):
        self.fade_box.fadeout()

        self.win.set_decorated(True)

    def _on_buffer_modified_change(self, widget, data=None):
        """ Called when the TextBuffer of our TextView gets modified.
            Only used to set the right window title (* when Buffer is
            modified)."""
        self.set_window_title()

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
        response = None
        if self.buffer.get_modified():
            response = self.show_ask_save_dialog()

        # When this returns True (it means the Safe-Dialog was canceled) we
        # dont quit
        result = response == gtk.RESPONSE_CANCEL
        if not result:
            gtk.main_quit()
        return result

    def quit(self):
        self.win.emit("delete-event", gtk.gdk.Event(gtk.gdk.DELETE))


def new_instance():
    new = ScribberGUI()
    new.run()


def main():
    if len(sys.argv) > 1:
        # TODO Make some real arg parsing here
        INST = ScribberGUI()
        INST.open(sys.argv[1])
    else:
        INST = ScribberGUI()

    INST.run()

if __name__ == '__main__':
    main()
