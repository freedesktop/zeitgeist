#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

import re
from zeitgeist.loggers.datasources.zeitgeist_recent import (SimpleMatch,
	MimeTypeSet, InverseMimeTypeSet)

import unittest


class SimpleMatchTest(unittest.TestCase):
	
	def testmatch(self):
		self.assertTrue(SimpleMatch("boo/*").match("boo/bar"))
		self.assertTrue(SimpleMatch("boo/bar.*").match("boo/bar.foo"))
		self.assertFalse(SimpleMatch("boo/bar.*").match("boo/barfoo"))

class MimeTypeSetTest(unittest.TestCase):
	
	def testinit(self):
		self.assertEquals(repr(MimeTypeSet("boo", "bar", "foo")), "MimeTypeSet('bar', 'boo', 'foo')")
		self.assertEquals(repr(MimeTypeSet("boo", "foo", "foo")), "MimeTypeSet('boo', 'foo')")
		m = MimeTypeSet("boo", SimpleMatch("bar/*"), re.compile("test.*"))
		self.assertEquals(len(m), 3)
		self.assertRaises(ValueError, MimeTypeSet, 1)
		
	def testcontains(self):
		m = MimeTypeSet("boo", SimpleMatch("bar/*"), re.compile("test.*"))
		self.assertTrue("boo" in m)
		self.assertTrue("bar/boo" in m)
		self.assertTrue("testboo" in m)
		self.assertFalse("boobar" in m)
		self.assertFalse("bar" in m)
		
class InverseMimeTypeSetTest(unittest.TestCase):
	
	def testinit(self):
		self.assertEquals(repr(InverseMimeTypeSet("boo", "bar", "foo")), "InverseMimeTypeSet('bar', 'boo', 'foo')")
		self.assertEquals(repr(InverseMimeTypeSet("boo", "foo", "foo")), "InverseMimeTypeSet('boo', 'foo')")
		m = InverseMimeTypeSet("boo", SimpleMatch("bar/*"), re.compile("test.*"))
		self.assertEquals(len(m), 3)
		self.assertRaises(ValueError, InverseMimeTypeSet, 1)
		
	def testcontains(self):
		m = InverseMimeTypeSet("boo", SimpleMatch("bar/*"), re.compile("test.*"))
		self.assertFalse("boo" in m)
		self.assertFalse("bar/boo" in m)
		self.assertFalse("testboo" in m)
		self.assertTrue("boobar" in m)
		self.assertTrue("bar" in m)


if __name__ == '__main__':
	unittest.main()
