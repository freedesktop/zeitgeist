# -.- coding: utf-8 -.-

# lrucache.py
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2011 Seif Lotfy <seif@lotfy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class LRUCache:
	"""
	A simple LRUCache implementation backed by a linked list and a dict.
	It can be accessed and updated just like a dict. To check if an element
	exists in the cache the following type of statements can be used:
		if "foo" in cache
	"""
	   		
	class _Item:
		"""
		A container for each item in LRUCache which knows about the 
		item's position and relations
		"""
		def __init__(self, item_key, item_value):
			self.value = item_value
			self.key = item_key
			self.next = None
			self.prev = None
	
	def __init__(self, max_size):
		"""
		The size of the cache (in number of cached items) is guaranteed to
		never exceed 'size'
		"""
		self._max_size = max_size
		self.clear()
	
	
	def clear(self):
		self._list_end = None # The newest item
		self._list_start = None # Oldest item
		self._map = {}	
	
	def __len__(self):
		return len(self._map)
	
	def __contains__(self, key):
		return key in self._map
		
	def __delitem__(self, key):
		item = self._map[key]
		if item.prev:
			item.prev.next = item.next
		else:
			# we are deleting the first item, so we need a new first one
			self._list_start = item.next
		if item.next:
			item.next.prev = item.prev
		else:
			# we are deleting the last item, get a new last one
			self._list_end = item.prev
		del self._map[key], item
	
	def __setitem__(self, key, value):
		if key in self._map:
			item = self._map[key]
			item.value = value
			self._move_item_to_end(item)
		else:
			new = LRUCache._Item(key, value)
			self._append_to_list(new)

			if len(self._map) > self._max_size :
				# Remove eldest entry from list
				self.remove_eldest_item()				

	def __getitem__(self, key):
		item = self._map[key]
		self._move_item_to_end(item)
		return item.value
	
	def __iter__(self):
		"""
		Iteration is in order from eldest to newest,
		and returns (key,value) tuples
		"""
		iter = self._list_start
		while iter != None:
			yield (iter.key, iter.value)
			iter = iter.next
	
	def _move_item_to_end(self, item):
		del self[item.key]
		self._append_to_list(item)
	
	def _append_to_list(self, item):
		self._map[item.key] = item
		if not self._list_start:
			self._list_start = item
		if self._list_end:
			self._list_end.next = item
			item.prev = self._list_end
			item.next = None
		self._list_end = item
	
	def remove_eldest_item(self):
		if self._list_start == self._list_end:
			self._list_start = None
			self._list_end = None
			return
		old = self._list_start
		old.next.prev = None
		self._list_start = old.next
		del self[old.key], old
