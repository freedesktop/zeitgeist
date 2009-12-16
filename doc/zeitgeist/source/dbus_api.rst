.. module:: _zeitgeist.engine.remote

========
DBus API
========

This is the raw DBus API for the Zeitgeist engine. Applications written in
Python are encouraged to use the
:class:`ZeitgeistClient <zeitgeist.client.ZeitgeistClient>` API instead.

org.gnome.zeitgeist.Log
+++++++++++++++++++++++

.. autoclass:: RemoteInterface
    :members: InsertEvents, GetEvents, FindEventIds, DeleteEvents, DeleteLog, Quit, InstallMonitor, RemoveMonitor

.. _org_gnome_zeitgeist_Monitor:

org.gnome.zeitgeist.Monitor
+++++++++++++++++++++++++++

.. autoclass:: zeitgeist.client.Monitor
    :members: NotifyInsert, NotifyDelete
