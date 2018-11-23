NULL =

appdir = $(pythondir)/zeitgeist/

app_PYTHON = \
	__init__.py \
	datamodel.py \
	client.py \
	mimetypes.py \
	_ontology.py \
	$(NULL)

ONTOLOGY = \
	$(wildcard $(top_srcdir)/data/ontology/*.trig) \
	$(NULL)

_ontology.py: $(ONTOLOGY) $(top_srcdir)/data/ontology2code
	@echo -e "#\n# Auto-generated from .trig files. Do not edit.\n#" > $@
	$(AM_V_GEN)$(PYTHON) $(top_srcdir)/data/ontology2code --dump-python >> $@

CLEANFILES = \
	_ontology.py \
	$(NULL)

all-local: _ontology.py
