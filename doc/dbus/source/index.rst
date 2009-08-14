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

.. _item-label:

Item
++++

A dict representing an item, with the following elements:

 #. **timestamp** (integer) -
 #. **uri** (string) -
 #. **text** (string) -
 #. **source** (string) -
 #. **content** (string) -
 #. **mimetype** (string) -
 #. **tags** (string) -
 #. **comment** (string) - (not used)
 #. **bookmark** (boolean) -
 #. **use** (string) -
 #. **icon** (string) -
 #. **app** (string) -
 #. **origin** (string) -

.. _filter-label:

Filter
++++++

A dict which can have the following items:

 * **name** (list of strings) - filter by name (``OR`` Condition)
 * **uri** (list of strings) - filter by uris (``OR`` Condition)
 * **tags** (list of strings) - filter by tags (``AND`` Condition)
 * **mimetypes** (list of strings) - filter by mimetypes (``OR`` Condition)
 * **source** (list of strings) - filter by source (``OR`` Condition)
 * **content** (list of strings) - filter by content (``OR`` Condition)
 * **application** (list of strings) - filter by application (ie., path to its .desktop file) (``OR`` Condition)
 * **bookmarked** (boolean) -
