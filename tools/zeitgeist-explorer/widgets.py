# -.- coding: utf-8 -.-
#
# Zeitgeist Explorer
#
# Copyright © 2011 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
# Copyright © 2011 Stefano Candori <stefano.candori@gmail.com>
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
import time
import gobject

class CalendarPopup(gtk.Dialog):

	calendar = None

	_callback = None
	_associated_widget = None

	def __init__(self, associated_widget, callback=None):
		super(CalendarPopup, self).__init__(None)
		self.calendar = gtk.Calendar()
		self._associated_widget = associated_widget
		self._callback = callback
		self.vbox.pack_start(self.calendar)
		self.set_decorated(False)
		self.set_position(gtk.WIN_POS_NONE)
		self.set_property('skip-taskbar-hint', True)
		self.connect('focus-out-event',
			lambda *discard: self.hide(False))
		self.calendar.connect('day-selected-double-click',
			lambda *discard: self.hide(True))

	def hide(self, accepted=False):
		super(CalendarPopup, self).hide()
		if accepted and self._callback:
			self._callback(self.calendar.get_date())

	def show(self):
		widget_pos = self._associated_widget.get_allocation()
		parent_pos = self._associated_widget.get_parent_window().get_position()
		self.move(parent_pos[0] + widget_pos.x,
			parent_pos[1] + widget_pos.y + widget_pos.height)
		self.show_all()

class DateSelector(gtk.Button):

	_calendar_popup = None

	def __init__(self):
		super(DateSelector, self).__init__()
		def cb(foo):
			print foo
		self._calendar_popup = CalendarPopup(self, cb)
		self.connect('clicked', lambda *discard: self._calendar_popup.show())
		self.set_label('%d-%d-%d' % self._calendar_popup.calendar.get_date())

	@property
	def calendar(self):
		return self._calendar_popup.calendar

class TimeSelector(gtk.HBox):

	_hour_selector = None
	_minute_selector = None

	def __init__(self):
		super(TimeSelector, self).__init__()
		self._hour_selector = gtk.SpinButton(gtk.Adjustment(0, 0, 24, 1))
		self._minute_selector = gtk.SpinButton(gtk.Adjustment(0, 0, 60, 1))
		self.pack_start(self._hour_selector)
		self.pack_start(gtk.Label(':'))
		self.pack_start(self._minute_selector)

class DateTimeSelector(gtk.HBox):

	_date_selector = None
	_time_selector = None

	def __init__(self):
		super(DateTimeSelector, self).__init__()
		self._date_selector = DateSelector()
		self._time_selector = TimeSelector()
		self.pack_start(self._date_selector)
		self.pack_start(self._time_selector)

	def get_timestamp(self):
		return 0
