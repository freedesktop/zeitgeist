from zeitgeist_gui.zeitgeist_engine_wrapper import engine
import sys


tags = engine.get_recent_used_tags(2,0,sys.maxint)
print tags

