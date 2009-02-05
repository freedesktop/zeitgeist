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


class EvolutionSource(DataProvider):
	
	def __init__(self, name="Mail", icon="stock_mail", uri="gzg/evolution"):
		DataProvider.__init__(self, name=name, icon=icon, uri = uri)
		self.name = "Mail"
		self.icon="stock_mail"
		self.type = "Mail"
		self.comment = "Mail sent via evolution"
		#self.emit("reload")
		
	def copy_sqlite(self):
		'''
		Copy the sqlite file to avoid file locks when it's being used by firefox.
		'''
		
		historydb = glob.glob(os.path.expanduser("~/.evolution/mail/local/folders.db"))
		newloc = glob.glob(os.path.expanduser("~/.Zeitgeist/"))
		newloc = newloc[0]+"evo.sqlite"
		shutil.copy2(historydb[0], newloc)
		return newloc
	
	def get_items(self):#
		path = self.copy_sqlite()
		
		# create a connection to firefox's sqlite database
		self.connection = db.connect(path,True)
		cursor = self.connection.cursor()
		
		# retrieve all urls from firefox history
		contents = "dsent, subject, mail_to"
		history = cursor.execute("SELECT " + contents + 
			" FROM Sent").fetchall()
		
		j = 0
		for i in history:
			try:
				if i != None:
					if i[1]==None:
						i[1]==""
					if i[2] == None:
						i[2] ==""
					name = i[1]+" \n"+i[2]
					timestamp = i[0] 
					yield Data(uri="mailto:"+i[2],
								name=name,
								timestamp=timestamp,
								mimetype="mail",
								use="visited",
								type="Mail")
			except:
				print "error fetching sent mail"
		cursor.close()