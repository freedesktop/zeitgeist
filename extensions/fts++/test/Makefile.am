NULL = 
check_PROGRAMS = test-fts
TESTS = test-fts

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	-I$(srcdir)/.. \
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
  -lxapian \
  $(NULL)

