NULL =

#extensionsdir = $(libdir)/zeitgeist/extensions
noinst_LTLIBRARIES = ds-registry.la

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/src
	$(NULL)

VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg gmodule-2.0 \
	$(top_srcdir)/src/zeitgeist-engine.vapi \
	$(NULL)

ds_registry_la_SOURCES = \
	ds-registry.vala \
	$(NULL)

ds_registry_la_LDFLAGS = -module -avoid-version

ds_registry_la_LIBADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)
