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
import calendar
import pango
import util
from SpiffGtkWidgets import color

class CanvasDay(hippo.CanvasBox, hippo.CanvasItem):
    """
    A canvas item representing a day.
    """
    def __init__(self, cal, **kwargs):
        """
        Constructor.
        """
        hippo.CanvasBox.__init__(self, **kwargs)

        self.cal         = cal
        self.date        = kwargs.get('date')
        self.active      = True
        self.selected    = False
        self.highlighted = False
        self.show_rulers = False

        # Create canvas items.
        self.box  = hippo.CanvasGradient(padding = 2, padding_right = 5)
        self.text = hippo.CanvasText(xalign    = hippo.ALIGNMENT_END,
                                     size_mode = hippo.CANVAS_SIZE_ELLIPSIZE_END)
        self.body = hippo.CanvasGradient()

        self.box.append(self.text, hippo.PACK_EXPAND)
        self.append(self.box)
        self.append(self.body, hippo.PACK_EXPAND)
        self.box.set_visible(True)


    def set_date(self, date):
        self.date = date


    def set_active(self, active):
        self.active = active


    def set_selected(self, selected):
        self.selected = selected


    def set_highlighted(self, highlighted):
        self.highlighted = highlighted


    def set_show_title(self, show_title):
        self.box.set_visible(show_title)


    def set_show_rulers(self, show_rulers):
        self.show_rulers = show_rulers


    def _set_color(self, box, color):
        box.set_property('start-color', color)
        box.set_property('end-color',   color)


    def get_body_position(self):
        return self.get_position(self.body)


    def get_body_allocation(self):
        return self.body.get_allocation()


    def update(self):
        # Draw the title box.
        if self.selected:
            self._set_color(self.box, self.cal.colors['selected'])
        elif not self.active:
            self._set_color(self.box, self.cal.colors['inactive'])
        else:
            self._set_color(self.box, self.cal.colors['border'])

        # Draw the title text.
        if self.date is not None:
            #day_name = self.cal.model.get_day_name(self.date)
            #caption  = '%s %s' % (self.date.timetuple()[2], day_name)
            caption  = '%d' % self.date.timetuple()[2]
            self.text.set_property('font',  self.cal.font.to_string())
            self.text.set_property('text',  caption)
            self.text.set_property('color', self.cal.colors['text'])

        # Draw the "body" of the day.
        if self.highlighted:
            self._set_color(self.body, self.cal.colors['body_today'])
        else:
            self._set_color(self.body, self.cal.colors['body'])
        self.body.set_property('spacing', 0)


    def do_paint_above_children(self, ctx, rect):
        if not self.show_rulers:
            return
        ctx.set_source_rgba(*color.to_rgba(self.cal.colors['inactive']))
        ctx.rectangle(rect.x, rect.y, rect.width, rect.height)
        ctx.set_line_width(1)
        ctx.set_dash((1, 1))
        ctx.clip()
        w, h = self.get_allocation()

        for n in range(0, 24):
            y = n * h / 24
            ctx.move_to(0, y)
            ctx.line_to(w, y)
        ctx.stroke()

gobject.type_register(CanvasDay)
