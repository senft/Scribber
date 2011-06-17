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
from ReSTExporter import ReSTExporter
from Widgets import ScribberTextView, ScribberFindBox, ScribberFindReplaceBox


class ScribberView():
    def __init__(self):
        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        # Parse own .gtkrc for colored cursor
        gtk.rc_parse(".gtkrc")

        self.view = ScribberTextView()
        self.is_fullscreen = False
        self.filename = None
        self.exporter = ReSTExporter(self.view.get_buffer())

        self.view.get_buffer().connect('modified-changed',
            self._on_buffer_modified_change)

        self.win.set_title("Scribber - Untitled")
        self.win.set_destroy_with_parent(False)

        # Callbacks
        self.win.connect('delete_event', self._delete_event)
        self.win.connect('destroy', self.destroy)
        self.win.connect('window-state-event', self._on_window_state_event)
        self.win.connect('size-request', self._on_window_resize)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.view)

        self.find_box = ScribberFindBox(self.view.get_buffer())
        self.fix_find = gtk.Fixed()
        self.fix_find.add(self.find_box)

        self.find_replace_box = ScribberFindReplaceBox(self.view.get_buffer())
        self.fix_find_replace = gtk.Fixed()
        self.fix_find_replace.add(self.find_replace_box)

        vbox = gtk.VBox(False, 2)

        self.menu_bar = self.create_menu_bar()
        self.status_bar = self.create_status_bar()

        vbox.pack_start(self.menu_bar, False, False, 0)
        vbox.pack_start(scrolled_window, True, True, 0)
        vbox.pack_start(self.fix_find, False, False, 0)
        vbox.pack_start(self.fix_find_replace, False, False, 0)
        vbox.pack_end(self.status_bar, False, False, 0)
        self.win.add(vbox)

        #check = gtkspell.Spell(view)
        #check.set_language("de_DE")

        self.open("default.txt")

        # Go!
        self.win.show_all()
        self.fix_find.hide()
        self.fix_find_replace.hide()
        gtk.main()

    def new(self):
        ScribberView()

    def save(self):
        if not self.filename:
            # Never saved before (no filename known) -> show SaveAs dialog
            if self.save_as():
                self.view.get_buffer().set_modified(False)
        else:
            # Filename is know
            if self.exporter.to_plain_text(self.filename):
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
        dialog = gtk.FileChooserDialog(parent=self.win, title='Export...',
            action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        filter_pdf = gtk.FileFilter()
        filter_pdf.set_name('PDF-Document')
        filter_pdf.add_pattern('*.pdf')
        dialog.add_filter(filter_pdf)

        filter_odt = gtk.FileFilter()
        filter_odt.set_name('Open-Office-Document')
        filter_odt.add_pattern('*.odt')
        dialog.add_filter(filter_odt)

        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            print 'Export to: ', filename

            file, ext = os.path.splitext(filename)
            
            if dialog.get_filter().get_name() == 'PDF-Document':
               self.exporter.to_pdf(file)
            elif dialog.get_filter().get_name() == 'Open-Office-Document':
               self.exporter.to_odt(file)

        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no file selected'


    def open(self, filename=None):
        response = None
        if self.view.get_buffer().get_modified():
            response = self.show_ask_save_dialog()

        if filename is None:
            if not response == gtk.RESPONSE_CANCEL:

                dialog = gtk.FileChooserDialog(parent=self.win, title='Open...',
                        action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))

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

    def find(self):
        self.fix_find_replace.hide()

        if self.fix_find.get_visible():
            self.fix_find.hide()
            self.view.get_buffer().stop_hilight_pattern()
            self.win.set_focus(self.view)
        else:
            self.fix_find.show()
            self.win.set_focus(self.find_box.txt_find)

    def find_replace(self):
        self.fix_find.hide()

        if self.fix_find_replace.get_visible():
            self.fix_find_replace.hide()
            self.view.get_buffer().stop_hilight_pattern()
            self.win.set_focus(self.view)
        else:
            self.fix_find_replace.show()
            self.win.set_focus(self.find_replace_box.txt_find)

    def show_ask_save_dialog(self):
        dialog = gtk.MessageDialog(parent=self.win, flags=0, 
                type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
                message_format='The document has been modified. Do you want \
to save your changes?')

        dialog.add_button('Cancel', gtk.RESPONSE_CANCEL)
        response = dialog.run()

        if response == gtk.RESPONSE_YES:
            self.save()

        dialog.destroy()
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
        newm.connect('activate', self._on_newm)
        filemenu.append(newm)

        openm = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        openm.connect('activate', self._on_openm)
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

        exportm = gtk.MenuItem("Expor_t...")
        exportm.connect('activate', self._on_exportm)
        filemenu.append(exportm)

        filemenu.append(gtk.SeparatorMenuItem())

        exit = gtk.ImageMenuItem(gtk.STOCK_QUIT, agr)
        exit.connect("activate", self._on_quitm)
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
        cutm.connect("activate", self._on_cutm)
        editmenu.append(cutm)

        copym = gtk.ImageMenuItem(gtk.STOCK_COPY, agr)
        copym.connect("activate", self._on_copym)
        editmenu.append(copym)

        pastem = gtk.ImageMenuItem(gtk.STOCK_PASTE, agr)
        pastem.connect("activate", self._on_pastem)
        editmenu.append(pastem)

        deletem = gtk.ImageMenuItem(gtk.STOCK_DELETE, agr)
        deletem.connect("activate", self._on_deletem)
        editmenu.append(deletem)

        editmenu.append(gtk.SeparatorMenuItem())

        findm = gtk.ImageMenuItem(gtk.STOCK_FIND, agr)
        findm.connect("activate", self._on_findm)
        editmenu.append(findm)

        findreplacem = gtk.ImageMenuItem(gtk.STOCK_FIND_AND_REPLACE, agr)
        findreplacem.connect("activate", self._on_findreplacem)
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
        sbar_wc.push(context_id, "wc")

        sbarbox.pack_start(self.button_focus, False, False, 0)
        sbarbox.pack_start(self.button_fullscreen, False, False, 0)
        sbarbox.pack_end(sbar_wc, True, True, 0)

        return sbarbox

    def _on_newm(self, data=None):
        self.new()

    def _on_savem(self, data=None):
        self.save()

    def _on_saveasm(self, data=None):
        self.save_as()

    def _on_exportm(self, data=None):
        self.export()

    def _on_openm(self, data=None):
        self.open()

    def _on_quitm(self, data=None):
        pass
        
    def _on_copym(self, data=None):
        self.copy()

    def _on_cutm(self, data=None):
        self.cut()

    def _on_pastem(self, data=None):
        self.paste()

    def _on_deletem(self, data=None):
        self.delete()

    def _on_findm(self, data=None):
        self.find()

    def _on_findreplacem(self, data=None):
        self.find_replace()
    
    def _on_buffer_modified_change(self, widget, data=None):
        if self.filename:
            filename = self.filename
        else:
            filename = 'Untitled'

        if self.view.get_buffer().get_modified():
            self.win.set_title('Scribber - ' + filename + '*')
        else:
            self.win.set_title('Scribber - ' + filename)

    def _on_focus_click(self, widget, data=None):
        if self.view.focus:
            self.view.get_buffer().stop_focus()
        else:
            self.view.get_buffer().focus_current_sentence()
        self.view.focus = not self.view.focus

    def _on_fullscreen_click(self, widget, data=None):
        if self.is_fullscreen:
            self.win.unfullscreen()
            # Gtk doesnt provied a way to check a windows state, so we have to
            # keep track ourselves
            self.menu_bar.show()
            self.status_bar.show()
            self.is_fullscreen = False
        else:
            self.win.fullscreen()
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

    def _on_window_resize(self, requisition, data=None):
        self.view.get_buffer().focus_current_sentence()

    def _delete_event(self, widget, event, data=None):
        # When this returns True we dont quit
        response = None
        if self.view.get_buffer().get_modified():
            response = self.show_ask_save_dialog()

        return response == gtk.RESPONSE_CANCEL

    def destroy(self, widget, data=None):
        gtk.main_quit()


if __name__ == '__main__':
    ScribberView()
