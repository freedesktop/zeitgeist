NULL =

check_PROGRAMS = test-fts
TESTS = test-fts

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	$(XAPIAN_CXXFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	-I $(srcdir)/.. \
	-I $(builddir)/.. \
	-I $(top_builddir)/libzeitgeist \
	-I $(top_builddir)/src \
	-include $(top_builddir)/src/zeitgeist-engine.h \
	$(NULL)

test_fts_SOURCES = \
	test-stringutils.cpp \
	test-indexer.cpp \
	test-fts.c \
	$(srcdir)/../stringutils.cpp \
	$(srcdir)/../controller.cpp \
	$(srcdir)/../indexer.cpp \
	$(srcdir)/../task.cpp \
	$(srcdir)/../fts.cpp \
	$(NULL)

test_fts_LDADD = \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(top_builddir)/src/libzeitgeist-engine.la \
	$(XAPIAN_LIBS) \
	$(NULL)

if HAVE_DEE_ICU
AM_CPPFLAGS += $(DEE_ICU_CFLAGS)
test_fts_LDADD += $(DEE_ICU_LIBS)
endif

