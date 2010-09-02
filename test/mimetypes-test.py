#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.mimetypes import interpretation_for_mimetype, manifestation_for_uri
from zeitgeist.datamodel import Interpretation, Manifestation


class MimetypesTest(unittest.TestCase):
    
    def test_textplain(self):
        self.assertEquals(
            Interpretation.TEXT_DOCUMENT, interpretation_for_mimetype("text/plain")
        )
    
    def test_mime_none(self):
        self.assertEquals(None, interpretation_for_mimetype("boobarbaz"))
    
    def test_mime_regex(self):
        self.assertEquals(
            Interpretation.DOCUMENT,
            interpretation_for_mimetype("application/x-applix-FOOOOBAR!")
        )
        self.assertEquals(
            Interpretation.SPREADSHEET,
            interpretation_for_mimetype("application/x-applix-spreadsheet")
        )
        
class SchemeTest(unittest.TestCase):
    
    def test_scheme_file(self):
        self.assertEquals(
            Manifestation.FILE_DATA_OBJECT,
            manifestation_for_uri("file:///tmp/foo.txt")
        )
        
    def test_scheme_none(self):
        self.assertEquals(None, manifestation_for_uri("boo:///tmp/foo.txt"))
        
	
if __name__ == '__main__':
	unittest.main()
