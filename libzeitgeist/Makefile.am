NULL = 


lib_LTLIBRARIES = libzeitgeist.la

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	-D BUILTIN_EXTENSIONS \
	$(top_srcdir)/config.vapi \
	$(NULL)

libzeitgeist_la_SOURCES = \
	log.vala \
	$(NULL)
