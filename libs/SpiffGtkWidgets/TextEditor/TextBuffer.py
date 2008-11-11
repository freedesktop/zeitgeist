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
import gtk, pango, time, gobject
from UndoInsertText import UndoInsertText
from UndoDeleteText import UndoDeleteText
from UndoApplyTag   import UndoApplyTag
from UndoRemoveTag  import UndoRemoveTag
from UndoCollection import UndoCollection
import Features

class TextBuffer(gtk.TextBuffer):
    def __init__(self, *args, **kwargs):
        gtk.TextBuffer.__init__(self, *args)
        self.undo_stack      = []
        self.redo_stack      = []
        self.current_undo    = UndoCollection(self)
        self.lock_undo       = False
        self.max_undo        = 250
        self.max_redo        = 250
        self.undo_freq       = 300 # minimum milliseconds between actions
        self.undo_timeout_id = None
        self.user_action     = 0
        self.active_features = []
        self.connect('insert-text',       self._on_insert_text)
        self.connect('delete-range',      self._on_delete_range)
        self.connect('apply-tag',         self._on_apply_tag)
        self.connect('remove-tag',        self._on_remove_tag)
        self.connect('begin-user-action', self._on_begin_user_action)
        self.connect('end-user-action',   self._on_end_user_action)

        features = (
            ('list-indent', True, Features.ListIndent, ()),
        )
        for name, default, feature, feature_args in features:
            active = kwargs.get(name, default)
            if active:
                self.activate_feature(feature, *feature_args)
        self._update_timestamp()


    def activate_feature(self, feature, *args):
        self.active_features.append(feature(self, *args))


    def _cancel_undo_timeout(self):
        if self.undo_timeout_id is None:
            return
        gobject.source_remove(self.undo_timeout_id)
        self.undo_timeout_id = None
        self.end_user_action()


    def _update_timestamp(self):
        if self.undo_timeout_id is not None:
            gobject.source_remove(self.undo_timeout_id)
        else:
            self.begin_user_action()
        self.undo_timeout_id = gobject.timeout_add(self.undo_freq,
                                                   self._cancel_undo_timeout)


    def _on_insert_text(self, buffer, start, text, length):
        if self.lock_undo:
            return
        self._update_timestamp()
        item = UndoInsertText(self, start, text)
        self.current_undo.add(item)
        self.emit('undo-stack-changed')


    def _on_delete_range(self, buffer, start, end):
        if self.lock_undo:
            return
        self._update_timestamp()
        item = UndoDeleteText(self, start, end)
        self.current_undo.add(item)


    def _on_apply_tag(self, buffer, tag, start, end):
        if self.lock_undo:
            return
        self._update_timestamp()
        item = UndoApplyTag(self, start, end, tag)
        self.current_undo.add(item)


    def _on_remove_tag(self, buffer, tag, start, end):
        if self.lock_undo:
            return
        self._update_timestamp()
        item = UndoRemoveTag(self, start, end, tag)
        self.current_undo.add(item)


    def _on_begin_user_action(self, buffer):
        self.user_action += 1


    def _on_end_user_action(self, buffer):
        self.user_action -= 1
        if self.user_action != 0:
            return
        if self.current_undo is None:
            return
        if len(self.current_undo.children) == 0:
            return
        self._undo_add(self.current_undo)
        self.redo_stack = []
        self.current_undo = UndoCollection(self)


    def _undo_add(self, item):
        self.undo_stack.append(item)
        while len(self.undo_stack) >= self.max_undo:
            self.undo_stack.pop(0)
        self.emit('undo-stack-changed')


    def _redo_add(self, item):
        self.redo_stack.append(item)
        while len(self.redo_stack) >= self.max_redo:
            self.redo_stack.pop(0)
        self.emit('undo-stack-changed')


    def insert_at_offset(self, offset, text):
        iter = self.get_iter_at_offset(offset)
        self.insert(iter, text)


    def delete_range_at_offset(self, start, end):
        start = self.get_iter_at_offset(start)
        end   = self.get_iter_at_offset(end)
        self.delete(start, end)


    def apply_tag_at_offset(self, tag, start, end):
        start = self.get_iter_at_offset(start)
        end   = self.get_iter_at_offset(end)
        self.apply_tag(tag, start, end)


    def remove_tag_at_offset(self, tag, start, end):
        start = self.get_iter_at_offset(start)
        end   = self.get_iter_at_offset(end)
        self.remove_tag(tag, start, end)


    def get_tags_at_offset(self, start, end):
        taglist = []
        iter    = self.get_iter_at_offset(start)
        while True:
            taglist.append(iter.get_tags())
            iter.forward_char()
            if iter.get_offset() >= end:
                break
        return taglist


    def apply_tags_at_offset(self, taglist, start, end):
        end   = self.get_iter_at_offset(start + 1)
        start = self.get_iter_at_offset(start)
        for tags in taglist:
            for tag in tags:
                self.apply_tag(tag, start, end)
            start.forward_char()
            end.forward_char()


    def can_undo(self):
        if self.current_undo is not None \
          and len(self.current_undo.children) > 0:
            return True
        return len(self.undo_stack) > 0


    def undo(self):
        self._cancel_undo_timeout()
        if len(self.undo_stack) == 0:
            return
        self.lock_undo = True
        item = self.undo_stack.pop()
        item.undo()
        self._redo_add(item)
        self.lock_undo = False


    def can_redo(self):
        return len(self.redo_stack) > 0


    def redo(self):
        self._cancel_undo_timeout()
        if len(self.redo_stack) == 0:
            return
        self.lock_undo = True
        item = self.redo_stack.pop()
        item.redo()
        self._undo_add(item)
        self.lock_undo = False


gobject.signal_new('undo-stack-changed',
                   TextBuffer,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   ())

gobject.type_register(TextBuffer)
