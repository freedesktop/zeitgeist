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

class LayoutBox(object):
    annotation = None
    pull       = 0
    y          = 0
    height     = 0

    def __init__(self, parent, annotation):
        self.parent     = parent
        self.annotation = annotation
        self.annotation.connect('size-allocate', self._on_annotation_allocate)


    def _on_annotation_allocate(self, annotation, rect):
        self.height = rect.height
        self.parent.widget._update_annotations()
