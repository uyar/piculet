Postprocessing
==============

Specifications can contain postprocessing operations
to make changes on the obtained data after extraction.

Postprocessors are functions that take a mapping and return a mapping.
Like with transformers, a map to look up postprocessor callables from names
has to be given to the :func:`load_spec <piculet.load_spec>` function.

An example use case for postprocessing could be combining data gathered
in separate pieces.
For example, to keep a combined crew list instead of separate
director and cast data, we can write:

.. code-block:: python

   def collect_crew_names(data):
       crew = [data["director"]["name"]]
       crew.extend([member["name"] for member in data["cast"]])
       data["crew"] = crew
       del data["director"]
       del data["cast"]
       return data

   postprocessors = {"crew_names": collect_crew_names}

   rules = [
       {
           "key": "title",
           "extractor": {"path": "//title//text()"}
       },
       {
           "key": "director",
           "extractor": {
               "rules": [
                   {
                       "key": "name",
                       "extractor": {"path": "//div[@class='director']//a/text()"}
                   },
                   {
                       "key": "link",
                       "extractor": {"path": "//div[@class='director']//a/@href"}
                   }
               ]
           }
       },
       {
           "key": "cast",
           "extractor": {
               "foreach": "//table[@class='cast']/tr",
               "rules": [
                   {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
                   {"key": "character", "extractor": {"path": "./td[2]/text()"}}
               ]
           }
       }
   ]

   spec = load_spec(
       {"doctype": "html", "rules": rules, "post": ["crew_names"]},
       postprocessors=postprocessors
   )
   scrape(document, spec)

   # result:
   {
       "title": "The Shining",
       "crew": ["Stanley Kubrick", "Jack Nicholson", "Shelley Duvall"]
   }
