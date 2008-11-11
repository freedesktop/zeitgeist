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

class Feature(object):
    """
    This class implements the common base class for all feature classes.
    """

    def __init__(self, buffer):
        """
        Constructor.
        
        buffer -- the associated TextBuffer
        """
        assert buffer is not None
        self.buffer = buffer


    def _print_range(self, start, end):
        print "RANGE:", repr(self.buffer.get_text(start, end))


    def _print_char(self, iter):
        end = iter.copy()
        end.forward_char()
        print "CHAR:", repr(self.buffer.get_text(iter, end))
