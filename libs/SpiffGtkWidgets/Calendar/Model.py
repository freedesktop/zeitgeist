# Copyright (C) 2008 Samuel Abels <http://debain.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import gobject
import datetime
import calendar
import util
from MyCalendar import MyCalendar

class Model(gobject.GObject):
    __gsignals__ = {
        'event-removed': (gobject.SIGNAL_RUN_FIRST,
                          gobject.TYPE_NONE,
                          (gobject.TYPE_PYOBJECT,)),
        'event-added': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self):
        """
        Constructor.
        
        start -- datetime
        end -- datetime
        """
        self.__gobject_init__()
        self.next_event_id = 0
        self.calendar      = MyCalendar(calendar.SUNDAY)
        self.events        = {}


    def get_week(self, date):
        """
        Returns a tuple (start, end), where "start" points to the first day 
        of the given week, and "end" points to the last day of given week.
        """
        return self.calendar.get_week(date)


    def get_month(self, date):
        """
        Returns a tuple (start, end), where "start points to the first day 
        of the given month and "end" points to the last day of the given 
        month.
        """
        return self.calendar.get_month(date)


    def get_month_weeks(self, date, fill = True):
        """
        Returns a tuple (start, end), where "start" points to the first day 
        of the first week of given month, and "end" points to the last day of 
        the last week of the same month.
        """
        return self.calendar.get_month_weeks(date, fill)


    def get_day_name(self, date):
        """
        Returns the name of the given week day.
        """
        return self.calendar.get_day_name(date)


    def get_month_name(self, date):
        """
        Returns the name of the given month.
        """
        return self.calendar.get_month_name(date)


    def remove_event(self, event):
        assert event is not None
        if event.id is None:
            return
        del self.events[event.id]
        self.emit('event-removed', event)


    def add_event(self, event):
        assert event    is not None
        assert event.id is None
        self.events[self.next_event_id] = event
        event.id = self.next_event_id
        self.next_event_id += 1
        self.emit('event-added', event)


    def get_events(self, start, end):
        """
        Returns a list of all events that intersect with the given start
        and end times.
        """
        events = []
        for event in self.events.values():
            if util.event_intersects(event, start, end):
                events.append(event)
        events.sort(util.event_days, reverse = True)
        return events


    def get_all_day_events(self, start, end, include_timed_events = False):
        # Get a list of all-day events and sort them by length.
        events = []
        for event in self.get_events(start, end):
            if event.all_day:
                events.append(event)
                continue
            if include_timed_events \
              and not util.same_day(event.start, event.end):
                events.append(event)
        return events


    def get_normal_events(self, start, end, include_multi_day_events = True):
        # Get a list of non-all-day events and sort them by length.
        events = []
        for event in self.get_events(start, end):
            if not include_multi_day_events \
              and not util.same_day(event.start, event.end):
                continue
            if not event.all_day:
                events.append(event)
        return events
