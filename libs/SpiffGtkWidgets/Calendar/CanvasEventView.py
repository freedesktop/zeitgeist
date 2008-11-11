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
import hippo
import gobject
import datetime
import util
from SpiffGtkWidgets import color
from CanvasEvent import CanvasEvent

class CanvasEventView(hippo.CanvasBox):
    """
    A canvas item that shows a range of events.
    """
    def __init__(self, cal, start = None, end = None, **kwargs):
        """
        Constructor.
        """
        hippo.CanvasBox.__init__(self, **kwargs)

        self.cal         = cal
        self.model       = cal.model
        self.range       = None
        self.event_items = {}
        self.allocs      = {}
        self.set_range(start, end)
        self.connect_after('button-press-event', self.on_button_press_event)
        self.model.connect('event-added',   self.on_model_event_added)
        self.model.connect('event-removed', self.on_model_event_removed)


    def on_model_event_added(self, model, event):
        self.update()


    def on_model_event_removed(self, model, event):
        if event not in self.event_items:
            return
        self.update()


    def on_button_press_event(self, widget, event):
        w, h  = self.get_allocation()
        days  = (self.range[1] - self.range[0]).days + 1
        day_w = w / float(days)
        day   = int(event.x / day_w)
        date  = self.range[0] + datetime.timedelta(1) * day
        time  = 24 / float(h) * event.y
        hour  = int(time)
        min   = (time - hour) * 60
        date += datetime.timedelta(0, 0, 0, 0, min, hour)
        self.emit('time-clicked', widget, event, date)


    def on_event_button_press_event(self, widget, event):
        self.emit('event-clicked', widget, event)
        return True


    def on_event_button_release_event(self, widget, event):
        self.emit('event-released', widget, event)
        return True


    def set_range(self, start, end):
        if start is None or end is None:
            return
        range = datetime.datetime(*start.timetuple()[:3]), \
                datetime.datetime(*end.timetuple()[:7])
        if self.range is not None \
          and self.range[0] == range[0] \
          and self.range[1] == range[1]:
            return
        self.range = range
        self.update()


gobject.type_register(CanvasEventView)

gobject.signal_new('time-clicked',
                   CanvasEventView,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT))

gobject.signal_new('event-clicked',
                   CanvasEventView,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

gobject.signal_new('event-released',
                   CanvasEventView,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
