PREFIX = /usr/local
MO_PREFIX = /usr

all:
	@echo "Makefile: Available actions: install, uninstall, clean, tarball, generate-pot, build-translations, install-translations, update-po, build-docs."

# install
install: clean build-docs install-translations
	mkdir -p $(PREFIX)/share/gnome-zeitgeist/data
	mkdir -p $(PREFIX)/share/doc/gnome-zeitgeist/html
	mkdir -p $(PREFIX)/share/applications
	mkdir -p $(PREFIX)/share/pixmaps
	mkdir -p $(PREFIX)/share/dbus-1/services
	mkdir -p $(PREFIX)/bin
	
	cp -r src $(PREFIX)/share/gnome-zeitgeist
	rm -r $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_experimental
	-install data/* $(PREFIX)/share/gnome-zeitgeist/data
	install extra/zeitgeist-journal.desktop $(PREFIX)/share/applications
	install extra/org.gnome.Zeitgeist.service $(PREFIX)/share/dbus-1/services
	install TODO $(PREFIX)/share/doc/gnome-zeitgeist
	install doc/gzg-userdocs.html $(PREFIX)/share/doc/gnome-zeitgeist/html
	
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist-daemon.py
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-journal.py
	chmod +x $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-trayicon.py
	
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist-daemon.py \
		$(PREFIX)/bin/zeitgeist-daemon
	ln -s $(PREFIX)/share/gnome-zeitgeist/src/zeitgeist_gui/zeitgeist-journal.py \
		$(PREFIX)/bin/zeitgeist-journal
	
	@echo "Makefile: Installed GNOME Zeitgeist."

# uninstall
uninstall:
	rm -rf $(PREFIX)/share/gnome-zeitgeist
	rm -rf $(PREFIX)/share/doc/gnome-zeitgeist
	rm -f $(PREFIX)/bin/zeitgeist-daemon
	rm -f $(PREFIX)/bin/zeitgeist-journal
	rm -f $(PREFIX)/share/applications/zeitgeist-journal.desktop
	rm -f $(PREFIX)/share/dbus-1/services/org.gnome.Zeitgeist.service
	@echo "Makefile: GNOME Zeitgeist uninstalled."

clean:
	find src/ -name "*\.pyc" -delete
	find src/ -name "*~" -delete
	rm -f po/*.mo doc/gzg-userdocs.html
	@echo "Makefile: Cleaned up."

# build a source release
tarball:
	@echo "Not yet implemented."
	#@echo "Makefile: Tarball is ready and waiting in ./dist ..."

build-docs:
	asciidoc doc/gzg-userdocs.txt

# generate translations template (POT)
generate-pot:
	xgettext src/*.py src/*/*.py \
		--output-dir=./po/ \
		--output=messages.pot \
		--language=Python \
		--copyright-holder="The Zeitgeist Team" \
		--msgid-bugs-address="gnome-zeitgeist-users@lists.launchpad.net"  \
		--package-name="GNOME Zeitgeist" \
		--package-version="$(cat VERSION)"

# build translations (into .mo files)
build-translations:
	for file in po/*.po; do \
		msgfmt $$file -o $${file%.*}.mo; \
	done

# install translations
install-translations: build-translations
	cd po/; for file in *.mo; do \
		mkdir -p $(MO_PREFIX)/share/locale/$${file%.*}/LC_MESSAGES/; \
		sudo mv $$file \
			$(MO_PREFIX)/share/locale/$${file%.*}/LC_MESSAGES/gnome-zeitgeist.mo; \
	done

# update .po files with the POT template
update-po: generate-pot
	cd po/; for file in *.po; do \
	  lang=$${file%.*}; \
	  mv $$lang.po $$lang.old.po; \
	  echo "$$lang:"; \
	  if msgmerge $$lang.old.po messages.pot -o $$lang.po; then \
	    rm -f $$lang.old.po; \
	  else \
	    echo "msgmerge for $$file failed!"; \
	    rm -f $$lang.po; \
	    mv $$lang.old.po $$lang.po; \
	  fi; \
	done

.PHONY: uninstall
