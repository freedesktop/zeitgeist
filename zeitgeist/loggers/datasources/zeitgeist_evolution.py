# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import glob
import gobject
import shutil
import sqlite3 as db
import gettext
from xdg import BaseDirectory

from zeitgeist.loggers.zeitgeist_base import DataProvider

class EvolutionSource(DataProvider):
	
	def __init__(self, name="Mail", icon="stock_mail", uri="gzg/evolution"):
		
		DataProvider.__init__(self, name = name, icon = icon, uri = uri)
		
		self.name = "Mail"
		self.icon="stock_mail"
		self.type = "Mail"
		self.comment = "Mail sent via evolution"
	
	def get_items(self):
		try:
			path = self.__copy_sqlite()
			if path != -1:
				# create a connection to evolution's sqlite database
				self.connection = db.connect(path, True)
				cursor = self.connection.cursor()
				
				# retrieve all urls from evolution's history
				contents = "dsent, subject, mail_to"
				history = cursor.execute("SELECT " + contents + 
					" FROM Sent").fetchall()
				
				for i in history:
					try:
						if i != None:
							if i[1]==None:
								i[1]==""
							if i[2] == None:
								i[2] ==""
							name = i[1]+" \n"+i[2]
							timestamp = i[0] 
							yield {
								"timestamp": timestamp,
								"uri": unicode("mailto:%s" % i[2]),
								"name": unicode(name),
								"use": u"visited",
								"type": u"Mail",
								"icon": unicode(self.icon),
								"comment": u"",
								"mimetype": u"mail",
								"tags": u"",
								"app": u"Evolution",
								}
					except Exception:
						print "error fetching sent mail"
				cursor.close()
		except Exception:
				pass
	
	def __copy_sqlite(self):
		"""
		Copy the sqlite file to avoid file locks when it's being used by evolution.
		"""
		try:
			historydb = glob.glob(os.path.expanduser(
				"~/.evolution/mail/local/folders.db"))
			path = os.path.join(BaseDirectory.xdg_cache_home, "zeitgeist")
			if not os.path.isdir(path):
				os.mkdir(path)
			newloc = os.path.join(path, "firefox.sqlite")
			shutil.copy2(historydb[0], newloc)
			return newloc
		except Exception:
			return -1

__datasource__ = EvolutionSource()
