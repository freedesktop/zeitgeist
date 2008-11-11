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
import pango, re
from Feature import Feature

bullet_point_re = re.compile(r'^(?:\d+\.|[\*\-])$')

class ListIndent(Feature):
    """
    This class implements an auto-indent feature for the text buffer.
    """

    def __init__(self, buffer):
        """
        Constructor.
        
        buffer -- the associated TextBuffer
        """
        Feature.__init__(self, buffer)
        self.bullet_point = u'•'
        self.lock_signals = None
        self.start_tag = buffer.create_tag('list-start',
                                           #foreground  = 'lightblue',
                                           left_margin = 30,
                                           pixels_above_lines = 12)
        self.bullet_tag = buffer.create_tag('list-bullet',
                                            #background  = 'orange',
                                            left_margin = 30)
        self.list_tag   = buffer.create_tag('list',
                                            #underline = pango.UNDERLINE_SINGLE,
                                            left_margin        = 30,
                                            pixels_above_lines = 3)
        buffer.connect_after('insert-text',  self._on_buffer_insert_text_after)
        buffer.connect('delete-range',   self._on_buffer_delete_range)
        buffer.connect('mark-set',       self._on_buffer_mark_set)


    def _on_buffer_mark_set(self, buffer, iter, mark):
        if mark.get_name() != 'insert':
            return
        if not iter.has_tag(self.bullet_tag):
            return
        if self.lock_signals:
            return
        self.lock_signals = True
        next = iter.copy()
        next.forward_char()
        if next.has_tag(self.bullet_tag):
            iter.forward_to_tag_toggle(self.bullet_tag)
        else:
            iter.backward_to_tag_toggle(self.bullet_tag)
            iter.backward_char()
        buffer.place_cursor(iter)
        self.lock_signals = False


    def _to_list_start(self, iter):
        self._to_list_item_start(iter)
        while not iter.is_start():
            next = iter.copy()
            next.backward_line()
            if not self._at_bullet_point(next):
                break
            iter = next


    def _to_list_end(self, iter):
        while True:
            self._to_list_item_end(iter)
            iter.forward_char()
            if iter.is_end():
                return
            if not self._at_bullet_point(iter):
                iter.backward_char()
                return


    def _to_list_item_start(self, iter):
        iter.set_line(iter.get_line())


    def _to_list_item_end(self, iter):
        iter.forward_line()
        if iter.is_end():
            return
        iter.backward_char()


    def _at_bullet_point(self, iter):
        end = iter.copy()
        end.forward_find_char(lambda x, d: x == ' ')
        if end.is_end() or end.get_line() != iter.get_line():
            return False
        text = self.buffer.get_text(iter, end)
        if text == self.bullet_point or bullet_point_re.match(text):
            return True
        return False


    def _insert_inside_list(self, buffer, start, end):
        #print "INSERT INSIDE"
        insert_start = buffer.get_iter_at_offset(start)
        insert_end   = buffer.get_iter_at_offset(end)
        text         = buffer.get_text(insert_start, insert_end)
        item_start   = insert_start.copy()
        self._to_list_item_start(item_start)
        list_end     = insert_end.copy()
        self._to_list_end(list_end)
        bullet_end   = item_start.copy()
        bullet_end.forward_to_tag_toggle(self.bullet_tag)
        bullet_point = buffer.get_text(item_start, bullet_end)

        #print "LIST",   repr(buffer.get_text(item_start, list_end))
        #print "BULLET", repr(bullet_point)
        #print "TEXT",   repr(text)
        buffer.apply_tag(self.list_tag, item_start, list_end)
        if text in ('\r', '\n'):
            next_char = list_end.copy()
            next_char.forward_char()
            buffer.remove_tag(self.list_tag, list_end, next_char)
            buffer.insert_with_tags(insert_end,
                                    bullet_point,
                                    self.bullet_tag, self.list_tag)


    def _insert_outside_list(self, buffer, insert_start_off, insert_end_off):
        # Move back to the beginning of the line in which text was inserted.
        #print "INSERT OUTSIDE"
        iter = buffer.get_iter_at_offset(insert_start_off)
        iter.set_line(iter.get_line())

        if not self._at_bullet_point(iter):
            return

        while iter.get_offset() < insert_end_off:
            if not self._at_bullet_point(iter):
                iter.forward_line()
                continue
            start_off = iter.get_offset()

            # Replace the item by a bullet point.
            start     = iter.copy()
            next_char = iter.copy()
            next_char.forward_find_char(lambda x, d: x == ' ')
            buffer.delete(start, next_char)
            buffer.insert(start, self.bullet_point)

            # Mark the bullet point.
            start   = buffer.get_iter_at_offset(start_off)
            end_off = start_off + len(self.bullet_point) + 1
            end     = buffer.get_iter_at_offset(end_off)
            buffer.apply_tag(self.bullet_tag, start, end)

            iter = buffer.get_iter_at_offset(start_off)
            iter.forward_line()

        # Mark the list start.
        start = buffer.get_iter_at_offset(insert_start_off)
        self._to_list_start(start)
        end   = start.copy()
        end.forward_to_tag_toggle(self.bullet_tag)
        buffer.apply_tag(self.start_tag,  start, end)
        buffer.apply_tag(self.bullet_tag, start, end)

        # Mark the entire list.
        self._to_list_end(end)
        buffer.apply_tag(self.list_tag, start, end)


    def _on_buffer_insert_text_after(self, buffer, iter, text, length):
        if self.lock_signals:
            return
        self.lock_signals = True
        end      = iter.get_offset()
        start    = end - len(unicode(text))
        previous = buffer.get_iter_at_offset(start - 1)
        if previous.has_tag(self.list_tag):
            self._insert_inside_list(buffer, start, end)
        else:
            self._insert_outside_list(buffer, start, end)
        self.lock_signals = False


    def _delete_inside_list(self, start, end):
        #print "DELETE INSIDE"
        if not start.has_tag(self.list_tag) and not self._at_bullet_point(end):
            #print "start has no list tag"
            next_item_start = end.copy()
            self._to_list_item_end(next_item_start)
            next_item_start.forward_line()
            self.buffer.remove_tag(self.list_tag, end, next_item_start)

            if self._at_bullet_point(next_item_start):
                bullet_end = next_item_start.copy()
                bullet_end.forward_to_tag_toggle(self.bullet_tag)
                self.buffer.apply_tag(self.start_tag,
                                      next_item_start,
                                      bullet_end)
            return

        if start.has_tag(self.start_tag):
            #print "instart"
            # Delete the old start tag.
            start.backward_to_tag_toggle(self.start_tag)

            # The text of the first item is now no longer a list.
            item_end = end.copy()
            self._to_list_item_end(item_end)
            item_end.forward_char()
            self.buffer.remove_tag(self.list_tag, start, item_end)

            # The start of the next item (if any) is now the start 
            # of the list.
            if not item_end.has_tag(self.bullet_tag):
                return
            bullet_end = item_end.copy()
            bullet_end.forward_to_tag_toggle(self.bullet_tag)
            self.buffer.apply_tag(self.start_tag, item_end, bullet_end)
            return

        if start.has_tag(self.bullet_tag):
            #print "start in bullet"
            start.backward_to_tag_toggle(self.bullet_tag)
            prev_char = start.copy()
            prev_char.backward_char()
            
            next_item = end.copy()
            self._to_list_item_end(next_item)
            next_item.forward_char()
            self.buffer.remove_tag(self.list_tag, prev_char, next_item)

            if next_item.has_tag(self.bullet_tag):
                bullet_end = next_item.copy()
                bullet_end.forward_to_tag_toggle(self.bullet_tag)
                self.buffer.apply_tag(self.start_tag, next_item, bullet_end)

        if end.has_tag(self.bullet_tag):
            #print "end in bullet"
            end.forward_to_tag_toggle(self.bullet_tag)

        end_line = end.copy()
        self._to_list_item_start(end_line)
        if end_line.has_tag(self.bullet_tag):
            return
        next = end.copy()
        self._to_list_item_end(next)
        if not next.is_end():
            next.backward_char()
        self.buffer.apply_tag(self.list_tag, end, next)


    def _delete_outside_list(self, start, end):
        next = start.copy()
        next.forward_char()
        text = self.buffer.get_text(start, next)
        if text not in ('\r', '\n'):
            return
        previous = start.copy()
        previous.backward_char()
        if not previous.has_tag(self.list_tag):
            return
        item_end = end.copy()
        self._to_list_item_end(item_end)
        self.buffer.apply_tag(self.list_tag, end, item_end)


    def _on_buffer_delete_range(self, buffer, start, end):
        if self.lock_signals:
            return
        self.lock_signals = True
        if start.has_tag(self.list_tag) or end.has_tag(self.list_tag):
            self._delete_inside_list(start, end)
        else:
            self._delete_outside_list(start, end)
        self.lock_signals = False
