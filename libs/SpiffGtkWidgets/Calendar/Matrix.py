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
class Matrix(object):
    def __init__(self, rows = -1, cols = -1):
        self.rows   = rows
        self.cols   = cols
        self.matrix = []
        self.resize(max(self.rows, 1), max(self.cols, 1))


    def resize(self, rows, cols):
        old_rows,  old_cols  = self.get_size()
        diff_rows, diff_cols = rows - old_rows, cols - old_cols
        while diff_rows > 0:
            self.matrix.append([None for f in range(old_cols)])
            diff_rows -= 1
        while diff_rows < 0:
            self.matrix.pop()
            diff_rows += 1
        for i in range(rows):
            diff = diff_cols
            while diff > 0:
                self.matrix[i].append(None)
                diff -= 1
            while diff < 0:
                self.matrix[i].pop()
                diff += 1


    def set(self, value, x1, y1, x2, y2):
        assert x1 <= x2
        assert y1 <= y2

        # Make sure that the table is big enough.
        rows, cols = self.get_size()
        if x2 > cols and self.cols != -1:
            msg = 'Adding a cell at column %s in a matrix with %s columns'
            raise Exception(msg % (x2, cols))
        elif y2 > rows and self.rows != -1:
            msg = 'Adding a cell at row %s in a matrix with %s rows'
            raise Exception(msg % (y2, rows))

        # Resize if necessary.
        if x2 > cols or y2 > rows:
            cols = max(cols, x2)
            rows = max(rows, y2)
            self.resize(rows, cols)

        # Allocate the cells to the new child.
        for rownum in range(y1, y2):
            for colnum in range(x1, x2):
                self.matrix[rownum][colnum] = value


    def unset(self, child):
        free_rows = []
        for rownum, row in enumerate(self.matrix):
            for cellnum, cell in enumerate(row):
                if cell == child:
                    row[cellnum] = None

        # Remove free rows from the end of the table.
        if self.rows == -1:
            free_rows = 0
            for rows in reversed(self.matrix):
                if not self._row_is_free(rows):
                    break
                free_rows += 1
            for row in range(free_rows):
                self.matrix.pop()

        # Remove free columns from the end of the table.
        if self.cols == -1:
            free_cols = 0
            for rows in reversed(self.matrix):
                free_cells = 0
                for cell in reversed(row):
                    if cell is not None:
                        break
                    free_cells += 1
                free_cols = min(free_cells, free_cols)
                if free_cols == 0:
                    break
            for row in self.matrix:
                for cell in range(free_cols):
                    row.pop()


    def get_size(self):
        rows = len(self.matrix)
        if rows == 0:
            return 0, 0
        return rows, len(self.matrix[0])


    def get_pos(self, child):
        x1, y1, x2, y2 = -1, -1, -1, -1
        for rownum, row in enumerate(self.matrix):
            for colnum, cell in enumerate(row):
                if cell != child:
                    continue
                if x1 == -1:
                    x1 = colnum
                else:
                    x1 = min(x1, colnum)
                if y1 == -1:
                    y1 = rownum
                else:
                    y1 = min(y1, rownum)
                x2 = max(x2, colnum + 1)
                y2 = max(y2, rownum + 1)
        return x1, y1, x2, y2


    def move_top(self, child):
        x1, y1, x2, y2 = self.get_pos(child)
        while True:
            if y1 <= 0:
                break
            if not self.is_free(x1, y1 - 1, x2, y1):
                break
            self.set(child, x1, y1 - 1, x2, y1)
            self.set(None,  x1, y2 - 1, x2, y2)
            y1 -= 1
            y2 -= 1
        return x1, y1, x2, y2


    def move_bottom(self, child):
        rows, cols     = self.get_size()
        x1, y1, x2, y2 = self.get_pos(child)
        while True:
            if y2 >= rows:
                break
            if not self.is_free(x1, y2, x2, y2 + 1):
                break
            self.set(child, x1, y2, x2, y2 + 1)
            self.set(None,  x1, y1, x2, y1 + 1)
            y1 += 1
            y2 += 1
        return x1, y1, x2, y2


    def move_left(self, child):
        x1, y1, x2, y2 = self.get_pos(child)
        while True:
            if x1 <= 0:
                break
            if not self.is_free(x1 - 1, y1, x1, y2):
                break
            self.set(child, x1 - 1, y1, x1, y2)
            self.set(None,  x2 - 1, y1, x2, y2)
            x1 -= 1
            x2 -= 1
        return x1, y1, x2, y2


    def move_right(self, child):
        rows, cols     = self.get_size()
        x1, y1, x2, y2 = self.get_pos(child)
        while True:
            if x2 >= cols:
                break
            if not self.is_free(x2, y1, x2 + 1, y2):
                break
            self.set(child, x2, y1, x2 + 1, y2)
            self.set(None,  x1, y1, x1 + 1, y2)
            x1 += 1
            x2 += 1
        return x1, y1, x2, y2


    def get_cells(self):
        cells = []
        for row in self.matrix:
            for cell in row:
                if cell is not None and cell not in cells:
                    cells.append(cell)
        return cells


    def get_rows(self):
        rows = []
        for row in self.matrix:
            cells = []
            for cell in row:
                if cell is not None and cell not in cells:
                    cells.append(cell)
            rows.append(cells)
        return rows


    def get_columns(self):
        rows, cols = self.get_size()
        result     = [[] for col in range(cols)]
        for row in self.matrix:
            for colnum, cell in enumerate(row):
                if cell is not None and cell not in result[colnum]:
                    result[colnum].append(cell)
        return result


    def is_free(self, x1, y1, x2, y2):
        for rownum in range(y1, y2):
            for colnum in range(x1, x2):
                if self.matrix[rownum][colnum] is not None:
                    return False
        return True


    def row_is_free(self, row):
        for cell in row:
            if cell is not None:
                return False
        return True


    def dump(self):
        for row in self.matrix:
            for cell in row:
                if cell is None:
                    print "None",
                else:
                    print "CELL",
            print
