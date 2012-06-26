NULL =

if ENABLE_DOCS

# valadoc in Ubuntu doesn't find it vala-0.16/vapi
VALADOC_FLAGS = \
	--force \
	--vapidir $(top_srcdir)/libzeitgeist \
	--vapidir /usr/share/vala-0.16/vapi/ \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--basedir $(top_srcdir)/libzeitgeist \
	--package-name libzeitgeist2 \
	--package-version $(PACKAGE_VERSION) \
	$(wildcard $(top_srcdir)/libzeitgeist/*.vala) \
	$(NULL)

valadoc:
	$(VALADOC) \
		-o valadoc \
		$(VALADOC_FLAGS) \
		$(NULL)

devhelp:
	$(VALADOC) \
		-o devhelp \
		--doclet devhelp \
		$(VALADOC_FLAGS) \
		$(NULL)

gtkdoc:
	$(VALADOC) \
		-X $(top_srcdir)/libzeitgeist/zeitgeist.h \
		-X $(top_srcdir)/config.h \
		-X -l -X $(top_srcdir)/libzeitgeist/.libs/libzeitgeist-2.0.so \
		-o gtkdoc \
		--doclet gtkdoc \
		$(VALADOC_FLAGS) \
		$(NULL)

clean-local:
	rm -rf valadoc devhelp gtkdoc

all: valadoc devhelp gtkdoc

endif
