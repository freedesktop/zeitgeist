NULL=

SUBDIRS = \
	ontology \
	$(NULL)

servicedir = $(DBUS_SERVICES_DIR)
service_DATA = org.gnome.zeitgeist.service

org.gnome.zeitgeist.service: org.gnome.zeitgeist.service.in
	$(AM_V_GEN)sed -e s!\@prefix\@!$(prefix)! < $< > $@
org.gnome.zeitgeist.service: Makefile

bashcompletiondir = $(datadir)/bash-completion/completions
dist_bashcompletion_DATA = completions/zeitgeist-daemon

xdgautostart_in_files = zeitgeist-datahub.desktop.in

if ENABLE_DATAHUB
xdgautostartdir=$(sysconfdir)/xdg/autostart
xdgautostart_DATA = $(xdgautostart_in_files:.desktop.in=.desktop)
endif

CLEANFILES = \
	org.gnome.zeitgeist.service \
	PythonSerializer.pyc \
	zeitgeist-datahub.desktop \
	$(NULL)

EXTRA_DIST = \
	org.gnome.zeitgeist.service.in \
	ontology2code \
	$(xdgautostart_in_files) \
	$(NULL)

all-local: org.gnome.zeitgeist.service

%.desktop: %.desktop.in
	$(AM_V_GEN)$(MSGFMT) --desktop --template $< -d $(top_srcdir)/po -o $@

clean:
	rm -rf *.pyc *.~[0-9]~
