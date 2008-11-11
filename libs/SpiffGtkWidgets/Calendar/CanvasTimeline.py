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

class CanvasTimeline(hippo.CanvasBox):
    """
    A canvas item representing a timeline.
    """
    def __init__(self, cal, **kwargs):
        """
        Constructor.
        """
        hippo.CanvasBox.__init__(self, **kwargs)

        self.cal  = cal
        self.text = {}

        # Create canvas items.
        for n in range(0, 24):
            if n == -1:
                caption = ' '
            else:
                caption = '%d' % n
            box     = hippo.CanvasGradient(padding_right = 5)
            text    = hippo.CanvasText(text   = caption,
                                       xalign = hippo.ALIGNMENT_END,
                                       yalign = hippo.ALIGNMENT_START)
            box.append(text, hippo.PACK_EXPAND)
            self.append(box, hippo.PACK_EXPAND)


    def _set_color(self, box, color):
        box.set_property('start-color', color)
        box.set_property('end-color',   color)


    def update(self):
        line_height = self.height / 24

        # Draw the timeline.
        for n, box in enumerate(self.get_children()):
            text = box.get_children()[0]
            self._set_color(box, self.cal.colors['border'])
            text.set_property('font',  self.cal.font.to_string())
            text.set_property('color', self.cal.colors['text'])
