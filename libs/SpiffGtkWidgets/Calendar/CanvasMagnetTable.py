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
import sys
import util
from SpiffGtkWidgets import color
from CanvasTable import CanvasTable

class CanvasMagnetTable(CanvasTable):
    """
    A table that works similar to four-in-a-row. It has a number homogeneous 
    columns, and every child is dragged towards the top of the column.
    The table also allows for adding children that span multiple columns.
    """
    ALIGN_TOP    = 1
    ALIGN_BOTTOM = 2
    ALIGN_LEFT   = 4
    ALIGN_RIGHT  = 8

    __gproperties__ = {
        'align':    (gobject.TYPE_LONG,
                     'the alignment',
                     'the direction into which children are pulled. one of'
                   + ' ALIGN_TOP, ALIGN_BOTTOM, ALIGN_LEFT or ALIGN_RIGHT',
                     1,
                     4,
                     ALIGN_TOP,
                     gobject.PARAM_READWRITE)
    }
    def __init__(self, **kwargs):
        """
        Constructor.
        """
        self.property_names = ('align',)
        self.align          = self.ALIGN_TOP
        CanvasTable.__init__(self, **kwargs)


    def do_get_property(self, property):
        if property.name in self.property_names:
            return self.__getattribute__(property.name.replace('-', '_'))
        else:
            raise AttributeError, 'unknown property %s' % property.name


    def do_set_property(self, property, value):
        if property.name in self.property_names:
            return self.__setattr__(property.name.replace('-', '_'), value)
        else:
            raise AttributeError, 'unknown property %s' % property.name


    def _shift(self, matrix, move_func):
        for cell in matrix.get_cells():
            old_pos = matrix.get_pos(cell)
            new_pos = move_func(cell)
            #print "OLD", old_pos, "NEW", new_pos, cell.event.caption
            if old_pos != new_pos:
                self.remove(cell)
                self.add(cell, new_pos[0], new_pos[2], new_pos[1], new_pos[3])


    def add(self, child, left=None, right=None, top=None, bottom=None, flags=0):
        CanvasTable.add(self, child, left, right, top, bottom, flags)
        matrix = self.get_matrix()
        if self.align == self.ALIGN_TOP:
            self._shift(matrix, matrix.move_top)
        elif self.align == self.ALIGN_BOTTOM:
            self._shift(matrix, matrix.move_bottom)
        if self.align == self.ALIGN_LEFT:
            self._shift(matrix, matrix.move_left)
        elif self.align == self.ALIGN_RIGHT:
            self._shift(matrix, matrix.move_right)

gobject.type_register(CanvasMagnetTable)
