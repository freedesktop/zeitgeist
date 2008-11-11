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
from SpiffGtkWidgets import color
from CanvasRectangle import CanvasRectangle

class CanvasEvent(CanvasRectangle):
    """
    A canvas item representing a day.
    """
    def __init__(self, cal, event, **kwargs):
        """
        Constructor.
        """
        self.cal    = cal
        text        = kwargs.pop('text', '')
        self.event  = event
        self.rulers = []
        CanvasRectangle.__init__(self, **kwargs)

        # Create canvas items.
        self.text = hippo.CanvasText(xalign    = hippo.ALIGNMENT_CENTER,
                                     yalign    = hippo.ALIGNMENT_CENTER,
                                     size_mode = hippo.CANVAS_SIZE_ELLIPSIZE_END)

        self.append(self.text, hippo.PACK_EXPAND)
        self.set_text(text)


    def set_text(self, text):
        self.text.set_property('text', text)


    def set_text_color(self, newcolor):
        self.text.props.color = color.to_int(newcolor)


    def set_text_properties(self, **kwargs):
        self.text.set_properties(**kwargs)


gobject.type_register(CanvasEvent)
