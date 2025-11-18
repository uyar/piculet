Data extraction
===============

This section explains how to write the rules for extracting the data.
We'll scrape the following HTML content for the movie "The Shining"
in our examples:

.. literalinclude:: ../tests/shining.html
   :language: html

Assuming the HTML document above is saved as :file:`shining.html`,
let's get its contents:

.. code-block:: python

   from pathlib import Path

   document = Path("shining.html").read_text()

.. note::

   The example uses an HTML document in combination with XPath queries.
   JSON documents in combination with JMESPath queries conceptually work
   the same way, differing only in XPath/JMESPath related details.

Rules
-----

Each rule in the list specifies what the name of a piece of data will be,
and how its value will be extracted.
In the simple case, an extractor will use a path query.

For example, to get the title of the movie from the example document,
we can write the following rule:

.. code-block:: python

   rule = {"key": "title", "extractor": {"path": "//title/text()"}}

Next, we use this rule in a specification
that we load using the :func:`load_spec <piculet.load_spec>` function:

.. code-block:: python

   from piculet import load_spec

   spec = load_spec({"doctype": "html", "rules": [rule]})

Now that we have the document and the specification,
we can use the :func:`scrape <piculet.scrape>` function
to extract data from the document:

.. code-block:: python

   from piculet import scrape

   scrape(document, spec)

   # result:
   {"title": "The Shining"}

The XPath query has to be arranged so that it will return a list of texts.
These will be joined to produce the value.
For example:

.. code-block:: python

   rule = {"key": "full_title", "extractor": {"path": "//h1//text()"}}

   spec = load_spec({"doctype": "html", "rules": [rule]})
   scrape(document, spec)

   # result:
   {"full_title": "The Shining (1980)"}

Multiple items can be collected in a single invocation:

.. code-block:: python

   rules = [
       {"key": "title", "extractor": {"path": "//title/text()"}},
       {"key": "country", "extractor": {"path": "//div[@class='info'][1]/p/text()"}}
   ]

   spec = load_spec({"doctype": "html", "rules": rules})
   scrape(document, spec)

   # result:
   {"title": "The Shining", "country": "United States"}

If a rule doesn't produce a value, the item will be excluded from the output.
Note that in the following example, there's no ``foo`` key in the result:

.. code-block:: python

   rules = [
       {"key": "title", "extractor": {"path": "//title/text()"}},
       {"key": "foo", "extractor": {"path": "//foo/text()"}}
   ]

   spec = load_spec({"doctype": "html", "rules": rules})
   scrape(document, spec)

   # result:
   {"title": "The Shining"}

Transforming results
--------------------

Extractors can apply transformations to the values they have obtained.
Each transformation has a name and an associated function.
We tell the extractor to apply the function by giving its name
in the extractor transforms.
To match the transformer names to their functions,
a lookup map has to be provided when the specification is loaded.

For example, the following rule for the movie year would produce a string::

  {"key": "year", "extractor": {"path": "//span[@class='year']/text()"}}

To convert that value to an integer,
let's define and use an ``int`` transformer:

.. code-block:: python

   rule = {
       "key": "year",
       "extractor": {
           "path": "//span[@class='year']/text()",
           "transforms": ["int"]
       }
   }

   transformers = {"int": int}
   spec = load_spec(
       {"doctype": "html", "rules": [rule]},
       transformers=transformers
   )
   scrape(document, spec)

   # result:
   {"year": 1980}

Multiple transformations are applied in the order they are listed:

.. code-block:: python

   rule = {
       "key": "title",
       "extractor": {
           "path": "//title/text()",
           "transforms": ["remove_spaces", "titlecase"]
       }
   }

   transformers = {
       "titlecase": str.title,
       "remove_spaces": lambda s: s.replace(" ", "")
   }
   spec = load_spec(
       {"doctype": "html", "rules": [rule]},
       transformers=transformers
   )
   scrape(document, spec)

   # result:
   {"title": "Theshining"}

Multivalued results
--------------------

Data with multiple values can be created by using a ``foreach`` key
in the extractor.
This should be a path expression to select elements from the tree.
After the elements are selected, the query in the ``path`` key
will be applied *to each element*,
and the obtained values will be collected in the resulting list.
For example, to get the genres of the movie, we can write:

.. code-block:: python

   rule = {
       "key": "genres",
       "extractor": {
           "foreach": "//ul[@class='genres']/li",
           "path": "./text()"
       }
   }

   spec = load_spec({"doctype": "html", "rules": [rule]})
   scrape(document, spec)

   # result:
   {"genres": ["Horror", "Drama"]}

If the ``foreach`` key doesn't match any element, the item will be excluded
from the result:

.. code-block:: python

   rules = [
       {
           "key": "title",
           "extractor": {"path": "//title/text()"}
       },
       {
           "key": "foos",
           "extractor": {
               "foreach": "//ul[@class='foos']/li",
               "path": "./text()"
           }
       }
   ]

   spec = load_spec({"doctype": "html", "rules": rules})
   scrape(document, spec)

   # result:
   {"title": "The Shining"}

If a transformation is specified, it will be applied to *each element*
in the resulting list:

.. code-block:: python

   rule = {
       "key": "genres",
       "extractor": {
           "foreach": "//ul[@class='genres']/li",
           "path": "./text()",
           "transforms": ["lower"]
       }
   }

   transformers = {"lower": str.lower}
   spec = load_spec(
       {"doctype": "html", "rules": [rule]},
       transformers=transformers
   )
   scrape(document, spec)

   # result:
   {"genres": ["horror", "drama"]}

Subrules
--------

Nested structures can be created by writing subrules as extractors.
If the extractor contains a ``rules`` key instead of a path,
then this will be interpreted as a subrule,
and the generated mapping will be the value for the key.

.. code-block:: python

   rule = {
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
   }

   spec = load_spec({"doctype": "html", "rules": [rule]})
   scrape(document, spec)

   # result:
   {"director": {"name": "Stanley Kubrick", "link": "/people/1"}}

Extractors can be moved to a selected node before applying the query.
This can improve readability and performance.
The ``root`` key has to be a path that selects the root for the operation.
If it returns multiple nodes, the first one will be selected.
The above rule is equivalent to:

.. code-block:: python

   rule = {
       "key": "director",
       "extractor": {
           "root": "//div[@class='director']//a",
           "rules": [
               {
                   "key": "name",
                   "extractor": {"path": "./text()"}
               },
               {
                   "key": "link",
                   "extractor": {"path": "./@href"}
               }
           ]
       }
   }

Subrules can be combined with multivalues:

.. code-block:: python

   rule = {
       "key": "cast",
       "extractor": {
           "foreach": "//table[@class='cast']/tr",
           "rules": [
               {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
               {"key": "character", "extractor": {"path": "./td[2]/text()"}}
           ]
       }
   }

   spec = load_spec({"doctype": "html", "rules": [rule]})
   scrape(document, spec)

   # result:
   {
     "cast": [
       {"name": "Jack Nicholson", "character": "Jack Torrance"},
       {"name": "Shelley Duvall", "character": "Wendy Torrance"}
     ]
   }

Moving the root takes place before selecting the elements using ``foreach``.
The rule given above is equivalent to:

.. code-block:: python

   rule = {
       "key": "cast",
       "extractor": {
           "root": "//table[@class='cast']"
           "foreach": "./tr",
           "rules": [
               {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
               {"key": "character", "extractor": {"path": "./td[2]/text()"}}
           ]
       }
   }

Subitems can also be transformed.
The transformation functions are always applied as the last step
in an extraction,
therefore the first transformer will take the generated mapping as parameter.

.. code-block:: python

   rule = {
       "key": "cast",
       "extractor": {
           "foreach": "//table[@class='cast']/tr",
           "rules": [
               {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
               {"key": "character", "extractor": {"path": "./td[2]/text()"}}
           ],
           "transforms": ["stars"]
       }
   }

   transformers = {"stars": lambda x: "%(name)s as %(character)s" % x}
   spec = load_spec(
       {"doctype": "html", "rules": [rule]},
       transformers=transformers
   )
   scrape(document, spec)

   # result:
   {
     "cast": [
        "Jack Nicholson as Jack Torrance",
        "Shelley Duvall as Wendy Torrance"
     ]
   }

Generating keys from content
----------------------------

You can generate items where the key value also comes from the content.
For example, consider how you would get the country and the language
of the movie.
Instead of writing multiple items for each ``h3`` element
under a ``div`` element with an ``info`` class,
we can write only one item that will select these divs
and use the h3 text as the key.

This method requires to locate the elements that contain both the key
and the value (in this example, the ``div``).
These elements will be selected using a ``foreach`` specification.
Key and value extractors will be applied to each selected element.

.. code-block:: python

   rule = {
       "foreach": "//div[@class='info']",
       "key": {"path": "./h3/text()" },
       "extractor": {"path": "./p/text()"}
   }

   spec = load_spec({"doctype": "html", "rules": [rule]})
   scrape(document, spec)

   # result:
   {"Country": "United States", "Language": "English"}

Like values, keys can also be transformed:

.. code-block:: python

   rule = {
       "foreach": "//div[@class='info']",
       "key": {"path": "./h3/text()", "transforms": ["lower"]},
       "extractor": {"path": "./p/text()"}
   }

   transformers = {"lower": str.lower}
   spec = load_spec(
       {"doctype": "html", "rules": [rule]},
       transformers=transformers
   )
   scrape(document, spec)

   # result:
   {"country": "United States", "language": "English"}
