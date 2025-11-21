Preprocessing
=============

Specifications can contain preprocessing operations
which allow modifications on the tree before starting data extraction.

Preprocessors are functions that take the root node of a tree and
return a node to be used as the root in extraction operations.
Like with transformers, a map to look up preprocessor callables from names
has to be given to the :func:`load_spec <piculet.load_spec>` function.

For example, to gather all the person names from the document,
we can use a preprocessor to select the relevant ``a`` tags and add them
a ``class`` attribute which we can later use in path queries:

.. code-block:: python

   def mark_people_links(root):
       for anchor in root.xpath("//a[starts-with(@href, '/people/')]"):
           anchor.attrib["class"] = "person"
       return root

   preprocessors = {"mark_people": mark_people_links}

   rules = [
       {
           "key": "title",
           "extractor": {"path": "//title//text()"}
       },
       {
           "key": "people",
           "extractor": {"foreach": "//a[@class='person']", "path": "./text()"}
       }
   ]

   spec = load_spec(
       {"pre": ["mark_people"], "rules": rules},
       preprocessors=preprocessors
   )
   data = spec.scrape(document, doctype="html")

   # data:
   {
       "title": "The Shining",
       "people": ["Stanley Kubrick", "Jack Nicholson", "Shelley Duvall"]
   }
