========
DBus API
========

.. module:: zeitgeist.engine.remote

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

A tuple representing an item, with the following elements:

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

 * **name** (string) - 
 * **uri** (string) - 
 * **tags** (list of strings) - filter by tags (``AND`` Condition)
 * **mimetypes** (list of strings) - filter by mimetypes (``AND`` Condition)
 * **source** (list of strings) - filter by source (``AND`` Condition)
 * **content** (list of strings) - filter by source (``AND`` Condition)
 * **bookmarked** (boolean) -
