#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _zeitgeist.engine
from _zeitgeist.engine import create_engine
from zeitgeist.datamodel import *
from _zeitgeist.json_importer import *

import gobject, gtk
import unittest
from threading import Thread

class RemoteTest(unittest.TestCase):

	def setUp(self):
		_zeitgeist.engine.DB_PATH = ":memory:"
		self.engine = create_engine()
		
		# The remote.py module is hacky so we must import this a bit late
		from _zeitgeist.engine.remote import RemoteInterface
		
		# We run the DBus server in a separate thread
		self.mainloop = gobject.MainLoop()
		self.remote = RemoteInterface()				
		
		def dispatch_mainloop():
			print "hhhhhhhhhhhhh"
			gtk.gdk.threads_enter()
			self.mainloop.run()
			gtk.gdk.threads_leave()
			print "ddddddddd"
		
		print 111111111
		self.engine_thread = Thread(target=dispatch_mainloop)
		self.engine_thread.start()
		print 12121212
		
	def tearDown (self):
		self.engine.close()
		_zeitgeist.engine._engine = None
		print 222222222222
		self.remote.Quit()
		
		# Wait at max 2s and assert that the engine is dead
		print 33333333333333
		self.engine_thread.join(2)
		print 444444444444444
		self.assertFalse(self.engine_thread.isAlive())
	
	def testNothing(self):
		# Simply assert that we start and stop correctly
		pass
	
if __name__ == "__main__":
	unittest.main()
	
