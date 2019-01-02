Preprocessing
=============

Other than extraction rules, specifications can also contain preprocessing
operations which allow modifications on the tree before starting
data extraction. Such operations can be needed to make data extraction
simpler or to remove the need for some postprocessing operations
on the collected data.

The syntax for writing preprocessing operations is as follows:

.. code-block:: python

   rules = {
       'pre': [
           {
               'op': '...',
               ...
           },
           {
               'op': '...',
               ...
           }
       ],
       'items': [ ... ]
   }

Every preprocessing operation item has a name which is given as the value
of the "op" key. The other items in the mapping are specific to the operation.
The operations are applied in the order as they are written in the operations
list.

The predefined preprocessing operations are explained below.

Removing elements
-----------------

This operation removes from the tree all the elements (and its subtree)
that are selected by a given XPath query:

.. code-block:: python

   {'op': 'remove', 'path': '...'}

Setting element attributes
--------------------------

This operation selects all elements by a given XPath query and
sets an attribute for these elements to a given value:

.. code-block:: python

   {'op': 'remove', 'path': '...', 'name': '...', 'value': '...'}

The attribute "name" can be a literal string or an extractor as described
in the data extraction chapter. Similarly, the attribute "value" can be given
as a literal string or an extractor.

Setting element text
--------------------

This operation selects all elements by a given XPath query and
sets their texts to a given value:

.. code-block:: python

   {'op': 'remove', 'path': '...', 'text': '...'}

The "text" can be a literal string or an extractor.
