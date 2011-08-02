ontology_trig_DATA = \
	zg.trig \
	nie.trig \
	nco.trig \
	nfo.trig \
	ncal.trig \
	nao.trig \
	nmo.trig \
	nmm.trig

ontology_py_DATA = \
	$(ontology_trig_DATA:.trig=.py) \
	zeitgeist.py

ontology_trigdir = $(datadir)/zeitgeist/ontology
ontology_pydir = $(datadir)/zeitgeist/ontology

%.py: %.trig
	echo -e "#\n# Auto-generated from $<. Do not edit\n#" > $@
	rapper -i trig -o rdfxml $< | $(top_srcdir)/ontology/rdfxml2py >> $@

zeitgeist.py: $(ontology_trig_DATA)
	echo -e "#\n# Auto-generated from all .trig files ($^). Do not edit\n#" > $@
	cat $^ | rapper -i trig -o rdfxml -I ZeitgeistNamespace - | \
		$(top_srcdir)/ontology/rdfxml2py >> $@

CLEANFILES = \
	$(ontology_py_DATA)

EXTRA_DIST = \
	$(ontology_trig_DATA)

