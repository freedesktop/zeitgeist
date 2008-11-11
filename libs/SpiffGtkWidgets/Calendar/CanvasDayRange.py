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
import math
import time
import datetime
import util
from SpiffGtkWidgets  import color
from CanvasTimeline   import CanvasTimeline
from CanvasGrid       import CanvasGrid
from CanvasDay        import CanvasDay
from CanvasTable      import CanvasTable
from CanvasHEventView import CanvasHEventView
from CanvasVEventView import CanvasVEventView

class CanvasDayRange(CanvasTable, hippo.CanvasItem):
    """
    A canvas item that shows a range of days.
    """
    def __init__(self, cal, **kwargs):
        """
        Constructor.
        """
        CanvasTable.__init__(self, **kwargs)

        self.cal          = cal
        self.range        = kwargs.get('range')
        self.active_range = self.range
        self.selected     = None

        # Create canvas items.
        self.scroll        = hippo.CanvasScrollbars()
        self.hbox_top      = hippo.CanvasBox(orientation = hippo.ORIENTATION_HORIZONTAL)
        self.vbox_top      = hippo.CanvasBox()
        self.day_captions  = CanvasTable()
        self.timeline      = CanvasTimeline(self.cal)
        self.padding_left  = hippo.CanvasBox()
        self.padding_right = hippo.CanvasBox()
        self.allday_view   = CanvasHEventView(self.cal, yalign = hippo.ALIGNMENT_FILL)
        self.grid          = CanvasGrid(self._new_cell)
        self.gridbox       = hippo.CanvasBox(orientation = hippo.ORIENTATION_HORIZONTAL)
        self.vevent_views  = {}
        self.hevent_views  = {}
        self.allocs        = {}
        self.allocs[self.padding_left]  = (0, 0, 0, 0)
        self.allocs[self.padding_right] = (0, 0, 0, 0)

        self.vbox_top.append(self.day_captions)
        self.vbox_top.append(self.allday_view)
        self.day_captions.set_homogeneus_columns(True)

        self.hbox_top.append(self.padding_left)
        self.hbox_top.append(self.vbox_top, hippo.PACK_EXPAND)
        self.hbox_top.append(self.padding_right)

        self.gridbox.append(self.timeline)
        self.gridbox.append(self.grid, hippo.PACK_EXPAND)
        self.scroll.set_root(self.gridbox)

        self.add(self.hbox_top, 0, 1, 0, 1)
        self.add(self.scroll,   0, 1, 1, 2)
        self.set_row_expand(1, True)
        self.set_column_expand(0, True)
        self.allday_view.show_normal = False
        self.allday_view.connect('event-clicked', self.on_view_event_clicked)
        self.grid.connect('paint', self.on_grid_paint)
        self.grid.set_homogeneus_columns(True)


    def on_day_button_press_event(self, widget, event):
        date = datetime.datetime(*widget.date.timetuple()[:3])
        self.emit('time-clicked', date, event)
        self.emit('day-clicked', widget.date, event)


    def on_view_time_clicked(self, view, item, ev, time):
        date = datetime.date(*time.timetuple()[:3])
        self.emit('time-clicked', time, ev)
        self.emit('day-clicked', date, ev)


    def on_view_event_clicked(self, view, item, ev):
        self.emit('event-clicked', item.event, ev)


    def _new_cell(self):
        cell = CanvasDay(self.cal, xalign = hippo.ALIGNMENT_FILL)
        cell.connect('button-press-event', self.on_day_button_press_event)
        return cell


    def is_active(self, date):
        return self.active_range[0] <= date <= self.active_range[1]


    def _get_event_view(self, row, start, end, horizontal):
        if horizontal:
            if self.hevent_views.has_key(row):
                view = self.hevent_views[row]
                view.set_range(start, end)
                return view
            view = CanvasHEventView(self.cal, start, end)
            self.hevent_views[row] = view
        else:
            if self.vevent_views.has_key(row):
                view = self.vevent_views[row]
                view.set_range(start, end)
                return view
            view = CanvasVEventView(self.cal, start, end)
            self.vevent_views[row] = view
        view.connect('time-clicked',  self.on_view_time_clicked)
        view.connect('event-clicked', self.on_view_event_clicked)
        self.allocs[view] = (0, 0, 0, 0)
        self.gridbox.append(view, hippo.PACK_FIXED)
        return view


    def _remove_vevent_view(self, cell):
        if not self.vevent_views.has_key(cell):
            return
        view = self.vevent_views[cell]
        self.gridbox.remove(view)
        del self.vevent_views[cell]
        del self.allocs[view]


    def _remove_hevent_view(self, cell):
        if not self.hevent_views.has_key(cell):
            return
        view = self.hevent_views[cell]
        self.gridbox.remove(view)
        del self.hevent_views[cell]
        del self.allocs[view]


    def update_one_row(self):
        self.scroll.set_policy(hippo.ORIENTATION_VERTICAL,
                               hippo.SCROLLBAR_ALWAYS)
        self.grid.set_properties(box_height = 800)
        self.allday_view.set_range(*self.range)
        self.allday_view.set_visible(True)
        self.padding_left.set_visible(True)
        self.padding_right.set_visible(True)

        # Hide all event views.
        for cell in [c for c in self.hevent_views]:
            self._remove_hevent_view(cell)
        current_children = self.grid.get_children()
        for cell in [c for c in self.vevent_views]:
            if cell not in current_children:
                self._remove_vevent_view(cell)

        # Create an event view on top of each cell.
        for child in self.grid.get_children():
            start = child.date
            end   = util.end_of_day(child.date)
            view  = self._get_event_view(child, start, end, False)
            self.allocs[view] = (0, 0, 0, 0)


    def update_multi_row(self):
        self.scroll.set_policy(hippo.ORIENTATION_VERTICAL,
                               hippo.SCROLLBAR_NEVER)
        self.grid.set_properties(box_height = -1)
        self.allday_view.set_visible(False)
        self.padding_left.set_visible(False)
        self.padding_right.set_visible(False)

        # Hide all event views.
        for cell in [c for c in self.vevent_views]:
            self._remove_vevent_view(cell)
        current_children = self.grid.get_children()
        for cell in [c for c in self.hevent_views]:
            if cell not in current_children:
                self._remove_hevent_view(cell)

        # Create an event view on top of each row.
        for row in self.grid.get_rows():
            start = row[0].date
            end   = row[-1].date
            view  = self._get_event_view(row[0], start, end, True)
            self.allocs[view] = (0, 0, 0, 0)


    def update(self):
        date  = self.range[0]
        days  = (self.range[1] - self.range[0]).days + 1
        rows  = int(math.ceil(float(days) / 7.0))
        cols  = days
        today = datetime.date(*time.localtime(time.time())[:3])
        if days > 7:
            cols = int(math.ceil(float(days) / float(rows)))

        # Update the timeline.
        self.timeline.set_visible(rows == 1)

        # Show captions for the day.
        if cols == 7 or rows == 1:
            for child in self.day_captions.get_children():
                self.day_captions.remove(child)
            for col in range(cols):
                this_date = self.range[0] + datetime.timedelta(col)
                day_name  = self.cal.model.get_day_name(this_date)
                text      = hippo.CanvasText(text      = day_name,
                                             xalign    = hippo.ALIGNMENT_CENTER,
                                             size_mode = hippo.CANVAS_SIZE_ELLIPSIZE_END)
                self.day_captions.add(text, col, col + 1, 0, 1)
                self.day_captions.set_column_expand(col, True)
            self.day_captions.set_visible(True)
        else:
            self.day_captions.set_visible(False)

        # Update the grid.
        self.grid.set_size(rows, cols)
        for row in range(rows):
            self.grid.set_row_expand(row, True)
        for child in self.grid.get_children():
            child.set_active(self.is_active(date))
            child.set_show_title(rows != 1)
            child.set_show_rulers(rows == 1)
            child.set_selected(date == self.selected)
            child.set_highlighted(date == today)
            child.set_date(date)
            child.update()
            date = util.next_day(date)

        if rows == 1:
            self.update_one_row()
        else:
            self.update_multi_row()


    def do_allocate_one_row(self, width, height, origin_changed):
        grid_x, grid_y = self.gridbox.get_position(self.grid)
        for cell in self.grid.get_children():
            cell_x_off,  cell_y_off  = self.grid.get_position(cell)
            cell_w,      cell_h      = cell.get_allocation()
            x                        = grid_x + cell_x_off
            y                        = grid_y + cell_y_off
            w                        = cell_w
            h                        = cell_h
            view                     = self.vevent_views[cell]
            alloc                    = (x, y, w, h)

            if self.allocs[view] == alloc:
                continue
            self.allocs[view] = alloc
            self.gridbox.set_position(view, alloc[0], alloc[1])
            view.set_properties(box_width  = alloc[2],
                                box_height = alloc[3])


    def do_allocate_multi_row(self, width, height, origin_changed):
        days           = (self.range[1] - self.range[0]).days + 1
        rows           = int(math.ceil(float(days) / 7.0))
        cols           = days
        grid_x, grid_y = self.gridbox.get_position(self.grid)
        if days > 7:
            cols = int(math.ceil(float(days) / float(rows)))

        for row in self.grid.get_rows():
            start = row[0].date
            end   = row[-1].date
            view  = self._get_event_view(row[0], start, end, True)
            view.set_column_count(cols)

            # Find the position of the writable area of the row.
            grid_w,      grid_h      = self.grid.get_allocation()
            row_x_off,   row_y_off   = self.grid.get_position(row[0])
            cell_w,      cell_h      = row[0].get_allocation()
            title_x_off, title_y_off = row[0].get_body_position()
            x                        = grid_x + row_x_off
            y                        = grid_y + row_y_off + title_y_off
            w                        = grid_w
            h                        = cell_h - title_y_off
            alloc                    = (x, y, w, h)

            if self.allocs[view] == alloc:
                continue
            self.allocs[view] = alloc
            self.gridbox.set_position(view, alloc[0], alloc[1])
            view.set_properties(box_width  = alloc[2],
                                box_height = alloc[3])


    def do_allocate(self, width, height, origin_changed): 
        days           = (self.range[1] - self.range[0]).days + 1
        rows           = int(math.ceil(float(days) / 7.0))
        cols           = days
        grid_x, grid_y = self.gridbox.get_position(self.grid)
        if days > 7:
            cols = int(math.ceil(float(days) / float(rows)))

        # Show the items for one-row mode or multi-row mode.
        if rows == 1:
            self.do_allocate_one_row(width, height, origin_changed)
        else:
            self.do_allocate_multi_row(width, height, origin_changed)
        hippo.CanvasBox.do_allocate(self, width, height, origin_changed)


    def on_grid_paint_one_row(self):
        w,          h          = self.get_allocation()
        grid_x,     grid_y     = self.gridbox.get_position(self.grid)
        grid_w,     grid_h     = self.grid.get_allocation()
        timeline_w, timeline_h = self.timeline.get_allocation()
        padding_left           = timeline_w
        padding_right          = w - timeline_w - grid_w

        if self.allocs[self.padding_left][2] != padding_left:
            self.allocs[self.padding_left] = (0, 0, padding_left, 0)
            self.padding_left.set_properties(box_width = padding_left)
        if self.allocs[self.padding_right][2] != padding_right:
            self.allocs[self.padding_right] = (0, 0, padding_right, 0)
            self.padding_right.set_properties(box_width = padding_right)


    def on_grid_paint(self, grid, ptr, rect):
        # catching this signal is ugly, but trying to do this  
        # in do_allocate() will result in painful to avoid event 
        # loops.
        days = (self.range[1] - self.range[0]).days + 1
        rows = int(math.ceil(float(days) / 7.0))

        if rows == 1:
            self.on_grid_paint_one_row()


gobject.type_register(CanvasDayRange)

gobject.signal_new('day-clicked',
                   CanvasDayRange,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

gobject.signal_new('time-clicked',
                   CanvasDayRange,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

gobject.signal_new('event-clicked',
                   CanvasDayRange,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
