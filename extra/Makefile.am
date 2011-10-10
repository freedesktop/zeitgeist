SUBDIRS = ontology

servicedir = $(DBUS_SERVICES_DIR)
service_DATA = org.gnome.zeitgeist.service

org.gnome.zeitgeist.service: org.gnome.zeitgeist.service.in
	$(AM_V_GEN)sed	-e s!\@prefix\@!$(prefix)! < $< > $@
org.gnome.zeitgeist.service: Makefile

CLEANFILES = \
	org.gnome.zeitgeist.service \
	PythonSerializer.pyc \
	$(NULL)
EXTRA_DIST = \
	org.gnome.zeitgeist.service.in \
	zeitgeist-daemon.bash_completion \
	ontology2code \
	$(NULL)

all-local: org.gnome.zeitgeist.service

clean:
	rm -rf *.pyc *.~[0-9]~
