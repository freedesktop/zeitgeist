from gi.repository import Zeitgeist
log = Zeitgeist.Log.get_default()

def callback (x):
    print x

log.get_events([x for x in xrange(100)], None, callback, None)  
