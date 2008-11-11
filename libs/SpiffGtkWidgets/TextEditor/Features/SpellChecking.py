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
import pango, re, enchant
from Feature         import Feature
from SpiffGtkWidgets import color

class SpellChecking(Feature):
    """
    This class implements a spell checking feature for the text buffer.
    This code is deprecated and you are advised to use gtkspell instead.
    """

    def __init__(self, buffer, language):
        """
        Constructor.
        
        buffer -- the associated TextBuffer
        language -- the spell checking language
        """
        Feature.__init__(self, buffer)
        if type(language) != type([]):
            language = [language]
        self.dicts         = []
        self.changed_lines = []
        self.tag           = buffer.create_tag('incorrect',
                                               underline  = pango.UNDERLINE_SINGLE,
                                               foreground = 'red')
        buffer.connect('insert-text',  self._on_buffer_insert_text)
        buffer.connect('delete-range', self._on_buffer_delete_range_after)
        buffer.connect('changed',      self._on_buffer_changed)
        for lang in language:
            self.dicts.append(enchant.Dict(lang))


    def correct(self, word):
        for dict in self.dicts:
            if dict.check(word):
                return True
        return False


    def _check_range(self, start, end):
        if not start.starts_word():
            start.forward_word_end()
            start.backward_word_start()

        end_off  = end.get_offset()
        word_end = start.copy()
        word_end.forward_word_end()
        while True:
            text = self.buffer.get_text(start, word_end)
            if self.correct(text):
                self.buffer.remove_tag(self.tag, start, word_end)
            else:
                self.buffer.apply_tag(self.tag, start, word_end)
            if word_end.get_offset() >= end_off:
                break
            word_end.forward_word_end()
            if not word_end.ends_word():
                break
            start = word_end.copy()
            start.backward_word_start()


    def _on_buffer_insert_text(self, buffer, iter, text, length):
        self.changed_lines.append(iter.get_line())


    def _on_buffer_delete_range_after(self, buffer, start, end):
        self.changed_lines += range(start.get_line(), end.get_line() + 1)


    def _on_buffer_changed(self, buffer):
        for line in self.changed_lines:
            start = buffer.get_iter_at_line_offset(line, 0)
            end   = start.copy()
            end.forward_to_line_end()
            self._check_range(start, end)
        self.changed_lines = []
