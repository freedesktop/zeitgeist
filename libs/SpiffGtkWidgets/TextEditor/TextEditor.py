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
import cairo
from SpiffGtkWidgets import color
from TextBuffer      import TextBuffer
from Layout          import Layout

class TextEditor(gtk.TextView):
    def __init__(self, textbuffer = None, *args, **kwargs):
        if textbuffer is None:
            textbuffer = TextBuffer()
        gtk.TextView.__init__(self, textbuffer, *args, **kwargs)
        self.anno_width       = 200
        self.anno_padding     = 10
        self.anno_layout      = Layout(self)
        self.annotations      = {}
        self.show_annotations = True
        self.set_right_margin(50 + self.anno_padding)
        self.connect('expose_event', self._on_expose_event)
        self.get_buffer().connect('mark-set', self._on_buffer_mark_set)
        self.set_wrap_mode(gtk.WRAP_WORD)


    def _on_buffer_mark_set(self, buffer, iter, mark):
        self._update_annotations()


    def _on_expose_event(self, widget, event):
        text_window = widget.get_window(gtk.TEXT_WINDOW_TEXT)
        if event.window != text_window:
            return

        # Create the cairo context.
        ctx = event.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        ctx.rectangle(event.area.x,
                      event.area.y,
                      event.area.width,
                      event.area.height)
        ctx.clip()

        self.draw(ctx, *event.window.get_size())


    def draw(self, ctx, w, h):
        if ctx is None:
            return
        if not self.show_annotations:
            return

        # Draw the dashes that connect annotations to their marker.
        ctx.set_line_width(1)
        ctx.set_dash((3, 2))
        right_margin = self.get_right_margin()
        for annotation in self.anno_layout.get_children():
            mark_x, mark_y = self._get_annotation_mark_position(annotation)
            anno_x, anno_y = self.anno_layout.get_annotation_position(annotation)
            anno_x, anno_y, anno_w, anno_h = annotation.get_allocation()
            path = [(mark_x,           mark_y - 5),
                    (mark_x,           mark_y),
                    (w - right_margin, mark_y),
                    (w,                anno_y + anno_h / 2)]

            stroke_color = annotation.get_border_color()
            ctx.set_source_rgba(*color.to_rgba(stroke_color))
            ctx.move_to(*path[0])
            for x, y in path[1:]:
                ctx.line_to(x, y)
            ctx.stroke()


    def _get_annotation_mark_offset(self, annotation1, annotation2):
        iter1 = self.get_buffer().get_iter_at_mark(annotation1.mark)
        iter2 = self.get_buffer().get_iter_at_mark(annotation2.mark)
        off1  = iter1.get_line()
        off2  = iter2.get_line()
        if off1 == off2:
            return iter2.get_offset() - iter1.get_offset()
        return off1 - off2


    def _get_annotation_mark_position(self, annotation):
        iter           = self.get_buffer().get_iter_at_mark(annotation.mark)
        rect           = self.get_iter_location(iter)
        mark_x, mark_y = rect.x, rect.y + rect.height
        return self.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
                                            mark_x,
                                            mark_y)


    def _update_annotation(self, annotation):
        # Resize the annotation.
        item_width = self.anno_width - 2 * self.anno_padding
        annotation.set_size_request(item_width, -1)

        # Find the x, y of the annotation's mark.
        mark_x, mark_y = self._get_annotation_mark_position(annotation)
        self.anno_layout.pull(annotation, mark_y)


    def _update_annotation_area(self):
        # Update the width and color of the annotation area.
        self.set_border_window_size(gtk.TEXT_WINDOW_RIGHT, self.anno_width)
        bg_color = self.get_style().base[gtk.STATE_NORMAL]
        window   = self.get_window(gtk.TEXT_WINDOW_RIGHT)
        window.set_background(bg_color)


    def _update_annotations(self):
        if not self.show_annotations:
            return

        # Sort the annotations by line/char number and update them.
        iter   = self.get_buffer().get_end_iter()
        rect   = self.get_iter_location(iter)
        height = rect.y + rect.height
        self.anno_layout.sort(self._get_annotation_mark_offset)
        for annotation in self.anno_layout.get_children():
            self._update_annotation(annotation)
        self.anno_layout.update(self.anno_width, height)

        # Update lines.
        self.queue_draw()


    def set_annotation_area_width(self, width, padding = 10):
        self.anno_width   = width
        self.anno_padding = padding
        self._update_annotations()


    def add_annotation(self, annotation):
        self.annotations[annotation.mark] = annotation
        if self.show_annotations == False:
            return

        self._update_annotation_area()
        self.anno_layout.add(annotation)
        self.add_child_in_window(annotation,
                                 gtk.TEXT_WINDOW_RIGHT,
                                 self.anno_padding,
                                 0)
        self._update_annotations()


    def remove_annotation(self, annotation):
        self.anno_layout.remove(annotation)
        del self.annotations[annotation.mark]
        self.remove(annotation)


    def set_show_annotations(self, active = True):
        if self.show_annotations == active:
            return

        # Unfortunately gtk.TextView deletes all children from the 
        # border window if its size is 0. So we must re-add them when the 
        # window reappears.
        self.show_annotations = active
        if active:
            for annotation in self.annotations.itervalues():
                self.add_annotation(annotation)
        else:
            for annotation in self.annotations.itervalues():
                self.anno_layout.remove(annotation)
                self.remove(annotation)
            self.set_border_window_size(gtk.TEXT_WINDOW_RIGHT, 0)
