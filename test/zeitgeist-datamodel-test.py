#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from zeitgeist.datamodel import *

import unittest

class CategoryTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Category class
	"""
	def setUp (self):
		pass
		
	def tearDown (self):
		pass
	
	def testAbstractClass(self):
		self.failUnlessRaises(ValueError, Category, "http://example.com/schema#Foo")
		self.failUnlessRaises(ValueError, Category.get, "http://example.com/schema#Foo")
			
	
if __name__ == '__main__':
	unittest.main()
