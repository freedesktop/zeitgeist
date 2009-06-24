#!/usr/bin/python

import os
import unittest

# Create a test suite to run all tests
suite = unittest.TestSuite()

# Find the test/ directory
testdir = os.path.dirname(os.path.abspath(__file__))

# Add all of the tests from each file that ends with "-test.py"
for fname in os.listdir(testdir):
	if fname.endswith("-test.py") and not fname.endswith("run-all-tests.py"):
		fname = os.path.basename(fname)[:-3] # Get the filename and chop off ".py"
		module = __import__(fname)
		suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))

# Run all of the tests
unittest.TextTestRunner(verbosity=2).run(suite)
