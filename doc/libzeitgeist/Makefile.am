NULL =

if ENABLE_DOCS

FILES = \
	$(top_srcdir)/libzeitgeist/data-source.vala \
	$(top_srcdir)/libzeitgeist/data-source-registry.vala \
	$(top_srcdir)/libzeitgeist/mimetype.vala \
	$(top_srcdir)/libzeitgeist/enumerations.vala \
	$(top_srcdir)/libzeitgeist/event.vala \
	$(top_srcdir)/libzeitgeist/errors.vala \
	$(top_srcdir)/libzeitgeist/subject.vala \
	$(top_srcdir)/libzeitgeist/timerange.vala \
	$(top_srcdir)/libzeitgeist/index.vala \
	$(top_srcdir)/libzeitgeist/log.vala \
	$(top_srcdir)/libzeitgeist/timestamp.vala \
	$(top_srcdir)/libzeitgeist/monitor.vala \
	$(top_srcdir)/libzeitgeist/ontology-uris.vala \
	$(top_srcdir)/libzeitgeist/ontology.vala \
	$(top_srcdir)/libzeitgeist/queued-proxy-wrapper.vala \
	$(top_srcdir)/libzeitgeist/remote.vala \
	$(top_srcdir)/libzeitgeist/result-set.vala \
	$(top_srcdir)/libzeitgeist/simple-result-set.vala \
	$(top_srcdir)/libzeitgeist/utils.vala \
	$(NULL)

# valadoc in Ubuntu doesn't find it vala-0.16/vapi
VALADOC_FLAGS = \
	--force \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	--pkg zeitgeist-internal \
	--vapidir $(top_builddir)/libzeitgeist \
	--basedir $(top_srcdir)/libzeitgeist \
	--package-name "zeitgeist-2.0" \
	--package-version $(PACKAGE_VERSION) \
	$(FILES) \
	$(NULL)

docs_vala: $(FILES)
	$(VALADOC) \
		-o $@ \
		$(VALADOC_FLAGS) \
		$(NULL)

# The output directory can't be called "gtkdoc" or it'll conflict
# with the "--doclet" option (it only works if the directory doesn't
# exist prior to invocation).
docs_c: $(FILES) $(srcdir)/zeitgeist-gtkdoc-index.sgml
	install -D $(srcdir)/zeitgeist-gtkdoc-index.sgml $@/zeitgeist-2.0-docs.xml
	$(VALADOC) \
		-X $(top_builddir)/libzeitgeist/zeitgeist-datamodel.h \
		-X $(top_builddir)/libzeitgeist/zeitgeist.h \
		-X -l -X $(top_builddir)/libzeitgeist/.libs/libzeitgeist-2.0.so \
		-o $@ \
		--doclet gtkdoc \
		$(VALADOC_FLAGS) \
		$(NULL)

EXTRA_DIST = \
	zeitgeist-gtkdoc-index.sgml \
	docs_c \
	docs_vala \
	$(NULL)

clean-local:
	rm -rf docs_vala docs_c

all: docs_vala docs_c

endif
