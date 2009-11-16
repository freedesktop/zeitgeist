#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from _zeitgeist.engine.resonance_engine import ZeitgeistEngine
from _zeitgeist.engine.extension import Extension

import unittest

class _Extension1(Extension):
	__public_methods__ = ["return_hallo", "return_engine"]
		
	def return_hallo(self):
		return "Hallo"
		
	def return_boo(self):
		return "boo"
		
	def return_engine(self):
		return self.engine
	

class TestExtensions(unittest.TestCase):
	
	def testCreateEngine(self):
		engine = ZeitgeistEngine()
		self.assertEqual(len(engine.extensions), 0)
		self.assertRaises(AttributeError, engine.__getattr__, "return_hallo")
		engine.extensions.load(_Extension1)
		self.assertEqual(engine.return_hallo(), "Hallo")
		self.assertRaises(AttributeError, engine.__getattr__, "return_boo")
		self.assertEqual(engine.return_engine(), engine)

if __name__ == "__main__":
	unittest.main()
