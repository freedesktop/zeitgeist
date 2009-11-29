==================
Zeitgeist DBus API
==================

.. module:: _zeitgeist.engine.remote

Engine
======

org.gnome.zeitgeist.Log Interface
+++++++++++++++++++++++++++++

.. autoclass:: RemoteInterface
    :members: InsertEvents, GetEvents, FindEventIds, DeleteLog, Quit

Data Types
==========

.. _sorting-label:

Result Types
++++++++++++

The *result_type* parameter to FindEventIds() is an unsigned integer with
one of the following values, to determine the type of sorting and grouping:

 * **0** - Most recent events.
     All events with the most recent events first
 * **1** - Least recent events.
     All events with the oldest ones first
 * **2** - Most recent subjects.
     One event for each subject only, ordered with the most recent event first
 * **3** - Most recent subjects.
     One event for each subject only, ordered with oldest event first
 * **4** - Most popular subjects.
     One event for each subject only, ordered by the popularity of the subject
 * **5** - Least popular subjects.
     One event for each subject only, ordered with the least popular subject first
