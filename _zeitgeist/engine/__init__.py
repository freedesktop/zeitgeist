import os
import logging

ENGINE_FALLBACK = "storm"

_engine = None
def create_engine(engine_type=None):
	""" Creates an engine instance of the type defined by 'engine_type'.
	If 'engine_type' is None 'ENGINE_FALLBACK' is used.
	This function looks at _zeitgeist.engine to find the engine implementation.
	Each engine implementation has to follow the following conventions:
		1.) it has to be in _zeitgeist/engine/SOMENAME_engine.py
			(where SOMENAME defines the type)
		2.) the name of the class has to be ZeitgeistEngine and the class
			itself has to be a sublass of _zeitgeist.engine.engine_base.ZeitgeistEngine
	"""	
	global _engine
	if engine_type is None:
		engine_type = ENGINE_FALLBACK
	engine_type = engine_type.lower()
	if _engine is not None:
		running_type = engine.__module__.split(".").pop().lower()
		if not running_type == engine_type:
			raise RuntimeError(
				("There is already a zeitgeist engine running. But this "
				 "engine has another than the requested type "
				 "(requested='%s', running='%s')" %(engine_type, running_type))
			)
		return _engine
	try:
		engine_cls = __import__(
			"_zeitgeist.engine.%s_engine" %engine_type,
			globals(), locals(), ["ZeitgeistEngine",], -1
		)
	except ImportError, err:
		logging.exception("Could not load engine implementation for %r" %engine_type)
		raise RuntimeError("Could not load engine implementation for %r" %engine_type)
	_engine = engine_cls.ZeitgeistEngine()
	return _engine
	
def get_default_engine():
	""" Get the running engine instance or create a new one.
	To get the type of the new engine instance it looks at the 'ZEITGEIST_ENGINE'
	environment variable. If this is not defined, it uses the engine type
	defined by ENGINE_FALLBACK.
	"""
	if _engine is not None:
		return _engine
	return create_engine(engine_type=os.environ.get("ZEITGEIST_ENGINE", ENGINE_FALLBACK))
