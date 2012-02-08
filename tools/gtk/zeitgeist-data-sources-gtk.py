#! /usr/bin/env python
# -.- coding: utf-8 -.-
#
# Zeitgeist
#
# Copyright © 2010 Siegfried Gevatter <siegfried@gevatter.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import gobject
from gettext import install, ngettext # TODO: Setup translations.

from zeitgeist.datamodel import Interpretation, Manifestation, DataSource
from zeitgeist.client import ZeitgeistDBusInterface

CLIENT = ZeitgeistDBusInterface()
REGISTRY = CLIENT.get_extension("DataSourceRegistry", "data_source_registry")

class DataSourceList(gtk.TreeView):
    
    def __init__(self, activate_callback=None, select_callback=None):
        super(DataSourceList, self).__init__()
        
        self.store = gtk.TreeStore(str, str, bool, bool, gobject.TYPE_PYOBJECT)
        self.selection = self.get_selection() # gtk.TreeSelection
        self.set_model(self.store)
        self.set_search_column(0)
        
        col = self._create_column(_("Name"))
        col[0].add_attribute(col[1], "text", 0)
        col = self._create_column(_("Description"))
        col[0].add_attribute(col[1], "text", 1)
        col = self._create_column(_("Running?"))
        col[0].add_attribute(col[1], "text", 2)
        col = self._create_column(_("Enabled?"), gtk.CellRendererToggle())
        col[1].set_property("activatable", 1)
        col[0].add_attribute(col[1], "active", 3)
        col[1].connect("toggled", self._toggle_checkbox, self.store, 3,
            activate_callback)
        
        self.selection.connect("changed", self._selection_changed,
            select_callback)
        
        for datasource in REGISTRY.GetDataSources():
            self._add_item(datasource)
    
    def __len__(self):
        return len(self.store)
    
    def _create_column(self, name, cell_renderer=gtk.CellRendererText()):
        column = gtk.TreeViewColumn(name, cell_renderer)
        column.set_expand(True)
        column.set_sort_column_id(0)
        self.append_column(column)
        return (column, cell_renderer)
    
    def _toggle_checkbox(self, renderer, row, store, pos, callback):
        treeiter = store.get_iter(row)
        store.set(treeiter, pos, not store.get_value(treeiter, pos))
        if callback:
            callback(store.get_value(treeiter, 4))
    
    def _selection_changed(self, treeselection, callback):
        store, treeiter = treeselection.get_selected()
        if callback:
            callback(store.get_value(treeiter, 4))
    
    def _add_item(self, datasource):
        self.store.append(None, [datasource[DataSource.Name],
            datasource[DataSource.Description], datasource[DataSource.Running],
            datasource[DataSource.Enabled], DataSource(*datasource)])

class MainWindow(gtk.Window):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.set_title("Manage Zeitgeist data-sources")
        self.connect("destroy", self.quit)
        
        self.mainbox = gtk.VBox()
        self.add(self.mainbox)

        self.list = DataSourceList(self.toggle_datasource,
            self.update_selection)
        self.mainbox.pack_start(self.list)
        
        self.mainbox.pack_start(gtk.HSeparator(), expand=False)
        self.selected_title = gtk.Label(ngettext(
            "There is 1 registered data-source.",
            "There are %d registered data-sources." % len(self.list),
            len(self.list)))
        self.mainbox.pack_start(self.selected_title, expand=False, padding=5)
        
        self.show_all()
        
        self.detailsbox = gtk.VBox()
        self.mainbox.pack_start(self.detailsbox, expand=False)
        
        description_label = gtk.Label()
        description_label.set_alignment(0, 0)
        description_label.set_markup("<b>%s</b>" % _("Description"))
        self.detailsbox.pack_start(description_label, expand=False)
        
        self.selected_description = gtk.Label()
        self.selected_description.set_alignment(0, 0)
        self.detailsbox.pack_start(self.selected_description, expand=False)
    
    def toggle_datasource(self, datasource):
        enabled = not datasource[DataSource.Enabled]
        REGISTRY.SetDataSourceEnabled(datasource[DataSource.UniqueId], enabled)
        datasource[DataSource.Enabled] = enabled
    
    def update_selection(self, datasource):
        self.selected_title.set_markup("<b>%s</b> - <i>%s</i>" % (
            datasource[DataSource.Name], datasource[DataSource.UniqueId]))
        self.selected_description.set_markup("<i>%s</i>" % (
            datasource[DataSource.Description]))
        self.detailsbox.show_all()
    
    def quit(self, *discard):
        gtk.main_quit()

if __name__ == "__main__":
    main = MainWindow()
    gtk.main()
