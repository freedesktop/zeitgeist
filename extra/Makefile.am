SUBDIRS = ontology

servicedir = $(datadir)/dbus-1/services
nodist_service_DATA = org.gnome.zeitgeist.service

org.gnome.zeitgeist.service: org.gnome.zeitgeist.service.in
	sed	-e s!\@prefix\@!$(prefix)! < $< > $@
org.gnome.zeitgeist.service: Makefile

CLEANFILES = org.gnome.zeitgeist.service \
	PythonSerializer.pyc
EXTRA_DIST = \
	org.gnome.zeitgeist.service.in \
	zeitgeist-daemon.bash_completion \
	ontology2code \
	$(NULL)

all-local: org.gnome.zeitgeist.service

clean:
	rm -rf *.pyc *.~[0-9]~
