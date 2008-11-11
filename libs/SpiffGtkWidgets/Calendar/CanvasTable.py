# Copyright (C) 2008 Samuel Abels, http://debain.org
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
import hippo
from TableLayout import TableLayout
from Matrix      import Matrix

class CanvasTable(hippo.CanvasBox):
    def __init__(self, column_spacing=0, row_spacing=0, **kwargs):
        hippo.CanvasBox.__init__(self, **kwargs)

        self.__layout = TableLayout(column_spacing=column_spacing, row_spacing=row_spacing)
        self.set_layout(self.__layout)

    def add(self, child, left=None, right=None, top=None, bottom=None, flags=0):
        self.__layout.add(child, left, right, top, bottom, flags)

    def remove(self, child):
        hippo.CanvasBox.remove(self, child)

    def set_homogeneus_rows(self, homogeneus):
        self.__layout.set_homogeneus_rows(homogeneus)

    def set_homogeneus_columns(self, homogeneus):
        self.__layout.set_homogeneus_columns(homogeneus)

    def set_column_expand(self, column, expand):
        self.__layout.set_column_expand(column, expand)

    def set_row_expand(self, row, expand):
        self.__layout.set_row_expand(row, expand)

    def set_row_count(self, rows):
        self.__layout.set_row_count(rows)

    def set_column_count(self, cols):
        self.__layout.set_column_count(cols)

    def set_size(self, rows, cols):
        self.__layout.set_size(rows, cols)

    def get_size(self):
        rows = self.__layout.get_row_count()
        cols = self.__layout.get_column_count()
        return rows, cols

    def get_total_row_spacing(self):
        return self.__layout.get_total_row_spacing()

    def get_total_column_spacing(self):
        return self.__layout.get_total_column_spacing()

    def shrink(self, rows, cols):
        for child in self.get_children():
            box = self.find_box_child(child)
            if box.bottom > rows or box.right > cols:
                self.remove(child)

    def get_matrix(self):
        rows, cols = self.get_size()
        matrix     = Matrix(rows, cols)
        for child in self.get_children():
            box = self.find_box_child(child)
            matrix.set(child, box.left, box.top, box.right, box.bottom)
        return matrix

    def get_rows(self):
        matrix = self.get_matrix()
        return matrix.get_rows()

    def remove_empty_rows(self):
        pass #FIXME
