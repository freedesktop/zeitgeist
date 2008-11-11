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
from math              import ceil
from CanvasEvent       import CanvasEvent
from CanvasEventView   import CanvasEventView
from CanvasMagnetTable import CanvasMagnetTable

class CanvasVEventView(CanvasEventView):
    """
    A canvas item that shows a range of events.
    """
    def __init__(self, cal, start = None, end = None, **kwargs):
        """
        Constructor.
        """
        self.table = CanvasMagnetTable(align = CanvasMagnetTable.ALIGN_LEFT)
        self.table.set_row_count(24 * 4)
        self.table.set_homogeneus_rows(True)
        CanvasEventView.__init__(self, cal, start, end, **kwargs)
        self.append(self.table, hippo.PACK_EXPAND)


    def _add_event(self, event):
        rows, cols     = self.table.get_size()
        event_start    = max(event.start, self.range[0])
        event_end      = min(event.end,   self.range[1])
        event_off      = (event_start   - self.range[0]).seconds
        event_len      = (event_end     - event_start).seconds
        range_len      = self.range[1] - self.range[0]
        seconds        = range_len.days * 24 * 60 * 60 + range_len.seconds
        row_seconds    = ceil(seconds / float(rows))
        event_off_rows = int(ceil(event_off / float(row_seconds)))
        event_len_rows = int(ceil(event_len / float(row_seconds)))
        event_end_rows = event_off_rows + event_len_rows

        # Create the event.
        item = CanvasEvent(self.cal, event)
        self.event_items[event] = item
        item.connect('button-press-event',   self.on_event_button_press_event)
        item.connect('button-release-event', self.on_event_button_release_event)
        self.table.set_column_expand(cols, True)
        self.table.add(item, cols + 1, cols + 2, event_off_rows, event_end_rows)
        item.set_text(event.caption)
        item.set_property('color', color.to_int(event.bg_color))
        if event.text_color is not None:
            item.set_text_color(event.text_color)

        radius_top_left     = 10
        radius_top_right    = 10
        radius_bottom_left  = 10
        radius_bottom_right = 10
        if event.end > self.range[1]:
            radius_bottom_left  = 0
            radius_bottom_right = 0
        if event.start < self.range[0]:
            radius_top_left  = 0
            radius_top_right = 0
        item.set_properties(radius_top_left     = radius_top_left,
                            radius_top_right    = radius_top_right,
                            radius_bottom_left  = radius_bottom_left,
                            radius_bottom_right = radius_bottom_right)


    def update(self):
        # Remove old events.
        for item in self.table.get_children():
            self.table.remove(item)
        self.table.set_column_count(0)

        if self.range is None:
            return
        for event in self.model.get_normal_events(*self.range):
            self._add_event(event)


gobject.type_register(CanvasVEventView)
