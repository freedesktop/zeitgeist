ontology_trig_DATA = \
	zeo.trig \
	nie.trig \
	nfo.trig

ontology_py_DATA = \
	$(ontology_trig_DATA:.trig=.py)

ontology_trigdir = $(datadir)/zeitgeist/ontology
ontology_pydir = $(datadir)/zeitgeist/ontology
	
%.py : %.trig
	echo -e "#\n# Auto-generated from $<. Do not edit\n#" > $@
	rapper -i trig -o rdfxml $< | $(top_srcdir)/extra/rdfxml2py >> $@

CLEANFILES = \
	$(ontology_py_DATA)

EXTRA_DIST = \
	$(ontology_trig_DATA)

