# -.- encoding: utf-8 -.-

import os
import glob
import gobject
import shutil
import sqlite3 as db
import gettext

from zeitgeist_base import DataProvider

class EvolutionSource(DataProvider):
	
	def __init__(self, name="Mail", icon="stock_mail", uri="gzg/evolution"):
		DataProvider.__init__(self, name=name, icon=icon, uri = uri)
		self.name = "Mail"
		self.icon="stock_mail"
		self.type = "Mail"
		self.comment = "Mail sent via evolution"
		#self.emit("reload")
		
	def get_items(self):#
		try:
			path = self.__copy_sqlite()
			if path != -1:
				# create a connection to evolution's sqlite database
				self.connection = db.connect(path,True)
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
								"count": u""
								}
					except Exception:
						print "error fetching sent mail"
				cursor.close()
		except Exception:
				pass
	
	def __copy_sqlite(self):
		'''
		Copy the sqlite file to avoid file locks when it's being used by evolution.
		'''
		try:
			historydb = glob.glob(os.path.expanduser("~/.evolution/mail/local/folders.db"))
			newloc = glob.glob(os.path.expanduser("~/.zeitgeist/"))
			newloc = newloc[0]+"evo.sqlite"
			shutil.copy2(historydb[0], newloc)
			return newloc
		except Exception:
			return -1

__datasource__ = EvolutionSource()
