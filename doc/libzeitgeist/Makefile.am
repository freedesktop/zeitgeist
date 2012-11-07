NULL =

if ENABLE_DOCS

FILES = \
	$(wildcard $(top_srcdir)/libzeitgeist/*.vala) \
	$(NULL)

# valadoc in Ubuntu doesn't find it vala-0.16/vapi
VALADOC_FLAGS = \
	--force \
	--vapidir $(top_srcdir)/libzeitgeist \
	--vapidir /usr/share/vala-0.16/vapi/ \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	--basedir $(top_srcdir)/libzeitgeist \
	--package-name "zeitgeist-2.0" \
	--package-version $(PACKAGE_VERSION) \
	--no-protected \
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
docs_c: $(FILES) zeitgeist-gtkdoc-index.sgml
	install -D zeitgeist-gtkdoc-index.sgml $@/zeitgeist-2.0-docs.xml
	$(VALADOC) \
		-X $(top_srcdir)/libzeitgeist/zeitgeist.h \
		-X -l -X $(top_srcdir)/libzeitgeist/.libs/libzeitgeist-2.0.so \
		-o $@ \
		--doclet gtkdoc \
		$(VALADOC_FLAGS) \
		$(NULL)

clean-local:
	rm -rf docs_vala docs_c

all: docs_vala docs_c

endif
