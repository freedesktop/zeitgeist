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

class UndoInsertText(Undoable):
    def __init__(self, buffer, startiter, text):
        Undoable.__init__(self, buffer, startiter)
        self.end  = self.start + len(unicode(text))
        self.text = text


    def undo(self):
        self.buffer.delete_range_at_offset(self.start, self.end)


    def redo(self):
        self.buffer.insert_at_offset(self.start, self.text)
