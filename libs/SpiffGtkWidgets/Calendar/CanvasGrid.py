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
from CanvasTable import CanvasTable

class CanvasGrid(CanvasTable):
    """
    A table item that automatically retrieves the cell content from a given 
    data provider.
    """
    def __init__(self, provider, **kwargs):
        """
        Constructor.
        """
        CanvasTable.__init__(self, 1, 1)
        self.provider = provider


    def _new_cell(self):
        cell = self.provider()
        return cell


    def _add_line(self, length):
        rows, cols = self.get_size()
        for colnum in range(length):
            self.set_column_expand(colnum, True)
            self.add(self._new_cell(), colnum, colnum + 1, rows, rows + 1)
        self.set_row_expand(rows, True)


    def _add_column(self):
        rows, cols = self.get_size()
        for rownum in range(rows):
            self.add(self._new_cell(), cols, cols + 1, rownum, rownum + 1)


    def set_size(self, rows, cols):
        old_rows, old_cols = self.get_size()

        # Create new cells if the new size is bigger.
        if rows > old_rows:
            for rownum in range(old_rows, rows):
                self._add_line(cols)
        if cols > old_cols:
            for x in range(old_cols, cols):
                self._add_column()

        # Remove cells if the new size is smaller.
        self.shrink(rows, cols)
        CanvasTable.set_size(self, rows, cols)
