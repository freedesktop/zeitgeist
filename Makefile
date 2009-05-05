PREFIX = /usr/local

all:
	echo $(PREFIX)
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
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-timeline.py
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-trayicon.py
	
	rm -f $(PREFIX)/bin/zeitgeist-daemon \
		$(PREFIX)/bin/zeitgeist-journal \
		$(PREFIX)/bin/zeitgeist-projectviewer \
		$(PREFIX)/bin/zeitgeist-timeline \
	
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist-daemon.py \
		$(PREFIX)/bin/zeitgeist-daemon
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-journal.py \
		$(PREFIX)/bin/zeitgeist-journal
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-projectviewer.py \
		$(PREFIX)/bin/zeitgeist-projectviewer
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-timeline.py \
		$(PREFIX)/bin/zeitgeist-timeline
		
	@echo "Makefile: Installed GNOME Zeitgeist."

# uninstall
uninstall:
	rm -rf $(PREFIX)/share/gnome-zeitgeist
	rm -rf $(PREFIX)/share/doc/gnome-zeitgeist
	rm -f $(PREFIX)/bin/zeitgeist-daemon
	rm -f $(PREFIX)/bin/zeitgeist-journal
	rm -f $(PREFIX)/bin/zeitgeist-projectviewer
	rm -f $(PREFIX)/bin/zeitgeist-timeline
	rm -f $(PREFIX)/share/applications/zeitgeist-journal.desktop
	rm -f $(PREFIX)/share/dbus-1/services/org.gnome.Zeitgeist.service
	@echo "Makefile: GNOME Zeitgeist uninstalled."

clean:
	find src/ -name "*\.pyc" -delete
	@echo "Makefile: Cleaned up."

# build a source release
source_package:
	@echo "Not yet implemented.
	#@echo "Makefile: Source-package is ready and waiting in ./dist ..."

# generate translations template
translations:
	xgettext src/*.py src/*/*.py \
		--output-dir=./po/ \
		--output=messages.pot \
		--language=Python \
		--copyright-holder="The Zeitgeist Team" \
		--msgid-bugs-address="gnome-zeitgeist-users@lists.launchpad.net"  \
		--package-name="GNOME Zeitgeist" \
		--package-version="$(cat VERSION)"

# build and install the translations -- (for developer use only)
install-translations:
	msgfmt po/ca.po
	sudo mv messages.mo /usr/share/locale/ca/LC_MESSAGES/gnome-zeitgeist.mo

update-po: translations
	for cat in $$catalogs; do \
	  cat=`basename $$cat`; \
	  lang=`echo $$cat | sed 's/\$(CATOBJEXT)$$//'`; \
	  mv $$lang.po $$lang.old.po; \
	  echo "$$lang:"; \
	  if $(MSGMERGE) -w 132 $$lang.old.po $(PACKAGE).pot -o $$lang.po; then \
	    rm -f $$lang.old.po; \
	  else \
	    echo "msgmerge for $$cat failed!"; \
	    rm -f $$lang.po; \
	    mv $$lang.old.po $$lang.po; \
	  fi; \
	done

.PHONY: uninstall
