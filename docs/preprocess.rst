Preprocessing
=============

Other than items, rules can also contain preprocessing operations which allow
modifications on the tree before starting data extraction. Such operations
can be needed to make data extraction simpler or to remove the need for
some postprocessing operations on the collected data.

The syntax for writing preprocessing operations is as follows:

.. code-block:: python

   rules = {
       "pre": [
           {
               "op": "...",
               ...
           }
       ]
       "items": [ ... ]
   }

Every preprocessing operation item has a name which is given as the value
of the "op" key. The other items in the mapping are specific to the operation.
The operations are applied in the order as they are written in the operations
list. Subrules can also contain preprocessing operations.

The predefined preprocessing operations are explained below.

Changing the root node
----------------------

If the data to be extracted is in some specific subtree, setting the root
node as the root of that subtree will make it easier to manage the XPath
queries. For example, most HTML templates use a markup like
``<div id="content">`` which marks the main content of the page and is likely
to contain the data to be scraped. In such a case, the following preprocessing
rule would allow you to write the XPath queries relative to that node:

.. code-block:: python

   {"op": "root", "path": ".//div[@id='content']"}
