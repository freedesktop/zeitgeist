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


class FirefoxData(Data):
	def __init__(self,uri,name,timestamp,count):
		self.uri = uri
		self.name = name
		self.timestamp = timestamp
		self.count = count
		Data.__init__(self,name=name,uri=uri, timestamp = timestamp, count=self.count,  use="visited", type="Firefox History")

class FirefoxSource(DataProvider):
	def __init__(self, name = "Firefox History", icon = "gnome-globe"):
		
		self.items=[]
		DataProvider.__init__(self, name=name, icon=icon)
		self.name = "Firefox History"
		self.icon="firefox"
		#print(cursor)
		#self.emit("reload")
		
	def copy_sqlite(self):

		
	   historydb = glob.glob(os.path.expanduser("~/.mozilla/firefox/*/places.sqlite"))
	   shutil.copy2(historydb[0],"./firefox-history.sqlite")

	
	def get_items_uncached(self):#
		print("reloading firefox history")
		self.copy_sqlite()
		historydb = "./firefox-history.sqlite"
		self.connection = db.connect(historydb,True)
		cursor = self.connection.cursor()
		contents = "id, place_id, visit_date"
		history = cursor.execute("SELECT " +contents+ " FROM moz_historyvisits WHERE visit_type=" +str(2)).fetchall()
		j = 0
		for i in history:
			cursor = self.connection.cursor()
			contents = "id, url, title, visit_count"
			item = cursor.execute("SELECT " +contents+ " FROM moz_places WHERE id="+str(i[1])).fetchall()
			url = item[0][1]
			name = item[0][2]
			count = item[0][3]
			timestamp = history[j][2]
			timestamp = timestamp / (1000000)
			j=j+1
			yield FirefoxData(url,name,timestamp,count)
			del i,url,item,name,count,timestamp
		print("reloading firefox history done")
		cursor.close()
		del history
