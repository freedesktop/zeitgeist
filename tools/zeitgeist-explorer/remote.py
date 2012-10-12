# -.- coding: utf-8 -.-
#
# Zeitgeist Explorer
#
# Copyright © 2011-2012 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time

from zeitgeist.client import ZeitgeistClient
from zeitgeist.datamodel import *

__all__ = ['get_interface']

class CustomSubject(Subject):

	@property
	def interp_string(self):
		try:
			return Interpretation[self.interpretation].display_name
		except (KeyError, AttributeError):
			return None

	@property
	def manif_string(self):
		try:
			return Manifestation[self.manifestation].display_name
		except (KeyError, AttributeError):
			return None

class CustomEvent(Event):

	_subject_type = CustomSubject

	@property
	def date_string(self):
		return time.ctime(int(self.timestamp) / 1000)

	@property
	def interp_string(self):
		try:
			return Interpretation[self.interpretation].display_name
		except (KeyError, AttributeError):
			return None

	@property
	def manif_string(self):
		try:
			return Manifestation[self.manifestation].display_name
		except (KeyError, AttributeError):
			return None

_zg = None
def get_interface():
	global _zg
	if _zg is None:
		_zg = ZeitgeistClient()
        _zg.register_event_subclass(CustomEvent)
	return _zg
