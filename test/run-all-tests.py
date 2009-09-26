#!/usr/bin/python

import os
import glob
import unittest
import doctest
import logging

# hide logging output
logging.basicConfig(filename="/dev/null")

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _zeitgeist.engine import get_engine_type, AVAILABLE_ENGINES

# Find the test/ directory
testdir = os.path.dirname(os.path.abspath(__file__))
doctests = glob.glob(os.path.join(testdir, "*.rst"))

# Create a test suite to run all tests
# FIXME: This doesn't work with Python 2.5
#suite = doctest.DocFileSuite(*doctests, module_relative=False, globs={"sys": sys})
suite = unittest.TestSuite()

# We will only run the tests suitable for the selected engine type
IGNORE_STRINGS = ["-%s-" % engine for engine in AVAILABLE_ENGINES
	if engine != get_engine_type()]

def is_ignored_test(filename):
	for text in IGNORE_STRINGS:
		if text in filename:
			return True
	return False

# Add all of the tests from each file that ends with "-test.py"
for fname in os.listdir(testdir):
	if fname.endswith("-test.py") and not is_ignored_test(fname):
		fname = os.path.basename(fname)[:-3] # Get the filename and chop off ".py"
		module = __import__(fname)
		suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))

# Run all of the tests
unittest.TextTestRunner(verbosity=2).run(suite)
