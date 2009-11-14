========
DBus API
========

.. module:: _zeitgeist.engine.remote

Engine
======

org.gnome.zeitgeist Interface
+++++++++++++++++++++++++++++

.. autoclass:: RemoteInterface
    :members:
    :undoc-members:

Data Types
==========

.. _sorting-label:

Sorting
+++++++

An unsigned integer with one of the following values, to determine the
type of sorting:

 * **0** - by timestamp (ascending order)
 * **1** - by timestamp (descending order)
 * **2** - by timestamp, no repeated items (ascending order)
 * **3** - by timestamp, no repeated items (descending order)
 * **4** - by usage, no repeated items (ascending order)
 * **5** - by usage, no repeated items (descending order)
