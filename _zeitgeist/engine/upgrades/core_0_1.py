import os
import sys

INTERPRETATION_RENAMES = \
[
	("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#ManifestationCode",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#SourceCode"),
	
	("http://www.semanticdesktop.org/ontologies/nfo/#Bookmark",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Bookmark"),
	
	("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Document",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Document"),
	 
	("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Image",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Image"),
	
	("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Video",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Video"),
	
	("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Audio",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Audio"),
	
	("http://www.semanticdesktop.org/ontologies/2007/03/22/nmo/#Email",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nmo#Email"),
	
	("http://www.semanticdesktop.org/ontologies/2007/03/22/nmo/#IMMessage",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nmo#IMMessage"),
	
	# FIXME: FEED_MESSAGE
	# FIXME: BROADCAST_MESSAGE
	# FIXME: FOCUS_EVENT
	# FIXME: WARN_EVENT
	# FIXME: ERROR_EVENT
	# FIXME: http://freedesktop.org/standards/xesam/1.0/core#SystemRessource
	
	("http://zeitgeist-project.com/schema/1.0/core#CreateEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#CreateEvent"),
	
	("http://zeitgeist-project.com/schema/1.0/core#ModifyEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#ModifyEvent"),
	
	("http://zeitgeist-project.com/schema/1.0/core#VisitEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#AccessEvent"),
	
	("http://zeitgeist-project.com/schema/1.0/core#OpenEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#AccessEvent"),
	
	("http://zeitgeist-project.com/schema/1.0/core#SaveEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#ModifyEvent"),
	
	("http://zeitgeist-project.com/schema/1.0/core#CloseEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#LeaveEvent"),
	
	("http://zeitgeist-project.com/schema/1.0/core#SendEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#SendEvent"),
	
	("http://zeitgeist-project.com/schema/1.0/core#ReceiveEvent",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#ReceiveEvent"),
]

MANIFESTATION_RENAMES = \
[
	("http://zeitgeist-project.com/schema/1.0/core#UserActivity",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#UserActivity"),
	
	("http://zeitgeist-project.com/schema/1.0/core#HeuristicActivity",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#HeuristicActivity"),
	
	("http://zeitgeist-project.com/schema/1.0/core#ScheduledActivity",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#ScheduledActivity"),
	
	("http://zeitgeist-project.com/schema/1.0/core#UserNotification",
	 "http://www.zeitgeist-project.com/ontologies/2010/01/27/zg#WorldActivity"),
	
	("http://www.semanticdesktop.org/ontologies/nfo/#FileDataObject",
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#FileDataObject"),
]

# These are left alone, but are listed here for completeness
INTERPRETATION_DELETIONS = \
[
	"http://www.semanticdesktop.org/ontologies/2007/01/19/nie/#comment",
	"http://zeitgeist-project.com/schema/1.0/core#UnknownInterpretation",
]

# These are left alone, but are listed here for completeness
MANIFESTATION_DELETIONS = \
[
	"http://zeitgeist-project.com/schema/1.0/core#UnknownManifestation",
]

#
# This module upgrades the 'core' schema from version 0 (or unversioned
# pre 0.3.3 DBs) to DB core schema version 1
#
def run(cursor):
	for r in INTERPRETATION_RENAMES:
		cursor.execute("""
			UPDATE interpretation SET value=? WHERE value=?
		""", r)
	
	for r in MANIFESTATION_RENAMES:
		cursor.execute("""
			UPDATE manifestation SET value=? WHERE value=?
		""", r)
	
	# START WEB HISTORY UPGRADE
	# The case of Manifestation.WEB_HISTORY it's a little more tricky.
	# We must set the subject interpretation to Interpretation.WEBSITE
	# and set the subject manifestation to Manifestation.REMOTE_DATA_OBJECT.
	#
	# We accomplish this by renaming nfo#WebHistory to nfo#RemoteDataObject
	# and after that set the interpretation of all events with manifestation
	# nfo#RemoteDataObjects to nfo#Website.
	
	cursor.execute("""
		UPDATE manifestation SET value=? WHERE value=?
	""", ("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#WebHistory",
	      "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#RemoteDataObject"))
	
	try:
		cursor.execute("""
			INSERT INTO interpretation (value) VALUES (?)
		""", ("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Website",))
	except:
		# Unique key constraint violation - it's already there...
		pass
	
	website_id = cursor.execute("SELECT id FROM interpretation WHERE value='http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Website'").fetchone()[0]
	remotes = cursor.execute("SELECT id FROM event WHERE subj_manifestation='http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#RemoteDataObject'").fetchall()
	for event_id in remotes:
		cursor.execute("""
			UPDATE event SET subj_interpretation=%s WHERE id=?
		""" % website_id, (event_id,))
	# END WEB HISTORY UPGRADE
	
