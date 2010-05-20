import os
import sys

RENAMES = \
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
	 "http://www.semanticdesktop.org/ontologies/2007/03/22/nmo#IMMessage"),s
	
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

DELETED = \
[
	# Interpretation.COMMENT
	"http://www.semanticdesktop.org/ontologies/2007/01/19/nie/#comment",
	
	,
	""
]

# Never existed:
"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#WebHistory"
"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Website" + "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#RemoteDataObject"

#
# This module upgrades the 'core' schema from version 0 (or unversioned
# pre 0.3.3 DBs) to DB core schema version 1
#
def run(cursor):
	raise Exception("Upgrade not implemented yet. Sorry")
