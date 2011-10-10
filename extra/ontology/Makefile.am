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
	zeitgeist.py

ontology_trigdir = $(datadir)/zeitgeist/ontology
ontology_pydir = $(datadir)/zeitgeist/ontology

zeitgeist.py: $(ontology_trig_DATA)
	@echo -e "#\n# Auto-generated from all .trig files ($^). Do not edit.\n#" > $@
	$(AM_V_GEN)$(top_srcdir)/extra/ontology2code --dump-python >> $@

CLEANFILES = \
	$(ontology_py_DATA)

EXTRA_DIST = \
	$(ontology_trig_DATA)
