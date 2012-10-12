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

class _HelpWindow(gtk.Window):

	def __init__(self, title):
		super(_HelpWindow, self).__init__()
		self.set_title(title)
		self.set_size_request(700, 400)

		self._main_box = gtk.VBox()
		self.add(self._main_box)

		values = self._get_values()

		self._main_table = gtk.Table(len(values) * 2, 2)
		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		sw.add_with_viewport(self._main_table)
		self._main_box.pack_start(sw)

		for i, value in enumerate(values):
			self._add_table_entry(2*i, value.display_name, value.uri, value.doc)

		self.show_all()

	def _add_table_entry(self, pos, name, uri, doc):
		entry_label = gtk.Label()
		entry_label.set_markup('<b>%s</b>' % name)
		entry_label.set_alignment(0, 0)
		entry_label.set_selectable(True)

		value_label = gtk.Label()
		value_label.set_text(uri)
		value_label.set_alignment(0, 0)
		value_label.set_selectable(True)

		doc_label = gtk.Label()
		doc_label.set_markup('<i>%s</i>' % doc)
		doc_label.set_alignment(0, 0)
		doc_label.set_line_wrap(True)
		doc_label.set_selectable(True)

		self._main_table.attach(entry_label, 0, 1, pos, pos + 1,
			xoptions=gtk.FILL, yoptions=gtk.FILL, xpadding=5, ypadding=5)
		self._main_table.attach(value_label, 1, 2, pos, pos + 1,
			yoptions=gtk.FILL, xpadding=5, ypadding=5)
		self._main_table.attach(doc_label, 0, 2, pos + 1, pos + 2,
			yoptions=gtk.FILL, xpadding=5, ypadding=5)

class EventInterpretationHelp(_HelpWindow):

	def __init__(self):
		title = _('Event Interpretations')
		super(EventInterpretationHelp, self).__init__(title)

	def _get_values(self):
		return Interpretation.EVENT_INTERPRETATION.get_all_children()

class SubjectInterpretationHelp(_HelpWindow):

	def __init__(self):
		title = _('Subject Interpretations')
		super(SubjectInterpretationHelp, self).__init__(title)

	def _get_values(self):
		interpretations = set()
		for child in Interpretation.iter_all_children():
			if not child.is_child_of(Interpretation.EVENT_INTERPRETATION):
				interpretations.add(child)
		return interpretations

class EventManifestationHelp(_HelpWindow):

	def __init__(self):
		title = _('Event Manifestations')
		super(EventManifestationHelp, self).__init__(title)

	def _get_values(self):
		return Manifestation.EVENT_MANIFESTATION.get_all_children()

class SubjectManifestationHelp(_HelpWindow):

	def __init__(self):
		title = _('Subject Manifestations')
		super(SubjectManifestationHelp, self).__init__(title)

	def _get_values(self):
		manifestations = set()
		for child in Manifestation.iter_all_children():
			if not child.is_child_of(Manifestation.EVENT_MANIFESTATION):
				manifestations.add(child)
		return manifestations
