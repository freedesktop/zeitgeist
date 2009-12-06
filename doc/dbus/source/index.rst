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

In general terms the *interpretation* of an event or subject is an abstract
description of *"what happened"* or *"what is this"*.

Each interpretation type is uniquely identified by a URI.

.. autodata:: Interpretation

Manifestation
+++++++++++++

The manifestation type of an event or subject is an abstract classification
of *"how did this happen"* or *"how does this item exist"*.

Each manifestation type s uniquely identified by a URI.

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



.. module:: zeitgeist.client

Zeitgeist Client API
====================

ZeitgeistClient
+++++++++++++++

.. autoclass:: ZeitgeistClient
    :members: 

Monitor
+++++++

.. autoclass:: Monitor
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
    :members: InsertEvents, GetEvents, FindEventIds, DeleteEvents, DeleteLog, Quit


