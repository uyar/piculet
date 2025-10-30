Preprocessing
=============

Specifications can contain preprocessing operations
which allow modifications on the tree before starting data extraction.
Such operations can be useful in simplifying data extraction.

Preprocessors are functions that take a tree and return a tree.
Like transformers, preprocessors have to be registered before use:

.. code-block:: python

   from piculet import preprocessors
   preprocessors[name] = function

Piculet does not provide any predefined preprocessors.
