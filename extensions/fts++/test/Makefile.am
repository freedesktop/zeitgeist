NULL = 
check_PROGRAMS = test-fts
TESTS = test-fts

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	-I.. \
	$(NULL)

test_fts_SOURCES = \
  test-stringutils.cpp \
  test-indexer.cpp \
  test-fts.c \
  ../stringutils.cpp \
  ../controller.cpp \
  ../indexer.cpp \
  ../task.cpp \
  ../fts.cpp \
  $(NULL)

test_fts_LDADD = \
  $(builddir)/../libzeitgeist-internal.la \
  -lxapian \
  $(NULL)

