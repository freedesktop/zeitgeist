#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.mimetypes import get_interpretation_for_mimetype, \
    get_manifestation_for_uri
from zeitgeist.datamodel import Interpretation, Manifestation


class MimetypesTest(unittest.TestCase):
    
    def test_textplain(self):
        self.assertEquals(
            Interpretation.TEXT_DOCUMENT, get_interpretation_for_mimetype("text/plain")
        )
    
    def test_mime_none(self):
        self.assertEquals(None, get_interpretation_for_mimetype("boobarbaz"))
    
    def test_mime_regex(self):
        self.assertEquals(
            Interpretation.DOCUMENT,
            get_interpretation_for_mimetype("application/x-applix-FOOOOBAR!")
        )
        self.assertEquals(
            Interpretation.SPREADSHEET,
            get_interpretation_for_mimetype("application/x-applix-spreadsheet")
        )
        
class SchemeTest(unittest.TestCase):
    
    def test_scheme_file(self):
        self.assertEquals(
            Manifestation.FILE_DATA_OBJECT,
            get_manifestation_for_uri("file:///tmp/foo.txt")
        )
        
    def test_scheme_none(self):
        self.assertEquals(None, get_manifestation_for_uri("boo:///tmp/foo.txt"))
        
	
if __name__ == '__main__':
	unittest.main()
