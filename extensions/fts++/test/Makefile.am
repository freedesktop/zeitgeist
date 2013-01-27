NULL = 
check_PROGRAMS = test-fts
TESTS = test-fts

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	-I$(srcdir)/.. \
	-I $(top_srcdir)/libzeitgeist/utils \
	-I $(top_srcdir)/libzeitgeist \
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
  $(builddir)/../libzeitgeist-internal.la \
  $(top_builddir)/libzeitgeist/libzeitgeist-utils.la \
  $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
  -lxapian \
  $(NULL)

if HAVE_DEE_ICU
AM_CPPFLAGS += $(DEE_ICU_CFLAGS)
test_fts_LDADD += $(DEE_ICU_LIBS)
endif

