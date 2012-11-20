from gi.repository import Zeitgeist
log = Zeitgeist.Log.get_default()
log.get_events([x for x in xrange(100)], None, callback, None)
