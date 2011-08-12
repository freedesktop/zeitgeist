#!/usr/bin/python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2010 Markus Korn <thekorn@gmx.de>
# Copyright © 2011 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import glob
import unittest
import doctest
import logging
import sys
import tempfile
import shutil
import signal

from optparse import OptionParser
from testutils import RemoteTestCase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Find the test/ directory
TESTDIR = os.path.dirname(os.path.abspath(__file__))
DOCTESTS = glob.glob(os.path.join(TESTDIR, "*.rst"))

def doctest_setup(test):
	test._datapath = tempfile.mkdtemp(prefix="zeitgeist.datapath.")
	test._env = os.environ.copy()
	os.environ.update({
		"ZEITGEIST_DATABASE_PATH": ":memory:",
		"ZEITGEIST_DATA_PATH": test._datapath
	})
	test._daemon = RemoteTestCase._safe_start_daemon()
	
def doctest_teardown(test):
	os.kill(test._daemon.pid, signal.SIGKILL)
	test._daemon.wait()
	shutil.rmtree(test._datapath)
	os.environ = test._env
	
def iter_tests(suite):
	for test in suite:
		if isinstance(test, unittest.TestSuite):
			for t in iter_tests(test):
				yield t
		else:
			yield test
			
def get_test_name(test):
	return ".".join((test.__class__.__module__, test.__class__.__name__, test._testMethodName))
	
def load_tests(module, pattern):
	suite = unittest.defaultTestLoader.loadTestsFromModule(module)
	for test in iter_tests(suite):
		name = get_test_name(test)
		if pattern is not None:
			for p in pattern:
				if name.startswith(p):
					yield test
					break
		else:
			yield test
			
def check_name(filename, pattern):
	if pattern is None:
		return True
	for p in pattern:
		if os.path.basename(filename).startswith(p):
			return True
	return False

def compile_suite(pattern=None):
	# Create a test suite to run all tests
	
	# first, add all doctests
	arguments = {
		"module_relative": False,
		"globs": {"sys": sys},
		"setUp": doctest_setup,
		"tearDown": doctest_teardown,
	}
	doctests = filter(lambda x: check_name(str(x), pattern), DOCTESTS)
	suite = doctest.DocFileSuite(*doctests, **arguments)

	# Add all of the tests from each file that ends with "-test.py"
	for fname in os.listdir(TESTDIR):
		if fname.endswith("-test.py"):
			fname = os.path.basename(fname)[:-3] # Get the filename and chop off ".py"
			module = __import__(fname)
			tests = list(load_tests(module, pattern))
			suite.addTests(tests)
	return suite

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-v", action="count", dest="verbosity")
	(options, args) = parser.parse_args()

	if options.verbosity:
		# do more fine grained stuff later
		# redirect all debugging output to stderr
		logging.basicConfig(stream=sys.stderr)
		sys.argv.append('--verbose-subprocess')
	else:
		logging.basicConfig(filename="/dev/null")
	
	from testutils import DBusPrivateMessageBus
	bus = DBusPrivateMessageBus()
	err = bus.run(ignore_errors=True)
	if err:
		print >> sys.stderr, "*** Failed to setup private bus, error was: %s" %err
	else:
		print >> sys.stderr, "*** Testsuite is running using a private dbus bus"
		config = bus.dbus_config.copy()
		config.update({"DISPLAY": bus.DISPLAY, "pid.Xvfb": bus.display.pid})
		print >> sys.stderr, "*** Configuration: %s" %config
	try:
		os.environ["ZEITGEIST_DEFAULT_EXTENSIONS"] = \
			"_zeitgeist.engine.extensions.blacklist.Blacklist," \
			"_zeitgeist.engine.extensions.datasource_registry.DataSourceRegistry"
		suite = compile_suite(args or None)
		# Run all of the tests
		unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
	finally:
		bus.quit(ignore_errors=True)
