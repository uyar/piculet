Data extraction
===============

This section explains how to write the rules for extracting the data.
We'll scrape the following HTML content for the movie "The Shining"
in our examples:

.. literalinclude:: ../tests/shining.html
   :language: html

The skeleton for a specification with an empty rule list
can be written as follows:

.. literalinclude:: ../tests/movie_xml_spec.json
   :language: json

Assuming the HTML document above is saved as :file:`shining.html`
and the specification is saved as :file:`movie_xml_spec.json`,
let's get their contents:

.. code-block:: python

   from pathlib import Path
   document = Path("shining.html").read_text()

   import json
   movie_spec = json.loads(Path("movie_xml_spec.json").read_text())

.. note::

   The example uses an HTML document in combination with XPath queries.
   JSON documents in combination with JMESPath queries conceptually work
   the same way, differing only in XPath/JMESPath related details.

Rules
-----

The rule list will contain key-value pairs where the extractor describes
how to extract the actual value.
In the simple case, an extractor contains an XPath query.

For example, to get the title of the movie from the example document,
we can write the following rule list containing only one rule:

.. code-block:: python

   rules = [{"key": "title", "extractor": {"path": "//title/text()"}}]

We can generate a full specification by substituting the empty rule list
in the skeleton specification:

.. code-block:: python

   movie_spec | {"rules": rules}

   # gives:
   {"doctype": "xml",
    "path_type": "xpath",
    "rules": [{"key": "title", "extractor": {"path": "//title/text()"}}]}

Next, we'll use the :func:`load_spec <piculet.load_spec>` function
to load this specification:

.. code-block:: python

   from piculet import load_spec
   spec = load_spec(movie_spec | {"rules": rules})

Now that we have the document and the specification,
we can use the :func:`scrape <piculet.scrape>` function
to extract data from the document:

.. code-block:: python

   from piculet import scrape
   scrape(document, spec)

   # result:
   {"title": "The Shining"}

.. note::

   After this point, only the rule list and the result will be given.
   The same ``load_spec`` and ``scrape`` function calls can be used
   to verify the results::

     rules = [...]
     spec = load_spec(movie_spec | {"rules": rules})
     scrape(document, spec)

Multiple items can be collected in a single invocation:

.. code-block:: python

   # rules:
   [
     {
       "key": "title",
       "extractor": {
         "path": "//title/text()"
       }
     },
     {
       "key": "year",
       "extractor": {
         "path": "//span[@class='year']/text()"
       }
     }
   ]

   # result:
   {
     "title": "The Shining",
     "year": "1980"
   }

If a rule doesn't produce a value, the item will be excluded from the output.
Note that in the following example, there's no ``foo`` key in the result:

.. code-block:: python

   # rules:
   [
     {
       "key": "title",
       "extractor": {
         "path": "//title/text()"
       }
     },
     {
       "key": "foo",
       "extractor": {
         "path": "//foo/text()"
       }
     }
   ]

   # result:
   {"title": "The Shining"}

Transforming results
--------------------

Extractors can apply transformation functions to the values they have obtained.
Piculet offers several predefined
:attr:`transformers <piculet.transformers>`.
For example, the previous rule for the movie year produces a string.
To convert that value to an integer, we can use the ``int`` transformer:

.. code-block:: python

   # rules:
   [
     {
       "key": "year",
       "extractor": {
         "path": "//span[@class='year']/text()",
         "transforms": [
           "int"
         ]
       }
     }
   ]

   # result:
   {"year": 1980}

If you want to use a custom transformer, you have to register it first:

.. code-block:: python

   from piculet import transformers
   transformers["underscore"] = lambda s: s.replace(" ", "_")

Now the transformer is available:

.. code-block:: python

   # rules:
   [
     {
       "key": "title",
       "extractor": {
         "path": "//title/text()",
         "transforms": [
           "underscore"
         ]
       }
     }
   ]

   # result:
   {"title": "The_Shining"}

Multiple transformations are applied in the order they are listed.
First, let's define two more transformations:

.. code-block:: python

   transformers["titlecase"] = str.title
   transformers["removespaces"] = lambda s: s.replace(" ", "")

   # rules:
   [
     {
       "key": "title",
       "extractor": {
         "path": "//title/text()",
         "transforms": [
           "removespaces",
           "titlecase"
         ]
       }
     }
   ]

   # result:
   {"title": "Theshining"}


Multi-valued results
--------------------

Data with multiple values can be created by using a ``foreach`` key
in the value specifier.
This is an XPath expression to select elements from the tree.

The XPath query in the ``path`` key will be applied *to each selected element*,
and the obtained values will be collected in the resulting list.
For example, to get the genres of the movie, we can write:

.. code-block:: python

   # rules:
   [
     {
       "key": "genres",
       "extractor": {
         "foreach": "//ul[@class='genres']/li",
         "path": "./text()"
       }
     }
   ]

   # result:
   {"genres": ["Horror", "Drama"]}

If the ``foreach`` key doesn't match any element, the item will be excluded
from the result:

.. code-block:: python

   # rules:
   [
     {
       "key": "foos",
       "extractor": {
         "foreach": "//ul[@class='foos']/li",
         "path": "./text()"
       }
     }
   ]

   # result:
   {}

If a transformation is specified, it will be applied to every element
in the resulting list.
Here's an example using the predefined ``lower`` transformer
for converting a string to lowercase:

.. code-block:: python

   # rules:
   [
     {
       "key": "genres",
       "extractor": {
         "foreach": "//ul[@class='genres']/li",
         "path": "./text()",
         "transforms": [
           "lower"
         ]
       }
     }
   ]

   # result:
   {"genres": ["horror", "drama"]}

Subrules
--------

Nested structures can be created by writing subrules as extractors.
If the extractor contains a ``rules`` key instead of a path,
then this will be interpreted as a subrule,
and the generated mapping will be the value for the key.

.. code-block:: python

   # rules:
   [
     {
       "key": "director",
       "extractor": {
         "rules": [
           {
             "key": "name",
             "extractor": {
               "path": "//div[@class='director']//a/text()"
             }
           },
           {
             "key": "link",
             "extractor": {
               "path": "//div[@class='director']//a/@href"
             }
           }
         ]
       }
     }
   ]

   # result:
   {
     "director": {
       "name": "Stanley Kubrick",
       "link": "/people/1"
     }
   }

Subrules can be combined with multi-values:

.. code-block:: python

   # rules:
   [
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

   # result:
   {
     "cast": [
       {
         "name": "Jack Nicholson",
         "character": "Jack Torrance"
       },
       {
         "name": "Shelley Duvall",
         "character": "Wendy Torrance"
       }
     ]
   }

Subitems can also be transformed.
The transformation functions are always applied as the last step
in an extraction,
therefore the first transformer will take the generated mapping as parameter.

.. code-block:: python

   transformers["stars"] = lambda x: "%(name)s as %(character)s" % x

   # rules:
   [
     {
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
   ]

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

   # rules:
   [
       {
           "foreach": "//div[@class='info']",
           "key": {"path": "./h3/text()" },
           "extractor": {"path": "./p/text()"}
       }
   ]

   # result:
   {"Country": "United States", "Language": "English"}

Like values, keys can also be transformed:

.. code-block:: python

   # rules:
   [
       {
           "foreach": "//div[@class='info']",
           "key": {"path": "./h3/text()", "transforms": ["lower"]},
           "extractor": {"path": "./p/text()"}
       }
   ]

   # result:
   {"country": "United States", "language": "English"}
