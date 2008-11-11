# -*- coding: UTF-8 -*-
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
from LayoutBox import LayoutBox

class Layout(object):
    def __init__(self, widget, *args, **kwargs):
        self.widget      = widget
        self.annotations = []
        self.boxes       = {}
        self.padding     = kwargs.get('padding', 0)


    def add(self, annotation):
        self.annotations.append(annotation)
        self.boxes[annotation] = LayoutBox(self, annotation)


    def remove(self, annotation):
        self.annotations.remove(annotation)
        del self.boxes[annotation]


    def pull(self, annotation, position):
        self.boxes[annotation].pull = position


    def sort(self, sort_func):
        self.annotations.sort(sort_func)


    def get_children(self):
        return self.annotations


    def get_annotation_position(self, annotation):
        box = self.boxes[annotation]
        return self.padding, box.y


    def _try_move_up(self, number, delta):
        if delta == 0:
            return
        annotation = self.annotations[number]
        box        = self.boxes[annotation]
        if number == 0:
            box.y = max(0, box.y - delta)
            return
        previous_annotation = self.annotations[number - 1]
        previous_box        = self.boxes[previous_annotation]
        previous_box_end    = previous_box.y + previous_box.height
        possible_delta      = max(0, box.y - previous_box_end)
        if possible_delta >= delta:
            box.y -= delta
            return
        box.y -= possible_delta
        if possible_delta != delta:
            self._try_move_up(number - 1, (delta - possible_delta) / 2)
            box.y = previous_box.y + previous_box.height


    def _dbg(self, action, number):
        return
        annotation = self.annotations[number]
        box        = self.boxes[annotation]
        values     = action, number, box.height, box.pull, box.y
        print "%s: Box %d (h%d) with pull %d is at %d" % values


    def update(self, width, height):
        for n, annotation in enumerate(self.annotations):
            box   = self.boxes[annotation]
            box.y = max(0, box.pull - box.height / 2)
            self._dbg('default', n)

            if n == 0:
                continue

            previous_annotation = self.annotations[n - 1]
            previous_box        = self.boxes[previous_annotation]
            previous_box_end    = previous_box.y + previous_box.height
            if previous_box_end >= box.y:
                self._dbg('moving', n - 1)
                self._try_move_up(n - 1, (previous_box_end - box.y) / 2)
                self._dbg('moved', n - 1)
                box.y = previous_box.y + previous_box.height
                self._dbg('moved', n)

        for n, annotation in enumerate(self.annotations):
            box = self.boxes[annotation]
            self._dbg('showing', n)
            self.widget.move_child(annotation, self.padding, box.y)
