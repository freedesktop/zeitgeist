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
import copy
import gobject
import hippo

def compute_homogeneus(width, count):
    lengths = []
    while count > 0:
        length = int(float(width) / count)
        lengths.append(length)
        width -= length
        count -= 1
    lengths.append(width)
    return lengths


def compute_lengths(allocated, min_lengths, natural_lengths, expand_map=None):
    count         = len(min_lengths)
    total_natural = sum(natural_lengths)
    to_shrink     = total_natural - allocated

    if to_shrink > 0:
        lengths = copy.copy(natural_lengths)
        # We were allocated less than our natural height. We want to shrink lines
        # as equally as possible, but no line more than it's maximum shrink.
        #
        # To do this, we process the lines in order of the available shrink from
        # least available shrink to most
        #
        shrinks = []
        for i in xrange(0, count):
            shrinks.append((i, natural_lengths[i] - min_lengths[i]))
        shrinks.sort(key=lambda t: t[1])
            
        lines_remaining = count
        for (i, shrink) in shrinks:
            # If we can shrink the rest of the lines equally, do that. Otherwise
            # shrink this line as much as possible
            if shrink * lines_remaining >= to_shrink:
                shrink = to_shrink // lines_remaining
                
            lengths[i] -= shrink
            lines_remaining -= 1
            to_shrink -= shrink
            
        return lengths
    elif to_shrink < 0 and expand_map != None and len(expand_map) > 0:
        expand_count = len(expand_map)
        lengths = copy.copy(natural_lengths)
        to_grow = -to_shrink
            
        for i in xrange(0, count):
            if i in expand_map:
                delta = to_grow // expand_count
                lengths[i] += delta
                to_grow -= delta
                expand_count -= 1

        return lengths
    else:
        return natural_lengths


class TableLayout(gobject.GObject,hippo.CanvasLayout):
    """
    A Canvas Layout manager that arranges items in a grid
    """

    def __init__(self, column_spacing=0, row_spacing=0):
        """
        Create a new TableLayout object
        
        Arguments:
        column_spacing: Spacing between columns of items
        row_spacing: Spacing between rows. This is added between all rows, whether
           they are rows of items or header rows. You can add more spacing above
           or below a header item by setting i's padding.
           
        """

        gobject.GObject.__init__(self)
        self.__box = None
        self.__column_spacing = column_spacing
        self.__row_spacing = row_spacing
        self.__rows = -1
        self.__cols = -1
        self.__homogeneous_rows = False
        self.__homogeneous_cols = False

        self.__expand_rows = {}
        self.__expand_columns = {}

    def add(self, child, left=None, right=None, top=None, bottom=None, flags=0):
        """
        Add an item to the layout.

        Arguments:
        left:
        right:
        top:
        bottom:
        flags: flags to pass to hippo.CanvasBox.append(). Currently, all flags
           passed in are ignored by this layout manager. (default=0)
        """
        if self.__box == None:
            raise Exception("Layout must be set on a box before adding children")

        if left == None and right == None:
            raise Exception("Either right or left must be specified")
            
        if left == None:
            left = right - 1
        elif right == None:
            right = left + 1

        if left < 0:
            raise Exception("Left attach is < 0")
        if right <= left:
            raise Exception("Right attach is <= left attach")
        
        if top == None and bottom == None:
            raise Exception("Either bottom or top must be specified")

        if top == None:
            top = bottom - 1
        elif bottom == None:
            bottom = top + 1
            
        if top < 0:
            raise Exception("Top attach is < 0")
        if bottom <= top:
            raise Exception("Bottom attach is <= top")
        
        self.__box.append(child, flags=flags)
        box_child = self.__box.find_box_child(child)
        box_child.left = left
        box_child.right = right
        box_child.top = top
        box_child.bottom = bottom

    def __set_expand(self, expands, i, expand):
        if expand:
            expands[i] = True
        else:
            try:
                del expands[column]
            except KeyError:
                pass

    def set_column_expand(self, column, expand):
        self.__set_expand(self.__expand_columns, column, expand)

    def set_row_expand(self, row, expand):
        self.__set_expand(self.__expand_rows, row, expand)

    def set_row_count(self, rows):
        self.__rows = rows

        # Remove items from the expand map, if necessary.
        expand = self.__expand_rows
        self.__expand_rows = {}
        for row in expand:
            if row < self.__rows:
                self.__expand_rows[row] = True

    def set_column_count(self, cols):
        self.__cols = cols

        # Remove items from the expand map, if necessary.
        expand = self.__expand_columns
        self.__expand_columns = {}
        for col in expand:
            if col < self.__cols:
                self.__expand_columns[col] = True

    def set_size(self, rows, cols):
        self.set_row_count(rows)
        self.set_column_count(cols)

    def set_homogeneus_rows(self, homogeneus):
        self.__homogeneous_rows = homogeneus

    def set_homogeneus_columns(self, homogeneus):
        self.__homogeneous_cols = homogeneus

    def do_set_box(self, box):
        self.__box = box

    def get_column_count(self):
        columns = max(0, self.__cols)
        
        for box_child in self.__box.get_layout_children():
            columns = max(columns, box_child.right)

        for column in self.__expand_columns:
            columns = max(columns, column + 1)

        return columns
    
    def get_row_count(self):
        rows = max(0, self.__rows)
        
        for box_child in self.__box.get_layout_children():
            rows = max(rows, box_child.bottom)

        for row in self.__expand_rows:
            rows = max(rows, row + 1)

        return rows

    def __get_total_column_spacing(self, count):
        if count > 1:
            return (count - 1) * self.__column_spacing
        else:
            return 0
    
    def __get_total_row_spacing(self, count):
        if count > 1:
            return (count - 1) * self.__row_spacing
        else:
            return 0
    
    def get_total_column_spacing(self):
        return self.__get_total_column_spacing(self.get_column_count())
    
    def get_total_row_spacing(self):
        return self.__get_total_row_spacing(self.get_row_count())
    
    def __get_request(self, count, get_start_end, get_request):
        min_lengths = [0 for i in xrange(0,count)]
        natural_lengths = [0 for i in xrange(0,count)]

        # First process non-spanned children
        for box_child in self.__box.get_layout_children():
            start, end = get_start_end(box_child)
            if end != start + 1:
                continue
            
            (min_length, natural_length) = get_request(box_child)

            min_lengths[start] = max(min_lengths[start], min_length)
            natural_lengths[start] = max(natural_lengths[start], natural_length)

        # Then process spanned children
        for box_child in self.__box.get_layout_children():
            start, end = get_start_end(box_child)
            
            if end == start + 1:
                continue
            
            (min_length, natural_length) = get_request(box_child)

            current_min_length = 0
            current_natural_length = 0
            for i in range(start, end):
                current_min_length += min_lengths[i]
                current_natural_length += natural_lengths[i]

            if current_min_length < min_length:
                excess = min_length - current_min_length
                child_count = end - start

                for i in range(start, end):
                    delta = excess // child_count
                    min_lengths[i] += delta
                    excess -= delta
                    child_count -= 1
                    
            if current_natural_length < natural_length:
                excess = natural_length - current_natural_length
                child_count = end - start

                for i in range(start, end):
                    delta = excess // child_count
                    natural_lengths[i] += delta
                    excess -= delta
                    child_count -= 1

        return (min_lengths, natural_lengths)

    def do_get_width_request(self):
        column_count         = self.get_column_count()
        total_column_spacing = self.__get_total_column_spacing(column_count)

        (min_widths, natural_widths) = self.__get_request(column_count,
                                                          lambda box_child: (box_child.left, box_child.right),
                                                          lambda box_child: box_child.get_width_request())

        if self.__homogeneous_cols:
            max_min_width = 0
            for width in min_widths:
                max_min_width = max(max_min_width, width)
            max_nat_width = 0
            for width in natural_widths:
                max_nat_width = max(max_nat_width, width)
            min_widths     = [max_min_width] * column_count
            natural_widths = [max_nat_width] * column_count

        self.__min_widths     = min_widths
        self.__natural_widths = natural_widths

        return (sum(self.__min_widths) + total_column_spacing, sum(self.__natural_widths) + total_column_spacing)

    def __compute_column_widths(self, width):
        cols = max(self.__cols, len(self.__min_widths))
        if self.__homogeneous_cols and width > 0 and cols > 0:
            return compute_homogeneus(width, cols)
        return compute_lengths(width, self.__min_widths, self.__natural_widths, self.__expand_columns)
        
    def do_get_height_request(self, width):
        row_count            = self.get_row_count()
        total_row_spacing    = self.__get_total_row_spacing(row_count)
        total_column_spacing = self.get_total_column_spacing()
        widths               = self.__compute_column_widths(width - total_column_spacing)

        def get_child_height_request(box_child):
            child_width = 0
            for i in xrange(box_child.left, box_child.right):
                child_width += widths[i]

            return box_child.get_height_request(child_width)

        (min_heights, natural_heights) = self.__get_request(row_count,
                                                            lambda box_child: (box_child.top, box_child.bottom),
                                                            get_child_height_request)

        self.__min_heights = min_heights
        self.__natural_heights = natural_heights

#        _logger.debug("height_request: min_heights=%s, natural_heights=%s", min_heights, natural_heights)
        
        return (sum(self.__min_heights) + total_row_spacing, sum(self.__natural_heights) + total_row_spacing)

    def __compute_row_heights(self, height):
        rows = self.get_row_count()
        if self.__homogeneous_rows and height > 0 and rows > 0:
            return compute_homogeneus(height, rows)
        return compute_lengths(height, self.__min_heights, self.__natural_heights, self.__expand_rows)
    
    def do_allocate(self, x, y, width, height, requested_width, requested_height, origin_changed):
        column_count = len(self.__min_widths)
        total_column_spacing = self.__get_total_column_spacing(column_count)
        
        row_count = len(self.__min_heights)
        total_row_spacing = self.__get_total_row_spacing(row_count)

        widths = self.__compute_column_widths(width - total_column_spacing)
        heights = self.__compute_row_heights(height - total_row_spacing)
            
#        _logger.debug("allocate: widths=%s, heights=%s", widths, heights)
        
        x = 0
        xs = []
        for width in widths:
            xs.append(x)
            x += width + self.__column_spacing
        xs.append(x)

        y = 0
        ys = []
        for height in heights:
            ys.append(y)
            y += height + self.__row_spacing
        ys.append(y)
        
        for box_child in self.__box.get_layout_children():
            x = xs[box_child.left]
            width = xs[box_child.right] - x - self.__column_spacing
            y = ys[box_child.top]
            height = ys[box_child.bottom] - y - self.__row_spacing

            box_child.allocate(x, y, width, height, origin_changed)

gobject.type_register(TableLayout)
