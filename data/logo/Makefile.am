pixmapdir = $(datadir)
pixmap_DATA = gnome-zeitgeist.xpm

hicolordir = $(datadir)/icons/hicolor
tango_icons = \
	22x22/apps/gnome-zeitgeist.png \
	24x24/apps/gnome-zeitgeist.png \
	32x32/apps/gnome-zeitgeist.png \
	scalable/apps/gnome-zeitgeist.svg

install-data-local:
	@-$(mkinstalldirs) $(DESTDIR)$(hicolordir)/22x22/apps
	$(INSTALL_DATA) $(srcdir)/22x22/apps/gnome-zeitgeist.png \
		$(DESTDIR)$(hicolordir)/22x22/apps/gnome-zeitgeist.png
	@-$(mkinstalldirs) $(DESTDIR)$(hicolordir)/24x24/apps
	$(INSTALL_DATA) $(srcdir)/24x24/apps/gnome-zeitgeist.png \
		$(DESTDIR)$(hicolordir)/24x24/apps/gnome-zeitgeist.png
	@-$(mkinstalldirs) $(DESTDIR)$(hicolordir)/32x32/apps
	$(INSTALL_DATA) $(srcdir)/32x32/apps/gnome-zeitgeist.png \
		$(DESTDIR)$(hicolordir)/32x32/apps/gnome-zeitgeist.png
	@-$(mkinstalldirs) $(DESTDIR)$(hicolordir)/scalable/apps
	$(INSTALL_DATA) $(srcdir)/scalable/apps/gnome-zeitgeist.svg \
		$(DESTDIR)$(hicolordir)/scalable/apps/gnome-zeitgeist.svg

gtk_update_icon_cache = gtk-update-icon-cache -f -t $(datadir)/icons/hicolor

install-data-hook:
	@-if test -z "$(DESTDIR)"; then \
		echo "Updating GTK icon cache."; \
		$(gtk_update_icon_cache); \
	else \
		echo "*** Icon cache not updated.  After install, run this:"; \
		echo "***   $(gtk_update_icon_cache)"; \
	fi

uninstall-hook:
	rm -f $(DESTDIR)$(hicolordir)/22x22/apps/gnome-zeitgeist.png
	rm -f $(DESTDIR)$(hicolordir)/24x24/apps/gnome-zeitgeist.png
	rm -f $(DESTDIR)$(hicolordir)/32x32/apps/gnome-zeitgeist.png
	rm -f $(DESTDIR)$(hicolordir)/scalable/apps/gnome-zeitgeist.svg

EXTRA_DIST = $(tango_icons) $(pixmap_DATA)
