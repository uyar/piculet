Preprocessing
=============

Specifications can contain preprocessing operations
which allow modifications on the tree before starting data extraction.

Preprocessors are functions that take the root node of a tree and
return a node to be used as the root in extraction operations.
Like with transformers, a map to look up preprocessor callables from names
has to be given to the :func:`load_spec <piculet.load_spec>` function.

An example use case for preprocessing is to select a new root
for simplifying data extraction queries.
For example, if all the data to be extracted from an HTML document
is under the ``body`` tag,
we can use a preprocessor to select that tag as the root and
write the path queries relative to it.
For the HTML/XPath example:

.. code-block:: python

   preprocessors = {"get_body": lambda x: x.xpath('//body')[0]}

   rules = [
       {
           "key": "full_title",
           "extractor": {"path": "./h1//text()"}
       },
       {
           "key": "genre",
           "extractor": {"path": "./ul[@class='genres']/li[1]/text()"}
       },
   ]

   spec = load_spec(
       {"doctype": "html", "pre": ["get_body"], "rules": rules},
       preprocessors=preprocessors
   )
   scrape(document, spec)

   # result:
   {"full_title": "The Shining (1980)", "genre": "Horror"}
