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
import pango
import datetime
import util
from SpiffGtkWidgets   import color
from CanvasEvent       import CanvasEvent
from CanvasEventView   import CanvasEventView
from CanvasMagnetTable import CanvasMagnetTable

class CanvasHEventView(CanvasEventView, hippo.CanvasItem):
    """
    A canvas item that shows a range of events.
    """
    def __init__(self, cal, start = None, end = None, **kwargs):
        """
        Constructor.
        """
        CanvasEventView.__init__(self, cal, **kwargs)
        self.table = CanvasMagnetTable(align = CanvasMagnetTable.ALIGN_TOP)
        self.table.set_homogeneus_columns(True)
        self.append(self.table, hippo.PACK_EXPAND)
        self.show_normal = True  # whether to show normal events
        self.overflow_indic = []
        self.columns = 0


    def _format_time(self, event):
        hour, minute = event.start.timetuple()[3:5]
        if minute == 0:
            text = '%d %s' % (hour, event.caption)
        else:
            text = '%d:%02d %s' % (hour, minute, event.caption)
        return text


    def set_column_count(self, count):
        if count == self.columns:
            return
        self.columns = count

        self.table.set_column_count(count)

        # Hide all overflow indicators.
        for child in self.get_children():
            if child != self.table:
                self.remove(child)

        for col in range(count):
            font = self.cal.font.copy()
            font.set_style(pango.STYLE_ITALIC)
            text = hippo.CanvasText(text   = 'more',
                                    font   = font.to_string(),
                                    xalign = hippo.ALIGNMENT_CENTER)
            self.append(text, hippo.PACK_FIXED)
            self.overflow_indic.append(text)
            text.set_visible(False)
            self.allocs[text] = (0, 0, 0, 0)


    def _add_event(self, event):
        event_start      = max(event.start, self.range[0])
        event_end        = min(event.end,   self.range[1])
        event_off_days   = (event_start - self.range[0]).days
        event_width_days = (event_end - event_start).days + 1

        # Create the event.
        item = CanvasEvent(self.cal, event)
        self.event_items[event] = item
        item.connect('button-press-event',   self.on_event_button_press_event)
        item.connect('button-release-event', self.on_event_button_release_event)
        self.table.add(item,
                       event_off_days,
                       event_off_days + event_width_days,
                       len(self.event_items))
        item.set_text(event.caption)
        if event.all_day:
            item.set_property('color', color.to_int(event.bg_color))
        if self.show_normal and not util.same_day(event.start, event.end):
            item.set_property('color', color.to_int(event.bg_color))
        elif not event.all_day:
            time = self._format_time(event)
            item.set_text(time)
            item.set_text_properties(xalign = hippo.ALIGNMENT_START)
        if event.text_color is not None:
            item.set_text_color(event.text_color)
        radius_top_left     = 10
        radius_top_right    = 10
        radius_bottom_left  = 10
        radius_bottom_right = 10
        if event.end > self.range[1]:
            radius_top_right    = 0
            radius_bottom_right = 0
        if event.start < self.range[0]:
            radius_top_left    = 0
            radius_bottom_left = 0
        item.set_properties(radius_top_left     = radius_top_left,
                            radius_top_right    = radius_top_right,
                            radius_bottom_left  = radius_bottom_left,
                            radius_bottom_right = radius_bottom_right)


    def update(self):
        days = (self.range[1] - self.range[0]).days + 1
        self.table.set_column_count(days)
        self.table.set_row_count(-1)

        # Remove old events.
        for item in self.table.get_children():
            self.table.remove(item)

        # Add events.
        if self.range is None:
            return
        for event in self.model.get_all_day_events(self.range[0],
                                                   self.range[1],
                                                   self.show_normal == True):
            self._add_event(event)
        if self.show_normal:
            for event in self.model.get_normal_events(self.range[0],
                                                      self.range[1],
                                                      False):
                self._add_event(event)

        # Change to fixed sizing.
        rows, cols = self.table.get_size()
        self.table.set_size(rows, cols)


    def do_allocate(self, width, height, origin_changed):
        CanvasEventView.do_allocate(self, width, height, origin_changed)

        # Hide all overflow indicators.
        for child in self.get_children():
            if child != self.table:
                child.set_visible(False)

        rows, cols = self.table.get_size()
        if min(rows, width, height) <= 0:
            return

        # Measure the height of the first event.
        children = self.table.get_children()
        if len(children) == 0:
            return
        first = children[0]
        min_row_h, row_h = first.get_height_request(width / cols)
        if row_h <= 0:
            return

        # Hide events that do not fit into the box.
        max_rows = height / row_h
        matrix   = self.table.get_matrix()
        for colnum, col in enumerate(matrix.get_columns()):
            # Count rows that are already hidden.
            hidden = 0
            for child in col:
                if not child.get_visible():
                    hidden += 1

            # No need to hide anything if the box is large enough.
            if hidden == 0 and len(col) <= max_rows:
                for child in col:
                    child.set_visible(True)
                continue

            # Hide enough rows to make room for an overflow indicator.
            to_hide = len(col) - max_rows + 1
            hidden  = 0
            for row in reversed(col):
                if hidden >= to_hide:
                    row.set_visible(True)
                    continue
                if not row.get_visible():
                    hidden += 1
                    continue
                row.set_visible(False)
                hidden += 1

            # Show overflow indicator
            indic   = self.overflow_indic[colnum]
            caption = '%d more' % hidden
            alloc   = (width / cols * colnum, height - row_h, width / cols, hidden)
            indic.set_visible(True)

            if self.allocs[indic] == alloc:
                continue
            self.allocs[indic] = alloc
            indic.set_properties(text        = caption,
                                 box_width   = alloc[2])
            self.set_position(indic, alloc[0], alloc[1])
        CanvasEventView.do_allocate(self, width, height, origin_changed)


gobject.type_register(CanvasHEventView)
