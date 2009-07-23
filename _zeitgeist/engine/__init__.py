import logging

_engine = None
def get_default_engine(type=None):
	global _engine
	if _engine is not None:
		return _engine
	if type is None:
		type = "storm"
	try:
		engine_cls = __import__(
			"_zeitgeist.engine.%s_engine" %type, globals(), locals(), ["ZeitgeistEngine",], -1
		)
	except ImportError, err:
		logging.exception("Could not load file: %s_engine" %type)
		return False
	_engine = engine_cls.ZeitgeistEngine()
	return _engine
