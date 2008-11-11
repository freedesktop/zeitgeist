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
import gtk
import gobject
import pango
import calendar
import datetime
import time
import util
import hippo
from SpiffGtkWidgets.color import to_int as c2i
from CanvasDayRange        import CanvasDayRange

class Calendar(hippo.Canvas):
    RANGE_WEEK   = 1
    RANGE_MONTH  = 2
    RANGE_CUSTOM = 3

    def __init__(self, model):
        """
        Constructor.
        """
        hippo.Canvas.__init__(self)
        self.root = hippo.CanvasBox()
        self.set_root(self.root)

        # Init the model and view options.
        self.realized      = False
        self.model         = model
        self.selected      = datetime.date(*time.localtime(time.time())[:3])
        self.range         = self.RANGE_MONTH
        self.visible_range = model.get_month_weeks(self.selected)
        self.active_range  = model.get_month(self.selected)

        # Widgets and canvas items.
        self.range_item = None
        self.colors     = None
        self.font       = None

        # Configure the canvas.
        self.set_flags(gtk.CAN_FOCUS)
        self.set_events(gtk.gdk.EXPOSURE_MASK
                      | gtk.gdk.BUTTON_PRESS_MASK
                      | gtk.gdk.BUTTON_RELEASE_MASK
                      | gtk.gdk.POINTER_MOTION_MASK
                      | gtk.gdk.POINTER_MOTION_HINT_MASK
                      | gtk.gdk.KEY_PRESS_MASK
                      | gtk.gdk.KEY_RELEASE_MASK
                      | gtk.gdk.ENTER_NOTIFY_MASK
                      | gtk.gdk.LEAVE_NOTIFY_MASK
                      | gtk.gdk.FOCUS_CHANGE_MASK)
        self.connect_after('realize',         self.on_realize)
        self.connect      ('size-allocate',   self.on_size_allocate)
        self.connect      ('key-press-event', self.on_key_press_event)


    def set_range(self, range):
        self.range = range
        self.refresh()


    def set_custom_range(self,
                         start,
                         end,
                         active_start = None,
                         active_end = None):
        if active_start is None:
            active_start = start
        if active_end is None:
            active_end = end
        self.range         = self.RANGE_CUSTOM
        self.visible_range = start, end
        self.active_range  = active_start, active_end
        self.refresh()


    def select(self, date):
        self.selected = date
        self.refresh()


    def get_selected(self):
        return self.selected


    def on_realize(self, *args):
        self.realized = True
        self.grab_focus()
        self.on_size_allocate(*args)


    def on_size_allocate(self, *args):
        alloc = self.get_allocation()
        if not self.realized or alloc.width < 10 or alloc.height < 10:
            return
        #self.set_bounds(0, 0, alloc.width, alloc.height)

        # Initialize colors.
        if self.colors is not None:
            return

        style       = self.get_style()
        self.font   = style.font_desc
        self.colors = dict(bg            = c2i(style.bg[gtk.STATE_PRELIGHT]),
                           text          = c2i(style.fg[gtk.STATE_NORMAL]),
                           text_inactive = c2i(style.fg[gtk.STATE_INSENSITIVE]),
                           body          = c2i(style.light[gtk.STATE_ACTIVE]),
                           body_today    = c2i('ivory'),
                           border        = c2i(style.mid[gtk.STATE_NORMAL]),
                           selected      = c2i(style.mid[gtk.STATE_SELECTED]),
                           inactive      = c2i(style.bg[gtk.STATE_PRELIGHT]))
        self.refresh()


    def refresh(self):
        if not self.realized:
            return
        self.draw_background()
        self.draw_days()


    def draw_background(self):
        self.root.color = self.colors['bg']


    def draw_days(self):
        """
        Draws the currently selected range of days.
        """
        if self.range_item is None:
            self.range_item = CanvasDayRange(self)
            self.root.append(self.range_item, hippo.PACK_EXPAND)
            self.range_item.connect('day-clicked',   self.on_day_clicked)
            self.range_item.connect('time-clicked',  self.on_time_clicked)
            self.range_item.connect('event-clicked', self.on_event_clicked)

        if self.range == self.RANGE_WEEK:
            self.visible_range = self.model.get_week(self.selected)
            self.active_range  = self.visible_range
        elif self.range == self.RANGE_MONTH:
            self.visible_range = self.model.get_month_weeks(self.selected)
            self.active_range  = self.model.get_month(self.selected)
        elif self.range == self.RANGE_CUSTOM:
            pass
        else:
            raise TypeError('Invalid range ' + self.range)

        date                         = self.selected
        self.range_item.range        = self.visible_range
        self.range_item.active_range = self.active_range
        self.range_item.selected     = self.selected
        self.range_item.update()


    def on_event_store_event_removed(self, store, event):
        self.refresh()


    def on_event_store_event_added(self, store, event):
        self.refresh()


    def on_key_press_event(self, widget, event):
        date = self.get_selected()
        if event.keyval == 65362:    # Up
            self.select(util.previous_week(date))
            self.emit('day-selected', date, event)
        elif event.keyval == 65364:  # Down
            self.select(util.next_week(date))
            self.emit('day-selected', date, event)
        elif event.keyval == 65361:  # Left
            self.select(util.previous_day(date))
            self.emit('day-selected', date, event)
        elif event.keyval == 65363:  # Right
            self.select(util.next_day(date))
            self.emit('day-selected', date, event)
        elif event.keyval == 65293:  # Enter
            if not self.emit('day-activate', date, event):
                self.set_range(self.RANGE_WEEK)
        return True


    def on_event_clicked(self, sender, event, ev):
        self.emit('event-clicked', event, ev)


    def on_day_clicked(self, sender, date, event):
        if self.emit('date-clicked', date, event):
            return True
        self.select(date)
        if self.range == self.RANGE_MONTH \
          and not self.range_item.is_active(date):
            self.set_range(self.RANGE_MONTH)
        if self.emit('day-selected', date, event):
            return True


    def on_time_clicked(self, sender, date, event):
        self.emit('time-clicked', date, event)


gobject.signal_new('event-clicked',
                   Calendar,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
gobject.signal_new('time-clicked',
                   Calendar,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
gobject.signal_new('date-clicked',
                   Calendar,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
gobject.signal_new('day-selected',
                   Calendar,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
gobject.signal_new('day-activate',
                   Calendar,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

gobject.type_register(Calendar)
