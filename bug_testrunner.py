import os
import glob
from subprocess import Popen

tests = map(lambda x: os.path.basename(x).rsplit(".", 1)[0], glob.glob("test/*.rst"))
tests += map(lambda x: os.path.basename(x).rsplit(".", 1)[0], glob.glob("test/*-test.py"))

for test in tests:
    print "*****************", test
    Popen(["test/run-all-tests.py", test, "blacklist-test"]).wait()
