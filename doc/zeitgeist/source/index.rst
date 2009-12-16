=======================
Zeitgeist Documentation
=======================

.. module:: zeitgeist.datamodel

Data Model
==========

Event
+++++

.. autoclass:: Event
    :members: 

Subject
+++++++

.. autoclass:: Subject
    :members: 

Interpretation
++++++++++++++

.. autodata:: Interpretation

Manifestation
+++++++++++++

.. autodata:: Manifestation

TimeRange
+++++++++

.. autoclass:: TimeRange
    :members: 

ResultType
+++++++++++

.. autoclass:: ResultType

StorageState
+++++++++++++

.. autoclass:: StorageState

NULL_EVENT
++++++++++

.. autodata:: NULL_EVENT


.. module:: zeitgeist.client

Zeitgeist Client API
====================

ZeitgeistClient
+++++++++++++++

.. autoclass:: ZeitgeistClient
    :members: 

.. module:: _zeitgeist.engine.remote

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
