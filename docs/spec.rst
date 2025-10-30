Specification
=============

The specification is a JSON document with the following structure:

.. code-block:: JSON

   {
     "doctype": ...,
     "path_type": ...,
     "pre": ...,
     "rules": ...
     "post": ...
   }

*doctype* (required)
    A string indicating the type of the document.
    Possible values are ``html``, ``xml``, and ``json``.

*path_type* (required)
    A string indicating whether queries are written in XPath or JMESPath.
    Possible values are ``xpath`` and ``jmespath``.

*pre*
    A list of preprocessors to apply to the document tree.

*rules* (required)
    A list of rules to apply to the document tree to extract the data.

*post*
    A list of postprocessors to apply to the extracted data.
