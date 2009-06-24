# -.- encoding: utf-8 -.-

# lrucache.py
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
#
# This module was inspired by *but not copied* from Evan Prodromou's
# lrucache.py. The reason for not using Evan's work is because it
# is licensed under the Academic Free License 2.1 which is not GPL compatible
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from heapq import heappush, heappop, heapreplace, heapify

class LRUCache:
	"""A simple LRUCache implementation backed by a heap and a dict. It can be
	   accessed and updated just like a dict. To check if an element exists
	   in the cache the 'if "foo" in cache' type of statements can be used."""
	
	class _Item:
		
		def __init__(self, item_id, item_key, item_value):
			self.id = item_id
			self.value = item_value
			self.key = item_key
	
		def __cmp__(self, item):
			return cmp(self.id, item.id)
	
	def __init__(self, max_size):
		"""The size of the cache (in number of cached items) is guaranteed to
		   never exceed 'size'"""
		self._max_size = max_size
		self._heap = []
		self._map = {}
		self._current_id = 0
	
	def __len__(self):
		return len(self._map)
	
	def __contains__(self, key):
		return key in self._map
	
	def __setitem__(self, key, value):
		if key in self._map:
			item = self._map[key]
			item.id = self._current_id
			item.value = value
			heapify(self._heap)			
		elif self._current_id > self._max_size - 1:
			new = LRUCache._Item(self._current_id, key, value)
			old = heapreplace(self._heap, new)
			del self._map[old.key]
			self._map[key] = new
		else:
			new = LRUCache._Item(self._current_id, key, value)
			self._map[key] = new
			heappush(self._heap, new)
		
		self._current_id += 1
	
	def __getitem__(self, key):
		item = self._map[key]
		item.id = self._current_id
		heapify(self._heap)
		self._current_id += 1
		return item.value
	
	def __iter__(self):
		"""Iteration is not in any particular order!"""
		for item in self._heap:
			yield item.value
