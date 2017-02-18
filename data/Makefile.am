NULL =

SUBDIRS = \
	ontology \
	$(NULL)

servicedir = $(datadir)/dbus-1/services
nodist_service_DATA = org.gnome.zeitgeist.Engine.service

systemd_userdir = $(prefix)/lib/systemd/user
nodist_systemd_user_DATA = zeitgeist.service

bashcompletiondir = $(datadir)/bash-completion/completions
dist_bashcompletion_DATA = completions/zeitgeist-daemon

xdgautostart_in_files = zeitgeist-datahub.desktop.in

if ENABLE_DATAHUB
xdgautostartdir=$(sysconfdir)/xdg/autostart
nodist_xdgautostart_DATA = $(xdgautostart_in_files:.desktop.in=.desktop)
endif

CLEANFILES = \
	org.gnome.zeitgeist.Engine.service \
	PythonSerializer.pyc \
	zeitgeist-datahub.desktop \
	zeitgeist.service \
	$(NULL)

EXTRA_DIST = \
	org.gnome.zeitgeist.Engine.service.in \
	ontology2code \
	zeitgeist.service.in \
	$(xdgautostart_in_files) \
	$(NULL)

%.desktop: %.desktop.in
	$(AM_V_GEN)$(MSGFMT) --desktop --template $< -d $(top_srcdir)/po -o $@

%.service: %.service.in
	$(AM_V_GEN)sed -e "s|@bindir[@]|$(bindir)|" $< > $@

clean:
	rm -rf *.pyc *.~[0-9]~
