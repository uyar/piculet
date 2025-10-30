Postprocessing
==============

Specifications can contain postprocessing operations
which allow modifications on the obtained data after extraction.
Such operations can be useful for deriving data from separate pieces.

Postprocessors are functions that take a mapping and return a mapping.
Like transformers, postprocessors have to be registered before use:

.. code-block:: python

   from piculet import postprocessors
   postprocessors[name] = function

Piculet does not provide any predefined postprocessors.
