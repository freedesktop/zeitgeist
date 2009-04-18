PREFIX = /usr/local
INSTALL_LOG = install.log

.PHONY : uninstall

all:
	@echo "Makefile: Available actions: install, uninstall, clean, source_package, translations"

# install
install:
	mkdir -p $(PREFIX)/share/gnome-zeitgeist/data
	mkdir -p $(PREFIX)/share/doc/gnome-zeitgeist/
	mkdir -p $(PREFIX)/share/applications
	mkdir -p $(PREFIX)/share/pixmaps
	mkdir -p $(PREFIX)/share/dbus-1/services
	
	cp -r src $(PREFIX)/share/gnome-zeitgeist
	install data/* $(PREFIX)/share/gnome-zeitgeist/data
	install extra/zeitgeist-journal.desktop $(PREFIX)/share/applications
	install extra/org.gnome.Zeitgeist.service $(PREFIX)/share/dbus-1/services
	install AUTHORS MAINTAINERS TODO $(PREFIX)/share/doc/gnome-zeitgeist
	
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist-daemon.py
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-journal.py
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-projectviewer.py
	
	rm -f $(PREFIX)/bin/zeitgeist-daemon \
		$(PREFIX)/bin/zeitgeist-journal \
		$(PREFIX)/bin/zeitgeist-projectviewer
	
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist-daemon.py \
		$(PREFIX)/bin/zeitgeist-daemon
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-journal.py \
		$(PREFIX)/bin/zeitgeist-journal
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-projectviewer.py \
		$(PREFIX)/bin/zeitgeist-projectviewer
	
	@echo "Makefile: Installed GNOME Zeitgeist."

# uninstall
uninstall:
	rm -rf $(PREFIX)/share/gnome-zeitgeist
	rm -rf $(PREFIX)/share/doc/gnome-zeitgeist
	rm -f $(PREFIX)/bin/zeitgeist-daemon
	rm -f $(PREFIX)/bin/zeitgeist-journal
	rm -f $(PREFIX)/bin/zeitgeist-projectviewer
	rm -f $(PREFIX)/share/applications/zeitgeist-journal.desktop
	rm -f $(PREFIX)/share/dbus-1/services/org.gnome.Zeitgeist.service
	@echo "Makefile: GNOME Zeitgeist uninstalled."

clean:
	find src/ -name "*\.pyc" -delete
	@echo "Makefile: Cleaned up."

# build a source-release
source_package:
	python setup.py sdist --formats=bztar
	@echo "Makefile: Source-package is ready and waiting in ./dist ..."

# generate translations template
translations:
	xgettext --language=Python --output=messages.pot \
		--copyright-holder="The Zeitgeist Team" \
		--msgid-bugs-address="seif@lotfy.com" src/*.py src/*/*.py
