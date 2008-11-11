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

class UndoDeleteText(Undoable):
    def __init__(self, buffer, startiter, enditer):
        Undoable.__init__(self, buffer, startiter)
        self.end  = enditer.get_offset()
        self.tags = buffer.get_tags_at_offset(self.start, self.end)
        self.text = buffer.get_text(startiter, enditer)


    def undo(self):
        self.buffer.insert_at_offset(self.start, self.text)
        self.buffer.apply_tags_at_offset(self.tags, self.start, self.end)


    def redo(self):
        self.buffer.delete_range_at_offset(self.start, self.end)
