NULL =

appdir = $(pythondir)/zeitgeist/

app_PYTHON = \
	__init__.py \
	datamodel.py \
	client.py \
	mimetypes.py \
	_ontology.py \
	$(NULL)

# FIXME: can we make this depend on $(ontology_trig_DATA)?
_ontology.py:
	@echo -e "#\n# Auto-generated from .trig files. Do not edit.\n#" > $@
	$(AM_V_GEN)$(top_srcdir)/data/ontology2code --dump-python >> $@

CLEANFILES = \
	_ontology.py \
	$(NULL)

all-local: _ontology.py
