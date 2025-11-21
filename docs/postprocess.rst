Postprocessing
==============

Specifications can contain postprocessing operations
to make changes on the obtained data after extraction.

Postprocessors are functions that take a mapping and return a mapping.
Like with transformers, a map to look up postprocessor callables from names
has to be given to the :func:`load_spec <piculet.load_spec>` function.

For example, to add a key by combining the director name with the title:

.. code-block:: python

   def add_director_title(data):
       data["director_title"] = "%(director)s's '%(title)s'" % data
       return data

   postprocessors = {"director_title": add_director_title}

   rules = [
       {
           "key": "title",
           "extractor": {"path": "//title//text()"}
       },
       {
           "key": "director",
           "extractor": {"path": "//div[@class='director']//a/text()"}
       }
   ]

   spec = load_spec(
       {"rules": rules, "post": ["director_title"]},
       postprocessors=postprocessors
   )
   data = spec.scrape(document, doctype="html")

   # data:
   {
       "title": "The Shining",
       "director": "Stanley Kubrick",
       "director_title": "Stanley Kubrick's 'The Shining'"
   }
