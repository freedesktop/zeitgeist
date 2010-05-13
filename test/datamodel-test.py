#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.datamodel import *
from zeitgeist.datamodel import Symbol
from testutils import parse_events


class SymbolTest(unittest.TestCase):
	
	def testInterpretationConstructors(self):
		foo_url = "http://example.com/schema#Foo"
		foo = Symbol("FOO", parent=set(['Interpretation']), uri=foo_url)
		self.assertEquals("FOO", foo.name)
		self.assertEquals(foo_url, foo.uri)

	def testManifestationConstructors(self):
		foo_url = "http://example.com/schema#Foo"
		foo = Symbol("FOO", parent=set(['Manifestation']), uri=foo_url)
		self.assertEquals("FOO", foo.name)
		self.assertEquals(foo_url, foo.uri)

class InterpretationTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Interpretation class
	"""

	def testPredefined(self):
		tag = Interpretation.AUDIO
		self.assertTrue(tag.name != None)
		self.assertTrue(tag.uri != None)
		self.assertTrue(tag.display_name != None)
		self.assertTrue(tag.doc != None)


class ManifestationTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Manifestation class
	"""
	
	def testPredefined(self):
		f = Manifestation.FILE_DATA_OBJECT
		self.assertTrue(f.name != None)
		self.assertTrue(f.uri != None)
		self.assertTrue(f.display_name != None)
		self.assertTrue(f.doc != None)

class RelationshipTest (unittest.TestCase):
	"""
	Tests for parent/child relationships in the loaded ontologies
	"""
	
	def testDirectParents (self):
		"""
		Tests relationship tracking for immediate parents
		"""
		self.assertTrue(Interpretation.AUDIO.is_child_of(Interpretation.MEDIA))
	
	def testSecondLevelParents (self):
		"""
		Tests relationship tracking for second level parents
		"""
		self.assertTrue(Interpretation.VECTOR_IMAGE.is_child_of(Interpretation.MEDIA))
		self.assertTrue(Interpretation.VECTOR_IMAGE.is_child_of(Interpretation.IMAGE))
	
	def testRootParents (self):
		"""
		Tests relationship tracking for root nodes, ie Interpretation
		and Manifestation
		"""
		self.assertTrue(Interpretation.VECTOR_IMAGE.is_child_of(Interpretation))
		self.assertTrue(Manifestation.FILE_DATA_OBJECT.is_child_of(Manifestation))
		self.assertTrue(Manifestation.USER_ACTIVITY.is_child_of(Manifestation))
	
	def testReflecsive (self):
		"""
		Assert that a symbol is a child of itself
		"""
		self.assertTrue(Manifestation.USER_ACTIVITY.is_child_of(Manifestation.USER_ACTIVITY))
	
	def testFindExtendedChildren (self):
		self.assertEquals(["foo://bar"], Symbol.find_child_uris_extended("foo://bar"))
		self.assertEquals(["http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Icon",
		                   "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#VectorImage",
		                   "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Cursor",
		                   "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#RasterImage",
		                   "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Image"],
		                  Symbol.find_child_uris_extended("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Image"))

class EventTest (unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def testSimple(self):
		ev = Event()
		ev.timestamp = 10
		ev.interpretation = "Bluff"
		self.assertEquals("10", ev.timestamp)
		self.assertEquals("Bluff", ev.interpretation)
	
	def testNewForValues1(self):
		ev = Event.new_for_values(timestamp=1,
					subjects=[Subject.new_for_values(uri="foo://bar")])
		self.assertEquals("1", ev.timestamp)
		self.assertEquals(1, len(ev.subjects))
		self.assertEquals("foo://bar", ev.subjects[0].uri)
	
	def testNewForValues2(self):
		ev = Event.new_for_values(timestamp=27,
					subject_uri="foo://baz",
					subject_mimetype="text/plain")
		self.assertEquals("27", ev.timestamp)
		self.assertEquals(1, len(ev.subjects))
		self.assertEquals("foo://baz", ev.subjects[0].uri)
		self.assertEquals("text/plain", ev.subjects[0].mimetype)
	
	def testTemplateMatching(self):
		template = Event.new_for_values(
					manifestation="klaf:CarvedRunes",
					subject_uri="runes:///jellinge_stone.stn",
					subject_mimetype="text/runes")

		e = Event.new_for_values(
					interpretation="klaf:Document",
					manifestation="klaf:CarvedRunes",
					subject_uri="runes:///jellinge_stone.stn",
					subject_text="Harald Blåtand",
					subject_mimetype="text/runes")
		self.assertTrue(e.matches_template(template))
		
		# Add a non-matching subject to the event.
		# We should still be good
		s = Subject.new_for_values(
					uri="file:///tmp/foo.txt",
					mimetype="text/plain")
		e.subjects.append(s)
		self.assertTrue(e.matches_template(template))
		
		# Remove all subjects from e and we should no longer match
		subjects = e.subjects
		e.subjects = []
		self.assertFalse(e.matches_template(template))
		
		# Re-instate the subjects we removed just before
		e.subjects = subjects
		self.assertTrue(e.matches_template(template))
		
		e.manifestation="ILLEGAL SNAFU"
		self.assertFalse(e.matches_template(template))
	
	def testTemplateParentMatching(self):
		template = Event.new_for_values(
					manifestation=Manifestation.EVENT_MANIFESTATION,
					subject_interpretation=Interpretation)

		e = Event.new_for_values(
					manifestation=Manifestation.USER_ACTIVITY,
					subject_interpretation=Interpretation.TEXT_DOCUMENT,
					subject_text="Foo")
		self.assertTrue(e.matches_template(template))		
	
	def testTemplateFiltering(self):
		template = Event.new_for_values(interpretation="stfu:OpenEvent")
		events = parse_events("test/data/five_events.js")
		filtered_events = filter(template.matches_event, events)
		self.assertEquals(2, len(filtered_events))
	
	def testInTimeRange(self):
		ev = Event.new_for_values(timestamp=10)
		self.assertTrue(ev.in_time_range(TimeRange(0, 20)))
		self.assertFalse(ev.in_time_range(TimeRange(0, 5)))
		self.assertFalse(ev.in_time_range(TimeRange(15, 20)))
		
	def testNegationTemplateMatching(self):
		event = Event.new_for_values(
			subject_interpretation=Interpretation.AUDIO
		)
		
		template = Event.new_for_values(
			subject_interpretation="!%s" %Interpretation.AUDIO
		)
		self.assertFalse(event.matches_template(template))
		
		template = Event.new_for_values(
			subject_interpretation="!%s" %Interpretation.MEDIA
		)
		self.assertFalse(event.matches_template(template))
		
		template = Event.new_for_values(
			subject_interpretation="!%s" %Interpretation.DOCUMENT
		)
		self.assertTrue(event.matches_template(template))
		
		template = Event.new_for_values(
			subject_interpretation="!somerandomtext"
		)
		self.assertTrue(event.matches_template(template))
		
		event = Event.new_for_values(
			subject_interpretation=Interpretation.MEDIA
		)
		
		template = Event.new_for_values(
			subject_interpretation="!%s" %Interpretation.AUDIO
		)
		self.assertTrue(event.matches_template(template))
		

class TimeRangeTest (unittest.TestCase):

	def testEquality(self):
		self.assertFalse(TimeRange(0,1) == TimeRange(0,2))
		self.assertTrue(TimeRange(0,1) == TimeRange(0,1))
	
	def testIntersectWithEnclosing(self):
		outer = TimeRange(0, 10)
		inner = TimeRange(3,6)
		always = TimeRange.always()
		
		self.assertTrue(inner.intersect(outer) == inner)
		self.assertTrue(outer.intersect(inner) == inner)
		
		self.assertTrue(always.intersect(inner) == inner)
		self.assertTrue(inner.intersect(always) == inner)
	
	def testIntersectDisjoint(self):
		t1 = TimeRange(0, 10)
		t2 = TimeRange(20, 30)
		self.assertTrue(t1.intersect(t2) is None)
		self.assertTrue(t2.intersect(t1) is None)
	
	def testIntersectOverlap(self):
		first = TimeRange(0, 10)
		last = TimeRange(5, 15)
		
		self.assertTrue(first.intersect(last) == TimeRange(5, 10))
		self.assertTrue(last.intersect(first) == TimeRange(5, 10))
	
if __name__ == '__main__':
	unittest.main()
