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
from Undoable import Undoable

class UndoRemoveTag(Undoable):
    def __init__(self, buffer, startiter, enditer, tag):
        Undoable.__init__(self, buffer, startiter)
        self.end      = enditer.get_offset()
        self.old_tags = buffer.get_tags_at_offset(self.start, self.end)
        self.tag      = tag


    def undo(self):
        self.buffer.apply_tags_at_offset(self.old_tags, self.start, self.end)


    def redo(self):
        self.buffer.remove_tag_at_offset(self.tag, self.start, self.end)
