import gc
import datetime
import os
import re
import glob
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError

import gnomevfs
import gobject
import gtk
import shutil
import sqlite3 as db
import tempfile
import W3CDate
from gettext import gettext as _

from zeitgeist_base import Data, DataProvider
from zeitgeist_util import FileMonitor, launcher


class FirefoxSource(DataProvider):
	
	def __init__(self, name="Firefox History", icon="gnome-globe", uri="gzg/firefox"):
		DataProvider.__init__(self, name=name, icon=icon, uri = uri)
		self.name = "Firefox History"
		self.icon="gnome-globe"
		self.type = self.name
		self.comment = "websites visited with Firefox"
		#self.emit("reload")
		
	def copy_sqlite(self):
		'''
		Copy the sqlite file to avoid file locks when it's being used by firefox.
		'''
		
		historydb = glob.glob(os.path.expanduser("~/.mozilla/firefox/*/places.sqlite"))
		newloc = glob.glob(os.path.expanduser("~/.Zeitgeist/"))
		newloc = newloc[0]+"firefox.sqlite"
		shutil.copy2(historydb[0], newloc)
		return newloc
	
	def get_items_uncached(self):#
		path = self.copy_sqlite()
		
		# create a connection to firefox's sqlite database
		self.connection = db.connect(path,True)
		cursor = self.connection.cursor()
		
		# retrieve all urls from firefox history
		contents = "id, place_id, visit_date,visit_type"
		history = cursor.execute("SELECT " + contents + " FROM moz_historyvisits").fetchall()
		
		j = 0
		for i in history:
			# TODO: Fetch full rows above so that we don't need to do another query here
			contents = "id, url, title, visit_count"
			item = cursor.execute("SELECT " + contents +" FROM moz_places WHERE id=" +str(i[1])).fetchall()
			url = item[0][1]
			name = item[0][2]
			count = item[0][3]
			timestamp = history[j][2] / (1000000)
			if history[j][3]==2 or history[j][3]==3 or history[j][3]==5:
				yield Data(uri=url,
						name=name,
						timestamp=timestamp,
						count=count,
						use="visited",
						type="Firefox History")
			
			else:
				yield Data(uri=url,
						name=name,
						timestamp=timestamp,
						count=count,
						use="linked",
						type="Firefox History")
			
			j += 1
			
		cursor.close()