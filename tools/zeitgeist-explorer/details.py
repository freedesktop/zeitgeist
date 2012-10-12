# -.- coding: utf-8 -.-
#
# Zeitgeist Explorer
#
# Copyright © 2011 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
# Copyright © 2010 Siegfried Gevatter <siegfried@gevatter.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import gobject

from zeitgeist.datamodel import Interpretation, Manifestation

import ontology

class _DetailsWindow(gtk.Window):

	_main_box = None
	_main_table = None

	def __init__(self, *args, **kwargs):
		super(_DetailsWindow, self).__init__()
		self.set_resizable(False)

		self._main_box = gtk.VBox()
		self.add(self._main_box)

		self._build_window(*args, **kwargs)

		button_box = gtk.HBox()
		button_box.pack_start(gtk.Label(""))
		close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
		close_button.connect('clicked', lambda *discard: self.destroy())
		button_box.pack_start(close_button, False)
		self._main_box.pack_start(button_box, True, False)
		close_button.grab_focus()

		self.show_all()

	def _add_title(self, title_text):
		title = gtk.Label()
		title.set_markup('<b>%s</b>' % title_text)
		title.set_alignment(0, 0)
		title.set_padding(5, 5)
		title.set_selectable(True)
		self._main_box.pack_start(title, False)

	def _add_table_entry(self, pos, label, value, tooltip=None, info=None):
		entry_label = gtk.Label()
		entry_label.set_markup('<b>%s:</b>' % label)
		entry_label.set_alignment(0, 0)
		entry_label.set_selectable(True)

		value_label = gtk.Label()
		if value:
			value_label.set_text(value)
		else:
			value_label.set_markup('<i>%s</i>' % _('No value'))
		value_label.set_alignment(0, 0)
		value_label.set_selectable(True)

		if tooltip:
			value_label.set_tooltip_text(tooltip)

		self._main_table.attach(entry_label, 0, 1, pos, pos + 1,
			xoptions=gtk.FILL, yoptions=gtk.FILL, xpadding=5, ypadding=5)
		self._main_table.attach(value_label, 1, 2, pos, pos + 1,
			yoptions=gtk.FILL, xpadding=5, ypadding=5)

		if info:
			info_image = gtk.Image()
			info_image.set_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON)
			info_button = gtk.Button()
			info_button.set_image(info_image)
			info_button.connect('clicked', lambda *discard: info())
			self._main_table.attach(info_button, 2, 3, pos, pos + 1,
				xoptions=gtk.FILL, yoptions=gtk.FILL)

	def _add_table_separator(self, pos):
		self._main_table.attach(gtk.HSeparator(), 0, 3, pos, pos + 1)

class EventDetails(_DetailsWindow):

	_event = None
	_subjects_view = None

	def _build_window(self, event):
		self.set_title(_('Event #%s: %s') % (event.id, event.date_string))
		self._event = event

		self._add_title(_('Event #%s') % event.id)

		self._main_table = gtk.Table(5, 3)
		self._main_box.pack_start(self._main_table, False)

		timestamp_text = '%s (%.3f)' % (event.date_string,
			int(event.timestamp) / 1000.0)
		self._add_table_entry(0, _('Timestamp'), timestamp_text)
		self._add_table_entry(1, _('Interpretation'), event.interp_string,
			event.interpretation, ontology.EventInterpretationHelp)
		self._add_table_entry(2, _('Manifestation'), event.manif_string,
			event.manifestation, ontology.EventManifestationHelp)
		self._add_table_entry(3, _('Actor'), event.actor)
		self._add_table_entry(4, _('Origin'), event.origin)

		self._subjects_view = EventSubjectsTreeView()
		self._main_box.pack_start(self._subjects_view, False)

		for subject in event.subjects:
			self._subjects_view.add_subject(subject)

class SubjectDetails(_DetailsWindow):

	_subject = None

	def _build_window(self, subject):
		self.set_title(_('Subject: %s') % subject.text)
		self._subject = subject

		self._add_title(_('Subject: %s') % subject.text)

		self._main_table = gtk.Table(8, 3)
		self._main_box.pack_start(self._main_table, False)

		self._add_table_entry(0, _('URI'), subject.uri)
		self._add_table_entry(1, _('Interpretation'), subject.interp_string,
			subject.interpretation, ontology.SubjectInterpretationHelp)
		self._add_table_entry(2, _('Manifestation'), subject.manif_string,
			subject.manifestation, ontology.SubjectManifestationHelp)
		self._add_table_entry(3, _('Origin'), subject.origin)
		self._add_table_entry(4, _('MIME-Type'), subject.mimetype)
		self._add_table_entry(5, _('Storage'), subject.storage)
		self._add_table_separator(6)
		self._add_table_entry(7, _('Current URI'), subject.current_uri)

		self.show_all()

class EventSubjectsTreeView(gtk.TreeView):

	_store = None

	def __init__(self):
		super(EventSubjectsTreeView, self).__init__()

		self._store = gtk.TreeStore(str, str, str, gobject.TYPE_PYOBJECT)
		self.set_model(self._store)
		self.set_search_column(0)

		col = self._create_column(_('Subject'), 0)
		col = self._create_column(_('Interpretation'), 1)
		col = self._create_column(_('Manifestation'), 2)

		self.connect('button-press-event', self._on_click)

	def _get_data_from_event(self, event):
		x, y = (int(round(event.x)), int(round(event.y)))
		treepath = self.get_path_at_pos(x, y)[0]
		treeiter = self._store.get_iter(treepath)
		return self._store.get_value(treeiter, 3)

	def _on_click(self, widget, event):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			data = self._get_data_from_event(event)
			SubjectDetails(data)

	def _create_column(self, name, data_col, cell_renderer=gtk.CellRendererText()):
		column = gtk.TreeViewColumn(name, cell_renderer)
		column.set_expand(True)
		column.set_sort_column_id(data_col)
		column.add_attribute(cell_renderer, 'text', data_col)
		self.append_column(column)
		return (column, cell_renderer)

	def add_subject(self, subject):
		self._store.append(None, [
			subject.text,
			Interpretation[subject.interpretation].display_name,
			Manifestation[subject.manifestation].display_name,
			subject])

# vim:noexpandtab:ts=4:sw=4
